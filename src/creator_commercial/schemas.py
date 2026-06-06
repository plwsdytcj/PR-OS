from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.schemas import stable_id


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def expires_at(days: int = 14) -> str:
    return (datetime.utcnow() + timedelta(days=days)).isoformat(timespec="seconds")


def invite_token() -> str:
    return secrets.token_urlsafe(18)


@dataclass
class CreatorInvitation:
    invitation_id: str
    creator_id: str
    creator_name: str = ""
    invited_by: str = "media_user"
    status: str = "sent"
    token: str = field(default_factory=invite_token)
    expires_at: str = field(default_factory=expires_at)
    created_at: str = field(default_factory=now_iso)
    opened_at: str = ""
    submitted_at: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "CreatorInvitation":
        return cls(**json.loads(value))


@dataclass
class CreatorCase:
    case_id: str
    creator_id: str
    brand_name: str
    industry: str = ""
    platform: str = ""
    content_format: str = ""
    content_url: str = ""
    cooperation_goal: str = ""
    performance: dict[str, Any] = field(default_factory=dict)
    comment_feedback: str = ""
    visibility: str = "client_summary"
    verification_status: str = "pending_review"
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreatorCase":
        return cls(**data)


@dataclass
class CreatorSubmission:
    submission_id: str
    creator_id: str
    invitation_id: str
    profile_fields: dict[str, Any] = field(default_factory=dict)
    cases: list[CreatorCase] = field(default_factory=list)
    ai_profile: dict[str, Any] = field(default_factory=dict)
    creator_note: str = ""
    status: str = "pending_review"
    created_at: str = field(default_factory=now_iso)
    reviewed_at: str = ""
    reviewed_by: str = ""

    def to_json(self) -> str:
        data = asdict(self)
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "CreatorSubmission":
        data = json.loads(value)
        data["cases"] = [CreatorCase.from_dict(item) for item in data.get("cases", [])]
        return cls(**data)


@dataclass
class CreatorCommercialProfile:
    creator_id: str
    commercial_positioning: str = ""
    industry_fit_tags: list[str] = field(default_factory=list)
    content_capability_tags: list[str] = field(default_factory=list)
    suitable_stages: list[str] = field(default_factory=list)
    suitable_goals: list[str] = field(default_factory=list)
    cooperation_preferences: list[str] = field(default_factory=list)
    unavailable_types: list[str] = field(default_factory=list)
    price_range: str = ""
    availability: str = ""
    case_summaries: list[str] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)
    profile_confidence: str = "medium"
    reviewed_by: str = ""
    visibility: str = "internal"
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "CreatorCommercialProfile":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def invitation_id_for(creator_id: str) -> str:
    return stable_id(creator_id, now_iso(), prefix="invite")


def submission_id_for(invitation_id: str) -> str:
    return stable_id(invitation_id, now_iso(), prefix="submission")


def case_id_for(creator_id: str, brand_name: str) -> str:
    return stable_id(creator_id, brand_name, now_iso(), prefix="case")
