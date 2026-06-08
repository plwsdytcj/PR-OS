from __future__ import annotations

import argparse
from datetime import datetime
import sys

from src.storage.object_store import get_object_store, sanitize_object_key


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload backup bytes from stdin to the configured object store.")
    parser.add_argument("--prefix", default="backups/postgres", help="Object key prefix for backup files.")
    parser.add_argument("--name", default="", help="Optional backup file name. Defaults to a UTC timestamp.")
    args = parser.parse_args()

    data = sys.stdin.buffer.read()
    if not data:
        raise SystemExit("backup stdin is empty")

    name = args.name or f"pr-ai-os-postgres-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.sql"
    key = sanitize_object_key(f"{args.prefix.rstrip('/')}/{name}")
    stored = get_object_store().put_bytes(data, key, content_type="application/sql")
    print(stored.to_dict())


if __name__ == "__main__":
    main()
