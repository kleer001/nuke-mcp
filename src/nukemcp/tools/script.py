"""Script-level operations — load, save, project settings, frame range."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool(annotations={"destructiveHint": True})
    def load_script(path: str, confirm: bool = False) -> dict:
        """Open a Nuke script file, replacing the current script.

        This is a destructive action — the current script will be replaced.
        You must set confirm=True after getting user confirmation.

        Args:
            path: Path to the .nk script file to open.
            confirm: Must be True to proceed.
        """
        if not confirm:
            return {
                "action": "load_script",
                "path": path,
                "message": (
                    f"This will open '{path}' and replace the current script. "
                    "Any unsaved changes will be lost. "
                    "Ask the user to confirm, then call again with confirm=True."
                ),
            }
        return conn.send_command("load_script", {"path": path})

    @mcp.tool(annotations={"destructiveHint": True})
    def save_script(path: str | None = None, confirm: bool = False) -> dict:
        """Save the current Nuke script.

        When saving to a new path, this overwrites the target file.
        You must set confirm=True after getting user confirmation.

        Args:
            path: Optional path to save to. If not provided, saves to the current path.
            confirm: Must be True to proceed.
        """
        if not confirm:
            return {
                "action": "save_script",
                "path": path,
                "message": (
                    f"This will save the script{f' to {path!r}' if path else ''}. "
                    "Ask the user to confirm, then call again with confirm=True."
                ),
            }
        params = {}
        if path is not None:
            params["path"] = path
        return conn.send_command("save_script", params)

    @mcp.tool(annotations={"idempotentHint": True})
    def set_project_settings(
        fps: float | None = None,
        colorspace: str | None = None,
        resolution: list[int] | None = None,
    ) -> dict:
        """Modify project-level settings on the Root node.

        Args:
            fps: Frames per second.
            colorspace: Color management setting (e.g., "ACES", "Nuke", "OCIO").
            resolution: [width, height] in pixels.
        """
        params = {}
        if fps is not None:
            params["fps"] = fps
        if colorspace is not None:
            params["colorspace"] = colorspace
        if resolution is not None:
            params["resolution"] = resolution
        return conn.send_command("set_project_settings", params)

    @mcp.tool(annotations={"idempotentHint": True})
    def set_frame_range(first: int, last: int) -> dict:
        """Set the script's frame range.

        Args:
            first: First frame number.
            last: Last frame number.
        """
        return conn.send_command("set_frame_range", {"first": first, "last": last})
