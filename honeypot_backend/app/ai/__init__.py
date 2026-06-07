"""
AI layer for the Honeypot SOC backend.

Exposes the three primary components:

* :class:`NIMClient` – multi-model NVIDIA NIM integration
* :class:`EmbeddingService` – Qdrant-backed attack vectorisation
* :mod:`guardrails` – input sanitisation & response validation
"""

from app.ai.embedding_service import EmbeddingService
from app.ai.guardrails import (
    remove_malformed_unicode,
    sanitize_input,
    truncate_safely,
    validate_response_schema,
)
from app.ai.nim_client import NIMClient

__all__ = [
    "NIMClient",
    "EmbeddingService",
    "sanitize_input",
    "truncate_safely",
    "remove_malformed_unicode",
    "validate_response_schema",
]
