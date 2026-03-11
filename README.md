# NukeMCP

An MCP server for Foundry Nuke — AI copilot for compositors.

NukeMCP connects AI assistants (Claude, ChatGPT, local LLMs) to a running Nuke session via the [Model Context Protocol](https://modelcontextprotocol.io). Describe what you want in plain English, and the AI creates, connects, and configures nodes in your comp.

## Status

**Phase 1 — Foundation.** Core tools verified end-to-end against Nuke 17.0v1. Memory, production comp workflows, and advanced NukeX tools are on the [roadmap](nuke_mcp_roadmap.md).

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Foundry Nuke 15+ (16+ recommended for PySide6, 17+ for full feature set)
- An MCP-compatible AI client (Claude Code, Claude Desktop, etc.)

## Quick Start

```bash
# Clone and install
git clone https://github.com/kleer001/nuke-mcp.git
cd nuke-mcp
uv sync

# Find Nuke on your machine and check licensing
uv run nuke-mcp --discover

# Run with mock Nuke (no Nuke required)
uv run nuke-mcp --mock

# Launch headless Nuke and connect automatically
uv run nuke-mcp --headless

# Run tests
uv run pytest -v
```

## Nuke Addon Setup

Copy the addon into your Nuke scripts directory:

```bash
cp nuke_addon/nuke_mcp_addon.py ~/.nuke/
```

Or add the `nuke_addon/` directory to your `NUKE_PATH`.

Launch Nuke — in the Script Editor, run:

```python
import nuke_mcp_addon
nuke_mcp_addon.start()
```

A **NukeMCP** panel appears with Start/Stop button and log. The server listens on port 54321.

## Headless Mode

NukeMCP can auto-discover and launch Nuke without a GUI:

```bash
# Auto-discover Nuke, launch headless, connect
uv run nuke-mcp --headless

# Specify a Nuke executable
uv run nuke-mcp --headless --nuke-path /usr/local/Nuke17.0v1/Nuke17.0

# Just find Nuke installations and check licensing
uv run nuke-mcp --discover
```

Discovery searches standard paths (`/usr/local/Nuke*`, `/Applications/Nuke*`), `.desktop` files, running processes, mounted volumes, and the `NUKE_EXE` environment variable. It also detects Foundry trial licenses (JWT tokens) and RLM license servers.

## Connecting to an AI Client

### Claude Code

The included `.mcp.json` configures the server automatically. Run Claude Code from the project root.

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "nuke-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/nuke-mcp", "nuke-mcp"]
    }
  }
}
```

## Available Tools

13 core tools available on all Nuke variants, plus gated tools for NukeX and Nuke 17+. Destructive tools require user confirmation — enforced at the code level, not just in the AI's instructions.

<details>
<summary>Full tool list (40+ tools)</summary>

### Core (all variants)

| Tool | Description | Annotations |
|---|---|---|
| `get_script_info` | Script name, frame range, FPS, colorspace, node count | readOnly |
| `get_node_info` | Node class, position, inputs, knob values | readOnly |
| `create_node` | Create a node with optional name, knobs, position | |
| `modify_node` | Set knob values on an existing node | idempotent |
| `delete_node` | Delete a node (requires confirmation) | destructive |
| `connect_nodes` | Connect output of one node to input of another | |
| `position_node` | Set node position in the graph | idempotent |
| `auto_layout` | Auto-arrange nodes | |
| `execute_python` | Run arbitrary Python in Nuke (requires confirmation) | destructive |
| `load_script` | Open a .nk file (requires confirmation) | destructive |
| `save_script` | Save the current script (requires confirmation) | destructive |
| `set_project_settings` | Set FPS, colorspace, resolution | idempotent |
| `set_frame_range` | Set first/last frame | idempotent |

### Comp & Rendering

| Tool | Description |
|---|---|
| `render_frames` | Render a Write node over a frame range |
| `set_proxy_mode` | Toggle proxy mode |
| `find_nodes_by_type` | Find all nodes of a given class |
| `find_broken_reads` | Find Read nodes with missing files |
| `find_error_nodes` | Find all nodes in error state |
| `batch_set_knob` | Set a knob value on multiple nodes |
| `batch_reconnect` | Reconnect multiple nodes to a new input |

### Templates & LiveGroups

| Tool | Description |
|---|---|
| `list_toolsets` | List saved toolsets |
| `load_toolset` | Load a toolset |
| `save_toolset` | Save selected nodes as a toolset |
| `create_live_group` | Create a LiveGroup from nodes |

### NukeX (gated)

| Tool | Description |
|---|---|
| `create_tracker` | Create a Tracker4 node |
| `solve_tracker` | Execute tracking |
| `setup_stabilize` | Set tracker to stabilize mode |
| `create_camera_tracker` | Create a CameraTracker node |
| `create_3d_camera` | Create a 3D camera |
| `create_3d_light` | Create a 3D light |
| `create_deep_merge` | Deep compositing merge |
| `create_deep_recolor` | Deep recolor node |
| `create_copycat` | CopyCat ML training node |

### Nuke 17+ (gated)

| Tool | Description |
|---|---|
| `create_splat_reader` | Gaussian splat reader |
| `create_annotation` | Create annotation/sticky note |
| `list_annotations` | List all annotations |

</details>

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

1. **Nuke Addon** — runs inside Nuke, executes commands thread-safely, reports version/variant. Supports both GUI mode (executeInMainThread) and headless mode (queue-based dispatch).
2. **MCP Server** — FastMCP 2.14.x, tool annotations, version gating, mock mode for offline dev, auto-discovery and headless launch.
3. **AI Guidance** — `CLAUDE.md` defines behavior rules: naming conventions, confirmation requirements, graph organization.

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
| NukeX | + Tracking, 3D, Deep, CopyCat/BigCat |
| Nuke 17+ | + Gaussian Splats, Annotations |

## Roadmap

See [nuke_mcp_roadmap.md](nuke_mcp_roadmap.md) for the full vision and phased plan. See [IMPLEMENTATION.md](IMPLEMENTATION.md) for the concrete build steps.

**Phases:**
1. Foundation (current)
2. Memory & Learning
3. Production Tooling
4. Advanced Features (NukeX / Nuke 17)
5. Documentation Grounding (RAG)
6. Bidirectional Events
7. Ecosystem & Community

## Acknowledgments

This project builds on the work of several open-source contributors:

- **[dughogan/nuke_mcp](https://github.com/dughogan/nuke_mcp)** — the right architecture and the right spirit. Clean, compositor-readable code with a clear socket-based design. Doug Hogan's [fxphd course](https://www.fxphd.com/details/707/) made the concept accessible to the compositing community.
- **[flowagent-sh/nuke-mcp](https://github.com/flowagent-sh/nuke-mcp)** — demonstrated that the feature set can be production-grade, with camera tracking, deep compositing, and ML integration.
- **[kleer001/houdini-mcp](https://github.com/kleer001/houdini-mcp)** — the persistent memory system, CLAUDE.md behavioral rules, BM25-based RAG, bidirectional events, and the proof that a DCC MCP can be a serious piece of software engineering.

## License

MIT
