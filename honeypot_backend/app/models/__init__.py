"""
Models package — imports every ORM model so Alembic can auto-detect them.

Usage::

    from app.models import Attack, AIAnalysis, Alert, CountryStat, HoneypotSession
"""

from app.models.attack import Attack
from app.models.ai_analysis import AIAnalysis
from app.models.alert import Alert
from app.models.country_stat import CountryStat
from app.models.session import HoneypotSession

__all__ = [
    "Attack",
    "AIAnalysis",
    "Alert",
    "CountryStat",
    "HoneypotSession",
]
