from __future__ import annotations

import sqlite3
from pathlib import Path

from src.agent.schemas import AgentArtifact, AgentEvent, AgentRun, AgentTask
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_agent_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_runs (
                run_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_artifacts (
                artifact_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_task(path: Path, task: AgentTask) -> None:
    if postgres_enabled():
        upsert_payload(path, "agent_tasks", "task_id", task.task_id, task.to_json(), {"status": task.status})
        return
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO agent_tasks (task_id, status, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(task_id) DO UPDATE SET
                status = excluded.status,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (task.task_id, task.status, task.to_json()),
        )


def load_task(path: Path, task_id: str) -> AgentTask | None:
    if postgres_enabled():
        payload = fetch_payload(path, "agent_tasks", "task_id", task_id)
        return AgentTask.from_json(payload) if payload else None
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM agent_tasks WHERE task_id = ?", (task_id,)).fetchone()
    return AgentTask.from_json(row[0]) if row else None


def load_all_tasks(path: Path) -> list[AgentTask]:
    if postgres_enabled():
        return [AgentTask.from_json(payload) for payload in fetch_payloads(path, "agent_tasks")]
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM agent_tasks ORDER BY updated_at DESC").fetchall()
    return [AgentTask.from_json(row[0]) for row in rows]


def upsert_run(path: Path, run: AgentRun) -> None:
    if postgres_enabled():
        upsert_payload(path, "agent_runs", "run_id", run.run_id, run.to_json(), {"task_id": run.task_id, "status": run.status})
        return
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO agent_runs (run_id, task_id, status, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(run_id) DO UPDATE SET
                task_id = excluded.task_id,
                status = excluded.status,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (run.run_id, run.task_id, run.status, run.to_json()),
        )


def load_run(path: Path, run_id: str) -> AgentRun | None:
    if postgres_enabled():
        payload = fetch_payload(path, "agent_runs", "run_id", run_id)
        return AgentRun.from_json(payload) if payload else None
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM agent_runs WHERE run_id = ?", (run_id,)).fetchone()
    return AgentRun.from_json(row[0]) if row else None


def load_runs_for_task(path: Path, task_id: str) -> list[AgentRun]:
    if postgres_enabled():
        return [AgentRun.from_json(payload) for payload in fetch_payloads(path, "agent_runs", where="task_id = %s", params=(task_id,))]
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM agent_runs WHERE task_id = ? ORDER BY updated_at DESC", (task_id,)).fetchall()
    return [AgentRun.from_json(row[0]) for row in rows]


def upsert_event(path: Path, event: AgentEvent) -> None:
    if postgres_enabled():
        upsert_payload(path, "agent_events", "event_id", event.event_id, event.to_json(), {"run_id": event.run_id, "task_id": event.task_id, "sequence": event.sequence})
        return
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO agent_events (event_id, run_id, task_id, sequence, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(event_id) DO UPDATE SET
                run_id = excluded.run_id,
                task_id = excluded.task_id,
                sequence = excluded.sequence,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (event.event_id, event.run_id, event.task_id, event.sequence, event.to_json()),
        )


def load_events_for_run(path: Path, run_id: str) -> list[AgentEvent]:
    if postgres_enabled():
        return [AgentEvent.from_json(payload) for payload in fetch_payloads(path, "agent_events", where="run_id = %s", params=(run_id,), order_by="sequence ASC")]
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM agent_events WHERE run_id = ? ORDER BY sequence ASC", (run_id,)).fetchall()
    return [AgentEvent.from_json(row[0]) for row in rows]


def upsert_artifact(path: Path, artifact: AgentArtifact) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "agent_artifacts",
            "artifact_id",
            artifact.artifact_id,
            artifact.to_json(),
            {"task_id": artifact.task_id, "run_id": artifact.run_id, "artifact_type": artifact.artifact_type},
        )
        return
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO agent_artifacts (artifact_id, task_id, run_id, artifact_type, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(artifact_id) DO UPDATE SET
                task_id = excluded.task_id,
                run_id = excluded.run_id,
                artifact_type = excluded.artifact_type,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (artifact.artifact_id, artifact.task_id, artifact.run_id, artifact.artifact_type, artifact.to_json()),
        )


def load_artifact(path: Path, artifact_id: str) -> AgentArtifact | None:
    if postgres_enabled():
        payload = fetch_payload(path, "agent_artifacts", "artifact_id", artifact_id)
        return AgentArtifact.from_json(payload) if payload else None
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM agent_artifacts WHERE artifact_id = ?", (artifact_id,)).fetchone()
    return AgentArtifact.from_json(row[0]) if row else None


def load_artifacts_for_task(path: Path, task_id: str) -> list[AgentArtifact]:
    if postgres_enabled():
        return [AgentArtifact.from_json(payload) for payload in fetch_payloads(path, "agent_artifacts", where="task_id = %s", params=(task_id,))]
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM agent_artifacts WHERE task_id = ? ORDER BY updated_at DESC", (task_id,)).fetchall()
    return [AgentArtifact.from_json(row[0]) for row in rows]
