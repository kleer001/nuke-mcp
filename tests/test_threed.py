"""Tests for 3D scene tools — camera, scene, ScanlineRender, projection. NukeX-gated."""


def test_create_3d_scene(connection):
    """Create a Scene node."""
    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "Scene", "name": "scene"},
    })
    assert resp["status"] == "ok"
    assert resp["result"]["class"] == "Scene"


def test_setup_camera(connection):
    """Create a Camera3 node with focal length and aperture."""
    resp = connection.send({
        "type": "create_node",
        "params": {
            "node_class": "Camera3",
            "name": "camera",
            "knobs": {"focal": 50.0, "haperture": 36.0},
        },
    })
    assert resp["status"] == "ok"
    assert resp["result"]["name"] == "camera"


def test_setup_scanline_render(connection):
    """Simulate setup_scanline_render: scene + camera → ScanlineRender."""
    connection.send({"type": "create_node", "params": {"node_class": "Scene", "name": "scene"}})
    connection.send({"type": "create_node", "params": {"node_class": "Camera3", "name": "cam"}})

    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "ScanlineRender", "name": "scanline_render"},
    })
    assert resp["status"] == "ok"

    # Connect scene → SR:0
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "scene", "input_node": "scanline_render", "input_index": 0},
    })
    assert resp["status"] == "ok"

    # Connect camera → SR:1
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "cam", "input_node": "scanline_render", "input_index": 1},
    })
    assert resp["status"] == "ok"


def test_setup_projection(connection):
    """Simulate setup_projection: source + camera → Project3D2."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "texture"}})
    connection.send({"type": "create_node", "params": {"node_class": "Camera3", "name": "proj_cam"}})

    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "Project3D2", "name": "proj_project3d"},
    })
    assert resp["status"] == "ok"

    # Connect source → Project3D2:0
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "texture", "input_node": "proj_project3d", "input_index": 0},
    })
    assert resp["status"] == "ok"

    # Connect camera → Project3D2:1
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "proj_cam", "input_node": "proj_project3d", "input_index": 1},
    })
    assert resp["status"] == "ok"


def test_scanline_render_missing_scene(connection):
    """Connecting ScanlineRender with a nonexistent scene should error."""
    connection.send({"type": "create_node", "params": {"node_class": "ScanlineRender", "name": "sr"}})

    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "no_scene", "input_node": "sr", "input_index": 0},
    })
    assert resp["status"] == "error"
