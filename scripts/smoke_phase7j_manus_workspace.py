from __future__ import annotations

import os
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import sdk_runtime
from src.agent.tools import search_knowledge_tool
from web.server import app


TENANT = f"phase7j-manus-workspace-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    old_env = {key: os.environ.get(key) for key in ["AGENT_RUNTIME", "AGENT_SDK_API_KEY", "AGENT_SDK_MODEL", "AGENT_PROVIDER"]}
    old_runner = sdk_runtime._run_sdk_agent
    old_project_tool = sdk_runtime.run_project_tool
    old_proposal_tool = sdk_runtime.create_proposal_tool
    try:
        os.environ["AGENT_RUNTIME"] = "openai_agents"
        os.environ["AGENT_SDK_API_KEY"] = "test-sdk-key"
        os.environ["AGENT_SDK_MODEL"] = "test-sdk-model"
        os.environ["AGENT_PROVIDER"] = "fallback"

        client = TestClient(app)
        bootstrap = client.post(
            "/api/auth/bootstrap-admin",
            headers=HEADERS,
            json={"email": "phase7j-admin@test.local", "name": "Phase7J Admin", "password": "phase7j-pass-123"},
        )
        assert bootstrap.status_code == 200, bootstrap.text
        sample = client.post("/api/import/sample", headers=HEADERS)
        assert sample.status_code == 200, sample.text

        def fake_project(db_path: Path, client_name: str, project_name: str, brief: str, top_n: int = 8) -> dict:
            matches = [
                {
                    "creator_id": "kol_neo_001",
                    "creator_name": "Neo 香氛实验室",
                    "platform": "小红书",
                    "match_score": 92,
                    "symbolic_score": 88,
                    "matched_brand_tags": ["年轻审美", "生活方式", "情绪价值"],
                    "risk_points": ["香味主观性强，需要控制承诺表达"],
                    "match_reason": "内容风格适合把香氛包装成可分享的年轻人身份符号。",
                },
                {
                    "creator_id": "kol_pop_002",
                    "creator_name": "Pop Vibe",
                    "platform": "抖音",
                    "match_score": 86,
                    "symbolic_score": 84,
                    "matched_brand_tags": ["潮流", "短视频", "预热"],
                    "risk_points": ["转化预期需要和内容种草分开评估"],
                    "match_reason": "适合用轻剧情和场景化内容做新品预热。",
                },
            ][:top_n]
            return {
                "run": {"matches": matches, "simulation_report": {"risk_points": ["避免夸大香氛功效"]}, "steps": [{"id": "match"}, {"id": "risk"}]},
                "summary": {"steps": 2, "matches": len(matches), "narratives": 2, "graph_nodes": 8, "campaign_id": "campaign_phase7j"},
            }

        def fake_proposal(db_path: Path, client_name: str, project_name: str, brief: str, top_n: int = 8, created_by: str = "agent") -> dict:
            return {
                "proposal": {"proposal_id": "proposal_phase7j", "share_url": "/client/share/mock-phase7j"},
                "version": {"version_id": "version_phase7j", "candidates": []},
                "markdown": "# Phase 7J Proposal",
                "summary": {"proposal_id": "proposal_phase7j", "share_token": "mock-phase7j", "candidate_count": min(top_n, 2), "budget_total": 500000},
            }

        sdk_runtime.run_project_tool = fake_project
        sdk_runtime.create_proposal_tool = fake_proposal

        def fake_sdk_agent(db_path: Path, message: str, client_name: str, project_name: str, brief: str, top_n: int) -> sdk_runtime.SdkExecutionResult:
            knowledge = search_knowledge_tool(db_path, query=brief, top_k=4)
            project = fake_project(db_path, client_name=client_name, project_name=project_name, brief=brief, top_n=top_n)
            return sdk_runtime.SdkExecutionResult(
                final_output="Manus-like workspace smoke completed.",
                model="test-sdk-model",
                provider="mock_openai_agents",
                tool_traces=[
                    sdk_runtime._trace_item("sdk_parse_brief", "parse brief", "brief ready", {"status": "ready"}),
                    sdk_runtime._trace_item("search_knowledge", "search memory", f"找到 {knowledge['count']} 条可参考记录。", {"count": knowledge["count"]}),
                    sdk_runtime._trace_item("run_project", "match KOL", f"推荐 {project['summary']['matches']} 位 KOL。", project["summary"]),
                ],
                knowledge=knowledge,
                project=project,
            )

        sdk_runtime._run_sdk_agent = fake_sdk_agent
        chat = client.post(
            "/api/agent/chat",
            headers=HEADERS,
            json={
                "client_name": "Phase7J 年轻品牌",
                "project_name": "Manus Workspace",
                "message": "产品是潮流香氛，预算50万，目标人群18-25岁，平台小红书和抖音，需要推荐好玩的KOL并说明风险。",
                "top_n": 3,
            },
        )
        assert chat.status_code == 200, chat.text
        body = chat.json()
        run_id = body["run"]["run_id"]
        assert body["run"]["status"] == "waiting_approval"
        artifact_types = {item["artifact_type"] for item in body["artifacts"]}
        assert {"sdk_run", "agent_handoffs", "memory_recall", "tool_trace", "reasoning_graph", "proposal"}.issubset(artifact_types), artifact_types
        event_types = {item["event_type"] for item in body["events"]}
        assert {"agent_handoff", "memory_recall", "sdk_runtime"}.issubset(event_types), event_types
        steps = body.get("steps") or []
        assert len(steps) >= 5, steps
        roles = {item["agent_role"] for item in steps}
        assert {"Planner Agent", "KOL Strategist Agent", "Memory Agent", "Proposal Agent"}.issubset(roles), roles

        assert any(route.path == "/api/agent/runs/{run_id}/stream" for route in app.routes)
        snapshot = client.get(f"/api/agent/runs/{run_id}", headers=HEADERS)
        assert snapshot.status_code == 200, snapshot.text
        assert snapshot.json().get("steps")

        target_step = next(item for item in steps if item["tool_name"] == "search_knowledge")
        edit = client.post(
            f"/api/agent/steps/{target_step['step_id']}/edit",
            headers=HEADERS,
            json={"input_summary": "edited smoke input"},
        )
        assert edit.status_code == 200, edit.text
        assert any(item["event_type"] == "step_control" for item in edit.json()["events"])
        retry = client.post(f"/api/agent/steps/{target_step['step_id']}/retry", headers=HEADERS, json={"top_k": 2})
        assert retry.status_code == 200, retry.text
        assert any(item["step_id"] == target_step["step_id"] and item["status"] == "completed" for item in retry.json()["steps"])
        skip_target = next(item for item in steps if item["tool_name"] == "suggest_memory")
        skip = client.post(f"/api/agent/steps/{skip_target['step_id']}/skip", headers=HEADERS, json={})
        assert skip.status_code == 200, skip.text
        assert any(item["step_id"] == skip_target["step_id"] and item["status"] == "skipped" for item in skip.json()["steps"])

        print(f"OK phase7j_manus_workspace run={run_id} steps={len(steps)} artifacts={len(artifact_types)}")
    finally:
        sdk_runtime._run_sdk_agent = old_runner
        sdk_runtime.run_project_tool = old_project_tool
        sdk_runtime.create_proposal_tool = old_proposal_tool
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    main()
