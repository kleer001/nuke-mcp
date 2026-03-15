# NukeMCP — Roadmap

> What remains to be built. Updated March 2026.

## Current State

All planned phases are **complete**. The server, addon, mock system, discovery, all 12 tool modules, bidirectional events, memory system, plugin architecture, CI pipeline, and contributor docs are real implementations — 66+ tools/resources/prompts, 123+ passing tests, verified end-to-end against Nuke 17.0v1.

---

## Completed

### 1a — Mock Tests for Advanced Tools

**Status:** Done.

All tool modules have dedicated tests: `test_deep.py`, `test_ml.py`, `test_splats.py`, `test_threed.py`. 123+ tests passing.

### 1b — Integration Tests Against Headless Nuke

**Status:** Done.

- `tests/integration/` with session-scoped headless Nuke fixture
- Marked with `@pytest.mark.integration`, skipped by default via `addopts`
- CI runs mock tests only; integration tests run locally with `uv run pytest -m integration`
- Tests cover: node CRUD, connections, knob modification, frame range, version gating

### 2 — Bidirectional Events (Addon Push)

**Status:** Done.

- Addon registers real Nuke callbacks: `addOnCreate`, `addOnDestroy`, `addKnobChanged`, `addOnScriptLoad`, `addOnScriptSave`
- Events pushed over the existing TCP socket as `{"type": "event", ...}` messages
- Connection multiplexes events vs responses via a background reader thread
- EventLog populated in real time; `get_events()` returns actual Nuke activity
- Mock server supports `push_event()` for testing

### 3 — Memory Auto-Population

**Status:** Done.

- `memory/facility.md` template shipped with commented sections
- Auto-populates `memory/project/{name}.md` on connection from script settings
- Memory exposed as MCP Resources: `nuke://memory/facility`, `nuke://memory/corrections`
- `CLAUDE.md` updated with memory usage instructions

### 4 — CI Hardening

**Status:** Done.

- `ruff check` in CI pipeline
- `pytest --cov` with `--cov-fail-under=80`
- Python matrix: 3.10, 3.11, 3.12
- Integration tests excluded from CI via pytest marker

### 5 — Ecosystem & Publishing

**Status:** Done.

- PyPI metadata: classifiers, keywords, project URLs
- `pip install nuke-mcp` / `uvx nuke-mcp` ready
- Plugin system: `plugins/` directory with auto-discovery
- Multi-client docs in README (Claude Code, Claude Desktop, ChatGPT, Ollama)

### 6 — Contributor Documentation

**Status:** Done.

- `CONTRIBUTING.md` — step-by-step guide for adding tools
- `BEST_PRACTICES.md` — compositor guide, client-agnostic
- `docs/examples/` — 5 example prompt sessions (greenscreen, CG integration, cleanup, deep comp, splat render)

---

## Future Ideas

These are not planned work — just possibilities for the future:

- **GSV change events** — Nuke 17 Global Scope Variables via callbacks
- **Frame change events** — tracking playhead position changes
- **Remote transport** — HTTP/WebSocket transport for network access
- **Multi-session** — connecting to multiple Nuke instances simultaneously
- **Node graph visualization** — generate SVG/PNG of the node graph for AI context
- **Undo integration** — expose Nuke's undo stack to the AI
- **MCP Registry listing** — list on the official MCP registry for discoverability

---

## Removed from Roadmap

These items from the original plan are **done**:

- Phase 1 Foundation (scaffolding, addon, connection, mock, version gating, graph tools, script tools, CLAUDE.md, bootstrap, tests, README)
- Core production tools (comp.py, render.py, templates.py, batch.py)
- Advanced/gated tools (tracking.py, threed.py, deep.py, ml.py, splats.py, annotations.py)
- MCP Resources (script/info, script/nodes, script/errors, memory/facility, memory/corrections)
- MCP Prompts (greenscreen_comp, cg_integration, delivery_setup, cleanup_plate)
- BM25 RAG infrastructure and search tool
- Discovery module (Nuke install finder, trial license detection)
- Bidirectional event system (addon push + connection multiplexing)
- Memory system (auto-population, facility template, MCP resources)
- Plugin architecture (auto-discovery from plugins/ directory)
- CI pipeline (ruff, coverage, Python matrix)
- Contributor and best practices documentation

The original `IMPLEMENTATION.md` (step-by-step Phase 1 build order) has been deleted — it served its purpose.
