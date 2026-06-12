from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.intelligence.brief_parser import parse_brief
from src.platform_os.service import campaign_room, create_campaign_project, run_campaign_plan_simulation
from src.schemas import stable_id
from src.simulation.llm_fallback import LlmFallbackStressTest
from src.simulation.mirofish_adapter import MiroFishCliAdapter
from src.simulation.schemas import SimulationReport
from src.storage.db import load_profiles
from src.symbolic.brand_profiler import generate_brand_symbolic_profile
from src.symbolic.creator_profiler import generate_creator_symbolic_profile
from src.symbolic.narrative_path import generate_narrative_path
from src.symbolic.os_service import (
    calibrate_brand_with_symbolic_context,
    create_brand_creator_match_assets,
    create_content_narrative_assets,
    generate_product_symbolic_profile,
    generate_social_symbolic_report,
)
from src.symbolic.os_storage import load_all_social_reports
from src.symbolic.storage import load_all_creator_symbolic, load_creator_symbolic, upsert_brand_symbolic, upsert_creator_symbolic
from src.symbolic.symbolic_matching import rank_symbolic_creators


def run_pr_project(
    db_path: Path,
    client_name: str,
    project_name: str,
    raw_brief: str,
    top_n: int = 8,
    simulation_engine: str = "auto",
) -> dict[str, Any]:
    raw_brief = raw_brief.strip()
    if not raw_brief:
        raise ValueError("brief is required")
    creators = load_profiles(db_path)
    if not creators:
        raise ValueError("creator profiles are required before running a PR project")

    brief = parse_brief(raw_brief)
    run_id = stable_id(client_name, project_name, raw_brief, prefix="run")
    steps: list[dict[str, Any]] = []

    def step(step_id: str, label: str, status: str = "done", detail: str = "", count: int = 0) -> None:
        steps.append({"id": step_id, "label": label, "status": status, "detail": detail, "count": count})

    step("brief", "解析 PR Brief", detail=f"{brief.industry or '未知行业'} / {brief.product or project_name}")

    social_report = generate_social_symbolic_report(
        db_path,
        {
            "period": project_name,
            "raw_input": raw_brief,
        },
    )
    step("social", "生成社会符号语境", detail=social_report.title, count=len(social_report.issues))

    brand = generate_brand_symbolic_profile(
        {
            "brand_name": client_name,
            "product": brief.product or project_name,
            "industry": brief.industry,
            "brief": raw_brief,
            "goals": brief.goals,
            "target_audience": brief.target_audience,
            "platforms": brief.platform_preference,
            "content_preferences": brief.content_preference,
        }
    )
    brand, calibration = calibrate_brand_with_symbolic_context(db_path, brand, report_id=social_report.report_id)
    upsert_brand_symbolic(db_path, brand)
    step("brand", "生成并校准品牌符号档案", detail=calibration.get("message", ""), count=len(brand.target_tags))

    product = generate_product_symbolic_profile(
        db_path,
        {
            "brand_id": brand.brand_id,
            "brand_name": brand.brand_name,
            "product_name": brand.product or brief.product or project_name,
            "category": brand.industry or brief.industry,
            "use_scenarios": brief.content_preference,
            "target_users": brief.target_audience,
            "functional_value": raw_brief,
            "suitable_creator_types": brand.suitable_creator_types,
        },
    )
    step("product", "生成产品符号档案", detail=product.product_name, count=len(product.metaphors))

    creator_symbolics = _ensure_creator_symbolics(db_path)
    step("creators", "补齐达人符号档案", detail=f"{len(creators)} 个达人进入候选池", count=len(creator_symbolics))

    results = rank_symbolic_creators(brand, creator_symbolics)[: max(1, top_n)]
    result_dicts = [item.to_dict() for item in results]
    match_assets = create_brand_creator_match_assets(
        db_path,
        {
            "brand": brand.to_dict(),
            "product": product.to_dict(),
            "results": result_dicts,
        },
    )
    step("match", "完成 KOL 符号匹配与选择", detail=f"Top {len(result_dicts)} 推荐名单", count=len(result_dicts))

    narratives = []
    for result in results[: min(3, len(results))]:
        creator_symbolic = load_creator_symbolic(db_path, result.creator_id)
        if creator_symbolic is None:
            continue
        narratives.append(generate_narrative_path(brand, creator_symbolic, project_name).to_dict())
    narrative_assets = create_content_narrative_assets(
        db_path,
        {
            "project": project_name,
            "brand": brand.to_dict(),
            "product": product.to_dict(),
            "narratives": narratives,
        },
    )
    step("narrative", "生成内容叙事资产", detail="为首选 KOL 生成内容路径", count=len(narratives))

    simulation_payload = {
        "client_name": client_name,
        "project_name": project_name,
        "raw_brief": raw_brief,
        "brief": asdict(brief),
        "social_report": social_report.to_dict(),
        "brand": brand.to_dict(),
        "product": product.to_dict(),
        "matches": result_dicts,
        "narratives": narratives,
    }
    simulation_report = _run_stress_test(simulation_payload, simulation_engine=simulation_engine)
    step("simulation", "完成投放前压力测试", detail=simulation_report.summary, count=len(simulation_report.nodes))

    campaign = create_campaign_project(
        db_path,
        client_name=client_name,
        project_name=project_name,
        raw_brief=raw_brief,
        top_n=top_n,
    )
    if campaign.plans:
        campaign = run_campaign_plan_simulation(db_path, campaign.campaign.campaign_id, campaign.plans[0].plan_id)
    room = campaign_room(db_path, campaign.campaign.campaign_id)
    step("campaign", "创建 Campaign Room", detail=campaign.campaign.status, count=len(room.get("plans", [])))

    return {
        "run_id": run_id,
        "status": "completed",
        "steps": steps,
        "brief": asdict(brief),
        "brand": brand.to_dict(),
        "product": product.to_dict(),
        "social_report": social_report.to_dict(),
        "social_reports_count": len(load_all_social_reports(db_path)),
        "calibration": calibration,
        "matches": result_dicts,
        "match_assets": [item.to_dict() for item in match_assets],
        "narratives": narratives,
        "narrative_assets": [item.to_dict() for item in narrative_assets],
        "simulation_report": simulation_report.to_dict(),
        "campaign": campaign.to_dict(),
        "campaign_room": room,
    }


def _run_stress_test(payload: dict[str, Any], simulation_engine: str = "auto") -> SimulationReport:
    engine = (simulation_engine or "auto").strip().lower()
    if engine in {"auto", "mirofish", "mirofish_cli"}:
        adapter = MiroFishCliAdapter()
        if adapter.available():
            try:
                return adapter.run(payload)
            except Exception as exc:
                if engine in {"mirofish", "mirofish_cli"}:
                    raise RuntimeError(f"MiroFish CLI failed: {exc}") from exc
                report = LlmFallbackStressTest().run(payload)
                report.engine = "llm_fallback_after_mirofish_error"
                report.engine_status = f"mirofish_error:{type(exc).__name__}"
                return report
        if engine in {"mirofish", "mirofish_cli"}:
            raise RuntimeError("MiroFish CLI is not installed or not on PATH")
        report = LlmFallbackStressTest().run(payload)
        report.engine = "llm_fallback_after_mirofish_unavailable"
        report.engine_status = "mirofish_unavailable"
        return report
    return LlmFallbackStressTest().run(payload)


def _ensure_creator_symbolics(db_path: Path) -> list[Any]:
    creator_symbolics = load_all_creator_symbolic(db_path)
    existing_ids = {item.creator_id for item in creator_symbolics}
    for creator in load_profiles(db_path):
        if creator.creator_id in existing_ids:
            continue
        symbolic = generate_creator_symbolic_profile(creator)
        upsert_creator_symbolic(db_path, symbolic)
        creator_symbolics.append(symbolic)
        existing_ids.add(symbolic.creator_id)
    return creator_symbolics
