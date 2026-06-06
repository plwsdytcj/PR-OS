from __future__ import annotations

import sqlite3
import json
from pathlib import Path

from src.collaboration.schemas import BrandPreferenceProfile, ClientFeedback, Proposal, ProposalVersion
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_collaboration_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proposals (
                proposal_id TEXT PRIMARY KEY,
                share_token TEXT UNIQUE NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proposal_versions (
                version_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS client_feedback (
                feedback_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                version_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS brand_preferences (
                client_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_proposal(path: Path, proposal: Proposal) -> None:
    if postgres_enabled():
        upsert_payload(path, "proposals", "proposal_id", proposal.proposal_id, proposal.to_json(), {"share_token": proposal.share_token})
        return
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO proposals (proposal_id, share_token, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(proposal_id) DO UPDATE SET
                share_token = excluded.share_token,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (proposal.proposal_id, proposal.share_token, proposal.to_json()),
        )


def load_proposal(path: Path, proposal_id: str) -> Proposal | None:
    if postgres_enabled():
        payload = fetch_payload(path, "proposals", "proposal_id", proposal_id)
        return Proposal.from_json(payload) if payload else None
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
    return Proposal.from_json(row[0]) if row else None


def load_proposal_by_token(path: Path, token: str) -> Proposal | None:
    if postgres_enabled():
        rows = fetch_payloads(path, "proposals", where="share_token = %s", params=(token,), order_by="")
        return Proposal.from_json(rows[0]) if rows else None
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM proposals WHERE share_token = ?", (token,)).fetchone()
    return Proposal.from_json(row[0]) if row else None


def load_all_proposals(path: Path) -> list[Proposal]:
    if postgres_enabled():
        return [Proposal.from_json(payload) for payload in fetch_payloads(path, "proposals")]
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM proposals ORDER BY updated_at DESC").fetchall()
    return [Proposal.from_json(row[0]) for row in rows]


def upsert_version(path: Path, version: ProposalVersion) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "proposal_versions",
            "version_id",
            version.version_id,
            _version_json(version),
            {"proposal_id": version.proposal_id, "version_number": version.version_number},
        )
        return
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO proposal_versions (version_id, proposal_id, version_number, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(version_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (version.version_id, version.proposal_id, version.version_number, _version_json(version)),
        )


def load_versions(path: Path, proposal_id: str) -> list[ProposalVersion]:
    if postgres_enabled():
        return [
            ProposalVersion.from_dict(json.loads(payload))
            for payload in fetch_payloads(path, "proposal_versions", where="proposal_id = %s", params=(proposal_id,), order_by="version_number")
        ]
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT payload FROM proposal_versions WHERE proposal_id = ? ORDER BY version_number",
            (proposal_id,),
        ).fetchall()
    return [ProposalVersion.from_dict(json.loads(row[0])) for row in rows]


def load_version(path: Path, version_id: str) -> ProposalVersion | None:
    if postgres_enabled():
        payload = fetch_payload(path, "proposal_versions", "version_id", version_id)
        return ProposalVersion.from_dict(json.loads(payload)) if payload else None
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM proposal_versions WHERE version_id = ?", (version_id,)).fetchone()
    return ProposalVersion.from_dict(json.loads(row[0])) if row else None


def upsert_feedback(path: Path, feedback: ClientFeedback) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "client_feedback",
            "feedback_id",
            feedback.feedback_id,
            feedback.to_json(),
            {"proposal_id": feedback.proposal_id, "version_id": feedback.version_id},
        )
        return
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO client_feedback (feedback_id, proposal_id, version_id, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(feedback_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (feedback.feedback_id, feedback.proposal_id, feedback.version_id, feedback.to_json()),
        )


def load_feedback(path: Path, proposal_id: str) -> list[ClientFeedback]:
    if postgres_enabled():
        return [
            ClientFeedback.from_json(payload)
            for payload in fetch_payloads(path, "client_feedback", where="proposal_id = %s", params=(proposal_id,))
        ]
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT payload FROM client_feedback WHERE proposal_id = ? ORDER BY updated_at DESC",
            (proposal_id,),
        ).fetchall()
    return [ClientFeedback.from_json(row[0]) for row in rows]


def load_feedback_item(path: Path, feedback_id: str) -> ClientFeedback | None:
    if postgres_enabled():
        payload = fetch_payload(path, "client_feedback", "feedback_id", feedback_id)
        return ClientFeedback.from_json(payload) if payload else None
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM client_feedback WHERE feedback_id = ?", (feedback_id,)).fetchone()
    return ClientFeedback.from_json(row[0]) if row else None


def upsert_preference(path: Path, preference: BrandPreferenceProfile) -> None:
    if postgres_enabled():
        upsert_payload(path, "brand_preferences", "client_id", preference.client_id, preference.to_json())
        return
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO brand_preferences (client_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(client_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (preference.client_id, preference.to_json()),
        )


def load_preference(path: Path, client_id: str) -> BrandPreferenceProfile | None:
    if postgres_enabled():
        payload = fetch_payload(path, "brand_preferences", "client_id", client_id)
        return BrandPreferenceProfile.from_json(payload) if payload else None
    init_collaboration_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM brand_preferences WHERE client_id = ?", (client_id,)).fetchone()
    return BrandPreferenceProfile.from_json(row[0]) if row else None


def _version_json(version: ProposalVersion) -> str:
    return json.dumps(version.to_dict(), ensure_ascii=False)
