from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from src.agent.memory import build_memory_suggestions, commit_memory_suggestion
from src.agent.model_provider import AgentModelProvider
from src.agent.planner import build_agent_plan, clarification_payload
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
    load_artifact,
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
    task, run = prepare_agent_run(db_path, message, task_id=task_id, client_name=client_name, project_name=project_name, created_by=created_by)
    execute_agent_run(db_path, run.run_id, top_n=top_n)
    return get_agent_run(db_path, run.run_id) or {"run": run.to_dict(), "task": task.to_dict(), "events": [], "artifacts": []}


def start_agent_chat(
    db_path: Path,
    message: str,
    task_id: str = "",
    client_name: str = "",
    project_name: str = "",
    top_n: int = 8,
    created_by: str = "",
) -> dict[str, Any]:
    task, run = prepare_agent_run(db_path, message, task_id=task_id, client_name=client_name, project_name=project_name, created_by=created_by)
    return {"task": task.to_dict(), "run": run.to_dict(), "top_n": top_n}


def prepare_agent_run(
    db_path: Path,
    message: str,
    task_id: str = "",
    client_name: str = "",
    project_name: str = "",
    created_by: str = "",
) -> tuple[AgentTask, AgentRun]:
    task = load_task(db_path, task_id) if task_id else None
    if task is None:
        task = create_agent_task(db_path, message=message, client_name=client_name, project_name=project_name, created_by=created_by)
    elif message.strip():
        task.brief = message.strip()
        task.updated_at = now_iso()
        upsert_task(db_path, task)

    run = AgentRun(run_id=run_id_for(task.task_id, message), task_id=task.task_id, user_message=message, created_by=created_by)
    upsert_run(db_path, run)
    task.status = "running"
    task.current_run_id = run.run_id
    task.updated_at = now_iso()
    upsert_task(db_path, task)
    return task, run


def execute_agent_run(db_path: Path, run_id: str, top_n: int = 8) -> None:
    run = load_run(db_path, run_id)
    if run is None:
        raise ValueError("run not found")
    task = load_task(db_path, run.task_id)
    if task is None:
        raise ValueError("agent task not found")
    message = run.user_message or task.brief
    sequence = len(load_events_for_run(db_path, run_id)) + 1

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

    tool_traces: list[dict[str, Any]] = []

    def trace_start(tool_name: str, input_summary: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "tool_name": tool_name,
            "input_summary": input_summary,
            "input_payload": payload or {},
            "status": "running",
            "started_at": now_iso(),
            "_started_perf": perf_counter(),
        }

    def trace_end(trace: dict[str, Any], status: str, output_summary: str, payload: dict[str, Any] | None = None, error: str = "", artifact_id: str = "") -> None:
        elapsed_ms = int((perf_counter() - float(trace.pop("_started_perf", perf_counter()))) * 1000)
        trace.update(
            {
                "status": status,
                "output_summary": output_summary,
                "output_payload": payload or {},
                "error": error,
                "artifact_id": artifact_id,
                "elapsed_ms": elapsed_ms,
                "finished_at": now_iso(),
            }
        )
        tool_traces.append(trace)

    try:
        run.status = "running"
        run.updated_at = now_iso()
        task.status = "running"
        task.updated_at = now_iso()
        upsert_run(db_path, run)
        upsert_task(db_path, task)

        plan = build_agent_plan(message, client_name=task.client_name, project_name=task.project_name, top_n=top_n)
        plan_artifact = artifact(
            "plan",
            "Agent 执行计划",
            "已生成执行计划。" if plan["status"] == "ready" else "已生成执行计划，但需要先补充关键信息。",
            plan,
        )
        event(
            "planner",
            "completed" if plan["status"] == "ready" else "waiting",
            "生成执行计划",
            plan_artifact.summary,
            tool_name="planner",
            payload={"status": plan["status"], "missing_fields": plan.get("missing_fields", [])},
            artifact_id=plan_artifact.artifact_id,
        )

        if plan["status"] == "needs_clarification":
            clarification = clarification_payload(plan)
            clarification_artifact = artifact(
                "clarification",
                "Agent 追问",
                "当前 brief 缺少关键字段，Agent 暂停执行并等待补充。",
                clarification,
            )
            event(
                "clarification",
                "waiting",
                "等待补充信息",
                "请补充预算、平台、产品或目标人群后重新启动 Agent。",
                tool_name="clarification",
                payload=clarification,
                artifact_id=clarification_artifact.artifact_id,
            )
            run.status = "waiting_clarification"
            run.final_answer = "需要补充信息：" + "；".join(clarification.get("questions") or [])
            run.updated_at = now_iso()
            task.status = "waiting_clarification"
            task.current_run_id = run.run_id
            task.updated_at = now_iso()
            upsert_run(db_path, run)
            upsert_task(db_path, task)
            return

        event("message", "completed", "理解项目需求", "已接收需求，准备检索组织记忆并调用 PR OS 工具。", payload={"message": message})

        event("tool_call", "running", "检索组织记忆", "查询历史提案、客户反馈、Campaign Room 和达人画像。", tool_name="search_knowledge")
        knowledge_trace = trace_start("search_knowledge", f"query={task.brief[:120]}", {"top_k": 6})
        knowledge = search_knowledge_tool(db_path, query=task.brief, top_k=6)
        knowledge_artifact = artifact("knowledge", "组织记忆检索", f"找到 {knowledge['count']} 条可参考记录。", knowledge)
        trace_end(knowledge_trace, "completed", knowledge_artifact.summary, {"count": knowledge["count"]}, artifact_id=knowledge_artifact.artifact_id)
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
        project_trace = trace_start("run_project", f"client={task.client_name}; project={task.project_name}; top_n={top_n}", {"top_n": top_n})
        project = run_project_tool(db_path, client_name=task.client_name, project_name=task.project_name, brief=task.brief, top_n=top_n)
        project_summary = project["summary"]
        project_artifact = artifact(
            "project_run",
            "PR 项目运行结果",
            f"推荐 {project_summary['matches']} 位 KOL，生成 {project_summary['narratives']} 条叙事资产。",
            project,
        )
        trace_end(project_trace, "completed", project_artifact.summary, project_summary, artifact_id=project_artifact.artifact_id)
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
        proposal_trace = trace_start("create_proposal", f"client={task.client_name}; project={task.project_name}; top_n={top_n}", {"top_n": top_n})
        proposal = create_proposal_tool(
            db_path,
            client_name=task.client_name,
            project_name=task.project_name,
            brief=task.brief,
            top_n=top_n,
            created_by=run.created_by or "agent",
        )
        proposal_artifact = artifact(
            "proposal",
            "甲方协作方案",
            f"已生成 {proposal['summary']['candidate_count']} 位候选 KOL 的客户方案。",
            proposal,
        )
        trace_end(proposal_trace, "completed", proposal_artifact.summary, proposal["summary"], artifact_id=proposal_artifact.artifact_id)
        event(
            "tool_result",
            "completed",
            "完成甲方方案草稿",
            f"方案 {proposal['summary']['proposal_id']} 已生成，等待人工确认是否授权给甲方。",
            tool_name="create_proposal",
            payload=proposal["summary"],
            artifact_id=proposal_artifact.artifact_id,
        )

        event("tool_call", "running", "生成记忆回流建议", "把本次项目产物整理为可确认入库的知识建议。", tool_name="suggest_memory")
        memory_trace = trace_start("suggest_memory", f"task={task.task_id}", {"artifact_types": ["case", "client_preference", "risk_policy"]})
        memory = build_memory_suggestions(task, knowledge, project, proposal)
        memory_artifact = artifact(
            "memory_suggestions",
            "记忆回流建议",
            f"生成 {len(memory.get('suggestions') or [])} 条可入库知识建议，等待人工确认。",
            memory,
        )
        trace_end(memory_trace, "completed", memory_artifact.summary, {"count": len(memory.get("suggestions") or [])}, artifact_id=memory_artifact.artifact_id)
        event(
            "tool_result",
            "completed",
            "完成记忆回流建议",
            memory_artifact.summary,
            tool_name="suggest_memory",
            payload={"count": len(memory.get("suggestions") or [])},
            artifact_id=memory_artifact.artifact_id,
        )

        trace_artifact = artifact(
            "tool_trace",
            "工具调用 Trace",
            f"记录 {len(tool_traces)} 次工具调用的输入、输出、耗时和状态。",
            {"items": tool_traces, "count": len(tool_traces)},
        )
        event(
            "tool_trace",
            "completed",
            "保存工具调用 Trace",
            trace_artifact.summary,
            tool_name="tool_trace",
            payload={"count": len(tool_traces)},
            artifact_id=trace_artifact.artifact_id,
        )

        model_result = AgentModelProvider().final_answer(task, knowledge, project_summary, proposal["summary"])
        final_answer = str(model_result.get("answer") or _final_answer(task, project_summary, proposal["summary"]))
        event(
            "assistant_message",
            "waiting",
            "等待人工确认",
            "下一步可以在组织管理里把方案授权给甲方客户账号。",
            payload={
                "final_answer": final_answer,
                "next_actions": model_result.get("next_actions") or [],
                "model_status": model_result.get("model_status") or "fallback",
            },
        )
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


def commit_agent_memory_suggestion(db_path: Path, artifact_id: str, suggestion_index: int = 0, created_by: str = "") -> dict[str, Any]:
    result = commit_memory_suggestion(db_path, artifact_id, suggestion_index=suggestion_index, created_by=created_by)
    artifact = load_artifact(db_path, artifact_id)
    if artifact:
        run = load_run(db_path, artifact.run_id)
        next_sequence = len(load_events_for_run(db_path, artifact.run_id)) + 1
        upsert_event(
            db_path,
            AgentEvent(
                event_id=event_id_for(artifact.run_id, next_sequence, "记忆已入库"),
                run_id=artifact.run_id,
                task_id=artifact.task_id,
                sequence=next_sequence,
                event_type="memory",
                status="completed",
                title="记忆已入库",
                summary=f"已将建议 {suggestion_index + 1} 写入知识库：{result['document']['title']}",
                tool_name="commit_memory",
                payload={"document_id": result["document"]["document_id"], "suggestion_index": suggestion_index},
                artifact_id=artifact_id,
            ),
        )
        if run:
            run.updated_at = now_iso()
            upsert_run(db_path, run)
    return result


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
