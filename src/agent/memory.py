from __future__ import annotations

from pathlib import Path
from typing import Any

from src.agent.storage import load_artifact, upsert_artifact
from src.knowledge.service import create_knowledge_document


def build_memory_suggestions(
    task: Any,
    knowledge: dict[str, Any],
    project: dict[str, Any],
    proposal: dict[str, Any],
) -> dict[str, Any]:
    project_summary = project.get("summary") or {}
    proposal_summary = proposal.get("summary") or {}
    run = project.get("run") or {}
    matches = (run.get("matches") or [])[:5]
    risks = _collect_risks(matches, run.get("simulation_report") or {})
    top_creators = [item.get("creator_name") for item in matches if item.get("creator_name")]
    suggestions = [
        {
            "source_type": "case",
            "title": f"{task.project_name} 项目案例",
            "industry": (run.get("brief") or {}).get("industry", ""),
            "tags": ["项目案例", "Agent产物", "KOL推荐"],
            "content": (
                f"客户：{task.client_name}\n"
                f"项目：{task.project_name}\n"
                f"Brief：{task.brief}\n"
                f"推荐 KOL 数：{project_summary.get('matches', 0)}\n"
                f"叙事资产数：{project_summary.get('narratives', 0)}\n"
                f"甲方方案：{proposal_summary.get('proposal_id', '')}\n"
                f"首选达人：{'、'.join(top_creators) or '暂无'}"
            ),
        },
        {
            "source_type": "client_preference",
            "title": f"{task.client_name} 偏好线索",
            "industry": (run.get("brief") or {}).get("industry", ""),
            "tags": ["客户偏好", "Agent产物"],
            "content": (
                f"{task.client_name} 在「{task.project_name}」中表达的需求：{task.brief}\n"
                f"系统检索到 {knowledge.get('count', 0)} 条组织记忆作为参考。\n"
                "后续可结合甲方反馈继续修正平台偏好、预算敏感点和达人类型偏好。"
            ),
        },
        {
            "source_type": "risk_policy",
            "title": f"{task.project_name} 风险规则沉淀",
            "industry": (run.get("brief") or {}).get("industry", ""),
            "tags": ["风险规则", "Agent产物"],
            "content": (
                f"项目：{task.project_name}\n"
                f"主要风险：{'；'.join(risks) or '暂无显著风险'}\n"
                "后续同类项目应在 KOL 选择和内容 brief 中提前规避这些风险点。"
            ),
        },
    ]
    return {
        "status": "pending_review",
        "suggestions": suggestions,
        "source_artifacts": {
            "knowledge_count": knowledge.get("count", 0),
            "proposal_id": proposal_summary.get("proposal_id", ""),
            "campaign_id": project_summary.get("campaign_id", ""),
        },
    }


def commit_memory_suggestion(
    db_path: Path,
    artifact_id: str,
    suggestion_index: int = 0,
    created_by: str = "",
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact = load_artifact(db_path, artifact_id)
    if artifact is None:
        raise ValueError("artifact not found")
    if artifact.artifact_type != "memory_suggestions":
        raise ValueError("artifact is not a memory suggestion")
    suggestions = artifact.payload.get("suggestions") or []
    if suggestion_index < 0 or suggestion_index >= len(suggestions):
        raise ValueError("memory suggestion not found")
    suggestion = {**suggestions[suggestion_index], **(override or {})}
    committed = artifact.payload.get("committed") or {}
    key = str(suggestion_index)
    if committed.get(key):
        return {"document": committed[key], "artifact": artifact.to_dict(), "already_committed": True}

    result = create_knowledge_document(
        db_path,
        title=str(suggestion.get("title") or "Agent 记忆回流"),
        content=str(suggestion.get("content") or ""),
        source_type=str(suggestion.get("source_type") or "case"),
        industry=str(suggestion.get("industry") or ""),
        tags=suggestion.get("tags") or [],
        metadata={"created_by": created_by, "source_artifact_id": artifact_id, "suggestion_index": suggestion_index},
    )
    committed[key] = result["document"]
    artifact.payload["committed"] = committed
    artifact.payload["status"] = "partially_committed" if len(committed) < len(suggestions) else "committed"
    upsert_artifact(db_path, artifact)
    return {"document": result["document"], "chunks": result["chunks"], "artifact": artifact.to_dict(), "already_committed": False}


def _collect_risks(matches: list[dict[str, Any]], simulation: dict[str, Any]) -> list[str]:
    risks: list[str] = []
    for item in matches:
        risks.extend(str(risk) for risk in item.get("risk_points") or [] if str(risk).strip())
    risks.extend(str(risk) for risk in simulation.get("risk_points") or [] if str(risk).strip())
    deduped: list[str] = []
    for risk in risks:
        if risk not in deduped:
            deduped.append(risk)
    return deduped[:8]
