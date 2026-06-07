from app.core.logging import get_logger
from app.alerts.telegram import telegram_alerter, AlertPayload
import asyncio

logger = get_logger(__name__)

async def send_telegram_alert(payload_dict: dict):
    logger.info(f"Worker sending telegram alert for {payload_dict.get('attack_id')}")
    try:
        payload = AlertPayload(**payload_dict)
        await telegram_alerter.send_alert(payload)
    except Exception as e:
        logger.error(f"Failed to send telegram alert in worker: {e}")
