from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.brief_distribution.storage import init_distribution_db
from src.collaboration.storage import init_collaboration_db
from src.creator_commercial.storage import init_creator_commercial_db
from src.intelligence.profiling import enrich_profiles
from src.platform_os.service import (
    add_post_campaign_review,
    campaign_room,
    create_campaign_project,
    create_distribution_from_campaign,
    platform_dashboard,
    run_campaign_plan_simulation,
)
from src.platform_os.storage import init_platform_db
from src.schemas import CreatorProfile, stable_id
from src.storage.db import init_db, load_profile, save_profile

DB_PATH = ROOT / "data" / "processed" / "smoke_phase5.sqlite3"


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db(DB_PATH)
    init_collaboration_db(DB_PATH)
    init_creator_commercial_db(DB_PATH)
    init_distribution_db(DB_PATH)
    init_platform_db(DB_PATH)
    creators = enrich_profiles(
        [
            CreatorProfile(
                creator_id=stable_id("phase5 creator 1"),
                name="汽车科技测评",
                platform="抖音",
                follower_count=350000,
                listed_price=50000,
                bio="新能源车和智能座舱测评",
            ),
            CreatorProfile(
                creator_id=stable_id("phase5 creator 2"),
                name="小红书通勤生活",
                platform="小红书",
                follower_count=180000,
                listed_price=26000,
                bio="城市通勤和家庭生活方式",
            ),
            CreatorProfile(
                creator_id=stable_id("phase5 creator 3"),
                name="B站硬核车评",
                platform="B站",
                follower_count=220000,
                listed_price=42000,
                bio="汽车技术拆解",
            ),
        ]
    )
    for creator in creators:
        save_profile(DB_PATH, creator)
    project = create_campaign_project(
        DB_PATH,
        client_name="某新能源汽车品牌",
        project_name="Phase5 SUV 发布",
        raw_brief="预算50万，新能源SUV新品上市预热，突出科技感、智能化，平台优先抖音、小红书、B站。",
    )
    assert len(project.plans) == 3
    assert len(project.simulations) == 3
    distribution = create_distribution_from_campaign(DB_PATH, project.campaign.campaign_id)
    assert distribution["distribution"]["recipients"]
    simulated = run_campaign_plan_simulation(DB_PATH, project.campaign.campaign_id, project.plans[0].plan_id)
    deep = next(item for item in simulated.simulations if item.plan_id == project.plans[0].plan_id)
    assert deep.simulation_report["nodes"]
    assert deep.simulation_report["timeline"]
    assert deep.simulation_report["agent_reactions"]
    reviewed = add_post_campaign_review(
        DB_PATH,
        project.campaign.campaign_id,
        {
            "creator_id": creators[0].creator_id,
            "content_url": "https://example.com/post",
            "actual_price": 48000,
            "views": 600000,
            "likes": 24000,
            "comments": 3200,
            "brand_feedback": "内容质量高，评论区讨论积极",
            "delivery_rating": 4.5,
        },
    )
    updated_creator = load_profile(DB_PATH, creators[0].creator_id)
    assert reviewed.reviews
    assert updated_creator is not None and "post_campaign_review" in updated_creator.data_sources
    dashboard = platform_dashboard(DB_PATH)
    assert dashboard["engine_status"]["phase_5"] == "ready"
    assert dashboard["metrics"]["campaign_projects"] == 1
    assert dashboard["metrics"]["post_reviews"] == 1
    assert len(dashboard["lifecycle"]) >= 6
    room = campaign_room(DB_PATH, project.campaign.campaign_id)
    assert room["decision_summary"]["recommended_plan"]
    assert room["plans"]
    assert room["creators"]
    assert room["distribution_briefs"]
    assert room["reviews"]
    assert room["next_actions"]
    print(f"OK phase5 metrics={len(dashboard['metrics'])} lifecycle={len(dashboard['lifecycle'])} room_plans={len(room['plans'])}")


if __name__ == "__main__":
    main()
