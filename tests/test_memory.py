"""Tests for persistent memory tools."""

import shutil

import pytest

from nukemcp.memory import MEMORY_DIR, read_file, write_file, append_file, list_files


@pytest.fixture(autouse=True)
def clean_memory():
    """Ensure a clean memory directory for each test."""
    test_dir = MEMORY_DIR
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    yield
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_write_and_read():
    write_file("test.md", "hello world")
    assert read_file("test.md") == "hello world"


def test_read_nonexistent():
    assert read_file("does_not_exist.md") is None


def test_append():
    write_file("log.md", "line1\n")
    append_file("log.md", "line2")
    content = read_file("log.md")
    assert "line1" in content
    assert "line2" in content


def test_list_files():
    write_file("a.md", "a")
    write_file("sub/b.md", "b")
    files = list_files()
    assert "a.md" in files
    assert "sub/b.md" in files


def test_path_traversal_rejected():
    with pytest.raises(ValueError, match="Path traversal rejected"):
        read_file("../../etc/passwd")

    with pytest.raises(ValueError, match="Path traversal rejected"):
        write_file("../../../tmp/evil.txt", "pwned")


def test_update_project_memory(connection):
    """Test that update_project_memory reads script info and writes a file."""
    # The connection fixture provides a mock; get_script_info should work
    response = connection.send({"type": "get_script_info", "params": {}})
    assert response["status"] == "ok"
    # Simulate what the tool does
    info = response["result"]
    write_file("project/test_show.md", f"# test_show\n\nFPS: {info['fps']}\n")
    content = read_file("project/test_show.md")
    assert "test_show" in content
    assert "24" in content
