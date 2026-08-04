#!/usr/bin/env sh
# Convenience wrapper. The real installer is scripts/install.py, which also runs on Windows.
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 &&
     "$py" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
    exec "$py" "$(dirname "$0")/scripts/install.py" "$@"
  fi
done

cat >&2 <<'EOF'
No Python 3.10 or newer on PATH.

uv is the shortest way out: it needs no Python itself, and installs both Python
and the PandaAI CLI.

  curl -LsSf https://astral.sh/uv/install.sh | sh
  uv python install 3.12
  uv tool install pandaai-cli

Or use a system package manager: brew install python (macOS),
sudo apt install python3 (Debian/Ubuntu), https://www.python.org/downloads/

Then run ./install.sh again.
EOF
exit 1
