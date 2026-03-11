"""Render tools — Write node setup, rendering, proxy mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nukemcp.tools._helpers import create_node as _create, connect_nodes as _connect

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def setup_write_node(
        source_node: str,
        file_path: str,
        file_type: str = "exr",
        name: str = "write_out",
        channels: str = "rgba",
        colorspace: str | None = None,
    ) -> dict:
        """Create and connect a Write node for rendering output.

        Args:
            source_node: Node to connect as input.
            file_path: Output file path (use #### or %04d for frame padding).
            file_type: Output format — "exr", "dpx", "jpg", "png", "mov".
            name: Name for the Write node.
            channels: Channels to render (default "rgba").
            colorspace: Optional output colorspace override.
        """
        knobs = {"file": file_path, "file_type": file_type, "channels": channels}
        if colorspace:
            knobs["colorspace"] = colorspace
        write = _create(conn, "Write", name, knobs)
        _connect(conn, source_node, write)
        return {"node": write, "file_path": file_path, "file_type": file_type}

    @mcp.tool(annotations={"destructiveHint": True})
    def render_frames(
        write_node: str,
        first_frame: int | None = None,
        last_frame: int | None = None,
        confirm: bool = False,
    ) -> dict:
        """Render frames from a Write node.

        This triggers rendering and may take a long time. Requires confirmation.

        Args:
            write_node: Name of the Write node to render.
            first_frame: Start frame (defaults to script range).
            last_frame: End frame (defaults to script range).
            confirm: Must be True to proceed.
        """
        if not confirm:
            return {
                "action": "render_frames",
                "write_node": write_node,
                "range": [first_frame, last_frame],
                "message": (
                    f"This will render '{write_node}' "
                    f"frames {first_frame or 'script_start'}-{last_frame or 'script_end'}. "
                    "Ask the user to confirm, then call again with confirm=True."
                ),
            }
        params = {"write_node": write_node}
        if first_frame is not None:
            params["first_frame"] = first_frame
        if last_frame is not None:
            params["last_frame"] = last_frame
        return conn.send_command("render_frames", params, timeout=3600.0)

    @mcp.tool()
    def set_proxy_mode(enabled: bool) -> dict:
        """Enable or disable proxy mode for the script.

        Args:
            enabled: True to enable proxy mode, False to disable.
        """
        return conn.send_command("set_proxy_mode", {"enabled": enabled})
