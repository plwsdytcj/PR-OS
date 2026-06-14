from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.openclaw.schemas import OpenClawConfig
from src.openclaw.storage import save_config
from src.openclaw.adapter import OpenClawAdapter
from web.server import app


TENANT = f"openclaw-permissions-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}
ADMIN_EMAIL = "openclaw-admin@test.local"
ADMIN_PASSWORD = "Aa88005568"
CLIENT_EMAIL = "openclaw-client@brand.test"
CLIENT_PASSWORD = "client-pass-123"
STAFF_EMAIL = "openclaw-staff@test.local"
STAFF_PASSWORD = "staff-pass-123"
SERVICE_TOKEN = "smoke-openclaw-service-token"


def assert_ok(response, label: str) -> dict:
    assert response.status_code == 200, f"{label}: {response.status_code} {response.text}"
    return response.json()


def login(email: str, password: str) -> TestClient:
    client = TestClient(app)
    assert_ok(client.post("/api/auth/login", headers=HEADERS, json={"email": email, "password": password}), f"login {email}")
    return client


def main() -> None:
    admin = TestClient(app)
    bootstrap = assert_ok(
        admin.post(
            "/api/auth/bootstrap-admin",
            headers=HEADERS,
            json={"email": ADMIN_EMAIL, "name": "OpenClaw Admin", "password": ADMIN_PASSWORD},
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
            control_ui_url="http://openclaw-ui-smoke.local",
            admin_token=SERVICE_TOKEN,
            default_agent_id="kolness_permission_smoke",
        ),
    )

    company = assert_ok(
        admin.post("/api/auth/clients", headers=HEADERS, json={"name": "OpenClaw Client", "company": "Brand Co"}),
        "create client",
    )["client"]
    user = assert_ok(
        admin.post(
            f"/api/auth/clients/{company['client_id']}/users",
            headers=HEADERS,
            json={"email": CLIENT_EMAIL, "name": "Client Reviewer", "password": CLIENT_PASSWORD, "role": "client_reviewer"},
        ),
        "create client user",
    )["user"]
    assert user["user_type"] == "client"
    staff = assert_ok(
        admin.post(
            "/api/auth/users",
            headers=HEADERS,
            json={"email": STAFF_EMAIL, "name": "OpenClaw Staff", "password": STAFF_PASSWORD, "user_type": "internal", "role": "strategist"},
        ),
        "create staff",
    )["user"]
    assert staff["user_type"] == "internal"

    internal_openclaw = admin.get("/openclaw", headers=HEADERS)
    assert internal_openclaw.status_code == 200, internal_openclaw.text[:400]
    assert "Kolness × OpenClaw" in internal_openclaw.text

    internal_status = assert_ok(admin.get("/api/openclaw/status", headers=HEADERS), "internal openclaw status")
    assert internal_status["status"]["available"] is True

    run_payload = OpenClawAdapter().start_chat(db_path, user_id=bootstrap["user"]["user_id"], message="Owner-only OpenClaw run access smoke")
    run_id = run_payload["run"]["run_id"]
    admin_events = assert_ok(admin.get(f"/api/openclaw/runs/{run_id}/events", headers=HEADERS), "admin own run events")
    assert admin_events["run"]["run_id"] == run_id

    staff_client = login(STAFF_EMAIL, STAFF_PASSWORD)
    blocked_events = staff_client.get(f"/api/openclaw/runs/{run_id}/events", headers=HEADERS)
    assert blocked_events.status_code == 403, blocked_events.text
    blocked_save = staff_client.post(f"/api/openclaw/runs/{run_id}/save-to-campaign", headers=HEADERS, json={"client_name": "Blocked", "project_name": "Blocked"})
    assert blocked_save.status_code == 403, blocked_save.text

    client = login(CLIENT_EMAIL, CLIENT_PASSWORD)
    forbidden_checks = [
        ("GET", "/openclaw", None),
        ("GET", "/openclaw/proxy", None),
        ("GET", "/api/openclaw/status", None),
        ("GET", "/api/openclaw/me", None),
        ("POST", "/api/openclaw/sessions", {}),
        ("POST", "/api/openclaw/chat", {"message": "client should not run OpenClaw"}),
        ("GET", "/api/openclaw/tools", None),
    ]
    for method, path, payload in forbidden_checks:
        response = client.request(method, path, headers=HEADERS, json=payload)
        assert response.status_code in {401, 403}, f"{method} {path}: {response.status_code} {response.text}"

    public_client = TestClient(app)
    unauth_openclaw = public_client.get("/openclaw", headers=HEADERS)
    assert unauth_openclaw.status_code == 401, unauth_openclaw.text
    unauth_tools = public_client.get("/api/openclaw/tools", headers=HEADERS)
    assert unauth_tools.status_code == 401, unauth_tools.text

    service_headers = {**HEADERS, "Authorization": f"Bearer {SERVICE_TOKEN}"}
    tools = assert_ok(public_client.get("/api/openclaw/tools", headers=service_headers), "service token tools")
    assert len(tools["items"]) >= 10
    brief = assert_ok(
        public_client.post("/api/openclaw/tools/kolness.analyze_brief", headers=service_headers, json={"brief": "新能源 SUV 上市预热，预算50万"}),
        "service token analyze brief",
    )
    assert brief["tool"] == "kolness.analyze_brief"

    blocked_status = public_client.get("/api/openclaw/status", headers=service_headers)
    assert blocked_status.status_code == 401, blocked_status.text

    print("OK openclaw_permissions internal=allowed client=blocked service_token=tools_only")


if __name__ == "__main__":
    main()
