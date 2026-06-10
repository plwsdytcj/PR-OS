from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from src.agent.memory import build_memory_suggestions, commit_memory_suggestion
from src.agent.model_provider import AgentModelProvider
from src.agent.planner import build_agent_plan, clarification_payload
from src.agent.reasoning_graph import build_reasoning_graph
from src.agent.schemas import (
    AgentArtifact,
    AgentEvent,
    AgentMessage,
    AgentRun,
    AgentStep,
    AgentTask,
    AgentThread,
    assistant_message_id_for,
    artifact_id_for,
    event_id_for,
    message_id_for,
    now_iso,
    run_id_for,
    task_id_for,
    thread_id_for,
)
from src.agent.storage import (
    load_all_threads,
    load_all_tasks,
    load_artifact,
    load_artifacts_for_task,
    load_events_for_run,
    load_messages_for_thread,
    load_run,
    load_runs_for_task,
    load_step,
    load_steps_for_run,
    load_task,
    load_thread,
    load_thread_by_task_id,
    upsert_artifact,
    upsert_event,
    upsert_message,
    upsert_run,
    upsert_step,
    upsert_task,
    upsert_thread,
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
        "steps": [step.to_dict() for step in load_steps_for_run(db_path, run_id)],
        "artifacts": [artifact.to_dict() for artifact in load_artifacts_for_task(db_path, run.task_id)],
    }


def create_agent_thread(
    db_path: Path,
    message: str,
    client_name: str = "",
    project_name: str = "",
    created_by: str = "",
) -> dict[str, Any]:
    task = create_agent_task(db_path, message=message, client_name=client_name, project_name=project_name, created_by=created_by)
    thread = AgentThread(
        thread_id=thread_id_for(task.client_name, task.project_name, message or task.title),
        task_id=task.task_id,
        title=task.title,
        client_name=task.client_name,
        project_name=task.project_name,
        summary=_thread_summary(message),
        created_by=created_by,
        metadata={"source": "agent_thread_chat"},
    )
    upsert_thread(db_path, thread)
    if message.strip():
        upsert_message(
            db_path,
            AgentMessage(
                message_id=message_id_for(thread.thread_id, "user", message),
                thread_id=thread.thread_id,
                role="user",
                content=message.strip(),
                created_by=created_by,
            ),
        )
    return get_agent_thread(db_path, thread.thread_id) or {"thread": thread.to_dict(), "messages": [], "task": task.to_dict(), "runs": [], "artifacts": []}


def list_agent_threads(db_path: Path) -> list[dict[str, Any]]:
    threads = load_all_threads(db_path)
    if threads:
        return [_thread_payload(db_path, thread) for thread in threads]
    # Backfill older task-only runs into read-only thread-shaped payloads for UI continuity.
    return [_legacy_thread_payload(db_path, task) for task in load_all_tasks(db_path)]


def get_agent_thread(db_path: Path, thread_id: str) -> dict[str, Any] | None:
    thread = load_thread(db_path, thread_id)
    if thread is None:
        task = load_task(db_path, thread_id)
        return _legacy_thread_payload(db_path, task) if task else None
    return _thread_payload(db_path, thread)


def start_agent_thread_message(
    db_path: Path,
    thread_id: str,
    message: str,
    top_n: int = 8,
    created_by: str = "",
    require_plan_approval: bool = False,
) -> dict[str, Any]:
    thread = load_thread(db_path, thread_id)
    if thread is None:
        raise ValueError("agent thread not found")
    message = message.strip()
    if not message:
        raise ValueError("message is required")
    upsert_message(
        db_path,
        AgentMessage(
            message_id=message_id_for(thread.thread_id, "user", message),
            thread_id=thread.thread_id,
            role="user",
            content=message,
            created_by=created_by,
        ),
    )
    composed = _compose_thread_prompt(db_path, thread, message)
    started = start_agent_chat(
        db_path,
        message=composed,
        task_id=thread.task_id,
        client_name=thread.client_name,
        project_name=thread.project_name,
        top_n=top_n,
        created_by=created_by,
        require_plan_approval=require_plan_approval,
    )
    run_id = started["run"]["run_id"]
    thread.current_run_id = run_id
    thread.status = started["run"].get("status") or "running"
    thread.summary = _thread_summary(composed)
    thread.updated_at = now_iso()
    upsert_thread(db_path, thread)
    messages = load_messages_for_thread(db_path, thread.thread_id)
    if messages:
        latest = messages[-1]
        latest.run_id = run_id
        latest.status = "running"
        upsert_message(db_path, latest)
    return get_agent_thread(db_path, thread.thread_id) | {"run": started["run"], "top_n": top_n, "require_plan_approval": require_plan_approval}


def run_agent_chat(
    db_path: Path,
    message: str,
    task_id: str = "",
    client_name: str = "",
    project_name: str = "",
    top_n: int = 8,
    created_by: str = "",
    require_plan_approval: bool = False,
) -> dict[str, Any]:
    task, run = prepare_agent_run(db_path, message, task_id=task_id, client_name=client_name, project_name=project_name, created_by=created_by)
    execute_agent_run(db_path, run.run_id, top_n=top_n, require_plan_approval=require_plan_approval)
    return get_agent_run(db_path, run.run_id) or {"run": run.to_dict(), "task": task.to_dict(), "events": [], "artifacts": []}


def start_agent_chat(
    db_path: Path,
    message: str,
    task_id: str = "",
    client_name: str = "",
    project_name: str = "",
    top_n: int = 8,
    created_by: str = "",
    require_plan_approval: bool = False,
) -> dict[str, Any]:
    task, run = prepare_agent_run(db_path, message, task_id=task_id, client_name=client_name, project_name=project_name, created_by=created_by)
    return {"task": task.to_dict(), "run": run.to_dict(), "top_n": top_n, "require_plan_approval": require_plan_approval}


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


def execute_agent_run(db_path: Path, run_id: str, top_n: int = 8, require_plan_approval: bool = False) -> None:
    run = load_run(db_path, run_id)
    if run is None:
        raise ValueError("run not found")
    task = load_task(db_path, run.task_id)
    if task is None:
        raise ValueError("agent task not found")
    message = run.user_message or task.brief
    original_status = run.status
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

        if original_status == "waiting_plan_approval":
            plan = _latest_plan_payload(db_path, task.task_id)
            event("planner", "completed", "计划已确认", "内部用户已确认计划，继续执行工具链。", tool_name="planner")
        else:
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
                _sync_thread_after_run(db_path, task, run)
                return

            if require_plan_approval:
                event(
                    "planner",
                    "waiting",
                    "等待计划确认",
                    "已生成执行计划，等待内部用户确认后再调用工具。",
                    tool_name="planner",
                    artifact_id=plan_artifact.artifact_id,
                )
                run.status = "waiting_plan_approval"
                run.final_answer = "执行计划已生成，请确认后继续运行。"
                run.updated_at = now_iso()
                task.status = "waiting_plan_approval"
                task.current_run_id = run.run_id
                task.updated_at = now_iso()
                upsert_run(db_path, run)
                upsert_task(db_path, task)
                _sync_thread_after_run(db_path, task, run)
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

        reasoning_graph = build_reasoning_graph(task, plan, knowledge, project, proposal, tool_traces, memory)
        graph_artifact = artifact(
            "reasoning_graph",
            "Agent 推理图谱",
            f"生成 {reasoning_graph['summary']['node_count']} 个节点和 {reasoning_graph['summary']['edge_count']} 条关系。",
            reasoning_graph,
        )
        event(
            "reasoning_graph",
            "completed",
            "生成 Agent 推理图谱",
            graph_artifact.summary,
            tool_name="build_reasoning_graph",
            payload=reasoning_graph["summary"],
            artifact_id=graph_artifact.artifact_id,
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
        _sync_thread_after_run(db_path, task, run, model_result=model_result)
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
        _sync_thread_after_run(db_path, task, run)
        raise


def commit_agent_memory_suggestion(db_path: Path, artifact_id: str, suggestion_index: int = 0, created_by: str = "", override: dict[str, Any] | None = None) -> dict[str, Any]:
    result = commit_memory_suggestion(db_path, artifact_id, suggestion_index=suggestion_index, created_by=created_by, override=override)
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


def approve_agent_plan(db_path: Path, run_id: str, top_n: int = 8) -> dict[str, Any]:
    run = load_run(db_path, run_id)
    if run is None:
        raise ValueError("run not found")
    if run.status != "waiting_plan_approval":
        raise ValueError("run is not waiting for plan approval")
    execute_agent_run(db_path, run_id, top_n=top_n, require_plan_approval=False)
    return get_agent_run(db_path, run_id) or {"run": run.to_dict()}


def cancel_agent_run(db_path: Path, run_id: str) -> dict[str, Any]:
    run = load_run(db_path, run_id)
    if run is None:
        raise ValueError("run not found")
    task = load_task(db_path, run.task_id)
    if run.status in {"approved", "cancelled"}:
        return get_agent_run(db_path, run_id) or {"run": run.to_dict()}
    run.status = "cancelled"
    run.final_answer = "本次 Agent run 已取消。"
    run.updated_at = now_iso()
    upsert_run(db_path, run)
    if task:
        task.status = "cancelled"
        task.updated_at = now_iso()
        upsert_task(db_path, task)
    next_sequence = len(load_events_for_run(db_path, run_id)) + 1
    upsert_event(
        db_path,
        AgentEvent(
            event_id=event_id_for(run_id, next_sequence, "Run 已取消"),
            run_id=run_id,
            task_id=run.task_id,
            sequence=next_sequence,
            event_type="control",
            status="cancelled",
            title="Run 已取消",
            summary="内部用户取消了本次 Agent 执行。",
        ),
    )
    return get_agent_run(db_path, run_id) or {"run": run.to_dict()}


def update_agent_step_control(
    db_path: Path,
    step_id: str,
    action: str,
    input_payload: dict[str, Any] | None = None,
    created_by: str = "",
) -> dict[str, Any]:
    step = load_step(db_path, step_id)
    if step is None:
        raise ValueError("step not found")
    run = load_run(db_path, step.run_id)
    if run is None:
        raise ValueError("run not found")
    task = load_task(db_path, run.task_id)
    if task is None:
        raise ValueError("agent task not found")
    action = action.strip().lower()
    payload = input_payload or {}
    if action == "skip":
        step.status = "skipped"
        step.output_summary = "人工跳过该步骤。"
        step.updated_at = now_iso()
        upsert_step(db_path, step)
        _step_control_event(db_path, run, step, "跳过 Step", "内部用户跳过了该工具步骤。", created_by)
        return get_agent_run(db_path, run.run_id) or {"run": run.to_dict()}
    if action == "edit":
        step.input_payload = payload or step.input_payload
        step.input_summary = str(payload.get("input_summary") or step.input_summary)
        step.status = "edited"
        step.updated_at = now_iso()
        upsert_step(db_path, step)
        _step_control_event(db_path, run, step, "编辑 Step 输入", "内部用户编辑了该工具步骤输入。", created_by)
        return get_agent_run(db_path, run.run_id) or {"run": run.to_dict()}
    if action != "retry":
        raise ValueError("unsupported step action")

    step.status = "running"
    step.error = ""
    step.updated_at = now_iso()
    upsert_step(db_path, step)
    _step_control_event(db_path, run, step, "重试 Step", "内部用户触发该工具步骤重试。", created_by)
    try:
        if step.tool_name in {"search_knowledge", "sdk_search_knowledge"}:
            result = search_knowledge_tool(db_path, query=str(payload.get("query") or task.brief), top_k=int(payload.get("top_k") or 6))
            step.output_payload = {"count": result["count"], "items": result.get("items", [])[:5]}
            step.output_summary = f"重试完成，找到 {result['count']} 条可参考记录。"
        elif step.tool_name in {"run_project", "sdk_match_kol_and_build_project"}:
            result = run_project_tool(db_path, client_name=task.client_name, project_name=task.project_name, brief=str(payload.get("brief") or task.brief), top_n=int(payload.get("top_n") or 8))
            step.output_payload = result.get("summary") or {}
            step.output_summary = f"重试完成，推荐 {result['summary']['matches']} 位候选 KOL。"
        elif step.tool_name == "create_proposal":
            result = create_proposal_tool(db_path, client_name=task.client_name, project_name=task.project_name, brief=str(payload.get("brief") or task.brief), top_n=int(payload.get("top_n") or 8), created_by=created_by or run.created_by or "agent")
            step.output_payload = result.get("summary") or {}
            step.output_summary = f"重试完成，生成方案 {result['summary']['proposal_id']}。"
        else:
            step.output_summary = "该步骤已标记重试，但没有专用重试执行器。"
            step.output_payload = {"manual_retry": True}
        step.status = "completed"
    except Exception as exc:
        step.status = "failed"
        step.error = str(exc)
        step.output_summary = f"重试失败：{type(exc).__name__}"
    step.updated_at = now_iso()
    upsert_step(db_path, step)
    _step_control_event(db_path, run, step, "Step 重试完成", step.output_summary, created_by)
    return get_agent_run(db_path, run.run_id) or {"run": run.to_dict()}


def _step_control_event(db_path: Path, run: AgentRun, step: AgentStep, title: str, summary: str, created_by: str = "") -> None:
    next_sequence = len(load_events_for_run(db_path, run.run_id)) + 1
    upsert_event(
        db_path,
        AgentEvent(
            event_id=event_id_for(run.run_id, next_sequence, title),
            run_id=run.run_id,
            task_id=run.task_id,
            sequence=next_sequence,
            event_type="step_control",
            status=step.status,
            title=title,
            summary=summary,
            tool_name=step.tool_name,
            payload={"step_id": step.step_id, "created_by": created_by},
        ),
    )


def resume_agent_clarification(db_path: Path, run_id: str, supplement: str, top_n: int = 8, created_by: str = "") -> dict[str, Any]:
    run = load_run(db_path, run_id)
    if run is None:
        raise ValueError("run not found")
    if run.status != "waiting_clarification":
        raise ValueError("run is not waiting for clarification")
    task = load_task(db_path, run.task_id)
    if task is None:
        raise ValueError("agent task not found")
    supplement = supplement.strip()
    if not supplement:
        raise ValueError("supplement is required")
    message = f"{task.brief}\n补充信息：{supplement}"
    task.brief = message
    task.updated_at = now_iso()
    upsert_task(db_path, task)
    next_sequence = len(load_events_for_run(db_path, run_id)) + 1
    upsert_event(
        db_path,
        AgentEvent(
            event_id=event_id_for(run_id, next_sequence, "已补充信息"),
            run_id=run_id,
            task_id=task.task_id,
            sequence=next_sequence,
            event_type="clarification",
            status="completed",
            title="已补充信息",
            summary=supplement,
        ),
    )
    return run_agent_chat(db_path, message=message, task_id=task.task_id, client_name=task.client_name, project_name=task.project_name, top_n=top_n, created_by=created_by)


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


def _thread_payload(db_path: Path, thread: AgentThread) -> dict[str, Any]:
    task = load_task(db_path, thread.task_id)
    runs = load_runs_for_task(db_path, thread.task_id)
    artifacts = load_artifacts_for_task(db_path, thread.task_id)
    messages = load_messages_for_thread(db_path, thread.thread_id)
    return {
        "thread": thread.to_dict(),
        "task": task.to_dict() if task else None,
        "messages": [message.to_dict() for message in messages],
        "runs": [run.to_dict() for run in runs],
        "artifacts": [artifact.to_dict() for artifact in artifacts],
    }


def _legacy_thread_payload(db_path: Path, task: AgentTask) -> dict[str, Any]:
    payload = _task_payload(db_path, task)
    payload["thread"] = {
        "thread_id": task.task_id,
        "task_id": task.task_id,
        "title": task.title,
        "status": task.status,
        "client_name": task.client_name,
        "project_name": task.project_name,
        "summary": _thread_summary(task.brief),
        "created_by": task.created_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "current_run_id": task.current_run_id,
        "metadata": {"legacy_task": True},
    }
    payload["messages"] = [
        {
            "message_id": f"{task.task_id}:brief",
            "thread_id": task.task_id,
            "role": "user",
            "content": task.brief,
            "run_id": task.current_run_id,
            "status": task.status,
            "created_by": task.created_by,
            "created_at": task.created_at,
            "metadata": {"legacy_task": True},
        }
    ] if task.brief else []
    return payload


def _sync_thread_after_run(db_path: Path, task: AgentTask, run: AgentRun, model_result: dict[str, Any] | None = None) -> None:
    thread = load_thread_by_task_id(db_path, task.task_id)
    if thread is None:
        return
    thread.status = run.status
    thread.current_run_id = run.run_id
    thread.summary = _thread_summary(task.brief)
    thread.updated_at = now_iso()
    upsert_thread(db_path, thread)
    content = run.final_answer or "Agent run 已更新。"
    if model_result and model_result.get("next_actions"):
        content += "\n\n下一步：" + "；".join(str(item) for item in model_result.get("next_actions") or [])
    upsert_message(
        db_path,
        AgentMessage(
            message_id=assistant_message_id_for(thread.thread_id, run.run_id),
            thread_id=thread.thread_id,
            role="assistant",
            content=content,
            run_id=run.run_id,
            status=run.status,
            created_by=run.created_by,
            metadata={"model_status": (model_result or {}).get("model_status", "")},
        ),
    )


def _compose_thread_prompt(db_path: Path, thread: AgentThread, latest_message: str) -> str:
    messages = load_messages_for_thread(db_path, thread.thread_id)[-8:]
    history = "\n".join(f"{item.role}: {item.content}" for item in messages if item.content)
    if not history:
        return latest_message
    return (
        f"这是同一个 PR Agent Thread 的多轮上下文。客户：{thread.client_name}。项目：{thread.project_name}。\n"
        f"历史消息：\n{history}\n\n"
        f"请基于上述上下文处理最新需求：{latest_message}"
    )


def _thread_summary(text: str, limit: int = 96) -> str:
    text = " ".join((text or "").split())
    return text[:limit] + ("..." if len(text) > limit else "")


def _latest_plan_payload(db_path: Path, task_id: str) -> dict[str, Any]:
    for artifact in load_artifacts_for_task(db_path, task_id):
        if artifact.artifact_type == "plan":
            return artifact.payload
    task = load_task(db_path, task_id)
    if task:
        return build_agent_plan(task.brief, client_name=task.client_name, project_name=task.project_name)
    return {"status": "ready", "steps": []}


def _final_answer(task: AgentTask, project_summary: dict[str, Any], proposal_summary: dict[str, Any]) -> str:
    return (
        f"已为「{task.project_name}」完成第一版 PR Agent 执行："
        f"推荐 {project_summary.get('matches', 0)} 位候选 KOL，"
        f"生成 {project_summary.get('narratives', 0)} 条叙事资产，"
        f"并创建甲方协作方案 {proposal_summary.get('proposal_id', '')}。"
        "下一步建议：内部先检查候选名单和风险点，再在组织管理中授权给对应甲方账号。"
    )
