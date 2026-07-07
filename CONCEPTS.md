# Concepts: Agents & Skills

A deep dive into the two building blocks in this collection — what each one *is*, how it actually works under the hood, and how to build good ones. For the platform-specific file formats and install commands, see the quick guides: [Claude agents](claude/agents/README.md) · [Claude skills](claude/skills/README.md) · [opencode agents](opencode/agents/README.md) · [opencode skills](opencode/skills/README.md). Back to the [main README](README.md).

---

## The mental model in one line

> **A skill teaches the assistant *how* to do something inside the current conversation. An agent hands a whole task off to a *separate* assistant that reports back.**

Everything below is an elaboration of that distinction.

---

## Agents

### What an agent is
An **agent** (in Claude Code, a *subagent*) is a self-contained assistant defined by a system prompt, a set of allowed tools, and optionally its own model. It is a *worker you delegate to*, not a snippet of instructions you inline. When invoked, it spins up with a **fresh context window** that contains only its own system prompt and the task it was handed — none of the calling conversation's history, unless that history is passed in as part of the task.

Think of an agent as a colleague you hand a ticket to: they go away, do the work in their own workspace, and come back with a result. You don't watch them think; you get their final answer.

### How agents work
1. **Discovery.** Claude Code loads every agent file it finds (`~/.claude/agents/` for user scope, `.claude/agents/` for project scope; opencode uses `~/.config/opencode/agents/` and `.opencode/agents/`). Only the `name` and `description` are kept in context — enough to decide *whether* to use each agent.
2. **Selection.** When a task matches an agent's `description`, the main assistant delegates to it — either automatically ("this looks like a job for `commit-writer`") or because the user asked explicitly. This is why the `description` should read as a **trigger condition**, not a summary.
3. **Isolation.** The agent runs in its own context window. It cannot see the main thread's messages; the caller cannot see the agent's intermediate steps. This isolation is the whole point: heavy exploration, long tool outputs, and noisy reasoning stay *out* of the main conversation.
4. **Tools & model.** The agent is restricted to its declared tools (or inherits all if none are declared) and runs on its declared model (or the default). A read-only reviewer with `Read, Grep` behaves very differently — and far more safely — than one with `Write, Bash`.
5. **Return.** The agent's **final message is the only thing the caller receives.** Everything else is discarded. This makes the *output contract* the most important part of the prompt.

### When to reach for an agent
- The task is **self-contained** and has a clear "done" — write a commit message, review a diff, research a question, migrate a file.
- The work is **noisy** — lots of file reads, big tool outputs, exploratory searching you don't want polluting the main context.
- You want a **different risk profile** — e.g. a read-only investigator that physically cannot edit files.
- You want to **parallelise** — several agents on independent slices of a job at once.

### Best practices for agents
- **Least privilege.** Declare the *minimum* tool set. A reviewer needs no `Write`; a planner needs no `Bash`. Narrow tools make behaviour predictable and safe.
- **Write the description as a trigger.** "Use when the user wants X" beats "An agent that does X." The first sentence decides whether the agent is ever selected.
- **Define the output contract explicitly.** Because only the final message survives, state the exact format you expect: a message, a diff, a JSON blob, a table. Ambiguity here is the #1 cause of disappointing results.
- **State the guard rails — what NOT to do.** "Do not commit unless asked." "Do not modify files outside `src/`." Autonomy makes negative constraints matter more.
- **Single responsibility.** One agent, one job. Compose several small agents rather than one that branches on ten scenarios.
- **Assume a blank slate.** The agent knows *only* its system prompt. Don't reference "the earlier discussion" — it can't see it. Put everything it needs in the prompt or the handed-in task.
- **Match the model to the work.** Mechanical, high-volume agents can run on a cheaper/faster model; reasoning-heavy ones justify a stronger one.

---

## Skills

### What a skill is
A **skill** is a packaged, reusable *capability* — a set of instructions, and optionally supporting scripts, templates, or reference files, that the assistant loads **on demand** and follows **in the current conversation**. It doesn't spin up a separate worker; it augments the assistant you're already talking to with know-how it didn't have a moment ago.

If an agent is a colleague you delegate to, a skill is a **playbook the assistant pulls off the shelf** the instant it recognises the situation the playbook is for.

### How skills work
1. **Packaging.** A skill is a *folder* whose entry point is `SKILL.md` (frontmatter + instructions). It can carry supporting files alongside — helper scripts, reference docs, templates.
2. **Progressive disclosure — the key mechanism.** Only the skill's `description` sits in context at all times (cheap). When a task matches, the assistant reads the full `SKILL.md`. Supporting files are pulled in **only if and when the instructions point to them.** This three-tier loading (description → body → referenced files) is what lets you keep *many* skills installed without bloating the context or slowing the model down.
3. **Triggering.** A skill fires either because its `description` matches the task (model-triggered) or because the user invokes it explicitly (`/skill-name`). As with agents, the `description` is doing the real work — it is the trigger.
4. **Execution.** The skill's instructions run in the **current context**, with the assistant's existing tools and the full conversation visible. There's no isolation and no separate return message — the skill simply steers the assistant's next actions.

### When to reach for a skill
- You're encoding a **procedure or house style** — "how we write release notes", "how we format a PR description", "the steps to cut a release."
- The capability should **stay in the conversation** and build on its context, rather than being handed off.
- You want to **bundle assets** — a script the instructions call, a template they fill in, a reference table they consult.
- The behaviour should be **available broadly** and trigger whenever relevant, not just when a task is explicitly delegated.

### Best practices for skills
- **The description is a trigger, not a title.** Include the phrases, verbs, and situations that should activate it ("Trigger on `/release-notes` or 'what changed since <ref>'"). A vague description means the skill never fires — or fires at the wrong time.
- **Keep the body procedural.** Numbered steps outperform prose. The model is following instructions, so make them followable.
- **Give a concrete output shape.** Show the exact format you want produced. Consistency comes from specifying it, not hoping for it.
- **Exploit progressive disclosure.** Keep `SKILL.md` lean; push long references, lookup tables, and examples into supporting files and *link* to them. The model loads them only when needed.
- **Make it self-contained and portable.** Bundle everything the skill depends on in its folder so copying the folder is all it takes to install.
- **One capability per skill.** A tightly scoped skill is easier to trigger correctly and reuse than a sprawling one.

---

## Agents vs. Skills — choosing

| | **Skill** | **Agent** |
|---|---|---|
| Runs in | the current conversation | its own isolated context |
| Sees the conversation | yes | no (only the handed-in task) |
| Returns | nothing — it steers the current assistant | a single final message |
| Best for | reusable *how-to* / procedures / house style | delegated, self-contained *tasks* |
| Can bundle files/scripts | ✅ | ✗ (single prompt file) |
| Own model / tool sandbox | inherits the session's | independently configurable |
| Good when you want | knowledge applied *here* | work done *elsewhere* and reported back |

**Rules of thumb**
- Need the result to build on the current conversation? → **skill.**
- Want to keep noisy work out of the main thread, or run something with restricted tools? → **agent.**
- Encoding *how to do something*? → **skill.** Offloading *a job*? → **agent.**
- They compose: a skill's instructions can tell the assistant to delegate part of the work to an agent.

---

## Platform notes: Claude Code vs. opencode

Both platforms share the same two concepts, and the `SKILL.md` format follows the same [Agent Skills](https://agentskills.io) open standard (so skills are essentially portable — opencode even reads `.claude/skills/` directly). The differences are in agent frontmatter and install paths:

| | **Claude Code** | **opencode** |
|---|---|---|
| Agent dir | `.claude/agents/` | `.opencode/agents/` (singular `agent/` also works) |
| Skill dir | `.claude/skills/` | `.opencode/skills/` (singular `skill/` also works) |
| Global scope | `~/.claude/…` | `~/.config/opencode/…` |
| Agent `name` field | optional (unique id; defaults matter) | none — the **filename** is the name |
| Agent `tools` | comma-separated allowlist string | **map of tool → boolean** |
| Agent modes | subagents only | `primary` / `subagent` / `all` (`primary` agents are Tab-switchable) |
| Agent model field | `sonnet` / `opus` / `haiku` / `fable` / id / `inherit` (default `inherit`) | `provider/model`, e.g. `anthropic/claude-sonnet-5` |
| Skill invocation | `/name` **or** model-triggered | agent-triggered via the `skill` tool (no `/slash`) |

> opencode's canonical directories are **plural** (`agents/`, `skills/`); the singular forms are kept only for backwards compatibility, so this collection uses the plural everywhere.

When an item ships for both platforms in this collection, we keep the same kebab-case name and mirror the behaviour, adjusting only the frontmatter to each platform's schema — see the [`commit-writer`](claude/agents/commit-writer.md) agent for a side-by-side example.

---

*Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).*
