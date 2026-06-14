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
from web.server import app


TENANT = f"openclaw-diagnostics-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


class FakeGatewayOpenClawAdapter(OpenClawAdapter):
    def _send_message(self, config: OpenClawConfig, run, message: str) -> dict:
        return {
            "session_id": "diagnostics_session",
            "response": "推荐以下1个KOL：\n1. Diagnostics KOL，平台：小红书，理由：适合诊断 smoke。",
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
            json={"email": "openclaw-diagnostics@test.local", "name": "OpenClaw Diagnostics", "password": "Aa88005568"},
        ),
        "bootstrap admin",
    )
    user_id = bootstrap["user"]["user_id"]
    db_path = ROOT / "data" / "processed" / "tenants" / TENANT / "app.sqlite3"

    initial = assert_ok(client.get("/api/openclaw/diagnostics", headers=HEADERS), "initial diagnostics")
    assert "checks" in initial
    assert "status" in initial
    assert "run_summary" in initial

    save_config(
        db_path,
        OpenClawConfig(
            enabled=True,
            gateway_url="http://openclaw-diagnostics.local",
            control_ui_url="http://openclaw-ui-diagnostics.local",
            admin_token="diagnostics-token",
            default_agent_id="kolness_diagnostics_default",
        ),
    )
    bind = assert_ok(
        client.post(
            "/api/openclaw/bindings",
            headers=HEADERS,
            json={"user_id": user_id, "openclaw_agent_id": "kolness_diagnostics_agent", "openclaw_session_id": "diagnostics_session"},
        ),
        "bind diagnostics agent",
    )
    assert bind["binding"]["openclaw_agent_id"] == "kolness_diagnostics_agent"

    run_payload = FakeGatewayOpenClawAdapter().start_chat(
        db_path,
        user_id=user_id,
        message="OpenClaw diagnostics should see this completed run.",
    )
    assert run_payload["run"]["status"] == "completed"

    diagnostics = assert_ok(client.get("/api/openclaw/diagnostics", headers=HEADERS), "configured diagnostics")
    checks = diagnostics["checks"]
    assert diagnostics["status"]["available"] is True
    assert checks["enabled"] is True
    assert checks["gateway_url"] is True
    assert checks["control_ui_url"] is True
    assert checks["default_agent_id"] is True
    assert checks["admin_token"] is True
    assert checks["tool_count"] >= 10
    assert checks["binding_count"] == 1
    assert checks["active_binding_count"] == 1
    assert checks["run_count"] == 1
    assert checks["issues"] == []
    assert diagnostics["config"]["admin_token"] != "diagnostics-token"
    assert diagnostics["run_summary"]["by_status"]["completed"] == 1
    recent = diagnostics["run_summary"]["recent"][0]
    assert recent["run_id"] == run_payload["run"]["run_id"]
    assert recent["event_count"] >= 5

    client_company = assert_ok(
        client.post("/api/auth/clients", headers=HEADERS, json={"name": "Diagnostics Client", "company": "Brand Co"}),
        "create client company",
    )["client"]
    client_user = assert_ok(
        client.post(
            f"/api/auth/clients/{client_company['client_id']}/users",
            headers=HEADERS,
            json={"email": "diagnostics-client@brand.test", "name": "Diagnostics Client", "password": "client-pass-123", "role": "client_reviewer"},
        ),
        "create client user",
    )["user"]
    client_session = TestClient(app)
    assert_ok(client_session.post("/api/auth/login", headers=HEADERS, json={"email": client_user["email"], "password": "client-pass-123"}), "client login")
    forbidden = client_session.get("/api/openclaw/diagnostics", headers=HEADERS)
    assert forbidden.status_code == 403, forbidden.text

    print("OK openclaw_diagnostics checks=ready run_summary=completed client=blocked")


if __name__ == "__main__":
    main()
