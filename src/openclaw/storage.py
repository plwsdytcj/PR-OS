from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from src.openclaw.schemas import OpenClawConfig, OpenClawEvent, OpenClawRun, OpenClawUserBinding, binding_id_for
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_openclaw_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS openclaw_configs (
                config_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS openclaw_user_bindings (
                binding_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS openclaw_runs (
                run_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                openclaw_agent_id TEXT NOT NULL DEFAULT '',
                openclaw_session_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS openclaw_events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def default_config_from_env() -> OpenClawConfig:
    return OpenClawConfig(
        enabled=os.getenv("OPENCLAW_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
        gateway_url=os.getenv("OPENCLAW_GATEWAY_URL", "").strip(),
        control_ui_url=os.getenv("OPENCLAW_CONTROL_UI_URL", "").strip(),
        admin_token=os.getenv("OPENCLAW_ADMIN_TOKEN", "").strip(),
        default_agent_id=os.getenv("OPENCLAW_DEFAULT_AGENT_ID", "kolness_default").strip() or "kolness_default",
        proxy_base_path=os.getenv("OPENCLAW_PROXY_BASE_PATH", "/openclaw").strip() or "/openclaw",
    )


def load_config(path: Path) -> OpenClawConfig:
    if postgres_enabled():
        payload = fetch_payload(path, "openclaw_configs", "config_id", "default")
        return OpenClawConfig.from_json(payload) if payload else default_config_from_env()
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM openclaw_configs WHERE config_id = ?", ("default",)).fetchone()
    return OpenClawConfig.from_json(row[0]) if row else default_config_from_env()


def save_config(path: Path, config: OpenClawConfig) -> None:
    if postgres_enabled():
        upsert_payload(path, "openclaw_configs", "config_id", config.config_id, config.to_json())
        return
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO openclaw_configs (config_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(config_id) DO UPDATE SET payload = excluded.payload, updated_at = CURRENT_TIMESTAMP
            """,
            (config.config_id, config.to_json()),
        )


def load_binding(path: Path, user_id: str) -> OpenClawUserBinding | None:
    binding_id = binding_id_for(user_id)
    if postgres_enabled():
        payload = fetch_payload(path, "openclaw_user_bindings", "binding_id", binding_id)
        return OpenClawUserBinding.from_json(payload) if payload else None
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM openclaw_user_bindings WHERE binding_id = ?", (binding_id,)).fetchone()
    return OpenClawUserBinding.from_json(row[0]) if row else None


def load_all_bindings(path: Path) -> list[OpenClawUserBinding]:
    if postgres_enabled():
        return [OpenClawUserBinding.from_json(payload) for payload in fetch_payloads(path, "openclaw_user_bindings")]
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM openclaw_user_bindings ORDER BY updated_at DESC").fetchall()
    return [OpenClawUserBinding.from_json(row[0]) for row in rows]


def save_binding(path: Path, binding: OpenClawUserBinding) -> None:
    if postgres_enabled():
        upsert_payload(path, "openclaw_user_bindings", "binding_id", binding.binding_id, binding.to_json(), {"user_id": binding.user_id})
        return
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO openclaw_user_bindings (binding_id, user_id, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(binding_id) DO UPDATE SET user_id = excluded.user_id, payload = excluded.payload, updated_at = CURRENT_TIMESTAMP
            """,
            (binding.binding_id, binding.user_id, binding.to_json()),
        )


def save_run(path: Path, run: OpenClawRun) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "openclaw_runs",
            "run_id",
            run.run_id,
            run.to_json(),
            {
                "user_id": run.user_id,
                "openclaw_agent_id": run.openclaw_agent_id,
                "openclaw_session_id": run.openclaw_session_id,
                "status": run.status,
            },
        )
        return
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO openclaw_runs (run_id, user_id, openclaw_agent_id, openclaw_session_id, status, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(run_id) DO UPDATE SET
                user_id = excluded.user_id,
                openclaw_agent_id = excluded.openclaw_agent_id,
                openclaw_session_id = excluded.openclaw_session_id,
                status = excluded.status,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (run.run_id, run.user_id, run.openclaw_agent_id, run.openclaw_session_id, run.status, run.to_json()),
        )


def load_run(path: Path, run_id: str) -> OpenClawRun | None:
    if postgres_enabled():
        payload = fetch_payload(path, "openclaw_runs", "run_id", run_id)
        return OpenClawRun.from_json(payload) if payload else None
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM openclaw_runs WHERE run_id = ?", (run_id,)).fetchone()
    return OpenClawRun.from_json(row[0]) if row else None


def save_event(path: Path, event: OpenClawEvent) -> None:
    if postgres_enabled():
        upsert_payload(path, "openclaw_events", "event_id", event.event_id, event.to_json(), {"run_id": event.run_id, "sequence": event.sequence, "event_type": event.event_type})
        return
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO openclaw_events (event_id, run_id, sequence, event_type, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(event_id) DO UPDATE SET
                run_id = excluded.run_id,
                sequence = excluded.sequence,
                event_type = excluded.event_type,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (event.event_id, event.run_id, event.sequence, event.event_type, event.to_json()),
        )


def load_events_for_run(path: Path, run_id: str) -> list[OpenClawEvent]:
    if postgres_enabled():
        return [OpenClawEvent.from_json(payload) for payload in fetch_payloads(path, "openclaw_events", where="run_id = %s", params=(run_id,), order_by="sequence ASC")]
    init_openclaw_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM openclaw_events WHERE run_id = ? ORDER BY sequence ASC", (run_id,)).fetchall()
    return [OpenClawEvent.from_json(row[0]) for row in rows]

