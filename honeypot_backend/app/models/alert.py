"""
Alert model — tracks Telegram and other alert notifications.

Supports cooldown tracking to prevent alert fatigue.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Alert(Base):
    """Outbound alert notification record."""

    __tablename__ = "alerts"

    alert_type: Mapped[str | None] = mapped_column(
        String(50),
        comment="Notification channel: telegram / email / webhook",
    )
    src_ip: Mapped[str | None] = mapped_column(
        String(45),
        comment="Source IP that triggered the alert",
    )
    severity: Mapped[str | None] = mapped_column(
        String(20),
        comment="Severity that triggered the alert",
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        comment="Alert message body",
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="When the alert was dispatched",
    )
    status: Mapped[str | None] = mapped_column(
        String(20),
        comment="Delivery status: sent / failed / suppressed",
    )
    cooldown_key: Mapped[str | None] = mapped_column(
        String(100),
        comment="De-duplication key for cooldown logic",
    )

    def __repr__(self) -> str:
        return (
            f"<Alert(id={self.id!r}, alert_type={self.alert_type!r}, "
            f"status={self.status!r})>"
        )
