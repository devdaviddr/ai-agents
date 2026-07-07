# opencode Skills

> Part of the [ai-agents](../../README.md) collection · see also [opencode agents](../agents/README.md) · [Claude skills](../../claude/skills/README.md)

[opencode](https://opencode.ai) supports **skills** following the [Agent Skills](https://agentskills.io) open standard — the same `SKILL.md` format as Claude Code: a packaged capability, discovered from your repo or home directory and loaded on demand, that teaches the agent *how* to do something.

Because the `SKILL.md` format is shared across both platforms, a skill is usually **portable** — the main difference is the install location. opencode even reads `.claude/skills/` directly, so a Claude skill is often picked up with no changes at all.

## Anatomy

A **folder** with a `SKILL.md` entry point plus any supporting files:

```
release-notes/
  SKILL.md          # required — frontmatter + instructions
  (optional supporting files…)
```

```markdown
---
name: release-notes
description: Generate grouped release notes from the git log between two refs. Trigger on any request to summarise commits for a release.
---

# release-notes
Instructions the model follows when the skill fires...
```

### Frontmatter fields
| Field | Required | Notes |
|-------|----------|-------|
| `name` | ✅ | kebab-case; matches the folder name. Required by the Agent Skills standard. |
| `description` | ✅ | What it does **and when to trigger** — the only part loaded up front. |

## How it's triggered
The agent loads a skill by calling its built-in **`skill` tool** (e.g. `skill({ name: "release-notes" })`) when the task matches the skill's `description`. So — as on Claude — the `description` is the trigger. Note opencode skills are agent-invoked; they aren't run with a `/slash` command (that's opencode's separate *commands* feature).

## Progressive disclosure
Only the `description` stays in context; the full body and any supporting files load when the skill actually fires. Many skills can sit installed without weighing down the session.

## Install
```bash
# project-scoped
cp -R release-notes /path/to/project/.opencode/skills/

# global (all projects)
cp -R release-notes ~/.config/opencode/skills/
```
Copy the **whole folder** so supporting files travel with `SKILL.md`. The canonical directory is the plural `skills/`; the singular `skill/` also works for backwards compatibility.

## Skill vs. agent in opencode
| | Skill | Agent |
|--|-------|-------|
| Runs in | current context | own context (subagent) / session (primary) |
| Best for | reusable *how-to* / procedures | delegated tasks, or a switchable mode |
| Config | `SKILL.md` only | `mode`, `model`, `tools` map, `permission` |

Reach for a **skill** to teach a procedure; reach for an **[agent](../agents/README.md)** to offload a task or define a working mode.

## Portability note
This skill is byte-for-byte compatible with the [Claude version](../../claude/skills/release-notes/SKILL.md) — the only thing that changes between platforms is where you copy it (`.opencode/skills/` vs `.claude/skills/`), and opencode can even read the Claude copy directly.

## Items in this collection
| Skill | Description |
|-------|-------------|
| [release-notes](release-notes/SKILL.md) | Buckets `git log` between two refs into grouped, human-readable release notes. |
| [azure-diagram](azure-diagram/) | Generates **editable, dark-theme** Azure architecture diagrams as `.excalidraw` files — official Azure icons as nodes, resource-group containers, connectors that auto-route around icons and stay snapped. Bundled Python generator + the full official Azure icon set (647) + design-system catalog. File-only; open at excalidraw.com. [Example →](azure-diagram/README.md) |

To add one, follow [CONTRIBUTING.md](../../CONTRIBUTING.md) and add a row here **and** in the [main README](../../README.md).
