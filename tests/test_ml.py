"""Tests for ML tools — CopyCat, train, BigCat. NukeX + Nuke 17+ gated."""


def test_setup_copycat(connection):
    """Simulate setup_copycat: input and ground truth → CopyCat."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "input"}})
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "gt"}})

    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "CopyCat", "name": "copycat"},
    })
    assert resp["status"] == "ok"

    # Connect input → CopyCat:0
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "input", "input_node": "copycat", "input_index": 0},
    })
    assert resp["status"] == "ok"

    # Connect ground truth → CopyCat:1
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "gt", "input_node": "copycat", "input_index": 1},
    })
    assert resp["status"] == "ok"


def test_train_copycat(connection):
    """Simulate train_copycat via the mock's train_copycat command."""
    connection.send({"type": "create_node", "params": {"node_class": "CopyCat", "name": "cc"}})

    resp = connection.send({
        "type": "train_copycat",
        "params": {"copycat_node": "cc", "epochs": 500},
    })
    assert resp["status"] == "ok"
    assert resp["result"]["trained"] == "cc"
    assert resp["result"]["epochs"] == 500


def test_train_copycat_missing_node(connection):
    """Training a nonexistent CopyCat node should error."""
    resp = connection.send({
        "type": "train_copycat",
        "params": {"copycat_node": "nonexistent"},
    })
    assert resp["status"] == "error"


def test_setup_bigcat(connection):
    """Simulate setup_bigcat: input and ground truth → BigCat."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "input"}})
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "gt"}})

    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "BigCat", "name": "bigcat"},
    })
    assert resp["status"] == "ok"

    # Connect input → BigCat:0
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "input", "input_node": "bigcat", "input_index": 0},
    })
    assert resp["status"] == "ok"

    # Connect ground truth → BigCat:1
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "gt", "input_node": "bigcat", "input_index": 1},
    })
    assert resp["status"] == "ok"


def test_setup_bigcat_no_augmentation(connection):
    """BigCat with augmentation disabled passes the knob."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "input"}})
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "gt"}})

    resp = connection.send({
        "type": "create_node",
        "params": {
            "node_class": "BigCat",
            "name": "bigcat_noaug",
            "knobs": {"augmentation": False},
        },
    })
    assert resp["status"] == "ok"
    assert resp["result"]["name"] == "bigcat_noaug"
