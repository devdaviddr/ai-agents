# opencode items

## Install an agent
Copy the file into your opencode agents directory:

```bash
# project-scoped
cp opencode/agents/commit-writer.md /path/to/project/.opencode/agents/

# or global (all projects)
cp opencode/agents/commit-writer.md ~/.config/opencode/agents/
```

opencode discovers agents in `.opencode/agents/` (and `~/.config/opencode/agents/`). The filename becomes the agent name. The plural `agents/` is the canonical directory; the singular `agent/` also works for backwards compatibility.

## Install a skill
Copy the whole skill folder:

```bash
# project-scoped
cp -R opencode/skills/release-notes /path/to/project/.opencode/skills/

# or global
cp -R opencode/skills/release-notes ~/.config/opencode/skills/
```

opencode uses the plural `skills/` directory and the standard `SKILL.md` format (singular `skill/` also works for backwards compatibility). opencode also reads skills from `.claude/skills/`, so a Claude skill folder is discovered without copying.
