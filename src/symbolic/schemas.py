from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Evidence:
    claim: str
    source: str
    quote: str


@dataclass
class CreatorSymbolicProfile:
    creator_id: str
    creator_name: str = ""
    primary_tags: list[str] = field(default_factory=list)
    secondary_tags: list[str] = field(default_factory=list)
    persona_structure: str = ""
    emotional_tone: str = ""
    narrative_style: str = ""
    audience_fantasy: str = ""
    common_metaphors: list[str] = field(default_factory=list)
    common_metonymies: list[str] = field(default_factory=list)
    suitable_brand_types: list[str] = field(default_factory=list)
    unsuitable_brand_types: list[str] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    confidence: float = 0.0
    visibility: str = "internal"
    manual_status: str = "pending_review"
    content_sample: str = ""
    comment_sample: str = ""
    case_sample: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "CreatorSymbolicProfile":
        data = json.loads(value)
        data["evidence"] = [Evidence(**item) for item in data.get("evidence", [])]
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BrandSymbolicProfile:
    brand_id: str
    brand_name: str
    product: str = ""
    industry: str = ""
    current_tags: list[str] = field(default_factory=list)
    target_tags: list[str] = field(default_factory=list)
    danger_tags: list[str] = field(default_factory=list)
    emotional_value: list[str] = field(default_factory=list)
    identity_value: list[str] = field(default_factory=list)
    product_metaphors: list[str] = field(default_factory=list)
    product_metonymies: list[str] = field(default_factory=list)
    suitable_social_issues: list[str] = field(default_factory=list)
    unsafe_social_issues: list[str] = field(default_factory=list)
    suitable_creator_types: list[str] = field(default_factory=list)
    communication_path: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    confidence: float = 0.0
    raw_input: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "BrandSymbolicProfile":
        data = json.loads(value)
        data["evidence"] = [Evidence(**item) for item in data.get("evidence", [])]
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SymbolicMatchResult:
    creator_id: str
    creator_name: str
    symbolic_score: int
    recommendation_level: str
    domain_fit: int
    emotion_fit: int
    narrative_fit: int
    audience_fit: int
    metaphor_fit: int
    case_fit: int
    risk_control: int
    matched_brand_tags: list[str] = field(default_factory=list)
    metaphor_relation: str = ""
    metonymy_relation: str = ""
    match_reason: str = ""
    risk_points: list[str] = field(default_factory=list)
    suggested_content_direction: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    needs_manual_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NarrativePath:
    project: str
    creator_id: str
    creator_name: str
    start_tag: str
    mediating_tags: list[str]
    target_tag: str
    narrative_path: str
    metaphor_strategy: str
    metonymy_strategy: str
    title_directions: list[str]
    must_include: list[str]
    must_avoid: list[str]
    comment_guidance: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
