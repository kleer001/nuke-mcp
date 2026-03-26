# NukeMCP — Technical Reference

## Architecture

```
AI Client (Claude, etc.)
    │ stdio (JSON-RPC)
    ▼
MCP Server (src/nukemcp/)
    │ TCP socket (JSON)
    ▼
Nuke Addon (nuke_addon/)
    │ executeInMainThread (GUI) / queue dispatch (headless)
    ▼
Nuke's Python Environment
```

Three layers, each with a clear job:

1. **Nuke Addon** — runs inside Nuke, executes commands thread-safely, pushes real-time events via Nuke callbacks. Supports both GUI mode (executeInMainThread) and headless mode (queue-based dispatch).
2. **MCP Server** — FastMCP 2.14.x, tool annotations, version gating, mock mode for offline dev, auto-discovery, headless launch, plugin system, persistent memory.
3. **AI Guidance** — `CLAUDE.md` defines behavior rules: naming conventions, confirmation requirements, graph organization, memory usage.

## Bidirectional Events

The addon pushes real-time scene change events to the MCP server when subscribed:

- `node_created` / `node_deleted` — track graph changes
- `knob_changed` — parameter modifications
- `script_loaded` / `script_saved` — file operations

Subscribe via `subscribe_events()`, retrieve with `get_events()`.

## Memory System

NukeMCP maintains persistent memory across sessions:

- **`memory/facility.md`** — studio conventions (colorspace, naming, paths, preferred tools)
- **`memory/project/`** — auto-populated script snapshots
- **`memory/corrections.md`** — logged corrections from the compositor

Memory is exposed as MCP Resources (`nuke://memory/facility`, `nuke://memory/corrections`) for automatic context at session start.

## Plugin System

Extend NukeMCP without forking — drop Python files into `plugins/`:

```python
# plugins/my_studio_tools.py
def register(server):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def my_custom_tool(node_name: str) -> dict:
        """Studio-specific tool."""
        return conn.send_command("get_node_info", {"node_name": node_name})
```

See `plugins/README.md` for full details.

## Offline Development

Run the server against a mock Nuke socket — no Nuke installation required:

```bash
uv run nuke-mcp --mock                           # Default: NukeX 17.0v1
uv run nuke-mcp --mock --mock-variant Nuke        # Plain Nuke (no NukeX tools)
uv run nuke-mcp --mock --mock-version 15.0v1      # Older version
```

The mock maintains internal state (nodes, connections, settings) so sequential commands produce coherent responses.

## Version Gating

The addon reports its Nuke version and variant on connection. Tools that require NukeX or a minimum Nuke version are gated — they simply don't appear if the connected Nuke doesn't support them.

| Variant | Available |
|---|---|
| Nuke | Core tools (graph, script, comp, render, batch, templates) |
| NukeX | + Tracking, 3D, Deep, CopyCat |
| Nuke 17+ | + Gaussian Splats, BigCat, Annotations |
