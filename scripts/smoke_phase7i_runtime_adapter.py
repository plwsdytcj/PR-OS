from __future__ import annotations

import os
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import sdk_runtime
from src.agent.runtime_adapter import CUSTOM_RUNTIME, OPENAI_AGENTS_RUNTIME, get_runtime_adapter, requested_runtime_name, runtime_status
from src.agent.tools import run_project_tool, search_knowledge_tool
from web.server import app


TENANT = f"phase7i-runtime-adapter-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    old_runtime = os.environ.get("AGENT_RUNTIME")
    old_adapter = os.environ.get("AGENT_RUNTIME_ADAPTER")
    old_provider = os.environ.get("AGENT_PROVIDER")
    old_sdk_key = os.environ.get("AGENT_SDK_API_KEY")
    old_runner = sdk_runtime._run_sdk_agent
    try:
        os.environ["AGENT_PROVIDER"] = "fallback"
        os.environ["AGENT_SDK_API_KEY"] = "test-sdk-key"
        os.environ.pop("AGENT_RUNTIME_ADAPTER", None)
        os.environ.pop("AGENT_RUNTIME", None)
        assert requested_runtime_name() == OPENAI_AGENTS_RUNTIME
        default_status = runtime_status()
        assert default_status["active_runtime"] == OPENAI_AGENTS_RUNTIME

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

        def fake_sdk_agent(db_path: Path, message: str, client_name: str, project_name: str, brief: str, top_n: int) -> sdk_runtime.SdkExecutionResult:
            knowledge = search_knowledge_tool(db_path, query=brief, top_k=3)
            project = run_project_tool(db_path, client_name=client_name, project_name=project_name, brief=brief, top_n=top_n)
            return sdk_runtime.SdkExecutionResult(
                final_output="SDK adapter smoke completed.",
                model="test-sdk-model",
                provider="mock_openai_agents",
                tool_traces=[
                    sdk_runtime._trace_item("sdk_parse_brief", "mock", "ready", {"status": "ready"}),
                    sdk_runtime._trace_item("search_knowledge", "mock", f"找到 {knowledge['count']} 条可参考记录。", {"count": knowledge["count"]}),
                    sdk_runtime._trace_item("run_project", "mock", f"推荐 {project['summary']['matches']} 位 KOL。", project["summary"]),
                ],
                knowledge=knowledge,
                project=project,
            )

        sdk_runtime._run_sdk_agent = fake_sdk_agent

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
        if old_sdk_key is None:
            os.environ.pop("AGENT_SDK_API_KEY", None)
        else:
            os.environ["AGENT_SDK_API_KEY"] = old_sdk_key
        sdk_runtime._run_sdk_agent = old_runner


if __name__ == "__main__":
    main()
