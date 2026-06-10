from __future__ import annotations

import sqlite3
from pathlib import Path

from src.agent.schemas import AgentArtifact, AgentEvent, AgentMessage, AgentRun, AgentStep, AgentTask, AgentThread
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_agent_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_threads (
                thread_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_messages (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                run_id TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
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
            CREATE TABLE IF NOT EXISTS agent_steps (
                step_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                tool_name TEXT NOT NULL,
                status TEXT NOT NULL,
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


def upsert_thread(path: Path, thread: AgentThread) -> None:
    if postgres_enabled():
        upsert_payload(path, "agent_threads", "thread_id", thread.thread_id, thread.to_json(), {"task_id": thread.task_id, "status": thread.status})
        return
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO agent_threads (thread_id, task_id, status, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(thread_id) DO UPDATE SET
                task_id = excluded.task_id,
                status = excluded.status,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (thread.thread_id, thread.task_id, thread.status, thread.to_json()),
        )


def load_thread(path: Path, thread_id: str) -> AgentThread | None:
    if postgres_enabled():
        payload = fetch_payload(path, "agent_threads", "thread_id", thread_id)
        return AgentThread.from_json(payload) if payload else None
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM agent_threads WHERE thread_id = ?", (thread_id,)).fetchone()
    return AgentThread.from_json(row[0]) if row else None


def load_thread_by_task_id(path: Path, task_id: str) -> AgentThread | None:
    if postgres_enabled():
        rows = fetch_payloads(path, "agent_threads", where="task_id = %s", params=(task_id,), order_by="updated_at DESC")
        return AgentThread.from_json(rows[0]) if rows else None
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM agent_threads WHERE task_id = ? ORDER BY updated_at DESC", (task_id,)).fetchone()
    return AgentThread.from_json(row[0]) if row else None


def load_all_threads(path: Path) -> list[AgentThread]:
    if postgres_enabled():
        return [AgentThread.from_json(payload) for payload in fetch_payloads(path, "agent_threads")]
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM agent_threads ORDER BY updated_at DESC").fetchall()
    return [AgentThread.from_json(row[0]) for row in rows]


def upsert_message(path: Path, message: AgentMessage) -> None:
    if postgres_enabled():
        upsert_payload(path, "agent_messages", "message_id", message.message_id, message.to_json(), {"thread_id": message.thread_id, "role": message.role, "run_id": message.run_id})
        return
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO agent_messages (message_id, thread_id, role, run_id, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(message_id) DO UPDATE SET
                thread_id = excluded.thread_id,
                role = excluded.role,
                run_id = excluded.run_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (message.message_id, message.thread_id, message.role, message.run_id, message.to_json()),
        )


def load_messages_for_thread(path: Path, thread_id: str) -> list[AgentMessage]:
    if postgres_enabled():
        return [AgentMessage.from_json(payload) for payload in fetch_payloads(path, "agent_messages", where="thread_id = %s", params=(thread_id,), order_by="updated_at ASC")]
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM agent_messages WHERE thread_id = ? ORDER BY updated_at ASC", (thread_id,)).fetchall()
    return [AgentMessage.from_json(row[0]) for row in rows]


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


def upsert_step(path: Path, step: AgentStep) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "agent_steps",
            "step_id",
            step.step_id,
            step.to_json(),
            {"run_id": step.run_id, "task_id": step.task_id, "sequence": step.sequence, "tool_name": step.tool_name, "status": step.status},
        )
        return
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO agent_steps (step_id, run_id, task_id, sequence, tool_name, status, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(step_id) DO UPDATE SET
                run_id = excluded.run_id,
                task_id = excluded.task_id,
                sequence = excluded.sequence,
                tool_name = excluded.tool_name,
                status = excluded.status,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (step.step_id, step.run_id, step.task_id, step.sequence, step.tool_name, step.status, step.to_json()),
        )


def load_step(path: Path, step_id: str) -> AgentStep | None:
    if postgres_enabled():
        payload = fetch_payload(path, "agent_steps", "step_id", step_id)
        return AgentStep.from_json(payload) if payload else None
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM agent_steps WHERE step_id = ?", (step_id,)).fetchone()
    return AgentStep.from_json(row[0]) if row else None


def load_steps_for_run(path: Path, run_id: str) -> list[AgentStep]:
    if postgres_enabled():
        return [AgentStep.from_json(payload) for payload in fetch_payloads(path, "agent_steps", where="run_id = %s", params=(run_id,), order_by="sequence ASC")]
    init_agent_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM agent_steps WHERE run_id = ? ORDER BY sequence ASC", (run_id,)).fetchall()
    return [AgentStep.from_json(row[0]) for row in rows]


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
