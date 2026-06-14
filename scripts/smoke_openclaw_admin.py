from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.openclaw.storage import load_binding, load_config
from web.server import app


TENANT = f"openclaw-admin-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}
ADMIN_EMAIL = "openclaw-admin-console@test.local"
ADMIN_PASSWORD = "Aa88005568"
STAFF_EMAIL = "openclaw-staff@test.local"
STAFF_PASSWORD = "staff-pass-123"
CLIENT_EMAIL = "openclaw-admin-client@brand.test"
CLIENT_PASSWORD = "client-pass-123"
ADMIN_TOKEN = "smoke-admin-token-secret"


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
            json={"email": ADMIN_EMAIL, "name": "OpenClaw Admin Console", "password": ADMIN_PASSWORD},
        ),
        "bootstrap admin",
    )
    assert bootstrap["user"]["role"] == "admin"

    staff = assert_ok(
        admin.post(
            "/api/auth/users",
            headers=HEADERS,
            json={"email": STAFF_EMAIL, "name": "OpenClaw Staff", "password": STAFF_PASSWORD, "user_type": "internal", "role": "strategist"},
        ),
        "create staff",
    )["user"]
    client_company = assert_ok(
        admin.post("/api/auth/clients", headers=HEADERS, json={"name": "OpenClaw Admin Client", "company": "Brand Co"}),
        "create client company",
    )["client"]
    client_user = assert_ok(
        admin.post(
            f"/api/auth/clients/{client_company['client_id']}/users",
            headers=HEADERS,
            json={"email": CLIENT_EMAIL, "name": "Client User", "password": CLIENT_PASSWORD, "role": "client_reviewer"},
        ),
        "create client user",
    )["user"]

    saved = assert_ok(
        admin.post(
            "/api/openclaw/config",
            headers=HEADERS,
            json={
                "enabled": True,
                "gateway_url": "http://openclaw-gateway-smoke.local",
                "control_ui_url": "http://openclaw-ui-smoke.local",
                "default_agent_id": "kolness_admin_default",
                "proxy_base_path": "/openclaw",
                "admin_token": ADMIN_TOKEN,
            },
        ),
        "save openclaw config",
    )
    assert saved["status"]["available"] is True
    assert saved["config"]["admin_token"] != ADMIN_TOKEN
    assert saved["config"]["admin_token"].startswith("smok")

    db_path = ROOT / "data" / "processed" / "tenants" / TENANT / "app.sqlite3"
    raw_config = load_config(db_path)
    assert raw_config.admin_token == ADMIN_TOKEN
    assert raw_config.gateway_url == "http://openclaw-gateway-smoke.local"

    listed = assert_ok(admin.get("/api/openclaw/config", headers=HEADERS), "list openclaw config")
    assert listed["config"]["admin_token"] != ADMIN_TOKEN
    assert listed["config"]["default_agent_id"] == "kolness_admin_default"

    binding_payload = {
        "user_id": staff["user_id"],
        "openclaw_agent_id": "kolness_staff_agent",
        "openclaw_session_id": "staff_session_001",
        "status": "active",
    }
    binding_response = assert_ok(admin.post("/api/openclaw/bindings", headers=HEADERS, json=binding_payload), "bind staff agent")
    assert binding_response["binding"]["openclaw_agent_id"] == "kolness_staff_agent"
    binding = load_binding(db_path, staff["user_id"])
    assert binding is not None
    assert binding.openclaw_session_id == "staff_session_001"

    client_binding = admin.post(
        "/api/openclaw/bindings",
        headers=HEADERS,
        json={"user_id": client_user["user_id"], "openclaw_agent_id": "should_not_bind"},
    )
    assert client_binding.status_code == 404, client_binding.text

    staff_client = login(STAFF_EMAIL, STAFF_PASSWORD)
    staff_config = staff_client.get("/api/openclaw/config", headers=HEADERS)
    assert staff_config.status_code == 403, staff_config.text
    staff_save = staff_client.post("/api/openclaw/config", headers=HEADERS, json={"enabled": False})
    assert staff_save.status_code == 403, staff_save.text
    staff_bind = staff_client.post("/api/openclaw/bindings", headers=HEADERS, json=binding_payload)
    assert staff_bind.status_code == 403, staff_bind.text

    client = login(CLIENT_EMAIL, CLIENT_PASSWORD)
    client_config = client.get("/api/openclaw/config", headers=HEADERS)
    assert client_config.status_code == 403, client_config.text
    client_save = client.post("/api/openclaw/config", headers=HEADERS, json={"enabled": False})
    assert client_save.status_code == 403, client_save.text

    print("OK openclaw_admin config=masked binding=internal_only admin_only=true")


if __name__ == "__main__":
    main()
