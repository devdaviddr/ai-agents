# Claude Code items

## Install an agent
Copy the file into your agents directory:

```bash
# project-scoped
cp claude/agents/commit-writer.md /path/to/project/.claude/agents/

# or user-scoped (all projects)
cp claude/agents/commit-writer.md ~/.claude/agents/
```

Claude Code auto-discovers agents in `.claude/agents/`. Invoke by asking for the agent, or let Claude delegate to it based on the `description`.

## Install a skill
Copy the whole skill folder:

```bash
# project-scoped
cp -R claude/skills/release-notes /path/to/project/.claude/skills/

# or user-scoped
cp -R claude/skills/release-notes ~/.claude/skills/
```

Skills are triggered by their `description`, or invoke directly with `/release-notes`.
