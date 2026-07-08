# Contributing

Each item is a self-contained agent or skill for either Claude Code or opencode. To add one:

1. Drop the file/folder in the right place (`claude/` or `opencode/`, then `agents/` or `skills/`).
2. Keep names kebab-case and identical across platforms when an item ships for both.
3. Run `./scripts/link.sh` to wire the new item into the repo's `.claude/`/`.opencode/` discovery dirs so it runs in-repo (these dirs are git-ignored — nothing to commit).
4. Add the item to the catalog in [README.md](README.md), which is **grouped by domain** (e.g. Clinical coding, Dev workflow, Diagrams). Put it in the relevant domain section, creating a new section if none fits. If the item is a companion agent of a skill (a **suite**), list it indented (`└`) directly under that skill rather than in a separate block. Also add it to the "Items in this collection" table in the relevant folder guide. One-line description each.

## File formats

### Claude Code agent — `claude/agents/<name>.md`
Single markdown file with YAML frontmatter. `tools` and `model` are optional (omit `tools` to inherit all).

```markdown
---
name: my-agent
description: When this agent should be invoked.
tools: Read, Grep, Glob, Bash
model: sonnet
---

System prompt for the subagent...
```

### Claude Code skill — `claude/skills/<name>/SKILL.md`
A folder containing `SKILL.md` (plus any supporting files). Frontmatter needs `name` and `description`; the description should say *when* to trigger.

```markdown
---
name: my-skill
description: What it does and when to use it. Trigger on "...".
---

# My Skill
Instructions the model follows when the skill is invoked...
```

### opencode agent — `opencode/agents/<name>.md`
Markdown with frontmatter. `mode` is `subagent`, `primary`, or `all`. `tools` is a map of tool → boolean.

```markdown
---
description: When this agent should be invoked.
mode: subagent
model: anthropic/claude-sonnet-4-5
tools:
  write: false
  edit: false
---

System prompt for the agent...
```

### opencode skill — `opencode/skills/<name>/SKILL.md`
Same [Agent Skills](https://agentskills.io) `SKILL.md` format as Claude Code.

## Checklist
- [ ] File in the correct `platform/type/` folder
- [ ] Frontmatter valid for the target platform
- [ ] Row added to the README table with a clear one-line description
