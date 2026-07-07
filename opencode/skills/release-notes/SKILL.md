---
name: release-notes
description: Generate grouped, human-readable release notes from the git log between two refs (tags, branches, or commits). Use when the user asks to draft release notes, a changelog entry, or "what changed since <ref>". Trigger on any request to summarise commits for a release.
---

# release-notes

Turn a range of git history into clean, grouped release notes.

## Inputs
- **from** — the previous release ref (tag/branch/commit). If not given, use the most recent tag: `git describe --tags --abbrev=0`.
- **to** — the target ref. Defaults to `HEAD`.

## Process
1. Resolve the range. Confirm both refs exist: `git rev-parse --verify <ref>`.
2. Collect commits: `git log <from>..<to> --pretty=format:'%h%x09%s'`.
3. Bucket each commit by its Conventional Commit type (or infer from the subject when the prefix is absent):
   - **✨ Features** — `feat`
   - **🐛 Fixes** — `fix`
   - **⚡ Performance** — `perf`
   - **📝 Docs** — `docs`
   - **🔧 Maintenance** — `refactor`, `build`, `ci`, `chore`, `test`
4. Drop noise (merge commits, `wip`, formatting-only) unless the user wants everything.
5. Rewrite each line as a user-facing bullet — plain language, not the raw commit subject. Keep the short hash for reference.

## Output
```markdown
## <to>  (<date>)

### ✨ Features
- Short user-facing description (`abc1234`)

### 🐛 Fixes
- ...

### 🔧 Maintenance
- ...
```

## Rules
- Omit empty sections.
- Call out breaking changes in a **⚠️ Breaking Changes** section at the top.
- If the range is empty, say so rather than inventing entries.
- Keep bullets scannable — one line each, no trailing period.
