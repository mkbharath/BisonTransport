"""Local event bus adapter using in-process asyncio pub/sub."""

import asyncio
import logging
import uuid
from collections import defaultdict
from typing import Any, Callable, Coroutine

from order_shared.adapters.base import Event, EventBusAdapter

logger = logging.getLogger(__name__)

# Type alias for event handler callbacks
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class LocalEventBusAdapter(EventBusAdapter):
    """In-process event bus using asyncio for local development.

    Replaces AWS EventBridge. Events are dispatched to registered
    handlers immediately within the same process.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._event_log: list[Event] = []

    async def publish_event(self, event: Event) -> str:
        event_id = str(uuid.uuid4())
        self._event_log.append(event)
        logger.info(f"Event published: {event.detail_type} from {event.source} ({event_id})")

        # Dispatch to subscribers
        handlers = self._subscribers.get(event.detail_type, [])
        for handler in handlers:
            try:
                asyncio.create_task(handler(event))
            except Exception as e:
                logger.error(f"Error in event handler for {event.detail_type}: {e}")

        return event_id

    async def subscribe(self, detail_type: str, callback: Any) -> None:
        self._subscribers[detail_type].append(callback)
        logger.info(f"Subscribed to event: {detail_type}")

    def get_event_log(self) -> list[Event]:
        """Get all published events (useful for testing)."""
        return self._event_log.copy()

    def clear_event_log(self) -> None:
        """Clear the event log (useful for testing)."""
        self._event_log.clear()
