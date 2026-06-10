from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from dotenv import load_dotenv

from src.agent.memory import build_memory_suggestions
from src.agent.model_provider import fallback_final_answer
from src.agent.planner import build_agent_plan, clarification_payload
from src.agent.reasoning_graph import build_reasoning_graph
from src.agent.schemas import AgentArtifact, AgentEvent, AgentStep, now_iso, artifact_id_for, event_id_for, step_id_for
from src.agent.storage import load_events_for_run, load_run, load_steps_for_run, load_task, upsert_artifact, upsert_event, upsert_run, upsert_step, upsert_task
from src.agent.tools import create_proposal_tool, run_project_tool, search_knowledge_tool
from src.agent import runtime as custom_runtime


@dataclass
class SdkExecutionResult:
    final_output: str
    model: str
    provider: str
    tool_traces: list[dict[str, Any]]
    knowledge: dict[str, Any]
    project: dict[str, Any]


def execute_agent_run_with_sdk(db_path: Path, run_id: str, top_n: int = 8, require_plan_approval: bool = False) -> None:
    """Run the PR OS agent through OpenAI Agents SDK for the orchestration step.

    The SDK path is intentionally scoped: the SDK decides and calls PR OS tools,
    while PR OS still owns persistence, proposal generation, memory writeback,
    and the explainable reasoning graph.
    """

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

    def step(tool_name: str, title: str, status: str, agent_role: str, input_summary: str = "", output_summary: str = "", input_payload: dict[str, Any] | None = None, output_payload: dict[str, Any] | None = None, artifact_id: str = "", error: str = "") -> AgentStep:
        index = len(load_steps_for_run(db_path, run.run_id)) + 1
        item = AgentStep(
            step_id=step_id_for(run.run_id, index, tool_name),
            run_id=run.run_id,
            task_id=task.task_id,
            sequence=index,
            tool_name=tool_name,
            title=title,
            status=status,
            agent_role=agent_role,
            input_summary=input_summary,
            output_summary=output_summary,
            input_payload=input_payload or {},
            output_payload=output_payload or {},
            artifact_id=artifact_id,
            error=error,
        )
        upsert_step(db_path, item)
        return item

    try:
        run.status = "running"
        run.updated_at = now_iso()
        task.status = "running"
        task.updated_at = now_iso()
        upsert_run(db_path, run)
        upsert_task(db_path, task)

        if original_status == "waiting_plan_approval":
            plan = _latest_plan_payload(db_path, task.task_id)
            event("planner", "completed", "计划已确认", "内部用户已确认计划，继续执行 SDK 工具链。", tool_name="planner")
        else:
            plan = build_agent_plan(message, client_name=task.client_name, project_name=task.project_name, top_n=top_n)
            plan_artifact = artifact(
                "plan",
                "Agent SDK 执行计划",
                "已生成 SDK 执行计划。" if plan["status"] == "ready" else "已生成执行计划，但需要先补充关键信息。",
                plan | {"runtime": "openai_agents"},
            )
            event(
                "planner",
                "completed" if plan["status"] == "ready" else "waiting",
                "生成 SDK 执行计划",
                plan_artifact.summary,
                tool_name="planner",
                payload={"status": plan["status"], "missing_fields": plan.get("missing_fields", []), "runtime": "openai_agents"},
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
                custom_runtime._sync_thread_after_run(db_path, task, run)
                return
            if require_plan_approval:
                event(
                    "planner",
                    "waiting",
                    "等待计划确认",
                    "已生成 SDK 执行计划，等待内部用户确认后再调用工具。",
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
                custom_runtime._sync_thread_after_run(db_path, task, run)
                return

        event("message", "completed", "进入 Agents SDK", "已接收需求，准备由 OpenAI Agents SDK 编排 PR OS 工具。", payload={"message": message})
        handoff_payload = _handoff_payload()
        handoff_artifact = artifact("agent_handoffs", "多 Agent 协作路径", "Planner、KOL、Risk、Proposal、Memory 角色已进入协作队列。", handoff_payload)
        for item in handoff_payload["agents"]:
            event("agent_handoff", "completed", f"{item['name']} 接手", item["responsibility"], tool_name="handoff", payload=item, artifact_id=handoff_artifact.artifact_id)
        event("sdk_runtime", "running", "启动 OpenAI Agents SDK", "SDK 将调用 brief 解析、组织记忆检索和 KOL 项目匹配工具。", tool_name="openai_agents")
        step("openai_agents", "启动 OpenAI Agents SDK", "running", "Planner Agent", input_summary=message[:160], input_payload={"runtime": "openai_agents", "top_n": top_n})

        sdk_result = _run_sdk_agent(db_path, message, task.client_name, task.project_name, task.brief, top_n)
        for trace in sdk_result.tool_traces:
            step(
                str(trace.get("tool_name") or "sdk_tool"),
                _step_title_for_tool(str(trace.get("tool_name") or "sdk_tool")),
                str(trace.get("status") or "completed"),
                _agent_role_for_tool(str(trace.get("tool_name") or "")),
                input_summary=str(trace.get("input_summary") or ""),
                output_summary=str(trace.get("output_summary") or ""),
                input_payload=trace.get("input_payload") or {},
                output_payload=trace.get("output_payload") or {},
                artifact_id=str(trace.get("artifact_id") or ""),
                error=str(trace.get("error") or ""),
            )
        sdk_artifact = artifact(
            "sdk_run",
            "OpenAI Agents SDK Run",
            f"SDK 编排完成，记录 {len(sdk_result.tool_traces)} 次工具调用。",
            {
                "runtime": "openai_agents",
                "model": sdk_result.model,
                "provider": sdk_result.provider,
                "final_output": sdk_result.final_output,
                "tool_count": len(sdk_result.tool_traces),
            },
        )
        event(
            "sdk_runtime",
            "completed",
            "完成 OpenAI Agents SDK 编排",
            sdk_artifact.summary,
            tool_name="openai_agents",
            payload={"model": sdk_result.model, "provider": sdk_result.provider, "tool_count": len(sdk_result.tool_traces)},
            artifact_id=sdk_artifact.artifact_id,
        )
        step("openai_agents", "完成 OpenAI Agents SDK 编排", "completed", "Planner Agent", output_summary=sdk_artifact.summary, output_payload={"model": sdk_result.model, "provider": sdk_result.provider, "tool_count": len(sdk_result.tool_traces)}, artifact_id=sdk_artifact.artifact_id)

        knowledge = sdk_result.knowledge or search_knowledge_tool(db_path, query=task.brief, top_k=6)
        knowledge_artifact = artifact("knowledge", "组织记忆检索", f"找到 {knowledge['count']} 条可参考记录。", knowledge)
        memory_recall = _memory_recall_payload(knowledge)
        memory_recall_artifact = artifact("memory_recall", "长程记忆召回", f"召回 {knowledge['count']} 条记忆，覆盖 {len(memory_recall['source_counts'])} 类来源。", memory_recall)
        event("tool_result", "completed", "完成组织记忆检索", knowledge_artifact.summary, tool_name="search_knowledge", payload={"count": knowledge["count"]}, artifact_id=knowledge_artifact.artifact_id)
        event("memory_recall", "completed", "完成长程记忆召回", memory_recall_artifact.summary, tool_name="search_knowledge", payload=memory_recall["summary"], artifact_id=memory_recall_artifact.artifact_id)

        project = sdk_result.project or run_project_tool(db_path, client_name=task.client_name, project_name=task.project_name, brief=task.brief, top_n=top_n)
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
        event(
            "tool_result",
            "completed",
            "完成甲方方案草稿",
            f"方案 {proposal['summary']['proposal_id']} 已生成，等待人工确认是否授权给甲方。",
            tool_name="create_proposal",
            payload=proposal["summary"],
            artifact_id=proposal_artifact.artifact_id,
        )
        step("create_proposal", "生成甲方协作方案", "completed", "Proposal Agent", input_summary=f"top_n={top_n}", output_summary=proposal_artifact.summary, output_payload=proposal["summary"], artifact_id=proposal_artifact.artifact_id)

        memory = build_memory_suggestions(task, knowledge, project, proposal)
        memory_artifact = artifact(
            "memory_suggestions",
            "记忆回流建议",
            f"生成 {len(memory.get('suggestions') or [])} 条可入库知识建议，等待人工确认。",
            memory,
        )
        event("tool_result", "completed", "完成记忆回流建议", memory_artifact.summary, tool_name="suggest_memory", payload={"count": len(memory.get("suggestions") or [])}, artifact_id=memory_artifact.artifact_id)
        step("suggest_memory", "生成记忆回流建议", "completed", "Memory Agent", input_summary=f"task={task.task_id}", output_summary=memory_artifact.summary, output_payload={"count": len(memory.get("suggestions") or [])}, artifact_id=memory_artifact.artifact_id)

        tool_traces = sdk_result.tool_traces + [
            _trace_item("create_proposal", "PR OS post-SDK proposal generation", proposal_artifact.summary, {"candidate_count": proposal["summary"]["candidate_count"]}, proposal_artifact.artifact_id),
            _trace_item("suggest_memory", "PR OS post-SDK memory suggestions", memory_artifact.summary, {"count": len(memory.get("suggestions") or [])}, memory_artifact.artifact_id),
        ]
        trace_artifact = artifact("tool_trace", "工具调用 Trace", f"记录 {len(tool_traces)} 次工具调用的输入、输出、耗时和状态。", {"items": tool_traces, "count": len(tool_traces), "runtime": "openai_agents"})
        event("tool_trace", "completed", "保存 SDK 工具调用 Trace", trace_artifact.summary, tool_name="tool_trace", payload={"count": len(tool_traces), "runtime": "openai_agents"}, artifact_id=trace_artifact.artifact_id)

        reasoning_graph = build_reasoning_graph(task, plan, knowledge, project, proposal, tool_traces, memory)
        graph_artifact = artifact(
            "reasoning_graph",
            "Agent 推理图谱",
            f"生成 {reasoning_graph['summary']['node_count']} 个节点和 {reasoning_graph['summary']['edge_count']} 条关系。",
            reasoning_graph,
        )
        event("reasoning_graph", "completed", "生成 Agent 推理图谱", graph_artifact.summary, tool_name="build_reasoning_graph", payload=reasoning_graph["summary"], artifact_id=graph_artifact.artifact_id)
        step("build_reasoning_graph", "生成 Agent 推理图谱", "completed", "Planner Agent", output_summary=graph_artifact.summary, output_payload=reasoning_graph["summary"], artifact_id=graph_artifact.artifact_id)

        fallback = fallback_final_answer(task, project_summary, proposal["summary"])
        final_answer = sdk_result.final_output.strip() or fallback["answer"]
        model_result = {"answer": final_answer, "next_actions": fallback["next_actions"], "model_status": f"openai_agents:{sdk_result.model}"}
        event("assistant_message", "waiting", "等待人工确认", "下一步可以在组织管理里把方案授权给甲方客户账号。", payload={"final_answer": final_answer, "model_status": model_result["model_status"]})
        run.status = "waiting_approval"
        run.final_answer = final_answer
        run.updated_at = now_iso()
        task.status = "waiting_approval"
        task.current_run_id = run.run_id
        task.updated_at = now_iso()
        upsert_run(db_path, run)
        upsert_task(db_path, task)
        custom_runtime._sync_thread_after_run(db_path, task, run, model_result=model_result)
    except Exception:
        raise


def _run_sdk_agent(db_path: Path, message: str, client_name: str, project_name: str, brief: str, top_n: int) -> SdkExecutionResult:
    from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner, function_tool

    load_dotenv()
    api_key = _sdk_api_key()
    if not api_key:
        raise RuntimeError("AGENT_SDK_API_KEY, OPENAI_API_KEY, AGENT_API_KEY, or GLM_API_KEY is required")
    model_name = _sdk_model_name()
    base_url = _sdk_base_url()
    provider = "openai_compatible" if base_url else "openai"
    model: Any = model_name
    if base_url:
        model = OpenAIChatCompletionsModel(model=model_name, openai_client=AsyncOpenAI(api_key=api_key, base_url=base_url))

    captured: dict[str, Any] = {"knowledge": {}, "project": {}, "tool_traces": []}

    @function_tool
    def sdk_parse_brief(raw_brief: str) -> dict[str, Any]:
        """Parse the PR brief and return extracted product, platform, budget, audience, and goal signals."""
        started = perf_counter()
        plan = build_agent_plan(raw_brief, client_name=client_name, project_name=project_name, top_n=top_n)
        trace = _trace_item("sdk_parse_brief", f"brief={raw_brief[:120]}", f"解析状态：{plan.get('status')}", {"status": plan.get("status"), "missing_fields": plan.get("missing_fields", [])}, elapsed_ms=_elapsed_ms(started))
        captured["tool_traces"].append(trace)
        return {"status": plan.get("status"), "missing_fields": plan.get("missing_fields", []), "steps": plan.get("steps", [])}

    @function_tool
    def sdk_search_knowledge(query: str, top_k: int = 6) -> dict[str, Any]:
        """Search PR OS organization memory and return relevant prior cases, preferences, and campaign records."""
        started = perf_counter()
        result = search_knowledge_tool(db_path, query=query, top_k=top_k)
        captured["knowledge"] = result
        captured["tool_traces"].append(_trace_item("search_knowledge", f"query={query[:120]}", f"找到 {result['count']} 条可参考记录。", {"count": result["count"]}, elapsed_ms=_elapsed_ms(started)))
        return result

    @function_tool
    def sdk_match_kol_and_build_project(brief_text: str) -> dict[str, Any]:
        """Run PR OS KOL matching, symbolic graph generation, risk simulation, and campaign room creation."""
        started = perf_counter()
        result = run_project_tool(db_path, client_name=client_name, project_name=project_name, brief=brief_text, top_n=top_n)
        captured["project"] = result
        summary = result["summary"]
        captured["tool_traces"].append(_trace_item("run_project", f"client={client_name}; project={project_name}; top_n={top_n}", f"推荐 {summary['matches']} 位 KOL，生成 {summary['narratives']} 条叙事资产。", summary, elapsed_ms=_elapsed_ms(started)))
        return summary

    agent = Agent(
        name="PR OS SDK Agent",
        instructions=(
            "你是 AI Native PR 公司的项目经理 Agent。必须按顺序调用工具："
            "1) sdk_parse_brief；2) sdk_search_knowledge；3) sdk_match_kol_and_build_project。"
            "工具完成后，用中文输出面向内部团队的简洁结论，包括推荐数量、风险检查和下一步。"
        ),
        model=model,
        tools=[sdk_parse_brief, sdk_search_knowledge, sdk_match_kol_and_build_project],
    )
    result = _run_agent_sync(Runner, agent, message, int(os.getenv("AGENT_SDK_MAX_TURNS") or "8"))
    if not captured["knowledge"]:
        captured["knowledge"] = search_knowledge_tool(db_path, query=brief, top_k=6)
        captured["tool_traces"].append(_trace_item("search_knowledge", "PR OS fallback after SDK run", f"找到 {captured['knowledge']['count']} 条可参考记录。", {"count": captured["knowledge"]["count"]}))
    if not captured["project"]:
        captured["project"] = run_project_tool(db_path, client_name=client_name, project_name=project_name, brief=brief, top_n=top_n)
        summary = captured["project"]["summary"]
        captured["tool_traces"].append(_trace_item("run_project", "PR OS fallback after SDK run", f"推荐 {summary['matches']} 位 KOL，生成 {summary['narratives']} 条叙事资产。", summary))
    return SdkExecutionResult(
        final_output=str(getattr(result, "final_output", "") or ""),
        model=model_name,
        provider=provider,
        tool_traces=captured["tool_traces"],
        knowledge=captured["knowledge"],
        project=captured["project"],
    )


def _trace_item(tool_name: str, input_summary: str, output_summary: str, payload: dict[str, Any] | None = None, artifact_id: str = "", elapsed_ms: int = 0) -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "input_summary": input_summary,
        "input_payload": {},
        "status": "completed",
        "started_at": now_iso(),
        "output_summary": output_summary,
        "output_payload": payload or {},
        "error": "",
        "artifact_id": artifact_id,
        "elapsed_ms": elapsed_ms,
        "finished_at": now_iso(),
        "runtime": "openai_agents",
    }


def _handoff_payload() -> dict[str, Any]:
    agents = [
        {"name": "Planner Agent", "responsibility": "拆解 brief、确认计划、协调工具顺序。", "stage": "plan"},
        {"name": "KOL Strategist Agent", "responsibility": "召回达人、匹配标签、产出候选名单。", "stage": "kol_match"},
        {"name": "Risk Agent", "responsibility": "识别报价、履约、舆情和内容风险。", "stage": "risk"},
        {"name": "Proposal Agent", "responsibility": "把内部结果转成甲方可读方案。", "stage": "proposal"},
        {"name": "Memory Agent", "responsibility": "沉淀客户偏好、案例和风险规则。", "stage": "memory"},
    ]
    return {"mode": "agents_sdk_handoff_trace", "agents": agents, "count": len(agents)}


def _memory_recall_payload(knowledge: dict[str, Any]) -> dict[str, Any]:
    items = knowledge.get("items") or []
    source_counts: dict[str, int] = {}
    for item in items:
        source = str(item.get("source_type") or item.get("source") or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    return {
        "summary": {"count": knowledge.get("count", len(items)), "source_counts": source_counts},
        "source_counts": source_counts,
        "items": items[:8],
    }


def _agent_role_for_tool(tool_name: str) -> str:
    if "parse" in tool_name:
        return "Planner Agent"
    if "knowledge" in tool_name:
        return "Memory Agent"
    if "project" in tool_name or "kol" in tool_name:
        return "KOL Strategist Agent"
    if "proposal" in tool_name:
        return "Proposal Agent"
    if "risk" in tool_name:
        return "Risk Agent"
    return "PR Manager Agent"


def _step_title_for_tool(tool_name: str) -> str:
    mapping = {
        "sdk_parse_brief": "解析 Brief",
        "search_knowledge": "检索组织记忆",
        "run_project": "匹配 KOL 与项目链路",
        "create_proposal": "生成甲方方案",
        "suggest_memory": "生成记忆建议",
    }
    return mapping.get(tool_name, tool_name.replace("_", " ").title())


def _elapsed_ms(started: float) -> int:
    return int((perf_counter() - started) * 1000)


def _run_agent_sync(runner: Any, agent: Any, message: str, max_turns: int) -> Any:
    from agents import RunConfig

    # Agents SDK run_sync owns an event loop; isolate it from FastAPI/TestClient loops.
    tracing_disabled = (os.getenv("AGENT_SDK_TRACING") or "").strip().lower() not in {"1", "true", "yes"}
    run_config = RunConfig(tracing_disabled=tracing_disabled)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: runner.run_sync(agent, input=message, max_turns=max_turns, run_config=run_config))
        return future.result()


def _sdk_api_key() -> str:
    load_dotenv()
    return (
        os.getenv("AGENT_SDK_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("AGENT_API_KEY")
        or os.getenv("GLM_API_KEY")
        or ""
    )


def _sdk_model_name() -> str:
    load_dotenv()
    return os.getenv("AGENT_SDK_MODEL") or os.getenv("OPENAI_DEFAULT_MODEL") or os.getenv("AGENT_MODEL") or os.getenv("GLM_MODEL") or "gpt-4.1-mini"


def _sdk_base_url() -> str:
    load_dotenv()
    value = os.getenv("AGENT_SDK_BASE_URL") or os.getenv("OPENAI_BASE_URL") or os.getenv("AGENT_BASE_URL") or os.getenv("GLM_BASE_URL") or ""
    value = value.strip().rstrip("/")
    suffix = "/chat/completions"
    if value.endswith(suffix):
        value = value[: -len(suffix)]
    return value


def _latest_plan_payload(db_path: Path, task_id: str) -> dict[str, Any]:
    from src.agent.storage import load_artifacts_for_task

    for item in load_artifacts_for_task(db_path, task_id):
        if item.artifact_type == "plan":
            return item.payload
    task = load_task(db_path, task_id)
    if task:
        return build_agent_plan(task.brief, client_name=task.client_name, project_name=task.project_name)
    return {"status": "ready", "steps": []}
