"""Deep compositing tools — pipeline setup, merge, conversion. NukeX-gated."""

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
    def setup_deep_pipeline(
        read_node: str,
        name_prefix: str = "deep",
    ) -> dict:
        """Set up a basic deep compositing pipeline from a deep EXR Read.

        Creates DeepRecolor, DeepHoldout, and DeepToImage nodes.

        Args:
            read_node: Name of the Read node with deep data.
            name_prefix: Prefix for node names.
        """
        recolor = _create(conn, "DeepRecolor", f"{name_prefix}_recolor")
        _connect(conn, read_node, recolor)

        to_image = _create(conn, "DeepToImage", f"{name_prefix}_to_image")
        _connect(conn, recolor, to_image)

        return {
            "pipeline": [recolor, to_image],
            "output_node": to_image,
        }

    @mcp.tool()
    def setup_deep_merge(
        deep_nodes: list[str],
        name: str = "deep_merge",
    ) -> dict:
        """Merge multiple deep streams together.

        Args:
            deep_nodes: List of deep node names to merge.
            name: Name for the DeepMerge node.
        """
        merge = _create(conn, "DeepMerge", name)
        for i, node in enumerate(deep_nodes):
            _connect(conn, node, merge, i)

        return {"node": merge, "inputs": deep_nodes}

    @mcp.tool()
    def convert_to_deep(
        source_node: str,
        name: str = "to_deep",
    ) -> dict:
        """Convert a flat image to deep using DeepFromImage.

        Args:
            source_node: Flat image node to convert.
            name: Name for the DeepFromImage node.
        """
        deep = _create(conn, "DeepFromImage", name)
        _connect(conn, source_node, deep)
        return {"node": deep, "source": source_node}
