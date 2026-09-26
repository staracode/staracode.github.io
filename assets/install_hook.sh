
#!/bin/sh
#
# One-time setup: copies pre-commit into .git/hooks/ and makes it
# executable. Run this once after cloning the repo (or right now, for
# your existing local clone). .git/hooks is never tracked by git, so
# this step has to be run manually on each machine/clone.
#
# Usage (from anywhere):
#   sh install_hook.sh

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cp "$SCRIPT_DIR/pre-commit" "$REPO_ROOT/.git/hooks/pre-commit"
chmod +x "$REPO_ROOT/.git/hooks/pre-commit"

echo "Installed pre-commit hook at $REPO_ROOT/.git/hooks/pre-commit"