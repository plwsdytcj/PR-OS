from __future__ import annotations

import sqlite3
from pathlib import Path

from src.kol_intelligence.schemas import KolEvidenceTag, KolGraphSnapshot, KolPrediction
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_kol_intelligence_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kol_evidence_tags (
                tag_id TEXT PRIMARY KEY,
                creator_id TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kol_graph_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kol_predictions (
                prediction_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_evidence_tag(path: Path, tag: KolEvidenceTag) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "kol_evidence_tags",
            "tag_id",
            tag.tag_id,
            tag.to_json(),
            extra={"creator_id": tag.creator_id, "category": tag.category, "status": tag.status},
        )
        return
    init_kol_intelligence_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO kol_evidence_tags (tag_id, creator_id, category, status, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(tag_id) DO UPDATE SET
                creator_id = excluded.creator_id,
                category = excluded.category,
                status = excluded.status,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (tag.tag_id, tag.creator_id, tag.category, tag.status, tag.to_json()),
        )


def load_evidence_tags(path: Path, creator_id: str = "") -> list[KolEvidenceTag]:
    if postgres_enabled():
        where = "creator_id = %s" if creator_id else ""
        params = (creator_id,) if creator_id else ()
        return [KolEvidenceTag.from_json(payload) for payload in fetch_payloads(path, "kol_evidence_tags", where=where, params=params)]
    init_kol_intelligence_db(path)
    with sqlite3.connect(path) as conn:
        if creator_id:
            rows = conn.execute(
                "SELECT payload FROM kol_evidence_tags WHERE creator_id = ? ORDER BY updated_at DESC",
                (creator_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT payload FROM kol_evidence_tags ORDER BY updated_at DESC").fetchall()
    return [KolEvidenceTag.from_json(row[0]) for row in rows]


def delete_evidence_tags_for_creator(path: Path, creator_id: str) -> None:
    if postgres_enabled():
        from src.storage.postgres_payload import delete_by_column

        delete_by_column(path, "kol_evidence_tags", "creator_id", creator_id)
        return
    init_kol_intelligence_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM kol_evidence_tags WHERE creator_id = ?", (creator_id,))


def load_evidence_tag(path: Path, tag_id: str) -> KolEvidenceTag | None:
    if postgres_enabled():
        payload = fetch_payload(path, "kol_evidence_tags", "tag_id", tag_id)
        return KolEvidenceTag.from_json(payload) if payload else None
    init_kol_intelligence_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM kol_evidence_tags WHERE tag_id = ?", (tag_id,)).fetchone()
    return KolEvidenceTag.from_json(row[0]) if row else None


def upsert_graph_snapshot(path: Path, snapshot: KolGraphSnapshot) -> None:
    if postgres_enabled():
        upsert_payload(path, "kol_graph_snapshots", "snapshot_id", snapshot.snapshot_id, snapshot.to_json())
        return
    init_kol_intelligence_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO kol_graph_snapshots (snapshot_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(snapshot_id) DO UPDATE SET payload = excluded.payload, updated_at = CURRENT_TIMESTAMP
            """,
            (snapshot.snapshot_id, snapshot.to_json()),
        )


def load_graph_snapshots(path: Path) -> list[KolGraphSnapshot]:
    if postgres_enabled():
        return [KolGraphSnapshot.from_json(payload) for payload in fetch_payloads(path, "kol_graph_snapshots")]
    init_kol_intelligence_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM kol_graph_snapshots ORDER BY updated_at DESC").fetchall()
    return [KolGraphSnapshot.from_json(row[0]) for row in rows]


def upsert_prediction(path: Path, prediction: KolPrediction) -> None:
    if postgres_enabled():
        upsert_payload(path, "kol_predictions", "prediction_id", prediction.prediction_id, prediction.to_json())
        return
    init_kol_intelligence_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO kol_predictions (prediction_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(prediction_id) DO UPDATE SET payload = excluded.payload, updated_at = CURRENT_TIMESTAMP
            """,
            (prediction.prediction_id, prediction.to_json()),
        )


def load_predictions(path: Path) -> list[KolPrediction]:
    if postgres_enabled():
        return [KolPrediction.from_json(payload) for payload in fetch_payloads(path, "kol_predictions")]
    init_kol_intelligence_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM kol_predictions ORDER BY updated_at DESC").fetchall()
    return [KolPrediction.from_json(row[0]) for row in rows]
