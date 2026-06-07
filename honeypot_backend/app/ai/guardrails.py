"""
AI Safety Guardrails for honeypot data sanitisation.

Attacker-controlled log content passes through these filters
*before* being injected into LLM prompts, preventing prompt
injection, SQL injection, and OS command injection from
honeypot captures.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Prompt-injection patterns ────────────────────────────────────────────────
# Case-insensitive patterns commonly used to hijack LLM behaviour.
_PROMPT_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\b", re.IGNORECASE),
    re.compile(r"act\s+as\s+if\b", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+are\b", re.IGNORECASE),
    re.compile(r"\bSYSTEM\s*:", re.IGNORECASE),
    re.compile(r"\bASSISTANT\s*:", re.IGNORECASE),
    re.compile(r"\bUSER\s*:", re.IGNORECASE),
    re.compile(r"\bHUMAN\s*:", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"```\s*system\b", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"\[/INST\]", re.IGNORECASE),
]

# ── SQL-injection patterns ───────────────────────────────────────────────────
_SQL_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"('\s*(OR|AND)\s+'[^']*'\s*=\s*'[^']*')", re.IGNORECASE),
    re.compile(r";\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\s+", re.IGNORECASE),
    re.compile(r"UNION\s+(ALL\s+)?SELECT\s+", re.IGNORECASE),
    re.compile(r"--\s*$", re.MULTILINE),
    re.compile(r"/\*.*?\*/", re.DOTALL),
    re.compile(r";\s*EXEC\s+", re.IGNORECASE),
    re.compile(r"'\s*;\s*--", re.IGNORECASE),
    re.compile(r"1\s*=\s*1", re.IGNORECASE),
    re.compile(r"WAITFOR\s+DELAY", re.IGNORECASE),
    re.compile(r"BENCHMARK\s*\(", re.IGNORECASE),
]

# ── OS command-injection patterns ────────────────────────────────────────────
_OS_COMMAND_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r";\s*(rm|cat|wget|curl|nc|bash|sh|python|perl|php)\s+", re.IGNORECASE),
    re.compile(r"\|\s*(rm|cat|wget|curl|nc|bash|sh|python|perl|php)\s+", re.IGNORECASE),
    re.compile(r"&&\s*(rm|cat|wget|curl|nc|bash|sh|python|perl|php)\s+", re.IGNORECASE),
    re.compile(r"\$\(.*\)", re.DOTALL),
    re.compile(r"`[^`]+`"),
    re.compile(r">\s*/etc/(passwd|shadow|hosts)", re.IGNORECASE),
    re.compile(r"/dev/(tcp|udp)/", re.IGNORECASE),
]

# Replacement placeholder used when dangerous content is stripped.
_SANITISED = "[SANITISED]"


def sanitize_input(text: str) -> str:
    """Remove known prompt-injection, SQL-injection, and OS command-injection
    patterns from attacker-controlled honeypot log content.

    The original payload is still stored in the database verbatim; this
    function only cleans the version sent to the LLM prompt.

    Args:
        text: Raw text extracted from honeypot logs.

    Returns:
        Sanitised text safe for LLM prompt inclusion.
    """
    if not text:
        return text

    sanitised = text

    for pattern in _PROMPT_INJECTION_PATTERNS:
        sanitised = pattern.sub(_SANITISED, sanitised)

    for pattern in _SQL_INJECTION_PATTERNS:
        sanitised = pattern.sub(_SANITISED, sanitised)

    for pattern in _OS_COMMAND_PATTERNS:
        sanitised = pattern.sub(_SANITISED, sanitised)

    if sanitised != text:
        logger.warning(
            "guardrails.input_sanitised",
            original_length=len(text),
            sanitised_length=len(sanitised),
            patterns_triggered=_count_replacements(text, sanitised),
        )

    return sanitised


def truncate_safely(cmd: str, max_chars: int = 1000) -> str:
    """Truncate oversized commands or base64 payloads to *max_chars*.

    Adds a ``[TRUNCATED]`` suffix when the string is cut so
    downstream consumers know the value was shortened.

    Args:
        cmd: The raw command or payload string.
        max_chars: Maximum allowed character count (default 1000).

    Returns:
        The original string if within limits, otherwise a truncated
        version with ``[TRUNCATED]`` appended.
    """
    if not cmd or len(cmd) <= max_chars:
        return cmd

    truncated = cmd[:max_chars] + " [TRUNCATED]"
    logger.debug(
        "guardrails.truncated",
        original_length=len(cmd),
        max_chars=max_chars,
    )
    return truncated


def remove_malformed_unicode(text: str) -> str:
    """Strip control characters (except ``\\n`` and ``\\t``), null bytes,
    and malformed unicode sequences from the input.

    Args:
        text: Raw text that may contain control characters.

    Returns:
        Cleaned text with only printable characters plus newline/tab.
    """
    if not text:
        return text

    # Remove null bytes first
    cleaned = text.replace("\x00", "")

    # Strip control characters except newline (\n) and tab (\t)
    cleaned = "".join(
        ch
        for ch in cleaned
        if ch in ("\n", "\t") or not unicodedata.category(ch).startswith("C")
    )

    # Normalise to NFC to collapse decomposed sequences
    cleaned = unicodedata.normalize("NFC", cleaned)

    if cleaned != text:
        logger.debug(
            "guardrails.unicode_cleaned",
            original_length=len(text),
            cleaned_length=len(cleaned),
        )

    return cleaned


def validate_response_schema(
    response_text: str,
    schema_class: type[BaseModel],
) -> dict[str, Any] | None:
    """Parse and validate an LLM JSON response against a Pydantic model.

    Handles the common case where models wrap their JSON in markdown
    code fences (````json ... ````).

    Args:
        response_text: Raw text returned by the LLM.
        schema_class: A Pydantic v2 ``BaseModel`` subclass to validate against.

    Returns:
        A validated ``dict`` on success, or ``None`` on any parsing /
        validation failure.
    """
    if not response_text:
        logger.warning("guardrails.empty_response", schema=schema_class.__name__)
        return None

    json_str = _extract_json(response_text)

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.warning(
            "guardrails.json_parse_failed",
            schema=schema_class.__name__,
            error=str(exc),
            response_preview=response_text[:200],
        )
        return None

    try:
        validated = schema_class.model_validate(parsed)
        return validated.model_dump()
    except ValidationError as exc:
        logger.warning(
            "guardrails.schema_validation_failed",
            schema=schema_class.__name__,
            errors=exc.error_count(),
            detail=str(exc),
        )
        return None


# ── Private helpers ──────────────────────────────────────────────────────────


def _extract_json(text: str) -> str:
    """Extract JSON from markdown code fences if present.

    Supports both ````json ... ```` and bare ```` ... ```` blocks.
    Falls back to returning the full text when no fences are detected.
    """
    # Try ```json ... ``` first
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try to find the outermost { ... } or [ ... ]
    first_brace = text.find("{")
    first_bracket = text.find("[")

    if first_brace == -1 and first_bracket == -1:
        return text

    # Pick the earlier starting delimiter
    if first_bracket == -1 or (first_brace != -1 and first_brace < first_bracket):
        start = first_brace
        end = text.rfind("}")
        if end != -1:
            return text[start : end + 1]
    else:
        start = first_bracket
        end = text.rfind("]")
        if end != -1:
            return text[start : end + 1]

    return text


def _count_replacements(original: str, sanitised: str) -> int:
    """Count how many ``[SANITISED]`` tokens were inserted."""
    return sanitised.count(_SANITISED)
