from __future__ import annotations

from pathlib import Path
import os
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = "phase8-kol-intelligence-smoke"
ADMIN_EMAIL = "phase8-smoke@pr-ai-os.local"
ADMIN_PASSWORD = "phase8-smoke-password"
HEADERS = {"X-Tenant-ID": TENANT}
if os.getenv("PR_AI_OS_ACCESS_KEY"):
    HEADERS["X-Access-Key"] = os.getenv("PR_AI_OS_ACCESS_KEY", "")


def main() -> None:
    client = TestClient(app)
    _ensure_auth(client)
    creators = [
        {
            "name": "小红书年轻家庭通勤",
            "platform": "小红书",
            "bio": "年轻家庭、新能源车、城市通勤、真实体验和周末露营",
            "follower_count": 210000,
            "engagement_rate": 0.045,
            "listed_price": 32000,
            "industry_fit_tags": "汽车,新能源,家庭出行",
            "content_capability_tags": "真实体验,生活方式种草,图文笔记",
            "suitable_goals": "预热,信任,种草",
            "suitable_stages": "上市预热,口碑建立",
            "risk_tags": "硬广不信任",
            "manual_notes": "历史合作适合把智驾和家庭安全讲成真实通勤场景。",
        },
        {
            "name": "抖音智能车评实验室",
            "platform": "抖音",
            "bio": "新能源 SUV、智驾体验、智能座舱和汽车技术解释",
            "follower_count": 520000,
            "engagement_rate": 0.038,
            "listed_price": 68000,
            "industry_fit_tags": "汽车,3C数码,AI软件",
            "content_capability_tags": "短视频测评,参数解释,科技感",
            "suitable_goals": "声量,信任,预热",
            "suitable_stages": "上市预热,首发发布",
            "cooperation_brands": "新能源车品牌,智能硬件",
            "manual_notes": "适合拆解智能化卖点，但要避免参数堆砌。",
        },
        {
            "name": "B站硬核安全拆解",
            "platform": "B站",
            "bio": "长视频深度讲解车辆安全、智能化系统和家庭用车选择",
            "follower_count": 260000,
            "engagement_rate": 0.026,
            "listed_price": 45000,
            "industry_fit_tags": "汽车,家庭安全",
            "content_capability_tags": "长视频解释,专业背书,风险说明",
            "suitable_goals": "信任,背书",
            "suitable_stages": "上市预热,口碑建立",
            "risk_tags": "周期较长",
        },
    ]
    for creator in creators:
        response = client.post("/api/import/manual", headers=HEADERS, json=creator)
        assert response.status_code == 200, response.text

    analyze = client.post("/api/kol-intelligence/analyze-tags", headers=HEADERS, json={"limit": 20})
    assert analyze.status_code == 200, analyze.text
    analyze_body = analyze.json()
    assert len(analyze_body["items"]) >= 12
    assert analyze_body["snapshot"]["metrics"]["creators_with_tags"] >= 3
    assert any(item["evidence"] for item in analyze_body["items"])

    brief = "新能源汽车品牌做 SUV 新品上市预热，目标年轻家庭，强调智驾、家庭安全、城市通勤和真实体验，平台优先小红书、抖音、B站。"
    graph = client.post("/api/kol-intelligence/graph", headers=HEADERS, json={"brief": brief, "limit": 30})
    assert graph.status_code == 200, graph.text
    graph_body = graph.json()
    assert graph_body["nodes"]
    assert graph_body["edges"]
    assert graph_body["evolution"]
    assert any(node["type"] == "creator" for node in graph_body["nodes"])
    assert any(edge["label"] in {"激活", "推理"} for edge in graph_body["edges"])

    prediction = client.post("/api/kol-intelligence/predict", headers=HEADERS, json={"brief": brief, "top_n": 5})
    assert prediction.status_code == 200, prediction.text
    prediction_body = prediction.json()
    assert prediction_body["recommendations"]
    assert prediction_body["graph"]["nodes"]
    top = prediction_body["recommendations"][0]
    assert top["creator_name"]
    assert top["reasons"]
    assert top["evidence"]

    snapshot = client.get("/api/kol-intelligence", headers=HEADERS)
    assert snapshot.status_code == 200
    assert snapshot.json()["metrics"]["predictions"] >= 1
    print(
        "OK phase8_kol_intelligence "
        f"tags={len(analyze_body['items'])} graph_nodes={len(graph_body['nodes'])} "
        f"recommendations={len(prediction_body['recommendations'])}"
    )


def _ensure_auth(client: TestClient) -> None:
    if "X-Access-Key" in HEADERS:
        return
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "name": "Phase 8 Smoke",
    }
    response = client.post("/api/auth/bootstrap-admin", headers=HEADERS, json=payload)
    if response.status_code == 200:
        return
    login = client.post("/api/auth/login", headers=HEADERS, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert login.status_code == 200, login.text


if __name__ == "__main__":
    main()
