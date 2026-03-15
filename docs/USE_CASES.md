# NukeMCP — Use Cases

Real compositing workflows where NukeMCP saves time. Intended as a conversation starter with working compositors — if a use case doesn't match how you actually work, tell us.

---

## Shot Setup

**The pain:** Every shot starts the same way. Read the plate, set the frame range, set up the Write node with the right path and colorspace, maybe drop in a standard LUT. You do this hundreds of times per show.

**With NukeMCP:** "Read /shots/sh010/plate.v003.####.exr, set the frame range to 1001-1120, add a Write node at /renders/sh010/comp.v001.####.exr in ACEScg EXR16." One sentence, done.

---

## Green Screen Keying Chain

**The pain:** Keylight → Erode → EdgeBlur → Despill → HueCorrect → Premult → Merge over BG. Every compositor knows the recipe. Building it node by node and wiring it up is muscle memory, not creativity.

**With NukeMCP:** "Set up a keyer on the fg_read with a green screen, despill it, and merge over bg_read." The AI builds the chain, connects the inputs, and names the nodes.

---

## Broken File Audit

**The pain:** Artist hands off a comp. Half the Read nodes point to paths on their local machine or a server that moved. You open it, see red nodes everywhere, and spend 20 minutes hunting down the right paths.

**With NukeMCP:** "Find all broken Read nodes and show me their file paths." Instant audit. Then: "Update all Read nodes under /old/server/ to /new/server/." Bulk path fix in one command.

---

## Inheriting Someone Else's Comp

**The pain:** You open a 300-node comp from another artist. No backdrops, no labels, node names like Merge47 and Grade12. You need to understand it before you can change it.

**With NukeMCP:** "What does this comp do? Walk me through the node graph." The AI reads the structure and explains it in plain English — what's the B pipe, where are the keys, what's being merged where.

---

## Consistent Team Standards

**The pain:** Ten compositors, ten different Write node setups. Different colorspaces, different file naming, different compression settings. The render farm chokes, the DI suite complains.

**With NukeMCP:** Facility conventions live in `memory/facility.md`. The AI reads them on every session and follows them by default. "Add a Write node for this shot" always produces the right format, path, and colorspace.

---

## Quick Grade Experiments

**The pain:** Sup asks "can you try it cooler? And maybe lift the blacks a bit?" You add a Grade, tweak the knobs, render a frame, show it. Then "actually, try it warmer." Back and forth, adjusting knobs manually each time.

**With NukeMCP:** "Add a grade after the merge, cool it down, lift the shadows a bit." Then: "Actually warmer, and crush the blacks instead." Faster iteration when you're exploring looks verbally with a supervisor standing behind you.

---

## Template Comp from Scratch

**The pain:** New sequence, new setup. Build the standard CG comp template: beauty pass, lighting passes, reflection, specular, AO — each as a Read, shuffle the channels, grade individually, merge them all together. Same structure every time, 30+ nodes.

**With NukeMCP:** "Build a CG multi-pass comp with beauty, diffuse, specular, reflection, and AO passes from /shots/sh010/cg/." Node tree built, shuffled, graded, merged, ready for art direction.

---

## Bulk Node Operations

**The pain:** Client changes the delivery format. Every Write node in 40 comps needs to switch from EXR to DPX, change the colorspace, and update the file extension in the path.

**With NukeMCP:** "Find all Write nodes and change the file type to DPX, set colorspace to rec709, and update the file extension in the path." `batch_set_knob` across the board.

---

## Learning and Onboarding

**The pain:** Junior compositor joins the team. They know After Effects but not Nuke. They need to learn the node graph, understand knob names, and figure out which nodes to use for what.

**With NukeMCP:** "Show me how to do a simple screen replacement in Nuke." The AI builds a working example — CornerPin, Grade, Merge — with proper connections. A living tutorial they can inspect node by node.

---

## Annotation and Documentation

**The pain:** Nuke 17 added annotations, but nobody uses them because it's faster to just keep comping. Comps stay undocumented, and the next artist wastes time deciphering them.

**With NukeMCP:** "Annotate each section of this comp with what it does." The AI reads the graph structure and creates annotations for each logical group. Documentation that writes itself.

---

## Event-Driven Awareness

**The pain:** You're working with a supervisor or lead, making changes in Nuke while discussing on a call. They can't see what you're doing unless you share your screen.

**With NukeMCP:** The bidirectional event system pushes real-time node changes to the AI. The AI can describe what's happening as you work: "You just added a Roto node after the key and connected it to the merge's mask input."

---

## Feedback for Us

These use cases are hypotheses. If you're a working compositor:

- Which of these would actually save you time?
- Which ones miss the mark?
- What tedious task do you do every day that isn't listed here?

Open an issue or start a discussion — we want to build what you'd actually use.
