# NukeMCP — Implementation Plan

> Concrete build order for the roadmap. Each step lists what to build, what it depends on, and how to verify it works.

---

## Current State

The repo is a skeleton: empty `src/main.py`, no `pyproject.toml`, no package structure. Everything below is built from scratch.

---

## Phase 1 — Foundation

### Step 1.1: Project Scaffolding

**Build:**
- `pyproject.toml` — package metadata, Python 3.10+ requirement, FastMCP 2.14.x dependency, `[project.scripts]` entry point (`nuke-mcp = "nukemcp.server:main"`), dev dependencies (pytest, ruff)
- Restructure `src/` to `src/nukemcp/` with proper `__init__.py`
- `src/nukemcp/tools/__init__.py`
- Delete old `src/main.py` and `src/__init__.py`
- Update `.gitignore` to include `rag_index/`, `memory/nodes/`, `memory/project/`

**Depends on:** Nothing.

**Verify:** `uv sync` installs the package. `uv run nuke-mcp --help` runs without import errors (even if it does nothing useful yet).

---

### Step 1.2: Nuke Addon (Socket Server)

**Build:**
- `nuke_addon/nuke_mcp_addon.py` — a socket server that:
  - Listens on a configurable port (default 54321)
  - Accepts JSON commands: `{"type": "command_name", "params": {...}}`
  - Executes them in Nuke's main thread via `nuke.executeInMainThread()`
  - Returns JSON responses: `{"status": "ok"|"error", "result": ..., "error": "..."}`
  - On connection, sends a handshake: `{"type": "handshake", "nuke_version": "17.0v1", "variant": "NukeX", "pid": 12345}`
  - Has a dockable PySide6 panel (with PySide2 fallback) showing: connection status, port, log of recent commands
  - Handles multiple reconnections gracefully (one client at a time)
- `nuke_addon/menu.py` — adds a "NukeMCP" menu item to Nuke's menu bar to launch/stop the server

**Depends on:** Nothing (can be built in parallel with 1.1).

**Verify:** Copy `nuke_addon/` into Nuke's scripts path. Launch Nuke. The panel appears. Connect with `nc localhost 54321` or a Python socket script and send `{"type": "ping"}` — get a response back.

**Key decisions:**
- PySide6 import with PySide2 fallback: `try: from PySide6 import ... except: from PySide2 import ...`
- All Nuke API calls wrapped in `nuke.executeInMainThread()` to avoid threading crashes
- Command dispatch via a simple dict mapping command names to handler functions — no framework, no magic
- Socket runs in a daemon thread; Nuke's main thread is never blocked
- Max message size: 10MB (covers large node graph queries)

---

### Step 1.3: Connection Layer

**Build:**
- `src/nukemcp/connection.py`:
  - `NukeConnection` class: connects to the addon socket, sends JSON commands, receives responses
  - Reconnect logic: if the socket drops, retry with exponential backoff (max 3 attempts)
  - Timeout: configurable per-command (default 10s, longer for heavy operations)
  - Handshake parsing: on connect, reads the handshake message and stores version/variant info
  - Clean disconnect on shutdown

**Depends on:** Step 1.2 (protocol definition, but can be coded against the spec before the addon exists).

**Verify:** With the addon running in Nuke, `NukeConnection("localhost", 54321)` connects, receives the handshake, and `connection.send({"type": "ping"})` returns a response. With Nuke not running, it fails gracefully with a clear error message.

---

### Step 1.4: Mock System

**Build:**
- `src/nukemcp/mock.py`:
  - `MockNukeSocket` class: mimics the addon's socket behavior without Nuke
  - Responds to the same JSON command protocol with realistic mock data
  - Handshake returns a configurable version/variant (default: NukeX 17.0v1)
  - Mock responses for all Phase 1 commands: `ping`, `get_script_info`, `get_node_info`, `create_node`, `modify_node`, `delete_node`, `connect_nodes`, `position_node`, `auto_layout`, `execute_python`, `load_script`, `save_script`, `set_project_settings`, `set_frame_range`
  - Maintains minimal internal state (list of nodes, connections) so sequential commands produce coherent responses
- `tests/mock_responses/` — JSON fixture files for each command

**Depends on:** Step 1.3 (uses the same interface as `NukeConnection`).

**Verify:** `uv run nuke-mcp --mock` starts the server without Nuke. All Phase 1 tools can be called and return coherent responses. Tests pass using the mock.

---

### Step 1.5: Version Detection & Tool Gating

**Build:**
- `src/nukemcp/version.py`:
  - `NukeVersion` dataclass: `major`, `minor`, `patch`, `variant` (Nuke/NukeX/NukeStudio)
  - `parse_version(handshake: dict) -> NukeVersion`
  - Guard decorators/functions:
    - `requires_nukex(func)` — tool only registered if variant is NukeX or NukeStudio
    - `requires_version(major, minor)` — tool only registered if version >= threshold
    - `requires_nuke17(func)` — shorthand for `requires_version(17, 0)`
  - These are used during tool registration, not at call time — unavailable tools simply don't appear

**Depends on:** Step 1.3 (needs handshake data).

**Verify:** Start server with mock variant "Nuke" (not NukeX) — NukeX-gated tools don't appear in the tool list. Start with mock version "16.0v5" — Nuke 17+ tools don't appear.

---

### Step 1.6: MCP Server & Core Graph Tools

**Build:**
- `src/nukemcp/server.py`:
  - FastMCP server initialization
  - CLI argument parsing: `--port` (addon port), `--mock` (use mock socket), `--host` (addon host, default localhost)
  - `main()` function as the entry point
  - Connects to the addon (or mock) on startup
  - Registers all tools from submodules

- `src/nukemcp/tools/graph.py` — core node manipulation:
  - `get_script_info()` — returns node count, script name, frame range, project settings. `readOnlyHint: true`
  - `get_node_info(node_name)` — returns node class, knob values, inputs, position. `readOnlyHint: true`
  - `create_node(node_class, name?, knobs?, position?)` — creates a node, returns its name and info
  - `modify_node(node_name, knobs)` — sets knob values on an existing node. `idempotentHint: true`
  - `delete_node(node_name, confirm)` — deletes a node. `destructiveHint: true`. Rejects if `confirm` is not `true`, returning a description of what would be deleted.
  - `connect_nodes(output_node, input_node, input_index?)` — connects two nodes
  - `position_node(node_name, x, y)` — sets a node's position. `idempotentHint: true`
  - `auto_layout(node_names?)` — auto-arranges selected or all nodes
  - `execute_python(code, confirm)` — executes arbitrary Python in Nuke. `destructiveHint: true`. Rejects without `confirm: true`.

**Depends on:** Steps 1.1, 1.3, 1.4, 1.5.

**Verify:** With `--mock`, all tools can be called from an MCP client (Claude Code, Claude Desktop). `create_node("Grade", name="hero_grade")` returns node info. `delete_node("hero_grade")` without `confirm: true` is rejected with a descriptive message.

---

### Step 1.7: Script Tools

**Build:**
- `src/nukemcp/tools/script.py`:
  - `load_script(path, confirm)` — opens a Nuke script. `destructiveHint: true` (replaces current script). Rejects without confirm.
  - `save_script(path?)` — saves the current script. `destructiveHint: true` if path differs from current (overwrite). Path optional (saves to current path).
  - `set_project_settings(fps?, colorspace?, resolution?)` — modifies root-level settings. `idempotentHint: true`
  - `set_frame_range(first, last)` — sets the script's frame range. `idempotentHint: true`

**Depends on:** Step 1.6 (same registration pattern).

**Verify:** `set_frame_range(1001, 1100)` succeeds. `load_script("/path/to/shot.nk")` without `confirm` is rejected.

---

### Step 1.8: CLAUDE.md & AI Behavior Rules

**Build:**
- `CLAUDE.md`:
  - Project description and architecture summary
  - Destructive action rules: always describe what you're about to do, ask for confirmation, pass `confirm: true` only after the user agrees
  - Node naming conventions: descriptive names, lowercase_with_underscores (e.g., `fg_key`, `bg_grade`, `hero_merge`)
  - Node organization: keep the graph flowing top-to-bottom, use Backdrop nodes to group related operations, label Dot nodes at junctions
  - When in doubt, use `get_node_info` and `get_script_info` to understand the current state before making changes
  - Never assume what nodes exist — always check first
  - Colorspace rules: respect the project's working colorspace, don't change it without asking
  - Memory instructions (placeholder for Phase 2)

**Depends on:** Steps 1.6, 1.7 (needs to reference actual tool names).

**Verify:** Load the project in Claude Code. Claude reads `CLAUDE.md` and follows the rules when interacting with the MCP tools.

---

### Step 1.9: Bootstrap & Configuration

**Build:**
- `bootstrap.sh`:
  - Checks for `uv` (installs if missing)
  - Runs `uv sync`
  - Prints the `.mcp.json` snippet to add to Claude Desktop / Claude Code config
  - Prints instructions for installing the Nuke addon
- `bootstrap.bat`: Windows equivalent
- `.mcp.json`: MCP server configuration for Claude Code (stdio transport, command = `uv run nuke-mcp`)

**Depends on:** Step 1.6 (server must be runnable).

**Verify:** Fresh clone → `./bootstrap.sh` → `uv run nuke-mcp --mock` starts successfully.

---

### Step 1.10: Tests & README

**Build:**
- `tests/test_graph.py` — tests for all graph tools using the mock socket
- `tests/test_script.py` — tests for all script tools using the mock socket
- `tests/test_version_gating.py` — tests that tools appear/disappear based on version/variant
- `tests/conftest.py` — shared fixtures (mock connection, mock server)
- `README.md`:
  - What NukeMCP is (one paragraph)
  - Requirements (Python 3.10+, Nuke 15+, uv)
  - Quick start (3 steps: clone, bootstrap, configure)
  - Nuke addon installation (copy to `.nuke/` or `NUKE_PATH`)
  - Connecting to Claude Desktop / Claude Code
  - Available tools (table with name, description, annotations)
  - Screenshots of the Nuke panel
  - Link to roadmap for future plans

**Depends on:** All previous steps.

**Verify:** `uv run pytest` passes. README instructions work on a fresh machine.

---

## Phase 1 — Dependency Graph

```
1.1 Scaffolding ──┐
                   ├──→ 1.3 Connection ──→ 1.4 Mock ──→ 1.5 Version ──→ 1.6 Server + Graph ──→ 1.7 Script ──→ 1.8 CLAUDE.md ──→ 1.9 Bootstrap ──→ 1.10 Tests + README
1.2 Nuke Addon ───┘
```

Steps 1.1 and 1.2 can be built in parallel. Everything else is sequential.

---

## Phase 1 — Exit Criteria

A compositor can:
1. Clone the repo and run `./bootstrap.sh`
2. Copy the addon into their Nuke scripts folder
3. Launch Nuke and see the NukeMCP panel
4. Add the `.mcp.json` config to Claude Code or Claude Desktop
5. Ask Claude to "create a Grade node connected to a Read node" and see it happen in Nuke
6. Try to delete a node and see Claude ask for confirmation first
7. See clear error messages if Nuke isn't running or the connection drops

A developer can:
1. Run `uv run nuke-mcp --mock` without Nuke installed
2. Run `uv run pytest` and see all tests pass
3. Read `CONTRIBUTING.md` (Phase 3 deliverable, but the pattern should be obvious from the code) and understand how to add a new tool

---

## Phase 2 — Memory & Learning

### Step 2.1: Memory File Structure

**Build:**
- `memory/` directory with `.gitkeep` files
- `memory/facility.md` — template with commented sections (colorspace, naming, render paths, preferred tools)
- `memory/corrections.md` — empty template with format example
- `memory/nodes/.gitkeep`
- `memory/project/.gitkeep`

**Depends on:** Phase 1 complete.

---

### Step 2.2: Memory Read/Write Module

**Build:**
- `src/nukemcp/memory.py`:
  - `read_memory(file_path)` — reads a memory file, returns contents
  - `write_memory(file_path, content)` — writes/updates a memory file
  - `append_memory(file_path, entry)` — appends to a memory file (for corrections log)
  - `list_memory_files()` — lists all files in the memory directory
  - `get_facility_memory()` — reads facility.md
  - `get_project_memory(project_name)` — reads project-specific memory
  - All exposed as MCP tools with appropriate annotations

**Depends on:** Step 2.1.

---

### Step 2.3: Auto-Population & Context Injection

**Build:**
- On connection, automatically read project settings from Nuke and write/update `memory/project/PROJECT_NAME.md` with frame range, colorspace, resolution, FPS
- On session start, inject facility memory and current project memory into the AI's context (via MCP Resources: `nuke://memory/facility`, `nuke://memory/project/{name}`, `nuke://memory/corrections`)
- `CLAUDE.md` update: instructions for when to read memory, when to update it, how to log corrections

**Depends on:** Steps 2.2 and 1.6.

---

### Step 2.4: Correction Logging

**Build:**
- When the compositor explicitly corrects the AI (e.g., "no, use IBK not Primatte"), the AI can call `log_correction(what_was_wrong, what_is_correct, context?)` to append to `corrections.md`
- Corrections are timestamped and tagged by context (node type, workflow, preference)
- `CLAUDE.md` update: after being corrected, offer to log the correction for future sessions

**Depends on:** Step 2.2.

**Exit criteria:** After three sessions, the memory directory contains facility preferences, project settings, and at least one logged correction. The AI references these on session start.

---

## Phase 3 — Production Tooling

### Step 3.1: Comp Tools (`comp.py`)
- `setup_keyer` (supports Primatte, IBK, Keylight — detects which are available)
- `setup_despill`, `setup_edge_blur`, `setup_basic_comp`
- `setup_grade_chain`, `setup_motion_blur`, `setup_light_wrap`, `setup_lens_distortion`
- Each returns a structured description of what was created and how it's connected

### Step 3.2: Render Tools (`render.py`)
- `setup_write_node` (codec presets: EXR, DPX, JPEG, MOV)
- `render_frames` (async via MCP Tasks — returns task handle, client polls for progress)
- `flipbook`, `set_proxy_mode`

### Step 3.3: Template Tools (`templates.py`)
- `load_toolset`, `save_toolset`, `list_toolsets`, `create_live_group`

### Step 3.4: Batch Tools (`batch.py`)
- `batch_set_knob`, `batch_reconnect`, `find_nodes_by_type`, `find_broken_reads`

### Step 3.5: MCP Resources & Prompts
- Resources: `nuke://script/info`, `nuke://script/nodes`, `nuke://script/selected`, `nuke://script/errors`
- Prompts: `greenscreen-comp`, `cg-integration`, `cleanup-plate`, `delivery-setup`

### Step 3.6: Documentation & Examples
- `BEST_PRACTICES.md`, `CONTRIBUTING.md`
- `docs/examples/` — 5-10 example prompt sessions

**Exit criteria:** Full greenscreen comp from natural language. AI has contextual awareness via Resources.

---

## Phase 4 — Advanced Features (NukeX / Nuke 17)

### Step 4.1: Tracking (`tracking.py`)
### Step 4.2: 3D & USD Geo (`threed.py`)
### Step 4.3: Deep Compositing (`deep.py`)
### Step 4.4: ML — CopyCat & BigCat (`ml.py`)
### Step 4.5: Gaussian Splats (`splats.py`)
### Step 4.6: Annotations (`annotations.py`)
### Step 4.7: Version guard tests for all gated tools

**Exit criteria:** All advanced tools implemented with version guards. Nuke 17 features available when supported.

---

## Phase 5 — Documentation Grounding (RAG)

### Step 5.1: BM25 index implementation (`rag.py`)
### Step 5.2: Doc ingestion script (`scripts/ingest_docs.py`)
### Step 5.3: Nukepedia + facility doc ingestion
### Step 5.4: RAG integration into tool responses

**Exit criteria:** Accurate, documentation-backed answers about obscure knobs and new Nuke 17 nodes.

---

## Phase 6 — Bidirectional Events

### Step 6.1: Event push from addon (`nuke_addon/events.py`)
### Step 6.2: Event receiver in server (`src/nukemcp/events.py`)
### Step 6.3: Event filtering and subscription config
### Step 6.4: GSV change events (Nuke 17+)

**Exit criteria:** AI observes compositor working and offers relevant suggestions.

---

## Phase 7 — Ecosystem & Community

### Step 7.1: PyPI publishing
### Step 7.2: CI with automated tests
### Step 7.3: Plugin system for facility extensions
### Step 7.4: Multi-client documentation
### Step 7.5: MCP Registry listing
### Step 7.6: Community prompt library

---

## Build Order Summary

```
Phase 1: Foundation
  1.1 Scaffolding          ─┐ parallel
  1.2 Nuke Addon           ─┘
  1.3 Connection Layer
  1.4 Mock System
  1.5 Version Detection
  1.6 Server + Graph Tools
  1.7 Script Tools
  1.8 CLAUDE.md
  1.9 Bootstrap Scripts
  1.10 Tests + README

Phase 2: Memory
  2.1 File Structure
  2.2 Read/Write Module
  2.3 Auto-Population
  2.4 Correction Logging

Phase 3: Production Tooling
  3.1 Comp Tools
  3.2 Render Tools
  3.3 Template Tools
  3.4 Batch Tools
  3.5 Resources & Prompts
  3.6 Docs & Examples

Phase 4: Advanced (NukeX/17)
  4.1–4.7 (can be built in any order within the phase)

Phase 5: RAG
  5.1–5.4 (sequential)

Phase 6: Events
  6.1–6.4 (sequential)

Phase 7: Ecosystem
  7.1–7.6 (can be built in any order)
```

Each phase has a clear exit criteria defined in the roadmap. Don't start a new phase until the previous phase's exit criteria are met.
