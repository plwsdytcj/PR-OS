from __future__ import annotations

import sqlite3
from pathlib import Path

from src.creator_commercial.schemas import CreatorCommercialProfile, CreatorInvitation, CreatorSubmission
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_creator_commercial_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS creator_invitations (
                invitation_id TEXT PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                creator_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS creator_submissions (
                submission_id TEXT PRIMARY KEY,
                invitation_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS creator_commercial_profiles (
                creator_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_invitation(path: Path, invitation: CreatorInvitation) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "creator_invitations",
            "invitation_id",
            invitation.invitation_id,
            invitation.to_json(),
            {"token": invitation.token, "creator_id": invitation.creator_id},
        )
        return
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO creator_invitations (invitation_id, token, creator_id, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(invitation_id) DO UPDATE SET
                token = excluded.token,
                creator_id = excluded.creator_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (invitation.invitation_id, invitation.token, invitation.creator_id, invitation.to_json()),
        )


def load_invitation(path: Path, invitation_id: str) -> CreatorInvitation | None:
    if postgres_enabled():
        payload = fetch_payload(path, "creator_invitations", "invitation_id", invitation_id)
        return CreatorInvitation.from_json(payload) if payload else None
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM creator_invitations WHERE invitation_id = ?", (invitation_id,)).fetchone()
    return CreatorInvitation.from_json(row[0]) if row else None


def load_invitation_by_token(path: Path, token: str) -> CreatorInvitation | None:
    if postgres_enabled():
        rows = fetch_payloads(path, "creator_invitations", where="token = %s", params=(token,), order_by="")
        return CreatorInvitation.from_json(rows[0]) if rows else None
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM creator_invitations WHERE token = ?", (token,)).fetchone()
    return CreatorInvitation.from_json(row[0]) if row else None


def load_all_invitations(path: Path) -> list[CreatorInvitation]:
    if postgres_enabled():
        return [CreatorInvitation.from_json(payload) for payload in fetch_payloads(path, "creator_invitations")]
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM creator_invitations ORDER BY updated_at DESC").fetchall()
    return [CreatorInvitation.from_json(row[0]) for row in rows]


def upsert_submission(path: Path, submission: CreatorSubmission) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "creator_submissions",
            "submission_id",
            submission.submission_id,
            submission.to_json(),
            {"invitation_id": submission.invitation_id, "creator_id": submission.creator_id},
        )
        return
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO creator_submissions (submission_id, invitation_id, creator_id, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(submission_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (submission.submission_id, submission.invitation_id, submission.creator_id, submission.to_json()),
        )


def load_submission(path: Path, submission_id: str) -> CreatorSubmission | None:
    if postgres_enabled():
        payload = fetch_payload(path, "creator_submissions", "submission_id", submission_id)
        return CreatorSubmission.from_json(payload) if payload else None
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM creator_submissions WHERE submission_id = ?", (submission_id,)).fetchone()
    return CreatorSubmission.from_json(row[0]) if row else None


def load_submissions_for_creator(path: Path, creator_id: str) -> list[CreatorSubmission]:
    if postgres_enabled():
        return [
            CreatorSubmission.from_json(payload)
            for payload in fetch_payloads(path, "creator_submissions", where="creator_id = %s", params=(creator_id,))
        ]
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT payload FROM creator_submissions WHERE creator_id = ? ORDER BY updated_at DESC",
            (creator_id,),
        ).fetchall()
    return [CreatorSubmission.from_json(row[0]) for row in rows]


def load_all_submissions(path: Path) -> list[CreatorSubmission]:
    if postgres_enabled():
        return [CreatorSubmission.from_json(payload) for payload in fetch_payloads(path, "creator_submissions")]
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM creator_submissions ORDER BY updated_at DESC").fetchall()
    return [CreatorSubmission.from_json(row[0]) for row in rows]


def upsert_commercial_profile(path: Path, profile: CreatorCommercialProfile) -> None:
    if postgres_enabled():
        upsert_payload(path, "creator_commercial_profiles", "creator_id", profile.creator_id, profile.to_json())
        return
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO creator_commercial_profiles (creator_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(creator_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (profile.creator_id, profile.to_json()),
        )


def load_commercial_profile(path: Path, creator_id: str) -> CreatorCommercialProfile | None:
    if postgres_enabled():
        payload = fetch_payload(path, "creator_commercial_profiles", "creator_id", creator_id)
        return CreatorCommercialProfile.from_json(payload) if payload else None
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM creator_commercial_profiles WHERE creator_id = ?", (creator_id,)).fetchone()
    return CreatorCommercialProfile.from_json(row[0]) if row else None


def load_all_commercial_profiles(path: Path) -> list[CreatorCommercialProfile]:
    if postgres_enabled():
        return [CreatorCommercialProfile.from_json(payload) for payload in fetch_payloads(path, "creator_commercial_profiles")]
    init_creator_commercial_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM creator_commercial_profiles ORDER BY updated_at DESC").fetchall()
    return [CreatorCommercialProfile.from_json(row[0]) for row in rows]
