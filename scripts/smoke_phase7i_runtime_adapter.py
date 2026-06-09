from __future__ import annotations

import os
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent.runtime_adapter import CUSTOM_RUNTIME, OPENAI_AGENTS_RUNTIME, get_runtime_adapter, runtime_status
from web.server import app


TENANT = f"phase7i-runtime-adapter-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    old_runtime = os.environ.get("AGENT_RUNTIME")
    old_adapter = os.environ.get("AGENT_RUNTIME_ADAPTER")
    old_provider = os.environ.get("AGENT_PROVIDER")
    try:
        os.environ["AGENT_PROVIDER"] = "fallback"
        os.environ.pop("AGENT_RUNTIME_ADAPTER", None)
        os.environ["AGENT_RUNTIME"] = CUSTOM_RUNTIME
        assert get_runtime_adapter().name == CUSTOM_RUNTIME
        custom_status = runtime_status()
        assert custom_status["active_runtime"] == CUSTOM_RUNTIME
        assert custom_status["active"]["available"] is True

        os.environ["AGENT_RUNTIME"] = "openai-agents"
        sdk_adapter = get_runtime_adapter()
        assert sdk_adapter.name == OPENAI_AGENTS_RUNTIME
        sdk_status = runtime_status()
        assert sdk_status["active_runtime"] == OPENAI_AGENTS_RUNTIME
        assert sdk_status["active"]["fallback_runtime"] == CUSTOM_RUNTIME

        client = TestClient(app)
        bootstrap = client.post(
            "/api/auth/bootstrap-admin",
            headers=HEADERS,
            json={"email": "phase7i-admin@test.local", "name": "Phase7I Admin", "password": "phase7i-pass-123"},
        )
        assert bootstrap.status_code == 200, bootstrap.text

        runtime_resp = client.get("/api/agent/runtime", headers=HEADERS)
        assert runtime_resp.status_code == 200, runtime_resp.text
        body = runtime_resp.json()
        assert body["active_runtime"] == OPENAI_AGENTS_RUNTIME
        assert any(item["name"] == CUSTOM_RUNTIME for item in body["available_runtimes"])
        assert any(item["name"] == OPENAI_AGENTS_RUNTIME for item in body["available_runtimes"])

        sample = client.post("/api/import/sample", headers=HEADERS)
        assert sample.status_code == 200, sample.text

        chat = client.post(
            "/api/agent/chat",
            headers=HEADERS,
            json={
                "client_name": "Phase7I Runtime 品牌",
                "project_name": "Adapter Smoke",
                "message": "预算35万，新能源SUV上市预热，平台优先小红书，需要推荐KOL并说明风险。",
                "top_n": 3,
            },
        )
        assert chat.status_code == 200, chat.text
        chat_body = chat.json()
        assert chat_body["run"]["status"] == "waiting_approval"
        assert {"knowledge", "project_run", "proposal"}.issubset({item["artifact_type"] for item in chat_body["artifacts"]})

        data_sources = client.get("/api/settings/data-sources", headers=HEADERS)
        assert data_sources.status_code == 200, data_sources.text
        agent_items = [item for item in data_sources.json()["items"] if item["id"] == "agent_runtime"]
        assert agent_items
        assert agent_items[0]["runtimes"]

        print(
            "OK phase7i_runtime_adapter "
            f"runtime={body['active_runtime']} delegated_status={body['active']['mode']} run={chat_body['run']['run_id']}"
        )
    finally:
        if old_runtime is None:
            os.environ.pop("AGENT_RUNTIME", None)
        else:
            os.environ["AGENT_RUNTIME"] = old_runtime
        if old_adapter is None:
            os.environ.pop("AGENT_RUNTIME_ADAPTER", None)
        else:
            os.environ["AGENT_RUNTIME_ADAPTER"] = old_adapter
        if old_provider is None:
            os.environ.pop("AGENT_PROVIDER", None)
        else:
            os.environ["AGENT_PROVIDER"] = old_provider


if __name__ == "__main__":
    main()
