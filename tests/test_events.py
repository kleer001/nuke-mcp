"""Tests for event system."""

from nukemcp.events import EventLog, EVENT_TYPES


def test_subscribe_all():
    log = EventLog()
    log.subscribe()
    assert log.subscriptions == set(EVENT_TYPES)


def test_subscribe_specific():
    log = EventLog()
    log.subscribe(["node_created", "node_deleted"])
    assert log.subscriptions == {"node_created", "node_deleted"}


def test_subscribe_filters_invalid():
    log = EventLog()
    log.subscribe(["node_created", "fake_event"])
    assert log.subscriptions == {"node_created"}


def test_add_event():
    log = EventLog()
    log.subscribe(["node_created"])
    log.add({"event_type": "node_created", "data": {"name": "Grade1"}})
    assert len(log.get_recent()) == 1
    assert log.get_recent()[0]["data"]["name"] == "Grade1"


def test_add_unsubscribed_event():
    log = EventLog()
    log.subscribe(["node_deleted"])
    log.add({"event_type": "node_created", "data": {}})
    assert len(log.get_recent()) == 0


def test_max_events():
    log = EventLog(max_events=5)
    log.subscribe()
    for i in range(10):
        log.add({"event_type": "node_created", "data": {"i": i}})
    assert len(log.events) == 5
    assert log.events[0]["data"]["i"] == 5  # Oldest retained


def test_clear():
    log = EventLog()
    log.subscribe()
    log.add({"event_type": "node_created", "data": {}})
    log.clear()
    assert len(log.events) == 0


def test_subscribe_events_mock(connection):
    """Test the subscribe_events addon command via mock."""
    response = connection.send({
        "type": "subscribe_events",
        "params": {"event_types": ["node_created", "node_deleted"]},
    })
    assert response["status"] == "ok"
    assert "node_created" in response["result"]["subscribed"]


def test_event_push_received(mock_server, mock_port):
    """Test that pushed events are received by the connection's event handler."""
    import time
    from nukemcp.connection import NukeConnection

    received = []

    conn = NukeConnection("127.0.0.1", mock_port)
    conn.set_event_handler(lambda msg: received.append(msg))
    conn.connect()

    # Push an event from the mock server
    mock_server.push_event("node_created", {"name": "Grade1", "class": "Grade"})

    # Give the reader thread time to process
    for _ in range(50):
        if received:
            break
        time.sleep(0.02)

    assert len(received) == 1
    assert received[0]["type"] == "event"
    assert received[0]["event_type"] == "node_created"
    assert received[0]["data"]["name"] == "Grade1"

    conn.disconnect()
