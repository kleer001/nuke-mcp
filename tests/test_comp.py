"""Tests for comp tool workflows — these compose existing create/connect commands."""


def test_keyer_pipeline(connection):
    """Simulate setup_keyer by creating and connecting nodes."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "plate"}})

    # Create keyer
    resp = connection.send({"type": "create_node", "params": {"node_class": "IBKGizmo", "name": "key_keyer"}})
    assert resp["status"] == "ok"

    # Connect
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "plate", "input_node": "key_keyer"},
    })
    assert resp["status"] == "ok"


def test_basic_comp_merge(connection):
    """Simulate setup_basic_comp with a Merge2 node."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "fg"}})
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "bg"}})

    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "Merge2", "name": "comp_merge", "knobs": {"operation": "over"}},
    })
    assert resp["status"] == "ok"

    # Connect B (bg) to input 0
    connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "bg", "input_node": "comp_merge", "input_index": 0},
    })
    # Connect A (fg) to input 1
    resp = connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "fg", "input_node": "comp_merge", "input_index": 1},
    })
    assert resp["status"] == "ok"


def test_grade_chain(connection):
    """Simulate setup_grade_chain."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "src"}})

    g1 = connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "grade_lift", "knobs": {"white": 1.2}},
    })
    assert g1["status"] == "ok"

    connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "src", "input_node": "grade_lift"},
    })

    g2 = connection.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "grade_gamma", "knobs": {"gamma": 0.9}},
    })
    assert g2["status"] == "ok"

    connection.send({
        "type": "connect_nodes",
        "params": {"output_node": "grade_lift", "input_node": "grade_gamma"},
    })
