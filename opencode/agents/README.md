# opencode Agents

> Part of the [ai-agents](../../README.md) collection · see also [opencode skills](../skills/README.md) · [Claude agents](../../claude/agents/README.md)

In [opencode](https://opencode.ai), **agents** are configurable assistants with their own prompt, model, tools, and permissions. They come in two flavours set by the `mode` field:

- **primary** — top-level agents you switch between with the **Tab** key (e.g. a "build" vs "plan" agent).
- **subagent** — specialised helpers invoked on demand via `@mention` or the task tool, running in their own context.
- **all** — usable as either.

## Anatomy

A Markdown file with YAML frontmatter, then the system prompt:

```markdown
---
description: Use when the user wants a commit message for their staged changes.
mode: subagent
model: anthropic/claude-sonnet-5
tools:
  write: false
  edit: false
  bash: true
  read: true
---

You are a focused commit-message writer...
```

### Frontmatter fields
| Field | Required | Notes |
|-------|----------|-------|
| `description` | ✅ | *When* to use the agent. Drives automatic delegation for subagents. |
| `mode` | — | `primary`, `subagent`, or `all`. Defaults to `all`. |
| `model` | — | `provider/model`, e.g. `anthropic/claude-sonnet-5`. Omit to inherit the session model. |
| `temperature` | — | Sampling temperature (0.0–1.0). Low for analysis, higher for creativity. |
| `tools` | — | **Map of tool → boolean.** Enable/disable individual tools (`read`, `write`, `edit`, `bash`, …). Everything not listed keeps its default. |
| `permission` | — | Fine-grained `allow`/`ask`/`deny` rules (e.g. gate `bash` or `edit`). |
| `prompt` | — | System prompt as a field, instead of (or in addition to) the markdown body. |
| `disable` | — | `true` to deactivate the agent. |

> **Note the format difference from Claude Code:** opencode uses a **`tools:` map of booleans**, not a comma-separated allowlist, and there is no `name` field — the filename is the agent name.

The body is the system prompt.

## How it's invoked
- **primary** — select it with **Tab** in the TUI.
- **subagent** — `@commit-writer` in chat, or delegated automatically based on `description`.

Agents can also be declared inline in `opencode.json` under the `agent` key; the Markdown-file form here is the portable, shareable format.

## Install
```bash
# project-scoped
cp commit-writer.md /path/to/project/.opencode/agents/

# global (all projects)
cp commit-writer.md ~/.config/opencode/agents/
```
The canonical directory is the plural `agents/`; the singular `agent/` also works for backwards compatibility.

## Writing a good agent
- **Disable tools you don't need** in the `tools` map — a reviewer sets `write: false`, `edit: false`.
- **Pick `mode` deliberately** — most reusable helpers are `subagent`.
- **Front-load the trigger** in `description` so delegation is reliable.
- **Define the output contract** — the caller only sees the agent's final message.

## Items in this collection
| Agent | Description |
|-------|-------------|
| [commit-writer](commit-writer.md) | Reviews the staged diff and writes a Conventional Commits message. `write`/`edit` disabled; never commits unless asked. |

To add one, follow [CONTRIBUTING.md](../../CONTRIBUTING.md) and add a row here **and** in the [main README](../../README.md).
