"""Tests for batch operations — find, filter, bulk modify."""


def test_find_nodes_by_type(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "g1"}})
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "g2"}})
    connection.send({"type": "create_node", "params": {"node_class": "Blur", "name": "b1"}})

    response = connection.send({"type": "find_nodes_by_type", "params": {"node_class": "Grade"}})
    assert response["status"] == "ok"
    names = [n["name"] for n in response["result"]["nodes"]]
    assert "g1" in names
    assert "g2" in names
    assert "b1" not in names


def test_find_nodes_by_type_wildcard(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "g1"}})
    connection.send({"type": "create_node", "params": {"node_class": "Blur", "name": "b1"}})

    response = connection.send({"type": "find_nodes_by_type", "params": {"node_class": "*"}})
    assert response["status"] == "ok"
    assert len(response["result"]["nodes"]) >= 2


def test_find_broken_reads(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Read", "name": "good_read", "knobs": {"file": "/valid/path.exr"}},
    })
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Read", "name": "bad_read", "knobs": {"file": ""}},
    })

    response = connection.send({"type": "find_broken_reads", "params": {}})
    assert response["status"] == "ok"
    broken_names = [r["name"] for r in response["result"]["broken_reads"]]
    assert "bad_read" in broken_names
    assert "good_read" not in broken_names


def test_find_error_nodes(connection):
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "ok_node"},
    })
    connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "err_node", "knobs": {"_error": "test error"}},
    })

    response = connection.send({"type": "find_error_nodes", "params": {}})
    assert response["status"] == "ok"
    error_names = [n["name"] for n in response["result"]["nodes"]]
    assert "err_node" in error_names
    assert "ok_node" not in error_names


def test_batch_set_knob(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "bs1"}})
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "bs2"}})

    response = connection.send({
        "type": "batch_set_knob",
        "params": {"node_names": ["bs1", "bs2"], "knob_name": "mix", "value": 0.5},
    })
    assert response["status"] == "ok"
    assert "bs1" in response["result"]["modified"]
    assert "bs2" in response["result"]["modified"]


def test_batch_reconnect(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "new_src"}})
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "br1"}})
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "br2"}})

    response = connection.send({
        "type": "batch_reconnect",
        "params": {"node_names": ["br1", "br2"], "new_input": "new_src"},
    })
    assert response["status"] == "ok"
    assert "br1" in response["result"]["reconnected"]
    assert "br2" in response["result"]["reconnected"]


def test_batch_reconnect_missing_source(connection):
    connection.send({"type": "create_node", "params": {"node_class": "Grade", "name": "br3"}})

    response = connection.send({
        "type": "batch_reconnect",
        "params": {"node_names": ["br3"], "new_input": "nonexistent"},
    })
    assert response["status"] == "error"
