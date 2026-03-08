# NukeMCP

An MCP server for Foundry Nuke — AI copilot for compositors.

NukeMCP connects AI assistants (Claude, ChatGPT, local LLMs) to a running Nuke session via the [Model Context Protocol](https://modelcontextprotocol.io). Describe what you want in plain English, and the AI creates, connects, and configures nodes in your comp.

## Status

**Phase 1 — Foundation.** Core node graph and script tools are implemented. Memory, production comp workflows, and advanced NukeX tools are on the [roadmap](nuke_mcp_roadmap.md).

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
./bootstrap.sh    # or bootstrap.bat on Windows

# Run with mock Nuke (no Nuke required)
uv run nuke-mcp --mock

# Run tests
uv run pytest -v
```

## Nuke Addon Setup

Copy the addon files into your Nuke scripts directory:

```bash
cp nuke_addon/nuke_mcp_addon.py ~/.nuke/
cp nuke_addon/menu.py ~/.nuke/
```

Or add the `nuke_addon/` directory to your `NUKE_PATH`.

Launch Nuke — a **NukeMCP** menu appears. Click **Start Server** to open the panel and begin listening for connections.

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

Destructive tools require the AI to ask for user confirmation before executing. This is enforced at the code level — not just in the AI's instructions.

## Architecture

```
AI Client (Claude, etc.)
    │ stdio (JSON-RPC)
    ▼
MCP Server (src/nukemcp/)
    │ TCP socket (JSON)
    ▼
Nuke Addon (nuke_addon/)
    │ nuke.executeInMainThread()
    ▼
Nuke's Python Environment
```

Three layers, each with a clear job:

1. **Nuke Addon** — runs inside Nuke, executes commands in the main thread, reports version/variant
2. **MCP Server** — FastMCP 2.14.x, tool annotations, version gating, mock mode for offline dev
3. **AI Guidance** — `CLAUDE.md` defines behavior rules: naming conventions, confirmation requirements, graph organization

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
| Nuke | Core tools (graph, script, comp, render) |
| NukeX | + Tracking, 3D, Deep, CopyCat/BigCat |
| Nuke 17+ | + Gaussian Splats, USD Geo, Annotations |

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
