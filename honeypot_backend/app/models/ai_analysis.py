"""
AIAnalysis model — stores AI-generated analysis of attack events.

Each analysis record is linked to a parent ``Attack`` via
``attack_id`` foreign key.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIAnalysis(Base):
    """AI-generated analysis result linked to an attack."""

    __tablename__ = "ai_analyses"

    # ── Foreign key ──────────────────────────────────────────────────────
    attack_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attacks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to the analysed attack",
    )

    # ── Analysis content ─────────────────────────────────────────────────
    summary: Mapped[str | None] = mapped_column(
        Text,
        comment="Human-readable summary of the attack",
    )
    severity: Mapped[str | None] = mapped_column(
        String(20),
        comment="AI-assessed severity: low / medium / high / critical",
    )
    attack_type: Mapped[str | None] = mapped_column(
        String(100),
        comment="AI-classified attack type",
    )
    recommendation: Mapped[str | None] = mapped_column(
        Text,
        comment="Recommended remediation steps",
    )
    attack_chain: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        comment="Structured MITRE ATT&CK chain mapping",
    )
    threat_actor_profile: Mapped[str | None] = mapped_column(
        Text,
        comment="Inferred threat actor description",
    )

    # ── Model metadata ───────────────────────────────────────────────────
    confidence: Mapped[float | None] = mapped_column(
        Float,
        comment="Model confidence score 0.0-1.0",
    )
    model_used: Mapped[str | None] = mapped_column(
        String(100),
        comment="Name of the LLM model used",
    )
    prompt_version: Mapped[str | None] = mapped_column(
        String(20),
        comment="Prompt template version identifier",
    )
    tokens_used: Mapped[int | None] = mapped_column(
        Integer,
        comment="Total tokens consumed (prompt + completion)",
    )
    analysis_type: Mapped[str | None] = mapped_column(
        String(20),
        comment="Analysis mode: 'realtime' or 'investigation'",
    )

    # ── Relationships ────────────────────────────────────────────────────
    attack: Mapped["Attack"] = relationship(
        "Attack",
        back_populates="ai_analyses",
    )

    def __repr__(self) -> str:
        return (
            f"<AIAnalysis(id={self.id!r}, attack_id={self.attack_id!r}, "
            f"analysis_type={self.analysis_type!r})>"
        )


# Import for IDE support only — resolved at mapper config time via strings.
from app.models.attack import Attack as Attack  # noqa: E402, F401
