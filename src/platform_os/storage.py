from __future__ import annotations

import sqlite3
from pathlib import Path

from src.platform_os.schemas import CampaignProject
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_platform_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS campaign_projects (
                campaign_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_campaign_project(path: Path, project: CampaignProject) -> None:
    if postgres_enabled():
        upsert_payload(path, "campaign_projects", "campaign_id", project.campaign.campaign_id, project.to_json())
        return
    init_platform_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO campaign_projects (campaign_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(campaign_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (project.campaign.campaign_id, project.to_json()),
        )


def load_campaign_project(path: Path, campaign_id: str) -> CampaignProject | None:
    if postgres_enabled():
        payload = fetch_payload(path, "campaign_projects", "campaign_id", campaign_id)
        return CampaignProject.from_json(payload) if payload else None
    init_platform_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM campaign_projects WHERE campaign_id = ?", (campaign_id,)).fetchone()
    return CampaignProject.from_json(row[0]) if row else None


def load_all_campaign_projects(path: Path) -> list[CampaignProject]:
    if postgres_enabled():
        return [CampaignProject.from_json(payload) for payload in fetch_payloads(path, "campaign_projects")]
    init_platform_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM campaign_projects ORDER BY updated_at DESC").fetchall()
    return [CampaignProject.from_json(row[0]) for row in rows]
