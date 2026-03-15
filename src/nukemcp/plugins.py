"""Plugin auto-discovery — load tool modules from a plugins directory."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer

log = logging.getLogger(__name__)


def load_plugins(server: NukeMCPServer, plugins_dir: Path | None = None):
    """Auto-discover and register plugin modules from the plugins directory.

    Plugins are Python files in the plugins directory with a ``register(server)``
    function, following the same pattern as the built-in tool modules.
    """
    if plugins_dir is None:
        plugins_dir = Path(__file__).parent.parent.parent / "plugins"
    if not plugins_dir.is_dir():
        return

    for path in sorted(plugins_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"nukemcp_plugin_{path.stem}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "register"):
                mod.register(server)
                log.info("Loaded plugin: %s", path.name)
            else:
                log.warning("Plugin %s has no register() function, skipping", path.name)
        except Exception:
            log.exception("Failed to load plugin: %s", path.name)
