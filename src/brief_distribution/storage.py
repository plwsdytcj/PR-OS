from __future__ import annotations

import sqlite3
from pathlib import Path

from src.brief_distribution.schemas import CreatorBriefResponse, DistributionBrief
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_distribution_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS distribution_briefs (
                brief_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS creator_brief_responses (
                response_id TEXT PRIMARY KEY,
                brief_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_distribution_brief(path: Path, brief: DistributionBrief) -> None:
    if postgres_enabled():
        upsert_payload(path, "distribution_briefs", "brief_id", brief.brief_id, brief.to_json())
        return
    init_distribution_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO distribution_briefs (brief_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(brief_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (brief.brief_id, brief.to_json()),
        )


def load_distribution_brief(path: Path, brief_id: str) -> DistributionBrief | None:
    if postgres_enabled():
        payload = fetch_payload(path, "distribution_briefs", "brief_id", brief_id)
        return DistributionBrief.from_json(payload) if payload else None
    init_distribution_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM distribution_briefs WHERE brief_id = ?", (brief_id,)).fetchone()
    return DistributionBrief.from_json(row[0]) if row else None


def load_all_distribution_briefs(path: Path) -> list[DistributionBrief]:
    if postgres_enabled():
        return [DistributionBrief.from_json(payload) for payload in fetch_payloads(path, "distribution_briefs")]
    init_distribution_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM distribution_briefs ORDER BY updated_at DESC").fetchall()
    return [DistributionBrief.from_json(row[0]) for row in rows]


def load_distribution_brief_by_token(path: Path, token: str) -> tuple[DistributionBrief, str] | None:
    for brief in load_all_distribution_briefs(path):
        for recipient in brief.recipients:
            if recipient.token == token:
                return brief, recipient.recipient_id
    return None


def upsert_creator_response(path: Path, response: CreatorBriefResponse) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "creator_brief_responses",
            "response_id",
            response.response_id,
            response.to_json(),
            {"brief_id": response.brief_id, "recipient_id": response.recipient_id, "creator_id": response.creator_id},
        )
        return
    init_distribution_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO creator_brief_responses (response_id, brief_id, recipient_id, creator_id, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(response_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (response.response_id, response.brief_id, response.recipient_id, response.creator_id, response.to_json()),
        )


def load_responses_for_brief(path: Path, brief_id: str) -> list[CreatorBriefResponse]:
    if postgres_enabled():
        return [
            CreatorBriefResponse.from_json(payload)
            for payload in fetch_payloads(path, "creator_brief_responses", where="brief_id = %s", params=(brief_id,))
        ]
    init_distribution_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT payload FROM creator_brief_responses WHERE brief_id = ? ORDER BY updated_at DESC",
            (brief_id,),
        ).fetchall()
    return [CreatorBriefResponse.from_json(row[0]) for row in rows]
