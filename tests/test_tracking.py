"""Tests for tracking tools — create, solve, stabilize, camera tracker."""


def test_create_tracker(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "plate"}})

    response = connection.send({
        "type": "create_tracker",
        "params": {"source_node": "plate", "name": "my_tracker"},
    })
    assert response["status"] == "ok"
    assert response["result"]["name"] == "my_tracker"
    assert response["result"]["source"] == "plate"


def test_create_tracker_missing_source(connection):
    response = connection.send({
        "type": "create_tracker",
        "params": {"source_node": "nonexistent"},
    })
    assert response["status"] == "error"


def test_solve_tracker(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "plate"}})
    connection.send({"type": "create_tracker", "params": {"source_node": "plate", "name": "trk"}})

    response = connection.send({
        "type": "solve_tracker",
        "params": {"tracker_node": "trk"},
    })
    assert response["status"] == "ok"
    assert response["result"]["solved"] == "trk"


def test_setup_stabilize(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "plate"}})
    connection.send({"type": "create_tracker", "params": {"source_node": "plate", "name": "trk"}})

    response = connection.send({
        "type": "setup_stabilize",
        "params": {"source_node": "plate", "tracker_node": "trk"},
    })
    assert response["status"] == "ok"
    assert response["result"]["name"] == "trk"  # Real addon modifies the tracker in place


def test_create_camera_tracker(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "plate"}})

    response = connection.send({
        "type": "create_camera_tracker",
        "params": {"source_node": "plate", "name": "cam_trk"},
    })
    assert response["status"] == "ok"
    assert response["result"]["name"] == "cam_trk"
    assert response["result"]["class"] == "CameraTracker"
