"""
Multi-model NVIDIA NIM client for the Honeypot SOC pipeline.

Wraps the OpenAI-compatible API exposed by NIM endpoints, adding:
* Semaphore-based concurrency control (realtime: 10, investigation: 3)
* Automatic fallback to a secondary model for realtime workloads
* Input sanitisation via :mod:`app.ai.guardrails`
* Structured logging with token-usage tracking
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from openai import AsyncOpenAI, APITimeoutError, APIConnectionError, APIStatusError
from pydantic import BaseModel

from app.ai import guardrails
from app.ai.prompts import (
    ADVERSARY_PROFILE_TEMPLATE,
    ALERT_SUMMARY_TEMPLATE,
    ATTACK_CHAIN_TEMPLATE,
    INCIDENT_INVESTIGATION_TEMPLATE,
    INVESTIGATION_SYSTEM_PROMPT,
    PROMPT_VERSIONS,
    REALTIME_ANALYSIS_TEMPLATE,
    REALTIME_SYSTEM_PROMPT,
    SEVERITY_CLASSIFICATION_TEMPLATE,
)
from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Timeout constants (seconds) ─────────────────────────────────────────────
_REALTIME_TIMEOUT: float = 10.0
_INVESTIGATION_TIMEOUT: float = 60.0
_EMBEDDING_TIMEOUT: float = 15.0

# ── Retry / back-off ────────────────────────────────────────────────────────
_MAX_RETRIES: int = 2
_BACKOFF_BASE: float = 0.5  # exponential back-off multiplier


# ── Pydantic response schemas ───────────────────────────────────────────────

class RealtimeAnalysisResponse(BaseModel):
    """Expected schema for ``analyze_realtime``."""

    summary: str
    severity: str
    attack_type: str
    recommendation: str


class InvestigationResponse(BaseModel):
    """Expected schema for ``investigate_incident``."""

    summary: str
    attack_chain: list[Any]
    severity: str
    threat_actor_profile: str
    recommended_actions: list[str]
    confidence: float
    mitre_techniques: list[str]


# ═══════════════════════════════════════════════════════════════════════════════


class NIMClient:
    """Async, multi-model NIM client with concurrency limits and fallback."""

    def __init__(self, settings: Settings) -> None:
        self.client = AsyncOpenAI(
            base_url=settings.NIM_BASE_URL,
            api_key=settings.NIM_API_KEY,
        )
        self.realtime_model: str = settings.REALTIME_MODEL
        self.fallback_realtime_model: str = settings.FALLBACK_REALTIME_MODEL
        self.investigation_model: str = settings.INVESTIGATION_MODEL
        self.embed_model: str = settings.EMBED_MODEL

        # Concurrency guards
        self._realtime_sem = asyncio.Semaphore(10)
        self._investigation_sem = asyncio.Semaphore(3)

        logger.info(
            "nim_client.initialised",
            realtime_model=self.realtime_model,
            fallback_model=self.fallback_realtime_model,
            investigation_model=self.investigation_model,
            embed_model=self.embed_model,
        )

    # ── Internal helpers ─────────────────────────────────────────────────

    async def _chat_completion(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        timeout: float,
        semaphore: asyncio.Semaphore,
    ) -> tuple[str, int]:
        """Send a chat-completion request and return ``(content, tokens_used)``.

        Acquires *semaphore* before making the network call so that
        concurrent usage stays within the configured limits.
        """
        async with semaphore:
            t0 = time.monotonic()
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                ),
                timeout=timeout,
            )
            elapsed = time.monotonic() - t0

        content = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0

        logger.info(
            "nim_client.completion",
            model=model,
            tokens=tokens_used,
            elapsed_s=round(elapsed, 3),
        )
        return content, tokens_used

    async def _realtime_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[str, str, int]:
        """Try the primary realtime model; fall back on **any** error.

        Returns ``(content, model_used, tokens_used)``.
        """
        # Attempt primary model with retries
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                content, tokens = await self._chat_completion(
                    model=self.realtime_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    timeout=_REALTIME_TIMEOUT,
                    semaphore=self._realtime_sem,
                )
                return content, self.realtime_model, tokens
            except (
                asyncio.TimeoutError,
                APITimeoutError,
                APIConnectionError,
                APIStatusError,
                Exception,
            ) as exc:
                logger.warning(
                    "nim_client.primary_retry",
                    model=self.realtime_model,
                    attempt=attempt,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(_BACKOFF_BASE * (2 ** (attempt - 1)))

        # Fallback model – single attempt
        logger.warning(
            "nim_client.fallback_triggered",
            primary_model=self.realtime_model,
            fallback_model=self.fallback_realtime_model,
        )
        try:
            content, tokens = await self._chat_completion(
                model=self.fallback_realtime_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                timeout=_REALTIME_TIMEOUT,
                semaphore=self._realtime_sem,
            )
            return content, self.fallback_realtime_model, tokens
        except Exception as exc:
            logger.error(
                "nim_client.fallback_failed",
                fallback_model=self.fallback_realtime_model,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

    # ── Sanitisation helpers ─────────────────────────────────────────────

    @staticmethod
    def _sanitize_attack_data(attack_data: dict[str, Any]) -> dict[str, Any]:
        """Deep-sanitize every string value in *attack_data*."""
        sanitised: dict[str, Any] = {}
        for key, value in attack_data.items():
            if isinstance(value, str):
                value = guardrails.remove_malformed_unicode(value)
                value = guardrails.truncate_safely(value)
                value = guardrails.sanitize_input(value)
            sanitised[key] = value
        return sanitised

    # ── Realtime methods ─────────────────────────────────────────────────

    async def analyze_realtime(
        self,
        attack_data: dict[str, Any],
    ) -> tuple[dict[str, Any], str, str]:
        """Analyse a single attack event in real-time.

        Returns:
            ``(analysis_result, model_used, prompt_version)``
        """
        safe = self._sanitize_attack_data(attack_data)
        user_prompt = REALTIME_ANALYSIS_TEMPLATE.format(**safe)

        content, model_used, _tokens = await self._realtime_with_fallback(
            system_prompt=REALTIME_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        prompt_version = PROMPT_VERSIONS["realtime"]

        result = guardrails.validate_response_schema(
            content, RealtimeAnalysisResponse,
        )
        if result is None:
            logger.warning(
                "nim_client.realtime_parse_fallback",
                model=model_used,
                raw_preview=content[:300],
            )
            result = {
                "summary": content.strip(),
                "severity": safe.get("severity", "medium"),
                "attack_type": "unknown",
                "recommendation": "Manual review recommended.",
            }

        return result, model_used, prompt_version

    async def generate_alert_summary(
        self,
        attack_data: dict[str, Any],
    ) -> str:
        """Generate a concise Telegram-ready alert summary."""
        safe = self._sanitize_attack_data(attack_data)
        user_prompt = ALERT_SUMMARY_TEMPLATE.format(**safe)

        content, model_used, _tokens = await self._realtime_with_fallback(
            system_prompt=REALTIME_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        logger.info(
            "nim_client.alert_summary_generated",
            model=model_used,
            src_ip=safe.get("src_ip"),
        )
        return content.strip()

    async def classify_severity(
        self,
        attack_data: dict[str, Any],
    ) -> str:
        """Classify an attack's severity as low/medium/high/critical."""
        safe = self._sanitize_attack_data(attack_data)
        user_prompt = SEVERITY_CLASSIFICATION_TEMPLATE.format(**safe)

        content, model_used, _tokens = await self._realtime_with_fallback(
            system_prompt=REALTIME_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        severity = content.strip().lower()
        valid_severities = {"low", "medium", "high", "critical"}
        if severity not in valid_severities:
            logger.warning(
                "nim_client.invalid_severity",
                raw=severity,
                model=model_used,
            )
            severity = "medium"

        return severity

    # ── Investigation methods (no fallback) ──────────────────────────────

    async def investigate_incident(
        self,
        attacks: list[dict[str, Any]],
        rag_context: str,
    ) -> tuple[dict[str, Any], str, str]:
        """Deep investigation across multiple correlated events.

        Returns:
            ``(report, model_used, prompt_version)``

        Raises:
            Any exception from the NIM API – callers must handle errors.
        """
        attacks_json = json.dumps(attacks, indent=2, default=str)
        user_prompt = INCIDENT_INVESTIGATION_TEMPLATE.format(
            attacks_json=guardrails.sanitize_input(attacks_json),
            rag_context=guardrails.sanitize_input(rag_context),
        )

        content, tokens = await self._chat_completion(
            model=self.investigation_model,
            system_prompt=INVESTIGATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=_INVESTIGATION_TIMEOUT,
            semaphore=self._investigation_sem,
        )

        prompt_version = PROMPT_VERSIONS["investigation"]

        result = guardrails.validate_response_schema(
            content, InvestigationResponse,
        )
        if result is None:
            logger.error(
                "nim_client.investigation_parse_failed",
                model=self.investigation_model,
                raw_preview=content[:500],
            )
            result = {
                "summary": "Investigation failed to produce a structured report due to an AI parsing error.",
                "attack_chain": [],
                "severity": "unknown",
                "threat_actor_profile": "Unknown profile",
                "recommended_actions": ["Manual review is required."],
                "confidence": 0.0,
                "mitre_techniques": []
            }

        return result, self.investigation_model, prompt_version

    async def analyze_attack_chain(
        self,
        attacks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Reconstruct the attack chain from a series of events.

        Raises:
            Any exception from the NIM API.
        """
        attacks_json = json.dumps(attacks, indent=2, default=str)
        user_prompt = ATTACK_CHAIN_TEMPLATE.format(
            attacks_json=guardrails.sanitize_input(attacks_json),
        )

        content, _tokens = await self._chat_completion(
            model=self.investigation_model,
            system_prompt=INVESTIGATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=_INVESTIGATION_TIMEOUT,
            semaphore=self._investigation_sem,
        )

        try:
            return json.loads(guardrails._extract_json(content))
        except json.JSONDecodeError as exc:
            logger.error(
                "nim_client.attack_chain_parse_failed",
                error=str(exc),
                raw_preview=content[:500],
            )
            raise ValueError("Failed to parse attack chain response") from exc

    async def profile_adversary(
        self,
        attacks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Profile the threat actor behind a series of attacks.

        Raises:
            Any exception from the NIM API.
        """
        attacks_json = json.dumps(attacks, indent=2, default=str)
        user_prompt = ADVERSARY_PROFILE_TEMPLATE.format(
            attacks_json=guardrails.sanitize_input(attacks_json),
        )

        content, _tokens = await self._chat_completion(
            model=self.investigation_model,
            system_prompt=INVESTIGATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=_INVESTIGATION_TIMEOUT,
            semaphore=self._investigation_sem,
        )

        try:
            return json.loads(guardrails._extract_json(content))
        except json.JSONDecodeError as exc:
            logger.error(
                "nim_client.adversary_profile_parse_failed",
                error=str(exc),
                raw_preview=content[:500],
            )
            raise ValueError("Failed to parse adversary profile response") from exc

    # ── Embedding methods ────────────────────────────────────────────────

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate a single embedding vector for *text*.

        Returns:
            A list of floats representing the embedding vector.
        """
        cleaned = guardrails.remove_malformed_unicode(text)
        cleaned = guardrails.truncate_safely(cleaned, max_chars=2000)

        response = await asyncio.wait_for(
            self.client.embeddings.create(
                model=self.embed_model,
                input=[cleaned],
                extra_body={"input_type": "query"}
            ),
            timeout=_EMBEDDING_TIMEOUT,
        )

        tokens_used = response.usage.total_tokens if response.usage else 0
        logger.debug(
            "nim_client.embedding_generated",
            model=self.embed_model,
            tokens=tokens_used,
            text_length=len(cleaned),
        )
        return response.data[0].embedding

    async def generate_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 20,
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Processes in chunks of *batch_size* to avoid API limits.

        Returns:
            A list of embedding vectors, one per input text.
        """
        all_embeddings: list[list[float]] = []
        total_tokens = 0

        for i in range(0, len(texts), batch_size):
            batch = [
                guardrails.truncate_safely(
                    guardrails.remove_malformed_unicode(t), max_chars=2000,
                )
                for t in texts[i : i + batch_size]
            ]

            response = await asyncio.wait_for(
                self.client.embeddings.create(
                    model=self.embed_model,
                    input=batch,
                    extra_body={"input_type": "passage"}
                ),
                timeout=_EMBEDDING_TIMEOUT,
            )

            batch_tokens = response.usage.total_tokens if response.usage else 0
            total_tokens += batch_tokens

            # Preserve original ordering
            sorted_data = sorted(response.data, key=lambda d: d.index)
            all_embeddings.extend(d.embedding for d in sorted_data)

        logger.info(
            "nim_client.batch_embeddings_generated",
            count=len(texts),
            batches=(len(texts) + batch_size - 1) // batch_size,
            total_tokens=total_tokens,
        )
        return all_embeddings

from app.core.config import get_settings
nim_client = NIMClient(get_settings())
