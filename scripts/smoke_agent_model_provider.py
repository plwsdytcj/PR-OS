from __future__ import annotations

from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent.model_provider import AgentModelProvider
from src.agent.schemas import AgentTask


def main() -> None:
    old_key = os.environ.get("GLM_API_KEY")
    old_agent_key = os.environ.get("AGENT_API_KEY")
    os.environ["GLM_API_KEY"] = ""
    os.environ["AGENT_API_KEY"] = ""
    try:
        provider = AgentModelProvider(provider="glm")
        result = provider.final_answer(
            AgentTask(task_id="agent_task_test", title="测试", client_name="测试客户", project_name="测试项目", brief="测试 brief"),
            knowledge={"count": 0},
            project_summary={"matches": 3, "narratives": 2},
            proposal_summary={"proposal_id": "proposal_test"},
        )
        assert result["model_status"] in {"glm_not_configured", "fallback"}
        assert "answer" in result
        assert result["next_actions"]
    finally:
        if old_key is None:
            os.environ.pop("GLM_API_KEY", None)
        else:
            os.environ["GLM_API_KEY"] = old_key
        if old_agent_key is None:
            os.environ.pop("AGENT_API_KEY", None)
        else:
            os.environ["AGENT_API_KEY"] = old_agent_key
    print("OK agent_model_provider fallback")


if __name__ == "__main__":
    main()
