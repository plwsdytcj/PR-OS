from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = "product-symbolic-smoke"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    client.post(
        "/api/symbolic-os/social-reports",
        headers=HEADERS,
        json={
            "period": "Product Smoke",
            "raw_input": "新能源车用户关注城市通勤、家庭安全、智驾体验和价格争议。",
        },
    )
    response = client.post(
        "/api/symbolic-os/products",
        headers=HEADERS,
        json={
            "brand_name": "产品符号测试品牌",
            "category": "汽车",
            "product_name": "新能源 SUV",
            "use_scenarios": "城市通勤,家庭出行",
            "functional_value": "智能座舱,安全辅助",
        },
    )
    assert response.status_code == 200
    product = response.json()["profile"]
    assert product["product_id"]
    assert product["metaphors"]
    assert product["metonymies"]
    assert product["suitable_creator_types"]
    assert response.json()["snapshot"]["metrics"]["product_symbolic_profiles"] >= 1

    products = client.get("/api/symbolic-os/products", headers=HEADERS)
    assert products.status_code == 200
    assert any(item["product_id"] == product["product_id"] for item in products.json()["items"])

    graph = client.post(
        "/api/symbolic/graph",
        headers=HEADERS,
        json={
            "brand": {"brand_id": "brand_product_smoke", "brand_name": "产品符号测试品牌"},
            "matches": [],
            "narratives": [],
            "product_context": product,
        },
    )
    assert graph.status_code == 200
    node_types = {node["type"] for node in graph.json()["nodes"]}
    assert "product" in node_types
    assert "narrative" in node_types
    assert "risk_tag" in node_types
    print(f"OK product_symbolic product={product['product_id']} graph_nodes={len(graph.json()['nodes'])}")


if __name__ == "__main__":
    main()
