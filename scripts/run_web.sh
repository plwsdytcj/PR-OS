#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8601}"

python3 -m uvicorn web.server:app --host "$HOST" --port "$PORT"
