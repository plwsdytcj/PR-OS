from __future__ import annotations

from typing import Any
from urllib.parse import unquote

from src.creator_commercial.schemas import CreatorCase, brand_slug


PUBLIC_VISIBILITIES = {"public", "client_summary"}


def case_display_title(case: CreatorCase) -> str:
    title = (case.case_title or case.content_topic or "").strip()
    if title:
        return title
    if case.brand_name and case.content_format:
        return f"{case.brand_name} · {case.content_format}"
    return case.brand_name or "合作案例"


def case_display_summary(case: CreatorCase) -> str:
    summary = (case.case_summary or case.comment_feedback or case.cooperation_goal or case.reuse_suggestion or "").strip()
    if summary:
        return summary
    return (case.content_topic or "").strip()


def is_public_case(case: CreatorCase) -> bool:
    return str(case.visibility or "").strip() in PUBLIC_VISIBILITIES


def public_case_payload(case: CreatorCase, *, creator: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = case.to_dict()
    payload["case_title"] = case_display_title(case)
    payload["case_summary"] = case_display_summary(case)
    payload["brand_slug"] = brand_slug(case.brand_name)
    payload["public_url"] = f"/cases/{case.case_id}"
    payload["creator_kit_url"] = f"/creator-kit/{case.creator_id}" if case.creator_id else ""
    if creator:
        payload["creator"] = {
            "creator_id": creator.get("creator_id") or case.creator_id,
            "name": creator.get("name") or case.creator_name,
            "platform": creator.get("platform") or case.platform,
            "avatar_url": creator.get("avatar_url") or "",
            "homepage_url": creator.get("homepage_url") or "",
        }
    return payload


def filter_public_cases(
    cases: list[CreatorCase],
    *,
    query: str = "",
    brand_name: str = "",
    creator_id: str = "",
    industry: str = "",
    platform: str = "",
    content_format: str = "",
    featured_only: bool = False,
) -> list[CreatorCase]:
    items = [case for case in cases if is_public_case(case)]
    if creator_id:
        items = [case for case in items if case.creator_id == creator_id]
    if brand_name:
        needle = brand_name.strip().lower()
        items = [case for case in items if case.brand_name.lower() == needle]
    if industry:
        needle = industry.strip().lower()
        items = [case for case in items if needle in (case.industry or "").lower()]
    if platform:
        needle = platform.strip().lower()
        items = [case for case in items if needle in (case.platform or "").lower()]
    if content_format:
        needle = content_format.strip().lower()
        items = [case for case in items if needle in (case.content_format or "").lower()]
    if featured_only:
        items = [case for case in items if bool(case.featured_on_kit)]
    if query:
        needle = query.strip().lower()
        items = [
            case
            for case in items
            if needle
            in " ".join(
                [
                    case_display_title(case),
                    case_display_summary(case),
                    case.brand_name,
                    case.creator_name,
                    case.industry,
                    case.product,
                    case.platform,
                    case.content_format,
                    " ".join(case.active_tags),
                ]
            ).lower()
        ]
    items.sort(key=lambda item: item.updated_at or item.created_at, reverse=True)
    return items


def decode_brand_slug(value: str) -> str:
    return unquote((value or "").strip())
