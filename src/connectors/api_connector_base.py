from __future__ import annotations

from abc import ABC, abstractmethod

from src.schemas import CreatorProfile


class ApiConnector(ABC):
    """Base API connector for third-party KOL data providers."""

    provider_name: str

    @abstractmethod
    def fetch_creator(self, platform: str, identifier: str) -> CreatorProfile:
        raise NotImplementedError

    def fetch_posts(self, platform: str, identifier: str) -> list[dict]:
        return []
