"""NukeMCP — FastMCP server entry point.

Connects to the Nuke addon (or mock) and exposes tools to AI clients via stdio.
"""

from __future__ import annotations

import argparse
import logging
import sys

from fastmcp import FastMCP

from nukemcp.connection import NukeConnection, DEFAULT_HOST, DEFAULT_PORT
from nukemcp.version import NukeVersion, parse_version
from nukemcp.tools import graph, script, comp, render, templates, batch, tracking, threed, deep, ml, splats, annotations

log = logging.getLogger("nukemcp")


class NukeMCPServer:
    """Holds the FastMCP instance and shared state (connection, version)."""

    def __init__(
        self,
        mcp: FastMCP,
        connection: NukeConnection,
        version: NukeVersion,
        mock_server=None,
    ):
        self.mcp = mcp
        self.connection = connection
        self.version = version
        self.event_log = None  # Set by events.register()
        self._mock_server = mock_server


def build_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    mock: bool = False,
    mock_version: str = "17.0v1",
    mock_variant: str = "NukeX",
) -> FastMCP:
    """Build and configure the FastMCP server.

    If mock=True, starts a mock Nuke socket server for offline development.
    """
    mock_server = None

    if mock:
        from nukemcp.mock import MockNukeServer

        mock_server = MockNukeServer(port=port, nuke_version=mock_version, variant=mock_variant)
        mock_server.start()
        log.info("Mock Nuke server started on port %d (%s %s)", port, mock_variant, mock_version)

    conn = NukeConnection(host, port)

    try:
        handshake = conn.connect()
    except Exception:
        if mock_server:
            mock_server.stop()
        raise

    version = parse_version(handshake)
    log.info("Connected to %s", version)

    mcp = FastMCP(
        "NukeMCP",
        instructions=(
            f"You are connected to {version}. "
            "Use the available tools to inspect and modify the Nuke script. "
            "Always check the current state with get_script_info or get_node_info "
            "before making changes. Never delete nodes or execute code without "
            "user confirmation (set confirm=True only after the user agrees)."
        ),
    )

    server = NukeMCPServer(mcp, conn, version, mock_server=mock_server)

    # Register tool modules
    graph.register(server)
    script.register(server)
    comp.register(server)
    render.register(server)
    templates.register(server)
    batch.register(server)
    tracking.register(server)
    threed.register(server)
    deep.register(server)
    ml.register(server)
    splats.register(server)
    annotations.register(server)

    # Register non-tool modules (memory, rag, events, resources, prompts)
    from nukemcp import memory, rag, events, resources, prompts
    memory.register(server)
    rag.register(server)
    events.register(server)
    resources.register(server)
    prompts.register(server)

    # Load facility plugins
    from nukemcp.plugins import load_plugins
    load_plugins(server)

    # Auto-populate project memory on connection
    try:
        info = conn.send_command("get_script_info")
        script_name = info.get("name", "untitled")
        # Derive a clean project name from the script filename
        project_name = script_name.rsplit("/", 1)[-1].rsplit(".", 1)[0] or "untitled"
        memory.write_file(
            f"project/{project_name}.md",
            f"# {project_name}\n\n"
            f"- **Script:** {info.get('name', 'unknown')}\n"
            f"- **Frame Range:** {info.get('frame_range', [0, 0])}\n"
            f"- **FPS:** {info.get('fps', 24)}\n"
            f"- **Colorspace:** {info.get('colorspace', 'unknown')}\n"
            f"- **Format:** {info.get('format', 'unknown')}\n"
            f"- **Node Count:** {info.get('node_count', 0)}\n",
        )
        log.info("Auto-populated project memory: project/%s.md", project_name)
    except Exception:
        log.debug("Skipped project memory auto-population", exc_info=True)

    return mcp


def main():
    parser = argparse.ArgumentParser(description="NukeMCP — MCP server for Foundry Nuke")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Nuke addon host (default: localhost)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Nuke addon port (default: 54321)")
    parser.add_argument("--mock", action="store_true", help="Use mock Nuke socket for offline development")
    parser.add_argument("--mock-version", default="17.0v1", help="Mock Nuke version (default: 17.0v1)")
    parser.add_argument("--mock-variant", default="NukeX", help="Mock Nuke variant (default: NukeX)")
    parser.add_argument("--discover", action="store_true", help="Find Nuke installations and exit")
    parser.add_argument("--headless", action="store_true", help="Launch Nuke in headless mode before connecting")
    parser.add_argument("--nuke-path", help="Path to Nuke executable (for --headless)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(name)s %(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    if args.discover:
        from nukemcp.discovery import discover_nuke
        result = discover_nuke(extra_paths=[args.nuke_path] if args.nuke_path else None)
        print(result.summary(), file=sys.stderr)
        sys.exit(0 if result.has_nuke else 1)

    nuke_proc = None
    if args.headless:
        from nukemcp.discovery import discover_nuke, launch_headless
        nuke_path = args.nuke_path
        if not nuke_path:
            result = discover_nuke()
            if not result.has_nuke:
                log.error("Cannot launch headless: %s", result.summary())
                sys.exit(1)
            nuke_path = str(result.best.executable)
            log.info("Auto-discovered: %s", result.best)
        nuke_proc = launch_headless(nuke_path, port=args.port)
        log.info("Headless Nuke running (PID %d)", nuke_proc.pid)

    mcp = build_server(
        host=args.host,
        port=args.port,
        mock=args.mock,
        mock_version=args.mock_version,
        mock_variant=args.mock_variant,
    )
    mcp.run()
