from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.schemas import stable_id


INTERNAL_ROLES = {"admin", "strategist", "media_buyer", "viewer"}
CLIENT_ROLES = {"client_owner", "client_reviewer", "client_viewer"}
ALL_ROLES = INTERNAL_ROLES | CLIENT_ROLES


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def session_expires_at(days: int = 14) -> str:
    return (datetime.utcnow() + timedelta(days=days)).isoformat(timespec="seconds")


def new_session_id() -> str:
    return f"sess_{secrets.token_urlsafe(32)}"


def user_id_for(email: str, provider: str = "local") -> str:
    return stable_id(provider, email.strip().lower(), prefix="user")


def client_id_for(name: str) -> str:
    return stable_id(name.strip().lower(), prefix="client")


@dataclass
class AuthUser:
    user_id: str
    email: str
    name: str = ""
    password_hash: str = ""
    user_type: str = "internal"
    role: str = "viewer"
    status: str = "active"
    identity_provider: str = "local"
    external_user_id: str = ""
    client_id: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    last_login_at: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "AuthUser":
        return cls(**json.loads(value))

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_sensitive:
            data.pop("password_hash", None)
        return data


@dataclass
class AuthSession:
    session_id: str
    user_id: str
    expires_at: str
    created_at: str = field(default_factory=now_iso)
    last_seen_at: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "AuthSession":
        return cls(**json.loads(value))

    def expired(self) -> bool:
        try:
            return datetime.fromisoformat(self.expires_at) < datetime.utcnow()
        except ValueError:
            return True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClientAccount:
    client_id: str
    name: str
    company: str = ""
    status: str = "active"
    created_by: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "ClientAccount":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClientUserLink:
    link_id: str
    client_id: str
    user_id: str
    role: str = "client_viewer"
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "ClientUserLink":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectAccess:
    access_id: str
    user_id: str
    client_id: str = ""
    proposal_id: str = ""
    campaign_id: str = ""
    permissions: list[str] = field(default_factory=lambda: ["view"])
    created_by: str = ""
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "ProjectAccess":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Identity:
    user: AuthUser
    client_ids: list[str] = field(default_factory=list)
    provider: str = "local"

    def to_dict(self) -> dict[str, Any]:
        return {
            "user": self.user.to_dict(),
            "client_ids": self.client_ids,
            "provider": self.provider,
        }
