from __future__ import annotations

import time
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = f"phase7h-agent-thread-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def wait_for_run(client: TestClient, run_id: str) -> dict:
    body = {}
    for _ in range(18):
        detail = client.get(f"/api/agent/runs/{run_id}", headers=HEADERS)
        assert detail.status_code == 200, detail.text
        body = detail.json()
        if body["run"]["status"] not in {"running"}:
            return body
        time.sleep(0.2)
    return body


def main() -> None:
    client = TestClient(app)
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "phase7h-admin@test.local", "name": "Phase7H Admin", "password": "phase7h-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text

    sample = client.post("/api/import/sample", headers=HEADERS)
    assert sample.status_code == 200, sample.text

    create = client.post(
        "/api/agent/threads",
        headers=HEADERS,
        json={
            "client_name": "Phase7H 新能源品牌",
            "project_name": "Thread Chat Smoke",
            "message": "预算50万，新能源SUV上市预热，目标年轻用户，平台优先小红书和抖音，需要推荐KOL。",
        },
    )
    assert create.status_code == 200, create.text
    thread_id = create.json()["thread"]["thread_id"]
    assert create.json()["messages"][0]["role"] == "user"

    first = client.post(
        f"/api/agent/threads/{thread_id}/messages",
        headers=HEADERS,
        json={"message": "先跑一版候选名单，并说明硬广风险。", "top_n": 3},
    )
    assert first.status_code == 200, first.text
    first_run_id = first.json()["run"]["run_id"]
    first_detail = wait_for_run(client, first_run_id)
    assert first_detail["run"]["status"] == "waiting_approval", first_detail

    second = client.post(
        f"/api/agent/threads/{thread_id}/messages",
        headers=HEADERS,
        json={"message": "预算降到30万，小红书优先，换成更年轻的生活方式KOL。", "top_n": 3},
    )
    assert second.status_code == 200, second.text
    second_run_id = second.json()["run"]["run_id"]
    second_detail = wait_for_run(client, second_run_id)
    assert second_detail["run"]["status"] == "waiting_approval", second_detail

    detail = client.get(f"/api/agent/threads/{thread_id}", headers=HEADERS)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    messages = body["messages"]
    assert len(messages) >= 5, messages
    assert [item["role"] for item in messages].count("user") >= 3
    assert [item["role"] for item in messages].count("assistant") >= 2
    assert len(body["runs"]) >= 2
    assert {"project_run", "proposal", "reasoning_graph"}.issubset({item["artifact_type"] for item in body["artifacts"]})

    threads = client.get("/api/agent/threads", headers=HEADERS)
    assert threads.status_code == 200, threads.text
    assert any(item["thread"]["thread_id"] == thread_id for item in threads.json()["items"])

    print(f"OK phase7h_agent_threads thread={thread_id} runs={len(body['runs'])} messages={len(messages)}")


if __name__ == "__main__":
    main()
