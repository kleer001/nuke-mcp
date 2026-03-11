"""Tests for annotation tools."""


def test_create_annotation(connection):
    response = connection.send({
        "type": "create_annotation",
        "params": {"text": "Hello world", "name": "note1"},
    })
    assert response["status"] == "ok"
    assert response["result"]["name"] == "note1"
    assert response["result"]["text"] == "Hello world"


def test_create_annotation_with_position(connection):
    response = connection.send({
        "type": "create_annotation",
        "params": {"text": "Positioned", "name": "note2", "position": [100, 200]},
    })
    assert response["status"] == "ok"


def test_list_annotations(connection):
    connection.send({
        "type": "create_annotation",
        "params": {"text": "Note A", "name": "ann_a"},
    })
    connection.send({
        "type": "create_annotation",
        "params": {"text": "Note B", "name": "ann_b"},
    })

    response = connection.send({"type": "list_annotations", "params": {}})
    assert response["status"] == "ok"
    names = [a["name"] for a in response["result"]["annotations"]]
    assert "ann_a" in names
    assert "ann_b" in names
