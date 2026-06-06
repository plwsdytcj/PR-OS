from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.platform_os.service import add_post_campaign_review, create_campaign_project
from src.storage.db import init_db, save_profile
from src.symbolic.creator_profiler import generate_creator_symbolic_profile
from src.symbolic.os_service import generate_social_symbolic_report, symbolic_os_snapshot
from src.symbolic.os_storage import init_symbolic_os_db, load_all_feedback_corrections
from src.symbolic.storage import init_symbolic_db, load_creator_symbolic, upsert_creator_symbolic
from src.schemas import CreatorProfile, stable_id


DB_PATH = ROOT / "data" / "processed" / "smoke_symbolic_os.sqlite3"


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db(DB_PATH)
    init_symbolic_db(DB_PATH)
    init_symbolic_os_db(DB_PATH)

    creator = CreatorProfile(
        creator_id=stable_id("symbolic os creator", prefix="creator"),
        name="城市生活方式博主",
        platform="小红书",
        follower_count=90000,
        listed_price=12000,
        bio="关注新能源车、城市通勤、家庭出行和真实体验。",
        industry_fit_tags=["汽车", "生活方式"],
        content_capability_tags=["真实测评", "场景种草"],
        suitable_goals=["新品预热", "口碑种草"],
        risk_tags=["硬广感"],
        ai_summary="适合新能源车真实体验和城市生活方式内容。",
    )
    save_profile(DB_PATH, creator)
    upsert_creator_symbolic(DB_PATH, generate_creator_symbolic_profile(creator))

    report = generate_social_symbolic_report(
        DB_PATH,
        {
            "period": "本周",
            "raw_input": "AI工具爆发，消费降级讨论持续升温。新能源车用户关注城市通勤、家庭安全、智驾体验和价格争议。",
        },
    )
    assert report.issues
    assert report.borrowable_directions

    project = create_campaign_project(
        DB_PATH,
        client_name="Symbolic OS 客户",
        project_name="新能源车上市",
        raw_brief="预算20万，新能源SUV新品预热，目标是一二线城市家庭用户，突出城市自由、真实感和安全感。",
    )
    add_post_campaign_review(
        DB_PATH,
        project.campaign.campaign_id,
        {
            "creator_id": creator.creator_id,
            "content_url": "https://example.com/post",
            "views": 50000,
            "likes": 3200,
            "comments": 260,
            "delivery_rating": 4.5,
            "brand_feedback": "客户认可真实感和城市自由表达，但评论区出现价格争议。",
            "comment_feedback": "用户觉得专业可信，也有人觉得有一点硬广。",
        },
    )
    corrections = load_all_feedback_corrections(DB_PATH)
    assert corrections
    assert corrections[0].activated_tags
    updated_symbolic = load_creator_symbolic(DB_PATH, creator.creator_id)
    assert updated_symbolic is not None
    assert updated_symbolic.manual_status == "post_review_adjusted"
    snapshot = symbolic_os_snapshot(DB_PATH)
    assert snapshot["metrics"]["social_reports"] >= 1
    assert snapshot["metrics"]["signifier_tags"] >= 5
    assert snapshot["metrics"]["feedback_corrections"] >= 1
    print(
        "OK symbolic_os "
        f"reports={snapshot['metrics']['social_reports']} "
        f"tags={snapshot['metrics']['signifier_tags']} "
        f"corrections={snapshot['metrics']['feedback_corrections']}"
    )


if __name__ == "__main__":
    main()
