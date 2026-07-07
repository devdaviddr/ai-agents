# ai-agents

A collection of reusable **agents** and **skills** for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [opencode](https://opencode.ai).

Every item is self-contained. Browse the catalog, then either **[run them straight from this repo](#run-the-items-from-this-repo)** or copy an item into your own config. Both platforms are supported side by side.

> **New here?** Read **[CONCEPTS.md](CONCEPTS.md)** for a deep dive on what agents and skills are, how they work, and best practices for building them.

## Contents
- [Catalog](#catalog) — every agent & skill, with descriptions
- [Run the items from this repo](#run-the-items-from-this-repo) — try them without installing
- [Install into your own config](#install-into-your-own-config) — use them everywhere
- [Documentation](#documentation) — guides for each platform & type
- [Repository layout](#repository-layout)
- [Contributing](#contributing)

## Catalog

### Claude Code
**Agents** — [guide](claude/agents/README.md)
| Agent | Description |
|-------|-------------|
| [commit-writer](claude/agents/commit-writer.md) | Reviews the staged diff and writes a clean Conventional Commits message. Read + Bash only; never commits unless asked. |

**Skills** — [guide](claude/skills/README.md)
| Skill | Description |
|-------|-------------|
| [release-notes](claude/skills/release-notes/SKILL.md) | Buckets `git log` between two refs into grouped, human-readable release notes. |

### opencode
**Agents** — [guide](opencode/agents/README.md)
| Agent | Description |
|-------|-------------|
| [commit-writer](opencode/agents/commit-writer.md) | Reviews the staged diff and writes a clean Conventional Commits message. `write`/`edit` disabled; never commits unless asked. |

**Skills** — [guide](opencode/skills/README.md)
| Skill | Description |
|-------|-------------|
| [release-notes](opencode/skills/release-notes/SKILL.md) | Buckets `git log` between two refs into grouped, human-readable release notes. |

## Run the items from this repo

The repo ships with `.claude/` and `.opencode/` discovery directories that **symlink** to the catalog above, so the moment you open Claude Code or opencode **with this repo as your working directory**, every item is live — no install step.

```bash
git clone <this-repo> && cd ai-agents
claude          # or: opencode
```

Then use them:

| | Agent — `commit-writer` | Skill — `release-notes` |
|---|---|---|
| **Claude Code** | Stage a change, then ask: *"use the commit-writer agent"* | Run `/release-notes` (or ask "draft release notes since v1.0") |
| **opencode** | Mention it: `@commit-writer` | Ask "summarise the commits since the last tag" |

The symlinks are committed, so they work immediately on a fresh clone (Git stores them as real links, mode `120000`). If you add a new item, refresh the links:

```bash
./scripts/link.sh          # relink this repo's .claude/ and .opencode/
```

## Install into your own config

To use the items **outside** this repo, either copy them or symlink them globally.

**Copy a single item** (see each platform's guide for exact paths):
```bash
cp    claude/agents/commit-writer.md      ~/.claude/agents/
cp -R claude/skills/release-notes         ~/.claude/skills/
cp    opencode/agents/commit-writer.md    ~/.config/opencode/agent/    # note: singular
cp -R opencode/skills/release-notes       ~/.config/opencode/skill/    # note: singular
```

**Or symlink the whole catalog into your user config** (updates as you `git pull`):
```bash
./scripts/link.sh --global
```
This links every catalog item into `~/.claude/` and `~/.config/opencode/`, pointing back at your clone. Run `./scripts/link.sh --help` for details. Existing real files are never overwritten — only symlinks are refreshed.

## Documentation

| Doc | What's in it |
|-----|--------------|
| **[CONCEPTS.md](CONCEPTS.md)** | What agents & skills are, how they work, best practices, and platform differences. Start here. |
| [claude/README.md](claude/README.md) | Claude Code install paths (agents & skills). |
| [claude/agents/README.md](claude/agents/README.md) | Claude Code agents — anatomy, frontmatter, invocation, authoring tips. |
| [claude/skills/README.md](claude/skills/README.md) | Claude Code skills — progressive disclosure, triggering, authoring tips. |
| [opencode/README.md](opencode/README.md) | opencode install paths (agents & skills). |
| [opencode/agents/README.md](opencode/agents/README.md) | opencode agents — modes, tools map, invocation. |
| [opencode/skills/README.md](opencode/skills/README.md) | opencode skills — spec, portability from Claude. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | File format for each item type + the checklist for adding one. |

## Repository layout

```
├── README.md              # this file — the catalog + how to run/install
├── CONCEPTS.md            # deep dive: agents vs skills, how they work
├── CONTRIBUTING.md        # how to add an item
├── scripts/
│   └── link.sh            # wire items into .claude/ & .opencode/ (repo or --global)
├── claude/                # Claude Code items
│   ├── agents/<name>.md
│   └── skills/<name>/SKILL.md
├── opencode/              # opencode items
│   ├── agents/<name>.md
│   └── skills/<name>/SKILL.md
├── .claude/               # ← generated symlinks so the items run in-repo
└── .opencode/             # ← generated symlinks (singular agent/ & skill/)
```

## Contributing

New items welcome. Add the file/folder under the right `platform/type/`, run `./scripts/link.sh` to wire it up, and add a catalog row here. Full format details and the checklist are in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © Daniel David
