# Example: Greenscreen Composite

## Prompt

> Set up a full greenscreen comp. The foreground plate is at `/shots/010/fg_plate.####.exr` and the background is `/shots/010/bg_plate.####.exr`. Key with IBKGizmo, add despill and edge treatment, merge over the BG, and write to `/renders/010/comp.####.exr`.

## What the AI Does

1. Creates `fg_read` — Read node for the foreground plate
2. Creates `bg_read` — Read node for the background plate
3. Creates `fg_key` — IBKGizmo keyer connected to `fg_read`
4. Creates `fg_despill` — HueCorrect despill node
5. Creates `fg_edge` — EdgeBlur for edge treatment
6. Creates `fg_grade` — Grade for foreground color correction
7. Creates `comp_merge` — Merge2 (over) with BG on input 0, keyed FG on input 1
8. Creates `final_grade` — Grade for overall look
9. Creates `comp_write` — Write node with output path
10. Auto-layouts the graph

## Key Nodes

```
fg_read → fg_key → fg_despill → fg_edge → fg_grade ─┐
                                                       ├→ comp_merge → final_grade → comp_write
bg_read ──────────────────────────────────────────────┘
```

## Follow-up Prompts

- "Adjust the despill — it's pulling too much green from the skin tones"
- "Add a light wrap between the FG and BG"
- "The edge is too hard — soften the edge blur to 3 pixels"
