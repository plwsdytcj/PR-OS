from __future__ import annotations

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv


DEFAULT_GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_GLM_MODEL = "glm-4-flash"


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
