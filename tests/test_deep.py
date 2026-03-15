"""Tests for deep compositing tools — pipeline, merge, conversion. NukeX-gated."""


def test_setup_deep_pipeline(connection):
    """Simulate setup_deep_pipeline: DeepRecolor → DeepToImage chain."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "deep_read"}})

    # Create DeepRecolor
    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "DeepRecolor", "name": "deep_recolor"},
    })
    assert resp["status"] == "ok"

    # Connect Read → DeepRecolor
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "deep_read", "input_node": "deep_recolor"},
    })
    assert resp["status"] == "ok"

    # Create DeepToImage
    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "DeepToImage", "name": "deep_to_image"},
    })
    assert resp["status"] == "ok"

    # Connect DeepRecolor → DeepToImage
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "deep_recolor", "input_node": "deep_to_image"},
    })
    assert resp["status"] == "ok"


def test_setup_deep_merge(connection):
    """Simulate setup_deep_merge: merge multiple deep streams."""
    # Create deep source nodes
    connection.send({"type": "create_node", "params": {"node_class": "DeepRead", "name": "deep_a"}})
    connection.send({"type": "create_node", "params": {"node_class": "DeepRead", "name": "deep_b"}})

    # Create DeepMerge
    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "DeepMerge", "name": "deep_merge"},
    })
    assert resp["status"] == "ok"

    # Connect each source at increasing input indices
    for i, name in enumerate(["deep_a", "deep_b"]):
        resp = connection.send({
            "type": "connect_nodes",
            "params": {"output_node": name, "input_node": "deep_merge", "input_index": i},
        })
        assert resp["status"] == "ok"


def test_convert_to_deep(connection):
    """Simulate convert_to_deep: flat image → DeepFromImage."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "flat_plate"}})

    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "DeepFromImage", "name": "to_deep"},
    })
    assert resp["status"] == "ok"

    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "flat_plate", "input_node": "to_deep"},
    })
    assert resp["status"] == "ok"


def test_connect_missing_node_errors(connection):
    """Deep merge with a nonexistent node should error."""
    connection.send({"type": "create_node", "params": {"node_class": "DeepMerge", "name": "dm"}})

    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "nonexistent", "input_node": "dm"},
    })
    assert resp["status"] == "error"
