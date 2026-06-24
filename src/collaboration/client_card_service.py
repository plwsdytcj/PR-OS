from __future__ import annotations

from pathlib import Path
from typing import Any

from src.collaboration.client_cards import ClientCardRecord, normalize_client_card_payload, now_iso
from src.collaboration.storage import delete_client_card, load_all_client_cards, load_client_card, upsert_client_card


def list_client_cards(db_path: Path, query: str = "") -> list[ClientCardRecord]:
    items = load_all_client_cards(db_path)
    needle = query.strip().lower()
    if not needle:
        return items
    filtered: list[ClientCardRecord] = []
    for card in items:
        text = " ".join(
            [
                card.client_name,
                card.industry,
                card.product_service,
                card.demand_type,
                card.target_audience,
                " ".join(card.tags),
            ]
        ).lower()
        if needle in text:
            filtered.append(card)
    return filtered


def save_client_card(db_path: Path, payload: dict[str, Any]) -> ClientCardRecord:
    normalized = normalize_client_card_payload(payload)
    existing = load_client_card(db_path, normalized["card_id"])
    card = ClientCardRecord(
        **normalized,
        created_at=existing.created_at if existing else now_iso(),
        updated_at=now_iso(),
    )
    upsert_client_card(db_path, card)
    return card


def remove_client_card(db_path: Path, card_id: str) -> bool:
    existing = load_client_card(db_path, card_id)
    if existing is None:
        return False
    delete_client_card(db_path, card_id)
    return True
