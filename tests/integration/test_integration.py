"""Integration tests — run against a real headless Nuke instance.

Run with: uv run pytest -m integration
Requires Nuke + license. Skipped by default in CI and normal test runs.
"""

import pytest

pytestmark = pytest.mark.integration


def test_ping(integration_conn):
    resp = integration_conn.send({"type": "ping", "params": {}})
    assert resp["status"] == "ok"
    assert resp["result"] == "pong"


def test_get_script_info(integration_conn):
    resp = integration_conn.send({"type": "get_script_info", "params": {}})
    assert resp["status"] == "ok"
    result = resp["result"]
    assert "frame_range" in result
    assert "fps" in result
    assert "node_count" in result


def test_create_and_delete_node(integration_conn):
    conn = integration_conn

    # Create
    resp = conn.send({
        "type": "create_node",
        "params": {"node_class": "Grade", "name": "test_grade"},
    })
    assert resp["status"] == "ok"
    assert resp["result"]["class"] == "Grade"

    # Verify it exists
    resp = conn.send({"type": "get_node_info", "params": {"node_name": "test_grade"}})
    assert resp["status"] == "ok"

    # Delete
    resp = conn.send({"type": "delete_node", "params": {"node_name": "test_grade"}})
    assert resp["status"] == "ok"

    # Verify it's gone
    resp = conn.send({"type": "get_node_info", "params": {"node_name": "test_grade"}})
    assert resp["status"] == "error"


def test_connect_nodes(integration_conn):
    conn = integration_conn

    conn.send({"type": "create_node", "params": {"node_class": "Constant", "name": "const"}})
    conn.send({"type": "create_node", "params": {"node_class": "Grade", "name": "grade"}})

    resp = conn.send({
        "type": "connect_nodes",
        "params": {"output_node": "const", "input_node": "grade"},
    })
    assert resp["status"] == "ok"

    # Verify connection via node info
    resp = conn.send({"type": "get_node_info", "params": {"node_name": "grade"}})
    assert resp["status"] == "ok"
    assert "const" in resp["result"]["inputs"]


def test_modify_node_knobs(integration_conn):
    conn = integration_conn

    conn.send({"type": "create_node", "params": {"node_class": "Grade", "name": "g"}})

    resp = conn.send({
        "type": "modify_node",
        "params": {"node_name": "g", "knobs": {"white": 1.5}},
    })
    assert resp["status"] == "ok"

    resp = conn.send({"type": "get_node_info", "params": {"node_name": "g"}})
    assert resp["status"] == "ok"
    assert resp["result"]["knobs"]["white"] == 1.5


def test_set_frame_range(integration_conn):
    conn = integration_conn

    resp = conn.send({
        "type": "set_frame_range",
        "params": {"first": 1001, "last": 1100},
    })
    assert resp["status"] == "ok"

    resp = conn.send({"type": "get_script_info", "params": {}})
    assert resp["result"]["frame_range"] == [1001, 1100]


def test_find_nodes_by_type(integration_conn):
    conn = integration_conn

    conn.send({"type": "create_node", "params": {"node_class": "Grade", "name": "g1"}})
    conn.send({"type": "create_node", "params": {"node_class": "Grade", "name": "g2"}})
    conn.send({"type": "create_node", "params": {"node_class": "Blur", "name": "b1"}})

    resp = conn.send({"type": "find_nodes_by_type", "params": {"node_class": "Grade"}})
    assert resp["status"] == "ok"
    names = [n["name"] for n in resp["result"]["nodes"]]
    assert "g1" in names
    assert "g2" in names
    assert "b1" not in names


def test_version_gating(integration_conn):
    """Verify the handshake contains version and variant info."""
    conn = integration_conn
    assert conn.handshake is not None
    assert "nuke_version" in conn.handshake
    assert "variant" in conn.handshake
