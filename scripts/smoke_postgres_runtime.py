from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.intelligence.profiling import enrich_profiles
from src.platform_os.service import campaign_room, create_campaign_project, run_campaign_plan_simulation
from src.platform_os.storage import load_all_campaign_projects
from src.schemas import CreatorProfile, stable_id
from src.storage.db import count_profiles, load_profiles, save_profile
from src.symbolic.creator_profiler import generate_creator_symbolic_profile
from src.symbolic.storage import load_all_creator_symbolic, upsert_creator_symbolic


def main() -> None:
    if not os.getenv("DATABASE_URL"):
        print("SKIP postgres runtime smoke: DATABASE_URL is not set")
        return
    tenant_path = ROOT / "data" / "processed" / "tenants" / "pg-runtime-smoke" / "phase1_web.sqlite3"
    creator = enrich_profiles(
        [
            CreatorProfile(
                creator_id=stable_id("pg-runtime-smoke-creator"),
                name="Postgres 运行时达人",
                platform="小红书",
                follower_count=88000,
                listed_price=18000,
                bio="新能源车、城市通勤、家庭出行",
            )
        ]
    )[0]
    save_profile(tenant_path, creator)
    total, enriched = count_profiles(tenant_path)
    assert total >= 1
    assert enriched >= 1
    assert any(item.creator_id == creator.creator_id for item in load_profiles(tenant_path))

    symbolic = generate_creator_symbolic_profile(creator)
    upsert_creator_symbolic(tenant_path, symbolic)
    assert any(item.creator_id == creator.creator_id for item in load_all_creator_symbolic(tenant_path))

    project = create_campaign_project(
        tenant_path,
        client_name="Postgres 客户",
        project_name="Postgres Runtime 战役",
        raw_brief="预算20万，新能源SUV预热，平台优先小红书，需要投放前风险推演。",
    )
    run_campaign_plan_simulation(tenant_path, project.campaign.campaign_id, project.plans[0].plan_id)
    room = campaign_room(tenant_path, project.campaign.campaign_id)
    assert room["plans"][0]["simulation"]["simulation_report"]["nodes"]
    assert any(item.campaign.project_name == "Postgres Runtime 战役" for item in load_all_campaign_projects(tenant_path))
    print(f"OK postgres runtime tenant=pg-runtime-smoke profiles={total} campaign={project.campaign.campaign_id}")


if __name__ == "__main__":
    main()
