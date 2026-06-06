from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.brief_distribution.service import create_distribution_brief
from src.brief_distribution.storage import load_all_distribution_briefs, load_responses_for_brief
from src.collaboration.storage import load_all_proposals, load_feedback, load_versions
from src.creator_commercial.storage import load_all_commercial_profiles, load_all_invitations, load_all_submissions
from src.intelligence.brief_parser import parse_brief
from src.intelligence.matching import rank_creators
from src.platform_os.schemas import (
    CampaignPlan,
    CampaignProfile,
    CampaignProject,
    CampaignSimulation,
    PostCampaignReview,
    campaign_id_for,
    plan_id_for,
    review_id_for,
    simulation_id_for,
)
from src.platform_os.storage import load_all_campaign_projects, upsert_campaign_project
from src.schemas import CreatorProfile
from src.simulation.llm_fallback import LlmFallbackStressTest
from src.storage.db import count_profiles, load_profiles
from src.storage.db import load_profile, save_profile


def platform_dashboard(db_path: Path) -> dict[str, Any]:
    total_profiles, enriched_profiles = count_profiles(db_path)
    proposals = load_all_proposals(db_path)
    invitations = load_all_invitations(db_path)
    submissions = load_all_submissions(db_path)
    commercial_profiles = load_all_commercial_profiles(db_path)
    distributions = load_all_distribution_briefs(db_path)
    campaigns = load_all_campaign_projects(db_path)
    response_count = sum(len(load_responses_for_brief(db_path, item.brief_id)) for item in distributions)
    review_count = sum(len(item.reviews) for item in campaigns)
    finalized = sum(1 for item in proposals if item.status == "已确认")
    dashboard = {
        "metrics": {
            "creators": total_profiles,
            "enriched_creators": enriched_profiles,
            "commercial_profiles": len(commercial_profiles),
            "client_proposals": len(proposals),
            "finalized_proposals": finalized,
            "creator_invitations": len(invitations),
            "creator_submissions": len(submissions),
            "distribution_briefs": len(distributions),
            "creator_responses": response_count,
            "campaign_projects": len(campaigns),
            "post_reviews": review_count,
        },
        "lifecycle": [
            _step("数据接入", total_profiles, "done" if total_profiles else "waiting"),
            _step("AI 商业画像", enriched_profiles, "done" if enriched_profiles else "waiting"),
            _step("符号图谱/压力测试", len(commercial_profiles), "active" if commercial_profiles else "waiting"),
            _step("客户方案协作", len(proposals), "active" if proposals else "waiting"),
            _step("博主商业档案", len(submissions), "active" if submissions else "waiting"),
            _step("Brief 分发响应", response_count, "active" if response_count else "waiting"),
            _step("投后案例回流", review_count, "active" if review_count else "waiting"),
            _step("偏好与案例沉淀", finalized + len(commercial_profiles) + review_count, "active" if finalized or commercial_profiles or review_count else "waiting"),
        ],
        "recent": {
            "proposals": [
                asdict(item)
                | {
                    "versions": len(load_versions(db_path, item.proposal_id)),
                    "feedback": len(load_feedback(db_path, item.proposal_id)),
                }
                for item in proposals[:6]
            ],
            "invitations": [asdict(item) for item in invitations[:6]],
            "distribution_briefs": [item.to_dict() for item in distributions[:6]],
            "campaign_projects": [item.to_dict() for item in campaigns[:6]],
        },
        "engine_status": {
            "phase_1": "ready",
            "phase_1_5": "ready",
            "phase_2": "ready",
            "phase_3": "ready" if commercial_profiles or submissions or invitations else "available",
            "phase_4": "ready" if distributions else "available",
            "phase_5": "ready",
        },
    }
    dashboard["next_actions"] = _next_actions(dashboard)
    return dashboard


def campaign_os_snapshot(db_path: Path, brief_text: str = "") -> dict[str, Any]:
    creators = load_profiles(db_path)
    dashboard = platform_dashboard(db_path)
    return {
        "dashboard": dashboard,
        "next_actions": _next_actions(dashboard),
        "creator_pool_sample": [
            {
                "creator_id": item.creator_id,
                "name": item.name,
                "platform": item.platform,
                "tags": (item.industry_fit_tags + item.content_capability_tags)[:6],
                "listed_price": item.listed_price,
            }
            for item in creators[:8]
        ],
        "brief_text": brief_text,
    }


def campaign_room(db_path: Path, campaign_id: str) -> dict[str, Any]:
    from src.platform_os.storage import load_campaign_project

    project = load_campaign_project(db_path, campaign_id)
    if project is None:
        raise KeyError("campaign not found")
    profiles = {profile.creator_id: profile for profile in load_profiles(db_path)}
    distributions = _related_distributions(db_path, project)
    selected_creator_ids = []
    for plan in project.plans:
        selected_creator_ids.extend(plan.creator_ids)
    creator_cards = [_creator_room_card(profiles[creator_id], project) for creator_id in dict.fromkeys(selected_creator_ids) if creator_id in profiles]
    plan_rooms = [_plan_room_card(project, plan, profiles) for plan in project.plans]
    room = {
        "project": project.to_dict(),
        "campaign": project.campaign.to_dict(),
        "plans": plan_rooms,
        "creators": creator_cards,
        "simulations": [item.to_dict() for item in project.simulations],
        "distribution_briefs": [item.to_dict() for item in distributions],
        "reviews": [item.to_dict() for item in project.reviews],
        "timeline": project.timeline,
        "decision_summary": _campaign_decision_summary(project, plan_rooms, distributions),
        "next_actions": _campaign_room_next_actions(project, distributions),
    }
    return room


def create_campaign_project(
    db_path: Path,
    client_name: str,
    project_name: str,
    raw_brief: str,
    top_n: int = 12,
) -> CampaignProject:
    brief = parse_brief(raw_brief)
    campaign = CampaignProfile(
        campaign_id=campaign_id_for(client_name, project_name),
        client_name=client_name,
        project_name=project_name,
        raw_brief=raw_brief,
        industry=brief.industry,
        product=brief.product,
        budget=brief.budget,
        stage=brief.campaign_stage,
        goals=brief.goals,
        target_audience=brief.target_audience,
        platforms=brief.platform_preference,
        content_preferences=brief.content_preference,
        risk_sensitivity="high" if "舆情" in raw_brief or "风险" in raw_brief else "medium",
    )
    creators = load_profiles(db_path)
    matches = rank_creators(brief, creators)[:top_n]
    plans = _generate_campaign_plans(campaign, matches)
    simulations = [_simulate_plan(campaign, plan) for plan in plans]
    project = CampaignProject(
        campaign=campaign,
        plans=plans,
        simulations=simulations,
        timeline=[
            _event("brief_created", "品牌 brief 已解析", {"budget": campaign.budget, "goals": campaign.goals}),
            _event("strategy_generated", "已生成 3 套传播方案", {"plans": [plan.plan_name for plan in plans]}),
            _event("stress_tested", "已完成投放前风险推演", {"disclaimer": simulations[0].disclaimer if simulations else ""}),
        ],
    )
    upsert_campaign_project(db_path, project)
    return project


def create_distribution_from_campaign(db_path: Path, campaign_id: str, plan_id: str = "") -> dict[str, Any]:
    from src.platform_os.storage import load_campaign_project

    project = load_campaign_project(db_path, campaign_id)
    if project is None:
        raise KeyError("campaign not found")
    plan = next((item for item in project.plans if item.plan_id == plan_id), None) or next((item for item in project.plans if item.is_recommended), None) or (project.plans[0] if project.plans else None)
    if plan is None:
        raise KeyError("plan not found")
    distribution = create_distribution_brief(
        db_path,
        client_name=project.campaign.client_name,
        project_name=f"{project.campaign.project_name}-{plan.plan_name}",
        raw_brief=project.campaign.raw_brief,
        creators=load_profiles(db_path),
        creator_ids=plan.creator_ids,
        top_n=len(plan.creator_ids),
        created_by="platform_os",
    )
    project.timeline.append(_event("brief_distribution_created", "已从 Campaign Plan 生成 Brief 分发", {"brief_id": distribution.brief_id, "plan_id": plan.plan_id}))
    upsert_campaign_project(db_path, project)
    return {"project": project.to_dict(), "distribution": distribution.to_dict()}


def run_campaign_plan_simulation(db_path: Path, campaign_id: str, plan_id: str = "") -> CampaignProject:
    from src.platform_os.storage import load_campaign_project

    project = load_campaign_project(db_path, campaign_id)
    if project is None:
        raise KeyError("campaign not found")
    plan = next((item for item in project.plans if item.plan_id == plan_id), None) or next((item for item in project.plans if item.is_recommended), None) or (project.plans[0] if project.plans else None)
    if plan is None:
        raise KeyError("plan not found")
    report = LlmFallbackStressTest().run(_simulation_payload_for_plan(db_path, project, plan))
    simulation = CampaignSimulation(
        simulation_id=simulation_id_for(plan.plan_id),
        campaign_id=campaign_id,
        plan_id=plan.plan_id,
        summary=report.summary,
        positive_reactions=report.positive_reactions,
        negative_reactions=report.negative_reactions,
        risk_points=report.risk_points,
        optimization_suggestions=report.optimization_suggestions,
        simulation_report=report.to_dict(),
        disclaimer=report.final_recommendation or "投放前推演仅用于辅助决策，不预测真实 ROI。",
    )
    project.simulations = [item for item in project.simulations if item.plan_id != plan.plan_id]
    project.simulations.append(simulation)
    project.timeline.append(_event("deep_simulation_created", "已生成 Campaign Room 深度推演", {"plan_id": plan.plan_id, "nodes": len(report.nodes), "timeline": len(report.timeline)}))
    project.campaign.status = "simulated"
    upsert_campaign_project(db_path, project)
    return project


def add_post_campaign_review(db_path: Path, campaign_id: str, payload: dict[str, Any]) -> CampaignProject:
    from src.platform_os.storage import load_campaign_project

    project = load_campaign_project(db_path, campaign_id)
    if project is None:
        raise KeyError("campaign not found")
    creator_id = str(payload.get("creator_id") or "")
    review = PostCampaignReview(
        review_id=review_id_for(campaign_id, creator_id, str(payload.get("content_url") or "")),
        campaign_id=campaign_id,
        creator_id=creator_id,
        content_url=str(payload.get("content_url") or ""),
        actual_price=int(payload.get("actual_price") or 0),
        views=int(payload.get("views") or 0),
        likes=int(payload.get("likes") or 0),
        comments=int(payload.get("comments") or 0),
        brand_feedback=str(payload.get("brand_feedback") or ""),
        comment_feedback=str(payload.get("comment_feedback") or ""),
        delivery_rating=float(payload.get("delivery_rating") or 0),
        case_status=str(payload.get("case_status") or "approved_case"),
        visibility=str(payload.get("visibility") or "client_summary"),
    )
    project.reviews.append(review)
    project.timeline.append(_event("post_review_added", "投后案例已录入并回流", review.to_dict()))
    project.campaign.status = "reviewed"
    _apply_review_to_creator(db_path, review)
    try:
        from src.symbolic.os_service import create_feedback_correction

        correction = create_feedback_correction(db_path, project, review)
        project.timeline.append(
            _event(
                "symbolic_feedback_corrected",
                "已生成符号反馈修正",
                {
                    "correction_id": correction.correction_id,
                    "activated_tags": correction.activated_tags,
                    "misread_points": correction.misread_points,
                },
            )
        )
    except Exception as exc:
        project.timeline.append(_event("symbolic_feedback_correction_failed", "符号反馈修正失败", {"error": str(exc)}))
    upsert_campaign_project(db_path, project)
    return project


def _generate_campaign_plans(campaign: CampaignProfile, matches: list[Any]) -> list[CampaignPlan]:
    specs = [
        ("稳健型方案", matches[:5], "以高匹配垂类达人和可解释内容为主，优先保证品牌安全与专业背书。", "medium"),
        ("破圈型方案", matches[2:8] or matches[:5], "组合垂类测评、生活方式和视觉内容节点，争取跨圈层讨论。", "high"),
        ("性价比型方案", sorted(matches, key=lambda item: item.suggested_budget or item.creator.listed_price)[:6], "优先选择预算友好且数据可信的 KOL/KOC，提高覆盖效率。", "low"),
    ]
    plans: list[CampaignPlan] = []
    budget = campaign.budget or sum(item.suggested_budget or item.creator.listed_price for item in matches[:6]) or 100000
    for index, (name, selected, summary, risk) in enumerate(specs):
        selected = selected or matches[:3]
        allocation = _budget_allocation(campaign.platforms, budget, index)
        content = _content_directions(campaign, name)
        risks = _plan_risks(campaign, selected, risk)
        score = _execution_score(selected, risk)
        plans.append(
            CampaignPlan(
                plan_id=plan_id_for(campaign.campaign_id, name),
                campaign_id=campaign.campaign_id,
                plan_name=name,
                strategy_summary=summary,
                creator_ids=[item.creator.creator_id for item in selected],
                creator_names=[item.creator.name for item in selected],
                budget_allocation=allocation,
                content_directions=content,
                strengths=_plan_strengths(name, selected),
                weaknesses=_plan_weaknesses(name, risk),
                risk_points=risks,
                risk_level=risk,
                execution_score=score,
                is_recommended=index == 0,
            )
        )
    return plans


def _simulate_plan(campaign: CampaignProfile, plan: CampaignPlan) -> CampaignSimulation:
    positive = [
        f"{plan.plan_name}能承接{campaign.product or campaign.industry or '产品'}的核心传播目标。",
        "达人组合有明确角色分工，便于甲方解释预算。",
    ]
    negative = ["如果内容过硬广，评论区可能质疑商业味过重。"]
    if plan.risk_level == "high":
        negative.append("破圈内容更容易触发人群理解偏差，需要预设评论区回应。")
    risks = list(dict.fromkeys(plan.risk_points + ["推演不代表真实 ROI"]))
    suggestions = [
        "保留机动预算给表现较好的内容做二次放大。",
        "在 brief 中明确禁用话术、评论区回应边界和二次授权范围。",
    ]
    return CampaignSimulation(
        simulation_id=simulation_id_for(plan.plan_id),
        campaign_id=campaign.campaign_id,
        plan_id=plan.plan_id,
        summary=f"{plan.plan_name}执行分 {plan.execution_score}，风险等级 {plan.risk_level}。该结论用于投放前压力测试，不预测真实 ROI。",
        positive_reactions=positive,
        negative_reactions=negative,
        risk_points=risks,
        optimization_suggestions=suggestions,
    )


def _apply_review_to_creator(db_path: Path, review: PostCampaignReview) -> None:
    creator = load_profile(db_path, review.creator_id)
    if creator is None:
        return
    data = asdict(creator)
    if review.actual_price:
        data["listed_price"] = review.actual_price
        data["price_source"] = "post_campaign_review"
    if review.delivery_rating:
        data["delivery_rating"] = max(float(data.get("delivery_rating") or 0), review.delivery_rating)
    notes = data.get("manual_notes") or ""
    data["manual_notes"] = f"{notes}\n投后复盘：曝光{review.views} 互动{review.likes + review.comments}；{review.brand_feedback or review.comment_feedback}".strip()
    sources = data.get("data_sources", [])
    if "post_campaign_review" not in sources:
        sources.append("post_campaign_review")
    data["data_sources"] = sources
    save_profile(db_path, CreatorProfile(**data))


def _related_distributions(db_path: Path, project: CampaignProject) -> list[Any]:
    prefix = f"{project.campaign.project_name}-"
    return [item for item in load_all_distribution_briefs(db_path) if item.project_name.startswith(prefix)]


def _simulation_payload_for_plan(db_path: Path, project: CampaignProject, plan: CampaignPlan) -> dict[str, Any]:
    profiles = {profile.creator_id: profile for profile in load_profiles(db_path)}
    matches = []
    for creator_id in plan.creator_ids:
        profile = profiles.get(creator_id)
        if profile is None:
            continue
        matches.append(
            {
                "creator_id": profile.creator_id,
                "creator_name": profile.name,
                "platform": profile.platform,
                "symbolic_score": plan.execution_score,
                "recommended_role": "Campaign Plan 承接达人",
                "risk_points": profile.risk_tags[:3] or plan.risk_points[:2],
            }
        )
    brand = {
        "brand_id": project.campaign.campaign_id,
        "brand_name": project.campaign.client_name,
        "product": project.campaign.product or project.campaign.project_name,
        "target_tags": (project.campaign.goals + project.campaign.target_audience + project.campaign.content_preferences)[:6],
        "danger_tags": plan.risk_points or ["硬广感", "评论区偏离预设叙事"],
    }
    narratives = [
        {
            "narrative_path": " -> ".join(plan.content_directions[:4]) or f"{project.campaign.product or project.campaign.project_name} 传播路径",
        }
    ]
    return {"brand": brand, "matches": matches, "narratives": narratives}


def _creator_room_card(profile: CreatorProfile, project: CampaignProject) -> dict[str, Any]:
    reviews = [item for item in project.reviews if item.creator_id == profile.creator_id]
    latest_review = reviews[-1].to_dict() if reviews else None
    return {
        "creator_id": profile.creator_id,
        "name": profile.name,
        "platform": profile.platform,
        "homepage_url": profile.homepage_url,
        "follower_count": profile.follower_count,
        "listed_price": profile.listed_price,
        "delivery_rating": profile.delivery_rating,
        "tags": (profile.industry_fit_tags + profile.content_capability_tags + profile.suitable_goals)[:8],
        "commercial_status": "reviewed" if latest_review else "candidate",
        "latest_review": latest_review,
    }


def _plan_room_card(project: CampaignProject, plan: CampaignPlan, profiles: dict[str, CreatorProfile]) -> dict[str, Any]:
    simulation = next((item for item in project.simulations if item.plan_id == plan.plan_id), None)
    creators = [
        {
            "creator_id": creator_id,
            "name": profiles[creator_id].name,
            "platform": profiles[creator_id].platform,
            "listed_price": profiles[creator_id].listed_price,
        }
        for creator_id in plan.creator_ids
        if creator_id in profiles
    ]
    return {
        **plan.to_dict(),
        "creators": creators,
        "simulation": simulation.to_dict() if simulation else None,
        "room_status": _plan_room_status(project, plan),
    }


def _plan_room_status(project: CampaignProject, plan: CampaignPlan) -> str:
    if project.archived:
        return "archived"
    if any(review.creator_id in plan.creator_ids for review in project.reviews):
        return "reviewed"
    if any(event.get("payload", {}).get("plan_id") == plan.plan_id and event.get("type") == "brief_distribution_created" for event in project.timeline):
        return "distributed"
    return "ready"


def _campaign_decision_summary(project: CampaignProject, plan_rooms: list[dict[str, Any]], distributions: list[Any]) -> dict[str, Any]:
    recommended = next((plan for plan in plan_rooms if plan.get("is_recommended")), plan_rooms[0] if plan_rooms else {})
    highest_risk = next((plan for plan in plan_rooms if plan.get("risk_level") == "high"), None)
    return {
        "recommended_plan": recommended.get("plan_name", "待生成"),
        "recommended_score": recommended.get("execution_score", 0),
        "risk_watch": (highest_risk or recommended).get("risk_points", [])[:4] if plan_rooms else [],
        "distribution_count": len(distributions),
        "review_count": len(project.reviews),
        "status": project.campaign.status,
    }


def _campaign_room_next_actions(project: CampaignProject, distributions: list[Any]) -> list[str]:
    actions: list[str] = []
    if not project.plans:
        actions.append("补充 brief 后重新生成 Campaign 方案。")
    if project.plans and not distributions:
        actions.append("选择推荐方案生成 Brief 分发，进入博主响应阶段。")
    if distributions and not project.reviews:
        actions.append("等待博主响应后录入首批投后案例，回流达人画像。")
    if project.reviews:
        actions.append("基于复盘表现更新下一轮推荐偏好和报价参考。")
    if not project.archived:
        actions.append("确认项目结束后归档 Campaign，保留案例沉淀。")
    return actions


def _event(event_type: str, title: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    from src.platform_os.schemas import now_iso

    return {"type": event_type, "title": title, "payload": payload or {}, "created_at": now_iso()}


def _budget_allocation(platforms: list[str], budget: int, index: int) -> dict[str, int]:
    if not platforms:
        platforms = ["抖音", "小红书", "B站"]
    weights = [0.5, 0.3, 0.2] if index != 2 else [0.35, 0.35, 0.3]
    allocation = {}
    for platform, weight in zip(platforms[:3], weights):
        allocation[platform] = int(budget * weight)
    allocation["reserve"] = max(0, budget - sum(allocation.values()))
    return allocation


def _content_directions(campaign: CampaignProfile, plan_name: str) -> list[str]:
    product = campaign.product or "产品"
    if "破圈" in plan_name:
        return [f"{product}话题化视觉内容", "垂类达人解释争议点", "生活方式场景种草"]
    if "性价比" in plan_name:
        return [f"{product}核心卖点拆解", "KOC真实体验", "搜索沉淀型图文"]
    return [f"{product}专业测评", "真实使用场景", "品牌背书内容"]


def _plan_risks(campaign: CampaignProfile, selected: list[Any], risk: str) -> list[str]:
    risks = []
    if risk == "high":
        risks.append("破圈内容理解偏差")
    if campaign.budget and sum(item.suggested_budget or item.creator.listed_price for item in selected) > campaign.budget:
        risks.append("预算可能超出")
    if campaign.risk_sensitivity == "high":
        risks.append("品牌安全敏感度高")
    return risks or ["需人工复核达人近期商业密度"]


def _execution_score(selected: list[Any], risk: str) -> int:
    if not selected:
        return 40
    base = round(sum(item.match_score for item in selected) / len(selected))
    penalty = 8 if risk == "high" else 0
    return max(40, min(96, base - penalty))


def _plan_strengths(name: str, selected: list[Any]) -> list[str]:
    return [f"候选达人 {len(selected)} 个", "推荐理由可解释", "可继续生成 Brief 分发"]


def _plan_weaknesses(name: str, risk: str) -> list[str]:
    if risk == "high":
        return ["需要更强评论区和品牌安全预案"]
    return ["仍需博主响应确认真实档期与报价"]


def _step(label: str, count: int, status: str) -> dict[str, Any]:
    return {"label": label, "count": count, "status": status}


def _next_actions(dashboard: dict[str, Any]) -> list[str]:
    metrics = dashboard.get("metrics", {})
    actions = []
    if not metrics.get("commercial_profiles"):
        actions.append("向重点博主发送商业档案邀请，补齐报价、档期和案例。")
    if not metrics.get("client_proposals"):
        actions.append("从客户 Brief 生成首个协作方案并打开甲方反馈链路。")
    if not metrics.get("distribution_briefs"):
        actions.append("把确认后的候选名单转为 Brief 分发，收集博主响应。")
    if not actions:
        actions.append("复盘客户反馈和博主案例，把偏好继续沉淀到统一 Profile。")
    return actions
