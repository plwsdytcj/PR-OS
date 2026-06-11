from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = f"homepage-core-flow-smoke-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    client = TestClient(app)

    intake = client.post(
        "/api/kol-intake",
        headers=HEADERS,
        data={
            "input_type": "text",
            "text": "\n".join(
                [
                    "达人：小红书家居灵感 KOL",
                    "平台：小红书",
                    "粉丝：9.6万",
                    "报价：16000",
                    "内容：家居改造、生活方式种草、真实体验",
                    "适合：新品预热、种草、信任背书",
                    "风险：硬广比例需要控制",
                ]
            ),
        },
    )
    assert intake.status_code == 200, intake.text
    intake_body = intake.json()
    assert intake_body["imported"] == 1
    assert intake_body["tag_summary"][0]["tag_count"] >= 5

    brief = "家居品牌做新品上市预热，目标年轻租房人群，强调真实改造、收纳和生活方式种草，平台优先小红书。"
    conversation = client.post(
        "/api/kol-intelligence/conversation/run",
        headers=HEADERS,
        json={
            "client_name": "家居品牌客户",
            "project_name": "收纳新品预热",
            "message": brief,
            "top_n": 5,
        },
    )
    assert conversation.status_code == 200, conversation.text
    conversation_body = conversation.json()
    assert len(conversation_body["graph_frames"]) >= 5
    assert conversation_body["recommendations"]
    assert conversation_body["summary"]

    proposal = client.post(
        "/api/collaboration/proposals",
        headers=HEADERS,
        json={
            "client_name": conversation_body["client_name"],
            "project_name": conversation_body["project_name"],
            "brief": conversation_body["brief"],
            "top_n": len(conversation_body["recommendations"]),
            "created_by": "homepage_core_flow_smoke",
        },
    )
    assert proposal.status_code == 200, proposal.text
    proposal_body = proposal.json()
    share_token = proposal_body["proposal"]["share_token"]
    assert proposal_body["proposal"]["share_url"].endswith(share_token)
    assert proposal_body["version"]["candidates"]
    assert proposal_body["markdown"]

    anonymous = TestClient(app)
    public_share = anonymous.get(f"/api/client/share/{share_token}", headers=HEADERS)
    assert public_share.status_code == 200, public_share.text
    share_body = public_share.json()
    assert share_body["proposal"]["proposal_id"] == proposal_body["proposal"]["proposal_id"]
    assert share_body["candidates"]

    feedback = anonymous.post(
        f"/api/client/share/{share_token}/feedback",
        headers=HEADERS,
        json={
            "target_type": "proposal",
            "decision": "maybe",
            "comment": "首页核心链路 smoke 反馈。",
        },
    )
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["feedback"]["decision"] == "maybe"

    print(
        "OK homepage_core_flow "
        f"tags={intake_body['tag_summary'][0]['tag_count']} "
        f"recommendations={len(conversation_body['recommendations'])} "
        f"candidates={len(share_body['candidates'])}"
    )


if __name__ == "__main__":
    main()
