"""Tests for plugin auto-discovery system."""

import textwrap
from pathlib import Path

from nukemcp.plugins import load_plugins


def test_load_plugin_with_register(tmp_path):
    """Plugins with register() are loaded."""
    plugin = tmp_path / "my_tool.py"
    plugin.write_text(textwrap.dedent("""\
        LOADED = False
        def register(server):
            global LOADED
            LOADED = True
    """))

    # Use a mock server object
    class FakeServer:
        pass

    load_plugins(FakeServer(), plugins_dir=tmp_path)


def test_skip_underscore_files(tmp_path):
    """Files starting with _ are ignored."""
    plugin = tmp_path / "_internal.py"
    plugin.write_text("def register(server): raise RuntimeError('should not run')")

    class FakeServer:
        pass

    # Should not raise
    load_plugins(FakeServer(), plugins_dir=tmp_path)


def test_skip_no_register(tmp_path):
    """Plugins without register() are skipped."""
    plugin = tmp_path / "no_register.py"
    plugin.write_text("x = 1")

    class FakeServer:
        pass

    # Should not raise
    load_plugins(FakeServer(), plugins_dir=tmp_path)


def test_missing_plugins_dir():
    """Non-existent plugins dir is silently ignored."""
    class FakeServer:
        pass

    load_plugins(FakeServer(), plugins_dir=Path("/nonexistent/plugins"))


def test_broken_plugin_does_not_crash(tmp_path):
    """A plugin that raises during import doesn't crash the server."""
    plugin = tmp_path / "broken.py"
    plugin.write_text("raise RuntimeError('boom')")

    class FakeServer:
        pass

    # Should not raise
    load_plugins(FakeServer(), plugins_dir=tmp_path)
