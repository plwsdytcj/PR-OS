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


TENANT = f"phase7g-agent-graph-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "phase7g-admin@test.local", "name": "Phase7G Admin", "password": "phase7g-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text

    sample = client.post("/api/import/sample", headers=HEADERS)
    assert sample.status_code == 200, sample.text

    knowledge = client.post(
        "/api/knowledge",
        headers=HEADERS,
        json={
            "title": "Phase7G 新能源传播图谱知识",
            "source_type": "case",
            "industry": "新能源汽车",
            "tags": "Phase7G,新能源,KOL,风险",
            "content": "新能源 SUV 上市预热需要把年轻用户、真实试用、生活方式 KOL、硬广风险和方案回流串成可解释图谱。",
        },
    )
    assert knowledge.status_code == 200, knowledge.text

    chat = client.post(
        "/api/agent/chat",
        headers=HEADERS,
        json={
            "client_name": "Phase7G 新能源品牌",
            "project_name": "Reasoning Graph Smoke",
            "message": "预算50万，新能源SUV上市预热，平台优先小红书和抖音，目标年轻用户，需要推荐KOL并解释硬广风险。",
            "top_n": 4,
        },
    )
    assert chat.status_code == 200, chat.text
    body = chat.json()
    assert body["run"]["status"] == "waiting_approval"
    graph_artifacts = [item for item in body["artifacts"] if item["artifact_type"] == "reasoning_graph"]
    assert graph_artifacts
    graph = graph_artifacts[0]["payload"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_types = {node["type"] for node in nodes}
    assert {"brief", "intent", "plan_step", "knowledge", "creator", "proposal", "memory", "tool_trace"}.issubset(node_types)
    assert "risk" in node_types
    assert graph["summary"]["node_count"] == len(nodes)
    assert graph["summary"]["edge_count"] == len(edges)
    assert graph["summary"]["kol_count"] >= 1
    assert any(edge["type"] == "evidence" for edge in edges)
    assert any(edge["type"] == "match" for edge in edges)
    assert any(edge["type"] == "memory" for edge in edges)

    detail = client.get(f"/api/agent/runs/{body['run']['run_id']}", headers=HEADERS)
    assert detail.status_code == 200, detail.text
    assert any(item["artifact_type"] == "reasoning_graph" for item in detail.json()["artifacts"])

    print(
        "OK phase7g_agent_reasoning_graph "
        f"run={body['run']['run_id']} nodes={len(nodes)} edges={len(edges)}"
    )


if __name__ == "__main__":
    main()
