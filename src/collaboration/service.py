from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.collaboration.schemas import (
    DEFAULT_VISIBLE_FIELDS,
    BrandPreferenceProfile,
    ClientFeedback,
    Proposal,
    ProposalCandidate,
    ProposalVersion,
    feedback_id_for,
    now_iso,
    proposal_id_for,
    version_id_for,
)
from src.collaboration.storage import load_feedback, load_preference, load_versions, upsert_feedback, upsert_preference
from src.intelligence.brief_parser import parse_brief
from src.intelligence.matching import rank_creators
from src.report.proposal_generator import generate_markdown_proposal
from src.schemas import CreatorProfile


def create_proposal_from_brief(
    db_path: Path,
    client_name: str,
    project_name: str,
    brief_text: str,
    creators: list[CreatorProfile],
    top_n: int = 12,
    created_by: str = "media_user",
) -> tuple[Proposal, ProposalVersion, str]:
    brief = parse_brief(brief_text)
    rankings = rank_creators(brief, creators)[:top_n]
    proposal_id = proposal_id_for(client_name, project_name)
    client_id = _client_id(client_name)
    proposal = Proposal(
        proposal_id=proposal_id,
        client_id=client_id,
        client_name=client_name,
        project_name=project_name,
        brief_text=brief_text,
        brief_summary=_brief_summary(brief_text),
        status="shared",
        created_by=created_by,
        visible_fields=dict(DEFAULT_VISIBLE_FIELDS),
    )
    candidates = [candidate_from_match(result) for result in rankings]
    version = ProposalVersion(
        version_id=version_id_for(proposal_id, 1),
        proposal_id=proposal_id,
        version_number=1,
        summary="v1 初版 AI 推荐",
        candidates=candidates,
        budget_total=sum(item.suggested_budget or item.listed_price for item in candidates),
    )
    markdown = generate_markdown_proposal(brief, rankings)
    return proposal, version, markdown


def candidate_from_match(result: Any) -> ProposalCandidate:
    creator = result.creator
    return ProposalCandidate(
        creator_id=creator.creator_id,
        creator_name=creator.name,
        platform=creator.platform,
        follower_count=creator.follower_count,
        listed_price=creator.listed_price,
        match_score=result.match_score,
        recommendation_level=result.recommendation_level,
        recommended_role=result.recommended_role,
        suggested_content=result.suggested_content,
        suggested_budget=result.suggested_budget,
        price_judgement=result.price_judgement,
        reasons=result.reasons,
        risk_points=result.risk_points,
        cooperation_brands=creator.cooperation_brands[:6],
        data_confidence=result.data_confidence,
    )


def public_proposal_payload(proposal: Proposal, version: ProposalVersion, feedback: list[ClientFeedback]) -> dict[str, Any]:
    visible = proposal.visible_fields or DEFAULT_VISIBLE_FIELDS
    feedback_by_creator = {item.target_id: item for item in feedback if item.target_type == "creator"}
    candidates = []
    for candidate in version.candidates:
        row = asdict(candidate)
        row["feedback"] = asdict(feedback_by_creator[candidate.creator_id]) if candidate.creator_id in feedback_by_creator else None
        candidates.append({key: value for key, value in row.items() if key in {"creator_id", "client_decision", "client_comment", "favorite", "feedback"} or visible.get(key, False)})
    return {
        "proposal": asdict(proposal) | {"share_url": proposal.public_url()},
        "version": version.to_dict(),
        "candidates": candidates,
        "feedback": [asdict(item) for item in feedback],
        "budget": {
            "total": version.budget_total,
            "approved": sum(item.suggested_budget or item.listed_price for item in version.candidates if item.client_decision == "approved"),
            "pending": sum(item.suggested_budget or item.listed_price for item in version.candidates if item.client_decision in {"pending", "maybe"}),
        },
    }


def record_feedback(
    db_path: Path,
    proposal: Proposal,
    version: ProposalVersion,
    target_type: str,
    target_id: str,
    decision: str = "",
    reason: str = "",
    comment: str = "",
    created_by: str = "client_user",
) -> ClientFeedback:
    feedback = ClientFeedback(
        feedback_id=feedback_id_for(proposal.proposal_id, target_id or target_type, f"{decision}|{reason}|{comment}"),
        proposal_id=proposal.proposal_id,
        version_id=version.version_id,
        target_type=target_type,
        target_id=target_id,
        decision=decision,
        reason=reason,
        comment=comment,
        created_by=created_by,
    )
    upsert_feedback(db_path, feedback)
    update_candidate_decision(version, target_id, decision, comment)
    update_preference_from_feedback(db_path, proposal, version)
    return feedback


def update_candidate_decision(version: ProposalVersion, creator_id: str, decision: str, comment: str) -> None:
    for candidate in version.candidates:
        if candidate.creator_id == creator_id:
            if decision:
                candidate.client_decision = decision
            if comment:
                candidate.client_comment = comment


def update_preference_from_feedback(db_path: Path, proposal: Proposal, version: ProposalVersion) -> BrandPreferenceProfile:
    feedback = load_feedback(db_path, proposal.proposal_id)
    approved_ids = {item.target_id for item in feedback if item.decision == "approved"}
    rejected = [item for item in feedback if item.decision == "rejected"]
    candidate_lookup = {item.creator_id: item for item in version.candidates}
    platforms = Counter(candidate_lookup[item].platform for item in approved_ids if item in candidate_lookup)
    creator_types = Counter(candidate_lookup[item].recommended_role for item in approved_ids if item in candidate_lookup)
    rejected_patterns = [item.reason or item.comment for item in rejected if item.reason or item.comment]
    preference = load_preference(db_path, proposal.client_id) or BrandPreferenceProfile(client_id=proposal.client_id, client_name=proposal.client_name)
    preference.preferred_platforms = [item for item, _ in platforms.most_common(5)] or preference.preferred_platforms
    preference.preferred_creator_types = [item for item, _ in creator_types.most_common(5)] or preference.preferred_creator_types
    preference.rejected_patterns = list(dict.fromkeys(preference.rejected_patterns + rejected_patterns))[:12]
    if len(rejected) >= 2:
        preference.risk_sensitivity = "high"
    if any("报价" in item for item in preference.rejected_patterns):
        preference.budget_sensitivity = "high"
    preference.decision_notes = _decision_notes(feedback)
    preference.updated_at = now_iso()
    upsert_preference(db_path, preference)
    return preference


def _client_id(client_name: str) -> str:
    from src.schemas import stable_id

    return stable_id(client_name, prefix="client")


def _brief_summary(text: str) -> str:
    return text.strip()[:180]


def _decision_notes(feedback: list[ClientFeedback]) -> str:
    approved = sum(1 for item in feedback if item.decision == "approved")
    rejected = sum(1 for item in feedback if item.decision == "rejected")
    maybe = sum(1 for item in feedback if item.decision == "maybe")
    return f"累计反馈：通过 {approved}，待定 {maybe}，拒绝 {rejected}。"
