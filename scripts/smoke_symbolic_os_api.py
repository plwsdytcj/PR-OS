from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = "symbolic-os-api-smoke"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    snapshot = client.get("/api/symbolic-os", headers=HEADERS)
    assert snapshot.status_code == 200
    assert snapshot.json()["metrics"]["signifier_tags"] >= 5

    report = client.post(
        "/api/symbolic-os/social-reports",
        headers=HEADERS,
        json={
            "period": "API Smoke",
            "raw_input": "AI工具、消费降级、新能源车城市通勤和价格争议同时出现。",
        },
    )
    assert report.status_code == 200
    body = report.json()
    assert body["report"]["issues"]
    assert body["snapshot"]["metrics"]["social_reports"] >= 1

    tag = client.post(
        "/api/symbolic-os/signifier-tags",
        headers=HEADERS,
        json={
            "name": "API测试标签",
            "tag_type": "测试标签",
            "related_tags": "真实感,专业可信",
            "opposite_tags": "硬广不信任",
            "risk_notes": "只用于 smoke。",
        },
    )
    assert tag.status_code == 200
    assert tag.json()["tag"]["related_tags"] == ["真实感", "专业可信"]
    tags = client.get("/api/symbolic-os/signifier-tags", headers=HEADERS)
    assert any(item["name"] == "API测试标签" for item in tags.json()["items"])
    print(f"OK symbolic_os_api tenant={TENANT} reports={body['snapshot']['metrics']['social_reports']}")


if __name__ == "__main__":
    main()
