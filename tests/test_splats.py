"""Tests for Gaussian Splat tools — import, render setup. Nuke 17+ gated."""


def test_import_splat(connection):
    """Simulate import_splat: Read node with splat file path."""
    resp = connection.send({
        "type": "create_node",
        "params": {
            "node_class": "Read",
            "name": "splat_read",
            "knobs": {"file": "/shots/env/garden.ply"},
        },
    })
    assert resp["status"] == "ok"
    assert resp["result"]["name"] == "splat_read"


def test_setup_splat_render(connection):
    """Simulate setup_splat_render: splat + camera → SplatRender."""
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Read", "name": "splat_read", "knobs": {"file": "/shots/env/garden.ply"}},
    })
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Camera3", "name": "cam"},
    })

    # Create SplatRender
    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "SplatRender", "name": "splat_render"},
    })
    assert resp["status"] == "ok"

    # Connect splat → SplatRender:0
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "splat_read", "input_node": "splat_render", "input_index": 0},
    })
    assert resp["status"] == "ok"

    # Connect camera → SplatRender:1
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "cam", "input_node": "splat_render", "input_index": 1},
    })
    assert resp["status"] == "ok"


def test_splat_render_missing_camera(connection):
    """Connecting to SplatRender with a nonexistent camera should error."""
    connection.send({
        "type": "create_node",
        "params": {"node_class": "SplatRender", "name": "sr"},
    })

    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "no_cam", "input_node": "sr", "input_index": 1},
    })
    assert resp["status"] == "error"
