"""Messaging module for event-driven communication."""

from .event_bus import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
    publish_event,
    subscribe,
)

__all__ = [
    "EventBus",
    "Event",
    "EventType",
    "get_event_bus",
    "publish_event",
    "subscribe",
]
