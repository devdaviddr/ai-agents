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
| `name` | ✅ | Lowercase letters and hyphens, unique. How you address the agent. |
| `description` | ✅ | *When* to use it. Claude reads this to decide whether to delegate automatically — write it as a trigger, not a summary. Add "use proactively" to encourage eager delegation. |
| `tools` | — | Comma-separated allowlist (e.g. `Read, Grep, Bash`). **Omit to inherit every tool** the main thread has. Narrow it to keep the agent safe and on-task. |
| `disallowedTools` | — | Comma-separated denylist — inherit everything *except* these (e.g. `Write, Edit`). Handy when you want all tools bar a couple. |
| `model` | — | `sonnet`, `opus`, `haiku`, `fable`, a full model id (e.g. `claude-opus-4-8`), or `inherit`. **Defaults to `inherit`** (same model as the main conversation). Cheaper models like `haiku` suit mechanical agents. |

Only `name` and `description` are required; everything else is optional. The body is the **system prompt**: role, process, output format, and hard rules. Be explicit — the agent starts with a clean, isolated context and only knows what you write here (plus your `CLAUDE.md` and the working directory).

## How it's invoked
- **Automatic delegation** — when a task matches the `description`, Claude hands it off. A sharp, trigger-shaped description is what makes this reliable.
- **Natural language** — name it in your prompt: *"use the commit-writer agent"*.
- **@-mention** — type `@` and pick it (or `@agent-commit-writer`) to force that specific agent to run.

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
- **Check it into version control.** Project agents in `.claude/agents/` are shared with your team and improved collaboratively — which is exactly what this collection is for.

## Items in this collection
| Agent | Description |
|-------|-------------|
| [commit-writer](commit-writer.md) | Reviews the staged diff and writes a Conventional Commits message. Read + Bash only; never commits unless asked. |
| [clin-coder-concept-extractor](clin-coder-concept-extractor.md) | Read-only extractor of codeable clinical concepts with evidence spans **and clinical context** (negation, temporality, certainty, family history) from a single document. Runs one-per-document in parallel; pairs with the `clin-coder` skill. |
| [clin-coder-verifier](clin-coder-verifier.md) | Read-only auditor of a proposed clinical coding — runs the engine's validity edits + grounding checks and flags anything unvalidated, ungrounded, or rule-violating. Cannot modify the proposal. Pairs with the `clin-coder` skill. |
| [clin-coder-cdi](clin-coder-cdi.md) | Read-only drafter of a non-leading Clinical Documentation Improvement (CDI) query when an episode's documentation is too thin/ambiguous to code confidently. Never codes. Pairs with the `clin-coder` skill. |

To add one, follow [CONTRIBUTING.md](../../CONTRIBUTING.md) and add a row here **and** in the [main README](../../README.md).
