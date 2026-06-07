from app.events.dispatcher import event_dispatcher
from app.models.attack import Attack
from app.core.logging import get_logger
import json

# In a full implementation, these would enqueue to RQ
# from redis import Redis
# from rq import Queue

logger = get_logger(__name__)

async def handle_attack_ingested(attack: Attack):
    logger.info(f"Handling attack_ingested event for attack {attack.id}")
    
    # 1. Enqueue realtime analysis
    # q_realtime.enqueue("app.workers.ai_worker.process_realtime_analysis", str(attack.id))
    
    # 2. Enqueue embedding
    # q_maintenance.enqueue("app.workers.rag_worker.embed_and_index_attack", str(attack.id))
    
    # 3. Evaluate alert rules
    import asyncio
    from app.workers.alert_worker import send_telegram_alert
    from app.alerts.telegram import telegram_alerter
    
    try:
        message = telegram_alerter.format_attack_alert(attack)
        payload_dict = {
            "attack_id": str(attack.id),
            "src_ip": attack.src_ip or "0.0.0.0",
            "alert_type": "attack_ingested",
            "severity": attack.severity or "low",
            "message": message
        }
        asyncio.create_task(send_telegram_alert(payload_dict))
    except Exception as e:
        logger.error(f"Failed to enqueue Telegram alert: {e}")
    
    # 4. WebSocket broadcast
    from app.websocket.manager import ws_manager
    from app.schemas.attack import AttackResponse
    # Basic conversion to dict, in reality use Pydantic
    try:
        attack_dict = {
            "id": str(attack.id),
            "src_ip": attack.src_ip,
            "service": attack.service,
            "severity": attack.severity,
            "attack_type": attack.attack_type
        }
        await ws_manager.broadcast({"type": "attack", "data": attack_dict})
    except Exception as e:
        logger.error(f"WebSocket broadcast failed: {e}")

async def handle_ai_analysis_completed(analysis: dict):
    logger.info("AI Analysis completed")
    # Prometheus metric increments would go here

def register_handlers():
    event_dispatcher.subscribe("attack_ingested", handle_attack_ingested)
    event_dispatcher.subscribe("ai_analysis_completed", handle_ai_analysis_completed)
    logger.info("Event handlers registered")
