#!/usr/bin/env bash
#
# link.sh — wire the collection's agents & skills into the discovery
# directories that Claude Code and opencode read.
#
#   ./scripts/link.sh            Link into THIS repo (.claude/ and .opencode/)
#                                so the items work whenever you open the repo.
#   ./scripts/link.sh --global   Link into your user config (~/.claude and
#                                ~/.config/opencode) so they work everywhere.
#   ./scripts/link.sh --help
#
# Re-run any time you add or remove an item. Existing symlinks are refreshed;
# real (non-symlink) files at a destination are left untouched and reported.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GLOBAL=0
for arg in "${@:-}"; do
  case "$arg" in
    --global|-g) GLOBAL=1 ;;
    --help|-h)
      sed -n '3,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    "" ) ;;
    * ) echo "unknown argument: $arg (try --help)" >&2; exit 1 ;;
  esac
done

if [ "$GLOBAL" -eq 1 ]; then
  CLAUDE_BASE="$HOME/.claude"
  OPENCODE_BASE="$HOME/.config/opencode"
  echo "Linking into user config (global):"
else
  CLAUDE_BASE="$REPO_ROOT/.claude"
  OPENCODE_BASE="$REPO_ROOT/.opencode"
  echo "Linking into repo ($REPO_ROOT):"
fi

# link_one <abs_source> <path_from_repo_root> <dest_dir> <link_name>
link_one() {
  local src_abs="$1" src_relroot="$2" dest_dir="$3" name="$4"
  mkdir -p "$dest_dir"
  local dst="$dest_dir/$name"
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    echo "  ! skip $dst (real file/dir exists — not overwriting)"
    return
  fi
  [ -L "$dst" ] && rm -f "$dst"
  if [ "$GLOBAL" -eq 1 ]; then
    ln -s "$src_abs" "$dst"                 # absolute → the repo clone
  else
    ln -s "../../$src_relroot" "$dst"       # relative → portable in-repo link
  fi
  echo "  ✓ ${dst#"$HOME"/}"
}

link_files() { # <src_dir> <path_from_root_prefix> <dest_dir>
  local src_dir="$1" relroot_prefix="$2" dest_dir="$3" f base
  for f in "$src_dir"/*.md; do
    [ -e "$f" ] || continue
    base="$(basename "$f")"
    [ "$base" = "README.md" ] && continue
    link_one "$f" "$relroot_prefix/$base" "$dest_dir" "$base"
  done
}

link_dirs() { # <src_dir> <path_from_root_prefix> <dest_dir>
  local src_dir="$1" relroot_prefix="$2" dest_dir="$3" d base
  for d in "$src_dir"/*/; do
    [ -d "$d" ] || continue
    base="$(basename "$d")"
    link_one "${d%/}" "$relroot_prefix/$base" "$dest_dir" "$base"
  done
}

echo "Claude Code agents:"
link_files "$REPO_ROOT/claude/agents" "claude/agents" "$CLAUDE_BASE/agents"
echo "Claude Code skills:"
link_dirs  "$REPO_ROOT/claude/skills" "claude/skills" "$CLAUDE_BASE/skills"
echo "opencode agents:"
link_files "$REPO_ROOT/opencode/agents" "opencode/agents" "$OPENCODE_BASE/agents"
echo "opencode skills:"
link_dirs  "$REPO_ROOT/opencode/skills" "opencode/skills" "$OPENCODE_BASE/skills"

echo "Done."
