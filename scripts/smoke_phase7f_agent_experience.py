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


TENANT = f"phase7f-agent-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "phase7f-admin@test.local", "name": "Phase7F Admin", "password": "phase7f-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text

    sample = client.post("/api/import/sample", headers=HEADERS)
    assert sample.status_code == 200, sample.text

    planned = client.post(
        "/api/agent/chat",
        headers=HEADERS,
        json={
            "client_name": "Phase7F 新能源品牌",
            "project_name": "Plan Approval Smoke",
            "message": "预算40万，新能源SUV上市预热，平台优先小红书和抖音，需要推荐KOL并说明风险。",
            "top_n": 3,
            "require_plan_approval": True,
        },
    )
    assert planned.status_code == 200, planned.text
    planned_body = planned.json()
    assert planned_body["run"]["status"] == "waiting_plan_approval"
    assert {item["artifact_type"] for item in planned_body["artifacts"]} == {"plan"}

    approved = client.post(
        f"/api/agent/runs/{planned_body['run']['run_id']}/approve-plan",
        headers=HEADERS,
        json={"top_n": 3},
    )
    assert approved.status_code == 200, approved.text
    approved_body = approved.json()
    assert approved_body["run"]["status"] == "waiting_approval"
    approved_types = {item["artifact_type"] for item in approved_body["artifacts"]}
    assert {"plan", "tool_trace", "memory_suggestions", "proposal"}.issubset(approved_types)

    memory = next(item for item in approved_body["artifacts"] if item["artifact_type"] == "memory_suggestions")
    commit = client.post(
        f"/api/agent/artifacts/{memory['artifact_id']}/knowledge",
        headers=HEADERS,
        json={
            "suggestion_index": 0,
            "override": {
                "title": "Phase7F 编辑后入库案例",
                "content": "这是 Phase7F smoke 编辑后的知识内容，包含计划确认、artifact detail 和 memory review。",
                "tags": "Phase7F,编辑入库,Agent体验",
            },
        },
    )
    assert commit.status_code == 200, commit.text
    document = commit.json()["document"]
    assert document["title"] == "Phase7F 编辑后入库案例"
    assert "编辑入库" in document["tags"]

    cancelled = client.post(
        "/api/agent/chat",
        headers=HEADERS,
        json={
            "client_name": "Phase7F 取消客户",
            "project_name": "Cancel Smoke",
            "message": "预算20万，新能源SUV上市预热，平台优先小红书，需要推荐KOL。",
            "top_n": 3,
            "require_plan_approval": True,
        },
    )
    assert cancelled.status_code == 200, cancelled.text
    cancel_run_id = cancelled.json()["run"]["run_id"]
    cancel = client.post(f"/api/agent/runs/{cancel_run_id}/cancel", headers=HEADERS)
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["run"]["status"] == "cancelled"

    unclear = client.post(
        "/api/agent/chat",
        headers=HEADERS,
        json={"client_name": "Phase7F 追问客户", "project_name": "Clarification Smoke", "message": "帮我做一个PR方案。", "top_n": 3},
    )
    assert unclear.status_code == 200, unclear.text
    unclear_body = unclear.json()
    assert unclear_body["run"]["status"] == "waiting_clarification"
    resumed = client.post(
        f"/api/agent/runs/{unclear_body['run']['run_id']}/clarification",
        headers=HEADERS,
        json={"supplement": "预算30万，产品是新能源SUV，平台优先小红书和抖音，目标年轻用户。", "top_n": 3},
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["run"]["status"] == "waiting_approval"

    print(
        "OK phase7f_agent_experience "
        f"approved_run={approved_body['run']['run_id']} document={document['document_id']}"
    )


if __name__ == "__main__":
    main()
