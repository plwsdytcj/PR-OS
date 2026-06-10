from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from src.schemas import stable_id


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


@dataclass
class KolEvidenceTag:
    tag_id: str
    creator_id: str
    creator_name: str = ""
    tag: str = ""
    category: str = "general"
    confidence: float = 0.0
    score: int = 0
    source_type: str = "profile"
    source: str = ""
    evidence: list[str] = field(default_factory=list)
    status: str = "suggested"
    version: int = 1
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "KolEvidenceTag":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KolGraphSnapshot:
    snapshot_id: str
    brief: str = ""
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    evolution: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "KolGraphSnapshot":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KolPrediction:
    prediction_id: str
    brief: str
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    activated_tags: list[dict[str, Any]] = field(default_factory=list)
    graph: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "KolPrediction":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evidence_tag_id(creator_id: str, tag: str, category: str) -> str:
    return stable_id(creator_id, tag, category, prefix="ktag")


def graph_snapshot_id(brief: str, size: int) -> str:
    return stable_id(brief[:160], size, now_iso(), prefix="kgraph")


def prediction_id_for(brief: str, top_n: int) -> str:
    return stable_id(brief[:240], top_n, now_iso(), prefix="kpred")
