"""Tracking tools — 2D tracking, camera tracking, stabilization. NukeX-gated."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    if not server.version.is_nukex:
        return

    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def create_tracker(source_node: str, name: str = "tracker") -> dict:
        """Create a Tracker node connected to a source.

        Requires NukeX.

        Args:
            source_node: Node to track.
            name: Name for the Tracker node.
        """
        return conn.send_command("create_tracker", {"source_node": source_node, "name": name})

    @mcp.tool(annotations={"destructiveHint": True})
    def solve_tracker(
        tracker_node: str,
        first_frame: int | None = None,
        last_frame: int | None = None,
        confirm: bool = False,
    ) -> dict:
        """Run the tracking solve on a Tracker node.

        This can be a long operation. Requires confirmation.

        Args:
            tracker_node: Name of the Tracker node to solve.
            first_frame: Start frame (defaults to script range).
            last_frame: End frame (defaults to script range).
            confirm: Must be True to proceed.
        """
        if not confirm:
            return {
                "action": "solve_tracker",
                "tracker_node": tracker_node,
                "message": "This will run a tracking solve. Confirm to proceed.",
            }
        params = {"tracker_node": tracker_node}
        if first_frame is not None:
            params["first_frame"] = first_frame
        if last_frame is not None:
            params["last_frame"] = last_frame
        return conn.send_command("solve_tracker", params, timeout=3600.0)

    @mcp.tool()
    def setup_stabilize(source_node: str, tracker_node: str, name: str = "stabilize") -> dict:
        """Set up a stabilization using tracking data from a Tracker node.

        Args:
            source_node: Node to stabilize.
            tracker_node: Tracker node with solved tracking data.
            name: Name for the stabilize node.
        """
        return conn.send_command("setup_stabilize", {
            "source_node": source_node, "tracker_node": tracker_node, "name": name,
        })

    @mcp.tool()
    def create_camera_tracker(source_node: str, name: str = "camera_tracker") -> dict:
        """Create a CameraTracker node for 3D camera solving.

        Requires NukeX.

        Args:
            source_node: Node to track (plate footage).
            name: Name for the CameraTracker node.
        """
        return conn.send_command("create_camera_tracker", {
            "source_node": source_node, "name": name,
        })
