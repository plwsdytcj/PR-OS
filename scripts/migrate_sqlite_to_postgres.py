from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "db" / "postgres_schema.sql"

TABLES: dict[str, dict[str, Any]] = {
    "creator_profiles": {"pk": "creator_id", "columns": ["creator_id", "payload", "enriched"]},
    "creator_symbolic_profiles": {"pk": "creator_id", "columns": ["creator_id", "payload"]},
    "brand_symbolic_profiles": {"pk": "brand_id", "columns": ["brand_id", "payload"]},
    "simulation_reports": {"pk": "report_id", "columns": ["report_id", "payload"]},
    "social_symbolic_reports": {"pk": "report_id", "columns": ["report_id", "payload"]},
    "signifier_tags": {"pk": "tag_id", "columns": ["tag_id", "payload"]},
    "product_symbolic_profiles": {"pk": "product_id", "columns": ["product_id", "brand_id", "payload"]},
    "content_narrative_assets": {"pk": "narrative_id", "columns": ["narrative_id", "brand_id", "creator_id", "payload"]},
    "brand_creator_match_assets": {"pk": "match_id", "columns": ["match_id", "brand_id", "creator_id", "payload"]},
    "feedback_corrections": {"pk": "correction_id", "columns": ["correction_id", "campaign_id", "creator_id", "payload"]},
    "proposals": {"pk": "proposal_id", "columns": ["proposal_id", "share_token", "payload"]},
    "proposal_versions": {"pk": "version_id", "columns": ["version_id", "proposal_id", "version_number", "payload"]},
    "client_feedback": {"pk": "feedback_id", "columns": ["feedback_id", "proposal_id", "version_id", "payload"]},
    "brand_preferences": {"pk": "client_id", "columns": ["client_id", "payload"]},
    "creator_invitations": {"pk": "invitation_id", "columns": ["invitation_id", "token", "creator_id", "payload"]},
    "creator_submissions": {"pk": "submission_id", "columns": ["submission_id", "invitation_id", "creator_id", "payload"]},
    "creator_commercial_profiles": {"pk": "creator_id", "columns": ["creator_id", "payload"]},
    "distribution_briefs": {"pk": "brief_id", "columns": ["brief_id", "payload"]},
    "creator_brief_responses": {"pk": "response_id", "columns": ["response_id", "brief_id", "recipient_id", "creator_id", "payload"]},
    "campaign_projects": {"pk": "campaign_id", "columns": ["campaign_id", "payload"]},
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate PR AI OS SQLite payload tables to PostgreSQL JSONB tables.")
    parser.add_argument("--sqlite", required=True, help="Path to source SQLite database.")
    parser.add_argument("--database-url", default="", help="PostgreSQL connection URL. Omit with --dry-run.")
    parser.add_argument("--tenant", default="default", help="Tenant/workspace id to attach to migrated rows.")
    parser.add_argument("--schema", default=str(SCHEMA_PATH), help="PostgreSQL schema SQL path.")
    parser.add_argument("--dry-run", action="store_true", help="Only inspect source rows and print counts.")
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite)
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite database not found: {sqlite_path}")

    rows_by_table = read_sqlite(sqlite_path)
    counts = {table: len(rows) for table, rows in rows_by_table.items()}
    print(json.dumps({"sqlite": str(sqlite_path), "tenant": args.tenant, "counts": counts}, ensure_ascii=False, indent=2))
    if args.dry_run:
        return
    if not args.database_url:
        raise SystemExit("--database-url is required unless --dry-run is set")
    migrate_to_postgres(args.database_url, Path(args.schema), args.tenant, rows_by_table)
    print("migration_complete")


def read_sqlite(path: Path) -> dict[str, list[dict[str, Any]]]:
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        result: dict[str, list[dict[str, Any]]] = {}
        for table, spec in TABLES.items():
            if table not in existing:
                result[table] = []
                continue
            columns = [column for column in spec["columns"] if _has_column(conn, table, column)]
            if not columns:
                result[table] = []
                continue
            rows = conn.execute(f"SELECT {', '.join(columns)} FROM {table}").fetchall()
            result[table] = [dict(row) for row in rows]
        return result


def migrate_to_postgres(database_url: str, schema_path: Path, tenant: str, rows_by_table: dict[str, list[dict[str, Any]]]) -> None:
    try:
        import psycopg
        from psycopg.types.json import Jsonb
    except ImportError as exc:
        raise SystemExit("psycopg is required for live migration. Install requirements.txt first.") from exc

    schema_sql = schema_path.read_text(encoding="utf-8")
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            for table, rows in rows_by_table.items():
                spec = TABLES[table]
                columns = ["tenant_id"] + spec["columns"]
                placeholders = ", ".join(["%s"] * len(columns))
                update_columns = [column for column in spec["columns"] if column != spec["pk"]]
                update_sql = ", ".join(f"{column} = EXCLUDED.{column}" for column in update_columns)
                if "updated_at" in _postgres_columns(cur, table):
                    update_sql = f"{update_sql}, updated_at = NOW()" if update_sql else "updated_at = NOW()"
                for row in rows:
                    values = [tenant]
                    for column in spec["columns"]:
                        value = row.get(column)
                        if column == "payload":
                            value = Jsonb(json.loads(value or "{}"))
                        if column == "enriched":
                            value = bool(value)
                        values.append(value)
                    conflict = f"(tenant_id, {spec['pk']})"
                    cur.execute(
                        f"""
                        INSERT INTO {table} ({', '.join(columns)})
                        VALUES ({placeholders})
                        ON CONFLICT {conflict} DO UPDATE SET {update_sql}
                        """,
                        values,
                    )


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})").fetchall())


def _postgres_columns(cur: Any, table: str) -> set[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        """,
        (table,),
    )
    return {row[0] for row in cur.fetchall()}


if __name__ == "__main__":
    main()
