# Claude Code Skills

> Part of the [ai-agents](../../README.md) collection · see also [Claude agents](../agents/README.md) · [opencode skills](../../opencode/skills/README.md)

A **skill** is a packaged, reusable capability — instructions (and optionally scripts or reference files) that Claude loads *on demand* when a task matches. Unlike an agent, a skill runs **in the current context**; it teaches Claude *how* to do something rather than spinning up a separate assistant.

## Anatomy

A skill is a **folder** whose entry point is `SKILL.md`:

```
release-notes/
  SKILL.md          # required — frontmatter + instructions
  (helpers/, references/, scripts/…  — optional supporting files)
```

```markdown
---
name: release-notes
description: Generate grouped release notes from the git log between two refs. Trigger on "/release-notes" or "what changed since <ref>".
---

# release-notes
Instructions the model follows when the skill fires...
```

### Frontmatter fields
| Field | Required | Notes |
|-------|----------|-------|
| `name` | Optional* | Display label; defaults to the folder name. The **folder name** is what you type after `/`, so keep them the same. Lowercase + hyphens. |
| `description` | Recommended | What it does **and when to trigger**. This is the only part loaded up front, so make it a precise trigger. If omitted, Claude falls back to the first paragraph of the body. Put the key use case first (the listing truncates long text). |
| `allowed-tools` | — | Tools Claude may use *without a permission prompt* while the skill is active. Space/comma-separated or a YAML list. |
| `disable-model-invocation` | — | `true` = only *you* can run it via `/name`; Claude won't auto-trigger it. Use for side-effecting workflows (`/deploy`, `/commit`) you want to control the timing of. |

\*Strictly, Claude Code needs neither field — but the [Agent Skills standard](https://agentskills.io) and opencode both require `name` **and** `description`, so include both for portability.

## Progressive disclosure
Only the `description` is kept in context at all times. When a task matches, Claude reads the full `SKILL.md`; supporting files are pulled in **only if the instructions reference them**. This keeps skills cheap to have installed — you can carry many without bloating the context.

## How it's invoked
- **Model-triggered** — the `description` matches the task and Claude loads the skill automatically (unless `disable-model-invocation: true`).
- **Explicit** — the user runs `/release-notes` (the command name comes from the folder name).

## Install
```bash
# project-scoped
cp -R release-notes /path/to/project/.claude/skills/

# user-scoped (all projects)
cp -R release-notes ~/.claude/skills/
```
Copy the **whole folder** — supporting files must travel with `SKILL.md`.

## Skill vs. agent
| | Skill | Agent |
|--|-------|-------|
| Runs in | current context | its own context window |
| Best for | reusable *how-to* / procedures | delegated, self-contained *tasks* |
| Can bundle files/scripts | ✅ | ✗ (single file) |
| Own model/tools | inherits | configurable |

Reach for a **skill** when you want to teach a procedure; reach for an **[agent](../agents/README.md)** when you want to offload a whole task.

## Writing a good skill
- **Make the description a trigger**, not a title — include the phrases and situations that should fire it.
- **Give a concrete output shape** so results are consistent.
- **Keep the body procedural** — numbered steps beat prose.
- **Push detail into supporting files** and reference them, rather than inlining everything.

## Items in this collection
| Skill | Description |
|-------|-------------|
| [release-notes](release-notes/SKILL.md) | Buckets `git log` between two refs into grouped, human-readable release notes. |
| [azure-diagram](azure-diagram/) | Generates **editable, dark-theme** Azure architecture diagrams as `.excalidraw` files — official Azure icons as nodes, resource-group containers, connectors that auto-route around icons and stay snapped. Bundled Python generator + the full official Azure icon set (647) + design-system catalog. Optional MCP live-render. [Example →](azure-diagram/README.md) |

To add one, follow [CONTRIBUTING.md](../../CONTRIBUTING.md) and add a row here **and** in the [main README](../../README.md).
