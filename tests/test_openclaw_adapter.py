from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.openclaw.adapter import OpenClawAdapter
from src.openclaw.schemas import OpenClawConfig
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


if __name__ == "__main__":
    unittest.main()

