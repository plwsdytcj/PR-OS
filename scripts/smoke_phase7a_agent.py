from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = f"phase7a-agent-smoke-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "agent-admin@test.local", "name": "Agent Admin", "password": "agent-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text

    sample = client.post("/api/import/sample", headers=HEADERS)
    assert sample.status_code == 200, sample.text
    assert sample.json()["imported"] > 0

    chat = client.post(
        "/api/agent/chat",
        headers=HEADERS,
        json={
            "client_name": "Phase7A 新能源品牌",
            "project_name": "Agent Workspace Smoke",
            "message": "预算50万，新能源SUV上市预热，平台优先小红书和抖音，需要推荐KOL、生成方案和风险说明。",
            "top_n": 4,
        },
    )
    assert chat.status_code == 200, chat.text
    body = chat.json()
    run = body["run"]
    task = body["task"]
    events = body["events"]
    artifacts = body["artifacts"]
    assert run["status"] == "waiting_approval"
    assert task["status"] == "waiting_approval"
    assert len(events) >= 7
    assert {"knowledge", "project_run", "proposal"}.issubset({item["artifact_type"] for item in artifacts})
    proposal_artifacts = [item for item in artifacts if item["artifact_type"] == "proposal"]
    assert proposal_artifacts
    proposal_id = proposal_artifacts[0]["payload"]["summary"]["proposal_id"]

    tasks = client.get("/api/agent/tasks", headers=HEADERS)
    assert tasks.status_code == 200, tasks.text
    assert any(item["task"]["task_id"] == task["task_id"] for item in tasks.json()["items"])

    events_resp = client.get(f"/api/agent/runs/{run['run_id']}/events", headers=HEADERS)
    assert events_resp.status_code == 200, events_resp.text
    assert len(events_resp.json()["items"]) == len(events)

    approve = client.post(f"/api/agent/runs/{run['run_id']}/approve", headers=HEADERS)
    assert approve.status_code == 200, approve.text
    assert approve.json()["run"]["status"] == "approved"

    proposal = client.get(f"/api/collaboration/proposals/{proposal_id}", headers=HEADERS)
    assert proposal.status_code == 200, proposal.text
    assert proposal.json()["proposal"]["proposal_id"] == proposal_id

    print(f"OK phase7a_agent run={run['run_id']} events={len(events)} proposal={proposal_id}")


if __name__ == "__main__":
    main()
