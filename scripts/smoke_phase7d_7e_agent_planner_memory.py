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


TENANT = f"phase7d7e-agent-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "planner-admin@test.local", "name": "Planner Admin", "password": "planner-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text

    clarification = client.post(
        "/api/agent/chat",
        headers=HEADERS,
        json={
            "client_name": "模糊客户",
            "project_name": "模糊项目",
            "message": "帮我做一个PR方案。",
            "top_n": 3,
        },
    )
    assert clarification.status_code == 200, clarification.text
    clarification_body = clarification.json()
    assert clarification_body["run"]["status"] == "waiting_clarification"
    clarification_types = {item["artifact_type"] for item in clarification_body["artifacts"]}
    assert {"plan", "clarification"}.issubset(clarification_types)
    assert "预算" in clarification_body["run"]["final_answer"]

    sample = client.post("/api/import/sample", headers=HEADERS)
    assert sample.status_code == 200, sample.text

    full = client.post(
        "/api/agent/chat",
        headers=HEADERS,
        json={
            "client_name": "Phase7D 新能源品牌",
            "project_name": "Planner Memory Smoke",
            "message": "预算40万，新能源SUV上市预热，平台优先小红书和抖音，需要推荐KOL、生成客户方案并说明硬广风险。",
            "top_n": 3,
        },
    )
    assert full.status_code == 200, full.text
    body = full.json()
    assert body["run"]["status"] == "waiting_approval"
    artifacts = body["artifacts"]
    artifact_types = {item["artifact_type"] for item in artifacts}
    assert {"plan", "knowledge", "project_run", "proposal", "tool_trace", "memory_suggestions"}.issubset(artifact_types)

    plan = next(item for item in artifacts if item["artifact_type"] == "plan")
    assert plan["payload"]["status"] == "ready"
    assert len(plan["payload"]["steps"]) >= 5

    trace = next(item for item in artifacts if item["artifact_type"] == "tool_trace")
    trace_tools = {item["tool_name"] for item in trace["payload"]["items"]}
    assert {"search_knowledge", "run_project", "create_proposal", "suggest_memory"}.issubset(trace_tools)
    assert all("elapsed_ms" in item for item in trace["payload"]["items"])

    memory = next(item for item in artifacts if item["artifact_type"] == "memory_suggestions")
    assert len(memory["payload"]["suggestions"]) >= 3
    commit = client.post(
        f"/api/agent/artifacts/{memory['artifact_id']}/knowledge",
        headers=HEADERS,
        json={"suggestion_index": 0},
    )
    assert commit.status_code == 200, commit.text
    document = commit.json()["document"]
    assert document["source_type"] == "case"

    search = client.post(
        "/api/knowledge/search",
        headers=HEADERS,
        json={"query": "Planner Memory Smoke 新能源 KOL 推荐", "top_k": 5},
    )
    assert search.status_code == 200, search.text
    assert any(item["ref_id"] == document["document_id"] for item in search.json()["items"])

    refreshed = client.get(f"/api/agent/runs/{body['run']['run_id']}", headers=HEADERS)
    assert refreshed.status_code == 200, refreshed.text
    refreshed_memory = next(item for item in refreshed.json()["artifacts"] if item["artifact_id"] == memory["artifact_id"])
    assert refreshed_memory["payload"]["committed"]["0"]["document_id"] == document["document_id"]

    print(
        "OK phase7d7e_agent "
        f"run={body['run']['run_id']} document={document['document_id']} traces={len(trace['payload']['items'])}"
    )


if __name__ == "__main__":
    main()
