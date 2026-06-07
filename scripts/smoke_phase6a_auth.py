from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = f"phase6a-auth-smoke-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    admin = TestClient(app)
    status = admin.get("/api/status", headers=HEADERS)
    assert status.status_code == 200

    bootstrap = admin.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "admin@agency.test", "name": "Agency Admin", "password": "admin-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text
    assert bootstrap.json()["user"]["role"] == "admin"

    anonymous = TestClient(app)
    protected = anonymous.get("/api/creators", headers=HEADERS)
    assert protected.status_code == 401

    client_account = admin.post("/api/auth/clients", headers=HEADERS, json={"name": "某新能源汽车品牌", "company": "品牌公司"})
    assert client_account.status_code == 200, client_account.text
    client_id = client_account.json()["client"]["client_id"]

    client_user = admin.post(
        f"/api/auth/clients/{client_id}/users",
        headers=HEADERS,
        json={
            "email": "reviewer@brand.test",
            "name": "Brand Reviewer",
            "password": "client-pass-123",
            "role": "client_reviewer",
        },
    )
    assert client_user.status_code == 200, client_user.text
    assert client_user.json()["user"]["user_type"] == "client"

    proposal = admin.post(
        "/api/collaboration/proposals",
        headers=HEADERS,
        json={
            "client_name": "某新能源汽车品牌",
            "project_name": "Phase6A Client Portal",
            "brief": "预算50万，新能源SUV上市预热，平台优先抖音、小红书，需要甲方确认KOL。",
            "top_n": 3,
        },
    )
    assert proposal.status_code == 200, proposal.text
    proposal_body = proposal.json()["proposal"]
    proposal_id = proposal_body["proposal_id"]
    share_token = proposal_body["share_token"]

    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        headers=HEADERS,
        json={"email": "reviewer@brand.test", "password": "client-pass-123"},
    )
    assert login.status_code == 200, login.text
    me = client.get("/api/auth/me", headers=HEADERS)
    assert me.json()["identity"]["user"]["user_type"] == "client"

    forbidden = client.get("/api/creators", headers=HEADERS)
    assert forbidden.status_code == 403

    projects = client.get("/api/client/portal/projects", headers=HEADERS)
    assert projects.status_code == 200, projects.text
    assert any(item["proposal_id"] == proposal_id for item in projects.json()["items"])

    portal = client.get(f"/api/client/portal/proposals/{proposal_id}", headers=HEADERS)
    assert portal.status_code == 200, portal.text
    assert portal.json()["proposal"]["proposal_id"] == proposal_id

    feedback = client.post(
        f"/api/client/portal/proposals/{proposal_id}/feedback",
        headers=HEADERS,
        json={"target_type": "proposal", "comment": "甲方登录态反馈通过。"},
    )
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["feedback"]["created_by"].startswith("user_")

    public_share = anonymous.get(f"/api/client/share/{share_token}", headers=HEADERS)
    assert public_share.status_code == 200, public_share.text
    assert public_share.json()["proposal"]["proposal_id"] == proposal_id

    print(f"OK phase6a_auth proposal={proposal_id} client={client_id}")


if __name__ == "__main__":
    main()
