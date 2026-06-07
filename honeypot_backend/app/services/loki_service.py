import asyncio
import httpx
import json
from datetime import datetime
from typing import Any
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class LokiService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.LOKI_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        self.semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests to Loki

    async def close(self):
        await self.client.aclose()

    def _datetime_to_ns(self, dt: datetime) -> int:
        return int(dt.timestamp() * 1e9)

    async def query_range(self, query: str, start: datetime, end: datetime, limit: int = 1000, direction: str = "forward") -> list[dict[str, Any]]:
        url = "/loki/api/v1/query_range"
        params = {
            "query": query,
            "start": self._datetime_to_ns(start),
            "end": self._datetime_to_ns(end),
            "limit": limit,
            "direction": direction,
        }

        retries = 3
        backoff = 1.0

        for attempt in range(retries):
            try:
                async with self.semaphore:
                    response = await self.client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    results = []
                    if data.get("status") == "success":
                        result_type = data["data"]["resultType"]
                        if result_type == "streams":
                            for stream in data["data"]["result"]:
                                stream_labels = stream["stream"]
                                for timestamp, log_line in stream["values"]:
                                    try:
                                        log_dict = json.loads(log_line)
                                        log_dict["_loki_timestamp"] = timestamp
                                        log_dict["_loki_labels"] = stream_labels
                                        results.append(log_dict)
                                    except json.JSONDecodeError:
                                        logger.warning("Failed to decode log line as JSON", log_line=log_line)
                    return results

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.error("Loki query failed", error=str(e), attempt=attempt+1, query=query)
                if attempt == retries - 1:
                    return []  # Graceful degradation
                await asyncio.sleep(backoff)
                backoff *= 2

        return []

    async def query_cowrie_logs(self, start: datetime, end: datetime, filters: dict = None) -> list[dict[str, Any]]:
        query = '{job="cowrie"}'
        return await self.query_range(query, start, end)

    async def query_opencanary_logs(self, start: datetime, end: datetime, filters: dict = None) -> list[dict[str, Any]]:
        query = '{job="opencanary"}'
        return await self.query_range(query, start, end)

    async def query_all_attacks(self, start: datetime, end: datetime, service: str = None, severity: str = None) -> list[dict[str, Any]]:
        # In a real scenario, we might use LogQL to filter service/severity if they are labels.
        # Here we just fetch both jobs.
        query = '{job=~"cowrie|opencanary"}'
        return await self.query_range(query, start, end)

loki_service = LokiService()
