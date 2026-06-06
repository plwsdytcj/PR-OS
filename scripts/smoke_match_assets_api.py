from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = "match-assets-smoke"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    creator = client.post(
        "/api/import/manual",
        headers=HEADERS,
        json={
            "name": "匹配资产测试博主",
            "platform": "小红书",
            "bio": "城市生活方式、新能源车真实体验、家庭出行。",
            "follower_count": 88000,
            "listed_price": 12000,
            "industry_fit_tags": ["汽车", "生活方式"],
            "content_capability_tags": ["真实测评", "场景种草"],
        },
    )
    assert creator.status_code == 200
    brand = client.post(
        "/api/symbolic/brand-profile",
        headers=HEADERS,
        json={
            "brand_name": "匹配资产测试品牌",
            "industry": "汽车",
            "product": "新能源 SUV",
            "brief": "新品上市预热，突出城市自由和家庭安全。",
        },
    )
    assert brand.status_code == 200
    product = client.post(
        "/api/symbolic-os/products",
        headers=HEADERS,
        json={"brand_name": "匹配资产测试品牌", "product_name": "新能源 SUV", "category": "汽车"},
    )
    assert product.status_code == 200
    match = client.post("/api/symbolic/match", headers=HEADERS, json={"brand_id": brand.json()["profile"]["brand_id"], "top_n": 5})
    assert match.status_code == 200
    results = match.json()["results"]
    assert results
    saved = client.post(
        "/api/symbolic-os/matches",
        headers=HEADERS,
        json={"brand": match.json()["brand"], "product": product.json()["profile"], "results": results},
    )
    assert saved.status_code == 200
    items = saved.json()["items"]
    assert items
    assert items[0]["match_id"]
    assert items[0]["match_reason"]
    assert saved.json()["snapshot"]["metrics"]["brand_creator_match_assets"] >= 1
    listed = client.get("/api/symbolic-os/matches", headers=HEADERS)
    assert any(item["match_id"] == items[0]["match_id"] for item in listed.json()["items"])
    print(f"OK match_assets matches={len(items)} first={items[0]['match_id']}")


if __name__ == "__main__":
    main()
