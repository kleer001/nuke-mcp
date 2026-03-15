# NukeMCP — Marketing Playbook

Where to talk about NukeMCP, what to say, and how to be genuinely useful while doing it.

## Positioning

NukeMCP is not "AI that replaces compositors." It's a tool that handles the tedious parts so compositors can focus on the creative parts. Lead with that framing every time.

**One-liner:** "Talk to Nuke — describe what you want, and the AI builds the node graph."

**Elevator pitch:** NukeMCP connects AI assistants to a running Nuke session over MCP. You keep your license, your scene, your tools. The AI creates nodes, sets knobs, and wires up comps from plain English. Open source, runs locally, no cloud dependency.

## Key Messages

1. **It's your Nuke, not ours.** Local TCP socket, your license, your machine. Nothing leaves your workstation.
2. **Skip the boilerplate.** Shot setup, template comps, Write node configuration, broken file audits — the stuff you do 50 times a day without thinking.
3. **Not a black box.** Every action creates real nodes you can inspect, modify, and version. The AI is a fast pair of hands, not a replacement for your eyes.
4. **Open source, MIT licensed.** Fork it, extend it, submit a PR. Plugin system for studio-specific tools without touching core code.
5. **Works with any MCP client.** Claude, ChatGPT, local LLMs — it speaks standard MCP, not a proprietary API.

## Where Compositors Are

| Community | Type | Notes |
|---|---|---|
| [r/vfx](https://reddit.com/r/vfx) | Reddit | Largest VFX community. Be helpful first, link second. |
| [r/NukeVFX](https://reddit.com/r/NukeVFX) | Reddit | Nuke-specific. Smaller, more focused. |
| [Foundry Community](https://community.foundry.com/discuss/forum/189/nuke-users) | Forum | Official forum. Good for thoughtful posts, not drive-by links. |
| [Nukepedia](https://www.nukepedia.com/) | Tool hub | Where Nuke tools live. Consider listing NukeMCP here. |
| [VFXTalk Discord](https://discord.do/vfxtalk/) | Discord | Real-time chat. Good for demos and Q&A. |
| [VFX Squad Discord](https://discord.com/invite/vfx-squad-797000245413281792) | Discord | ~7k members. |
| [fxphd](https://www.fxphd.com/) | Training | Courses + community. Doug Hogan's MCP course is here. |
| [comp-sup Slack](https://comp-sup.slack.com) | Slack | Comp supervisors and senior artists. Invite-only. |
| [Hacker News](https://news.ycombinator.com/) | Tech | For the engineering angle — MCP, open source, DCC integration. |
| [LinkedIn](https://www.linkedin.com/) | Professional | VFX groups, Foundry-adjacent network. |

## Content Ideas

### Tutorials That Sell Without Selling

Write these up as blog posts, forum threads, or short videos. Each one demonstrates NukeMCP by solving a real problem.

1. **"Set up a keying comp in 30 seconds"** — Show the full chain: Read → Keylight → Despill → Grade → Merge → Write, built from a single sentence. Compare to building it by hand.

2. **"Audit 200 shots for broken Read nodes"** — `find_broken_reads` across a whole project. Comps with missing textures are a daily headache on every show.

3. **"Consistent Write node setup across a team"** — Studio conventions (colorspace, file type, path template) applied automatically. No more "who rendered this as sRGB JPEG?"

4. **"Explain this comp to me"** — Point the AI at a comp you inherited and get a plain-English walkthrough of the node graph. Great for onboarding.

5. **"Build a contact sheet"** — Read multiple plates, append them in a grid, Write out a reference image. Tedious to build by hand, one sentence with NukeMCP.

### Forum Posts That Help First

Don't post "check out my tool." Instead, answer real questions and mention NukeMCP when it's genuinely relevant.

- **"How do I set up despill for green screen?"** → Walk through the technique, then mention: "I've been using NukeMCP to scaffold these — `setup_despill` builds the DespillMadness + Grade chain in one call."
- **"My Read nodes keep breaking when the server moves"** → Explain path best practices, then mention `find_broken_reads` + `batch_set_knob` for bulk path fixing.
- **"How do you organize a big comp?"** → Talk about backdrops, B-pipe structure, naming conventions. Mention that NukeMCP follows naming conventions by default (`fg_key` not `Keyer1`).

### Demo Angles

- **Speed run:** Build a full green screen comp from an empty script in under 60 seconds, entirely by conversation.
- **Inheritance:** Open someone else's messy comp, ask the AI to explain what each section does.
- **Bulk ops:** Fix paths, rename nodes, or swap colorspaces across 50 nodes in one command.
- **Teaching tool:** A student asks "how do I do edge blur on a key?" and the AI builds a working example they can study.

## What NOT to Say

- Don't claim it replaces compositors. It doesn't. Compositing is judgment, not node creation.
- Don't promise it works on Nuke versions we haven't tested (currently only verified on 17.0).
- Don't imply Foundry endorsement. We're an independent open-source project.
- Don't oversell AI intelligence. It builds what you describe. It doesn't have taste.

## Launch Checklist

- [ ] Nukepedia listing (tool + description + screenshots)
- [ ] r/vfx post — demo video or GIF showing a real workflow
- [ ] r/NukeVFX post — more technical, show the node graph results
- [ ] Foundry Community post — respectful, link to repo, ask for feedback
- [ ] fxphd forum mention — context: builds on Doug Hogan's work
- [ ] HN "Show HN" post — emphasize MCP protocol, open source, DCC integration pattern
- [ ] LinkedIn post — tag Foundry, VFX industry contacts
- [ ] Discord drops — VFXTalk, VFX Squad — show, don't tell
