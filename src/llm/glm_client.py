from __future__ import annotations

import base64
import json
import os
from typing import Any

import requests
from dotenv import load_dotenv


DEFAULT_GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_GLM_MODEL = "glm-4-flash"
DEFAULT_GLM_VISION_MODEL = "glm-4v-flash"


class GlmClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("GLM_API_KEY", "")
        self.model = model or os.getenv("GLM_MODEL", DEFAULT_GLM_MODEL)
        self.base_url = base_url or os.getenv("GLM_BASE_URL", DEFAULT_GLM_BASE_URL)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def complete_json(self, system: str, user: str, timeout: int = 30) -> dict[str, Any]:
        if not self.available:
            raise RuntimeError("GLM_API_KEY is not configured")
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

    def complete_vision_json(
        self,
        system: str,
        user: str,
        image_bytes: bytes,
        content_type: str = "image/png",
        timeout: int = 60,
    ) -> dict[str, Any]:
        if not self.available:
            raise RuntimeError("GLM_API_KEY is not configured")
        model = os.getenv("GLM_VISION_MODEL", DEFAULT_GLM_VISION_MODEL)
        data_url = f"data:{content_type or 'image/png'};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
