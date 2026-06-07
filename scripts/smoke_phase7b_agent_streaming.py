from __future__ import annotations

from pathlib import Path
import sys
import time
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = f"phase7b-agent-streaming-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "stream-admin@test.local", "name": "Stream Admin", "password": "stream-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text
    sample = client.post("/api/import/sample", headers=HEADERS)
    assert sample.status_code == 200, sample.text

    start = client.post(
        "/api/agent/chat/start",
        headers=HEADERS,
        json={
            "client_name": "Phase7B 新能源品牌",
            "project_name": "Streaming Agent Smoke",
            "message": "预算40万，新能源SUV上市预热，平台优先小红书，需要推荐KOL并生成客户提案。",
            "top_n": 3,
        },
    )
    assert start.status_code == 200, start.text
    run_id = start.json()["run"]["run_id"]

    final = None
    for _ in range(12):
        poll = client.get(f"/api/agent/runs/{run_id}/events", headers=HEADERS)
        assert poll.status_code == 200, poll.text
        events = poll.json()["items"]
        if events and events[-1]["title"] in {"等待人工确认", "Agent 执行失败"}:
            final = poll.json()
            break
        time.sleep(0.2)

    detail = client.get(f"/api/agent/runs/{run_id}", headers=HEADERS)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["run"]["status"] in {"waiting_approval", "failed"}
    assert body["run"]["status"] == "waiting_approval", body
    assert len(body["events"]) >= 7
    assert {"knowledge", "project_run", "proposal"}.issubset({item["artifact_type"] for item in body["artifacts"]})
    assert final is not None or body["events"]

    print(f"OK phase7b_agent_streaming run={run_id} events={len(body['events'])} artifacts={len(body['artifacts'])}")


if __name__ == "__main__":
    main()
