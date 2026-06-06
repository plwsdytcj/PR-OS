from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.storage.object_store import object_store_status
from src.storage.postgres_payload import postgres_enabled, tenant_from_path


def database_status(db_path: Path | str | Any) -> dict[str, Any]:
    if postgres_enabled():
        return {
            "provider": "postgres",
            "configured": True,
            "available": True,
            "tenant": tenant_from_path(db_path),
            "database_url_configured": True,
            "detail": "DATABASE_URL 已配置，业务对象写入 PostgreSQL JSONB 表。",
        }
    path = Path(str(db_path))
    return {
        "provider": "sqlite",
        "configured": True,
        "available": True,
        "tenant": tenant_from_path(db_path),
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "detail": "本地 SQLite，适合开发和单机内部版。",
    }


def storage_runtime_status(db_path: Path | str | Any) -> dict[str, Any]:
    return {
        "database": database_status(db_path),
        "object_store": object_store_status(),
        "env": {
            "DATABASE_URL": _masked(os.getenv("DATABASE_URL", "")),
            "OBJECT_STORE_PROVIDER": os.getenv("OBJECT_STORE_PROVIDER", "local"),
            "OBJECT_STORE_BUCKET": os.getenv("OBJECT_STORE_BUCKET", ""),
            "OBJECT_STORE_ENDPOINT_URL": os.getenv("OBJECT_STORE_ENDPOINT_URL", ""),
        },
    }


def _masked(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 12:
        return "*" * len(value)
    return f"{value[:6]}...{value[-4:]}"
