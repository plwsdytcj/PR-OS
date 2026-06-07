from __future__ import annotations

from pathlib import Path
from typing import Any

from src.collaboration.storage import load_all_proposals, load_feedback, load_preference
from src.knowledge.service import search_knowledge_base
from src.platform_os.storage import load_all_campaign_projects
from src.storage.db import load_profiles


def search_pr_knowledge(db_path: Path, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Lightweight local RAG placeholder.

    This searches existing structured OS memory before a pgvector-backed
    knowledge base is introduced.
    """
    terms = [item for item in query.lower().replace("，", " ").replace("。", " ").split() if item]
    docs: list[dict[str, Any]] = search_knowledge_base(db_path, query=query, top_k=top_k * 2)

    for proposal in load_all_proposals(db_path):
        text = f"{proposal.client_name} {proposal.project_name} {proposal.brief_text} {proposal.brief_summary}"
        docs.append(
            {
                "title": f"历史提案：{proposal.project_name}",
                "source": "proposal",
                "content": proposal.brief_summary or proposal.brief_text[:220],
                "score": _score(text, terms),
                "ref_id": proposal.proposal_id,
            }
        )
        preference = load_preference(db_path, proposal.client_id)
        if preference:
            docs.append(
                {
                    "title": f"客户偏好：{proposal.client_name}",
                    "source": "client_preference",
                    "content": preference.decision_notes or "暂无明确偏好",
                    "score": _score(" ".join([proposal.client_name, preference.decision_notes, *preference.preferred_platforms, *preference.rejected_patterns]), terms),
                    "ref_id": proposal.client_id,
                }
            )
        feedback = load_feedback(db_path, proposal.proposal_id)
        for item in feedback[:8]:
            docs.append(
                {
                    "title": f"甲方反馈：{proposal.project_name}",
                    "source": "client_feedback",
                    "content": item.comment or item.reason or item.decision,
                    "score": _score(f"{proposal.project_name} {item.comment} {item.reason} {item.decision}", terms),
                    "ref_id": item.feedback_id,
                }
            )

    for campaign in load_all_campaign_projects(db_path):
        text = f"{campaign.campaign.client_name} {campaign.campaign.project_name} {campaign.campaign.raw_brief}"
        docs.append(
            {
                "title": f"Campaign Room：{campaign.campaign.project_name}",
                "source": "campaign",
                "content": campaign.campaign.raw_brief[:240],
                "score": _score(text, terms),
                "ref_id": campaign.campaign.campaign_id,
            }
        )

    for profile in load_profiles(db_path)[:2000]:
        text = " ".join(
            [
                profile.name,
                profile.platform,
                profile.ai_summary,
                profile.bio,
                *profile.industry_fit_tags,
                *profile.content_capability_tags,
                *profile.suitable_goals,
                *profile.risk_tags,
            ]
        )
        score = _score(text, terms)
        if score:
            docs.append(
                {
                    "title": f"KOL 记忆：{profile.name}",
                    "source": "creator_profile",
                    "content": profile.ai_summary or profile.bio[:220],
                    "score": score,
                    "ref_id": profile.creator_id,
                }
            )

    docs.sort(key=lambda item: (item["score"], item["source"] != "creator_profile"), reverse=True)
    return docs[: max(1, top_k)]


def _score(text: str, terms: list[str]) -> float:
    if not terms:
        return 0.1
    lower = text.lower()
    score = 0.0
    for term in terms:
        if term and term in lower:
            score += 1.0
    return score
