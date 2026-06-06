from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from src.schemas import stable_id


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


@dataclass
class SocialSymbolicIssue:
    issue: str
    keywords: list[str] = field(default_factory=list)
    core_emotion: str = ""
    symptom: str = ""
    public_fantasy: str = ""
    rupture_point: str = ""
    opportunity: str = ""
    risk_direction: str = ""
    suitable_brand_types: list[str] = field(default_factory=list)
    suitable_creator_types: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SocialSymbolicReport:
    report_id: str
    period: str
    title: str
    raw_input: str = ""
    overall_symptom: str = ""
    mood_map: list[str] = field(default_factory=list)
    issues: list[SocialSymbolicIssue] = field(default_factory=list)
    borrowable_directions: list[str] = field(default_factory=list)
    high_risk_directions: list[str] = field(default_factory=list)
    brand_implications: list[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "SocialSymbolicReport":
        data = json.loads(value)
        data["issues"] = [SocialSymbolicIssue(**item) for item in data.get("issues", [])]
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SignifierTag:
    tag_id: str
    name: str
    tag_type: str = "传播标签"
    parent: str = ""
    children: list[str] = field(default_factory=list)
    related_tags: list[str] = field(default_factory=list)
    opposite_tags: list[str] = field(default_factory=list)
    metaphor_relations: list[str] = field(default_factory=list)
    metonymy_relations: list[str] = field(default_factory=list)
    emotion: str = ""
    suitable_industries: list[str] = field(default_factory=list)
    suitable_creator_types: list[str] = field(default_factory=list)
    suitable_content_forms: list[str] = field(default_factory=list)
    risk_notes: str = ""
    examples: list[str] = field(default_factory=list)
    source: str = "system"
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "SignifierTag":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductSymbolicProfile:
    product_id: str
    brand_id: str = ""
    brand_name: str = ""
    product_name: str = ""
    category: str = ""
    physical_attributes: list[str] = field(default_factory=list)
    use_scenarios: list[str] = field(default_factory=list)
    target_users: list[str] = field(default_factory=list)
    functional_value: list[str] = field(default_factory=list)
    emotional_value: list[str] = field(default_factory=list)
    identity_value: list[str] = field(default_factory=list)
    metaphors: list[str] = field(default_factory=list)
    metonymies: list[str] = field(default_factory=list)
    association_words: list[str] = field(default_factory=list)
    anti_association_words: list[str] = field(default_factory=list)
    suitable_content_scenarios: list[str] = field(default_factory=list)
    suitable_creator_types: list[str] = field(default_factory=list)
    unsuitable_creator_types: list[str] = field(default_factory=list)
    social_issue_hooks: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = "generated"
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "ProductSymbolicProfile":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContentNarrativeAsset:
    narrative_id: str
    project: str = ""
    brand_id: str = ""
    brand_name: str = ""
    product_id: str = ""
    product_name: str = ""
    creator_id: str = ""
    creator_name: str = ""
    target_tag: str = ""
    start_tag: str = ""
    mediating_tags: list[str] = field(default_factory=list)
    narrative_path: str = ""
    metaphor_strategy: str = ""
    metonymy_strategy: str = ""
    emotion_strategy: str = ""
    title_directions: list[str] = field(default_factory=list)
    content_brief: str = ""
    suitable_creator_types: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    must_avoid: list[str] = field(default_factory=list)
    comment_guidance: str = ""
    risk_words: list[str] = field(default_factory=list)
    client_status: str = "draft"
    source: str = "symbolic_match"
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "ContentNarrativeAsset":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BrandCreatorMatchAsset:
    match_id: str
    brand_id: str = ""
    brand_name: str = ""
    product_id: str = ""
    product_name: str = ""
    creator_id: str = ""
    creator_name: str = ""
    symbolic_score: int = 0
    recommendation_level: str = ""
    domain_fit: int = 0
    emotion_fit: int = 0
    narrative_fit: int = 0
    audience_fit: int = 0
    metaphor_fit: int = 0
    case_fit: int = 0
    risk_control: int = 0
    matched_brand_tags: list[str] = field(default_factory=list)
    metaphor_relation: str = ""
    metonymy_relation: str = ""
    emotion_relation: str = ""
    audience_relation: str = ""
    case_basis: list[str] = field(default_factory=list)
    match_reason: str = ""
    risk_points: list[str] = field(default_factory=list)
    suggested_content_direction: str = ""
    suggested_priority: str = "pending"
    manual_status: str = "pending_review"
    client_status: str = "not_shared"
    evidence: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "BrandCreatorMatchAsset":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackCorrection:
    correction_id: str
    campaign_id: str
    creator_id: str
    review_id: str
    assumed_tags: list[str] = field(default_factory=list)
    activated_tags: list[str] = field(default_factory=list)
    missing_tags: list[str] = field(default_factory=list)
    misread_points: list[str] = field(default_factory=list)
    creator_tag_updates: list[str] = field(default_factory=list)
    brand_tag_updates: list[str] = field(default_factory=list)
    next_suggestion: str = ""
    confidence_delta: float = 0.0
    evidence_summary: str = ""
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "FeedbackCorrection":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def report_id_for(period: str, raw_input: str) -> str:
    return stable_id(period, raw_input[:120], now_iso(), prefix="social")


def tag_id_for(name: str, tag_type: str = "") -> str:
    return stable_id(name, tag_type, prefix="tag")


def product_id_for(brand_name: str, product_name: str) -> str:
    return stable_id(brand_name, product_name, prefix="product")


def narrative_id_for(project: str, brand_id: str, creator_id: str, target_tag: str) -> str:
    return stable_id(project, brand_id, creator_id, target_tag, now_iso(), prefix="narrative")


def match_id_for(brand_id: str, product_id: str, creator_id: str) -> str:
    return stable_id(brand_id, product_id, creator_id, now_iso(), prefix="match")


def correction_id_for(campaign_id: str, creator_id: str, review_id: str) -> str:
    return stable_id(campaign_id, creator_id, review_id, prefix="correction")
