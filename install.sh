#!/usr/bin/env sh
# Convenience wrapper. The installer itself is scripts/install.py, which also runs on Windows.
py=$(command -v python3 || command -v python) || {
  echo "python3 not found; install Python 3.10+ first" >&2
  exit 1
}
exec "$py" "$(dirname "$0")/scripts/install.py" "$@"
