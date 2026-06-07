import asyncio
import httpx
from pydantic import BaseModel
from typing import Any
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.cache_service import cache_service

logger = get_logger(__name__)

class AlertPayload(BaseModel):
    attack_id: str
    src_ip: str
    alert_type: str
    severity: str
    message: str

class TelegramAlerter:
    def __init__(self):
        self.settings = get_settings()
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.http_client.aclose()

    def format_attack_alert(self, attack: Any, ai_summary: str = "No summary available.") -> str:
        rep_emoji = "🔴" if attack.reputation in ["high", "critical"] else "🟡" if attack.reputation == "medium" else "🟢"
        sev_emoji = "🔴" if attack.severity in ["high", "critical"] else "🟡" if attack.severity == "medium" else "🟢"
        
        service_name = attack.service
        if not service_name and attack.dst_port:
            port_map = {
                22: "SSH", 2222: "SSH (Cowrie)", 23: "Telnet",
                80: "HTTP", 443: "HTTPS", 445: "SMB", 3389: "RDP",
                21: "FTP", 25: "SMTP", 53: "DNS", 3306: "MySQL", 6379: "Redis",
                5900: "VNC", 8080: "HTTP", 1433: "MSSQL"
            }
            service_name = port_map.get(attack.dst_port)
        service_str = service_name.upper() if service_name else 'UNKNOWN'

        username_str = attack.username
        if not username_str and getattr(attack, 'raw_log', None):
            username_str = attack.raw_log.get('username') or attack.raw_log.get('login')
        username_str = username_str or 'N/A'

        if ai_summary == "No summary available.":
            ai_summary = "Analysis pending... (Check dashboard for updates)"

        return f"""<b>🚨 Honeypot Alert</b>

<b>Source IP:</b> <code>{attack.src_ip}</code>
<b>Country:</b> {attack.src_country}
<b>ISP:</b> {attack.isp or 'Unknown'}
<b>Reputation:</b> {rep_emoji} {attack.reputation.upper()} (abuse: {attack.abuse_confidence or 0}/100, {attack.total_reports or 0} reports)
<b>Threat Score:</b> {attack.threat_score} ({rep_emoji} {self._get_threat_level(attack.threat_score).upper()})
<b>Service:</b> {service_str}
<b>Port:</b> {attack.dst_port}
<b>Username:</b> {username_str}
<b>Severity:</b> {sev_emoji} {attack.severity.upper()}

<b>AI Summary:</b>
{ai_summary}"""

    def _get_threat_level(self, score: int) -> str:
        if score <= 25: return "low"
        if score <= 50: return "medium"
        if score <= 75: return "high"
        return "critical"

    async def send_alert(self, payload: AlertPayload) -> bool:
        if not self.settings.TELEGRAM_BOT_TOKEN or not self.settings.TELEGRAM_CHAT_ID:
            logger.debug("Telegram credentials not configured, skipping alert")
            return False

        # Cooldown check
        redis = cache_service.redis
        if redis and payload.severity != "critical":
            cooldown_key = f"alert:cooldown:{payload.src_ip}"
            if await redis.get(cooldown_key):
                logger.info(f"Alert for {payload.src_ip} suppressed due to cooldown")
                return False
            await redis.setex(cooldown_key, 300, "1") # 5 min cooldown

        url = f"https://api.telegram.org/bot{self.settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": self.settings.TELEGRAM_CHAT_ID,
            "text": payload.message,
            "parse_mode": "HTML"
        }

        try:
            response = await self.http_client.post(url, json=data)
            if response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                logger.warning(f"Telegram rate limit hit, retry after {retry_after}s")
                await asyncio.sleep(retry_after)
                # Simple one-time retry
                response = await self.http_client.post(url, json=data)
            
            response.raise_for_status()
            logger.info(f"Successfully sent Telegram alert for {payload.src_ip}")
            return True
        except Exception as e:
            logger.error("Failed to send Telegram alert", error=str(e), ip=payload.src_ip)
            return False

telegram_alerter = TelegramAlerter()
