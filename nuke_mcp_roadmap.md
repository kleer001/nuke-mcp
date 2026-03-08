# NukeMCP — Vision & Roadmap

> *An open-source AI copilot for Nuke compositors. Production-grade tooling, compositor-readable code, memory that learns your pipeline.*

---

## The 10,000 Foot Vision

NukeMCP is not a novelty demo. It is not a tool that impresses in a two-minute clip and then sits unused. It is a persistent, intelligent layer between an AI assistant and a working compositor's node graph — one that understands Nuke at a technical level, respects the compositor's creative control, learns how a specific facility works over time, and earns trust by never doing anything dangerous without asking first.

The broader goal is this: a junior compositor should be able to describe a comp setup in plain English and get a working, well-organized node graph. A senior compositor should be able to offload the tedious setup work — keyers, grades, write nodes, LiveGroups, render submits — and stay focused on the creative decisions only they can make. A pipeline TD should be able to extend the tool in an afternoon without reading the entire codebase.

Where existing Nuke MCP projects either built something lean and learnable (dughogan) or something feature-rich but murky (flowagent-sh), NukeMCP aims for both at once. Where kleer001's houdini-mcp showed that a DCC MCP can have memory, documentation grounding, bidirectional events, and proper software engineering practices, NukeMCP brings those ideas into the compositing space.

The result should feel less like a chatbot that happens to know Nuke's Python API, and more like a compositor's technical assistant who knows your scripts, your facility conventions, your preferred keyers, and your render farm.

---

## Guiding Principles

**Compositor-first, not engineer-first.** Every design decision should be evaluated from the perspective of a working compositor. The code should be readable by someone who knows Python and Nuke scripting. The setup should not require Node.js, Docker, or a PhD.

**Trust is earned, not assumed.** The AI should never delete nodes, overwrite scripts, or trigger renders without explicit confirmation. Destructive actions require confirmation at multiple levels: AI behavior rules in `CLAUDE.md`, MCP tool annotations (`destructiveHint: true`), and code-level enforcement in the server. The tool should fail loudly and obviously rather than silently and subtly.

**Depth over breadth, deliberately.** Every tool that exists should work reliably and handle edge cases gracefully before new tools are added. A smaller set of solid tools is worth more than a large set of fragile ones.

**Persistent memory makes it useful long-term.** A tool that forgets everything between sessions is a toy. A tool that remembers your facility's conventions, your preferred node naming, your project's frame range and colorspace, and your past corrections — that is a workflow partner.

**It should be easy to extend.** Any pipeline TD should be able to add a new tool in under an hour by following a clear pattern. No framework magic. No hidden complexity.

**Client-agnostic by design.** The MCP server should work with any MCP-compatible client — Claude Desktop, Claude Code, ChatGPT (via HTTP wrapper), local LLMs via Ollama, or custom integrations. AI-specific behavior rules live in `CLAUDE.md` and similar files, not in the server code.

---

## Architecture Overview

The system has three layers, each with a clean separation of concerns.

### Layer 1 — The Nuke Addon (`nuke_mcp_addon.py`)

Runs inside Nuke. Creates a socket server that listens for JSON commands, executes them in Nuke's Python environment, and returns structured responses. Has a minimal dockable UI panel (PySide6 for Nuke 16+, PySide2 for older versions) showing connection status, port, and a log of recent commands. Reports Nuke version and variant (Nuke / NukeX / NukeStudio) on connection so the server layer can guard version-specific tools.

Optionally pushes scene events (node creation, parameter changes, errors) to the MCP server for real-time AI awareness, following the bidirectional event pattern established by kleer001's houdini-mcp.

This file is intentionally kept as close to vanilla Python as possible. No external dependencies beyond what Nuke ships with. Any compositor should be able to open this file and understand what it does.

### Layer 2 — The MCP Server (`src/nukemcp/`)

A proper Python package. Uses FastMCP 2.14.x (targets MCP spec `2025-11-25`). Organized into submodules by domain rather than one monolithic file. Connects to the Nuke addon via TCP socket. Communicates with AI clients via stdio transport. Handles version guards, error formatting, and response normalization.

**MCP Primitives Used:**

- **Tools** — The primary interface. All tools carry annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) so clients can make informed confirmation decisions.
- **Resources** — Expose read-only scene state (node graph overview, project settings, current frame, colorspace) as contextual data the AI can reference without explicit tool calls.
- **Prompts** — Reusable workflow templates ("set up a greenscreen comp", "create a CG integration template", "configure Write node for EXR delivery") that users can invoke as standardized starting points.
- **Tasks** — Long-running operations (renders, BigCat/CopyCat training, camera solves) return async task handles that clients can poll for progress, avoiding connection blocking.

**Submodules:**
- `tools/graph.py` — node creation, modification, deletion, connection, positioning, layout
- `tools/comp.py` — high-level compositing workflows: keying pipelines, grade chains, merge setups, light wraps, motion blur
- `tools/script.py` — script-level operations: load, save, project settings, frame range, colorspace
- `tools/render.py` — render control, Write node setup, proxy modes, flipbook
- `tools/tracking.py` — 2D tracking, camera tracking, solve operations, reconcile 3D
- `tools/threed.py` — 3D scene setup, camera, geometry, ScanlineRender, USD/Geo nodes (NukeX-gated)
- `tools/deep.py` — Deep compositing pipeline setup (NukeX-gated)
- `tools/ml.py` — CopyCat and BigCat node setup, training, and inference (NukeX-gated)
- `tools/splats.py` — Gaussian Splat import, SplatRender setup, Field nodes (Nuke 17+)
- `tools/templates.py` — Toolset and LiveGroup load/save/manage
- `tools/batch.py` — batch operations across multiple nodes or scripts
- `tools/annotations.py` — programmatic annotation creation and management (Nuke 17+)
- `version.py` — version detection and tool gating
- `memory.py` — read/write to the persistent memory directory
- `rag.py` — documentation retrieval for grounded, accurate node/tool descriptions
- `events.py` — bidirectional event handling (scene changes pushed from Nuke addon)
- `resources.py` — MCP Resources exposing scene state
- `prompts.py` — MCP Prompts for reusable workflow templates

### Layer 3 — AI Guidance (`CLAUDE.md`, `CLAUDE_GENERIC.md`, `BEST_PRACTICES.md`)

Markdown files that shape how the AI behaves when connected to this tool. These are not documentation for humans — they are instructions read by the AI at the start of every session. They define when to ask before acting, how to name nodes, how to organize the node graph, and what a well-structured Nuke script looks like. This is the layer that makes the difference between an AI that crashes your script and one that a compositor would actually trust.

For non-Claude clients, `BEST_PRACTICES.md` serves as a client-agnostic reference that can be adapted into system prompts for ChatGPT, Ollama, or other LLMs.

---

## Key Features

### Version-Aware Tool Gating

On connection, the Nuke addon reports its version string and variant. The MCP server uses this to determine which tools are available:

- **Plain Nuke:** Core tools only (graph, comp, script, render, templates, batch)
- **NukeX:** Adds tracking, 3D, deep compositing, CopyCat/BigCat
- **NukeStudio:** Adds timeline tools (future)
- **Nuke 17+:** Adds Gaussian Splats, USD Geo nodes, BigCat, Annotations API, GSV automation
- **Nuke 16+:** PySide6 UI, OpenAssetIO

Tools requiring a minimum version number warn gracefully rather than failing silently. This is something no existing Nuke MCP does.

### MCP Tool Annotations

Every tool carries semantic annotations per the MCP `2025-11-25` spec:

- `readOnlyHint: true` — tools that inspect without modifying (e.g., `get_node_info`, `get_script_info`)
- `destructiveHint: true` — tools that delete or overwrite (e.g., `delete_node`, `save_script`)
- `idempotentHint: true` — tools safe to retry (e.g., `set_parameter`, `set_frame_range`)

Clients use these annotations to decide which tools need user confirmation prompts. This is defense-in-depth alongside `CLAUDE.md` soft guards.

### Persistent Memory (`memory/`)

A local directory of plain-text and JSON files written by the AI and read back at the start of sessions. Organized into:

- `facility.md` — facility-wide conventions (colorspace, naming conventions, render paths, project structure)
- `project/PROJ_NAME.md` — per-project notes (frame range, shot conventions, known issues)
- `nodes/` — per-node-type notes the AI accumulates about how specific nodes behave, their quirks, and useful parameter combinations
- `corrections.md` — a running log of things the compositor corrected, so the AI can avoid repeating mistakes

This is inspired directly by kleer001's houdini-mcp "AI Academy" approach. Over time, the tool becomes better calibrated to how a specific artist or facility works.

### Documentation RAG (`rag.py`)

The AI's built-in knowledge of Nuke's Python API is often incomplete or outdated. `rag.py` provides a retrieval layer using a BM25 full-text index (pure stdlib, no external dependencies, following the houdini-mcp pattern) that can ingest:

- Nuke's official Python Developer Guide (local copy)
- Nukepedia gizmo READMEs and documentation
- A facility's internal toolset documentation
- Foundry release notes for the connected version

When the AI needs to know what knobs a node has, or what a particular parameter does, it can query this instead of guessing. This is especially valuable for third-party gizmos, facility-specific tools, and new Nuke 17 nodes (Gaussian Splats, USD Geo nodes, BigCat) that the AI has no training data on.

### Bidirectional Events (`events.py`)

Beyond request-response, the Nuke addon can push scene events to the MCP server in real-time:

- Node created / deleted / renamed
- Parameter changed
- Script loaded / saved
- Error occurred (node cook failure, missing input)
- Frame changed

This gives the AI ambient awareness of what the compositor is doing, enabling smarter suggestions and reducing the need for the AI to repeatedly poll for state. Event subscription is opt-in and configurable.

### MCP Resources (Scene Context)

Read-only scene state exposed as MCP Resources, allowing the AI to have contextual awareness without explicit tool calls:

- `nuke://script/info` — script name, path, frame range, FPS, colorspace
- `nuke://script/nodes` — node graph overview (types, connections, names)
- `nuke://script/selected` — currently selected nodes
- `nuke://script/errors` — nodes with errors or warnings

### MCP Prompts (Workflow Templates)

Reusable, parameterized workflow templates exposed as MCP Prompts:

- `greenscreen-comp` — set up a full greenscreen pipeline from Read to Write
- `cg-integration` — CG element over plate with proper color management
- `cleanup-plate` — paint/roto/patch workflow
- `stereo-setup` — stereo comp template with hero eye and views
- `delivery-setup` — Write nodes configured for specific delivery specs

These are invoked by users (not the AI) and inject structured multi-step instructions into the conversation.

### Destructive Action Guards

Defense-in-depth approach to preventing accidental damage:

1. **`CLAUDE.md` soft guards** — AI behavior rules that instruct the AI to describe what it is about to do, ask for confirmation, and wait before proceeding.
2. **MCP tool annotations** — `destructiveHint: true` on all tools that modify or delete, letting clients enforce confirmation prompts.
3. **Code-level enforcement** — Destructive tools accept an optional `confirm: bool` parameter. The server rejects destructive calls where `confirm` is not explicitly `true`, returning a description of what would happen and asking the AI to confirm with the user first.
4. **Input validation** — All tool inputs are validated at the server level to defend against prompt injection. The server does not trust the AI to sanitize.

### Async Tasks for Long Operations

Operations that take more than a few seconds return MCP Task handles instead of blocking:

- Rendering frames (`render.py`)
- BigCat / CopyCat training (`ml.py`)
- Camera solve (`tracking.py`)
- Batch operations across many nodes (`batch.py`)

The client can poll for progress, and the AI can continue the conversation while the operation runs. Uses FastMCP 2.14's `task=True` decorator on async tools.

### Offline Development Mode

A `--mock` flag that runs the MCP server against a mock Nuke socket that returns realistic responses. Allows tool development, testing, and documentation without Nuke running. Every tool in the codebase has a corresponding mock response.

---

## File Structure

```
nuke-mcp/
├── src/
│   └── nukemcp/
│       ├── __init__.py
│       ├── server.py              # FastMCP server, entry point
│       ├── connection.py          # Socket connection to Nuke addon
│       ├── version.py             # Version detection + tool gating
│       ├── memory.py              # Read/write persistent memory
│       ├── rag.py                 # Documentation retrieval (BM25)
│       ├── events.py              # Bidirectional event handling
│       ├── resources.py           # MCP Resources (scene context)
│       ├── prompts.py             # MCP Prompts (workflow templates)
│       ├── mock.py                # Mock Nuke socket for offline dev
│       └── tools/
│           ├── __init__.py
│           ├── graph.py
│           ├── comp.py
│           ├── script.py
│           ├── render.py
│           ├── tracking.py
│           ├── threed.py
│           ├── deep.py
│           ├── ml.py              # CopyCat + BigCat (Nuke 17+)
│           ├── splats.py          # Gaussian Splats (Nuke 17+)
│           ├── annotations.py    # Annotations API (Nuke 17+)
│           ├── templates.py
│           └── batch.py
├── nuke_addon/
│   ├── nuke_mcp_addon.py          # Runs inside Nuke (PySide6 for 16+)
│   ├── menu.py                    # Optional menu/toolbar integration
│   └── events.py                  # Event push from Nuke to MCP server
├── memory/
│   ├── facility.md
│   ├── corrections.md
│   ├── nodes/
│   └── project/
├── docs/
│   ├── nuke_api/                  # Local copy of Nuke Python docs for RAG
│   └── examples/                  # Example prompt sessions
├── tests/
│   ├── test_graph.py
│   ├── test_comp.py
│   ├── test_version_gating.py
│   ├── test_annotations.py
│   └── mock_responses/            # JSON fixtures for offline tests
├── scripts/
│   └── ingest_docs.py             # Populate RAG from local Nuke install
├── CLAUDE.md                      # Nuke-specific AI behavior rules
├── CLAUDE_GENERIC.md              # General compositor workflow rules
├── BEST_PRACTICES.md              # Human-readable guide for users + contributors
├── CONTRIBUTING.md                # How to add a new tool (step-by-step)
├── pyproject.toml
├── uv.lock
├── bootstrap.sh
├── bootstrap.bat
├── .mcp.json
└── README.md
```

---

## Roadmap

### Phase 1 — Foundation
*Get something solid and trustworthy into the hands of artists.*

- Clean Python package structure with `pyproject.toml` and `uv`
- Target FastMCP 2.14.x (MCP spec `2025-11-25` compliance, background tasks, no 3.x complexity)
- `nuke_mcp_addon.py` with dockable panel (PySide6 for Nuke 16+, PySide2 fallback), version reporting, and robust socket handling
- `connection.py` with reconnect logic and timeout handling
- Core `graph.py` tools: `create_node`, `modify_node`, `delete_node`, `connect_nodes`, `position_node`, `auto_layout`, `get_node_info`, `get_script_info`, `execute_python`
- `script.py` tools: `load_script`, `save_script`, `set_project_settings`, `set_frame_range`
- `version.py` with variant detection (Nuke / NukeX / NukeStudio) and version detection (16, 17+) for tool gating
- MCP tool annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) on all tools
- `CLAUDE.md` with destructive action rules and node naming conventions
- Code-level destructive action guards (`confirm` parameter pattern)
- `bootstrap.sh` / `bootstrap.bat`
- `--mock` flag and basic mock socket
- README with clear, tested installation instructions for Mac, Windows, Linux
- MIT license

**Exit criteria:** A compositor can install it in under 10 minutes, connect to a running Nuke 16 or 17, and have an AI assistant create and connect a basic comp tree via natural language. Destructive actions are blocked at both the AI instruction level and the code level.

---

### Phase 2 — Memory & Learning
*Make it remember. This is the key differentiator — promote it early.*

- `memory.py` with read/write interface for all memory files
- `facility.md` template and population workflow
- `corrections.md` logging — any time the compositor corrects the AI, the correction is optionally logged
- Per-project memory written automatically from project settings on connection
- Memory injected into AI context at session start via MCP Resources
- `CLAUDE.md` instructions for how to use and update memory
- Documentation: how to set up facility memory, what goes in it, how to review and edit it

**Exit criteria:** After three sessions with NukeMCP, it should know what colorspace the facility uses, the preferred keyer, the render output path structure, and at least one thing the artist has previously corrected.

---

### Phase 3 — Production Tooling
*Make it genuinely useful for real shots.*

- `comp.py`: `setup_keyer` (Primatte, IBK, Keylight), `setup_despill`, `setup_edge_blur`, `setup_basic_comp`, `setup_grade_chain`, `setup_motion_blur`, `setup_light_wrap`, `setup_lens_distortion`
- `render.py`: `setup_write_node`, `render_frames` (async via MCP Tasks), `flipbook`, `set_proxy_mode`
- `templates.py`: `load_toolset`, `save_toolset`, `list_toolsets`, `create_live_group`
- `batch.py`: `batch_set_knob`, `batch_reconnect`, `find_nodes_by_type`, `find_broken_reads`
- MCP Prompts for common workflows: `greenscreen-comp`, `cg-integration`, `cleanup-plate`, `delivery-setup`
- MCP Resources for scene context: `nuke://script/info`, `nuke://script/nodes`, `nuke://script/selected`, `nuke://script/errors`
- Full test suite with mock responses for all tools
- `BEST_PRACTICES.md` written from the perspective of a working compositor
- `CONTRIBUTING.md` with the exact pattern for adding a new tool
- Example prompt sessions in `docs/examples/` covering common compositor tasks

**Exit criteria:** A compositor can use NukeMCP to set up a full greenscreen comp from scratch — Read, keyer, despill, edge treatment, grade, merge over background, Write node — via a single natural language description. The AI has contextual awareness of the current script state via Resources.

---

### Phase 4 — Advanced Features (NukeX / Version Gating)
*Unlock the deeper toolset for those who have it.*

- `tracking.py`: `create_tracker`, `solve_tracker`, `setup_stabilize`, `create_camera_tracker`, `solve_camera_track` (async via MCP Tasks), `reconcile_3d`
- `threed.py`: `create_3d_scene`, `setup_camera`, `add_geometry`, `setup_scanline_render`, `setup_projection`
- Nuke 17 USD/Geo nodes: `setup_geo_camera`, `setup_geo_light`, `setup_geo_material` (via `threed.py`, Nuke 17+ gated)
- `deep.py`: `setup_deep_pipeline`, `setup_deep_merge`, `convert_to_deep`, `deep_crop`
- `ml.py`: `setup_copycat`, `train_copycat` (async via MCP Tasks), `apply_copycat_model`, `setup_optical_flow`
- `ml.py` (Nuke 17+): `setup_bigcat`, `train_bigcat` (async, with data augmentation and custom loss config)
- `splats.py` (Nuke 17+): `import_splat`, `setup_splat_render`, `setup_field_nodes`
- `annotations.py` (Nuke 17+): `create_annotation`, `list_annotations`, `modify_annotation`
- Version guard tests for all NukeX/Studio and Nuke 17+ tools

**Exit criteria:** All production-grade tools are implemented in the clean Python architecture, with version guards preventing them from appearing on incompatible Nuke installs. Nuke 17 features (Gaussian Splats, BigCat, USD Geo, Annotations) are available when the connected Nuke supports them.

---

### Phase 5 — Documentation Grounding (RAG)
*Make it accurate, not just plausible.*

- `rag.py` built on a BM25 full-text index (pure stdlib, no external dependencies, following houdini-mcp's pattern)
- `scripts/ingest_docs.py` to parse the local Nuke Python docs from a running Nuke install
- Ingestion support for Nukepedia gizmo documentation (HTML parsing)
- Ingestion support for a facility's internal tool docs (Markdown or plain text)
- Ingestion of Nuke 17 new node documentation (Gaussian Splats, USD Geo, BigCat, MaterialX)
- RAG queries integrated into tool responses — when the AI describes a node's parameters, it is drawing from actual documentation
- Documentation on how to populate and update the RAG store

**Exit criteria:** Ask NukeMCP about a specific knob on an obscure node and get an accurate, documentation-backed answer rather than a hallucinated one. Nuke 17's new nodes are documented and queryable.

---

### Phase 6 — Bidirectional Events
*Give the AI ambient awareness of the compositor's work.*

- `events.py` in the Nuke addon: push scene changes to the MCP server over the existing socket connection
- `events.py` in the MCP server: receive, filter, and surface events to the AI client
- Event types: node created/deleted/renamed, parameter changed, script loaded/saved, cook error, frame changed
- Event subscription is opt-in and configurable (per-event-type filtering)
- `CLAUDE.md` instructions for how to respond to events (observe, don't interrupt)
- GSV (Graph Scope Variable) change events via Nuke 17's new Python callbacks

**Exit criteria:** The AI can observe the compositor working and offer relevant suggestions based on what it sees happening in the script, without the compositor needing to explicitly describe the current state.

---

### Phase 7 — Ecosystem & Community
*Make it something others can build on.*

- Published to PyPI so it can be installed with `uvx nuke-mcp`
- Versioned releases with changelogs
- CI with automated tests on every PR
- Plugin system for facility-specific tool extensions — a studio can ship their own `tools/studio_tools.py` without forking the repo
- Nukepedia listing
- Community prompt library — a curated collection of useful prompt patterns contributed by users
- Multi-client documentation: tested setup guides for Claude Desktop, Claude Code, ChatGPT (via HTTP wrapper / ngrok), Ollama (via ollama-mcp-bridge)
- Registration in the MCP Registry for discoverability

---

## What This Is Not

It is worth being explicit about the boundaries.

NukeMCP is not a replacement for a compositor. It does not make creative decisions. It does not know what looks good. It cannot compensate for a poorly shot plate. The compositor remains the artist; the tool handles the plumbing.

NukeMCP is not a pipeline automation system. It does not talk to ShotGrid, frame servers, or render farm managers. Those integrations are out of scope for the core project, though the plugin system in Phase 7 would make them possible as extensions.

NukeMCP is not trying to be everything to everyone. It is specifically for Foundry Nuke. Houdini, Maya, and Flame are other people's problems, and they are better served by tools built by people who know those applications deeply.

---

## Technical Decisions

### Why FastMCP 2.14.x (not 3.x)

FastMCP 3.0 (February 2026) introduced a major architectural rewrite with providers, component versioning, and OpenTelemetry. While powerful, it adds significant complexity and breaking changes that conflict with the compositor-first principle. FastMCP 2.14.x provides:

- Full MCP `2025-11-25` spec compliance
- Background tasks (`task=True` on async tools) for renders and training
- Simple `@mcp.tool()` decorator pattern that pipeline TDs can read and extend
- Stable API without the 3.x migration burden

If 3.x stabilizes and the ecosystem moves there, migration can happen in a future major version.

### Why stdio Transport (not Streamable HTTP)

The MCP server communicates with AI clients via stdio (JSON-RPC over stdin/stdout). This is the standard for local CLI tools and desktop AI clients. It requires no auth setup, no port management, and no TLS configuration. The compositor runs the server locally — there is no remote deployment scenario in the core project.

Streamable HTTP transport could be added later for remote/cloud scenarios via the plugin system.

### Why BM25 for RAG (not Vector Embeddings)

Following houdini-mcp's proven approach: a pure-stdlib BM25 full-text index with zero external dependencies. No embedding models to download, no vector databases to manage, no cloud services to authenticate. A compositor should not need to understand ML infrastructure to get accurate documentation lookups.

### Why PySide6 Default (with PySide2 Fallback)

Nuke 16+ ships PySide6. Nuke 15 and earlier ship PySide2. The addon UI code detects which is available and imports accordingly. All UI code uses the common subset of both APIs.

---

## Inspiration and Acknowledgments

This project synthesizes work from several open-source contributors:

- **dughogan/nuke_mcp** — the right architecture, the right spirit, the right attitude toward compositor-readable code. 13 clean tools, MIT license, fxphd course that made the concept accessible.
- **flowagent-sh/nuke-mcp** — proof that the feature set can be production-grade, with camera tracking, deep compositing, and ML integration.
- **kleer001/houdini-mcp** — the memory system, the CLAUDE.md pattern, the BM25-based RAG, bidirectional events, BEST_PRACTICES.md as a living document, and the demonstration that a DCC MCP can be a serious piece of software engineering. 166 tools, 73 commits, 30,000 searchable docs.
- **Doug Hogan** (Groove Jones) — for doing it first, documenting it well, and building the fxphd course that made the concept accessible to the compositor community.

---

*This document is a living specification. It will be updated as the project evolves.*

*Last updated: March 2026. Reflects MCP spec `2025-11-25`, FastMCP 2.14.x, Nuke 17.0, and lessons from the DCC MCP ecosystem.*
