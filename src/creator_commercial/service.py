from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.creator_commercial.schemas import (
    CreatorCase,
    CreatorCommercialProfile,
    CreatorInvitation,
    CreatorSubmission,
    case_id_for,
    expires_at,
    invitation_id_for,
    now_iso,
    submission_id_for,
)
from src.creator_commercial.storage import delete_case, load_all_cases, load_case, upsert_case, upsert_commercial_profile, upsert_invitation, upsert_submission
from src.intelligence.profiling import enrich_profiles
from src.schemas import CreatorProfile, split_tags
from src.storage.db import load_profile, save_profile


LIST_FIELDS = {
    "industry_fit_tags",
    "content_capability_tags",
    "suitable_stages",
    "suitable_goals",
    "cooperation_preferences",
    "unavailable_types",
    "risk_tags",
    "cooperation_brands",
    "cooperation_formats",
}


def create_creator_invitation(
    db_path: Path,
    creator: CreatorProfile,
    invited_by: str = "media_user",
    expires_days: int = 14,
) -> CreatorInvitation:
    invitation = CreatorInvitation(
        invitation_id=invitation_id_for(creator.creator_id),
        creator_id=creator.creator_id,
        creator_name=creator.name,
        invited_by=invited_by,
        expires_at=expires_at(expires_days),
    )
    upsert_invitation(db_path, invitation)
    return invitation


def mark_invitation_opened(db_path: Path, invitation: CreatorInvitation) -> CreatorInvitation:
    if not invitation.opened_at:
        invitation.opened_at = now_iso()
    if invitation.status == "sent":
        invitation.status = "opened"
    upsert_invitation(db_path, invitation)
    return invitation


def create_creator_submission(
    db_path: Path,
    invitation: CreatorInvitation,
    payload: dict[str, Any],
) -> CreatorSubmission:
    fields = payload.get("profile_fields") if isinstance(payload.get("profile_fields"), dict) else payload
    fields = normalize_profile_fields(fields if isinstance(fields, dict) else {})
    cases = [_case_from_payload(invitation.creator_id, item) for item in payload.get("cases") or [] if isinstance(item, dict)]
    draft = generate_ai_commercial_profile(invitation.creator_id, fields, cases)
    submission = CreatorSubmission(
        submission_id=submission_id_for(invitation.invitation_id),
        creator_id=invitation.creator_id,
        invitation_id=invitation.invitation_id,
        profile_fields=fields,
        cases=cases,
        ai_profile=draft.to_dict(),
        creator_note=str(payload.get("creator_note") or fields.get("creator_note") or ""),
    )
    invitation.status = "submitted"
    invitation.submitted_at = now_iso()
    upsert_invitation(db_path, invitation)
    upsert_submission(db_path, submission)
    return submission


def generate_ai_commercial_profile(creator_id: str, fields: dict[str, Any], cases: list[CreatorCase]) -> CreatorCommercialProfile:
    industry_tags = split_tags(fields.get("industry_fit_tags")) or _dedupe([case.industry for case in cases if case.industry])
    capability_tags = split_tags(fields.get("content_capability_tags")) or split_tags(fields.get("cooperation_formats"))
    goals = split_tags(fields.get("suitable_goals")) or _dedupe([case.cooperation_goal for case in cases if case.cooperation_goal])
    stages = split_tags(fields.get("suitable_stages")) or _infer_stages(goals, fields)
    preferences = split_tags(fields.get("cooperation_preferences"))
    unavailable = split_tags(fields.get("unavailable_types"))
    risks = split_tags(fields.get("risk_tags"))
    price_range = str(fields.get("price_range") or fields.get("listed_price") or "").strip()
    availability = str(fields.get("availability") or "").strip()
    positioning = str(fields.get("commercial_positioning") or fields.get("bio") or "").strip()
    if not positioning:
        tags = "、".join((industry_tags + capability_tags)[:4]) or "待补充"
        positioning = f"适合{tags}方向的商业合作博主"
    if not risks and not cases:
        risks = ["缺少可核验案例"]
    confidence = "high" if len(cases) >= 2 and price_range else ("medium" if cases or price_range else "low")
    return CreatorCommercialProfile(
        creator_id=creator_id,
        commercial_positioning=positioning,
        industry_fit_tags=industry_tags,
        content_capability_tags=capability_tags,
        suitable_stages=stages,
        suitable_goals=goals,
        cooperation_preferences=preferences,
        unavailable_types=unavailable,
        price_range=price_range,
        availability=availability,
        case_summaries=[case_summary(case) for case in cases],
        risk_tags=risks,
        profile_confidence=confidence,
    )


def review_creator_submission(
    db_path: Path,
    creator: CreatorProfile,
    submission: CreatorSubmission,
    decision: str = "approved",
    reviewed_by: str = "media_user",
    review_note: str = "",
) -> tuple[CreatorSubmission, CreatorCommercialProfile | None, CreatorProfile | None]:
    submission.status = decision
    submission.reviewed_at = now_iso()
    submission.reviewed_by = reviewed_by
    if review_note:
        submission.creator_note = f"{submission.creator_note}\n审核备注：{review_note}".strip()
    if decision != "approved":
        upsert_submission(db_path, submission)
        return submission, None, None

    commercial = generate_ai_commercial_profile(submission.creator_id, submission.profile_fields, submission.cases)
    commercial.reviewed_by = reviewed_by
    commercial.updated_at = now_iso()
    upsert_commercial_profile(db_path, commercial)
    for case in submission.cases:
        enriched = _case_from_payload(submission.creator_id, case.to_dict())
        enriched.creator_name = creator.name
        enriched.platform = enriched.platform or creator.platform
        enriched.verification_status = "approved"
        upsert_case(db_path, enriched)
    updated = merge_commercial_into_creator(creator, submission, commercial)
    save_profile(db_path, updated)
    upsert_submission(db_path, submission)
    return submission, commercial, updated


def merge_commercial_into_creator(
    creator: CreatorProfile,
    submission: CreatorSubmission,
    commercial: CreatorCommercialProfile,
) -> CreatorProfile:
    fields = submission.profile_fields
    data = asdict(creator)
    for key in ["name", "platform", "platform_user_id", "homepage_url", "bio", "region", "contact", "manual_notes"]:
        if fields.get(key):
            data[key] = str(fields[key]).strip()
    if fields.get("follower_count"):
        data["follower_count"] = int(fields["follower_count"] or 0)
    listed_price = _extract_price(fields.get("listed_price") or commercial.price_range)
    if listed_price:
        data["listed_price"] = listed_price
        data["price_source"] = "creator_submission"
    data["cooperation_brands"] = _dedupe(data.get("cooperation_brands", []) + split_tags(fields.get("cooperation_brands")) + [case.brand_name for case in submission.cases])
    data["cooperation_formats"] = _dedupe(data.get("cooperation_formats", []) + split_tags(fields.get("cooperation_formats")) + commercial.content_capability_tags)
    data["industry_fit_tags"] = _dedupe(data.get("industry_fit_tags", []) + commercial.industry_fit_tags)
    data["content_capability_tags"] = _dedupe(data.get("content_capability_tags", []) + commercial.content_capability_tags)
    data["suitable_goals"] = _dedupe(data.get("suitable_goals", []) + commercial.suitable_goals)
    data["suitable_stages"] = _dedupe(data.get("suitable_stages", []) + commercial.suitable_stages)
    data["risk_tags"] = _dedupe(data.get("risk_tags", []) + commercial.risk_tags)
    data["data_sources"] = _dedupe(data.get("data_sources", []) + ["creator_submission", "commercial_profile"])
    data["ai_summary"] = commercial.commercial_positioning or data.get("ai_summary", "")
    merged = CreatorProfile(**data)
    return enrich_profiles([merged])[0]


def normalize_profile_fields(fields: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in fields.items():
        if key in LIST_FIELDS:
            normalized[key] = split_tags(value)
        elif key in {"follower_count", "listed_price"}:
            normalized[key] = int(value or 0)
        else:
            normalized[key] = str(value or "").strip()
    return normalized


def save_creator_case(db_path: Path, creator: CreatorProfile, payload: dict[str, Any]) -> CreatorCase:
    merged = {
        **payload,
        "creator_id": creator.creator_id,
        "creator_name": creator.name,
        "platform": str(payload.get("platform") or creator.platform or ""),
    }
    case = _case_from_payload(creator.creator_id, merged)
    case.updated_at = now_iso()
    upsert_case(db_path, case)
    _sync_creator_brands_from_cases(db_path, creator, [case])
    return case


def sync_creator_commercial_cases(db_path: Path, creator: CreatorProfile, cases_payload: list[dict[str, Any]]) -> list[CreatorCase]:
    existing = [case for case in load_all_cases(db_path) if case.creator_id == creator.creator_id]
    kept_ids: set[str] = set()
    saved: list[CreatorCase] = []
    for item in cases_payload:
        brand = str(item.get("brand_name") or item.get("brand") or "").strip()
        title = str(item.get("case_title") or item.get("title") or "").strip()
        if not brand and not title:
            continue
        merged = {
            **item,
            "creator_id": creator.creator_id,
            "creator_name": creator.name,
            "platform": str(item.get("platform") or creator.platform or ""),
        }
        case = _case_from_payload(creator.creator_id, merged)
        case.updated_at = now_iso()
        upsert_case(db_path, case)
        kept_ids.add(case.case_id)
        saved.append(case)
    for case in existing:
        if case.case_id not in kept_ids:
            delete_case(db_path, case.case_id)
    _sync_creator_brands_from_cases(db_path, creator, saved)
    return saved


def _sync_creator_brands_from_cases(db_path: Path, creator: CreatorProfile, cases: list[CreatorCase]) -> None:
    if not cases:
        return
    brands = _dedupe([*creator.cooperation_brands, *[case.brand_name for case in cases if case.brand_name]])
    if brands == creator.cooperation_brands:
        return
    updated = CreatorProfile(**{**asdict(creator), "cooperation_brands": brands, "last_synced_at": now_iso()})
    save_profile(db_path, updated)


def settlement_writeback(
    db_path: Path,
    *,
    client_name: str = "",
    brand_name: str = "",
    industry: str = "",
    product: str = "",
    business_type: str = "",
    settlement_target: str = "",
    project_name: str = "",
    client_confirmed: bool = False,
    payment_status: str = "",
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    cases: list[CreatorCase] = []
    creators_updated: list[str] = []
    settlement_note = " | ".join(
        part
        for part in [
            f"项目：{project_name}" if project_name else "",
            f"客户：{client_name}" if client_name else "",
            f"业务类型：{business_type}" if business_type else "",
            f"结算目标：{settlement_target}" if settlement_target else "",
            "客户已确认" if client_confirmed else "",
            f"付款：{payment_status}" if payment_status else "",
        ]
        if part
    )
    for item in items:
        creator_id = str(item.get("creator_id") or "").strip()
        if not creator_id:
            continue
        creator = load_profile(db_path, creator_id)
        if creator is None:
            continue
        case_payload = {
            **item,
            "brand_name": str(item.get("brand_name") or brand_name or "未命名品牌"),
            "industry": str(item.get("industry") or industry or ""),
            "product": str(item.get("product") or product or ""),
            "cooperation_goal": str(item.get("cooperation_goal") or settlement_target or ""),
            "active_tags": split_tags(item.get("active_tags")) + ([business_type] if business_type else []),
            "comment_feedback": str(item.get("comment_feedback") or settlement_note or ""),
        }
        case = save_creator_case(db_path, creator, case_payload)
        cases.append(case)

        brands = _dedupe([*creator.cooperation_brands, case.brand_name])
        notes = str(creator.manual_notes or "").strip()
        feedback = str(item.get("comment_feedback") or "").strip()
        reuse = str(item.get("reuse_suggestion") or "").strip()
        note_bits = [bit for bit in [feedback, reuse] if bit]
        if note_bits:
            block = " | ".join(note_bits)
            notes = f"{notes}\n{block}".strip() if notes else block
        updated = CreatorProfile(**{**asdict(creator), "cooperation_brands": brands, "manual_notes": notes, "last_synced_at": now_iso()})
        save_profile(db_path, updated)
        creators_updated.append(creator_id)

    return {
        "cases": [case.to_dict() for case in cases],
        "creators_updated": creators_updated,
        "total_cases": len(cases),
    }


def case_summary(case: CreatorCase) -> str:
    parts = [case.brand_name, case.industry, case.content_format, case.cooperation_goal]
    base = " / ".join([part for part in parts if part])
    metrics = "，".join(f"{key}:{value}" for key, value in case.performance.items() if value)
    return f"{base}（{metrics}）" if metrics else base


def _case_from_payload(creator_id: str, data: dict[str, Any]) -> CreatorCase:
    brand = str(data.get("brand_name") or data.get("brand") or "未命名品牌").strip()
    title = str(data.get("case_title") or data.get("title") or data.get("content_topic") or "").strip()
    summary = str(data.get("case_summary") or data.get("summary") or data.get("comment_feedback") or "").strip()
    performance = data.get("performance") if isinstance(data.get("performance"), dict) else {}
    for key in ["exposure", "views", "likes", "comments", "sales", "reads"]:
        if data.get(key):
            performance[key] = data[key]
    featured_raw = data.get("featured_on_kit")
    featured_on_kit = True if featured_raw is None else bool(featured_raw)
    existing_id = str(data.get("case_id") or "").strip()
    return CreatorCase(
        case_id=case_id_for(creator_id, brand, title, existing_id=existing_id),
        creator_id=creator_id,
        creator_name=str(data.get("creator_name") or ""),
        brand_name=brand,
        case_title=title,
        case_summary=summary,
        industry=str(data.get("industry") or ""),
        product=str(data.get("product") or ""),
        platform=str(data.get("platform") or ""),
        content_format=str(data.get("content_format") or data.get("format") or ""),
        content_url=str(data.get("content_url") or data.get("url") or ""),
        content_topic=str(data.get("content_topic") or data.get("topic") or title or ""),
        cooperation_goal=str(data.get("cooperation_goal") or data.get("goal") or ""),
        active_tags=split_tags(data.get("active_tags")),
        performance=performance,
        comment_feedback=str(data.get("comment_feedback") or summary or ""),
        is_successful=str(data.get("is_successful") or ""),
        reuse_suggestion=str(data.get("reuse_suggestion") or ""),
        visibility=str(data.get("visibility") or "public"),
        featured_on_kit=featured_on_kit,
        verification_status=str(data.get("verification_status") or "approved"),
    )


def _infer_stages(goals: list[str], fields: dict[str, Any]) -> list[str]:
    text = " ".join(goals + split_tags(fields.get("cooperation_preferences")) + [str(fields.get("commercial_positioning") or "")])
    stages = []
    if "预热" in text or "上市" in text:
        stages.append("新品预热")
    if "种草" in text:
        stages.append("内容种草")
    if "转化" in text or "销售" in text:
        stages.append("转化收口")
    return stages or ["品牌曝光"]


def _extract_price(value: Any) -> int:
    text = str(value or "")
    if not text:
        return 0
    match = re.search(r"(\d+(?:\.\d+)?)\s*万", text)
    if match:
        return int(float(match.group(1)) * 10_000)
    match = re.search(r"\d{4,}", text.replace(",", ""))
    return int(match.group(0)) if match else 0


def _dedupe(items: list[Any]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result[:18]
