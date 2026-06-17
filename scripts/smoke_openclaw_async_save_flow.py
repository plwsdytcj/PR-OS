from __future__ import annotations

from pathlib import Path
import sys
import time
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.openclaw.schemas import OpenClawConfig
from src.openclaw.storage import save_config
from web.server import app


TENANT = f"openclaw-async-save-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def assert_ok(response, label: str) -> dict:
    assert response.status_code == 200, f"{label}: {response.status_code} {response.text}"
    return response.json()


def fake_send_message(self, config, run, message: str) -> dict:
    return {
        "session_id": "async_save_session",
        "response": (
            "推荐以下2个KOL：\n"
            "1. Async 汽车生活家，平台：小红书，理由：适合新能源 SUV 年轻家庭场景。\n"
            "2. Async 智驾测评，平台：抖音，理由：适合解释智能化和安全配置。\n"
            "主要风险：预算分配、履约排期和内容夸大。"
        ),
    }


def main() -> None:
    client = TestClient(app)
    bootstrap = assert_ok(
        client.post(
            "/api/auth/bootstrap-admin",
            headers=HEADERS,
            json={"email": "openclaw-async-save@test.local", "name": "Async Save", "password": "Aa88005568"},
        ),
        "bootstrap admin",
    )
    assert bootstrap["user"]["user_type"] == "internal"

    db_path = ROOT / "data" / "processed" / "tenants" / TENANT / "app.sqlite3"
    save_config(
        db_path,
        OpenClawConfig(
            enabled=True,
            gateway_url="http://openclaw-smoke.local",
            default_agent_id="kolness_async_save_smoke",
        ),
    )

    with patch("src.openclaw.adapter.OpenClawAdapter._send_message", fake_send_message):
        started = assert_ok(
            client.post(
                "/api/openclaw/chat",
                headers=HEADERS,
                json={
                    "async": True,
                    "client_name": "Async 保存客户",
                    "project_name": "Async OpenClaw 保存测试",
                    "message": "预算50万，新能源 SUV 上市预热，需要推荐 KOL 并保存成 Campaign。",
                    "top_n": 5,
                },
            ),
            "start async openclaw",
        )

    run_id = started["run"]["run_id"]
    assert started["run"]["status"] == "running", started
    assert [event["event_type"] for event in started["events"]] == ["message.created"]

    completed = {}
    for _ in range(20):
        completed = assert_ok(client.get(f"/api/openclaw/runs/{run_id}/events", headers=HEADERS), "poll async openclaw")
        if completed["run"]["status"] != "running":
            break
        time.sleep(0.2)
    assert completed["run"]["status"] == "completed", completed
    assert "Async 汽车生活家" in completed["run"]["response"]
    assert any(event["event_type"] == "message.completed" for event in completed["events"])

    saved = assert_ok(
        client.post(
            f"/api/openclaw/runs/{run_id}/save-to-campaign",
            headers=HEADERS,
            json={"client_name": "Async 保存客户", "project_name": "Async OpenClaw 保存测试", "top_n": 5},
        ),
        "save async openclaw",
    )
    campaign_id = saved["campaign"]["campaign_id"]
    assert saved["campaign"]["status"] == "openclaw_saved"
    assert saved["target"] == {"view": "platformOS", "action": "campaign", "id": campaign_id}

    room = assert_ok(client.get(f"/api/platform/campaigns/{campaign_id}/room", headers=HEADERS), "async campaign room")["room"]
    room_event = next((event for event in room["timeline"] if event.get("event_type") == "openclaw_run_saved"), None)
    assert room_event is not None, room["timeline"]
    assert room_event["payload"]["run_id"] == run_id
    assert room_event["payload"]["status"] == "completed"
    assert "Async 汽车生活家" in room_event["payload"]["response"]

    print(f"OK openclaw_async_save_flow run={run_id} campaign={campaign_id} events={len(completed['events'])}")


if __name__ == "__main__":
    main()
