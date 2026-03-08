"""Tests for version detection and gating."""

from nukemcp.version import parse_version, NukeVersion


def test_parse_standard_version():
    v = parse_version({"nuke_version": "17.0v1", "variant": "NukeX"})
    assert v.major == 17
    assert v.minor == 0
    assert v.patch == "v1"
    assert v.variant == "NukeX"


def test_parse_older_version():
    v = parse_version({"nuke_version": "15.1v3", "variant": "Nuke"})
    assert v.major == 15
    assert v.minor == 1
    assert v.patch == "v3"
    assert v.variant == "Nuke"


def test_parse_malformed_version():
    v = parse_version({"nuke_version": "garbage", "variant": "Nuke"})
    assert v.major == 0
    assert v.minor == 0


def test_is_nukex():
    v = NukeVersion(17, 0, "v1", "NukeX")
    assert v.is_nukex
    assert not v.is_studio


def test_is_studio():
    v = NukeVersion(17, 0, "v1", "NukeStudio")
    assert v.is_nukex  # Studio implies X
    assert v.is_studio


def test_is_plain_nuke():
    v = NukeVersion(17, 0, "v1", "Nuke")
    assert not v.is_nukex
    assert not v.is_studio


def test_at_least():
    v = NukeVersion(17, 0, "v1", "NukeX")
    assert v.at_least(17, 0)
    assert v.at_least(16, 0)
    assert v.at_least(17)
    assert not v.at_least(18, 0)
    assert not v.at_least(17, 1)


def test_handshake_connection(connection):
    """Verify the mock connection provides valid handshake data."""
    assert connection.handshake is not None
    assert connection.handshake["type"] == "handshake"
    assert "nuke_version" in connection.handshake
    assert "variant" in connection.handshake
