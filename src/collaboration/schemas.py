from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.schemas import stable_id


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def default_expires_at(days: int = 14) -> str:
    return (datetime.utcnow() + timedelta(days=days)).isoformat(timespec="seconds")


def share_token() -> str:
    return secrets.token_urlsafe(18)


DEFAULT_VISIBLE_FIELDS = {
    "creator_name": True,
    "platform": True,
    "follower_count": True,
    "listed_price": True,
    "match_score": True,
    "recommendation_level": True,
    "recommended_role": True,
    "suggested_content": True,
    "suggested_budget": True,
    "reasons": True,
    "risk_points": True,
    "cooperation_brands": True,
    "data_confidence": True,
    "contact": False,
    "manual_notes": False,
    "price_source": False,
}


@dataclass
class ProposalCandidate:
    creator_id: str
    creator_name: str
    platform: str = ""
    follower_count: int = 0
    listed_price: int = 0
    match_score: int = 0
    recommendation_level: str = ""
    recommended_role: str = ""
    suggested_content: str = ""
    suggested_budget: int = 0
    price_judgement: str = ""
    reasons: list[str] = field(default_factory=list)
    risk_points: list[str] = field(default_factory=list)
    cooperation_brands: list[str] = field(default_factory=list)
    data_confidence: str = ""
    client_decision: str = "pending"
    client_comment: str = ""
    favorite: bool = False


@dataclass
class ProposalVersion:
    version_id: str
    proposal_id: str
    version_number: int
    summary: str
    candidates: list[ProposalCandidate] = field(default_factory=list)
    budget_total: int = 0
    created_at: str = field(default_factory=now_iso)
    is_final: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProposalVersion":
        data["candidates"] = [ProposalCandidate(**item) for item in data.get("candidates", [])]
        return cls(**data)


@dataclass
class Proposal:
    proposal_id: str
    client_id: str
    client_name: str
    project_name: str
    brief_text: str
    brief_summary: str = ""
    status: str = "draft"
    current_version: int = 1
    created_by: str = "media_user"
    visible_fields: dict[str, bool] = field(default_factory=lambda: dict(DEFAULT_VISIBLE_FIELDS))
    share_token: str = field(default_factory=share_token)
    share_enabled: bool = True
    expires_at: str = field(default_factory=default_expires_at)
    allow_comments: bool = True
    allow_download: bool = True
    access_count: int = 0
    last_accessed_at: str = ""
    confirmed_at: str = ""
    confirmed_by: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "Proposal":
        return cls(**json.loads(value))

    def public_url(self) -> str:
        return f"/?share={self.share_token}"


@dataclass
class ClientFeedback:
    feedback_id: str
    proposal_id: str
    version_id: str
    target_type: str = "proposal"
    target_id: str = ""
    status: str = "open"
    decision: str = ""
    reason: str = ""
    comment: str = ""
    created_by: str = "client_user"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "ClientFeedback":
        return cls(**json.loads(value))


@dataclass
class BrandPreferenceProfile:
    client_id: str
    client_name: str = ""
    preferred_platforms: list[str] = field(default_factory=list)
    preferred_creator_types: list[str] = field(default_factory=list)
    rejected_patterns: list[str] = field(default_factory=list)
    budget_sensitivity: str = "medium"
    risk_sensitivity: str = "medium"
    preferred_content_style: list[str] = field(default_factory=list)
    decision_notes: str = ""
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "BrandPreferenceProfile":
        return cls(**json.loads(value))


def proposal_id_for(client_name: str, project_name: str) -> str:
    return stable_id(client_name, project_name, now_iso(), prefix="proposal")


def version_id_for(proposal_id: str, version_number: int) -> str:
    return f"{proposal_id}_v{version_number}"


def feedback_id_for(proposal_id: str, target_id: str, comment: str) -> str:
    return stable_id(proposal_id, target_id, comment, now_iso(), prefix="feedback")
