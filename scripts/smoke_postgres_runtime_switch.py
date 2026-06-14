from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.storage.postgres_payload import postgres_enabled, tenant_from_path


def main() -> None:
    previous = os.environ.get("DATABASE_URL")
    try:
        os.environ.pop("DATABASE_URL", None)
        assert postgres_enabled() is False
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
        assert postgres_enabled() is True
        assert tenant_from_path(Path("data/processed/phase1_web.sqlite3")) == "default"
        assert tenant_from_path(Path("data/processed/tenants/alpha-media/phase1_web.sqlite3")) == "alpha-media"
        assert tenant_from_path(Path("data/processed/tenants/openclaw-smoke/app.sqlite3")) == "openclaw-smoke"
        print("OK postgres runtime switch")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


if __name__ == "__main__":
    main()
