"""Machine learning tools — CopyCat and BigCat setup and training. NukeX-gated."""

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
    def setup_copycat(
        input_node: str,
        ground_truth_node: str,
        name: str = "copycat",
    ) -> dict:
        """Set up a CopyCat node for ML inference training.

        CopyCat trains a neural network to reproduce a target look from input data.

        Args:
            input_node: Source image node (training input).
            ground_truth_node: Target image node (what the network should learn to produce).
            name: Name for the CopyCat node.
        """
        cc = _create(conn, "CopyCat", name)
        _connect(conn, input_node, cc, 0)
        _connect(conn, ground_truth_node, cc, 1)
        return {"node": cc, "input": input_node, "ground_truth": ground_truth_node}

    @mcp.tool(annotations={"destructiveHint": True})
    def train_copycat(
        copycat_node: str,
        epochs: int = 1000,
        confirm: bool = False,
    ) -> dict:
        """Train a CopyCat model. This is a long-running operation.

        Args:
            copycat_node: Name of the CopyCat node to train.
            epochs: Number of training epochs.
            confirm: Must be True to proceed.
        """
        if not confirm:
            return {
                "action": "train_copycat",
                "node": copycat_node,
                "epochs": epochs,
                "message": f"This will train CopyCat '{copycat_node}' for {epochs} epochs. Confirm to proceed.",
            }
        return conn.send_command(
            "train_copycat",
            {"copycat_node": copycat_node, "epochs": epochs},
            timeout=7200.0,
        )

    if not server.version.at_least(17):
        return

    @mcp.tool()
    def setup_bigcat(
        input_node: str,
        ground_truth_node: str,
        name: str = "bigcat",
        augmentation: bool = True,
    ) -> dict:
        """Set up a BigCat node for large-scale ML training (Nuke 17+).

        BigCat extends CopyCat with data augmentation and custom loss functions.

        Args:
            input_node: Source image node.
            ground_truth_node: Target image node.
            name: Name for the BigCat node.
            augmentation: Enable data augmentation (default True).
        """
        knobs = {}
        if not augmentation:
            knobs["augmentation"] = False
        bc = _create(conn, "BigCat", name, knobs or None)
        _connect(conn, input_node, bc, 0)
        _connect(conn, ground_truth_node, bc, 1)
        return {"node": bc, "input": input_node, "ground_truth": ground_truth_node}
