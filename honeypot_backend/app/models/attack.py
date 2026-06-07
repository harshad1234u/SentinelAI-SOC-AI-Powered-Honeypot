"""
Attack model — primary log table for honeypot events.

Each row represents a single observed attack event, enriched with
geolocation, threat intelligence, and abuse data.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Attack(Base):
    """Honeypot attack event record."""

    __tablename__ = "attacks"

    # ── Timestamp & source ───────────────────────────────────────────────
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
        comment="When the attack was observed",
    )

    src_ip: Mapped[str] = mapped_column(
        String(45),
        index=True,
        nullable=False,
        comment="Source IP address (v4 or v6)",
    )

    # ── Geolocation ──────────────────────────────────────────────────────
    src_country: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        comment="Resolved source country name",
    )
    src_country_code: Mapped[str | None] = mapped_column(
        String(3),
        comment="ISO 3166-1 alpha-2 country code",
    )
    src_city: Mapped[str | None] = mapped_column(
        String(100),
        comment="Resolved source city",
    )
    src_lat: Mapped[float | None] = mapped_column(
        Float,
        comment="Source latitude",
    )
    src_lon: Mapped[float | None] = mapped_column(
        Float,
        comment="Source longitude",
    )
    src_asn: Mapped[str | None] = mapped_column(
        String(200),
        comment="Autonomous System Name / Number",
    )

    # ── Connection details ───────────────────────────────────────────────
    dst_port: Mapped[int | None] = mapped_column(
        Integer,
        comment="Destination port targeted",
    )
    service: Mapped[str | None] = mapped_column(
        String(50),
        index=True,
        comment="Service name (ssh, telnet, http, …)",
    )
    username: Mapped[str | None] = mapped_column(
        String(255),
        comment="Attempted username",
    )
    password: Mapped[str | None] = mapped_column(
        String(255),
        comment="Attempted password",
    )
    command: Mapped[str | None] = mapped_column(
        Text,
        comment="Command executed in the honeypot shell",
    )

    # ── Classification ───────────────────────────────────────────────────
    severity: Mapped[str | None] = mapped_column(
        String(20),
        index=True,
        comment="Severity level: low / medium / high / critical",
    )
    attack_type: Mapped[str | None] = mapped_column(
        String(100),
        comment="Attack classification (brute_force, exploit, …)",
    )
    honeypot_type: Mapped[str | None] = mapped_column(
        String(20),
        index=True,
        comment="Honeypot source: cowrie / opencanary",
    )
    session_id: Mapped[str | None] = mapped_column(
        String(100),
        comment="Honeypot session identifier",
    )

    # ── Raw data ─────────────────────────────────────────────────────────
    raw_log: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        comment="Original un-parsed log entry",
    )
    vector_indexed: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        default=False,
        comment="Whether this row has been embedded into Qdrant",
    )

    # ── Threat intelligence ──────────────────────────────────────────────
    abuse_confidence: Mapped[int | None] = mapped_column(
        Integer,
        comment="AbuseIPDB confidence score 0-100",
    )
    isp: Mapped[str | None] = mapped_column(
        String(200),
        comment="ISP reported by AbuseIPDB",
    )
    usage_type: Mapped[str | None] = mapped_column(
        String(100),
        comment="IP usage type (Data Center, ISP, …)",
    )
    total_reports: Mapped[int | None] = mapped_column(
        Integer,
        comment="Total abuse reports in AbuseIPDB",
    )
    reputation: Mapped[str | None] = mapped_column(
        String(20),
        index=True,
        comment="Reputation label: clean / suspicious / malicious",
    )

    # ── Unified threat score ─────────────────────────────────────────────
    threat_score: Mapped[int | None] = mapped_column(
        Integer,
        index=True,
        comment="Unified 0-100 composite threat score",
    )

    # ── Relationships ────────────────────────────────────────────────────
    ai_analyses: Mapped[list["AIAnalysis"]] = relationship(
        "AIAnalysis",
        back_populates="attack",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ── Composite indexes ────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_attacks_timestamp_severity", "timestamp", "severity"),
        Index("ix_attacks_timestamp_threat_score", "timestamp", "threat_score"),
    )

    def __repr__(self) -> str:
        return (
            f"<Attack(id={self.id!r}, src_ip={self.src_ip!r}, "
            f"timestamp={self.timestamp!r}, severity={self.severity!r})>"
        )


# Avoid circular-import issues — the string "AIAnalysis" is resolved at mapper
# configuration time.  We import the type here solely for IDE support.
from app.models.ai_analysis import AIAnalysis as AIAnalysis  # noqa: E402, F401
