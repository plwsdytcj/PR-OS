from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.openclaw.adapter import OpenClawAdapter
from src.openclaw.schemas import OpenClawConfig, OpenClawRun
from src.openclaw.storage import load_binding, load_config, load_runs_for_session, load_sessions_for_user, save_config


class OpenClawAdapterTest(unittest.TestCase):
    def test_default_binding_and_unconfigured_chat_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "openclaw.sqlite3"
            save_config(db_path, OpenClawConfig(enabled=False, gateway_url="", default_agent_id="kolness_default"))

            adapter = OpenClawAdapter()
            payload = adapter.start_chat(db_path, user_id="user_1", message="帮我推荐 KOL")

            self.assertEqual(load_config(db_path).default_agent_id, "kolness_default")
            self.assertIsNotNone(load_binding(db_path, "user_1"))
            self.assertEqual(payload["run"]["status"], "failed")
            self.assertIn("OpenClaw 未启用", payload["run"]["error"])
            self.assertGreaterEqual(len(payload["events"]), 2)

    def test_chat_completions_gateway_payload_is_supported(self) -> None:
        run = OpenClawRun(
            run_id="run_1",
            user_id="user_1",
            openclaw_agent_id="kolness_user_1",
            openclaw_session_id="session_1",
            status="running",
            message="brief",
            history=[{"role": "user", "content": "上一轮 brief"}, {"role": "assistant", "content": "上一轮回复"}],
        )
        response = Mock()
        response.status_code = 200
        response.content = b"{}"
        response.headers = {"x-openclaw-session-key": "session_2"}
        response.json.return_value = {"choices": [{"message": {"content": "pong"}}]}

        with patch("src.openclaw.adapter.requests.post", return_value=response) as post:
            payload = OpenClawAdapter()._send_chat_completions(
                "http://openclaw-gateway:18789",
                {"Content-Type": "application/json", "Authorization": "Bearer token"},
                run,
                "Reply with pong",
            )

        self.assertEqual(payload["response"], "pong")
        self.assertEqual(payload["session_id"], "session_2")
        request = post.call_args
        self.assertEqual(request.args[0], "http://openclaw-gateway:18789/v1/chat/completions")
        self.assertEqual(request.kwargs["json"]["model"], "openclaw")
        self.assertEqual(request.kwargs["json"]["messages"][-3]["content"], "上一轮 brief")
        self.assertEqual(request.kwargs["json"]["messages"][-2]["content"], "上一轮回复")
        self.assertEqual(request.kwargs["json"]["messages"][-1]["content"], "Reply with pong")
        self.assertEqual(request.kwargs["json"]["stream"], False)
        self.assertEqual(request.kwargs["headers"]["x-openclaw-session-key"], "session_1")
        self.assertEqual(request.kwargs["headers"]["x-openclaw-agent-id"], "kolness_user_1")

    def test_user_can_have_multiple_backend_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "openclaw.sqlite3"
            save_config(db_path, OpenClawConfig(enabled=False, gateway_url="", default_agent_id="kolness_default"))

            adapter = OpenClawAdapter()
            session_a = adapter.create_session(db_path, user_id="user_1", title="新能源 SUV")
            session_b = adapter.create_session(db_path, user_id="user_1", title="美妆新品")

            run_a = adapter.start_chat(db_path, user_id="user_1", message="推荐汽车 KOL", session_record_id=session_a.session_id)
            run_b = adapter.start_chat(db_path, user_id="user_1", message="推荐美妆 KOL", session_record_id=session_b.session_id)

            sessions = load_sessions_for_user(db_path, "user_1")
            self.assertEqual({item.session_id for item in sessions}, {session_a.session_id, session_b.session_id})
            self.assertEqual(run_a["run"]["session_id"], session_a.session_id)
            self.assertEqual(run_b["run"]["session_id"], session_b.session_id)
            self.assertEqual([run.message for run in load_runs_for_session(db_path, session_a.session_id)], ["推荐汽车 KOL"])
            self.assertEqual([run.message for run in load_runs_for_session(db_path, session_b.session_id)], ["推荐美妆 KOL"])


if __name__ == "__main__":
    unittest.main()
