from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "data" / "processed" / "smoke_postgres_migration.sqlite3"


def main() -> None:
    schema = (ROOT / "db" / "postgres_schema.sql").read_text(encoding="utf-8")
    for text in ["CREATE EXTENSION IF NOT EXISTS vector", "tenant_id TEXT", "payload JSONB", "creator_embeddings"]:
        assert text in schema
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "docker-compose.yml").exists()
    if TMP.exists():
        TMP.unlink()
    TMP.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(TMP) as conn:
        conn.execute(
            """
            CREATE TABLE creator_profiles (
                creator_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                enriched INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT INTO creator_profiles (creator_id, payload, enriched) VALUES (?, ?, ?)",
            ("creator_smoke", '{"creator_id":"creator_smoke","name":"Smoke"}', 1),
        )
    result = subprocess.run(
        [
            "python3",
            "scripts/migrate_sqlite_to_postgres.py",
            "--sqlite",
            str(TMP),
            "--tenant",
            "smoke",
            "--dry-run",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert '"creator_profiles": 1' in result.stdout
    print("OK postgres schema and sqlite dry-run migration")


if __name__ == "__main__":
    main()
