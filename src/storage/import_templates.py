from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def load_templates(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return list(data.get("templates", []))


def save_templates(path: Path, templates: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump({"templates": templates}, handle, ensure_ascii=False, indent=2)


def upsert_template(path: Path, name: str, sheets: dict[str, Any], template_id: str | None = None) -> dict[str, Any]:
    templates = load_templates(path)
    now = datetime.utcnow().isoformat(timespec="seconds")
    existing = next((item for item in templates if item.get("id") == template_id), None)
    if existing is None:
        existing = {
            "id": template_id or f"tpl_{uuid.uuid4().hex[:12]}",
            "name": name.strip() or "未命名导入模板",
            "created_at": now,
        }
        templates.append(existing)
    existing["name"] = name.strip() or existing.get("name") or "未命名导入模板"
    existing["updated_at"] = now
    existing["sheets"] = _normalize_sheets(sheets)
    save_templates(path, templates)
    return existing


def delete_template(path: Path, template_id: str) -> bool:
    templates = load_templates(path)
    next_templates = [item for item in templates if item.get("id") != template_id]
    if len(next_templates) == len(templates):
        return False
    save_templates(path, next_templates)
    return True


def find_best_template(templates: list[dict[str, Any]], tables: dict[str, Any]) -> tuple[dict[str, Any] | None, int]:
    best_template = None
    best_score = 0
    for template in templates:
        score = score_template(template, tables)
        if score > best_score:
            best_score = score
            best_template = template
    return (best_template, best_score) if best_score >= 20 else (None, best_score)


def apply_template_mapping(sheet_name: str, columns: list[str], detected_mapping: dict[str, str], template: dict[str, Any] | None) -> tuple[dict[str, str], str]:
    if not template:
        return detected_mapping, ""
    template_sheet = _find_template_sheet(template, sheet_name)
    if not template_sheet:
        return detected_mapping, ""
    valid_columns = set(map(str, columns))
    mapping = dict(detected_mapping)
    for field, column in template_sheet.get("mapping", {}).items():
        if str(column) in valid_columns:
            mapping[field] = str(column)
    return mapping, str(template.get("name") or "")


def score_template(template: dict[str, Any], tables: dict[str, Any]) -> int:
    score = 0
    template_sheets = template.get("sheets", {})
    for sheet_name, df in tables.items():
        template_sheet = _find_template_sheet(template, str(sheet_name))
        if not template_sheet:
            continue
        score += 10
        columns = set(map(str, getattr(df, "columns", [])))
        score += sum(2 for column in template_sheet.get("mapping", {}).values() if str(column) in columns)
        if str(sheet_name) in template_sheets:
            score += 8
    return score


def _normalize_sheets(sheets: dict[str, Any]) -> dict[str, Any]:
    normalized = {}
    for sheet_name, config in sheets.items():
        if not isinstance(config, dict):
            continue
        mapping = config.get("mapping", {})
        normalized[str(sheet_name)] = {
            "enabled": config.get("enabled") is not False,
            "sheet_key": _sheet_key(str(sheet_name)),
            "mapping": {str(field): str(column) for field, column in mapping.items() if column},
        }
    return normalized


def _find_template_sheet(template: dict[str, Any], sheet_name: str) -> dict[str, Any] | None:
    sheets = template.get("sheets", {})
    if sheet_name in sheets:
        return sheets[sheet_name]
    key = _sheet_key(sheet_name)
    for config in sheets.values():
        if config.get("sheet_key") == key:
            return config
    return None


def _sheet_key(sheet_name: str) -> str:
    return re.sub(r"\s+", "", sheet_name).lower()
