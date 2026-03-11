"""Toolset and LiveGroup management — load, save, list."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool(annotations={"readOnlyHint": True})
    def list_toolsets() -> dict:
        """List available toolsets (saved node presets) in the Nuke environment."""
        return conn.send_command("list_toolsets")

    @mcp.tool()
    def load_toolset(name: str) -> dict:
        """Load a toolset (preset node template) into the current script.

        Args:
            name: Name of the toolset to load.
        """
        return conn.send_command("load_toolset", {"name": name})

    @mcp.tool(annotations={"destructiveHint": True})
    def save_toolset(node_names: list[str], name: str, confirm: bool = False) -> dict:
        """Save selected nodes as a reusable toolset.

        Args:
            node_names: List of node names to include in the toolset.
            name: Name for the saved toolset.
            confirm: Must be True to proceed (overwrites existing toolset of same name).
        """
        if not confirm:
            return {
                "action": "save_toolset",
                "name": name,
                "nodes": node_names,
                "message": (
                    f"This will save {len(node_names)} nodes as toolset '{name}'. "
                    "Ask the user to confirm, then call again with confirm=True."
                ),
            }
        return conn.send_command("save_toolset", {"node_names": node_names, "name": name})

    @mcp.tool()
    def create_live_group(
        node_names: list[str],
        name: str = "LiveGroup1",
        file_path: str | None = None,
    ) -> dict:
        """Create a LiveGroup from selected nodes.

        LiveGroups are reusable, version-controlled node groups that can be
        shared across scripts.

        Args:
            node_names: Nodes to include in the LiveGroup.
            name: Name for the LiveGroup node.
            file_path: Optional path to save the LiveGroup file.
        """
        params = {"node_names": node_names, "name": name}
        if file_path:
            params["file_path"] = file_path
        return conn.send_command("create_live_group", params)
