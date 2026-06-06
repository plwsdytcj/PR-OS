from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from src.schemas import stable_id


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


@dataclass
class CampaignProfile:
    campaign_id: str
    client_name: str
    project_name: str
    raw_brief: str
    industry: str = ""
    product: str = ""
    budget: int = 0
    stage: str = ""
    goals: list[str] = field(default_factory=list)
    target_audience: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    content_preferences: list[str] = field(default_factory=list)
    risk_sensitivity: str = "medium"
    status: str = "strategy_generated"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "CampaignProfile":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CampaignPlan:
    plan_id: str
    campaign_id: str
    plan_name: str
    strategy_summary: str
    creator_ids: list[str] = field(default_factory=list)
    creator_names: list[str] = field(default_factory=list)
    budget_allocation: dict[str, int] = field(default_factory=dict)
    content_directions: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    risk_points: list[str] = field(default_factory=list)
    risk_level: str = "medium"
    execution_score: int = 0
    is_recommended: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignPlan":
        return cls(**data)


@dataclass
class CampaignSimulation:
    simulation_id: str
    campaign_id: str
    plan_id: str
    summary: str
    positive_reactions: list[str] = field(default_factory=list)
    negative_reactions: list[str] = field(default_factory=list)
    risk_points: list[str] = field(default_factory=list)
    optimization_suggestions: list[str] = field(default_factory=list)
    simulation_report: dict[str, Any] = field(default_factory=dict)
    disclaimer: str = "投放前推演仅用于辅助决策，不预测真实 ROI。"
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignSimulation":
        return cls(**data)


@dataclass
class PostCampaignReview:
    review_id: str
    campaign_id: str
    creator_id: str
    content_url: str = ""
    actual_price: int = 0
    views: int = 0
    likes: int = 0
    comments: int = 0
    brand_feedback: str = ""
    comment_feedback: str = ""
    delivery_rating: float = 0.0
    case_status: str = "approved_case"
    visibility: str = "client_summary"
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PostCampaignReview":
        return cls(**data)


@dataclass
class CampaignProject:
    campaign: CampaignProfile
    plans: list[CampaignPlan] = field(default_factory=list)
    simulations: list[CampaignSimulation] = field(default_factory=list)
    reviews: list[PostCampaignReview] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    archived: bool = False

    def to_json(self) -> str:
        return json.dumps(
            {
                "campaign": self.campaign.to_dict(),
                "plans": [item.to_dict() for item in self.plans],
                "simulations": [item.to_dict() for item in self.simulations],
                "reviews": [item.to_dict() for item in self.reviews],
                "timeline": self.timeline,
                "archived": self.archived,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, value: str) -> "CampaignProject":
        data = json.loads(value)
        return cls(
            campaign=CampaignProfile(**data["campaign"]),
            plans=[CampaignPlan.from_dict(item) for item in data.get("plans", [])],
            simulations=[CampaignSimulation.from_dict(item) for item in data.get("simulations", [])],
            reviews=[PostCampaignReview.from_dict(item) for item in data.get("reviews", [])],
            timeline=data.get("timeline", []),
            archived=bool(data.get("archived", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return json.loads(self.to_json())


def campaign_id_for(client_name: str, project_name: str) -> str:
    return stable_id(client_name, project_name, now_iso(), prefix="campaign")


def plan_id_for(campaign_id: str, plan_name: str) -> str:
    return stable_id(campaign_id, plan_name, prefix="plan")


def simulation_id_for(plan_id: str) -> str:
    return stable_id(plan_id, now_iso(), prefix="simulation")


def review_id_for(campaign_id: str, creator_id: str, content_url: str = "") -> str:
    return stable_id(campaign_id, creator_id, content_url, now_iso(), prefix="review")
