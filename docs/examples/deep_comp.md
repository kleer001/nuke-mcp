# Example: Deep Compositing (NukeX)

## Prompt

> Set up a deep comp pipeline. I have two deep EXR renders: `/shots/040/char_deep.####.exr` and `/shots/040/env_deep.####.exr`. Merge them together and convert to flat for grading.

## What the AI Does

1. Creates `char_read` — Read node for character deep render
2. Creates `env_read` — Read node for environment deep render
3. Creates `deep_merge` — DeepMerge to combine both deep streams
4. Creates `deep_to_image` — DeepToImage to flatten for grading
5. Creates `final_grade` — Grade on the flattened result
6. Creates `comp_write` — Write node
7. Auto-layouts

## Key Nodes

```
char_read ─┐
            ├→ deep_merge → deep_to_image → final_grade → comp_write
env_read ──┘
```

## Follow-up Prompts

- "Add a DeepRecolor to the character stream before the merge"
- "Convert a flat plate to deep using DeepFromImage and add it to the merge"
- "Add holdout matte extraction before the DeepToImage"
