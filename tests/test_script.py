"""Tests for script tools using the mock socket."""


def test_set_frame_range(connection):
    response = connection.send({
        "type": "set_frame_range",
        "params": {"first": 1001, "last": 1100},
    })
    assert response["status"] == "ok"
    assert response["result"]["first_frame"] == 1001
    assert response["result"]["last_frame"] == 1100


def test_set_project_settings_fps(connection):
    response = connection.send({
        "type": "set_project_settings",
        "params": {"fps": 30.0},
    })
    assert response["status"] == "ok"
    assert "fps" in response["result"]["modified"]


def test_set_project_settings_colorspace(connection):
    response = connection.send({
        "type": "set_project_settings",
        "params": {"colorspace": "OCIO"},
    })
    assert response["status"] == "ok"
    assert "colorspace" in response["result"]["modified"]


def test_load_script(connection):
    response = connection.send({
        "type": "load_script",
        "params": {"path": "/shots/ABC/comp/ABC_010_comp_v01.nk"},
    })
    assert response["status"] == "ok"
    assert response["result"]["loaded"] == "/shots/ABC/comp/ABC_010_comp_v01.nk"


def test_save_script(connection):
    response = connection.send({
        "type": "save_script",
        "params": {"path": "/tmp/test_save.nk"},
    })
    assert response["status"] == "ok"
    assert response["result"]["saved"] == "/tmp/test_save.nk"


def test_save_script_default_path(connection):
    response = connection.send({
        "type": "save_script",
        "params": {},
    })
    assert response["status"] == "ok"
    assert response["result"]["saved"] == "untitled.nk"
