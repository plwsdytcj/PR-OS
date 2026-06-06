from __future__ import annotations

import sqlite3
from pathlib import Path

from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload
from src.symbolic.os_schemas import BrandCreatorMatchAsset, ContentNarrativeAsset, FeedbackCorrection, ProductSymbolicProfile, SignifierTag, SocialSymbolicReport


def init_symbolic_os_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS social_symbolic_reports (
                report_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS signifier_tags (
                tag_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_symbolic_profiles (
                product_id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS content_narrative_assets (
                narrative_id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS brand_creator_match_assets (
                match_id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback_corrections (
                correction_id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_social_report(path: Path, report: SocialSymbolicReport) -> None:
    if postgres_enabled():
        upsert_payload(path, "social_symbolic_reports", "report_id", report.report_id, report.to_json())
        return
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO social_symbolic_reports (report_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(report_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (report.report_id, report.to_json()),
        )


def load_social_report(path: Path, report_id: str) -> SocialSymbolicReport | None:
    if postgres_enabled():
        payload = fetch_payload(path, "social_symbolic_reports", "report_id", report_id)
        return SocialSymbolicReport.from_json(payload) if payload else None
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM social_symbolic_reports WHERE report_id = ?", (report_id,)).fetchone()
    return SocialSymbolicReport.from_json(row[0]) if row else None


def load_all_social_reports(path: Path) -> list[SocialSymbolicReport]:
    if postgres_enabled():
        return [SocialSymbolicReport.from_json(payload) for payload in fetch_payloads(path, "social_symbolic_reports")]
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM social_symbolic_reports ORDER BY updated_at DESC").fetchall()
    return [SocialSymbolicReport.from_json(row[0]) for row in rows]


def upsert_signifier_tag(path: Path, tag: SignifierTag) -> None:
    if postgres_enabled():
        upsert_payload(path, "signifier_tags", "tag_id", tag.tag_id, tag.to_json())
        return
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO signifier_tags (tag_id, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(tag_id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (tag.tag_id, tag.to_json()),
        )


def load_signifier_tag(path: Path, tag_id: str) -> SignifierTag | None:
    if postgres_enabled():
        payload = fetch_payload(path, "signifier_tags", "tag_id", tag_id)
        return SignifierTag.from_json(payload) if payload else None
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM signifier_tags WHERE tag_id = ?", (tag_id,)).fetchone()
    return SignifierTag.from_json(row[0]) if row else None


def load_all_signifier_tags(path: Path) -> list[SignifierTag]:
    if postgres_enabled():
        return [SignifierTag.from_json(payload) for payload in fetch_payloads(path, "signifier_tags")]
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM signifier_tags ORDER BY updated_at DESC").fetchall()
    return [SignifierTag.from_json(row[0]) for row in rows]


def upsert_product_symbolic(path: Path, profile: ProductSymbolicProfile) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "product_symbolic_profiles",
            "product_id",
            profile.product_id,
            profile.to_json(),
            extra={"brand_id": profile.brand_id},
        )
        return
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO product_symbolic_profiles (product_id, brand_id, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(product_id) DO UPDATE SET
                brand_id = excluded.brand_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (profile.product_id, profile.brand_id, profile.to_json()),
        )


def load_product_symbolic(path: Path, product_id: str) -> ProductSymbolicProfile | None:
    if postgres_enabled():
        payload = fetch_payload(path, "product_symbolic_profiles", "product_id", product_id)
        return ProductSymbolicProfile.from_json(payload) if payload else None
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM product_symbolic_profiles WHERE product_id = ?", (product_id,)).fetchone()
    return ProductSymbolicProfile.from_json(row[0]) if row else None


def load_all_product_symbolic(path: Path) -> list[ProductSymbolicProfile]:
    if postgres_enabled():
        return [ProductSymbolicProfile.from_json(payload) for payload in fetch_payloads(path, "product_symbolic_profiles")]
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM product_symbolic_profiles ORDER BY updated_at DESC").fetchall()
    return [ProductSymbolicProfile.from_json(row[0]) for row in rows]


def upsert_content_narrative(path: Path, asset: ContentNarrativeAsset) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "content_narrative_assets",
            "narrative_id",
            asset.narrative_id,
            asset.to_json(),
            extra={"brand_id": asset.brand_id, "creator_id": asset.creator_id},
        )
        return
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO content_narrative_assets (narrative_id, brand_id, creator_id, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(narrative_id) DO UPDATE SET
                brand_id = excluded.brand_id,
                creator_id = excluded.creator_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (asset.narrative_id, asset.brand_id, asset.creator_id, asset.to_json()),
        )


def load_content_narrative(path: Path, narrative_id: str) -> ContentNarrativeAsset | None:
    if postgres_enabled():
        payload = fetch_payload(path, "content_narrative_assets", "narrative_id", narrative_id)
        return ContentNarrativeAsset.from_json(payload) if payload else None
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM content_narrative_assets WHERE narrative_id = ?", (narrative_id,)).fetchone()
    return ContentNarrativeAsset.from_json(row[0]) if row else None


def load_all_content_narratives(path: Path) -> list[ContentNarrativeAsset]:
    if postgres_enabled():
        return [ContentNarrativeAsset.from_json(payload) for payload in fetch_payloads(path, "content_narrative_assets")]
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM content_narrative_assets ORDER BY updated_at DESC").fetchall()
    return [ContentNarrativeAsset.from_json(row[0]) for row in rows]


def upsert_brand_creator_match(path: Path, asset: BrandCreatorMatchAsset) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "brand_creator_match_assets",
            "match_id",
            asset.match_id,
            asset.to_json(),
            extra={"brand_id": asset.brand_id, "creator_id": asset.creator_id},
        )
        return
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO brand_creator_match_assets (match_id, brand_id, creator_id, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(match_id) DO UPDATE SET
                brand_id = excluded.brand_id,
                creator_id = excluded.creator_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (asset.match_id, asset.brand_id, asset.creator_id, asset.to_json()),
        )


def load_brand_creator_match(path: Path, match_id: str) -> BrandCreatorMatchAsset | None:
    if postgres_enabled():
        payload = fetch_payload(path, "brand_creator_match_assets", "match_id", match_id)
        return BrandCreatorMatchAsset.from_json(payload) if payload else None
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM brand_creator_match_assets WHERE match_id = ?", (match_id,)).fetchone()
    return BrandCreatorMatchAsset.from_json(row[0]) if row else None


def load_all_brand_creator_matches(path: Path) -> list[BrandCreatorMatchAsset]:
    if postgres_enabled():
        return [BrandCreatorMatchAsset.from_json(payload) for payload in fetch_payloads(path, "brand_creator_match_assets")]
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM brand_creator_match_assets ORDER BY updated_at DESC").fetchall()
    return [BrandCreatorMatchAsset.from_json(row[0]) for row in rows]


def upsert_feedback_correction(path: Path, correction: FeedbackCorrection) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "feedback_corrections",
            "correction_id",
            correction.correction_id,
            correction.to_json(),
            extra={"campaign_id": correction.campaign_id, "creator_id": correction.creator_id},
        )
        return
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO feedback_corrections (correction_id, campaign_id, creator_id, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(correction_id) DO UPDATE SET
                campaign_id = excluded.campaign_id,
                creator_id = excluded.creator_id,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (correction.correction_id, correction.campaign_id, correction.creator_id, correction.to_json()),
        )


def load_all_feedback_corrections(path: Path) -> list[FeedbackCorrection]:
    if postgres_enabled():
        return [FeedbackCorrection.from_json(payload) for payload in fetch_payloads(path, "feedback_corrections")]
    init_symbolic_os_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM feedback_corrections ORDER BY updated_at DESC").fetchall()
    return [FeedbackCorrection.from_json(row[0]) for row in rows]
