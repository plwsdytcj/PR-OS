from __future__ import annotations

import sqlite3
from pathlib import Path

from src.symbolic.schemas import BrandSymbolicProfile, CreatorSymbolicProfile
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_symbolic_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS creator_symbolic_profiles (
                creator_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS brand_symbolic_profiles (
                brand_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS simulation_reports (
                report_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_creator_symbolic(path: Path, profile: CreatorSymbolicProfile) -> None:
    if postgres_enabled():
        upsert_payload(path, "creator_symbolic_profiles", "creator_id", profile.creator_id, profile.to_json())
        return
    init_symbolic_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO creator_symbolic_profiles (creator_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(creator_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (profile.creator_id, profile.to_json()),
        )


def load_creator_symbolic(path: Path, creator_id: str) -> CreatorSymbolicProfile | None:
    if postgres_enabled():
        payload = fetch_payload(path, "creator_symbolic_profiles", "creator_id", creator_id)
        return CreatorSymbolicProfile.from_json(payload) if payload else None
    init_symbolic_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM creator_symbolic_profiles WHERE creator_id = ?", (creator_id,)).fetchone()
    return CreatorSymbolicProfile.from_json(row[0]) if row else None


def load_all_creator_symbolic(path: Path) -> list[CreatorSymbolicProfile]:
    if postgres_enabled():
        return [CreatorSymbolicProfile.from_json(payload) for payload in fetch_payloads(path, "creator_symbolic_profiles")]
    init_symbolic_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM creator_symbolic_profiles ORDER BY updated_at DESC").fetchall()
    return [CreatorSymbolicProfile.from_json(row[0]) for row in rows]


def upsert_brand_symbolic(path: Path, profile: BrandSymbolicProfile) -> None:
    if postgres_enabled():
        upsert_payload(path, "brand_symbolic_profiles", "brand_id", profile.brand_id, profile.to_json())
        return
    init_symbolic_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO brand_symbolic_profiles (brand_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(brand_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (profile.brand_id, profile.to_json()),
        )


def load_brand_symbolic(path: Path, brand_id: str) -> BrandSymbolicProfile | None:
    if postgres_enabled():
        payload = fetch_payload(path, "brand_symbolic_profiles", "brand_id", brand_id)
        return BrandSymbolicProfile.from_json(payload) if payload else None
    init_symbolic_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM brand_symbolic_profiles WHERE brand_id = ?", (brand_id,)).fetchone()
    return BrandSymbolicProfile.from_json(row[0]) if row else None


def load_all_brand_symbolic(path: Path) -> list[BrandSymbolicProfile]:
    if postgres_enabled():
        return [BrandSymbolicProfile.from_json(payload) for payload in fetch_payloads(path, "brand_symbolic_profiles")]
    init_symbolic_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM brand_symbolic_profiles ORDER BY updated_at DESC").fetchall()
    return [BrandSymbolicProfile.from_json(row[0]) for row in rows]
