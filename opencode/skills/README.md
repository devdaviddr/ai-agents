# opencode Skills

> Part of the [ai-agents](../../README.md) collection · see also [opencode agents](../agents/README.md) · [Claude skills](../../claude/skills/README.md)

[opencode](https://opencode.ai) supports **skills** following the same [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) spec as Claude Code: a packaged capability, loaded on demand, that runs **in the current context** and teaches the model *how* to do something.

Because the `SKILL.md` format is shared across both platforms, a skill is usually **portable** — the main difference is the install location and directory name.

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
| `name` | ✅ | kebab-case; matches the folder name. |
| `description` | ✅ | What it does **and when to trigger** — the only part loaded up front. |

## Progressive disclosure
As with Claude, only the `description` stays in context; the full body and any supporting files load when the skill actually fires. Many skills can sit installed without weighing down the session.

## Install
```bash
# project-scoped — note the SINGULAR "skill" directory
cp -R release-notes /path/to/project/.opencode/skill/

# global (all projects)
cp -R release-notes ~/.config/opencode/skill/
```
Copy the **whole folder** so supporting files travel with `SKILL.md`.

## Skill vs. agent in opencode
| | Skill | Agent |
|--|-------|-------|
| Runs in | current context | own context (subagent) / session (primary) |
| Best for | reusable *how-to* / procedures | delegated tasks, or a switchable mode |
| Config | `SKILL.md` only | `mode`, `model`, `tools` map, `permission` |

Reach for a **skill** to teach a procedure; reach for an **[agent](../agents/README.md)** to offload a task or define a working mode.

## Portability note
This skill is byte-for-byte compatible with the [Claude version](../../claude/skills/release-notes/SKILL.md) — the only thing that changes between platforms is where you copy it (`.opencode/skill/` vs `.claude/skills/`).

## Items in this collection
| Skill | Description |
|-------|-------------|
| [release-notes](release-notes/SKILL.md) | Buckets `git log` between two refs into grouped, human-readable release notes. |

To add one, follow [CONTRIBUTING.md](../../CONTRIBUTING.md) and add a row here **and** in the [main README](../../README.md).
