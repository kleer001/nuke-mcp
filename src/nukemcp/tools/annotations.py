"""Annotations API — programmatic annotation creation. Nuke 17+ gated."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    if not server.version.at_least(17):
        return

    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def create_annotation(
        text: str,
        position: list[int] | None = None,
        color: list[float] | None = None,
        name: str = "annotation",
    ) -> dict:
        """Create an annotation (sticky note) in the node graph.

        Requires Nuke 17+.

        Args:
            text: The annotation text (supports markdown).
            position: Optional [x, y] position in the node graph.
            color: Optional [r, g, b] color (0.0-1.0).
            name: Name for the annotation node.
        """
        params = {"text": text, "name": name}
        if position:
            params["position"] = position
        if color:
            params["color"] = color
        return conn.send_command("create_annotation", params)

    @mcp.tool(annotations={"readOnlyHint": True})
    def list_annotations() -> dict:
        """List all annotations in the current script."""
        return conn.send_command("list_annotations")
