"""
CountryStat model — pre-aggregated per-country attack statistics.

Used by the globe / map visualisation and geographic analytics.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CountryStat(Base):
    """Aggregated attack statistics by country."""

    __tablename__ = "country_stats"

    country_code: Mapped[str] = mapped_column(
        String(3),
        unique=True,
        nullable=False,
        comment="ISO 3166-1 alpha-2 country code",
    )
    country_name: Mapped[str | None] = mapped_column(
        String(100),
        comment="Full country name",
    )
    attack_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="Total attacks from this country",
    )
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="Timestamp of the most recent attack from this country",
    )
    lat: Mapped[float | None] = mapped_column(
        Float,
        comment="Country centroid latitude",
    )
    lon: Mapped[float | None] = mapped_column(
        Float,
        comment="Country centroid longitude",
    )

    def __repr__(self) -> str:
        return (
            f"<CountryStat(country_code={self.country_code!r}, "
            f"attack_count={self.attack_count!r})>"
        )
