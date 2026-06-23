from __future__ import annotations

import re
from urllib.parse import urlparse

from src.schemas import CreatorProfile, stable_id


PLATFORM_HINTS = {
    "douyin": "抖音",
    "iesdouyin": "抖音",
    "xiaohongshu": "小红书",
    "xhslink": "小红书",
    "bilibili": "B站",
    "b23": "B站",
    "weibo": "微博",
    "weixin": "微信公众号",
    "mp.weixin": "微信公众号",
    "channels.weixin": "视频号",
    "zhihu": "知乎",
    "douban": "豆瓣",
    "toutiao": "今日头条",
    "snssdk": "今日头条",
    "twitter": "推特",
    "x.com": "推特",
}


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    for hint, platform in PLATFORM_HINTS.items():
        if hint in host:
            return platform
    return "未知"


def extract_identifier(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if path:
        parts = [p for p in re.split(r"[/?:=&]", path) if p]
        if parts:
            return parts[-1][:80]
    return parsed.netloc or url[:80]


def parse_links(lines: list[str]) -> list[CreatorProfile]:
    profiles: list[CreatorProfile] = []
    for line in lines:
        url = line.strip()
        if not url:
            continue
        platform = detect_platform(url)
        identifier = extract_identifier(url)
        name = f"{platform}达人-{identifier}" if platform != "未知" else f"待补充达人-{identifier}"
        profiles.append(
            CreatorProfile(
                creator_id=stable_id(platform, identifier, url),
                name=name,
                platform=platform,
                platform_user_id=identifier,
                homepage_url=url,
                data_sources=["link"],
                risk_tags=["链接解析数据有限，需人工核验"],
            )
        )
    return profiles
