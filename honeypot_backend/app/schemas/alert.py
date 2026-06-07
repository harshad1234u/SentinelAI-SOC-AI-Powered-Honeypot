from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class AlertResponse(BaseModel):
    id: uuid.UUID
    alert_type: str
    src_ip: str
    severity: str
    message: str
    sent_at: datetime
    status: str
    
    class Config:
        from_attributes = True

class AlertTestRequest(BaseModel):
    message: Optional[str] = None
