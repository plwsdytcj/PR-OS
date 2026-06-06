from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from src.schemas import stable_id


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def response_token() -> str:
    return secrets.token_urlsafe(18)


@dataclass
class DistributionRecipient:
    recipient_id: str
    brief_id: str
    creator_id: str
    creator_name: str = ""
    platform: str = ""
    status: str = "queued"
    token: str = field(default_factory=response_token)
    pushed_at: str = ""
    viewed_at: str = ""
    responded_at: str = ""
    match_score: int = 0
    recommended_role: str = ""
    suggested_budget: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DistributionRecipient":
        return cls(**data)


@dataclass
class DistributionBrief:
    brief_id: str
    client_name: str
    project_name: str
    raw_brief: str
    parsed_brief: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"
    created_by: str = "media_user"
    created_at: str = field(default_factory=now_iso)
    pushed_at: str = ""
    recipients: list[DistributionRecipient] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "DistributionBrief":
        data = json.loads(value)
        data["recipients"] = [DistributionRecipient.from_dict(item) for item in data.get("recipients", [])]
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CreatorBriefResponse:
    response_id: str
    brief_id: str
    recipient_id: str
    creator_id: str
    interest: str = "interested"
    quote: int = 0
    availability: str = ""
    deliverables: str = ""
    content_direction: str = ""
    needs_sample: bool = False
    accepts_secondary_rights: bool = False
    accepts_revision: bool = True
    questions: str = ""
    constraints: str = ""
    decline_reason: str = ""
    media_note: str = ""
    status: str = "submitted"
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "CreatorBriefResponse":
        return cls(**json.loads(value))


def brief_id_for(client_name: str, project_name: str) -> str:
    return stable_id(client_name, project_name, now_iso(), prefix="brief")


def recipient_id_for(brief_id: str, creator_id: str) -> str:
    return stable_id(brief_id, creator_id, prefix="recipient")


def response_id_for(recipient_id: str, interest: str) -> str:
    return stable_id(recipient_id, interest, now_iso(), prefix="response")
