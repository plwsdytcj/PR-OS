#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.creator_commercial.schemas import CreatorCase, case_id_for, now_iso
from src.creator_commercial.storage import upsert_case
from src.intelligence.profiling import enrich_profiles
from src.normalize.mapper import map_dataframe_to_profiles
from src.schemas import CreatorProfile, split_tags
from src.storage.db import init_db, load_profiles, replace_profiles, save_profile

import pandas as pd

DB = ROOT / "data" / "processed" / "phase1_web.sqlite3"
CREATORS_CSV = ROOT / "data" / "raw" / "seed_creators.csv"
CASES_CSV = ROOT / "data" / "raw" / "seed_cases.csv"


def seed_creators() -> int:
    init_db(DB)
    df = pd.read_csv(CREATORS_CSV)
    profiles = enrich_profiles(map_dataframe_to_profiles(df, source="seed_creators"))
    replace_profiles(DB, profiles)
    return len(profiles)


def _creator_lookup() -> dict[str, object]:
    return {profile.name: profile for profile in load_profiles(DB)}


def seed_cases() -> int:
    lookup = _creator_lookup()
    count = 0
    with CASES_CSV.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            creator = lookup.get(str(row.get("达人名称") or "").strip())
            if creator is None:
                continue
            brand = str(row.get("合作品牌") or "").strip()
            if not brand:
                continue
            case = CreatorCase(
                case_id=case_id_for(creator.creator_id, brand),
                creator_id=creator.creator_id,
                creator_name=creator.name,
                brand_name=brand,
                industry=str(row.get("行业") or ""),
                product=str(row.get("产品") or ""),
                platform=creator.platform,
                content_format=str(row.get("合作形式") or ""),
                content_topic=str(row.get("内容主题") or ""),
                cooperation_goal=str(row.get("传播目标") or ""),
                active_tags=split_tags(row.get("传播目标")),
                is_successful=str(row.get("是否成功") or ""),
                reuse_suggestion=str(row.get("复用建议") or ""),
                comment_feedback=str(row.get("媒介备注") or ""),
                verification_status="approved",
                updated_at=now_iso(),
            )
            upsert_case(DB, case)
            brands = list(creator.cooperation_brands or [])
            if brand not in brands:
                from dataclasses import asdict

                data = asdict(creator)
                data["cooperation_brands"] = brands + [brand]
                save_profile(DB, CreatorProfile(**data))
                lookup[creator.name] = CreatorProfile(**data)
            count += 1
    return count


def main() -> None:
    creators = seed_creators()
    cases = seed_cases()
    print(f"seeded creators={creators} cases={cases} db={DB}")


if __name__ == "__main__":
    main()
