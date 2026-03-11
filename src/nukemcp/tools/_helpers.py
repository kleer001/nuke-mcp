"""Shared helpers for tool modules that compose addon commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.connection import NukeConnection


def create_node(conn: NukeConnection, node_class: str, name: str | None = None,
                knobs: dict | None = None, position: list[int] | None = None) -> str:
    """Create a node via the addon and return its actual name."""
    params: dict = {"node_class": node_class}
    if name:
        params["name"] = name
    if knobs:
        params["knobs"] = knobs
    if position:
        params["position"] = position
    return conn.send_command("create_node", params)["name"]


def connect_nodes(conn: NukeConnection, output: str, inp: str, index: int = 0) -> None:
    """Connect two nodes via the addon."""
    conn.send_command("connect_nodes", {
        "output_node": output, "input_node": inp, "input_index": index,
    })
