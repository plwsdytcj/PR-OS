from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def stable_id(*parts: object, prefix: str = "creator") -> str:
    raw = "|".join(str(p or "").strip().lower() for p in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def split_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    for sep in ["，", "、", ";", "；", "|", "\n"]:
        text = text.replace(sep, ",")
    return [item.strip() for item in text.split(",") if item.strip()]


@dataclass
class CreatorProfile:
    creator_id: str
    name: str
    platform: str = "未知"
    platform_user_id: str = ""
    homepage_url: str = ""
    avatar_url: str = ""
    bio: str = ""
    region: str = ""
    follower_count: int = 0
    following_count: int = 0
    total_likes: int = 0
    recent_posts_count: int = 0
    avg_likes: int = 0
    avg_comments: int = 0
    avg_shares: int = 0
    avg_collections: int = 0
    engagement_rate: float = 0.0
    listed_price: int = 0
    price_source: str = ""
    contact: str = ""
    cooperation_brands: list[str] = field(default_factory=list)
    cooperation_formats: list[str] = field(default_factory=list)
    delivery_rating: float = 0.0
    communication_rating: float = 0.0
    negotiation_space: str = ""
    manual_notes: str = ""
    data_sources: list[str] = field(default_factory=list)
    industry_fit_tags: list[str] = field(default_factory=list)
    content_capability_tags: list[str] = field(default_factory=list)
    suitable_goals: list[str] = field(default_factory=list)
    suitable_stages: list[str] = field(default_factory=list)
    budget_fit_tags: list[str] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)
    ai_summary: str = ""
    last_synced_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))

    def merge(self, other: "CreatorProfile") -> "CreatorProfile":
        """Merge another profile using manual/internal values where present."""
        data = asdict(self)
        incoming = asdict(other)
        for key, value in incoming.items():
            if key in {"creator_id"}:
                continue
            if isinstance(value, list):
                data[key] = sorted(set(data.get(key, []) + value))
            elif isinstance(value, (int, float)):
                if value:
                    data[key] = value
            elif value:
                if key in {"listed_price", "manual_notes", "contact"} or not data.get(key):
                    data[key] = value
        data["last_synced_at"] = datetime.utcnow().isoformat(timespec="seconds")
        return CreatorProfile(**data)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "CreatorProfile":
        return cls(**json.loads(value))


@dataclass
class BrandBrief:
    raw_text: str
    industry: str = ""
    product: str = ""
    budget: int = 0
    campaign_stage: str = ""
    goals: list[str] = field(default_factory=list)
    target_audience: list[str] = field(default_factory=list)
    platform_preference: list[str] = field(default_factory=list)
    content_preference: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "BrandBrief":
        return cls(**json.loads(value))


@dataclass
class MatchResult:
    creator: CreatorProfile
    match_score: int
    recommendation_level: str
    recommended_role: str
    suggested_content: str
    suggested_budget: int
    price_judgement: str
    reasons: list[str]
    risk_points: list[str]
    data_confidence: str
    needs_manual_review: bool = False

    def to_table_row(self) -> dict[str, Any]:
        return {
            "达人": self.creator.name,
            "平台": self.creator.platform,
            "匹配分": self.match_score,
            "等级": self.recommendation_level,
            "推荐角色": self.recommended_role,
            "建议预算": self.suggested_budget,
            "报价判断": self.price_judgement,
            "推荐理由": "；".join(self.reasons),
            "风险提示": "；".join(self.risk_points),
            "数据可信度": self.data_confidence,
            "需人工核验": "是" if self.needs_manual_review else "否",
        }

    def to_json(self) -> str:
        data = asdict(self)
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "MatchResult":
        data = json.loads(value)
        data["creator"] = CreatorProfile(**data["creator"])
        return cls(**data)
