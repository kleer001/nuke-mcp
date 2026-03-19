# Skill: retarget-fx-shot (Nuke)

Retarget an existing FX rig from one shot to another. Duplicates a named node
group (and its BackdropNode), renames shot-coded nodes, then remaps all file
references from the source shot's sequences to their analogues in the target shot.

## Invoke

> "Retarget the [backdrop/group name] network from [SOURCE_SHOT] to [TARGET_SHOT]."

Or supply the three inputs explicitly:

| Input | Description | Example |
|---|---|---|
| `SOURCE_NODES` | List of node names + backdrop label to copy | `Read1`, `Grade2`, `Merge3`, `PARK003 Rig` |
| `SOURCE_DIR` | Root directory of the source shot's sequences | `/path/to/raw_videos/PARK003/` |
| `TARGET_DIR` | Root directory of the target shot's sequences | `/path/to/raw_videos/CWG006/` |

---

## Phases

### 1. Copy

- Verify Nuke connection (ping or `get_script_info`).
- Read the position of every source node via `get_node_info` (knobs `xpos`, `ypos`).
- Find the BackdropNode enclosing the group: it has knobs `xpos`, `ypos`,
  `bdwidth`, `bdheight`, and a `label` matching the group name.
- Determine bounding box of the group: `max_xpos` across all nodes + node width (~80).
- Compute `offset_x` = bounding box width + a gap of at least 150 units (Nuke's
  coordinate scale is larger than Houdini's).
- Duplicate via `execute_python`:
  ```python
  nuke.selectAll()
  nuke.invertSelection()
  for name in source_node_names:
      nuke.toNode(name).setSelected(True)
  nuke.nodeCopy('%clipboard%')
  nuke.nodePaste('%clipboard%')
  ```
- Move each new node's `xpos` by `+ offset_x`.
- Create a new BackdropNode at the same offset: copy `bdwidth`, `bdheight`, `label`.

### 2. Rename

- Scan new node names for the source shot code, case-insensitive.
- Also catch Nuke's auto-suffix artefacts: Nuke appends a number on paste
  (e.g. `Read_PARK003` → `Read_PARK0031`). Detect these by the shot code stem.
- Propose renames: replace source shot code with target shot code.
- Also update the BackdropNode `label` knob if it contains the source shot code.
- **Show the rename list and get user confirmation before applying.**
- Apply: `node['name'].setValue(new_name)` via `execute_python` or `modify_node`.

### 3. Scan

- Scan all new nodes for `file` knob values containing the source shot directory.
- Also check inside `Group` nodes — recurse via
  `nuke.toNode(group_name).nodes()` and scan each child's knobs.
- Other knobs that may contain file paths: `vfield_file`, `lut`, `script`
  (on Group nodes), any knob of type `File_Knob`.
- Collect: node name | knob name | current value.

### 4. Match

- List the source shot directory — collect sequence folder names.
- List the target shot directory — collect sequence folder names.
- Match sequences semantically, in this priority order:
  1. **Shot plate** — keywords: `pl01_ref`, `ref`, `HD_ref`, `plate`
  2. **Clean plate** — keywords: `cp01`, `cleanPlate`, `clean_plate`
  3. **Roto** — keywords: `roto`
  4. **Render passes** — match by pass name: `Normal`, `Depth`, `Alpha`,
     `BaseColor`, `Roughness`, `Metallic`, `Specular`, `Source`
- Use process of elimination: once a source sequence is matched, remove it from
  the candidate pool for subsequent matches.
- Flag format changes (`.exr` ↔ `.png`) — note these explicitly.
- Flag unmatched source sequences — leave their parameters unchanged.

**Frame expression translation table:**

Nuke uses printf-style or hash-style frame tokens, not Houdini's `$F` syntax.

| Source pattern | Detected by | New pattern |
|---|---|---|
| `%04d` | printf 4-digit | `%04d` (usually unchanged) |
| `%06d` | printf 6-digit | `%06d` (usually unchanged) |
| `####` | 4 hashes | `####` (usually unchanged) |
| `%04d` with frame offset | expression node upstream | Adjust offset value, keep format |

Determine which pattern applies by inspecting the first filename in the target
sequence folder: count the digits, check for leading zeros, check whether the
frame number matches `%d` directly or requires an offset expression.

If the source used a Nuke frame offset (e.g. Read node `frame_mode: offset`,
`frame: -1000`) and the target sequence starts at a different frame number,
update the `frame` knob accordingly — do not change the file path pattern.

### 5. Confirm

- Present the full mapping table before touching any parameters:
  - Old path → New path
  - Expression/offset change (if any)
  - Format change (if any)
  - Unmatched sequences (listed separately)
- **Do not proceed until the user approves.**

### 6. Remap

- For each approved mapping, update the `file` knob via `modify_node` or
  `execute_python`: `nuke.toNode(name)['file'].setValue(new_path)`.
- If the frame padding changed, also update the `format` or `frame` knobs as needed.
- Apply to every node/knob pair found in the scan.

### 7. Save

- Call `save_script` after all remaps are applied.
- Report a final summary: N nodes copied, M nodes renamed, P parameters remapped,
  Q sequences unmatched.

---

## Notes

- **Do not remap** unmatched-sequence parameters — leave them pointing at the
  source shot. The user handles those manually.
- In Nuke, the BackdropNode label is the primary human-readable identifier for
  a rig group — always update it to reflect the target shot name.
- Nuke Read nodes have a `colorspace` knob — if the source and target shots use
  different colorspace tags (e.g. different camera LUTs), flag this for the user
  but do not change it automatically.
- If source nodes use a `TimeOffset` or `Retime` node with frame expressions,
  those may need adjustment when the target shot has a different frame range —
  flag but do not auto-fix.
