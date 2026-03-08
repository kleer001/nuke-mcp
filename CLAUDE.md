# NukeMCP — AI Behavior Rules

You are connected to a live Nuke compositing session via MCP. Follow these rules.

## Architecture

Three-layer system:
1. **Nuke Addon** — socket server running inside Nuke (port 54321)
2. **MCP Server** (`src/nukemcp/`) — FastMCP bridge, exposes tools via stdio
3. **AI Client** — you, reading this file

## Destructive Actions

**Never** perform destructive actions without explicit user confirmation:

- `delete_node` — always call first with `confirm=False` to show what would be deleted, then confirm with the user before calling with `confirm=True`
- `execute_python` — always show the code to the user first, then confirm before calling with `confirm=True`
- `load_script` — always warn that the current script will be replaced, then confirm

**The pattern:**
1. Call the tool with `confirm=False` (returns a description of what would happen)
2. Show the description to the user
3. Ask for confirmation
4. Only if confirmed, call again with `confirm=True`

## Before Making Changes

- Call `get_script_info` to understand the current state
- Call `get_node_info` on relevant nodes before modifying them
- Never assume what nodes exist — always check first
- Read error messages carefully; they tell you what went wrong

## Node Naming

Use descriptive, lowercase names with underscores:
- `fg_key` not `Keyer1`
- `bg_grade` not `Grade3`
- `hero_merge` not `Merge1`
- `plate_read` not `Read1`

## Node Organization

- Keep the graph flowing top-to-bottom
- Source nodes (Read) at the top, output nodes (Write) at the bottom
- Use `auto_layout` after creating multi-node setups
- Position related nodes near each other

## Colorspace

- Respect the project's working colorspace — check with `get_script_info`
- Never change colorspace settings without asking
- When creating Read nodes, mention the expected colorspace if relevant

## When Uncertain

- Ask the user rather than guessing
- If a tool returns an error, report it clearly — don't retry silently
- If you don't know what a specific Nuke knob does, say so
