from __future__ import annotations

from pathlib import Path
from typing import Any

from src.agent.schemas import (
    AgentArtifact,
    AgentEvent,
    AgentRun,
    AgentTask,
    artifact_id_for,
    event_id_for,
    now_iso,
    run_id_for,
    task_id_for,
)
from src.agent.storage import (
    load_all_tasks,
    load_artifacts_for_task,
    load_events_for_run,
    load_run,
    load_runs_for_task,
    load_task,
    upsert_artifact,
    upsert_event,
    upsert_run,
    upsert_task,
)
from src.agent.tools import create_proposal_tool, run_project_tool, search_knowledge_tool
from src.intelligence.brief_parser import parse_brief


def create_agent_task(
    db_path: Path,
    message: str,
    client_name: str = "",
    project_name: str = "",
    created_by: str = "",
) -> AgentTask:
    brief = message.strip()
    parsed = parse_brief(brief)
    client = client_name.strip() or "未命名客户"
    project = project_name.strip() or parsed.product or "AI PR 项目"
    title = f"{client} · {project}"
    task = AgentTask(
        task_id=task_id_for(title, brief),
        title=title,
        client_name=client,
        project_name=project,
        brief=brief,
        created_by=created_by,
        metadata={"parsed_brief": parsed.__dict__},
    )
    upsert_task(db_path, task)
    return task


def list_agent_tasks(db_path: Path) -> list[dict[str, Any]]:
    return [_task_payload(db_path, task) for task in load_all_tasks(db_path)]


def get_agent_task(db_path: Path, task_id: str) -> dict[str, Any] | None:
    task = load_task(db_path, task_id)
    return _task_payload(db_path, task) if task else None


def get_agent_run(db_path: Path, run_id: str) -> dict[str, Any] | None:
    run = load_run(db_path, run_id)
    if run is None:
        return None
    task = load_task(db_path, run.task_id)
    return {
        "run": run.to_dict(),
        "task": task.to_dict() if task else None,
        "events": [event.to_dict() for event in load_events_for_run(db_path, run_id)],
        "artifacts": [artifact.to_dict() for artifact in load_artifacts_for_task(db_path, run.task_id)],
    }


def run_agent_chat(
    db_path: Path,
    message: str,
    task_id: str = "",
    client_name: str = "",
    project_name: str = "",
    top_n: int = 8,
    created_by: str = "",
) -> dict[str, Any]:
    task = load_task(db_path, task_id) if task_id else None
    if task is None:
        task = create_agent_task(db_path, message=message, client_name=client_name, project_name=project_name, created_by=created_by)
    elif message.strip():
        task.brief = message.strip()
        task.updated_at = now_iso()
        upsert_task(db_path, task)

    run = AgentRun(run_id=run_id_for(task.task_id, message), task_id=task.task_id, user_message=message, created_by=created_by)
    upsert_run(db_path, run)

    sequence = 1

    def event(event_type: str, status: str, title: str, summary: str = "", tool_name: str = "", payload: dict[str, Any] | None = None, artifact_id: str = "") -> AgentEvent:
        nonlocal sequence
        item = AgentEvent(
            event_id=event_id_for(run.run_id, sequence, title),
            run_id=run.run_id,
            task_id=task.task_id,
            sequence=sequence,
            event_type=event_type,
            status=status,
            title=title,
            summary=summary,
            tool_name=tool_name,
            payload=payload or {},
            artifact_id=artifact_id,
        )
        upsert_event(db_path, item)
        sequence += 1
        return item

    def artifact(artifact_type: str, title: str, summary: str, payload: dict[str, Any]) -> AgentArtifact:
        item = AgentArtifact(
            artifact_id=artifact_id_for(task.task_id, artifact_type, title),
            task_id=task.task_id,
            run_id=run.run_id,
            artifact_type=artifact_type,
            title=title,
            summary=summary,
            payload=payload,
        )
        upsert_artifact(db_path, item)
        return item

    try:
        event("message", "completed", "理解项目需求", "已接收需求，准备检索组织记忆并调用 PR OS 工具。", payload={"message": message})

        event("tool_call", "running", "检索组织记忆", "查询历史提案、客户反馈、Campaign Room 和达人画像。", tool_name="search_knowledge")
        knowledge = search_knowledge_tool(db_path, query=task.brief, top_k=6)
        knowledge_artifact = artifact("knowledge", "组织记忆检索", f"找到 {knowledge['count']} 条可参考记录。", knowledge)
        event(
            "tool_result",
            "completed",
            "完成组织记忆检索",
            knowledge_artifact.summary,
            tool_name="search_knowledge",
            payload={"count": knowledge["count"]},
            artifact_id=knowledge_artifact.artifact_id,
        )

        event("tool_call", "running", "运行 PR 项目链路", "解析 Brief、生成符号图谱、匹配 KOL、跑压力测试并创建 Campaign Room。", tool_name="run_project")
        project = run_project_tool(db_path, client_name=task.client_name, project_name=task.project_name, brief=task.brief, top_n=top_n)
        project_summary = project["summary"]
        project_artifact = artifact(
            "project_run",
            "PR 项目运行结果",
            f"推荐 {project_summary['matches']} 位 KOL，生成 {project_summary['narratives']} 条叙事资产。",
            project,
        )
        event(
            "tool_result",
            "completed",
            "完成 KOL 选择与风险推演",
            f"已完成 {project_summary['steps']} 个步骤，推荐 {project_summary['matches']} 位候选 KOL。",
            tool_name="run_project",
            payload=project_summary,
            artifact_id=project_artifact.artifact_id,
        )

        event("tool_call", "running", "生成甲方协作方案", "把推荐结果转为甲方可查看、可反馈的协作提案。", tool_name="create_proposal")
        proposal = create_proposal_tool(
            db_path,
            client_name=task.client_name,
            project_name=task.project_name,
            brief=task.brief,
            top_n=top_n,
            created_by=created_by or "agent",
        )
        proposal_artifact = artifact(
            "proposal",
            "甲方协作方案",
            f"已生成 {proposal['summary']['candidate_count']} 位候选 KOL 的客户方案。",
            proposal,
        )
        event(
            "tool_result",
            "completed",
            "完成甲方方案草稿",
            f"方案 {proposal['summary']['proposal_id']} 已生成，等待人工确认是否授权给甲方。",
            tool_name="create_proposal",
            payload=proposal["summary"],
            artifact_id=proposal_artifact.artifact_id,
        )

        final_answer = _final_answer(task, project_summary, proposal["summary"])
        event("assistant_message", "waiting", "等待人工确认", "下一步可以在组织管理里把方案授权给甲方客户账号。", payload={"final_answer": final_answer})
        run.status = "waiting_approval"
        run.final_answer = final_answer
        run.updated_at = now_iso()
        task.status = "waiting_approval"
        task.current_run_id = run.run_id
        task.updated_at = now_iso()
        upsert_run(db_path, run)
        upsert_task(db_path, task)
    except Exception as exc:
        event("error", "failed", "Agent 执行失败", str(exc))
        run.status = "failed"
        run.final_answer = str(exc)
        run.updated_at = now_iso()
        task.status = "failed"
        task.current_run_id = run.run_id
        task.updated_at = now_iso()
        upsert_run(db_path, run)
        upsert_task(db_path, task)
        raise

    return get_agent_run(db_path, run.run_id) or {"run": run.to_dict(), "task": task.to_dict(), "events": [], "artifacts": []}


def approve_agent_run(db_path: Path, run_id: str) -> dict[str, Any]:
    run = load_run(db_path, run_id)
    if run is None:
        raise ValueError("run not found")
    task = load_task(db_path, run.task_id)
    run.status = "approved"
    run.updated_at = now_iso()
    upsert_run(db_path, run)
    if task:
        task.status = "approved"
        task.updated_at = now_iso()
        upsert_task(db_path, task)
    next_sequence = len(load_events_for_run(db_path, run_id)) + 1
    upsert_event(
        db_path,
        AgentEvent(
            event_id=event_id_for(run_id, next_sequence, "人工确认"),
            run_id=run_id,
            task_id=run.task_id,
            sequence=next_sequence,
            event_type="approval",
            status="completed",
            title="人工确认",
            summary="内部团队已确认本次 Agent 产物，可进入客户授权或方案调整。",
        ),
    )
    return get_agent_run(db_path, run_id) or {"run": run.to_dict()}


def _task_payload(db_path: Path, task: AgentTask) -> dict[str, Any]:
    runs = load_runs_for_task(db_path, task.task_id)
    artifacts = load_artifacts_for_task(db_path, task.task_id)
    return {
        "task": task.to_dict(),
        "runs": [run.to_dict() for run in runs],
        "artifacts": [artifact.to_dict() for artifact in artifacts],
    }


def _final_answer(task: AgentTask, project_summary: dict[str, Any], proposal_summary: dict[str, Any]) -> str:
    return (
        f"已为「{task.project_name}」完成第一版 PR Agent 执行："
        f"推荐 {project_summary.get('matches', 0)} 位候选 KOL，"
        f"生成 {project_summary.get('narratives', 0)} 条叙事资产，"
        f"并创建甲方协作方案 {proposal_summary.get('proposal_id', '')}。"
        "下一步建议：内部先检查候选名单和风险点，再在组织管理中授权给对应甲方账号。"
    )
