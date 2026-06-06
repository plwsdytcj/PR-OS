from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.creator_commercial.service import create_creator_invitation, create_creator_submission, review_creator_submission
from src.creator_commercial.storage import init_creator_commercial_db, load_commercial_profile
from src.intelligence.profiling import enrich_profiles
from src.schemas import CreatorProfile, stable_id
from src.storage.db import init_db, load_profile, save_profile

DB_PATH = ROOT / "data" / "processed" / "smoke_phase3.sqlite3"


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db(DB_PATH)
    init_creator_commercial_db(DB_PATH)
    creator = enrich_profiles(
        [
            CreatorProfile(
                creator_id=stable_id("phase3 creator"),
                name="Phase3 商业博主",
                platform="小红书",
                follower_count=120000,
                listed_price=18000,
                bio="生活方式与新品体验",
            )
        ]
    )[0]
    save_profile(DB_PATH, creator)
    invitation = create_creator_invitation(DB_PATH, creator)
    submission = create_creator_submission(
        DB_PATH,
        invitation,
        {
            "profile_fields": {
                "price_range": "2万-3万",
                "availability": "6月可排 3 条",
                "industry_fit_tags": "美妆,生活方式",
                "content_capability_tags": "图文种草,短视频",
                "suitable_goals": "新品预热,种草",
                "cooperation_preferences": "真实体验,长期合作",
            },
            "cases": [
                {
                    "brand_name": "某护肤品牌",
                    "industry": "美妆",
                    "content_format": "图文种草",
                    "cooperation_goal": "新品预热",
                    "views": "18w",
                }
            ],
        },
    )
    reviewed, commercial, updated = review_creator_submission(DB_PATH, creator, submission)
    stored = load_commercial_profile(DB_PATH, creator.creator_id)
    reloaded = load_profile(DB_PATH, creator.creator_id)
    assert reviewed.status == "approved"
    assert commercial is not None and stored is not None
    assert updated is not None and reloaded is not None
    assert "美妆" in reloaded.industry_fit_tags
    print(f"OK invitation={invitation.invitation_id} submission={submission.submission_id} confidence={stored.profile_confidence}")


if __name__ == "__main__":
    main()
