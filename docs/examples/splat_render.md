# Example: Gaussian Splat Render (Nuke 17+)

## Prompt

> Import the splat file at `/assets/env/garden.ply` and set up a render with the existing camera node `main_cam`.

## What the AI Does

1. Creates `splat_read` — Read node for the `.ply` splat file
2. Creates `splat_render` — SplatRender node
3. Connects `splat_read` to SplatRender input 0, `main_cam` to input 1
4. Auto-layouts

## Key Nodes

```
splat_read ─┐
             ├→ splat_render → ...
main_cam ───┘
```

## Follow-up Prompts

- "Add a Grade after the splat render to adjust the exposure"
- "Merge the splat render over a plate background"
- "Create a new camera and set focal length to 35mm for the splat render"
