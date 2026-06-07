"""
SQLAlchemy declarative base and shared timestamp mixin.

Every model inherits ``TimestampMixin`` (via ``Base``) to get:
- ``id``          — UUID primary key (generated server-side)
- ``created_at``  — timezone-aware creation timestamp
- ``updated_at``  — timezone-aware last-modified timestamp
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy.sql import func


class TimestampMixin:
    """Mixin that adds UUID primary key and audit timestamps."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
        comment="Primary key (UUID v4)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Row creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        comment="Last update timestamp (UTC)",
    )


class Base(TimestampMixin, DeclarativeBase):
    """Application-wide declarative base.

    All ORM models should inherit from this class, which provides
    the common ``id``, ``created_at``, and ``updated_at`` columns.
    """

    __abstract__ = True
