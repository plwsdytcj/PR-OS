from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.openclaw.schemas import OpenClawConfig
from src.openclaw.storage import save_config
from web.server import app


TENANT = f"openclaw-workspace-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "openclaw-workspace@test.local", "name": "OpenClaw Workspace", "password": "Aa88005568"},
    )
    assert bootstrap.status_code == 200, bootstrap.text

    app_page = client.get("/app", headers=HEADERS)
    assert app_page.status_code == 200, app_page.text[:400]
    assert "agentFloatOpenNativeBtn" in app_page.text
    assert "openNativeOpenClawFromWorkspaceBtn" in app_page.text
    assert "app.js?v=20260614-3" in app_page.text

    unconfigured = client.get("/openclaw", headers=HEADERS)
    assert unconfigured.status_code == 200, unconfigured.text[:400]
    assert "OpenClaw 原生控制台还没接上" in unconfigured.text
    assert "返回 Kolness 工作台" in unconfigured.text

    db_path = ROOT / "data" / "processed" / "tenants" / TENANT / "app.sqlite3"
    save_config(
        db_path,
        OpenClawConfig(
            enabled=True,
            gateway_url="http://openclaw-smoke.local",
            control_ui_url="http://openclaw-ui-smoke.local",
            default_agent_id="kolness_workspace_smoke",
        ),
    )

    configured = client.get("/openclaw", headers=HEADERS)
    assert configured.status_code == 200, configured.text[:400]
    assert "Kolness × OpenClaw" in configured.text
    assert "Native OpenClaw UI" in configured.text
    assert "Kolness MCP Tools" in configured.text
    assert "kolness_workspace_smoke" in configured.text
    assert "<iframe src='/openclaw/proxy'" in configured.text

    print("OK openclaw_workspace buttons=2 native_shell=configured")


if __name__ == "__main__":
    main()
