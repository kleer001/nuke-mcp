"""3D scene tools — camera, geometry, ScanlineRender, projection. NukeX-gated."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nukemcp.tools._helpers import create_node as _create, connect_nodes as _connect

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    if not server.version.is_nukex:
        return

    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def create_3d_scene(name: str = "scene") -> dict:
        """Create a Scene node for 3D compositing.

        Args:
            name: Name for the Scene node.
        """
        return conn.send_command("create_node", {"node_class": "Scene", "name": name})

    @mcp.tool()
    def setup_camera(
        name: str = "camera",
        focal_length: float = 50.0,
        haperture: float = 36.0,
    ) -> dict:
        """Create and configure a Camera node.

        Args:
            name: Name for the Camera node.
            focal_length: Focal length in mm.
            haperture: Horizontal aperture in mm.
        """
        return conn.send_command("create_node", {
            "node_class": "Camera3",
            "name": name,
            "knobs": {"focal": focal_length, "haperture": haperture},
        })

    @mcp.tool()
    def setup_scanline_render(
        scene_node: str,
        camera_node: str,
        name: str = "scanline_render",
    ) -> dict:
        """Create a ScanlineRender node connected to a scene and camera.

        Args:
            scene_node: Name of the Scene node.
            camera_node: Name of the Camera node.
            name: Name for the ScanlineRender node.
        """
        sr_name = _create(conn, "ScanlineRender", name)
        _connect(conn, scene_node, sr_name, 0)
        _connect(conn, camera_node, sr_name, 1)
        return {"node": sr_name, "scene": scene_node, "camera": camera_node}

    @mcp.tool()
    def setup_projection(
        source_node: str,
        camera_node: str,
        name_prefix: str = "proj",
    ) -> dict:
        """Set up a camera projection workflow.

        Creates a Project3D node connected to the source image and camera.

        Args:
            source_node: Image node to project.
            camera_node: Camera node defining the projection.
            name_prefix: Prefix for node names.
        """
        proj_name = _create(conn, "Project3D2", f"{name_prefix}_project3d")
        _connect(conn, source_node, proj_name, 0)
        _connect(conn, camera_node, proj_name, 1)
        return {"node": proj_name, "source": source_node, "camera": camera_node}
