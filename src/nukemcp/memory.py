"""Persistent memory — read/write facility, project, and correction data across sessions."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer

MEMORY_DIR = Path(__file__).parent.parent.parent / "memory"


def _safe_path(rel_path: str) -> Path:
    """Resolve a relative path within MEMORY_DIR, rejecting traversal attempts."""
    fp = (MEMORY_DIR / rel_path).resolve()
    if not fp.is_relative_to(MEMORY_DIR.resolve()):
        raise ValueError(f"Path traversal rejected: {rel_path}")
    return fp


def read_file(rel_path: str) -> str | None:
    """Read a memory file by relative path. Returns None if not found."""
    fp = _safe_path(rel_path)
    if fp.is_file():
        return fp.read_text(encoding="utf-8")
    return None


def write_file(rel_path: str, content: str):
    """Write content to a memory file by relative path."""
    fp = _safe_path(rel_path)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")


def append_file(rel_path: str, entry: str):
    """Append an entry to a memory file."""
    fp = _safe_path(rel_path)
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def list_files() -> list[str]:
    """List all files in the memory directory as relative paths."""
    if not MEMORY_DIR.exists():
        return []
    result = []
    for root, _dirs, files in os.walk(MEMORY_DIR):
        for fname in files:
            full = Path(root) / fname
            result.append(str(full.relative_to(MEMORY_DIR)))
    return sorted(result)


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool(annotations={"readOnlyHint": True})
    def read_memory(file_path: str) -> dict:
        """Read a memory file.

        Memory files store persistent knowledge across sessions: facility conventions,
        project settings, node notes, and past corrections.

        Args:
            file_path: Relative path within the memory directory
                       (e.g., "facility.md", "project/MY_SHOW.md", "corrections.md").
        """
        content = read_file(file_path)
        if content is None:
            return {"found": False, "file_path": file_path}
        return {"found": True, "file_path": file_path, "content": content}

    @mcp.tool()
    def write_memory(file_path: str, content: str) -> dict:
        """Write or overwrite a memory file.

        Use this to store facility conventions, project notes, or node-specific knowledge
        that should persist across sessions.

        Args:
            file_path: Relative path within the memory directory.
            content: Full content to write.
        """
        write_file(file_path, content)
        return {"written": file_path}

    @mcp.tool()
    def log_correction(what_was_wrong: str, what_is_correct: str, context: str = "") -> dict:
        """Log a correction made by the compositor.

        When the user corrects you, call this to remember the correction for future sessions.

        Args:
            what_was_wrong: What the AI did or assumed incorrectly.
            what_is_correct: The correct approach or value.
            context: Optional context (e.g., node type, workflow step).
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        entry = f"- [{timestamp}] **{what_was_wrong}** -> {what_is_correct}"
        if context:
            entry += f" (context: {context})"
        append_file("corrections.md", entry)
        return {"logged": True, "entry": entry}

    @mcp.tool(annotations={"readOnlyHint": True})
    def list_memory() -> dict:
        """List all files in the memory directory."""
        return {"files": list_files()}

    @mcp.tool()
    def update_project_memory(project_name: str) -> dict:
        """Auto-populate project memory from the current Nuke script settings.

        Reads the current script's frame range, FPS, colorspace, and resolution,
        then writes them to memory/project/{project_name}.md.

        Args:
            project_name: Name of the project (used as filename).
        """
        info = conn.send_command("get_script_info")
        content = (
            f"# {project_name}\n\n"
            f"- **Script:** {info.get('name', 'unknown')}\n"
            f"- **Frame Range:** {info.get('frame_range', [0, 0])}\n"
            f"- **FPS:** {info.get('fps', 24)}\n"
            f"- **Colorspace:** {info.get('colorspace', 'unknown')}\n"
            f"- **Format:** {info.get('format', 'unknown')}\n"
            f"- **Node Count:** {info.get('node_count', 0)}\n"
        )
        write_file(f"project/{project_name}.md", content)
        return {"written": f"project/{project_name}.md", "info": info}
