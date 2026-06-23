from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "db" / "postgres_schema.sql"


def postgres_enabled() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


def tenant_from_path(path: Path | str | Any) -> str:
    text = str(path)
    parts = Path(text).parts
    if "tenants" in parts:
        index = parts.index("tenants")
        if index + 1 < len(parts):
            return parts[index + 1]
    return "default"


def ensure_schema() -> None:
    if not postgres_enabled():
        return
    _ensure_schema_cached(os.getenv("DATABASE_URL", "").strip())


@lru_cache(maxsize=8)
def _ensure_schema_cached(database_url: str) -> None:
    import psycopg

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(schema)


def fetch_payloads(
    path: Path | str | Any,
    table: str,
    where: str = "",
    params: Iterable[Any] = (),
    order_by: str = "updated_at DESC",
) -> list[str]:
    import psycopg

    ensure_schema()
    tenant = tenant_from_path(path)
    sql = f"SELECT payload FROM {table} WHERE tenant_id = %s"
    values: list[Any] = [tenant]
    if where:
        sql += f" AND {where}"
        values.extend(params)
    if order_by:
        sql += f" ORDER BY {order_by}"
    with psycopg.connect(os.getenv("DATABASE_URL", "")) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, values)
            return [_json_text(row[0]) for row in cur.fetchall()]


def fetch_payload(path: Path | str | Any, table: str, key_column: str, key_value: str) -> str | None:
    rows = fetch_payloads(path, table, where=f"{key_column} = %s", params=(key_value,), order_by="")
    return rows[0] if rows else None


def upsert_payload(
    path: Path | str | Any,
    table: str,
    key_column: str,
    key_value: str,
    payload: str | dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> None:
    import psycopg
    from psycopg.types.json import Jsonb

    ensure_schema()
    tenant = tenant_from_path(path)
    extra = extra or {}
    payload_obj = json.loads(payload) if isinstance(payload, str) else payload
    columns = ["tenant_id", key_column, *extra.keys(), "payload"]
    values = [tenant, key_value, *extra.values(), Jsonb(payload_obj)]
    placeholders = ", ".join(["%s"] * len(columns))
    update_columns = [column for column in [*extra.keys(), "payload"]]
    update_sql = ", ".join(f"{column} = EXCLUDED.{column}" for column in update_columns)
    update_sql += ", updated_at = NOW()"
    with psycopg.connect(os.getenv("DATABASE_URL", "")) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {table} ({", ".join(columns)})
                VALUES ({placeholders})
                ON CONFLICT (tenant_id, {key_column}) DO UPDATE SET {update_sql}
                """,
                values,
            )


def delete_by_column(path: Path | str | Any, table: str, column: str, value: str) -> None:
    import psycopg

    ensure_schema()
    tenant = tenant_from_path(path)
    with psycopg.connect(os.getenv("DATABASE_URL", "")) as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE tenant_id = %s AND {column} = %s", (tenant, value))


def delete_rows(path: Path | str | Any, table: str, key_column: str, key_values: Iterable[str]) -> None:
    import psycopg

    ensure_schema()
    tenant = tenant_from_path(path)
    values = list(key_values)
    if not values:
        return
    with psycopg.connect(os.getenv("DATABASE_URL", "")) as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE tenant_id = %s AND {key_column} = ANY(%s)", (tenant, values))


def clear_table(path: Path | str | Any, table: str) -> None:
    import psycopg

    ensure_schema()
    with psycopg.connect(os.getenv("DATABASE_URL", "")) as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE tenant_id = %s", (tenant_from_path(path),))


def count_rows(path: Path | str | Any, table: str, enriched: bool = False) -> tuple[int, int]:
    import psycopg

    ensure_schema()
    with psycopg.connect(os.getenv("DATABASE_URL", "")) as conn:
        with conn.cursor() as cur:
            if enriched:
                cur.execute(
                    f"SELECT COUNT(*), COALESCE(SUM(CASE WHEN enriched THEN 1 ELSE 0 END), 0) FROM {table} WHERE tenant_id = %s",
                    (tenant_from_path(path),),
                )
            else:
                cur.execute(f"SELECT COUNT(*), 0 FROM {table} WHERE tenant_id = %s", (tenant_from_path(path),))
            row = cur.fetchone()
            return int(row[0]), int(row[1])


def _json_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)
