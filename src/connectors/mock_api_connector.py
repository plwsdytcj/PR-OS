from __future__ import annotations

import random

from src.connectors.api_connector_base import ApiConnector
from src.schemas import CreatorProfile, stable_id


class MockApiConnector(ApiConnector):
    provider_name = "mock_api"

    def fetch_creator(self, platform: str, identifier: str) -> CreatorProfile:
        key = f"{platform}:{identifier}"
        rng = random.Random(key)
        followers = rng.randint(20_000, 1_800_000)
        avg_likes = max(200, int(followers * rng.uniform(0.005, 0.06)))
        avg_comments = max(20, int(avg_likes * rng.uniform(0.03, 0.18)))
        price = int(max(3000, followers * rng.uniform(0.015, 0.08)) // 100 * 100)
        topics = ["汽车", "科技", "美妆", "职场", "生活方式", "母婴", "食品", "AIGC"]
        topic = topics[rng.randrange(len(topics))]
        return CreatorProfile(
            creator_id=stable_id(platform, identifier),
            name=f"{platform}达人{str(identifier)[-6:]}",
            platform=platform,
            platform_user_id=str(identifier),
            homepage_url=str(identifier) if str(identifier).startswith("http") else "",
            bio=f"专注{topic}内容，擅长真实体验、测评和场景化表达。",
            follower_count=followers,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            recent_posts_count=rng.randint(15, 80),
            listed_price=price,
            price_source="mock_api",
            data_sources=[self.provider_name],
        )
