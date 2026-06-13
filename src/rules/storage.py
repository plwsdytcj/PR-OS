from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path
from typing import Any

from src.storage.postgres_payload import fetch_payload, postgres_enabled, upsert_payload

RULE_CONFIG_ID = "default"


def init_rule_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rule_configs (
                config_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def default_rule_config() -> dict[str, Any]:
    from src.kol_intelligence.service import BRIEF_KEYWORDS, CATEGORY_LABELS
    from src.symbolic.brand_profiler import BRAND_ARCHETYPES
    from src.symbolic.creator_profiler import SYMBOLIC_PATTERNS

    return {
        "version": 1,
        "creator_symbolic_patterns": copy.deepcopy(SYMBOLIC_PATTERNS),
        "brief_keywords": copy.deepcopy(BRIEF_KEYWORDS),
        "category_labels": copy.deepcopy(CATEGORY_LABELS),
        "brand_archetypes": copy.deepcopy(BRAND_ARCHETYPES),
    }


def load_rule_config(path: Path) -> dict[str, Any]:
    defaults = default_rule_config()
    payload = _load_payload(path)
    if not payload:
        return defaults
    return _deep_merge(defaults, payload)


def save_rule_config(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("rule config must be a JSON object")
    merged = _deep_merge(default_rule_config(), payload)
    _validate_rule_config(merged)
    if postgres_enabled():
        upsert_payload(path, "rule_configs", "config_id", RULE_CONFIG_ID, merged)
    else:
        init_rule_db(path)
        with sqlite3.connect(path) as conn:
            conn.execute(
                """
                INSERT INTO rule_configs (config_id, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(config_id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (RULE_CONFIG_ID, json.dumps(merged, ensure_ascii=False)),
            )
    return merged


def reset_rule_config(path: Path) -> dict[str, Any]:
    defaults = default_rule_config()
    if postgres_enabled():
        upsert_payload(path, "rule_configs", "config_id", RULE_CONFIG_ID, defaults)
    else:
        init_rule_db(path)
        with sqlite3.connect(path) as conn:
            conn.execute(
                """
                INSERT INTO rule_configs (config_id, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(config_id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (RULE_CONFIG_ID, json.dumps(defaults, ensure_ascii=False)),
            )
    return defaults


def _load_payload(path: Path) -> dict[str, Any]:
    if postgres_enabled():
        payload = fetch_payload(path, "rule_configs", "config_id", RULE_CONFIG_ID)
        return json.loads(payload) if payload else {}
    init_rule_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM rule_configs WHERE config_id = ?", (RULE_CONFIG_ID,)).fetchone()
    return json.loads(row[0]) if row else {}


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in (patch or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validate_rule_config(config: dict[str, Any]) -> None:
    required = ["creator_symbolic_patterns", "brief_keywords", "category_labels", "brand_archetypes"]
    for key in required:
        if not isinstance(config.get(key), dict):
            raise ValueError(f"{key} must be an object")
    for pattern_name, pattern in config["creator_symbolic_patterns"].items():
        if not isinstance(pattern, dict) or not isinstance(pattern.get("keywords"), list):
            raise ValueError(f"creator_symbolic_patterns.{pattern_name}.keywords must be an array")
    for label, keywords in config["brief_keywords"].items():
        if not isinstance(keywords, list):
            raise ValueError(f"brief_keywords.{label} must be an array")
