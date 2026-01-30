"""Tests for messaging/event bus module."""

import pytest

from messaging import Event, EventBus, EventType, get_event_bus, publish_event


class TestEventType:
    """Tests for EventType enum."""

    def test_order_event_types(self):
        """Test order-related event types exist."""
        assert EventType.ORDER_CREATED.value == "order.created"
        assert EventType.ORDER_UPDATED.value == "order.updated"
        assert EventType.ORDER_CANCELLED.value == "order.cancelled"
        assert EventType.ORDER_SHIPPED.value == "order.shipped"
        assert EventType.ORDER_DELIVERED.value == "order.delivered"

    def test_inventory_event_types(self):
        """Test inventory-related event types exist."""
        assert EventType.INVENTORY_LOW.value == "inventory.low"
        assert EventType.INVENTORY_DEPLETED.value == "inventory.depleted"
        assert EventType.INVENTORY_REPLENISHED.value == "inventory.replenished"

    def test_agent_event_types(self):
        """Test agent-related event types exist."""
        assert EventType.AGENT_TASK_STARTED.value == "agent.task.started"
        assert EventType.AGENT_TASK_COMPLETED.value == "agent.task.completed"
        assert EventType.AGENT_TASK_FAILED.value == "agent.task.failed"

    def test_simulation_event_types(self):
        """Test simulation-related event types exist."""
        assert EventType.SIMULATION_STARTED.value == "simulation.started"
        assert EventType.SIMULATION_STOPPED.value == "simulation.stopped"


class TestEvent:
    """Tests for Event dataclass."""

    def test_event_creation(self):
        """Test creating an event."""
        event = Event(
            type=EventType.ORDER_CREATED,
            data={"order_id": "123", "total": 99.99},
            source="test",
        )

        assert event.type == EventType.ORDER_CREATED
        assert event.data["order_id"] == "123"
        assert event.source == "test"
        assert event.id is not None
        assert event.timestamp is not None

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = Event(
            type=EventType.INVENTORY_LOW,
            data={"product_id": 1, "quantity": 5},
            source="inventory_agent",
        )

        event_dict = event.to_dict()

        assert event_dict["type"] == "inventory.low"
        assert event_dict["data"]["product_id"] == 1
        assert event_dict["source"] == "inventory_agent"
        assert "id" in event_dict
        assert "timestamp" in event_dict

    def test_event_to_json(self):
        """Test converting event to JSON."""
        event = Event(
            type=EventType.PRICE_CHANGED,
            data={"product_id": 1, "old_price": 100, "new_price": 90},
        )

        json_str = event.to_json()

        assert "price.changed" in json_str
        assert "product_id" in json_str
        assert "old_price" in json_str

    def test_event_from_dict(self):
        """Test creating event from dictionary."""
        data = {
            "id": "test-id",
            "type": "order.created",
            "data": {"order_id": "456"},
            "timestamp": "2024-01-29T12:00:00",
            "source": "api",
        }

        event = Event.from_dict(data)

        assert event.id == "test-id"
        assert event.type == EventType.ORDER_CREATED
        assert event.data["order_id"] == "456"
        assert event.source == "api"

    def test_event_from_json(self):
        """Test creating event from JSON."""
        json_str = (
            '{"id": "test-id", "type": "inventory.low", "data": {"qty": 5}, "source": "test"}'
        )

        event = Event.from_json(json_str)

        assert event.id == "test-id"
        assert event.type == EventType.INVENTORY_LOW
        assert event.data["qty"] == 5

    def test_event_with_correlation_id(self):
        """Test event with correlation ID for tracing."""
        event = Event(
            type=EventType.AGENT_TASK_STARTED,
            data={"task": "check_inventory"},
            correlation_id="corr-123",
        )

        assert event.correlation_id == "corr-123"
        assert event.to_dict()["correlation_id"] == "corr-123"


class TestEventBus:
    """Tests for EventBus class."""

    def test_event_bus_init(self):
        """Test event bus initialization."""
        bus = EventBus()

        assert bus._redis is None
        assert bus._running is False
        assert bus._handlers == {}

    @pytest.mark.asyncio
    async def test_local_mode_publish_subscribe(self):
        """Test publish/subscribe in local mode (no Redis)."""
        bus = EventBus()
        bus._use_redis = False  # Force local mode

        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        await bus.subscribe(EventType.ORDER_CREATED, handler)

        event = Event(
            type=EventType.ORDER_CREATED,
            data={"order_id": "test-123"},
        )
        await bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].data["order_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        """Test wildcard pattern subscription."""
        bus = EventBus()
        bus._use_redis = False

        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        await bus.subscribe("order.*", handler)

        # Publish order.created
        event1 = Event(type=EventType.ORDER_CREATED, data={"id": 1})
        await bus.publish(event1)

        # Publish order.shipped
        event2 = Event(type=EventType.ORDER_SHIPPED, data={"id": 2})
        await bus.publish(event2)

        assert len(received_events) == 2

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        bus._use_redis = False

        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        await bus.subscribe(EventType.INVENTORY_LOW, handler)
        await bus.unsubscribe(EventType.INVENTORY_LOW, handler)

        event = Event(type=EventType.INVENTORY_LOW, data={"product_id": 1})
        await bus.publish(event)

        assert len(received_events) == 0

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        """Test multiple handlers for same event type."""
        bus = EventBus()
        bus._use_redis = False

        handler1_calls = []
        handler2_calls = []

        async def handler1(event: Event):
            handler1_calls.append(event)

        async def handler2(event: Event):
            handler2_calls.append(event)

        await bus.subscribe(EventType.PRICE_CHANGED, handler1)
        await bus.subscribe(EventType.PRICE_CHANGED, handler2)

        event = Event(type=EventType.PRICE_CHANGED, data={"price": 50})
        await bus.publish(event)

        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1


class TestEventBusHelpers:
    """Tests for event bus helper functions."""

    def test_get_event_bus_singleton(self):
        """Test get_event_bus returns singleton."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    @pytest.mark.asyncio
    async def test_publish_event_helper(self):
        """Test publish_event convenience function."""
        bus = get_event_bus()
        bus._use_redis = False

        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        await bus.subscribe(EventType.SIMULATION_STARTED, handler)

        event = await publish_event(
            EventType.SIMULATION_STARTED,
            {"scenario": "flash_sale"},
            source="simulation_engine",
        )

        assert event.type == EventType.SIMULATION_STARTED
        assert event.source == "simulation_engine"
        assert len(received_events) == 1
