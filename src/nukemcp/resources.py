"""MCP Resources — expose read-only scene state as contextual data for the AI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection

    @mcp.resource("nuke://script/info")
    def script_info() -> str:
        """Current script metadata: name, frame range, FPS, colorspace, node count."""
        r = conn.send_command("get_script_info")
        return (
            f"Script: {r.get('name', 'unknown')}\n"
            f"Frame Range: {r.get('frame_range', [0, 0])}\n"
            f"FPS: {r.get('fps', 24)}\n"
            f"Colorspace: {r.get('colorspace', 'unknown')}\n"
            f"Format: {r.get('format', 'unknown')}\n"
            f"Node Count: {r.get('node_count', 0)}"
        )

    @mcp.resource("nuke://script/nodes")
    def script_nodes() -> str:
        """Overview of all nodes in the current script."""
        r = conn.send_command("find_nodes_by_type", {"node_class": "*"})
        if isinstance(r, dict) and "nodes" in r:
            lines = [f"- {n['name']} ({n['class']})" for n in r["nodes"]]
            return f"Nodes ({len(r['nodes'])}):\n" + "\n".join(lines)
        return str(r)

    @mcp.resource("nuke://script/errors")
    def script_errors() -> str:
        """Nodes with errors or warnings in the current script."""
        r = conn.send_command("find_error_nodes")
        if isinstance(r, dict) and "nodes" in r:
            if not r["nodes"]:
                return "No errors found."
            lines = [f"- {n['name']}: {n.get('error', 'unknown error')}" for n in r["nodes"]]
            return f"Error nodes ({len(r['nodes'])}):\n" + "\n".join(lines)
        return str(r)
