"""Bidirectional events — receive and surface scene change events from the Nuke addon."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer

EVENT_TYPES = [
    "node_created",
    "node_deleted",
    "node_renamed",
    "knob_changed",
    "script_loaded",
    "script_saved",
    "frame_changed",
    "cook_error",
]


class EventLog:
    """Stores recent events received from the Nuke addon."""

    def __init__(self, max_events: int = 100):
        self.events: list[dict] = []
        self.max_events = max_events
        self.subscriptions: set[str] = set()

    def subscribe(self, event_types: list[str] | None = None):
        """Subscribe to event types. None means all."""
        if event_types is None:
            self.subscriptions = set(EVENT_TYPES)
        else:
            self.subscriptions = set(event_types) & set(EVENT_TYPES)

    def add(self, event: dict):
        """Add an event if we're subscribed to its type."""
        if event.get("event_type", "") not in self.subscriptions:
            return
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

    def get_recent(self, count: int = 20) -> list[dict]:
        return self.events[-count:]

    def clear(self):
        self.events.clear()


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection
    event_log = EventLog()
    server.event_log = event_log

    @mcp.tool()
    def subscribe_events(event_types: list[str] | None = None) -> dict:
        """Subscribe to Nuke scene change events.

        Once subscribed, events are logged and can be retrieved with get_events.

        Args:
            event_types: List of event types to subscribe to. Pass None for all.
                         Available: node_created, node_deleted, node_renamed,
                         knob_changed, script_loaded, script_saved, frame_changed, cook_error.
        """
        event_log.subscribe(event_types)
        conn.send_command("subscribe_events", {"event_types": list(event_log.subscriptions)})
        return {"subscribed": list(event_log.subscriptions)}

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_events(count: int = 20) -> dict:
        """Get recent scene change events from the Nuke addon.

        Args:
            count: Number of recent events to return (default 20).
        """
        return {"events": event_log.get_recent(count)}

    @mcp.tool()
    def clear_events() -> dict:
        """Clear the event log."""
        event_log.clear()
        return {"cleared": True}
