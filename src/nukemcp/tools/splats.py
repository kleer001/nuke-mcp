"""Gaussian Splat tools — import, render setup. Nuke 17+ gated."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nukemcp.tools._helpers import create_node as _create, connect_nodes as _connect

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    if not server.version.at_least(17):
        return  # Gaussian Splats require Nuke 17+

    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def import_splat(
        file_path: str,
        name: str = "splat_read",
    ) -> dict:
        """Import a Gaussian Splat file (.ply or .splat).

        Requires Nuke 17+.

        Args:
            file_path: Path to the .ply or .splat file.
            name: Name for the Read node.
        """
        node = _create(conn, "Read", name, {"file": file_path})
        return {"node": node, "file_path": file_path}

    @mcp.tool()
    def setup_splat_render(
        splat_node: str,
        camera_node: str,
        name: str = "splat_render",
    ) -> dict:
        """Set up a SplatRender node to render Gaussian Splats.

        Requires Nuke 17+.

        Args:
            splat_node: Node containing the splat data.
            camera_node: Camera node for the render viewpoint.
            name: Name for the SplatRender node.
        """
        sr = _create(conn, "SplatRender", name)
        _connect(conn, splat_node, sr, 0)
        _connect(conn, camera_node, sr, 1)
        return {"node": sr, "splat": splat_node, "camera": camera_node}
