<div align="center">

# 🤖 AI Agents &amp; Skills

**A curated collection of reusable agents and skills for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [opencode](https://opencode.ai).**

Browse the catalog · run them straight from the repo · install them everywhere.

<br>

[![Platforms](https://img.shields.io/badge/platforms-Claude%20Code%20%7C%20opencode-4c6ef5?style=flat-square)](#catalog)
[![Catalog](https://img.shields.io/badge/catalog-1%20agent%20%C2%B7%201%20skill-2f9e44?style=flat-square)](#catalog)
[![Docs](https://img.shields.io/badge/docs-CONCEPTS-7048e8?style=flat-square)](CONCEPTS.md)
[![License](https://img.shields.io/badge/license-MIT-868e96?style=flat-square)](LICENSE)

</div>

---

> [!TIP]
> **New to agents & skills?** Read **[CONCEPTS.md](CONCEPTS.md)** — what they are, how they work, and best practices for building them.

## Quick start

Clone the repo and run the linker once — that's what makes every item discoverable by your CLI.

```bash
git clone <repo-url>
cd ai-agents
./scripts/link.sh          # in this repo only
# – or –
./scripts/link.sh --global # everywhere (links into ~/.claude & ~/.config/opencode)
```

Launch your CLI (from inside the repo if you used the plain command) and invoke an item:

```bash
claude        # or: opencode
```

|              | 🧑‍💻 **commit-writer** *(agent)*                            | 📝 **release-notes** *(skill)*                          |
| ------------ | ---------------------------------------------------------- | ------------------------------------------------------- |
| **Claude Code** | Stage a change, then ask: *“use the commit-writer agent”*  | Type `/release-notes`, or ask *“draft release notes since v1.0”* |
| **opencode**    | Mention it: `@commit-writer`                               | Ask *“summarise the commits since the last tag”*        |

> `./scripts/link.sh` (no flag) works only when the repo is your working directory. `--global` makes the items available in every project. See [Run the items](#run-the-items-from-this-repo) and [Install everywhere](#install-into-your-own-config) for detail.

## Contents

- [**Quick start**](#quick-start) — clone → link → use
- [**Catalog**](#catalog) — every agent &amp; skill, with descriptions
- [**Run the items from this repo**](#run-the-items-from-this-repo) — try them without installing
- [**Install into your own config**](#install-into-your-own-config) — use them everywhere
- [**Documentation**](#documentation) — guides for each platform &amp; type
- [**Repository layout**](#repository-layout)
- [**Contributing**](#contributing)

---

## Catalog

<table>
<tr><th align="left">Item</th><th align="left">Type</th><th align="left">Description</th></tr>
<tr>
<td><a href="claude/agents/commit-writer.md">commit-writer</a><br><sub>Claude · <a href="opencode/agents/commit-writer.md">opencode</a></sub></td>
<td>Agent</td>
<td>Reviews the staged diff and writes a clean Conventional Commits message. Limited to <code>Read</code> + <code>Bash</code> (no write/edit); never commits unless asked.</td>
</tr>
<tr>
<td><a href="claude/skills/release-notes/SKILL.md">release-notes</a><br><sub>Claude · <a href="opencode/skills/release-notes/SKILL.md">opencode</a></sub></td>
<td>Skill</td>
<td>Buckets <code>git log</code> between two refs into grouped, human-readable release notes.</td>
</tr>
<tr>
<td><a href="claude/skills/azure-diagram/">azure-diagram</a><br><sub>Claude · <a href="opencode/skills/azure-diagram/">opencode</a></sub></td>
<td>Skill</td>
<td>Generates editable, dark-theme Azure architecture diagrams as <code>.excalidraw</code> files — official Azure icons as nodes, resource-group containers, and auto-routed connectors that dodge other icons and stay snapped to nodes. Describe the architecture in one line. Bundles a pure-Python generator + the full official Azure icon set (647 icons). <a href="claude/skills/azure-diagram/">See example →</a></td>
</tr>
</table>

Per-platform guides: Claude [agents](claude/agents/README.md) · [skills](claude/skills/README.md) — opencode [agents](opencode/agents/README.md) · [skills](opencode/skills/README.md).

---

## Run the items from this repo

Run the linker once, and Claude Code / opencode will discover every catalog item whenever this repo is your working directory. `link.sh` generates `.claude/` and `.opencode/` discovery directories containing **symlinks** back into the catalog — they're git-ignored, so the catalog stays the single source of truth.

```bash
git clone <repo-url> && cd ai-agents
./scripts/link.sh       # generate the local .claude/ & .opencode/ links
claude                  # or: opencode
```

Then use them:

| Platform        | Agent — `commit-writer`                                     | Skill — `release-notes`                                        |
| --------------- | ---------------------------------------------------------- | -------------------------------------------------------------- |
| **Claude Code** | Stage a change, then ask *“use the commit-writer agent”*   | Run `/release-notes` (or ask *“draft release notes since v1.0”*) |
| **opencode**    | Mention it: `@commit-writer`                               | Ask *“summarise the commits since the last tag”*               |

Re-run the linker any time you add or remove an item:

```bash
./scripts/link.sh          # refresh this repo's .claude/ and .opencode/
```

---

## Install into your own config

To use the items **outside** this repo, either copy them or symlink them globally.

**Copy a single item** (see each platform's guide for exact paths):

```bash
cp    claude/agents/commit-writer.md      ~/.claude/agents/
cp -R claude/skills/release-notes         ~/.claude/skills/
cp    opencode/agents/commit-writer.md    ~/.config/opencode/agents/   # plural (canonical)
cp -R opencode/skills/release-notes       ~/.config/opencode/skills/   # plural (canonical)
```

**Or symlink the whole catalog into your user config** (updates as you `git pull`):

```bash
./scripts/link.sh --global
```

This links every catalog item into `~/.claude/` and `~/.config/opencode/`, pointing back at your clone. Run `./scripts/link.sh --help` for details. Existing real files are never overwritten — only symlinks are refreshed.

---

## Documentation

| Doc | What's in it |
|-----|--------------|
| **[CONCEPTS.md](CONCEPTS.md)** | What agents &amp; skills are, how they work, best practices, and platform differences. **Start here.** |
| [claude/README.md](claude/README.md) | Claude Code install paths (agents &amp; skills). |
| [claude/agents/README.md](claude/agents/README.md) | Claude Code agents — anatomy, frontmatter, invocation, authoring tips. |
| [claude/skills/README.md](claude/skills/README.md) | Claude Code skills — progressive disclosure, triggering, authoring tips. |
| [opencode/README.md](opencode/README.md) | opencode install paths (agents &amp; skills). |
| [opencode/agents/README.md](opencode/agents/README.md) | opencode agents — modes, tools map, invocation. |
| [opencode/skills/README.md](opencode/skills/README.md) | opencode skills — spec, portability from Claude. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | File format for each item type + the checklist for adding one. |

---

## Repository layout

```
ai-agents/
├── README.md              # this file — catalog + how to run/install
├── CONCEPTS.md            # deep dive: agents vs skills, how they work
├── CONTRIBUTING.md        # how to add an item
├── scripts/
│   └── link.sh            # wire items into .claude/ & .opencode/ (repo or --global)
├── claude/                # Claude Code items  ─┐
│   ├── agents/<name>.md                        │  the catalog —
│   └── skills/<name>/SKILL.md                  │  the source of truth
├── opencode/              # opencode items     ─┘
│   ├── agents/<name>.md
│   └── skills/<name>/SKILL.md
└── .claude/ · .opencode/  # generated by link.sh, git-ignored (symlinks
                           # into the catalog so items run in this repo)
```

---

## Contributing

New items welcome. Add the file/folder under the right `platform/type/`, run `./scripts/link.sh` to wire it up, then add a catalog row here. Full format details and the checklist are in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © Daniel David
