from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = "narrative-assets-smoke"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    brand = client.post(
        "/api/symbolic/brand-profile",
        headers=HEADERS,
        json={
            "brand_name": "叙事资产测试品牌",
            "industry": "汽车",
            "product": "新能源 SUV",
            "brief": "新品上市预热，突出城市自由、家庭安全和真实体验。",
        },
    )
    assert brand.status_code == 200
    brand_profile = brand.json()["profile"]
    product = client.post(
        "/api/symbolic-os/products",
        headers=HEADERS,
        json={"brand_name": brand_profile["brand_name"], "product_name": "新能源 SUV", "category": "汽车"},
    )
    assert product.status_code == 200

    narrative_payload = {
        "brand": brand_profile,
        "product": product.json()["profile"],
        "narratives": [
            {
                "project": "叙事资产测试项目",
                "creator_id": "creator_smoke",
                "creator_name": "城市生活方式博主",
                "start_tag": "城市通勤",
                "mediating_tags": ["智能座舱", "家庭安全"],
                "target_tag": "城市自由",
                "narrative_path": "从城市通勤压力切入，经由智能座舱和家庭安全，转向城市自由。",
                "metaphor_strategy": "新能源 SUV 被表达为移动城堡",
                "metonymy_strategy": "用车钥匙、后备箱和露营装备完成转喻",
                "must_include": ["真实体验", "家庭安全"],
                "must_avoid": ["价格争议", "智驾夸大"],
                "comment_guidance": "引导用户讨论真实通勤和家庭出行。",
            }
        ],
    }
    saved = client.post("/api/symbolic-os/narratives", headers=HEADERS, json=narrative_payload)
    assert saved.status_code == 200
    items = saved.json()["items"]
    assert len(items) == 1
    assert items[0]["narrative_id"]
    assert items[0]["content_brief"]
    assert saved.json()["snapshot"]["metrics"]["content_narrative_assets"] >= 1

    listed = client.get("/api/symbolic-os/narratives", headers=HEADERS)
    assert listed.status_code == 200
    assert any(item["narrative_id"] == items[0]["narrative_id"] for item in listed.json()["items"])
    print(f"OK narrative_assets narrative={items[0]['narrative_id']}")


if __name__ == "__main__":
    main()
