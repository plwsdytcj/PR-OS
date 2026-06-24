"""Map parsed PR briefs to creator-filter criteria (shared tag framework)."""

from __future__ import annotations

import re
from typing import Any

from src.intelligence.brief_parser import parse_brief
from src.intelligence.business_type import classify_business_type
from src.intelligence.tag_classifier import PLATFORM_ALIASES, classify_creator_tags
from src.schemas import BrandBrief

# Filter UI group id -> classified field buckets
_FILTER_GROUP_FIELDS: dict[str, list[str]] = {
    "industry": ["industry_fit_tags"],
    "identity": ["identity_tags"],
    "capability": ["content_capability_tags"],
    "commercial": ["budget_fit_tags", "cooperation_brands"],
    "delivery": ["delivery_tags"],
    "risk": ["risk_tags"],
    "narrative": ["suitable_goals"],
}

_GOAL_NARRATIVE_HINTS: dict[str, str] = {
    "曝光": "圈层扩散",
    "种草": "圈层扩散",
    "转化": "专业背书",
    "新品预热": "议题引爆",
    "品牌背书": "专业背书",
    "公关破圈": "议题引爆",
    "舆情修复": "风险缓冲",
    "搜索沉淀": "搜索沉淀",
    "用户教育": "技术解释者",
}

_CONTENT_CAPABILITY_HINTS: dict[str, str] = {
    "科技感": "科普解释",
    "智能化": "科普解释",
    "专业测评": "测评",
    "真实体验": "种草",
    "口播解释": "科普解释",
    "视觉大片": "深度稿",
    "生活方式": "种草",
    "成分科技": "科普解释",
    "高端感": "深度稿",
}


def _normalize_platform(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    for alias, canonical in PLATFORM_ALIASES.items():
        if alias.lower() == lowered or alias == text:
            return canonical
    return text


def _raw_text_tokens(raw_text: str) -> list[str]:
    text = str(raw_text or "").strip()
    if not text:
        return []
    segments = re.split(r"[，,。；;\n、]+", text)
    return [segment.strip() for segment in segments if segment.strip()]


def _brief_tokens(brief: BrandBrief) -> list[str]:
    tokens: list[str] = []
    if brief.industry:
        tokens.append(brief.industry)
    if brief.product:
        tokens.append(brief.product)
    if brief.campaign_stage:
        tokens.append(brief.campaign_stage)
    tokens.extend(brief.goals)
    tokens.extend(brief.content_preference)
    tokens.extend(brief.target_audience)
    tokens.extend(brief.platform_preference)
    tokens.extend(_raw_text_tokens(brief.raw_text))
    return [str(item).strip() for item in tokens if str(item).strip()]


def _tags_for_groups(classified: dict[str, Any]) -> dict[str, list[str]]:
    tags: dict[str, list[str]] = {}
    for group_id, fields in _FILTER_GROUP_FIELDS.items():
        merged: list[str] = []
        for field in fields:
            merged.extend(str(item).strip() for item in classified.get(field, []) if str(item).strip())
        # preserve order, dedupe
        seen: set[str] = set()
        ordered: list[str] = []
        for item in merged:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        if ordered:
            tags[group_id] = ordered[:4]
    return tags


def _budget_fit_tag(budget: int) -> str | None:
    if budget <= 0:
        return None
    if budget >= 500_000:
        return "适合高预算"
    if budget >= 100_000:
        return "适合中预算"
    return "适合低预算"


def suggest_creator_filter_from_brief(brief: BrandBrief) -> dict[str, Any]:
    tokens = _brief_tokens(brief)
    classified = classify_creator_tags(tokens, platform=brief.platform_preference[0] if brief.platform_preference else "")

    for goal in brief.goals:
        narrative = _GOAL_NARRATIVE_HINTS.get(goal)
        if narrative:
            classified["suitable_goals"].append(narrative)
    for pref in brief.content_preference:
        capability = _CONTENT_CAPABILITY_HINTS.get(pref)
        if capability:
            classified["content_capability_tags"].append(capability)

    if brief.industry and brief.industry not in classified["industry_fit_tags"]:
        classified["industry_fit_tags"].insert(0, brief.industry)

    budget_tag = _budget_fit_tag(brief.budget)
    if budget_tag:
        classified["budget_fit_tags"].append(budget_tag)

    raw_text = str(brief.raw_text or "")
    if "无拖稿" in raw_text or "不拖稿" in raw_text:
        classified["delivery_tags"] = [tag for tag in classified["delivery_tags"] if tag != "出稿慢"]
        if "出稿快" not in classified["delivery_tags"]:
            classified["delivery_tags"].append("出稿快")
    if "赞粉比" in raw_text and any(marker in raw_text for marker in ("高", "≥", ">=", "大于")):
        hard_min_ratio: float | None = 5.0
    else:
        hard_min_ratio = None

    tags = _tags_for_groups(classified)
    platform = ""
    if brief.platform_preference:
        platform = _normalize_platform(brief.platform_preference[0])
    elif classified.get("platform_hint"):
        platform = _normalize_platform(str(classified["platform_hint"]))

    query_parts = [part for part in [brief.product, brief.industry] if part]
    hard: dict[str, Any] = {
        "platform": platform,
        "query": " ".join(query_parts).strip(),
        "maxPrice": None,
        "minLikeFanRatio": hard_min_ratio,
    }
    if brief.budget > 0:
        # Rough per-creator quote ceiling for shortlist building.
        hard["maxPrice"] = max(10_000, brief.budget // 8)
    if hard_min_ratio is not None:
        hard["minRecentPostsCount"] = 10

    hints: list[str] = []
    if brief.industry:
        hints.append(f"行业：{brief.industry}")
    if brief.goals:
        hints.append(f"目标：{'、'.join(brief.goals[:3])}")
    if platform:
        hints.append(f"平台：{platform}")
    if brief.budget:
        hints.append(f"预算：{brief.budget:,} 元")
    tag_count = sum(len(values) for values in tags.values())
    if tag_count:
        hints.append(f"已点亮 {tag_count} 个叙事标签")
    if hard_min_ratio:
        hints.append(f"赞粉比门槛 ≥ {hard_min_ratio:g}")

    return {
        "brief": {
            "industry": brief.industry,
            "product": brief.product,
            "budget": brief.budget,
            "campaign_stage": brief.campaign_stage,
            "goals": brief.goals,
            "platform_preference": brief.platform_preference,
            "content_preference": brief.content_preference,
        },
        "business": classify_business_type(brief),
        "hard": hard,
        "tags": tags,
        "hints": hints,
    }


def suggest_creator_filter_from_text(text: str) -> dict[str, Any]:
    return suggest_creator_filter_from_brief(parse_brief(text))
