# Claude Code Agents

> Part of the [ai-agents](../../README.md) collection · see also [Claude skills](../skills/README.md) · [opencode agents](../../opencode/agents/README.md)

**Subagents** are specialised assistants that Claude Code can delegate to. Each one runs in its **own context window** with its own system prompt, tool allowlist, and (optionally) its own model. They keep focused work off the main thread and let you encode reusable expertise.

## Anatomy

A subagent is a single Markdown file with YAML frontmatter followed by the system prompt:

```markdown
---
name: commit-writer
description: Use when the user wants a commit message for their staged changes.
tools: Bash, Read
model: sonnet
---

You are a focused commit-message writer...
```

### Frontmatter fields
| Field | Required | Notes |
|-------|----------|-------|
| `name` | ✅ | kebab-case, unique. How you address the agent. |
| `description` | ✅ | *When* to use it. Claude reads this to decide whether to delegate automatically — write it as a trigger, not a summary. |
| `tools` | — | Comma-separated allowlist (e.g. `Read, Grep, Bash`). **Omit to inherit every tool** the main thread has. Narrow it to keep the agent safe and on-task. |
| `model` | — | `sonnet`, `opus`, `haiku`, `inherit`, or a full model id. Omit to use the default. Cheaper models suit mechanical agents. |

The body is the **system prompt**: role, process, output format, and hard rules. Be explicit — the agent starts with a clean context and only knows what you write here.

## How it's invoked
- **Automatic delegation** — when a task matches the `description`, Claude hands it off. A sharp, trigger-shaped description is what makes this reliable.
- **Explicit** — the user (or you) can say "use the commit-writer agent".

## Install
```bash
# project-scoped (this repo only)
cp commit-writer.md /path/to/project/.claude/agents/

# user-scoped (all your projects)
cp commit-writer.md ~/.claude/agents/
```
Claude Code auto-discovers any `*.md` in `.claude/agents/`. Project agents override user agents with the same name.

## Writing a good agent
- **Scope the tools.** A read-only reviewer shouldn't have `Write`/`Edit`. Least privilege keeps behaviour predictable.
- **Front-load the trigger.** The first sentence of `description` decides whether the agent ever runs.
- **Define the output contract.** State the exact format you expect back — the caller only sees the agent's final message.
- **State what NOT to do.** e.g. "do not commit unless asked". Guard rails matter more when the agent acts autonomously.
- **Keep it single-purpose.** One agent, one job. Compose several rather than building a do-everything agent.

## Items in this collection
| Agent | Description |
|-------|-------------|
| [commit-writer](commit-writer.md) | Reviews the staged diff and writes a Conventional Commits message. Read + Bash only; never commits unless asked. |

To add one, follow [CONTRIBUTING.md](../../CONTRIBUTING.md) and add a row here **and** in the [main README](../../README.md).
