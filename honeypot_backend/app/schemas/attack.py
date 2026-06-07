from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from datetime import datetime
import uuid

class AttackBase(BaseModel):
    src_ip: str
    src_country: Optional[str] = None
    src_country_code: Optional[str] = None
    src_city: Optional[str] = None
    src_lat: Optional[float] = None
    src_lon: Optional[float] = None
    src_asn: Optional[str] = None
    dst_port: Optional[int] = None
    service: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    command: Optional[str] = None
    severity: Optional[str] = None
    attack_type: Optional[str] = None
    honeypot_type: Optional[str] = None
    session_id: Optional[str] = None
    abuse_confidence: Optional[int] = None
    isp: Optional[str] = None
    usage_type: Optional[str] = None
    total_reports: Optional[int] = None
    reputation: Optional[str] = None
    threat_score: Optional[int] = None

class AttackCreate(AttackBase):
    timestamp: datetime
    raw_log: Optional[Any] = None

class AttackResponse(AttackBase):
    id: uuid.UUID
    timestamp: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class AttackListResponse(BaseModel):
    items: list[AttackResponse]
    total: int
    page: int
    page_size: int
    pages: int

class AttackFilters(BaseModel):
    service: Optional[str] = None
    severity: Optional[str] = None
    src_ip: Optional[str] = None
    country: Optional[str] = None
    attack_type: Optional[str] = None
    honeypot_type: Optional[str] = None
    reputation: Optional[str] = None
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 50
    sort_by: str = "timestamp"
    sort_order: str = "desc"
