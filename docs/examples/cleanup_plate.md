# Example: Plate Cleanup

## Prompt

> Set up a cleanup comp for the plate at `/shots/030/plate.####.exr`. There's a rig visible in the upper right corner and some noise in the shadows.

## What the AI Does

1. Creates `plate_read` — Read node for the plate
2. Creates `cleanup_roto` — RotoPaint for manual rig removal
3. Creates `cleanup_denoise` — Denoise node for shadow noise
4. Creates `cleanup_grade` — Grade for exposure corrections
5. Creates `cleanup_write` — Write node for output
6. Auto-layouts

## Key Nodes

```
plate_read → cleanup_roto → cleanup_denoise → cleanup_grade → cleanup_write
```

## Follow-up Prompts

- "The denoise is too aggressive — reduce the amount"
- "Add a second RotoPaint after the Grade for fine detail cleanup"
- "Set the frame range to 1001-1050 and render"
