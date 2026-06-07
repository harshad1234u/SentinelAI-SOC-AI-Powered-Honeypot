import asyncio
from typing import Callable, Any
from app.core.logging import get_logger

logger = get_logger(__name__)

class EventDispatcher:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")

    async def dispatch(self, event_type: str, *args, **kwargs):
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    # Execute in background task
                    asyncio.create_task(self._execute_handler(handler, *args, **kwargs))
                except Exception as e:
                    logger.error(f"Failed to dispatch event {event_type} to handler", error=str(e))

    async def _execute_handler(self, handler: Callable, *args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(*args, **kwargs)
            else:
                handler(*args, **kwargs)
        except Exception as e:
            logger.error(f"Event handler failed", error=str(e))

event_dispatcher = EventDispatcher()
