from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse

from src.schemas import CreatorProfile


def normalize_name(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[_\-｜|·.。]", "", text)
    return text


def normalize_platform(value: str) -> str:
    return str(value or "未知").strip().lower()


def normalize_url(value: str) -> str:
    text = str(value or "").strip()
    if not _usable_key(text):
        return ""
    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def strong_dedupe_profiles(profiles: list[CreatorProfile]) -> tuple[list[CreatorProfile], dict[str, Any]]:
    """Merge profiles that are very likely the same platform account."""
    merged: list[CreatorProfile] = []
    indexes: dict[str, dict[str, int]] = {
        "platform_id": {},
        "platform_url": {},
        "platform_name": {},
    }
    merge_events = []

    for profile in profiles:
        keys = _strong_keys(profile)
        target_idx = next((indexes[kind][key] for kind, key in keys if key in indexes[kind]), None)
        if target_idx is None:
            target_idx = len(merged)
            merged.append(profile)
        else:
            original = merged[target_idx]
            merged[target_idx] = original.merge(profile)
            merge_events.append(
                {
                    "kept_creator_id": original.creator_id,
                    "merged_creator_id": profile.creator_id,
                    "name": profile.name,
                    "platform": profile.platform,
                }
            )
        for kind, key in _strong_keys(merged[target_idx]):
            indexes[kind][key] = target_idx

    return merged, {"auto_merged": len(merge_events), "merge_events": merge_events}


def find_duplicate_candidates(profiles: list[CreatorProfile], limit: int = 100) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    by_name: dict[str, list[CreatorProfile]] = defaultdict(list)
    for profile in profiles:
        name_key = normalize_name(profile.name)
        if name_key:
            by_name[name_key].append(profile)

    for group in by_name.values():
        if len(group) < 2:
            continue
        for left_idx, left in enumerate(group):
            for right in group[left_idx + 1 :]:
                candidates.append(_duplicate_candidate(left, right, "同名跨平台或多来源", 86, seen_pairs))

    for left_idx, left in enumerate(profiles):
        if not left.name:
            continue
        for right in profiles[left_idx + 1 :]:
            if normalize_platform(left.platform) == normalize_platform(right.platform):
                continue
            ratio = SequenceMatcher(None, normalize_name(left.name), normalize_name(right.name)).ratio()
            if ratio >= 0.92:
                candidates.append(_duplicate_candidate(left, right, "名称高度相似", int(ratio * 100), seen_pairs))

    return [item for item in candidates if item][:limit]


def quality_issues(profiles: list[CreatorProfile], limit: int = 200) -> list[dict[str, Any]]:
    issues = []
    for profile in profiles:
        missing = []
        if not profile.follower_count:
            missing.append("缺粉丝数")
        if not profile.listed_price:
            missing.append("缺报价")
        if not profile.homepage_url:
            missing.append("缺主页链接")
        if not profile.bio:
            missing.append("缺简介")
        warnings = []
        if profile.follower_count and profile.follower_count < 100:
            warnings.append("粉丝数疑似未按万转换")
        if profile.listed_price and profile.listed_price > 5_000_000:
            warnings.append("报价异常偏高")
        if missing or warnings:
            issues.append(
                {
                    "creator_id": profile.creator_id,
                    "name": profile.name,
                    "platform": profile.platform,
                    "missing": missing,
                    "warnings": warnings,
                    "source": "、".join(profile.data_sources[:3]),
                }
            )
    return issues[:limit]


def governance_summary(profiles: list[CreatorProfile]) -> dict[str, Any]:
    duplicate_count = len(find_duplicate_candidates(profiles, limit=1000))
    issues = quality_issues(profiles, limit=10000)
    return {
        "total_profiles": len(profiles),
        "duplicate_candidates": duplicate_count,
        "quality_issues": len(issues),
        "missing_follower_count": sum(1 for profile in profiles if not profile.follower_count),
        "missing_listed_price": sum(1 for profile in profiles if not profile.listed_price),
        "missing_homepage_url": sum(1 for profile in profiles if not profile.homepage_url),
        "missing_bio": sum(1 for profile in profiles if not profile.bio),
    }


def profile_card(profile: CreatorProfile) -> dict[str, Any]:
    data = asdict(profile)
    return {
        "creator_id": data["creator_id"],
        "name": data["name"],
        "platform": data["platform"],
        "platform_user_id": data["platform_user_id"],
        "homepage_url": data["homepage_url"],
        "follower_count": data["follower_count"],
        "listed_price": data["listed_price"],
        "data_sources": data["data_sources"],
    }


def _strong_keys(profile: CreatorProfile) -> list[tuple[str, str]]:
    platform = normalize_platform(profile.platform)
    keys = []
    if _usable_key(profile.platform_user_id):
        keys.append(("platform_id", f"{platform}:{str(profile.platform_user_id).strip().lower()}"))
    url = normalize_url(profile.homepage_url)
    if url:
        keys.append(("platform_url", f"{platform}:{url}"))
    name = normalize_name(profile.name)
    if name:
        keys.append(("platform_name", f"{platform}:{name}"))
    return keys


def _usable_key(value: object) -> bool:
    text = str(value or "").strip().lower()
    if not text or text in {"nan", "/", "-", "--", "无", "暂无", "无id", "none", "null"}:
        return False
    return bool(re.search(r"[\w\u4e00-\u9fff]", text))


def _duplicate_candidate(left: CreatorProfile, right: CreatorProfile, reason: str, confidence: int, seen_pairs: set[tuple[str, str]]) -> dict[str, Any] | None:
    pair = tuple(sorted([left.creator_id, right.creator_id]))
    if pair in seen_pairs:
        return None
    seen_pairs.add(pair)
    return {
        "confidence": confidence,
        "reason": reason,
        "left": profile_card(left),
        "right": profile_card(right),
    }
