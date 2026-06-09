from __future__ import annotations

import os
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import sdk_runtime
from src.agent.runtime_adapter import OPENAI_AGENTS_RUNTIME, get_runtime_adapter, runtime_status
from src.agent.tools import run_project_tool, search_knowledge_tool
from web.server import app


TENANT = f"phase7i-b-agent-sdk-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    old_env = {key: os.environ.get(key) for key in ["AGENT_RUNTIME", "AGENT_RUNTIME_ADAPTER", "AGENT_SDK_API_KEY", "AGENT_SDK_MODEL", "AGENT_PROVIDER"]}
    old_runner = sdk_runtime._run_sdk_agent
    try:
        os.environ["AGENT_RUNTIME"] = "openai_agents"
        os.environ.pop("AGENT_RUNTIME_ADAPTER", None)
        os.environ["AGENT_SDK_API_KEY"] = "test-sdk-key"
        os.environ["AGENT_SDK_MODEL"] = "test-sdk-model"
        os.environ["AGENT_PROVIDER"] = "fallback"

        adapter = get_runtime_adapter()
        assert adapter.name == OPENAI_AGENTS_RUNTIME
        status = runtime_status()
        assert status["active_runtime"] == OPENAI_AGENTS_RUNTIME
        assert status["active"]["mode"] == "sdk_ready", status

        client = TestClient(app)
        bootstrap = client.post(
            "/api/auth/bootstrap-admin",
            headers=HEADERS,
            json={"email": "phase7ib-admin@test.local", "name": "Phase7IB Admin", "password": "phase7ib-pass-123"},
        )
        assert bootstrap.status_code == 200, bootstrap.text
        sample = client.post("/api/import/sample", headers=HEADERS)
        assert sample.status_code == 200, sample.text

        def fake_sdk_agent(db_path: Path, message: str, client_name: str, project_name: str, brief: str, top_n: int) -> sdk_runtime.SdkExecutionResult:
            knowledge = search_knowledge_tool(db_path, query=brief, top_k=3)
            project = run_project_tool(db_path, client_name=client_name, project_name=project_name, brief=brief, top_n=top_n)
            return sdk_runtime.SdkExecutionResult(
                final_output="SDK POC 已完成：已调用 PR OS 工具并生成候选 KOL。",
                model="test-sdk-model",
                provider="mock_openai_agents",
                tool_traces=[
                    sdk_runtime._trace_item("sdk_parse_brief", "mock brief", "mock parsed", {"status": "ready"}),
                    sdk_runtime._trace_item("search_knowledge", "mock query", f"找到 {knowledge['count']} 条可参考记录。", {"count": knowledge["count"]}),
                    sdk_runtime._trace_item("run_project", "mock project", f"推荐 {project['summary']['matches']} 位 KOL。", project["summary"]),
                ],
                knowledge=knowledge,
                project=project,
            )

        sdk_runtime._run_sdk_agent = fake_sdk_agent
        chat = client.post(
            "/api/agent/chat",
            headers=HEADERS,
            json={
                "client_name": "Phase7IB SDK 品牌",
                "project_name": "Agent SDK POC",
                "message": "产品是气泡饮料，预算40万，目标人群18-28岁，平台优先小红书和抖音，需要推荐年轻化KOL并说明风险。",
                "top_n": 3,
            },
        )
        assert chat.status_code == 200, chat.text
        body = chat.json()
        assert body["run"]["status"] == "waiting_approval"
        artifact_types = {item["artifact_type"] for item in body["artifacts"]}
        assert {"sdk_run", "knowledge", "project_run", "proposal", "tool_trace", "reasoning_graph"}.issubset(artifact_types), artifact_types
        sdk_artifact = next(item for item in body["artifacts"] if item["artifact_type"] == "sdk_run")
        assert sdk_artifact["payload"]["runtime"] == "openai_agents"
        trace = next(item for item in body["artifacts"] if item["artifact_type"] == "tool_trace")
        trace_tools = {item["tool_name"] for item in trace["payload"]["items"]}
        assert {"sdk_parse_brief", "search_knowledge", "run_project", "create_proposal", "suggest_memory"}.issubset(trace_tools)

        def failing_sdk_agent(*args, **kwargs) -> sdk_runtime.SdkExecutionResult:
            raise RuntimeError("mock sdk failure")

        sdk_runtime._run_sdk_agent = failing_sdk_agent
        fallback_chat = client.post(
            "/api/agent/chat",
            headers=HEADERS,
            json={
                "client_name": "Phase7IB SDK 回退品牌",
                "project_name": "Agent SDK Fallback",
                "message": "产品是AI耳机，预算30万，目标人群20-35岁，平台优先小红书，需要推荐KOL。",
                "top_n": 2,
            },
        )
        assert fallback_chat.status_code == 200, fallback_chat.text
        fallback_body = fallback_chat.json()
        assert fallback_body["run"]["status"] == "waiting_approval"
        assert {"knowledge", "project_run", "proposal", "tool_trace"}.issubset({item["artifact_type"] for item in fallback_body["artifacts"]})
        assert any(event["event_type"] == "sdk_runtime" and event["status"] == "failed" for event in fallback_body["events"])

        print(
            "OK phase7i_b_agent_sdk "
            f"runtime={status['active_runtime']} mode={status['active']['mode']} "
            f"sdk_run={body['run']['run_id']} fallback_run={fallback_body['run']['run_id']}"
        )
    finally:
        sdk_runtime._run_sdk_agent = old_runner
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    main()
