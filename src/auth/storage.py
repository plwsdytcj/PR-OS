from __future__ import annotations

import sqlite3
from pathlib import Path

from src.auth.schemas import AuthSession, AuthUser, ClientAccount, ClientUserLink, ProjectAccess
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_auth_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                client_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS client_users (
                link_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_access (
                access_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                client_id TEXT NOT NULL DEFAULT '',
                proposal_id TEXT NOT NULL DEFAULT '',
                campaign_id TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_user(path: Path, user: AuthUser) -> None:
    if postgres_enabled():
        upsert_payload(path, "auth_users", "user_id", user.user_id, user.to_json(), {"email": user.email.lower()})
        return
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO auth_users (user_id, email, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                email = excluded.email,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user.user_id, user.email.lower(), user.to_json()),
        )


def load_user(path: Path, user_id: str) -> AuthUser | None:
    if postgres_enabled():
        payload = fetch_payload(path, "auth_users", "user_id", user_id)
        return AuthUser.from_json(payload) if payload else None
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM auth_users WHERE user_id = ?", (user_id,)).fetchone()
    return AuthUser.from_json(row[0]) if row else None


def load_user_by_email(path: Path, email: str) -> AuthUser | None:
    normalized = email.strip().lower()
    if postgres_enabled():
        rows = fetch_payloads(path, "auth_users", where="email = %s", params=(normalized,), order_by="")
        return AuthUser.from_json(rows[0]) if rows else None
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM auth_users WHERE email = ?", (normalized,)).fetchone()
    return AuthUser.from_json(row[0]) if row else None


def load_all_users(path: Path) -> list[AuthUser]:
    if postgres_enabled():
        return [AuthUser.from_json(payload) for payload in fetch_payloads(path, "auth_users")]
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM auth_users ORDER BY updated_at DESC").fetchall()
    return [AuthUser.from_json(row[0]) for row in rows]


def upsert_session(path: Path, session: AuthSession) -> None:
    if postgres_enabled():
        upsert_payload(path, "auth_sessions", "session_id", session.session_id, session.to_json(), {"user_id": session.user_id})
        return
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO auth_sessions (session_id, user_id, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                user_id = excluded.user_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (session.session_id, session.user_id, session.to_json()),
        )


def load_session(path: Path, session_id: str) -> AuthSession | None:
    if postgres_enabled():
        payload = fetch_payload(path, "auth_sessions", "session_id", session_id)
        return AuthSession.from_json(payload) if payload else None
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM auth_sessions WHERE session_id = ?", (session_id,)).fetchone()
    return AuthSession.from_json(row[0]) if row else None


def delete_session(path: Path, session_id: str) -> None:
    if postgres_enabled():
        import psycopg
        import os
        from src.storage.postgres_payload import tenant_from_path

        with psycopg.connect(os.getenv("DATABASE_URL", "")) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM auth_sessions WHERE tenant_id = %s AND session_id = %s", (tenant_from_path(path), session_id))
        return
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM auth_sessions WHERE session_id = ?", (session_id,))


def upsert_client(path: Path, client: ClientAccount) -> None:
    if postgres_enabled():
        upsert_payload(path, "clients", "client_id", client.client_id, client.to_json())
        return
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO clients (client_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(client_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (client.client_id, client.to_json()),
        )


def load_client(path: Path, client_id: str) -> ClientAccount | None:
    if postgres_enabled():
        payload = fetch_payload(path, "clients", "client_id", client_id)
        return ClientAccount.from_json(payload) if payload else None
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM clients WHERE client_id = ?", (client_id,)).fetchone()
    return ClientAccount.from_json(row[0]) if row else None


def load_all_clients(path: Path) -> list[ClientAccount]:
    if postgres_enabled():
        return [ClientAccount.from_json(payload) for payload in fetch_payloads(path, "clients")]
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM clients ORDER BY updated_at DESC").fetchall()
    return [ClientAccount.from_json(row[0]) for row in rows]


def upsert_client_user(path: Path, link: ClientUserLink) -> None:
    if postgres_enabled():
        upsert_payload(path, "client_users", "link_id", link.link_id, link.to_json(), {"client_id": link.client_id, "user_id": link.user_id})
        return
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO client_users (link_id, client_id, user_id, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(link_id) DO UPDATE SET
                client_id = excluded.client_id,
                user_id = excluded.user_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (link.link_id, link.client_id, link.user_id, link.to_json()),
        )


def load_client_users_for_user(path: Path, user_id: str) -> list[ClientUserLink]:
    if postgres_enabled():
        return [ClientUserLink.from_json(payload) for payload in fetch_payloads(path, "client_users", where="user_id = %s", params=(user_id,))]
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM client_users WHERE user_id = ?", (user_id,)).fetchall()
    return [ClientUserLink.from_json(row[0]) for row in rows]


def load_client_users_for_client(path: Path, client_id: str) -> list[ClientUserLink]:
    if postgres_enabled():
        return [ClientUserLink.from_json(payload) for payload in fetch_payloads(path, "client_users", where="client_id = %s", params=(client_id,))]
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM client_users WHERE client_id = ?", (client_id,)).fetchall()
    return [ClientUserLink.from_json(row[0]) for row in rows]


def upsert_project_access(path: Path, access: ProjectAccess) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "project_access",
            "access_id",
            access.access_id,
            access.to_json(),
            {"user_id": access.user_id, "client_id": access.client_id, "proposal_id": access.proposal_id, "campaign_id": access.campaign_id},
        )
        return
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO project_access (access_id, user_id, client_id, proposal_id, campaign_id, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(access_id) DO UPDATE SET
                user_id = excluded.user_id,
                client_id = excluded.client_id,
                proposal_id = excluded.proposal_id,
                campaign_id = excluded.campaign_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (access.access_id, access.user_id, access.client_id, access.proposal_id, access.campaign_id, access.to_json()),
        )


def load_project_access_for_user(path: Path, user_id: str) -> list[ProjectAccess]:
    if postgres_enabled():
        return [ProjectAccess.from_json(payload) for payload in fetch_payloads(path, "project_access", where="user_id = %s", params=(user_id,))]
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM project_access WHERE user_id = ?", (user_id,)).fetchall()
    return [ProjectAccess.from_json(row[0]) for row in rows]


def load_all_project_access(path: Path) -> list[ProjectAccess]:
    if postgres_enabled():
        return [ProjectAccess.from_json(payload) for payload in fetch_payloads(path, "project_access")]
    init_auth_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM project_access ORDER BY updated_at DESC").fetchall()
    return [ProjectAccess.from_json(row[0]) for row in rows]
