"""Tests for shared _helpers (create_node, connect_nodes)."""


def test_create_node_basic(connection):
    from nukemcp.tools._helpers import create_node
    name = create_node(connection, "Blur")
    assert "Blur" in name


def test_create_node_with_name(connection):
    from nukemcp.tools._helpers import create_node
    name = create_node(connection, "Grade", name="MyGrade")
    assert name == "MyGrade"


def test_create_node_with_knobs(connection):
    from nukemcp.tools._helpers import create_node
    name = create_node(connection, "Grade", name="G1", knobs={"white": 1.5})
    info = connection.send_command("get_node_info", {"node_name": name})
    assert info["knobs"]["white"] == 1.5


def test_connect_nodes_success(connection):
    from nukemcp.tools._helpers import create_node, connect_nodes
    a = create_node(connection, "Read", name="ReadA")
    b = create_node(connection, "Grade", name="GradeB")
    # Should not raise
    connect_nodes(connection, a, b)


def test_connect_nodes_missing_node(connection):
    import pytest
    from nukemcp.tools._helpers import create_node, connect_nodes
    a = create_node(connection, "Read", name="ReadX")
    with pytest.raises(RuntimeError, match="not found"):
        connect_nodes(connection, a, "nonexistent_node")
