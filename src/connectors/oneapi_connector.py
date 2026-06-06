from __future__ import annotations

from typing import Any

import requests

from src.connectors.api_connector_base import ApiConnector
from src.schemas import CreatorProfile, stable_id


class OneApiConnector(ApiConnector):
    """Connector for GetOneAPI KOL/social data APIs.

    OneAPI uses Bearer token auth and exposes platform-specific endpoints.
    This connector implements a conservative first pass for user profile lookup.
    """

    provider_name = "oneapi"

    ENDPOINTS = {
        "抖音": "/api/douyin/fetch_user_data_by_short",
        "小红书": "/api/xiaohongshu-v2/fetch_user_info",
        "B站": "/api/bilibili/fetch_user_info",
        "快手": "/api/kuaishou/fetch_user_info",
        "微博": "/api/weibo/fetch_user_info",
    }

    def __init__(self, api_key: str, base_url: str = "https://api.getoneapi.com", timeout: int = 60) -> None:
        if not api_key:
            raise ValueError("OneAPI api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_creator(self, platform: str, identifier: str) -> CreatorProfile:
        endpoint = self.ENDPOINTS.get(platform)
        if not endpoint:
            raise ValueError(f"OneAPI connector does not support platform: {platform}")
        payload = self._request(endpoint, self._payload_for(platform, identifier))
        data = payload.get("data") if isinstance(payload, dict) else {}
        user = self._unwrap_user(data)
        return self._profile_from_user(platform, identifier, user, payload)

    def _request(self, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 200:
            raise RuntimeError(f"OneAPI business error: {payload.get('code')} {payload.get('message')}")
        return payload

    def _payload_for(self, platform: str, identifier: str) -> dict[str, Any]:
        if platform == "抖音":
            return {"user_id": identifier}
        if platform in {"小红书", "B站", "快手", "微博"}:
            return {"user_id": identifier}
        return {"id": identifier}

    def _unwrap_user(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return {}
        for key in ["user", "user_info", "author", "profile", "data"]:
            value = data.get(key)
            if isinstance(value, dict):
                return value
        return data

    def _first(self, data: dict[str, Any], keys: list[str], default: Any = "") -> Any:
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return value
        return default

    def _to_int(self, value: Any) -> int:
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    def _profile_from_user(
        self,
        platform: str,
        identifier: str,
        user: dict[str, Any],
        raw_payload: dict[str, Any],
    ) -> CreatorProfile:
        name = self._first(user, ["nickname", "name", "user_name", "screen_name", "uname"], f"{platform}达人{identifier}")
        uid = str(self._first(user, ["uid", "user_id", "sec_uid", "id", "mid"], identifier))
        followers = self._to_int(self._first(user, ["follower_count", "followers", "fans", "fans_count", "follower"], 0))
        likes = self._to_int(self._first(user, ["total_favorited", "total_likes", "liked_count", "likes"], 0))
        bio = str(self._first(user, ["signature", "desc", "description", "bio", "sign"], ""))
        avatar = str(self._first(user, ["avatar", "avatar_url", "avatar_larger", "face"], ""))
        return CreatorProfile(
            creator_id=stable_id(platform, uid),
            name=str(name),
            platform=platform,
            platform_user_id=uid,
            avatar_url=avatar,
            bio=bio,
            follower_count=followers,
            total_likes=likes,
            data_sources=[self.provider_name],
            manual_notes=f"OneAPI 原始响应字段需按平台核验；业务 code={raw_payload.get('code')}",
        )
