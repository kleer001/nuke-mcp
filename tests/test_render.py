"""Tests for render tools — render_frames, set_proxy_mode."""


def test_render_frames(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Write", "name": "write_out", "knobs": {"file": "/tmp/out.####.exr"}},
    })
    response = connection.send({
        "type": "render_frames",
        "params": {"write_node": "write_out", "first_frame": 1001, "last_frame": 1010},
    })
    assert response["status"] == "ok"
    assert response["result"]["rendered"] == "write_out"


def test_render_frames_missing_node(connection):
    response = connection.send({
        "type": "render_frames",
        "params": {"write_node": "nonexistent"},
    })
    assert response["status"] == "error"


def test_set_proxy_mode(connection):
    response = connection.send({
        "type": "set_proxy_mode",
        "params": {"enabled": True},
    })
    assert response["status"] == "ok"
    assert response["result"]["proxy_mode"] is True

    response = connection.send({
        "type": "set_proxy_mode",
        "params": {"enabled": False},
    })
    assert response["status"] == "ok"
    assert response["result"]["proxy_mode"] is False
