from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.schemas import stable_id, split_tags


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


@dataclass
class ClientCardRecord:
    card_id: str
    client_name: str
    industry: str = ""
    decision_maker: str = ""
    contact_person: str = ""
    budget_range: str = ""
    demand_type: str = ""
    product_service: str = ""
    product_facts: str = ""
    brand_meaning: str = ""
    target_audience: str = ""
    required_platforms: str = ""
    must_say: str = ""
    must_not_say: str = ""
    proof_evidence: str = ""
    deadline: str = ""
    payment_status: str = ""
    risk_notes: str = ""
    settlement_target: str = ""
    next_action: str = ""
    brief_excerpt: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClientCardRecord":
        payload = dict(data)
        payload.setdefault("tags", [])
        return cls(**payload)


def card_id_for(client_name: str) -> str:
    return stable_id(client_name, prefix="client_card")


def normalize_client_card_payload(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get("client_name") or "").strip()
    if not name:
        raise ValueError("client_name is required")
    card_id = str(data.get("card_id") or card_id_for(name)).strip()
    return {
        "card_id": card_id,
        "client_name": name,
        "industry": str(data.get("industry") or "").strip(),
        "decision_maker": str(data.get("decision_maker") or "").strip(),
        "contact_person": str(data.get("contact_person") or "").strip(),
        "budget_range": str(data.get("budget_range") or "").strip(),
        "demand_type": str(data.get("demand_type") or "").strip(),
        "product_service": str(data.get("product_service") or "").strip(),
        "product_facts": str(data.get("product_facts") or "").strip(),
        "brand_meaning": str(data.get("brand_meaning") or "").strip(),
        "target_audience": str(data.get("target_audience") or "").strip(),
        "required_platforms": str(data.get("required_platforms") or "").strip(),
        "must_say": str(data.get("must_say") or "").strip(),
        "must_not_say": str(data.get("must_not_say") or "").strip(),
        "proof_evidence": str(data.get("proof_evidence") or "").strip(),
        "deadline": str(data.get("deadline") or "").strip(),
        "payment_status": str(data.get("payment_status") or "").strip(),
        "risk_notes": str(data.get("risk_notes") or "").strip(),
        "settlement_target": str(data.get("settlement_target") or "").strip(),
        "next_action": str(data.get("next_action") or "").strip(),
        "brief_excerpt": str(data.get("brief_excerpt") or "").strip(),
        "tags": split_tags(data.get("tags")),
    }
