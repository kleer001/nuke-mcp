"""Tests for graph tools using the mock socket."""


def test_get_script_info(connection):
    response = connection.send({"type": "get_script_info", "params": {}})
    assert response["status"] == "ok"
    result = response["result"]
    assert "name" in result
    assert "frame_range" in result
    assert "node_count" in result


def test_create_node(connection):
    response = connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "test_grade"},
    })
    assert response["status"] == "ok"
    assert response["result"]["name"] == "test_grade"
    assert response["result"]["class"] == "Grade"


def test_create_node_with_knobs(connection):
    response = connection.send({
        "type": "create_node",
        "params": {
            "node_class": "Grade",
            "name": "graded",
            "knobs": {"white": 1.5, "mix": 0.8},
            "position": [100, 200],
        },
    })
    assert response["status"] == "ok"
    assert response["result"]["xpos"] == 100
    assert response["result"]["ypos"] == 200


def test_get_node_info(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Blur", "name": "my_blur"},
    })
    response = connection.send({
        "type": "get_node_info",
        "params": {"node_name": "my_blur"},
    })
    assert response["status"] == "ok"
    assert response["result"]["class"] == "Blur"


def test_get_node_info_not_found(connection):
    response = connection.send({
        "type": "get_node_info",
        "params": {"node_name": "nonexistent"},
    })
    assert response["status"] == "error"
    assert "not found" in response["error"]


def test_modify_node(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "mod_grade"},
    })
    response = connection.send({
        "type": "modify_node",
        "params": {"node_name": "mod_grade", "knobs": {"white": 2.0}},
    })
    assert response["status"] == "ok"
    assert "white" in response["result"]["modified_knobs"]


def test_delete_node(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "doomed"},
    })
    response = connection.send({
        "type": "delete_node",
        "params": {"node_name": "doomed"},
    })
    assert response["status"] == "ok"
    assert response["result"]["deleted"] == "doomed"

    # Verify it's gone
    response = connection.send({
        "type": "get_node_info",
        "params": {"node_name": "doomed"},
    })
    assert response["status"] == "error"


def test_connect_nodes(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Read", "name": "read_a"},
    })
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "grade_a"},
    })
    response = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "read_a", "input_node": "grade_a"},
    })
    assert response["status"] == "ok"
    assert response["result"]["output"] == "read_a"
    assert response["result"]["input"] == "grade_a"


def test_position_node(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "pos_grade"},
    })
    response = connection.send({
        "type": "position_node",
        "params": {"node_name": "pos_grade", "x": 500, "y": 300},
    })
    assert response["status"] == "ok"
    assert response["result"]["xpos"] == 500
    assert response["result"]["ypos"] == 300


def test_auto_layout(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "layout_a"},
    })
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Blur", "name": "layout_b"},
    })
    response = connection.send({
        "type": "auto_layout",
        "params": {},
    })
    assert response["status"] == "ok"
    assert response["result"]["laid_out"] >= 2


def test_execute_python(connection):
    response = connection.send({
        "type": "execute_python",
        "params": {"code": "result = 42"},
    })
    assert response["status"] == "ok"


def test_ping(connection):
    response = connection.send({"type": "ping", "params": {}})
    assert response["status"] == "ok"
    assert response["result"] == "pong"


def test_unknown_command(connection):
    response = connection.send({"type": "nonexistent_command", "params": {}})
    assert response["status"] == "error"
    assert "Unknown command" in response["error"]
