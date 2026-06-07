from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = f"phase6b-org-smoke-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    admin = TestClient(app)
    bootstrap = admin.post(
        "/api/auth/bootstrap-admin",
        headers=HEADERS,
        json={"email": "admin@agency.test", "name": "Agency Admin", "password": "admin-pass-123"},
    )
    assert bootstrap.status_code == 200, bootstrap.text

    internal = admin.post(
        "/api/auth/users",
        headers=HEADERS,
        json={"email": "planner@agency.test", "name": "Planner", "password": "planner-pass-123", "user_type": "internal", "role": "strategist"},
    )
    assert internal.status_code == 200, internal.text

    client_account = admin.post("/api/auth/clients", headers=HEADERS, json={"name": "Phase6B Demo Brand", "company": "Demo Brand Co."})
    assert client_account.status_code == 200, client_account.text
    client_id = client_account.json()["client"]["client_id"]

    client_user = admin.post(
        f"/api/auth/clients/{client_id}/users",
        headers=HEADERS,
        json={
            "email": "reviewer@phase6b.test",
            "name": "Client Reviewer",
            "password": "client-pass-123",
            "role": "client_reviewer",
        },
    )
    assert client_user.status_code == 200, client_user.text
    user_id = client_user.json()["user"]["user_id"]

    proposal = admin.post(
        "/api/collaboration/proposals",
        headers=HEADERS,
        json={
            "client_name": "Phase6B Demo Brand",
            "project_name": "Phase6B Org Console",
            "brief": "预算50万，新能源SUV上市预热，需要甲方登录后查看KOL方案并反馈。",
            "top_n": 3,
        },
    )
    assert proposal.status_code == 200, proposal.text
    proposal_id = proposal.json()["proposal"]["proposal_id"]

    grant = admin.post(
        "/api/auth/project-access",
        headers=HEADERS,
        json={"user_id": user_id, "client_id": client_id, "proposal_id": proposal_id, "permissions": ["view", "comment"]},
    )
    assert grant.status_code == 200, grant.text

    users = admin.get("/api/auth/users", headers=HEADERS)
    clients = admin.get("/api/auth/clients", headers=HEADERS)
    access = admin.get("/api/auth/project-access", headers=HEADERS)
    assert users.status_code == 200, users.text
    assert clients.status_code == 200, clients.text
    assert access.status_code == 200, access.text
    assert any(item["email"] == "planner@agency.test" for item in users.json()["items"])
    assert any(item["client_id"] == client_id and item["members"] for item in clients.json()["items"])
    assert any(item["proposal_id"] == proposal_id and item["user_id"] == user_id for item in access.json()["items"])

    client = TestClient(app)
    login = client.post("/api/auth/login", headers=HEADERS, json={"email": "reviewer@phase6b.test", "password": "client-pass-123"})
    assert login.status_code == 200, login.text
    portal = client.get("/api/client/portal/projects", headers=HEADERS)
    assert portal.status_code == 200, portal.text
    assert any(item["proposal_id"] == proposal_id for item in portal.json()["items"])

    forbidden = client.get("/api/auth/project-access", headers=HEADERS)
    assert forbidden.status_code == 403

    print(f"OK phase6b_org users={len(users.json()['items'])} clients={len(clients.json()['items'])} access={len(access.json()['items'])}")


if __name__ == "__main__":
    main()
