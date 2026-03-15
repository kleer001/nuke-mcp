# NukeMCP Best Practices

A guide for compositors using NukeMCP with any AI client.

## Getting Started

1. **Start the addon in Nuke** — run `nuke_mcp_addon.start()` in the Script Editor
2. **Connect your AI client** — configure it to use `nuke-mcp` as an MCP server
3. **Check the connection** — ask the AI to describe your current script

## Working Effectively

### Be Specific

Instead of "set up a comp," say:

> "Create a greenscreen comp: read `/shots/010/fg.####.exr` as fg_plate, key with IBKGizmo, despill, merge over `/shots/010/bg.####.exr`, write to `/renders/010/comp.####.exr`."

The AI works best with concrete file paths, node names, and specific operations.

### Use Descriptive Node Names

The AI follows the naming convention in `CLAUDE.md`:

- `fg_key` not `Keyer1`
- `bg_grade` not `Grade3`
- `hero_merge` not `Merge1`

This makes it easier for both you and the AI to reference nodes later.

### Check Before Changing

Before making modifications, ask the AI to describe the current state:

> "What nodes are in the script?" or "Show me the settings on fg_grade."

### Confirm Destructive Actions

The AI will always ask before:
- Deleting nodes
- Executing arbitrary Python
- Loading a new script (replaces current work)

Never say "yes" without reading what it's about to do.

### Iterate in Small Steps

Build your comp incrementally:

1. Read nodes and basic connections first
2. Verify the structure looks right
3. Add color corrections
4. Add effects and finishing

This gives you checkpoints and makes it easier to course-correct.

## Common Workflows

### Greenscreen Comp
> "Set up a greenscreen comp with fg plate at `/path/fg.exr` and bg at `/path/bg.exr`"

The AI uses the `greenscreen_comp` prompt template to build the full pipeline.

### CG Integration
> "Integrate CG render `/path/cg.exr` over plate `/path/plate.exr` with light wrap"

### Plate Cleanup
> "Set up cleanup for plate `/path/plate.exr` with RotoPaint and Denoise"

### Deep Compositing (NukeX)
> "Set up a deep pipeline from `/path/deep.exr` with DeepRecolor and DeepToImage"

### Camera Tracking (NukeX)
> "Create a camera tracker on plate_read"

## Memory System

NukeMCP remembers things across sessions:

- **Facility conventions** — edit `memory/facility.md` with your studio's preferences
- **Corrections** — when you correct the AI, it logs the correction for future sessions
- **Project settings** — automatically snapshots your script's settings

## Troubleshooting

### "Node not found"
The AI tried to reference a node that doesn't exist. Ask it to list all nodes first.

### "Not connected"
The addon isn't running in Nuke. Open the NukeMCP panel and click Start.

### Tools missing
Some tools require NukeX or Nuke 17+. Check your variant with `get_script_info`.

### Wrong colorspace
Always check the project colorspace before creating Read/Write nodes. Ask: "What's the current colorspace setting?"

## Client-Specific Setup

### Claude Code
The `.mcp.json` in the repo root configures everything. Run Claude Code from the project directory.

### Claude Desktop
Add to your config (see README.md for the full JSON block).

### ChatGPT / Other Clients
Wrap the MCP server with an HTTP bridge. The server uses stdio transport — any MCP-compatible wrapper will work.

### Local LLMs (Ollama, etc.)
Use an MCP-compatible client that supports stdio transport. The server doesn't require any specific AI provider.
