#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIROFISH_HOME="${1:-${MIROFISH_HOME:-/opt/mirofish}}"
MIROFISH_REPO="${MIROFISH_REPO:-https://github.com/amadad/mirofish.git}"
MIROFISH_REF="${MIROFISH_REF:-3e98e776cdfc9556c12ace82a60e9d3da5bd41e7}"
PATCH_FILE="$REPO_ROOT/vendor/mirofish-openai-compatible.patch"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it first: python3 -m pip install --user uv" >&2
  exit 1
fi

if [ ! -d "$MIROFISH_HOME/.git" ]; then
  mkdir -p "$(dirname "$MIROFISH_HOME")"
  git clone "$MIROFISH_REPO" "$MIROFISH_HOME"
fi

cd "$MIROFISH_HOME"
git fetch --all --tags
git checkout "$MIROFISH_REF"

if git apply --check "$PATCH_FILE" >/dev/null 2>&1; then
  git apply "$PATCH_FILE"
elif grep -q "openai-compatible" app/config.py app/utils/llm_client.py app/cli.py; then
  echo "MiroFish OpenAI-compatible patch already appears to be applied."
else
  echo "Cannot apply $PATCH_FILE cleanly." >&2
  exit 1
fi

uv sync

echo "MiroFish runtime ready at $MIROFISH_HOME"
echo "Set: MIROFISH_COMMAND=\"uv --directory $MIROFISH_HOME run mirofish\""
