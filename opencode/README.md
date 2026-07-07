# opencode items

## Install an agent
Copy the file into your opencode agent directory:

```bash
# project-scoped
cp opencode/agents/commit-writer.md /path/to/project/.opencode/agent/

# or global (all projects)
cp opencode/agents/commit-writer.md ~/.config/opencode/agent/
```

opencode discovers agents in `.opencode/agent/`. Note the singular `agent/` directory name used by opencode.

## Install a skill
Copy the whole skill folder:

```bash
# project-scoped
cp -R opencode/skills/release-notes /path/to/project/.opencode/skill/

# or global
cp -R opencode/skills/release-notes ~/.config/opencode/skill/
```

opencode uses the singular `skill/` directory and the standard `SKILL.md` format.
