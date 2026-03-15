# Contributing to NukeMCP

## Adding a New Tool

NukeMCP tools follow a consistent pattern. To add a new tool:

### 1. Create or edit a tool module

Tool modules live in `src/nukemcp/tools/`. Each module has a `register(server)` function:

```python
"""My tool module — short description."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nukemcp.tools._helpers import create_node as _create, connect_nodes as _connect

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    # Optional: gate on NukeX or version
    if not server.version.is_nukex:
        return

    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def my_tool(param: str, name: str = "default") -> dict:
        """One-line description shown to the AI.

        Args:
            param: What this parameter does.
            name: Name for the created node.
        """
        node = _create(conn, "NodeClass", name)
        return {"node": node}
```

### 2. Register the module

Add your import and `register()` call in `src/nukemcp/server.py`:

```python
from nukemcp.tools import graph, script, ..., my_module

# In build_server():
my_module.register(server)
```

### 3. Add a mock command (if needed)

If your tool uses a new addon command (not just `create_node`/`connect_nodes`), add a handler to both:

- **`nuke_addon/nuke_mcp_addon.py`** — the real Nuke handler (add `_handle_my_command` and register in `COMMANDS`)
- **`src/nukemcp/mock.py`** — the mock handler (add `_cmd_my_command` to `MockNukeState`)

### 4. Write tests

Create `tests/test_my_module.py` following the existing pattern:

```python
"""Tests for my_module tools."""


def test_my_tool(connection):
    """Describe what this test verifies."""
    connection.send({"type": "create_node", "params": {"node_class": "Read", "name": "src"}})

    resp = connection.send({
        "type": "create_node",
        "params": {"node_class": "NodeClass", "name": "my_node"},
    })
    assert resp["status"] == "ok"
```

Tests use the `connection` fixture from `tests/conftest.py`, which connects to a `MockNukeServer`.

### 5. Run the suite

```bash
uv run pytest -v          # All mock tests
uv run ruff check src/    # Lint
```

## Version Gating

Gate tools on Nuke variant or version in `register()`:

```python
def register(server):
    if not server.version.is_nukex:
        return  # NukeX-only tools

    if not server.version.at_least(17):
        return  # Nuke 17+ only
```

The server integration tests in `tests/test_server_integration.py` verify that gated tools don't appear for lower variants.

## Destructive Tools

Tools that modify or delete data must use the confirmation pattern:

```python
@mcp.tool(annotations={"destructiveHint": True})
def dangerous_tool(node_name: str, confirm: bool = False) -> dict:
    if not confirm:
        return {"action": "dangerous_tool", "node": node_name, "message": "Confirm to proceed."}
    return conn.send_command("dangerous_command", {"node_name": node_name})
```

## Facility Plugins

Facilities can extend NukeMCP without forking by dropping Python files into `plugins/`. See `plugins/README.md`.

## Code Style

- `ruff check` must pass
- `snake_case` for functions/variables, `PascalCase` for classes
- Target Python 3.10+
- No external dependencies beyond `fastmcp`
