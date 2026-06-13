from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.openclaw.adapter import OpenClawAdapter
from src.openclaw.schemas import OpenClawConfig, OpenClawRun
from src.openclaw.storage import load_binding, load_config, save_config


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
        self.assertEqual(request.kwargs["json"]["model"], "openclaw/kolness_user_1")
        self.assertEqual(request.kwargs["json"]["stream"], False)
        self.assertEqual(request.kwargs["headers"]["x-openclaw-session-key"], "session_1")
        self.assertEqual(request.kwargs["headers"]["x-openclaw-agent-id"], "kolness_user_1")


if __name__ == "__main__":
    unittest.main()
