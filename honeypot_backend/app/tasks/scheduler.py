import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, desc
from app.db.session import async_session_maker
from app.models.attack import Attack
from app.ai.nim_client import nim_client
from app.alerts.telegram import telegram_alerter, AlertPayload
from app.core.logging import get_logger

logger = get_logger(__name__)

async def hourly_report_loop():
    logger.info("Hourly AI Report loop started.")
    while True:
        try:
            await asyncio.sleep(3600)  # 1 hour
            logger.info("Running hourly AI report...")
            
            async with async_session_maker() as db:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=1)
                
                query = select(Attack).where(Attack.timestamp >= start_time).order_by(desc(Attack.timestamp)).limit(50)
                result = await db.execute(query)
                recent_attacks = list(result.scalars().all())
                
                if not recent_attacks:
                    logger.info("No attacks in the last hour. Skipping hourly report.")
                    continue
                
                # Format for NIM
                attacks_data = [
                    {
                        "id": str(a.id),
                        "timestamp": str(a.timestamp),
                        "src_ip": a.src_ip,
                        "dst_port": a.dst_port,
                        "service": a.service,
                        "attack_type": a.attack_type,
                    } for a in recent_attacks
                ]
                
                context_str = "Generate a brief executive summary of these attacks from the last hour."
                
                report_data, model_used, prompt_version = await nim_client.investigate_incident(
                    attacks_data, 
                    context_str
                )
                
                summary = report_data.get("summary", "No summary generated.")
                recommendations = "\n".join(report_data.get("recommended_actions", []))
                
                message = f"<b>📈 Hourly SOC Report</b>\n\n<b>Attacks Last Hour:</b> {len(recent_attacks)}\n\n<b>AI Summary:</b>\n{summary}\n\n<b>Recommendations:</b>\n{recommendations}"
                
                payload = AlertPayload(
                    attack_id="hourly_report",
                    src_ip="0.0.0.0",
                    alert_type="hourly_summary",
                    severity="info",
                    message=message
                )
                
                await telegram_alerter.send_alert(payload)
                
        except asyncio.CancelledError:
            logger.info("Hourly report loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in hourly report loop: {e}")
            await asyncio.sleep(60) # Wait a bit before retrying on error
