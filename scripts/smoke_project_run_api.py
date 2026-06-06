from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = "project-run-api-smoke"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    creators = [
        {
            "name": "汽车科技测评Lab",
            "platform": "抖音",
            "bio": "新能源车、智能座舱、智驾体验测评",
            "follower_count": 360000,
            "listed_price": 52000,
            "cooperation_brands": "新能源车品牌,智能硬件",
        },
        {
            "name": "小红书城市通勤生活",
            "platform": "小红书",
            "bio": "年轻家庭、城市通勤、周末露营和真实生活方式",
            "follower_count": 180000,
            "listed_price": 28000,
            "cooperation_brands": "汽车,家居,户外",
        },
        {
            "name": "B站硬核车评社",
            "platform": "B站",
            "bio": "汽车技术拆解，智能化和安全配置解释",
            "follower_count": 240000,
            "listed_price": 43000,
            "cooperation_brands": "车企,科技品牌",
        },
    ]
    for creator in creators:
        response = client.post("/api/import/manual", headers=HEADERS, json=creator)
        assert response.status_code == 200, response.text

    response = client.post(
        "/api/project-run",
        headers=HEADERS,
        json={
            "client_name": "某新能源汽车品牌",
            "project_name": "Project Run Smoke",
            "top_n": 6,
            "brief": "预算50万，新能源SUV新品上市预热，目标用户是25-40岁一二线城市年轻家庭和科技兴趣人群。希望突出科技感、智能化、高端感和城市生活方式。平台优先抖音、小红书、B站，需要选择合适KOL并做投放前风险推演。",
        },
    )
    assert response.status_code == 200, response.text
    run = response.json()["run"]
    assert run["status"] == "completed"
    assert len(run["steps"]) >= 8
    assert run["brief"]["industry"]
    assert run["brand"]["brand_id"]
    assert run["product"]["product_id"]
    assert run["social_report"]["issues"]
    assert run["matches"]
    assert run["narratives"]
    assert run["simulation_report"]["nodes"]
    assert run["campaign_room"]["plans"]
    assert run["graph"]["nodes"]
    node_types = {node["type"] for node in run["graph"]["nodes"]}
    assert {"brand", "product", "creator", "narrative"}.issubset(node_types)
    node_stages = {node.get("stage") for node in run["graph"]["nodes"]}
    assert {"brand_calibration", "product_profile", "kol_match", "narrative_asset", "risk_test"}.issubset(node_stages)
    assert any(node.get("detail") for node in run["graph"]["nodes"])
    assert any(node.get("payload") for node in run["graph"]["nodes"])
    print(
        "OK project_run_api "
        f"steps={len(run['steps'])} matches={len(run['matches'])} "
        f"graph_nodes={len(run['graph']['nodes'])} plans={len(run['campaign_room']['plans'])}"
    )


if __name__ == "__main__":
    main()
