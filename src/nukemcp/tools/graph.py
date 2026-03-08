"""Core node graph tools — create, modify, delete, connect, position, layout, inspect."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool(
        annotations={"readOnlyHint": True},
    )
    def get_script_info() -> dict:
        """Get information about the current Nuke script.

        Returns script name, frame range, FPS, format, colorspace, and node count.
        """
        response = conn.send({"type": "get_script_info", "params": {}})
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]

    @mcp.tool(
        annotations={"readOnlyHint": True},
    )
    def get_node_info(node_name: str) -> dict:
        """Get detailed information about a specific node.

        Returns the node's class, position, inputs, and knob values.

        Args:
            node_name: The name of the node to inspect.
        """
        response = conn.send({"type": "get_node_info", "params": {"node_name": node_name}})
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]

    @mcp.tool()
    def create_node(
        node_class: str,
        name: str | None = None,
        knobs: dict | None = None,
        position: list[int] | None = None,
    ) -> dict:
        """Create a new node in the Nuke script.

        Args:
            node_class: The Nuke node class (e.g., "Grade", "Merge2", "Read").
            name: Optional name for the node. If not provided, Nuke assigns a default.
            knobs: Optional dict of knob names to values to set on creation.
            position: Optional [x, y] position in the node graph.
        """
        params = {"node_class": node_class}
        if name is not None:
            params["name"] = name
        if knobs is not None:
            params["knobs"] = knobs
        if position is not None:
            params["position"] = position

        response = conn.send({"type": "create_node", "params": params})
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]

    @mcp.tool(
        annotations={"idempotentHint": True},
    )
    def modify_node(node_name: str, knobs: dict) -> dict:
        """Modify knob values on an existing node.

        Args:
            node_name: The name of the node to modify.
            knobs: Dict of knob names to new values.
        """
        response = conn.send({
            "type": "modify_node",
            "params": {"node_name": node_name, "knobs": knobs},
        })
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]

    @mcp.tool(
        annotations={"destructiveHint": True},
    )
    def delete_node(node_name: str, confirm: bool = False) -> dict:
        """Delete a node from the Nuke script.

        This is a destructive action. You must set confirm=True after getting
        user confirmation.

        Args:
            node_name: The name of the node to delete.
            confirm: Must be True to proceed. If False, returns a description
                     of what would be deleted without deleting it.
        """
        if not confirm:
            return {
                "action": "delete_node",
                "node_name": node_name,
                "message": (
                    f"This will permanently delete node '{node_name}'. "
                    "Ask the user to confirm, then call again with confirm=True."
                ),
            }

        response = conn.send({"type": "delete_node", "params": {"node_name": node_name}})
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]

    @mcp.tool()
    def connect_nodes(
        output_node: str,
        input_node: str,
        input_index: int = 0,
    ) -> dict:
        """Connect two nodes in the Nuke script.

        Connects the output of one node to the input of another.

        Args:
            output_node: The name of the node whose output to connect.
            input_node: The name of the node whose input to connect to.
            input_index: Which input on the input_node to connect to (default 0).
        """
        response = conn.send({
            "type": "connect_nodes",
            "params": {
                "output_node": output_node,
                "input_node": input_node,
                "input_index": input_index,
            },
        })
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]

    @mcp.tool(
        annotations={"idempotentHint": True},
    )
    def position_node(node_name: str, x: int, y: int) -> dict:
        """Set the position of a node in the node graph.

        Args:
            node_name: The name of the node to position.
            x: X coordinate in the node graph.
            y: Y coordinate in the node graph.
        """
        response = conn.send({
            "type": "position_node",
            "params": {"node_name": node_name, "x": x, "y": y},
        })
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]

    @mcp.tool()
    def auto_layout(node_names: list[str] | None = None) -> dict:
        """Auto-arrange nodes in the node graph for a clean layout.

        Args:
            node_names: Optional list of node names to arrange. If None, arranges all nodes.
        """
        params = {}
        if node_names is not None:
            params["node_names"] = node_names

        response = conn.send({"type": "auto_layout", "params": params})
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]

    @mcp.tool(
        annotations={"destructiveHint": True},
    )
    def execute_python(code: str, confirm: bool = False) -> dict:
        """Execute arbitrary Python code in Nuke's environment.

        This is a powerful but destructive tool. You must set confirm=True
        after getting user confirmation.

        Args:
            code: Python code to execute. The `nuke` module is available.
                  Assign to `result` to return a value.
            confirm: Must be True to proceed.
        """
        if not confirm:
            return {
                "action": "execute_python",
                "code_preview": code[:200],
                "message": (
                    "This will execute arbitrary Python code in Nuke. "
                    "Show the code to the user and ask them to confirm, "
                    "then call again with confirm=True."
                ),
            }

        response = conn.send({"type": "execute_python", "params": {"code": code}})
        if response["status"] == "error":
            raise RuntimeError(response["error"])
        return response["result"]
