from __future__ import annotations

import os
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import sdk_runtime
from src.agent.tools import run_project_tool, search_knowledge_tool
from web.server import app


TENANT = f"phase7i-c-runtime-ab-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    old_env = {key: os.environ.get(key) for key in ["AGENT_RUNTIME", "AGENT_SDK_API_KEY", "AGENT_SDK_MODEL", "AGENT_PROVIDER"]}
    old_runner = sdk_runtime._run_sdk_agent
    try:
        os.environ["AGENT_RUNTIME"] = "custom"
        os.environ["AGENT_SDK_API_KEY"] = "test-sdk-key"
        os.environ["AGENT_SDK_MODEL"] = "test-sdk-model"
        os.environ["AGENT_PROVIDER"] = "fallback"

        client = TestClient(app)
        bootstrap = client.post(
            "/api/auth/bootstrap-admin",
            headers=HEADERS,
            json={"email": "phase7ic-admin@test.local", "name": "Phase7IC Admin", "password": "phase7ic-pass-123"},
        )
        assert bootstrap.status_code == 200, bootstrap.text
        sample = client.post("/api/import/sample", headers=HEADERS)
        assert sample.status_code == 200, sample.text

        def fake_sdk_agent(db_path: Path, message: str, client_name: str, project_name: str, brief: str, top_n: int) -> sdk_runtime.SdkExecutionResult:
            knowledge = search_knowledge_tool(db_path, query=brief, top_k=3)
            project = run_project_tool(db_path, client_name=client_name, project_name=project_name, brief=brief, top_n=top_n)
            return sdk_runtime.SdkExecutionResult(
                final_output="SDK runtime override 已完成。",
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
        payload = {
            "client_name": "Phase7IC 品牌",
            "project_name": "Runtime Override",
            "message": "产品是AI耳机，预算30万，目标人群20-35岁，平台优先小红书，需要推荐KOL并说明风险。",
            "top_n": 2,
        }

        custom = client.post("/api/agent/chat", headers=HEADERS, json=payload | {"runtime": "custom"})
        assert custom.status_code == 200, custom.text
        custom_body = custom.json()
        assert custom_body["run"]["status"] == "waiting_approval"
        assert "sdk_run" not in {item["artifact_type"] for item in custom_body["artifacts"]}

        sdk = client.post("/api/agent/chat", headers=HEADERS, json=payload | {"runtime": "openai_agents"})
        assert sdk.status_code == 200, sdk.text
        sdk_body = sdk.json()
        assert sdk_body["run"]["status"] == "waiting_approval"
        assert "sdk_run" in {item["artifact_type"] for item in sdk_body["artifacts"]}

        compare = client.post("/api/agent/chat/compare-runtimes", headers=HEADERS, json=payload)
        assert compare.status_code == 200, compare.text
        compare_body = compare.json()
        assert compare_body["runtime_a"]["run"]["status"] == "waiting_approval"
        assert compare_body["runtime_b"]["run"]["status"] == "waiting_approval"
        assert compare_body["comparison"]["runtime_a"] == "custom"
        assert compare_body["comparison"]["runtime_b"] == "openai_agents"
        assert compare_body["artifact"]["artifact_type"] == "runtime_comparison"
        assert "sdk_run" in {item["artifact_type"] for item in compare_body["runtime_b"]["artifacts"]}

        print(
            "OK phase7i_c_runtime_ab "
            f"custom={custom_body['run']['run_id']} sdk={sdk_body['run']['run_id']} "
            f"compare={compare_body['artifact']['artifact_id']}"
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
