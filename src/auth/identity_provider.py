from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.auth.schemas import AuthUser
from src.auth.service import authenticate_user


@dataclass
class ProviderIdentity:
    provider: str
    external_user_id: str
    email: str
    name: str


class IdentityProvider:
    provider = "base"

    def authenticate(self, db_path: Path, email: str, password: str) -> AuthUser | None:
        raise NotImplementedError


class LocalIdentityProvider(IdentityProvider):
    provider = "local"

    def authenticate(self, db_path: Path, email: str, password: str) -> AuthUser | None:
        return authenticate_user(db_path, email, password)
