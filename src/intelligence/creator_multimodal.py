from __future__ import annotations

from typing import Any

from src.llm.glm_client import GlmClient
from src.schemas import split_tags


PROFILE_FIELDS = {
    "name",
    "platform",
    "platform_user_id",
    "homepage_url",
    "avatar_url",
    "bio",
    "region",
    "follower_count",
    "following_count",
    "total_likes",
    "recent_posts_count",
    "avg_likes",
    "avg_comments",
    "avg_shares",
    "avg_collections",
    "engagement_rate",
    "listed_price",
    "price_source",
    "contact",
    "cooperation_brands",
    "cooperation_formats",
    "delivery_rating",
    "communication_rating",
    "negotiation_space",
    "manual_notes",
    "industry_fit_tags",
    "content_capability_tags",
    "suitable_goals",
    "suitable_stages",
    "budget_fit_tags",
    "risk_tags",
}

LIST_FIELDS = {
    "cooperation_brands",
    "cooperation_formats",
    "industry_fit_tags",
    "content_capability_tags",
    "suitable_goals",
    "suitable_stages",
    "budget_fit_tags",
    "risk_tags",
}

INT_FIELDS = {
    "follower_count",
    "following_count",
    "total_likes",
    "recent_posts_count",
    "avg_likes",
    "avg_comments",
    "avg_shares",
    "avg_collections",
    "listed_price",
}

FLOAT_FIELDS = {"engagement_rate", "delivery_rating", "communication_rating"}


def analyze_creator_image(
    image_bytes: bytes,
    content_type: str,
    filename: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract creator profile fields from screenshots, rate cards, or case images."""
    context = context or {}
    system = (
        "你是一个公关媒介团队的达人档案录入助手。"
        "你只能根据图片中可见的信息抽取字段，不要编造。"
        "输出必须是 JSON object。"
    )
    user = (
        "请识别这张图片可能包含的 KOL/达人资料、主页截图、报价单或合作案例信息。"
        "返回 JSON，格式为："
        "{"
        '"extracted_fields": {可写入达人档案的字段}, '
        '"evidence": ["逐条说明从图片哪里看出"], '
        '"image_type": "profile_screenshot|rate_card|case_screenshot|avatar|unknown", '
        '"confidence": "high|medium|low", '
        '"warnings": ["不确定或需要人工确认的点"]'
        "}。"
        "extracted_fields 只允许使用这些 key："
        f"{sorted(PROFILE_FIELDS)}。"
        "如果图片中有粉丝数、获赞、报价，请换算成数字，例如 12.3万 -> 123000。"
        "如果没有明确字段，留空对象。"
        "已有档案上下文只用于判断是否为同一个达人，不允许把上下文里的内容当成图片识别结果写入 extracted_fields。"
        f"当前已有档案上下文：{context}"
    )
    try:
        raw = GlmClient().complete_vision_json(system, user, image_bytes, content_type=content_type, timeout=80)
        return normalize_image_analysis(raw)
    except Exception as exc:
        return {
            "extracted_fields": {},
            "evidence": [],
            "image_type": infer_image_type(filename),
            "confidence": "low",
            "warnings": [f"多模态识别暂未成功：{exc}。图片已保存，可人工录入。"],
            "provider": "fallback",
        }


def normalize_image_analysis(raw: dict[str, Any]) -> dict[str, Any]:
    fields = raw.get("extracted_fields") if isinstance(raw.get("extracted_fields"), dict) else {}
    normalized: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in PROFILE_FIELDS:
            continue
        if value is None or value == "":
            continue
        if key in LIST_FIELDS:
            normalized[key] = split_tags(value)
        elif key in INT_FIELDS:
            normalized[key] = _to_int(value)
        elif key in FLOAT_FIELDS:
            normalized[key] = _to_float(value)
        else:
            normalized[key] = str(value).strip()
    return {
        "extracted_fields": normalized,
        "evidence": _string_list(raw.get("evidence")),
        "image_type": str(raw.get("image_type") or "unknown"),
        "confidence": str(raw.get("confidence") or "low"),
        "warnings": _string_list(raw.get("warnings")),
        "provider": str(raw.get("provider") or "glm_vision"),
    }


def infer_image_type(filename: str) -> str:
    text = (filename or "").lower()
    if any(item in text for item in ["avatar", "head", "logo", "头像"]):
        return "avatar"
    if any(item in text for item in ["price", "rate", "报价", "刊例"]):
        return "rate_card"
    if any(item in text for item in ["case", "案例"]):
        return "case_screenshot"
    if any(item in text for item in ["profile", "home", "主页"]):
        return "profile_screenshot"
    return "unknown"


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value:
        return [str(value).strip()]
    return []


def _to_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip().replace(",", "")
    multiplier = 1
    if "万" in text:
        multiplier = 10000
        text = text.replace("万", "")
    elif "k" in text.lower():
        multiplier = 1000
        text = text.lower().replace("k", "")
    elif "m" in text.lower():
        multiplier = 1000000
        text = text.lower().replace("m", "")
    digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
    return int(float(digits or 0) * multiplier)


def _to_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
    number = float(digits or 0)
    if "%" in str(value):
        return number / 100
    return number
