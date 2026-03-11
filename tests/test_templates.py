"""Tests for toolset and LiveGroup management."""


def test_list_toolsets(connection):
    response = connection.send({"type": "list_toolsets", "params": {}})
    assert response["status"] == "ok"
    assert "toolsets" in response["result"]


def test_save_and_load_toolset(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "ts_g"}})

    save_resp = connection.send({
        "type": "save_toolset",
        "params": {"name": "my_toolset", "node_names": ["ts_g"]},
    })
    assert save_resp["status"] == "ok"
    assert save_resp["result"]["saved"] == "my_toolset"

    load_resp = connection.send({
        "type": "load_toolset",
        "params": {"name": "my_toolset"},
    })
    assert load_resp["status"] == "ok"


def test_load_toolset_not_found(connection):
    response = connection.send({
        "type": "load_toolset",
        "params": {"name": "nonexistent"},
    })
    assert response["status"] == "error"


def test_create_live_group(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "lg_g1"}})
    connection.send({"type": "create_node", "params": {"node_class": "Blur", "name": "lg_b1"}})

    response = connection.send({
        "type": "create_live_group",
        "params": {"name": "MyLiveGroup", "node_names": ["lg_g1", "lg_b1"]},
    })
    assert response["status"] == "ok"
    assert response["result"]["name"] == "MyLiveGroup"
