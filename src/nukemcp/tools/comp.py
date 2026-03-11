"""High-level compositing workflow tools — keying, despill, grade chains, merges."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nukemcp.tools._helpers import create_node as _create, connect_nodes as _connect

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def setup_keyer(
        source_node: str,
        keyer_type: str = "IBKGizmo",
        name_prefix: str = "key",
    ) -> dict:
        """Set up a keying pipeline connected to a source node.

        Creates a keyer node, connects it to the source, and adds a standard
        post-processing chain (erode, blur edge, premult).

        Args:
            source_node: Name of the node to key (typically a Read or Grade).
            keyer_type: Keyer class — "IBKGizmo", "Primatte", "Keylight", or "Cryptomatte".
            name_prefix: Prefix for generated node names.
        """
        keyer = _create(conn, keyer_type, f"{name_prefix}_keyer")
        _connect(conn, source_node, keyer)

        erode = _create(conn, "FilterErode", f"{name_prefix}_erode", {"size": -0.5})
        _connect(conn, keyer, erode)

        edge_blur = _create(conn, "Blur", f"{name_prefix}_edge_blur", {"size": 1.0, "channels": "alpha"})
        _connect(conn, erode, edge_blur)

        premult = _create(conn, "Premult", f"{name_prefix}_premult")
        _connect(conn, edge_blur, premult)

        return {
            "pipeline": [keyer, erode, edge_blur, premult],
            "keyer_type": keyer_type,
            "output_node": premult,
        }

    @mcp.tool()
    def setup_despill(source_node: str, screen_color: str = "green", name_prefix: str = "despill") -> dict:
        """Set up a despill operation on a keyed source.

        Args:
            source_node: Node to despill (typically the output of a keyer).
            screen_color: "green" or "blue".
            name_prefix: Prefix for node names.
        """
        hue_correct = _create(conn, "HueCorrect", f"{name_prefix}_hue")
        _connect(conn, source_node, hue_correct)

        return {"pipeline": [hue_correct], "output_node": hue_correct}

    @mcp.tool()
    def setup_basic_comp(
        fg_node: str,
        bg_node: str,
        name_prefix: str = "comp",
    ) -> dict:
        """Set up a basic A-over-B composite.

        Creates a Merge2 (over) with the foreground over the background.

        Args:
            fg_node: Foreground node name (keyed, premultiplied).
            bg_node: Background node name.
            name_prefix: Prefix for node names.
        """
        merge = _create(conn, "Merge2", f"{name_prefix}_merge", {"operation": "over"})
        _connect(conn, bg_node, merge, 0)  # B input
        _connect(conn, fg_node, merge, 1)  # A input

        return {"pipeline": [merge], "output_node": merge}

    @mcp.tool()
    def setup_grade_chain(
        source_node: str,
        grades: list[dict],
        name_prefix: str = "grade",
    ) -> dict:
        """Create a chain of Grade nodes connected in sequence.

        Args:
            source_node: Node to start the chain from.
            grades: List of dicts, each with optional keys: "white", "black",
                    "multiply", "gamma", "gain", "offset", "mix", "label".
            name_prefix: Prefix for node names.
        """
        nodes = []
        prev = source_node
        for i, g in enumerate(grades):
            label = g.get("label", f"grade_{i + 1}")
            knobs = {k: v for k, v in g.items() if k != "label"}
            requested_name = f"{name_prefix}_{label}"
            actual_name = _create(conn, "Grade", requested_name, knobs)
            _connect(conn, prev, actual_name)
            nodes.append(actual_name)
            prev = actual_name

        return {"pipeline": nodes, "output_node": prev}

    @mcp.tool()
    def setup_light_wrap(
        fg_node: str,
        bg_node: str,
        name_prefix: str = "lw",
    ) -> dict:
        """Set up a light wrap effect — blurs the background edge onto the foreground.

        Args:
            fg_node: Premultiplied foreground node.
            bg_node: Background plate node.
            name_prefix: Prefix for node names.
        """
        blur = _create(conn, "Blur", f"{name_prefix}_bg_blur", {"size": 20.0})
        _connect(conn, bg_node, blur)

        merge = _create(conn, "Merge2", f"{name_prefix}_merge", {"operation": "screen", "mix": 0.3})
        _connect(conn, fg_node, merge, 0)
        _connect(conn, blur, merge, 1)

        return {"pipeline": [blur, merge], "output_node": merge}

    @mcp.tool()
    def setup_edge_blur(
        source_node: str,
        size: float = 2.0,
        name_prefix: str = "edge",
    ) -> dict:
        """Blur the edges of a matte to soften fringe.

        Args:
            source_node: Node with alpha channel to soften.
            size: Blur size in pixels.
            name_prefix: Prefix for node names.
        """
        edge = _create(conn, "EdgeBlur", f"{name_prefix}_blur", {"size": size})
        _connect(conn, source_node, edge)
        return {"pipeline": [edge], "output_node": edge}
