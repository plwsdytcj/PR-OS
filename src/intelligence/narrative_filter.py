"""Narrative-first creator filter analysis for PR campaign briefs."""

from __future__ import annotations

from typing import Any

from src.intelligence.brief_parser import parse_brief
from src.intelligence.filter_from_brief import suggest_creator_filter_from_brief
from src.intelligence.matching import rank_creator, rank_creators
from src.intelligence.tag_classifier import classify_creator_tags
from src.llm.glm_client import GlmClient
from src.schemas import BrandBrief, CreatorProfile

_NARRATIVE_GROUP_IDS = ("industry", "identity", "capability", "narrative")
_EXTRA_GROUP_IDS = ("commercial", "delivery", "risk")


def _split_tags(value: str | list[str] | None) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    parts: list[str] = []
    for chunk in text.replace("，", ",").replace("、", ",").split(","):
        for piece in chunk.splitlines():
            piece = piece.strip()
            if piece:
                parts.append(piece)
    return parts


def _merge_tag_groups(base: dict[str, list[str]], classified: dict[str, Any]) -> dict[str, list[str]]:
    mapping = {
        "industry": "industry_fit_tags",
        "identity": "identity_tags",
        "capability": "content_capability_tags",
        "narrative": "suitable_goals",
        "commercial": ("budget_fit_tags", "cooperation_brands"),
        "delivery": "delivery_tags",
        "risk": "risk_tags",
    }
    merged = {key: list(values) for key, values in base.items()}
    for group_id, fields in mapping.items():
        if isinstance(fields, tuple):
            values: list[str] = []
            for field in fields:
                values.extend(str(item).strip() for item in classified.get(field, []) if str(item).strip())
        else:
            values = [str(item).strip() for item in classified.get(fields, []) if str(item).strip()]
        if not values:
            continue
        seen = set(merged.get(group_id, []))
        for item in values:
            if item in seen:
                continue
            seen.add(item)
            merged.setdefault(group_id, []).append(item)
    return {key: values[:5] for key, values in merged.items() if values}


def _rule_summary(brief: BrandBrief, tags: dict[str, list[str]]) -> str:
    focus = []
    for group_id in _NARRATIVE_GROUP_IDS:
        values = tags.get(group_id) or []
        if values:
            focus.append(f"{group_id}={ '、'.join(values[:3]) }")
    parts = ["已根据 Brief 与文字标签完成叙事匹配。"]
    if brief.industry:
        parts.append(f"行业：{brief.industry}")
    if brief.goals:
        parts.append(f"目标：{'、'.join(brief.goals[:3])}")
    if focus:
        parts.append(f"建议点亮：{'；'.join(focus)}")
    return " ".join(parts)


def _glm_narrative_enrich(brief: BrandBrief, text_tags: list[str], tags: dict[str, list[str]]) -> dict[str, str]:
    client = GlmClient()
    if not client.available:
        return {}
    prompt = {
        "brief": brief.raw_text[:1200],
        "text_tags": text_tags[:24],
        "current_tags": tags,
        "task": "你是公关 KOL 筛选顾问。根据 brief 和标签，输出叙事筛选策略。",
        "output_json": {
            "summary": "2-3句分析摘要",
            "narrative_strategy": "商业叙事如何落到博主标签",
            "focus_groups": {"industry": [], "identity": [], "capability": [], "narrative": []},
            "avoid_risks": [],
        },
    }
    try:
        result = client.complete_json(
            "你是 PR 达人筛选专家，只返回 JSON。",
            str(prompt),
            timeout=45,
        )
    except Exception:
        return {}
    out: dict[str, str] = {}
    if isinstance(result.get("summary"), str):
        out["summary"] = result["summary"].strip()
    if isinstance(result.get("narrative_strategy"), str):
        out["narrative_strategy"] = result["narrative_strategy"].strip()
    focus = result.get("focus_groups")
    if isinstance(focus, dict):
        for group_id in _NARRATIVE_GROUP_IDS:
            values = focus.get(group_id)
            if not isinstance(values, list):
                continue
            cleaned = [str(item).strip() for item in values if str(item).strip()]
            if cleaned:
                tags.setdefault(group_id, [])
                seen = set(tags[group_id])
                for item in cleaned:
                    if item in seen:
                        continue
                    seen.add(item)
                    tags[group_id].append(item)
    return out


def analyze_narrative_filter(
    *,
    brief_text: str,
    text_tags: str | list[str] | None = None,
    platform: str = "",
) -> dict[str, Any]:
    brief = parse_brief(brief_text)
    tags_list = _split_tags(text_tags)
    classified = classify_creator_tags(tags_list + [brief_text], platform=platform)
    base = suggest_creator_filter_from_brief(brief)
    tags = _merge_tag_groups(base.get("tags", {}), classified)
    for tag in tags_list:
        extra = classify_creator_tags([tag], platform=platform)
        tags = _merge_tag_groups(tags, extra)

    glm = _glm_narrative_enrich(brief, tags_list, tags)
    summary = glm.get("summary") or _rule_summary(brief, tags)
    narrative_strategy = glm.get("narrative_strategy") or (
        "优先匹配叙事角色与内容能力，确认博主能否把品牌故事转译给目标人群。"
    )

    return {
        "brief": {
            "raw_text": brief.raw_text,
            "industry": brief.industry,
            "product": brief.product,
            "budget": brief.budget,
            "goals": brief.goals,
            "platform_preference": brief.platform_preference,
            "content_preference": brief.content_preference,
        },
        "tags": tags,
        "narrative_tags": {key: tags[key] for key in _NARRATIVE_GROUP_IDS if tags.get(key)},
        "extra_tags": {key: tags[key] for key in _EXTRA_GROUP_IDS if tags.get(key)},
        "hard": base.get("hard", {}),
        "summary": summary,
        "narrative_strategy": narrative_strategy,
        "hints": base.get("hints", []),
        "ai_used": bool(glm),
    }


def recommend_creators_for_filter(
    *,
    brief_text: str,
    text_tags: str | list[str] | None,
    creators: list[CreatorProfile],
) -> list[dict[str, Any]]:
    brief = parse_brief(brief_text)
    tags_list = _split_tags(text_tags)
    if tags_list:
        brief = BrandBrief(
            raw_text=brief.raw_text,
            industry=brief.industry,
            product=brief.product,
            budget=brief.budget,
            campaign_stage=brief.campaign_stage,
            goals=brief.goals or tags_list[:3],
            target_audience=brief.target_audience,
            platform_preference=brief.platform_preference,
            content_preference=brief.content_preference or tags_list[:4],
        )
    rankings = rank_creators(brief, creators)
    items: list[dict[str, Any]] = []
    for result in rankings:
        items.append(
            {
                "creator_id": result.creator.creator_id,
                "creator_name": result.creator.name,
                "platform": result.creator.platform,
                "match_score": result.match_score,
                "recommendation_level": result.recommendation_level,
                "recommended_role": result.recommended_role,
                "reasons": result.reasons,
                "reason_text": "；".join(result.reasons),
                "risk_points": result.risk_points,
            }
        )
    return items
