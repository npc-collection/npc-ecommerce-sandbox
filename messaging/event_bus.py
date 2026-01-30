"""Event bus implementation using Redis pub/sub for agent communication."""

import asyncio
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional
from uuid import uuid4

import redis.asyncio as redis

from config import get_settings


class EventType(str, Enum):
    """Types of events in the system."""

    # Order events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"

    # Inventory events
    INVENTORY_LOW = "inventory.low"
    INVENTORY_DEPLETED = "inventory.depleted"
    INVENTORY_REPLENISHED = "inventory.replenished"
    INVENTORY_RESERVED = "inventory.reserved"

    # Price events
    PRICE_CHANGED = "price.changed"
    PRICE_ALERT = "price.alert"

    # Agent events
    AGENT_TASK_STARTED = "agent.task.started"
    AGENT_TASK_COMPLETED = "agent.task.completed"
    AGENT_TASK_FAILED = "agent.task.failed"
    AGENT_MESSAGE = "agent.message"

    # Simulation events
    SIMULATION_STARTED = "simulation.started"
    SIMULATION_STOPPED = "simulation.stopped"
    SIMULATION_EVENT = "simulation.event"

    # Customer events
    CUSTOMER_INQUIRY = "customer.inquiry"
    CUSTOMER_FEEDBACK = "customer.feedback"


@dataclass
class Event:
    """Event data structure."""

    type: EventType
    data: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "system"
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, EventType) else self.type,
            "data": self.data,
            "timestamp": self.timestamp,
            "source": self.source,
            "correlation_id": self.correlation_id,
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        event_type = data.get("type", "")
        try:
            event_type = EventType(event_type)
        except ValueError:
            pass  # Keep as string if not a valid EventType

        return cls(
            id=data.get("id", str(uuid4())),
            type=event_type,
            data=data.get("data", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            source=data.get("source", "system"),
            correlation_id=data.get("correlation_id"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))


# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Redis-based event bus for async agent communication."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize the event bus.

        Args:
            redis_url: Redis connection URL. If not provided, uses settings.
        """
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
        self._local_handlers: Dict[str, List[EventHandler]] = {}
        self._use_redis = True

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            self._pubsub = self._redis.pubsub()
            print(f"[EventBus] Connected to Redis: {self.redis_url}")
        except Exception as e:
            print(f"[EventBus] Redis connection failed: {e}. Using local mode.")
            self._use_redis = False
            self._redis = None
            self._pubsub = None

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self._running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.close()

        if self._redis:
            await self._redis.close()

        print("[EventBus] Disconnected")

    async def publish(self, event: Event) -> None:
        """Publish an event.

        Args:
            event: The event to publish.
        """
        channel = self._get_channel(event.type)
        message = event.to_json()

        if self._use_redis and self._redis:
            await self._redis.publish(channel, message)
            print(f"[EventBus] Published {event.type} to {channel}")
        else:
            # Local mode: directly call handlers
            await self._dispatch_local(event)

    async def _dispatch_local(self, event: Event) -> None:
        """Dispatch event to local handlers (when Redis is not available)."""
        event_type = event.type.value if isinstance(event.type, EventType) else event.type

        # Check exact match handlers
        if event_type in self._local_handlers:
            for handler in self._local_handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    print(f"[EventBus] Handler error: {e}")

        # Check wildcard handlers (e.g., "order.*")
        prefix = event_type.split(".")[0] + ".*"
        if prefix in self._local_handlers:
            for handler in self._local_handlers[prefix]:
                try:
                    await handler(event)
                except Exception as e:
                    print(f"[EventBus] Handler error: {e}")

        # Check global handlers
        if "*" in self._local_handlers:
            for handler in self._local_handlers["*"]:
                try:
                    await handler(event)
                except Exception as e:
                    print(f"[EventBus] Handler error: {e}")

    async def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        """Subscribe to an event type.

        Args:
            event_type: The event type to subscribe to. Can use "*" for all events
                        or "order.*" for all order events.
            handler: Async function to call when event is received.
        """
        if isinstance(event_type, EventType):
            pattern = event_type.value
        else:
            pattern = event_type

        # Store handler locally
        if pattern not in self._local_handlers:
            self._local_handlers[pattern] = []
        self._local_handlers[pattern].append(handler)

        if self._use_redis and self._pubsub:
            channel = self._get_channel(pattern)

            if "*" in pattern:
                await self._pubsub.psubscribe(channel)
            else:
                await self._pubsub.subscribe(channel)

            if pattern not in self._handlers:
                self._handlers[pattern] = []
            self._handlers[pattern].append(handler)

            print(f"[EventBus] Subscribed to {pattern}")

    async def unsubscribe(
        self,
        event_type: EventType | str,
        handler: Optional[EventHandler] = None,
    ) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: The event type to unsubscribe from.
            handler: Specific handler to remove. If None, removes all handlers.
        """
        if isinstance(event_type, EventType):
            pattern = event_type.value
        else:
            pattern = event_type

        # Remove from local handlers
        if pattern in self._local_handlers:
            if handler:
                self._local_handlers[pattern] = [
                    h for h in self._local_handlers[pattern] if h != handler
                ]
            else:
                del self._local_handlers[pattern]

        if self._use_redis and self._pubsub:
            channel = self._get_channel(pattern)

            if "*" in pattern:
                await self._pubsub.punsubscribe(channel)
            else:
                await self._pubsub.unsubscribe(channel)

            if pattern in self._handlers:
                if handler:
                    self._handlers[pattern] = [h for h in self._handlers[pattern] if h != handler]
                else:
                    del self._handlers[pattern]

    async def start_listening(self) -> None:
        """Start the event listener loop."""
        if not self._use_redis or not self._pubsub:
            print("[EventBus] Running in local mode (no Redis)")
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen())
        print("[EventBus] Started listening for events")

    async def _listen(self) -> None:
        """Listen for events from Redis."""
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )

                if message:
                    await self._handle_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[EventBus] Listener error: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle a received message."""
        try:
            data = message.get("data")
            if not data:
                return

            event = Event.from_json(data)
            channel = message.get("channel", "")
            pattern = message.get("pattern")

            # Determine which handlers to call
            event_type = event.type.value if isinstance(event.type, EventType) else event.type

            handlers_to_call = []

            # Exact match handlers
            if event_type in self._handlers:
                handlers_to_call.extend(self._handlers[event_type])

            # Pattern match handlers (e.g., "order.*")
            if pattern:
                pattern_str = pattern.decode() if isinstance(pattern, bytes) else pattern
                if pattern_str in self._handlers:
                    handlers_to_call.extend(self._handlers[pattern_str])

            # Call all matching handlers
            for handler in handlers_to_call:
                try:
                    await handler(event)
                except Exception as e:
                    print(f"[EventBus] Handler error for {event_type}: {e}")

        except json.JSONDecodeError as e:
            print(f"[EventBus] Invalid JSON in message: {e}")
        except Exception as e:
            print(f"[EventBus] Error handling message: {e}")

    def _get_channel(self, event_type: EventType | str) -> str:
        """Get Redis channel name for event type."""
        if isinstance(event_type, EventType):
            return f"events:{event_type.value}"
        return f"events:{event_type}"


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def publish_event(
    event_type: EventType,
    data: Dict[str, Any],
    source: str = "system",
    correlation_id: Optional[str] = None,
) -> Event:
    """Convenience function to publish an event.

    Args:
        event_type: Type of event to publish.
        data: Event data payload.
        source: Source of the event (e.g., "inventory_agent").
        correlation_id: Optional ID to correlate related events.

    Returns:
        The published event.
    """
    event = Event(
        type=event_type,
        data=data,
        source=source,
        correlation_id=correlation_id,
    )

    bus = get_event_bus()
    await bus.publish(event)

    return event


def subscribe(event_type: EventType | str):
    """Decorator to subscribe a function to an event type.

    Usage:
        @subscribe(EventType.ORDER_CREATED)
        async def handle_order_created(event: Event):
            print(f"Order created: {event.data}")
    """

    def decorator(func: EventHandler) -> EventHandler:
        async def register():
            bus = get_event_bus()
            await bus.subscribe(event_type, func)

        # Schedule registration when event loop is running
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(register())
        except RuntimeError:
            # No running loop, will need to register manually
            pass

        return func

    return decorator
