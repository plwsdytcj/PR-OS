from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from src.schemas import stable_id


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def document_id_for(title: str, content: str, source_type: str = "manual") -> str:
    return stable_id(title.strip(), content.strip()[:500], source_type, prefix="knowledge_doc")


def chunk_id_for(document_id: str, index: int, content: str) -> str:
    return stable_id(document_id, index, content.strip()[:240], prefix="knowledge_chunk")


@dataclass
class KnowledgeDocument:
    document_id: str
    title: str
    source_type: str = "manual"
    source_ref: str = ""
    client_id: str = ""
    project_id: str = ""
    industry: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = "active"
    chunk_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "KnowledgeDocument":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    title: str
    content: str
    embedding: list[float] = field(default_factory=list)
    token_estimate: int = 0
    source_type: str = "manual"
    client_id: str = ""
    project_id: str = ""
    industry: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "KnowledgeChunk":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
