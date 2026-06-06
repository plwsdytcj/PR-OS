from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.brief_distribution.schemas import (
    CreatorBriefResponse,
    DistributionBrief,
    DistributionRecipient,
    brief_id_for,
    now_iso,
    recipient_id_for,
    response_id_for,
)
from src.brief_distribution.storage import upsert_creator_response, upsert_distribution_brief
from src.intelligence.brief_parser import parse_brief
from src.intelligence.matching import rank_creators
from src.schemas import CreatorProfile
from src.storage.db import save_profile


def create_distribution_brief(
    db_path: Path,
    client_name: str,
    project_name: str,
    raw_brief: str,
    creators: list[CreatorProfile],
    creator_ids: list[str] | None = None,
    top_n: int = 8,
    created_by: str = "media_user",
) -> DistributionBrief:
    parsed = parse_brief(raw_brief)
    selected: list[DistributionRecipient] = []
    brief_id = brief_id_for(client_name, project_name)
    if creator_ids:
        creator_lookup = {creator.creator_id: creator for creator in creators}
        for creator_id in creator_ids:
            creator = creator_lookup.get(creator_id)
            if not creator:
                continue
            selected.append(_recipient_from_creator(brief_id, creator))
    else:
        for result in rank_creators(parsed, creators)[:top_n]:
            selected.append(
                DistributionRecipient(
                    recipient_id=recipient_id_for(brief_id, result.creator.creator_id),
                    brief_id=brief_id,
                    creator_id=result.creator.creator_id,
                    creator_name=result.creator.name,
                    platform=result.creator.platform,
                    match_score=result.match_score,
                    recommended_role=result.recommended_role,
                    suggested_budget=result.suggested_budget,
                )
            )
    brief = DistributionBrief(
        brief_id=brief_id,
        client_name=client_name,
        project_name=project_name,
        raw_brief=raw_brief,
        parsed_brief=asdict(parsed),
        created_by=created_by,
        recipients=selected,
    )
    upsert_distribution_brief(db_path, brief)
    return brief


def push_distribution_brief(db_path: Path, brief: DistributionBrief) -> DistributionBrief:
    brief.status = "pushed"
    brief.pushed_at = now_iso()
    for recipient in brief.recipients:
        if recipient.status == "queued":
            recipient.status = "pushed"
        if not recipient.pushed_at:
            recipient.pushed_at = brief.pushed_at
    upsert_distribution_brief(db_path, brief)
    return brief


def mark_recipient_viewed(db_path: Path, brief: DistributionBrief, recipient_id: str) -> tuple[DistributionBrief, DistributionRecipient]:
    recipient = _find_recipient(brief, recipient_id)
    if recipient.status in {"queued", "pushed"}:
        recipient.status = "viewed"
    if not recipient.viewed_at:
        recipient.viewed_at = now_iso()
    upsert_distribution_brief(db_path, brief)
    return brief, recipient


def submit_creator_response(
    db_path: Path,
    brief: DistributionBrief,
    recipient_id: str,
    payload: dict[str, Any],
) -> CreatorBriefResponse:
    recipient = _find_recipient(brief, recipient_id)
    response = CreatorBriefResponse(
        response_id=response_id_for(recipient_id, str(payload.get("interest") or "interested")),
        brief_id=brief.brief_id,
        recipient_id=recipient_id,
        creator_id=recipient.creator_id,
        interest=str(payload.get("interest") or "interested"),
        quote=int(payload.get("quote") or 0),
        availability=str(payload.get("availability") or ""),
        deliverables=str(payload.get("deliverables") or payload.get("content_format") or ""),
        content_direction=str(payload.get("content_direction") or ""),
        needs_sample=bool(payload.get("needs_sample") or False),
        accepts_secondary_rights=bool(payload.get("accepts_secondary_rights") or False),
        accepts_revision=bool(payload.get("accepts_revision", True)),
        questions=str(payload.get("questions") or ""),
        constraints=str(payload.get("constraints") or ""),
        decline_reason=str(payload.get("decline_reason") or ""),
        media_note=str(payload.get("media_note") or ""),
    )
    recipient.status = "responded"
    recipient.responded_at = now_iso()
    upsert_distribution_brief(db_path, brief)
    upsert_creator_response(db_path, response)
    return response


def apply_response_to_creator(
    db_path: Path,
    creator: CreatorProfile,
    response: CreatorBriefResponse,
    brief: DistributionBrief,
) -> CreatorProfile:
    data = asdict(creator)
    notes = data.get("manual_notes") or ""
    response_note = (
        f"Brief响应：{brief.project_name} / {response.interest} / "
        f"报价{response.quote or '-'} / 档期{response.availability or '-'} / "
        f"{response.content_direction or response.decline_reason or response.constraints}"
    )
    data["manual_notes"] = f"{notes}\n{response_note}".strip()
    if response.quote:
        data["listed_price"] = response.quote
        data["price_source"] = "brief_response"
    if response.content_direction:
        formats = data.get("cooperation_formats", [])
        if response.deliverables and response.deliverables not in formats:
            formats.append(response.deliverables)
        data["cooperation_formats"] = formats[:18]
    if response.interest == "declined" and response.decline_reason:
        risks = data.get("risk_tags", [])
        tag = f"不接原因:{response.decline_reason}"
        if tag not in risks:
            risks.append(tag)
        data["risk_tags"] = risks[:18]
    sources = data.get("data_sources", [])
    if "brief_response" not in sources:
        sources.append("brief_response")
    data["data_sources"] = sources
    updated = CreatorProfile(**data)
    save_profile(db_path, updated)
    return updated


def distribution_summary(brief: DistributionBrief, responses: list[CreatorBriefResponse]) -> dict[str, Any]:
    response_by_recipient = {item.recipient_id: item for item in responses}
    executable = []
    declined = []
    pending = []
    for recipient in brief.recipients:
        response = response_by_recipient.get(recipient.recipient_id)
        if response is None:
            pending.append(recipient.to_dict())
            continue
        row = recipient.to_dict() | {"response": asdict(response)}
        if response.interest in {"interested", "maybe"}:
            executable.append(row)
        else:
            declined.append(row)
    return {
        "brief": brief.to_dict(),
        "counts": {
            "total": len(brief.recipients),
            "responded": len(responses),
            "viewed": sum(1 for item in brief.recipients if item.status in {"viewed", "responded"}),
            "interested": sum(1 for item in responses if item.interest == "interested"),
            "maybe": sum(1 for item in responses if item.interest == "maybe"),
            "declined": sum(1 for item in responses if item.interest == "declined"),
            "pending": len(pending),
            "can_execute": sum(1 for item in responses if item.interest in {"interested", "maybe"}),
            "over_budget": sum(1 for item in responses if item.quote and _recipient_budget(brief, item.recipient_id) and item.quote > _recipient_budget(brief, item.recipient_id)),
        },
        "rates": {
            "view_rate": round(sum(1 for item in brief.recipients if item.status in {"viewed", "responded"}) / len(brief.recipients), 3) if brief.recipients else 0,
            "response_rate": round(len(responses) / len(brief.recipients), 3) if brief.recipients else 0,
        },
        "pricing": {
            "average_quote": round(sum(item.quote for item in responses if item.quote) / max(1, sum(1 for item in responses if item.quote))),
        },
        "executable": sorted(executable, key=lambda item: (item["response"].get("quote") or item.get("suggested_budget") or 0)),
        "pending": pending,
        "declined": declined,
    }


def client_response_view(brief: DistributionBrief, responses: list[CreatorBriefResponse]) -> dict[str, Any]:
    summary = distribution_summary(brief, responses)
    visible = []
    for row in summary["executable"]:
        response = row.get("response") or {}
        visible.append(
            {
                "creator_name": row.get("creator_name"),
                "platform": row.get("platform"),
                "match_score": row.get("match_score"),
                "quote": response.get("quote"),
                "availability": response.get("availability"),
                "content_direction": response.get("content_direction"),
                "deliverables": response.get("deliverables"),
                "media_recommendation": _media_recommendation(row, response),
                "risk_points": _client_risks(row, response),
            }
        )
    return {
        "brief": {
            "client_name": brief.client_name,
            "project_name": brief.project_name,
            "parsed_brief": brief.parsed_brief,
            "status": brief.status,
        },
        "counts": summary["counts"],
        "rates": summary["rates"],
        "candidates": visible,
    }


def _recipient_budget(brief: DistributionBrief, recipient_id: str) -> int:
    for recipient in brief.recipients:
        if recipient.recipient_id == recipient_id:
            return recipient.suggested_budget
    return 0


def _media_recommendation(row: dict[str, Any], response: dict[str, Any]) -> str:
    quote = response.get("quote") or 0
    suggested = row.get("suggested_budget") or 0
    if suggested and quote <= suggested:
        return "报价在建议预算内，可优先沟通。"
    if quote:
        return "有合作意向，但报价需与客户预算确认。"
    return "已表达意向，需补充报价。"


def _client_risks(row: dict[str, Any], response: dict[str, Any]) -> list[str]:
    risks = []
    if not response.get("availability"):
        risks.append("档期未明确")
    if not response.get("quote"):
        risks.append("报价未明确")
    suggested = row.get("suggested_budget") or 0
    if suggested and response.get("quote") and response["quote"] > suggested:
        risks.append("报价高于原建议预算")
    return risks


def _recipient_from_creator(brief_id: str, creator: CreatorProfile) -> DistributionRecipient:
    return DistributionRecipient(
        recipient_id=recipient_id_for(brief_id, creator.creator_id),
        brief_id=brief_id,
        creator_id=creator.creator_id,
        creator_name=creator.name,
        platform=creator.platform,
        suggested_budget=creator.listed_price,
    )


def _find_recipient(brief: DistributionBrief, recipient_id: str) -> DistributionRecipient:
    for recipient in brief.recipients:
        if recipient.recipient_id == recipient_id:
            return recipient
    raise KeyError("recipient not found")
