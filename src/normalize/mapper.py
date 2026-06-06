from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.schemas import CreatorProfile, split_tags, stable_id


FIELD_ALIASES = {
    "name": [
        "name",
        "creator",
        "creator_name",
        "达人",
        "达人名称",
        "账号",
        "账号名称",
        "昵称",
        "博主",
        "kol",
        "小红书昵称",
        "微信视频账号",
        "快手账号名称",
        "懂车帝账号",
    ],
    "platform": ["platform", "平台", "渠道", "分发平台"],
    "platform_user_id": ["id", "账号id", "账号ID", "抖音号", "小红书号", "小红书号", "视频号ID", "UID", "主页id", "account_id", "懂车帝账号"],
    "homepage_url": ["homepage", "homepage_url", "主页", "主页链接", "链接", "url", "账号链接", "达人主页", "抖音主页链接", "星图主页链接", "蒲公英主页", "主页链接", "红书链接", "抖音链接"],
    "bio": ["bio", "简介", "账号简介", "达人简介", "账号简介", "内容方向", "description"],
    "region": ["region", "地区", "城市", "所在地"],
    "follower_count": ["fans", "followers", "follower_count", "粉丝", "粉丝数", "粉丝量", "粉丝量（W）", "粉丝量(W)", "粉丝数(万)", "粉丝（W）", "粉丝量 （W）"],
    "avg_likes": ["avg_likes", "平均点赞", "赞均", "点赞均值"],
    "avg_comments": ["avg_comments", "平均评论", "评均", "评论均值"],
    "avg_shares": ["avg_shares", "平均分享", "分享均值"],
    "avg_collections": ["avg_collections", "平均收藏", "收藏均值"],
    "listed_price": ["price", "listed_price", "报价", "刊例价", "价格", "合作报价", "星图价格 （21-60s）", "星图价格 （60s+）", "21-60s植入价", "60s+定制价", "视频号价格", "快手21-60s", "定制视频", "报备视频（单品）", "小红书定制视频", "懂车帝价格"],
    "contact": ["contact", "联系方式", "微信", "商务联系方式"],
    "cooperation_brands": ["cooperation_brands", "合作品牌", "历史合作品牌", "品牌案例", "部分合作客户", "优秀广告案例"],
    "cooperation_formats": ["cooperation_formats", "合作形式", "内容形式", "类型", "品类", "标签", "达人标签", "账号标签"],
    "manual_notes": ["manual_notes", "备注", "媒介备注", "风险备注", "履约反馈"],
}


def _norm_col(col: Any) -> str:
    return str(col).strip().lower().replace(" ", "").replace("_", "")


def _find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lookup = {_norm_col(c): c for c in df.columns}
    for alias in aliases:
        key = _norm_col(alias)
        if key in lookup:
            return lookup[key]
    for col in df.columns:
        norm = _norm_col(col)
        if any(_norm_col(alias) in norm for alias in aliases if len(_norm_col(alias)) >= 3):
            return col
    return None


def _parse_int(value: Any) -> int:
    if value is None or pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if not text or text.lower() == "nan":
        return 0
    multiplier = 1
    if "万" in text:
        multiplier = 10_000
    elif "w" in text.lower() and len(re.findall(r"\d+(?:\.\d+)?", text)) == 1:
        multiplier = 10_000
    elif "k" in text.lower():
        multiplier = 1_000
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    return int(float(nums[0]) * multiplier) if nums else 0


def _clean_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _clean_name(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[0] if lines else text


def _clean_platform(value: Any, source: str, columns: object) -> str:
    text = _clean_text(value)
    normalized = text.replace(" ", "").lower()
    known = {
        "抖音",
        "小红书",
        "b站",
        "bilibili",
        "快手",
        "微博",
        "视频号",
        "公众号",
        "微信",
        "懂车帝",
    }
    if normalized in known:
        return "B站" if normalized in {"b站", "bilibili"} else ("公众号" if normalized == "微信" else text)
    return _infer_platform(source, columns)


def infer_column_mapping(df: pd.DataFrame) -> dict[str, str]:
    return {
        field: column
        for field, aliases in FIELD_ALIASES.items()
        if (column := _find_column(df, aliases))
    }


def map_dataframe_to_profiles(df: pd.DataFrame, source: str, column_mapping: dict[str, str] | None = None) -> list[CreatorProfile]:
    columns = infer_column_mapping(df)
    if column_mapping:
        valid_columns = {str(column) for column in df.columns}
        for field, column in column_mapping.items():
            if field in FIELD_ALIASES and str(column) in valid_columns:
                columns[field] = str(column)
    profiles: list[CreatorProfile] = []
    for _, row in df.iterrows():
        name_col = columns.get("name")
        name = _clean_name(row.get(name_col, "")) if name_col else ""
        if not name:
            continue
        platform = _clean_platform(row.get(columns["platform"], ""), source, df.columns) if columns.get("platform") else _infer_platform(source, df.columns)
        homepage = str(row.get(columns["homepage_url"], "")).strip() if columns.get("homepage_url") else ""
        platform_user_id = str(row.get(columns["platform_user_id"], "")).strip() if columns.get("platform_user_id") else ""
        creator_id = stable_id(platform, platform_user_id or homepage or name)
        profiles.append(
            CreatorProfile(
                creator_id=creator_id,
                name=name,
                platform=platform or "未知",
                platform_user_id=platform_user_id if platform_user_id.lower() != "nan" else "",
                homepage_url=homepage if homepage.lower() != "nan" else "",
                bio=str(row.get(columns["bio"], "")).strip() if columns.get("bio") else "",
                region=str(row.get(columns["region"], "")).strip() if columns.get("region") else "",
                follower_count=_parse_int(row.get(columns["follower_count"])) if columns.get("follower_count") else 0,
                avg_likes=_parse_int(row.get(columns["avg_likes"])) if columns.get("avg_likes") else 0,
                avg_comments=_parse_int(row.get(columns["avg_comments"])) if columns.get("avg_comments") else 0,
                avg_shares=_parse_int(row.get(columns["avg_shares"])) if columns.get("avg_shares") else 0,
                avg_collections=_parse_int(row.get(columns["avg_collections"])) if columns.get("avg_collections") else 0,
                listed_price=_parse_int(row.get(columns["listed_price"])) if columns.get("listed_price") else 0,
                price_source=source if columns.get("listed_price") else "",
                contact=str(row.get(columns["contact"], "")).strip() if columns.get("contact") else "",
                cooperation_brands=split_tags(row.get(columns["cooperation_brands"])) if columns.get("cooperation_brands") else [],
                cooperation_formats=split_tags(row.get(columns["cooperation_formats"])) if columns.get("cooperation_formats") else [],
                manual_notes=str(row.get(columns["manual_notes"], "")).strip() if columns.get("manual_notes") else "",
                data_sources=[source],
            )
        )
    return profiles


def _infer_platform(source: str, columns: object) -> str:
    text = f"{source} {' '.join(map(str, columns))}"
    if "小红书" in text or "红书" in text or "蒲公英" in text:
        return "小红书"
    if "抖音" in text or "星图" in text:
        return "抖音"
    if "B站" in text or "bilibili" in text.lower() or "UID" in text:
        return "B站"
    if "快手" in text:
        return "快手"
    if "视频号" in text or "微信视频" in text:
        return "视频号"
    if "微博" in text:
        return "微博"
    if "微信" in text or "公众号" in text:
        return "公众号"
    if "懂车帝" in text:
        return "懂车帝"
    return "未知"
