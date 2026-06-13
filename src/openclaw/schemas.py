from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from src.agent.schemas import now_iso
from src.schemas import stable_id


def openclaw_config_id() -> str:
    return "default"


def binding_id_for(user_id: str) -> str:
    return stable_id("openclaw_binding", user_id, prefix="openclaw_binding")


def run_id_for(user_id: str, message: str) -> str:
    return stable_id("openclaw_run", user_id, message.strip()[:240], now_iso(), prefix="openclaw_run")


def event_id_for(run_id: str, sequence: int, event_type: str) -> str:
    return stable_id(run_id, str(sequence), event_type, prefix="openclaw_event")


@dataclass
class OpenClawConfig:
    config_id: str = field(default_factory=openclaw_config_id)
    enabled: bool = False
    gateway_url: str = ""
    control_ui_url: str = ""
    admin_token: str = ""
    default_agent_id: str = "kolness_default"
    proxy_base_path: str = "/openclaw"
    updated_by: str = ""
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "OpenClawConfig":
        return cls(**json.loads(value))

    def to_dict(self, mask_secret: bool = True) -> dict[str, Any]:
        data = asdict(self)
        if mask_secret:
            token = str(data.get("admin_token") or "")
            data["admin_token"] = "" if not token else f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "*" * len(token)
        return data


@dataclass
class OpenClawUserBinding:
    binding_id: str
    user_id: str
    openclaw_gateway_url: str = ""
    openclaw_agent_id: str = ""
    openclaw_session_id: str = ""
    status: str = "active"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "OpenClawUserBinding":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OpenClawRun:
    run_id: str
    user_id: str
    campaign_id: str = ""
    openclaw_agent_id: str = ""
    openclaw_session_id: str = ""
    status: str = "running"
    message: str = ""
    response: str = ""
    error: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "OpenClawRun":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OpenClawEvent:
    event_id: str
    run_id: str
    sequence: int
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "OpenClawEvent":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

