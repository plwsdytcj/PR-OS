from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.brief_distribution.service import (
    create_distribution_brief,
    distribution_summary,
    push_distribution_brief,
    submit_creator_response,
)
from src.brief_distribution.storage import init_distribution_db, load_responses_for_brief
from src.intelligence.profiling import enrich_profiles
from src.schemas import CreatorProfile, stable_id
from src.storage.db import init_db, save_profile

DB_PATH = ROOT / "data" / "processed" / "smoke_phase4.sqlite3"


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db(DB_PATH)
    init_distribution_db(DB_PATH)
    creators = enrich_profiles(
        [
            CreatorProfile(
                creator_id=stable_id("phase4 creator 1"),
                name="新能源测评老王",
                platform="抖音",
                follower_count=300000,
                listed_price=50000,
                bio="汽车科技测评",
            ),
            CreatorProfile(
                creator_id=stable_id("phase4 creator 2"),
                name="城市生活方式",
                platform="小红书",
                follower_count=160000,
                listed_price=25000,
                bio="城市生活与家庭消费",
            ),
        ]
    )
    for creator in creators:
        save_profile(DB_PATH, creator)
    brief = create_distribution_brief(
        DB_PATH,
        client_name="某新能源汽车品牌",
        project_name="SUV 新品预热",
        raw_brief="预算50万，新能源SUV新品上市预热，突出科技感、智能化，平台优先抖音、小红书。",
        creators=creators,
        top_n=2,
    )
    pushed = push_distribution_brief(DB_PATH, brief)
    recipient = pushed.recipients[0]
    response = submit_creator_response(
        DB_PATH,
        pushed,
        recipient.recipient_id,
        {
            "interest": "interested",
            "quote": 48000,
            "availability": "6月下旬",
            "content_direction": "智能座舱体验测评",
        },
    )
    summary = distribution_summary(pushed, load_responses_for_brief(DB_PATH, brief.brief_id))
    assert pushed.status == "pushed"
    assert response.interest == "interested"
    assert summary["counts"]["interested"] == 1
    print(f"OK brief={brief.brief_id} recipients={len(brief.recipients)} responses={summary['counts']['responded']}")


if __name__ == "__main__":
    main()
