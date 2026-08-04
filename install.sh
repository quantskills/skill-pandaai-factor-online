#!/usr/bin/env bash
# Install this skill into the AI coding tools you use.
#
#   ./install.sh                 # install into every tool detected on this machine
#   ./install.sh claude cursor   # install into specific tools
#   ./install.sh --copy claude   # copy instead of symlinking
#   ./install.sh project [DIR]   # wire it into one project instead of your home directory
#
# Symlinking is the default so `git pull` in this repository updates every tool at once.
set -euo pipefail

NAME="skill-pandaai-factor-online"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="link"

place() { # place <destination>
  local dest="$1"
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  if [ "$MODE" = "copy" ]; then cp -R "$SRC" "$dest"; else ln -s "$SRC" "$dest"; fi
  echo "  $dest"
}

point() { # point <instruction-file>  -- append a pointer, once
  local file="$1"
  mkdir -p "$(dirname "$file")"
  if [ -f "$file" ] && grep -q "$NAME" "$file"; then
    echo "  $file (already referenced)"
    return
  fi
  printf '\n## %s\n\nFor PandaAI factor work, read %s/SKILL.md first.\n做 PandaAI 因子时，先读 %s/SKILL.md。\n' \
    "$NAME" "$SRC" "$SRC" >> "$file"
  echo "  $file"
}

install_claude() { echo "Claude Code:";   place "$HOME/.claude/skills/$NAME"; }
install_cursor() { echo "Cursor:";        place "$HOME/.cursor/skills/$NAME"; }
install_codex()  { echo "Codex:";         point "$HOME/.codex/AGENTS.md"; }
install_gemini() { echo "Gemini CLI:";    point "$HOME/.gemini/GEMINI.md"; }

install_project() {
  local dir="${1:-$PWD}"
  echo "Project $dir:"
  place "$dir/.cursor/skills/$NAME"
  place "$dir/.claude/skills/$NAME"
  point "$dir/AGENTS.md"
}

# Any agent that reads AGENTS.md -- Codex, Kimi Code, opencode, Aider and others -- picks the skill
# up from the project pointer written by `install.sh project`.

targets=()
for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    project) install_project "${2:-$PWD}"; exit 0 ;;
    claude|cursor|codex|gemini|all) targets+=("$arg") ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown target: $arg" >&2; exit 1 ;;
  esac
done

if [ ${#targets[@]} -eq 0 ] || [ "${targets[0]}" = "all" ]; then
  targets=()
  [ -d "$HOME/.claude" ] && targets+=(claude)
  [ -d "$HOME/.cursor" ] && targets+=(cursor)
  [ -d "$HOME/.codex" ]  && targets+=(codex)
  [ -d "$HOME/.gemini" ] && targets+=(gemini)
  if [ ${#targets[@]} -eq 0 ]; then
    echo "No supported tool directories found in \$HOME." >&2
    echo "Pass a target explicitly, or use: ./install.sh project [DIR]" >&2
    exit 1
  fi
fi

for t in "${targets[@]}"; do "install_$t"; done

echo
echo "Next: python3 $SRC/scripts/bootstrap.py && pandaai-cli login"
