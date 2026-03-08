"""NukeMCP — FastMCP server entry point.

Connects to the Nuke addon (or mock) and exposes tools to AI clients via stdio.
"""

from __future__ import annotations

import argparse
import logging
import sys

from fastmcp import FastMCP

from nukemcp.connection import NukeConnection, DEFAULT_HOST, DEFAULT_PORT
from nukemcp.version import parse_version, NukeVersion
from nukemcp.tools import graph, script

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

    return mcp


def main():
    parser = argparse.ArgumentParser(description="NukeMCP — MCP server for Foundry Nuke")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Nuke addon host (default: localhost)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Nuke addon port (default: 54321)")
    parser.add_argument("--mock", action="store_true", help="Use mock Nuke socket for offline development")
    parser.add_argument("--mock-version", default="17.0v1", help="Mock Nuke version (default: 17.0v1)")
    parser.add_argument("--mock-variant", default="NukeX", help="Mock Nuke variant (default: NukeX)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(name)s %(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    mcp = build_server(
        host=args.host,
        port=args.port,
        mock=args.mock,
        mock_version=args.mock_version,
        mock_variant=args.mock_variant,
    )
    mcp.run()
