from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from src.agent.schemas import AgentTask
from src.llm.glm_client import GlmClient


class AgentModelProvider:
    def __init__(self, provider: str | None = None) -> None:
        load_dotenv()
        self.provider = (provider or os.getenv("AGENT_PROVIDER") or "glm").strip().lower()

    @property
    def available(self) -> bool:
        if self.provider == "glm":
            return _agent_glm_client().available
        return False

    def final_answer(
        self,
        task: AgentTask,
        knowledge: dict[str, Any],
        project_summary: dict[str, Any],
        proposal_summary: dict[str, Any],
    ) -> dict[str, Any]:
        if self.provider == "glm":
            try:
                return _glm_final_answer(task, knowledge, project_summary, proposal_summary)
            except Exception as exc:
                fallback = fallback_final_answer(task, project_summary, proposal_summary)
                fallback["model_status"] = f"glm_failed:{type(exc).__name__}"
                return fallback
        fallback = fallback_final_answer(task, project_summary, proposal_summary)
        fallback["model_status"] = "fallback"
        return fallback


def fallback_final_answer(task: AgentTask, project_summary: dict[str, Any], proposal_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "answer": (
            f"已为「{task.project_name}」完成第一版 PR Agent 执行："
            f"推荐 {project_summary.get('matches', 0)} 位候选 KOL，"
            f"生成 {project_summary.get('narratives', 0)} 条叙事资产，"
            f"并创建甲方协作方案 {proposal_summary.get('proposal_id', '')}。"
            "下一步建议：内部先检查候选名单和风险点，再在组织管理中授权给对应甲方账号。"
        ),
        "next_actions": [
            "检查候选 KOL 的报价、履约记录和风险点。",
            "确认客户账号和项目授权范围。",
            "根据甲方反馈生成下一版方案。",
        ],
        "model_status": "fallback",
    }


def _glm_final_answer(
    task: AgentTask,
    knowledge: dict[str, Any],
    project_summary: dict[str, Any],
    proposal_summary: dict[str, Any],
) -> dict[str, Any]:
    client = _agent_glm_client()
    if not client.available:
        fallback = fallback_final_answer(task, project_summary, proposal_summary)
        fallback["model_status"] = "glm_not_configured"
        return fallback
    return client.complete_json(
        system=(
            "你是 AI Native PR 公司的项目经理 Agent。"
            "你需要基于工具结果输出简洁、可执行、面向内部团队的中文总结。"
            "必须返回 JSON，字段为 answer、next_actions、model_status。"
            "next_actions 是 2 到 4 条短句。model_status 固定为 glm。"
        ),
        user=(
            f"客户：{task.client_name}\n"
            f"项目：{task.project_name}\n"
            f"Brief：{task.brief}\n"
            f"组织记忆数量：{knowledge.get('count', 0)}\n"
            f"Project Summary：{project_summary}\n"
            f"Proposal Summary：{proposal_summary}\n"
            "请输出本次 Agent 执行总结和下一步。"
        ),
        timeout=45,
    )


def _agent_glm_client() -> GlmClient:
    load_dotenv()
    return GlmClient(
        api_key=os.getenv("AGENT_API_KEY") or os.getenv("GLM_API_KEY"),
        model=os.getenv("AGENT_MODEL") or os.getenv("GLM_MODEL"),
        base_url=os.getenv("AGENT_BASE_URL") or os.getenv("GLM_BASE_URL"),
    )
