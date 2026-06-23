"""Rule-based creator tag classification for WeChat-style free tags."""

from __future__ import annotations

import re
from typing import Any

PLATFORM_ALIASES: dict[str, str] = {
    "抖音": "抖音",
    "douyin": "抖音",
    "小红书": "小红书",
    "xhs": "小红书",
    "知乎": "知乎",
    "zhihu": "知乎",
    "b站": "B站",
    "bilibili": "B站",
    "微博": "微博",
    "weibo": "微博",
    "公众号": "微信公众号",
    "微信": "微信公众号",
    "视频号": "视频号",
    "豆瓣": "豆瓣",
    "今日头条": "今日头条",
    "头条": "今日头条",
    "快手": "快手",
    "推特": "推特",
    "twitter": "推特",
}

INDUSTRY_HINTS: dict[str, str] = {
    "科技": "科技互联网",
    "科技互联网": "科技互联网",
    "互联网": "科技互联网",
    "ai": "AI产业",
    "人工智能": "AI产业",
    "ai产业": "AI产业",
    "电影": "电影",
    "影视": "电影",
    "游戏": "游戏",
    "公关": "公关",
    "消费": "消费",
    "财经": "财经",
    "法律": "法律",
    "新闻": "新闻",
    "时政": "新闻",
    "汽车": "汽车",
    "文旅": "文旅出行",
    "生活方式": "生活方式",
}

IDENTITY_HINTS: dict[str, str] = {
    "记者": "记者",
    "影评人": "影评人",
    "科技博主": "科技博主",
    "博主": "科技博主",
    "kol": "科技博主",
    "行业专家": "行业专家",
    "专家": "行业专家",
    "专栏作者": "专栏作者",
    "专栏": "专栏作者",
    "创作者": "创作者",
    "网红": "网红",
    "up主": "创作者",
    "公关": "公关",
    "pr": "公关",
}

CAPABILITY_HINTS: dict[str, str] = {
    "深度稿": "深度稿",
    "深度": "深度稿",
    "观点文": "观点文",
    "观点": "观点文",
    "快评": "快评",
    "专访": "专访",
    "访谈": "专访",
    "影评": "影评",
    "人物稿": "人物稿",
    "案例拆解": "案例拆解",
    "科普": "科普解释",
    "科普解释": "科普解释",
    "测评": "测评",
    "种草": "种草",
}

DELIVERY_HINTS: dict[str, str] = {
    "出稿快": "出稿快",
    "出稿慢": "出稿慢",
    "内容精品": "内容精品",
    "精品": "内容精品",
    "沟通顺畅": "沟通顺畅",
    "好沟通": "沟通顺畅",
    "需要催": "需要催",
    "要催": "需要催",
    "容易改稿": "容易改稿",
    "改稿多": "容易改稿",
    "配合度高": "配合度高",
    "配合好": "配合度高",
    "响应快": "响应快",
    "拖稿": "出稿慢",
}

RISK_HINTS: dict[str, str] = {
    "争议大": "争议大",
    "争议": "争议大",
    "立场强": "立场强",
    "观点强": "立场强",
    "审核风险": "审核风险",
    "审核": "审核风险",
    "报价波动": "报价波动",
    "报价不稳定": "报价不稳定",
    "不可控": "内容不可控",
    "内容不可控": "内容不可控",
    "硬广": "不适合硬广",
    "不适合硬广": "不适合硬广",
    "商业痕迹敏感": "商业痕迹敏感",
    "需提前确认立场": "需提前确认立场",
}

GOAL_HINTS: dict[str, str] = {
    "技术解释者": "技术解释者",
    "技术解释": "技术解释者",
    "圈层扩散": "圈层扩散",
    "扩散": "圈层扩散",
    "品牌故事": "品牌故事转译",
    "故事转译": "品牌故事转译",
    "专业背书": "专业背书",
    "背书": "专业背书",
    "搜索沉淀": "搜索沉淀",
    "风险缓冲": "风险缓冲",
    "议题引爆": "议题引爆",
    "高知信任": "高知信任入口",
}

FORMAT_HINTS: dict[str, str] = {
    "约稿": "约稿",
    "代发": "代发",
    "原创发": "原创发",
    "原创": "原创发",
    "转发": "转发",
    "专栏": "专栏",
    "圆桌": "圆桌",
}

BUDGET_HINTS: dict[str, str] = {
    "高预算": "适合高预算",
    "中预算": "适合中预算",
    "低预算": "适合低预算",
    "报价稳定": "报价稳定",
    "报价浮动": "报价浮动",
}

BRAND_HINTS = {
    "腾讯",
    "华为",
    "美团",
    "minimax",
    "爱奇艺",
    "字节跳动",
    "字节",
    "网易",
    "万里汇",
    "理想",
    "特斯拉",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "").strip().lower())


def _match_map(text: str, mapping: dict[str, str]) -> str | None:
    norm = _norm(text)
    if not norm:
        return None
    for key, value in mapping.items():
        if _norm(key) in norm or norm in _norm(key):
            return value
    return None


def _split_mixed_tag(tag: str) -> list[str]:
    raw = str(tag or "").strip()
    if not raw:
        return []
    parts = re.split(r"[\s/|+、，,]+", raw)
    return [part.strip() for part in parts if part.strip()] or [raw]


def classify_single_tag(tag: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {
        "platform_hint": [],
        "industry_fit_tags": [],
        "identity_tags": [],
        "content_capability_tags": [],
        "delivery_tags": [],
        "risk_tags": [],
        "suitable_goals": [],
        "cooperation_formats": [],
        "budget_fit_tags": [],
        "cooperation_brands": [],
        "unclassified": [],
    }
    text = str(tag or "").strip()
    if not text:
        return result

    for alias, platform in PLATFORM_ALIASES.items():
        if alias.lower() in _norm(text):
            result["platform_hint"].append(platform)

    industry = _match_map(text, INDUSTRY_HINTS)
    if industry:
        result["industry_fit_tags"].append(industry)

    identity = _match_map(text, IDENTITY_HINTS)
    if identity:
        result["identity_tags"].append(identity)

    capability = _match_map(text, CAPABILITY_HINTS)
    if capability:
        result["content_capability_tags"].append(capability)

    delivery = _match_map(text, DELIVERY_HINTS)
    if delivery:
        result["delivery_tags"].append(delivery)

    risk = _match_map(text, RISK_HINTS)
    if risk:
        result["risk_tags"].append(risk)

    goal = _match_map(text, GOAL_HINTS)
    if goal:
        result["suitable_goals"].append(goal)

    fmt = _match_map(text, FORMAT_HINTS)
    if fmt:
        result["cooperation_formats"].append(fmt)

    budget = _match_map(text, BUDGET_HINTS)
    if budget:
        result["budget_fit_tags"].append(budget)

    for brand in BRAND_HINTS:
        if brand.lower() in _norm(text):
            result["cooperation_brands"].append(brand)

    classified = any(
        result[key]
        for key in result
        if key not in {"platform_hint", "unclassified"}
    )
    if not classified:
        result["unclassified"].append(text)
    return result


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _merge_bucket(target: dict[str, list[str]], bucket: dict[str, list[str]]) -> None:
    for key, values in bucket.items():
        target.setdefault(key, [])
        target[key].extend(values)


def build_narrative_position(
    *,
    industry: list[str],
    identity: list[str],
    capability: list[str],
    delivery: list[str],
    risk: list[str],
    goals: list[str],
) -> str:
    parts: list[str] = []
    if identity:
        parts.append(identity[0])
    if industry:
        parts.append(f"聚焦{'/'.join(industry[:2])}")
    if capability:
        parts.append(f"擅长{capability[0]}")
    if goals:
        parts.append(f"适合担任{goals[0]}")
    elif identity and industry:
        parts.append("适合担任圈层扩散或专业背书角色")
    narrative = "，".join(parts)
    if delivery:
        narrative += f"；履约侧：{'/'.join(delivery[:2])}"
    if risk:
        narrative += f"；注意{'/'.join(risk[:2])}"
    return narrative.strip("；")


def classify_creator_tags(
    tags: list[str] | str,
    *,
    platform: str = "",
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = existing or {}
    incoming = tags if isinstance(tags, list) else re.split(r"[,，、\n]+", str(tags or ""))
    incoming = [str(item).strip() for item in incoming if str(item).strip()]

    merged: dict[str, list[str]] = {
        "platform_hint": [],
        "industry_fit_tags": [],
        "identity_tags": [],
        "content_capability_tags": [],
        "delivery_tags": [],
        "risk_tags": [],
        "suitable_goals": [],
        "cooperation_formats": [],
        "budget_fit_tags": [],
        "cooperation_brands": [],
        "unclassified": [],
        "personal_tags": [],
    }

    for tag in incoming:
        for piece in _split_mixed_tag(tag):
            _merge_bucket(merged, classify_single_tag(piece))

    for key in list(merged):
        if key == "personal_tags":
            continue
        merged[key] = _dedupe(merged.get(key, []))

    for field in (
        "industry_fit_tags",
        "identity_tags",
        "content_capability_tags",
        "delivery_tags",
        "risk_tags",
        "suitable_goals",
        "cooperation_formats",
        "budget_fit_tags",
        "cooperation_brands",
    ):
        current = [str(item).strip() for item in existing.get(field, []) if str(item).strip()]
        merged[field] = _dedupe(current + merged.get(field, []))

    merged["personal_tags"] = _dedupe(incoming + merged.get("unclassified", []))

    platform_hint = merged["platform_hint"][0] if merged["platform_hint"] else ""
    if not platform_hint and platform:
        platform_hint = platform

    narrative = build_narrative_position(
        industry=merged["industry_fit_tags"],
        identity=merged["identity_tags"],
        capability=merged["content_capability_tags"],
        delivery=merged["delivery_tags"],
        risk=merged["risk_tags"],
        goals=merged["suitable_goals"],
    )
    if existing.get("narrative_position"):
        narrative = str(existing["narrative_position"])

    return {
        "platform_hint": platform_hint,
        "industry_fit_tags": merged["industry_fit_tags"],
        "identity_tags": merged["identity_tags"],
        "content_capability_tags": merged["content_capability_tags"],
        "delivery_tags": merged["delivery_tags"],
        "risk_tags": merged["risk_tags"],
        "suitable_goals": merged["suitable_goals"],
        "cooperation_formats": merged["cooperation_formats"],
        "budget_fit_tags": merged["budget_fit_tags"],
        "cooperation_brands": merged["cooperation_brands"],
        "personal_tags": merged["personal_tags"],
        "unclassified": merged["unclassified"],
        "narrative_position": narrative,
        "narrative_suggestions": _dedupe(
            merged["suitable_goals"]
            + [
                "科技权威解释者",
                "电影文化圈层扩散者",
                "公关行业关系背书者",
                "高知人群信任入口",
                "品牌故事转译者",
            ]
        )[:4],
    }
