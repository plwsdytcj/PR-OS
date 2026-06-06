from __future__ import annotations

import sqlite3
from pathlib import Path

from src.intelligence.data_quality import strong_dedupe_profiles
from src.schemas import CreatorProfile
from src.storage.postgres_payload import clear_table, count_rows, delete_rows, fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS creator_profiles (
                creator_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                enriched INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def load_profiles(path: Path) -> list[CreatorProfile]:
    if postgres_enabled():
        return [CreatorProfile.from_json(payload) for payload in fetch_payloads(path, "creator_profiles")]
    init_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM creator_profiles ORDER BY updated_at DESC").fetchall()
    return [CreatorProfile.from_json(row[0]) for row in rows]


def load_profile(path: Path, creator_id: str) -> CreatorProfile | None:
    if postgres_enabled():
        payload = fetch_payload(path, "creator_profiles", "creator_id", creator_id)
        return CreatorProfile.from_json(payload) if payload else None
    init_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM creator_profiles WHERE creator_id = ?", (creator_id,)).fetchone()
    return CreatorProfile.from_json(row[0]) if row else None


def upsert_profiles(path: Path, profiles: list[CreatorProfile]) -> None:
    if postgres_enabled():
        existing_profiles = load_profiles(path)
        profiles, _ = strong_dedupe_profiles(existing_profiles + profiles)
        existing_ids = {p.creator_id for p in existing_profiles}
        incoming_ids = {p.creator_id for p in profiles}
        delete_rows(path, "creator_profiles", "creator_id", existing_ids - incoming_ids)
        for profile in profiles:
            upsert_payload(path, "creator_profiles", "creator_id", profile.creator_id, profile.to_json(), {"enriched": bool(profile.ai_summary)})
        return
    init_db(path)
    existing_profiles = load_profiles(path)
    profiles, _ = strong_dedupe_profiles(existing_profiles + profiles)
    existing_ids = {p.creator_id for p in existing_profiles}
    incoming_ids = {p.creator_id for p in profiles}
    merged: list[CreatorProfile] = []
    for profile in profiles:
        merged.append(profile)
    with sqlite3.connect(path) as conn:
        for creator_id in existing_ids - incoming_ids:
            conn.execute("DELETE FROM creator_profiles WHERE creator_id = ?", (creator_id,))
        for profile in merged:
            conn.execute(
                """
                INSERT INTO creator_profiles (creator_id, payload, enriched, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(creator_id) DO UPDATE SET
                    payload = excluded.payload,
                    enriched = excluded.enriched,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (profile.creator_id, profile.to_json(), int(bool(profile.ai_summary))),
            )


def replace_profiles(path: Path, profiles: list[CreatorProfile]) -> None:
    if postgres_enabled():
        clear_table(path, "creator_profiles")
        upsert_profiles(path, profiles)
        return
    init_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM creator_profiles")
    upsert_profiles(path, profiles)


def count_profiles(path: Path) -> tuple[int, int]:
    if postgres_enabled():
        return count_rows(path, "creator_profiles", enriched=True)
    init_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT COUNT(*), COALESCE(SUM(enriched), 0) FROM creator_profiles").fetchone()
    return int(row[0]), int(row[1])


def save_profile(path: Path, profile: CreatorProfile) -> None:
    if postgres_enabled():
        upsert_payload(path, "creator_profiles", "creator_id", profile.creator_id, profile.to_json(), {"enriched": bool(profile.ai_summary)})
        return
    init_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO creator_profiles (creator_id, payload, enriched, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(creator_id) DO UPDATE SET
                payload = excluded.payload,
                enriched = excluded.enriched,
                updated_at = CURRENT_TIMESTAMP
            """,
            (profile.creator_id, profile.to_json(), int(bool(profile.ai_summary))),
        )


def delete_profiles(path: Path, creator_ids: list[str]) -> None:
    if postgres_enabled():
        delete_rows(path, "creator_profiles", "creator_id", creator_ids)
        return
    init_db(path)
    with sqlite3.connect(path) as conn:
        conn.executemany("DELETE FROM creator_profiles WHERE creator_id = ?", [(creator_id,) for creator_id in creator_ids])


def merge_profiles(path: Path, primary_id: str, duplicate_ids: list[str]) -> CreatorProfile:
    profiles = load_profiles(path)
    lookup = {profile.creator_id: profile for profile in profiles}
    if primary_id not in lookup:
        raise KeyError(primary_id)
    merged = lookup[primary_id]
    for duplicate_id in duplicate_ids:
        if duplicate_id in lookup and duplicate_id != primary_id:
            merged = merged.merge(lookup[duplicate_id])
    delete_profiles(path, [creator_id for creator_id in duplicate_ids if creator_id != primary_id])
    upsert_profiles(path, [merged])
    return merged
