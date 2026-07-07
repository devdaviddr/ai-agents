# ai-agents

A collection of reusable **agents** and **skills** for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [opencode](https://opencode.ai).

Each item is self-contained — browse the tables below, then copy the file (or folder) into your own config. Install locations are noted per platform.

## Layout

```
claude/
  agents/<name>.md          # Claude Code subagents
  skills/<name>/SKILL.md    # Claude Code skills
opencode/
  agents/<name>.md          # opencode subagents
  skills/<name>/SKILL.md    # opencode skills
```

## Claude Code

### Agents — [guide](claude/agents/README.md)
| Agent | Description |
|-------|-------------|
| [commit-writer](claude/agents/commit-writer.md) | Reviews the staged diff and writes a clean Conventional Commits message. |

### Skills — [guide](claude/skills/README.md)
| Skill | Description |
|-------|-------------|
| [release-notes](claude/skills/release-notes/SKILL.md) | Generate grouped, human-readable release notes from the git log between two refs. |

**Install** — see [claude/README.md](claude/README.md).

## opencode

### Agents — [guide](opencode/agents/README.md)
| Agent | Description |
|-------|-------------|
| [commit-writer](opencode/agents/commit-writer.md) | Reviews the staged diff and writes a clean Conventional Commits message. |

### Skills — [guide](opencode/skills/README.md)
| Skill | Description |
|-------|-------------|
| [release-notes](opencode/skills/release-notes/SKILL.md) | Generate grouped, human-readable release notes from the git log between two refs. |

**Install** — see [opencode/README.md](opencode/README.md).

## Contributing

New items welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the file format of each item type and the checklist for adding an entry to the tables above.

## License

[MIT](LICENSE) © Daniel David
