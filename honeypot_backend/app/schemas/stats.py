from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ServiceCount(BaseModel):
    service: str
    count: int

class DashboardStats(BaseModel):
    total_attacks: int
    attacks_today: int
    unique_ips: int
    unique_countries: int
    top_services: list[ServiceCount]
    severity_breakdown: dict[str, int]

class TopAttacker(BaseModel):
    src_ip: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    attack_count: int
    last_seen: datetime
    services: list[str]
    reputation: str
    abuse_confidence: int

class CountryStats(BaseModel):
    country: str
    country_code: str
    count: int
    lat: Optional[float] = None
    lon: Optional[float] = None

class TimelineBucket(BaseModel):
    timestamp: datetime
    count: int
    severity_breakdown: dict[str, int]
