# Example: CG Element Integration

## Prompt

> Integrate the CG robot render at `/shots/020/cg_robot.####.exr` over the plate `/shots/020/plate.####.exr`. It has premultiplied alpha. Add a light wrap and color match the CG to the plate.

## What the AI Does

1. Creates `plate_read` — Read node for the background plate
2. Creates `cg_read` — Read node for the CG render
3. Creates `cg_unpremult` — Unpremult to separate alpha for grading
4. Creates `cg_grade` — Grade for CG color matching
5. Creates `cg_premult` — Premult before merge
6. Creates `cg_lightwrap` — light wrap setup (Grade + Blur + Merge)
7. Creates `comp_merge` — Merge2 (over)
8. Creates `final_grade` — overall Grade
9. Creates `comp_write` — Write node
10. Auto-layouts

## Key Nodes

```
plate_read ────────────────────────────────────┐
                                                ├→ comp_merge → final_grade → comp_write
cg_read → cg_unpremult → cg_grade → cg_premult ┘
                                        │
                                   cg_lightwrap
```

## Follow-up Prompts

- "The CG is too bright — bring down the gain on cg_grade"
- "Add a Defocus to the CG to match the plate's depth of field"
- "Split the CG into separate beauty and utility passes"
