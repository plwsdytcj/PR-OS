from __future__ import annotations

import os
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["AGENT_PROVIDER"] = "fallback"

from web.server import app


TENANT = f"phase7c-knowledge-rag-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "knowledge-admin@test.local", "name": "Knowledge Admin", "password": "knowledge-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text

    create = client.post(
        "/api/knowledge",
        headers=HEADERS,
        json={
            "title": "新能源 SUV 小红书投放风险规则",
            "source_type": "risk_policy",
            "industry": "新能源汽车",
            "tags": "新能源,小红书,KOL,风险,年轻用户",
            "content": (
                "新能源 SUV 在小红书做预热时，优先选择生活方式博主和真实试用博主。"
                "需要规避硬广感、参数堆砌和价格争议；科技测评达人只适合作为补充解释节点。"
                "年轻用户更关注城市通勤、家庭出行、智能座舱和情绪价值。"
            ),
        },
    )
    assert create.status_code == 200, create.text
    created = create.json()
    assert created["document"]["chunk_count"] >= 1
    document_id = created["document"]["document_id"]

    listing = client.get("/api/knowledge", headers=HEADERS)
    assert listing.status_code == 200, listing.text
    assert listing.json()["stats"]["documents"] >= 1
    assert listing.json()["stats"]["chunks"] >= 1

    detail = client.get(f"/api/knowledge/{document_id}", headers=HEADERS)
    assert detail.status_code == 200, detail.text
    assert detail.json()["document"]["document_id"] == document_id
    assert detail.json()["chunks"]

    search = client.post(
        "/api/knowledge/search",
        headers=HEADERS,
        json={"query": "新能源 SUV 小红书 年轻用户 KOL 风险", "top_k": 5},
    )
    assert search.status_code == 200, search.text
    search_items = search.json()["items"]
    assert search_items
    assert search_items[0]["source"] == "knowledge_base"
    assert "小红书" in search_items[0]["content"]

    sample = client.post("/api/import/sample", headers=HEADERS)
    assert sample.status_code == 200, sample.text

    chat = client.post(
        "/api/agent/chat",
        headers=HEADERS,
        json={
            "client_name": "Phase7C 新能源品牌",
            "project_name": "Knowledge RAG Agent Smoke",
            "message": "预算40万，新能源SUV上市预热，平台优先小红书，需要推荐KOL并说明年轻用户风险。",
            "top_n": 3,
        },
    )
    assert chat.status_code == 200, chat.text
    artifacts = chat.json()["artifacts"]
    knowledge_artifacts = [item for item in artifacts if item["artifact_type"] == "knowledge"]
    assert knowledge_artifacts
    knowledge_items = knowledge_artifacts[0]["payload"]["items"]
    assert any(item.get("source") == "knowledge_base" for item in knowledge_items), knowledge_items

    print(
        "OK phase7c_knowledge_rag "
        f"document={document_id} search={len(search_items)} artifacts={len(artifacts)}"
    )


if __name__ == "__main__":
    main()
