from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = "symbolic-calibration-smoke"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)
    report = client.post(
        "/api/symbolic-os/social-reports",
        headers=HEADERS,
        json={
            "period": "Calibration Smoke",
            "raw_input": "新能源车用户关注城市通勤、家庭安全、智驾体验和价格争议。消费降级讨论持续升温。",
        },
    )
    assert report.status_code == 200
    report_id = report.json()["report"]["report_id"]

    brand = client.post(
        "/api/symbolic/brand-profile",
        headers=HEADERS,
        json={
            "brand_name": "校准测试汽车品牌",
            "industry": "汽车",
            "product": "新能源 SUV",
            "brief": "新品上市预热，强调城市自由和家庭安全。",
        },
    )
    assert brand.status_code == 200
    brand_id = brand.json()["profile"]["brand_id"]
    original_targets = set(brand.json()["profile"]["target_tags"])

    calibrated = client.post(
        f"/api/symbolic/brand-profile/{brand_id}/calibrate",
        headers=HEADERS,
        json={"report_id": report_id},
    )
    assert calibrated.status_code == 200
    body = calibrated.json()
    assert body["calibration"]["applied"] is True
    assert set(body["profile"]["target_tags"]) >= original_targets
    assert body["calibration"]["relevant_issues"]
    assert body["profile"]["suitable_social_issues"]
    assert body["profile"]["unsafe_social_issues"]

    graph = client.post(
        "/api/symbolic/graph",
        headers=HEADERS,
        json={"brand": body["profile"], "matches": [], "narratives": [], "social_context": report.json()["report"]},
    )
    assert graph.status_code == 200
    node_types = {node["type"] for node in graph.json()["nodes"]}
    assert "social_context" in node_types
    assert "social_issue" in node_types
    print(
        "OK symbolic_calibration "
        f"brand={brand_id} added_targets={len(body['calibration']['added_target_tags'])} "
        f"graph_nodes={len(graph.json()['nodes'])}"
    )


if __name__ == "__main__":
    main()
