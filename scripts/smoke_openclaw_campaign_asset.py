from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.openclaw.adapter import OpenClawAdapter
from src.openclaw.schemas import OpenClawConfig
from src.openclaw.storage import save_config
from src.platform_os.storage import load_campaign_project
from web.server import app


TENANT = f"openclaw-campaign-asset-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


class FakeGatewayOpenClawAdapter(OpenClawAdapter):
    def _send_message(self, config: OpenClawConfig, run, message: str) -> dict:
        return {
            "session_id": "campaign_asset_session",
            "response": (
                "推荐以下3个KOL：\n"
                "1. 城市车生活，平台：小红书，理由：适合新能源 SUV 年轻家庭场景。\n"
                "2. 智驾测评Lab，平台：抖音，理由：适合讲智能化和安全配置。\n"
                "3. 周末露营研究所，平台：小红书，理由：适合做城市周末生活方式内容。\n"
                "主要风险：报价、履约节奏和内容夸大需提前确认。"
            ),
        }


def assert_ok(response, label: str) -> dict:
    assert response.status_code == 200, f"{label}: {response.status_code} {response.text}"
    return response.json()


def main() -> None:
    client = TestClient(app)
    bootstrap = assert_ok(
        client.post(
            "/api/auth/bootstrap-admin",
            headers=HEADERS,
            json={"email": "openclaw-asset@test.local", "name": "OpenClaw Asset", "password": "Aa88005568"},
        ),
        "bootstrap admin",
    )
    user_id = bootstrap["user"]["user_id"]
    db_path = ROOT / "data" / "processed" / "tenants" / TENANT / "app.sqlite3"
    save_config(
        db_path,
        OpenClawConfig(
            enabled=True,
            gateway_url="http://openclaw-smoke.local",
            default_agent_id="kolness_asset_smoke",
        ),
    )

    run_payload = FakeGatewayOpenClawAdapter().start_chat(
        db_path,
        user_id=user_id,
        message="预算50万，新能源 SUV 上市预热，需要推荐 KOL，并沉淀成 Campaign 资产。",
        campaign_id="",
    )
    run = run_payload["run"]
    assert run["status"] == "completed", run
    assert any(event["event_type"] == "message.completed" for event in run_payload["events"]), run_payload["events"]

    saved = assert_ok(
        client.post(
            f"/api/openclaw/runs/{run['run_id']}/save-to-campaign",
            headers=HEADERS,
            json={"client_name": "OpenClaw 汽车客户", "project_name": "OpenClaw 深度任务沉淀", "top_n": 6},
        ),
        "save openclaw run",
    )
    campaign = saved["campaign"]
    assert campaign["status"] == "openclaw_saved", campaign
    assert saved["target"]["view"] == "platformOS"
    campaign_id = campaign["campaign_id"]

    project = load_campaign_project(db_path, campaign_id)
    assert project is not None
    assert project.campaign.client_name == "OpenClaw 汽车客户"
    saved_event = next((event for event in project.timeline if event.get("event_type") == "openclaw_run_saved"), None)
    assert saved_event is not None, project.timeline
    event_payload = saved_event["payload"]
    assert event_payload["run_id"] == run["run_id"]
    assert event_payload["status"] == "completed"
    assert "城市车生活" in event_payload["response"]
    assert any(event["event_type"] == "message.completed" for event in event_payload["events"])

    history = assert_ok(client.get("/api/history/workspace", headers=HEADERS), "workspace history")
    item = next((entry for entry in history["items"] if entry["id"] == campaign_id), None)
    assert item is not None, history["items"][:5]
    assert item["type"] == "campaign"
    assert item["status"] == "openclaw_saved"
    assert item["target"] == {"view": "platformOS", "action": "campaign", "id": campaign_id}

    room = assert_ok(client.get(f"/api/platform/campaigns/{campaign_id}/room", headers=HEADERS), "campaign room")["room"]
    assert room["campaign"]["campaign_id"] == campaign_id
    assert room["campaign"]["status"] == "openclaw_saved"
    room_event = next((event for event in room["timeline"] if event.get("event_type") == "openclaw_run_saved"), None)
    assert room_event is not None, room["timeline"]
    assert room_event["payload"]["run_id"] == run["run_id"]
    assert "城市车生活" in room_event["payload"]["response"]

    print(f"OK openclaw_campaign_asset campaign={campaign_id} timeline={len(project.timeline)}")


if __name__ == "__main__":
    main()
