"""
HoneypotSession model — tracks interactive attacker sessions.

Records the full lifecycle of a honeypot shell session, including
all commands issued and timing data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HoneypotSession(Base):
    """Interactive honeypot session record."""

    __tablename__ = "honeypot_sessions"

    session_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="Honeypot-assigned session identifier",
    )
    src_ip: Mapped[str | None] = mapped_column(
        String(45),
        comment="Source IP of the attacker",
    )
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="Session start timestamp",
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Session end timestamp (null if still active)",
    )
    commands_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="Number of commands executed in the session",
    )
    honeypot_type: Mapped[str | None] = mapped_column(
        String(20),
        comment="Honeypot source: cowrie / opencanary",
    )
    commands_log: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        comment="Ordered list of command entries",
    )

    def __repr__(self) -> str:
        return (
            f"<HoneypotSession(session_id={self.session_id!r}, "
            f"src_ip={self.src_ip!r}, commands_count={self.commands_count!r})>"
        )
