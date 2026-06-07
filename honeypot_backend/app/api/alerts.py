from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.alert import AlertResponse, AlertTestRequest
from app.middleware.auth import get_current_user
from app.alerts.telegram import telegram_alerter, AlertPayload
import uuid

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/test")
async def test_alert(request: AlertTestRequest):
    payload = AlertPayload(
        attack_id=str(uuid.uuid4()),
        src_ip="8.8.8.8",
        alert_type="test",
        severity="medium",
        message=request.message or "This is a test alert from the Honeypot SOC."
    )
    success = await telegram_alerter.send_alert(payload)
    return {"success": success}

@router.get("/history", response_model=list[AlertResponse])
async def get_alert_history(db: AsyncSession = Depends(get_db)):
    # Placeholder
    return []
