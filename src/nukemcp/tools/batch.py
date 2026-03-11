"""Batch operations — bulk knob setting, node search, broken read detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool(annotations={"readOnlyHint": True})
    def find_nodes_by_type(node_class: str) -> dict:
        """Find all nodes of a given type in the script.

        Args:
            node_class: The Nuke node class to search for (e.g., "Grade", "Read", "Write").
        """
        return conn.send_command("find_nodes_by_type", {"node_class": node_class})

    @mcp.tool(annotations={"readOnlyHint": True})
    def find_broken_reads() -> dict:
        """Find all Read nodes with missing or invalid file paths."""
        return conn.send_command("find_broken_reads")

    @mcp.tool()
    def batch_set_knob(
        node_names: list[str],
        knob_name: str,
        value: str | int | float | bool,
    ) -> dict:
        """Set the same knob value on multiple nodes at once.

        Args:
            node_names: List of node names to modify.
            knob_name: The knob to set.
            value: The value to set on all nodes.
        """
        return conn.send_command("batch_set_knob", {
            "node_names": node_names, "knob_name": knob_name, "value": value,
        })

    @mcp.tool()
    def batch_reconnect(
        node_names: list[str],
        new_input: str,
        input_index: int = 0,
    ) -> dict:
        """Reconnect multiple nodes to a new input source.

        Args:
            node_names: List of node names whose inputs should be changed.
            new_input: The node to connect as the new input.
            input_index: Which input slot to reconnect (default 0).
        """
        return conn.send_command("batch_reconnect", {
            "node_names": node_names, "new_input": new_input, "input_index": input_index,
        })
