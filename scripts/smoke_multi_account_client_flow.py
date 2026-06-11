from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = f"multi-account-flow-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}
ADMIN_EMAIL = "admin@agency.test"
ADMIN_PASSWORD = "admin-pass-123"


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
            json={"email": ADMIN_EMAIL, "name": "Agency Admin", "password": ADMIN_PASSWORD},
        ),
        "bootstrap admin",
    )
    assert bootstrap["user"]["user_type"] == "internal"
    assert bootstrap["user"]["role"] == "admin"

    internal_specs = [
        ("strategist@agency.test", "策略负责人", "strategist", "strategist-pass-123"),
        ("buyer@agency.test", "媒介采买", "media_buyer", "buyer-pass-123"),
        ("viewer@agency.test", "只读同事", "viewer", "viewer-pass-123"),
    ]
    for email, name, role, password in internal_specs:
        user = assert_ok(
            admin.post(
                "/api/auth/users",
                headers=HEADERS,
                json={"email": email, "name": name, "password": password, "user_type": "internal", "role": role},
            ),
            f"create internal {email}",
        )
        assert user["user"]["user_type"] == "internal"
        assert user["user"]["role"] == role

    strategist = login("strategist@agency.test", "strategist-pass-123")
    viewer = login("viewer@agency.test", "viewer-pass-123")

    intake = assert_ok(
        strategist.post(
            "/api/kol-intake",
            headers=HEADERS,
            data={
                "input_type": "text",
                "name": "多账号链路种子达人",
                "text": "\n".join(
                    [
                        "达人：小红书家庭出行测评 KOL",
                        "平台：小红书｜粉丝：18万｜报价：22000",
                        "内容：新能源 SUV 真实试驾、儿童安全座椅、城市通勤、家庭露营",
                        "适合：新品预热、家庭安全背书、真实体验种草",
                        "风险：需要控制硬广比例",
                    ]
                ),
                "replace": "false",
            },
        ),
        "strategist kol intake",
    )
    assert intake["imported"] >= 1
    assert sum(item["tag_count"] for item in intake["tag_summary"]) > 0

    viewer_write = viewer.post(
        "/api/kol-intake",
        headers=HEADERS,
        data={"input_type": "text", "text": "只读账号不应该能写入"},
    )
    assert viewer_write.status_code == 403, viewer_write.text

    client_specs = [
        ("Nova EV", "Nova EV China", "新能源 SUV 上市预热，目标年轻家庭，强调智驾、儿童安全和城市通勤。"),
        ("Glow Lab", "Glow Lab Beauty", "护肤新品种草，目标成分党和职场女性，强调真实测评和温和修护。"),
        ("City Go", "City Go Travel", "城市周末出行 App 拉新，目标年轻白领，强调轻决策和本地生活。"),
    ]

    created_clients: list[dict] = []
    created_users: list[dict] = []
    proposals: list[dict] = []

    for index, (client_name, company, brief) in enumerate(client_specs, start=1):
        client_account = assert_ok(
            admin.post("/api/auth/clients", headers=HEADERS, json={"name": client_name, "company": company}),
            f"create client {client_name}",
        )["client"]
        created_clients.append(client_account)

        for role in ["client_owner", "client_reviewer", "client_viewer"]:
            email = f"{role}.{index}@brand.test"
            user = assert_ok(
                admin.post(
                    f"/api/auth/clients/{client_account['client_id']}/users",
                    headers=HEADERS,
                    json={
                        "email": email,
                        "name": f"{client_name} {role}",
                        "password": f"{role}-pass-123",
                        "role": role,
                    },
                ),
                f"create {role} for {client_name}",
            )["user"]
            assert user["user_type"] == "client"
            assert user["role"] == role
            created_users.append(user)

        recommendation = assert_ok(
            strategist.post(
                "/api/kol-intelligence/conversation/run",
                headers=HEADERS,
                json={"message": brief, "client_name": client_name, "project_name": f"{client_name} Campaign", "top_n": 3},
            ),
            f"brief recommendation {client_name}",
        )
        assert recommendation["graph_frames"], client_name
        assert recommendation["recommendations"], client_name

        proposal = assert_ok(
            strategist.post(
                "/api/collaboration/proposals",
                headers=HEADERS,
                json={"client_name": client_name, "project_name": f"{client_name} Campaign", "brief": brief, "top_n": 3},
            ),
            f"create proposal {client_name}",
        )["proposal"]
        proposals.append(proposal)

        client_users = [user for user in created_users if user["client_id"] == client_account["client_id"]]
        for user in client_users:
            grant = assert_ok(
                admin.post(
                    "/api/auth/project-access",
                    headers=HEADERS,
                    json={
                        "user_id": user["user_id"],
                        "client_id": client_account["client_id"],
                        "proposal_id": proposal["proposal_id"],
                        "permissions": ["view", "comment"],
                    },
                ),
                f"grant {user['email']}",
            )
            assert grant["access"]["proposal_id"] == proposal["proposal_id"]

    users = assert_ok(admin.get("/api/auth/users", headers=HEADERS), "list users")["items"]
    clients = assert_ok(admin.get("/api/auth/clients", headers=HEADERS), "list clients")["items"]
    access = assert_ok(admin.get("/api/auth/project-access", headers=HEADERS), "list access")["items"]
    assert len([item for item in users if item["user_type"] == "internal"]) == 4
    assert len([item for item in users if item["user_type"] == "client"]) == 9
    assert len(clients) == 3
    assert len(access) == 9

    first_owner = login("client_owner.1@brand.test", "client_owner-pass-123")
    first_reviewer = login("client_reviewer.1@brand.test", "client_reviewer-pass-123")
    first_viewer = login("client_viewer.1@brand.test", "client_viewer-pass-123")
    second_reviewer = login("client_reviewer.2@brand.test", "client_reviewer-pass-123")

    owner_me = assert_ok(first_owner.get("/api/auth/me", headers=HEADERS), "owner me")
    assert owner_me["identity"]["user"]["user_type"] == "client"

    owner_projects = assert_ok(first_owner.get("/api/client/portal/projects", headers=HEADERS), "owner projects")["items"]
    assert [item["proposal_id"] for item in owner_projects] == [proposals[0]["proposal_id"]]

    cross_client = second_reviewer.get(f"/api/client/portal/proposals/{proposals[0]['proposal_id']}", headers=HEADERS)
    assert cross_client.status_code == 403, cross_client.text

    internal_forbidden = first_owner.get("/api/creators", headers=HEADERS)
    assert internal_forbidden.status_code == 403, internal_forbidden.text

    portal = assert_ok(first_reviewer.get(f"/api/client/portal/proposals/{proposals[0]['proposal_id']}", headers=HEADERS), "reviewer portal")
    assert portal["proposal"]["proposal_id"] == proposals[0]["proposal_id"]

    feedback = assert_ok(
        first_reviewer.post(
            f"/api/client/portal/proposals/{proposals[0]['proposal_id']}/feedback",
            headers=HEADERS,
            json={"target_type": "proposal", "decision": "maybe", "comment": "预算可以，想替换一个更偏家庭场景的 KOL。"},
        ),
        "reviewer feedback",
    )
    assert feedback["feedback"]["created_by"].startswith("user_")

    viewer_feedback = first_viewer.post(
        f"/api/client/portal/proposals/{proposals[0]['proposal_id']}/feedback",
        headers=HEADERS,
        json={"target_type": "proposal", "comment": "只读账号不应该能评论。"},
    )
    assert viewer_feedback.status_code == 403, viewer_feedback.text

    public_share = TestClient(app).get(f"/api/client/share/{proposals[0]['share_token']}", headers=HEADERS)
    assert public_share.status_code == 200, public_share.text

    print(
        "OK multi_account_client_flow "
        f"tenant={TENANT} internal=4 client_companies=3 client_users=9 proposals=3 access=9 "
        f"recommendations={len(recommendation['recommendations'])}"
    )


if __name__ == "__main__":
    main()
