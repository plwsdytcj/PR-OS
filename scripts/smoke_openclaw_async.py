from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.openclaw.adapter import OpenClawAdapter
from src.openclaw.schemas import OpenClawConfig
from src.openclaw.storage import load_binding, save_config


TENANT = f"openclaw-async-{uuid4().hex[:8]}"
DB_PATH = ROOT / "data" / "processed" / "tenants" / TENANT / "app.sqlite3"


class FakeGatewayOpenClawAdapter(OpenClawAdapter):
    def _send_message(self, config: OpenClawConfig, run, message: str) -> dict:
        return {
            "session_id": "smoke_session_001",
            "response": (
                "推荐以下2个KOL：\n\n"
                "1. 贵州数码王，平台：抖音，理由：新能源 SUV 和数码汽车内容匹配，适合做预热种草。\n"
                "2. 西南数码王，平台：小红书，理由：科技生活方式标签强，适合解释智能化卖点。\n\n"
                "主要风险：需要控制报价、履约和内容夸大风险。"
            ),
        }


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_config(
        DB_PATH,
        OpenClawConfig(
            enabled=True,
            gateway_url="http://openclaw-smoke.local",
            default_agent_id="kolness_default",
        ),
    )

    adapter = FakeGatewayOpenClawAdapter()
    created = adapter.start_chat_async(
        DB_PATH,
        user_id="smoke@kolness.local",
        message="预算50万，新能源SUV上市预热，需要推荐KOL并说明风险。",
        campaign_id="campaign_smoke",
    )
    assert created["run"]["status"] == "running", created
    assert [event["event_type"] for event in created["events"]] == ["message.created"], created["events"]

    completed = adapter.complete_chat(DB_PATH, created["run"]["run_id"])
    event_types = [event["event_type"] for event in completed["events"]]
    expected = [
        "message.created",
        "gateway.started",
        "gateway.completed",
        "kolness.match.completed",
        "artifact.preview.created",
        "message.completed",
        "run.completed",
    ]
    assert completed["run"]["status"] == "completed", completed
    assert event_types == expected, event_types

    match_event = next(event for event in completed["events"] if event["event_type"] == "kolness.match.completed")
    kols = match_event["payload"]["recommended_kols"]
    assert kols == ["贵州数码王", "西南数码王"], kols

    binding = load_binding(DB_PATH, "smoke@kolness.local")
    assert binding is not None
    assert binding.openclaw_session_id == "smoke_session_001", binding

    print(f"OK openclaw_async events={len(event_types)} kols={','.join(kols)}")


if __name__ == "__main__":
    main()
