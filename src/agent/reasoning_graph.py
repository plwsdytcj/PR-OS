from __future__ import annotations

from typing import Any


def build_reasoning_graph(
    task: Any,
    plan: dict[str, Any],
    knowledge: dict[str, Any],
    project: dict[str, Any],
    proposal: dict[str, Any],
    tool_traces: list[dict[str, Any]],
    memory: dict[str, Any],
) -> dict[str, Any]:
    """Build a visual reasoning graph for the Agent run.

    The graph is intentionally explanatory rather than a hidden chain-of-thought:
    it links user brief, parsed intent, knowledge evidence, tool calls, KOL picks,
    risk signals, proposal, and memory writeback candidates.
    """
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    def add_node(node_id: str, label: str, node_type: str, stage: str, detail: str = "", payload: dict[str, Any] | None = None, score: int = 0) -> None:
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "type": node_type,
                "stage": stage,
                "detail": detail,
                "payload": payload or {},
                "score": score,
            }
        )

    def add_edge(source: str, target: str, label: str, edge_type: str = "reasoning") -> None:
        edges.append({"source": source, "target": target, "label": label, "type": edge_type})

    parsed = plan.get("parsed_brief") or {}
    add_node("brief", "甲方 Brief", "brief", "input", task.brief[:180], {"client_name": task.client_name, "project_name": task.project_name, "brief": task.brief})
    add_node("intent", "解析目标", "intent", "analysis", plan.get("goal", ""), parsed)
    add_edge("brief", "intent", "解析")

    for step in (plan.get("steps") or [])[:8]:
        node_id = f"plan_{step.get('id')}"
        add_node(node_id, step.get("label") or step.get("id") or "计划步骤", "plan_step", "plan", step.get("reason", ""), step)
        add_edge("intent", node_id, "计划")

    knowledge_items = knowledge.get("items") or []
    for index, item in enumerate(knowledge_items[:5], start=1):
        node_id = f"knowledge_{index}"
        add_node(
            node_id,
            item.get("title") or f"知识证据 {index}",
            "knowledge",
            "evidence",
            item.get("content") or item.get("summary") or "",
            item,
            score=int(float(item.get("score") or 0) * 100),
        )
        add_edge("plan_search_knowledge", node_id, "检索证据", "evidence")
        add_edge(node_id, "plan_run_project", "影响匹配", "evidence")

    run = project.get("run") or {}
    matches = run.get("matches") or []
    for index, item in enumerate(matches[:8], start=1):
        node_id = f"kol_{index}"
        score = int(item.get("symbolic_score") or item.get("match_score") or 0)
        add_node(
            node_id,
            item.get("creator_name") or f"KOL {index}",
            "creator",
            "kol_match",
            item.get("match_reason") or item.get("suggested_content_direction") or "",
            item,
            score=score,
        )
        add_edge("plan_run_project", node_id, "推荐候选", "match")
        for tag_index, tag in enumerate((item.get("matched_brand_tags") or [])[:3], start=1):
            tag_id = f"tag_{index}_{tag_index}"
            add_node(tag_id, str(tag), "tag", "ontology", f"影响 {item.get('creator_name') or 'KOL'} 的匹配解释。", {"creator": item.get("creator_name"), "tag": tag})
            add_edge(tag_id, node_id, "标签命中", "ontology")

    risks = _collect_risks(matches, run.get("simulation_report") or {})
    for index, risk in enumerate(risks[:8], start=1):
        node_id = f"risk_{index}"
        add_node(node_id, risk, "risk", "risk", "匹配或推演中出现的风险信号。", {"risk": risk})
        add_edge("plan_run_project", node_id, "风险识别", "risk")

    proposal_summary = proposal.get("summary") or {}
    add_node("proposal", "甲方方案", "proposal", "proposal", f"候选 {proposal_summary.get('candidate_count', 0)} 位，预算 {proposal_summary.get('budget_total', 0)}。", proposal_summary)
    add_edge("plan_create_proposal", "proposal", "生成方案", "proposal")
    for index, item in enumerate(matches[:5], start=1):
        add_edge(f"kol_{index}", "proposal", "进入方案", "proposal")

    for index, trace in enumerate(tool_traces[:8], start=1):
        node_id = f"trace_{index}"
        add_node(node_id, trace.get("tool_name") or f"工具 {index}", "tool_trace", "trace", trace.get("output_summary") or trace.get("error") or "", trace)
        source = f"plan_{_plan_id_for_tool(trace.get('tool_name', ''))}"
        if any(node["id"] == source for node in nodes):
            add_edge(source, node_id, "调用记录", "trace")

    for index, item in enumerate((memory.get("suggestions") or [])[:5], start=1):
        node_id = f"memory_{index}"
        add_node(node_id, item.get("title") or f"记忆建议 {index}", "memory", "memory", item.get("content", "")[:180], item)
        add_edge("proposal", node_id, "沉淀经验", "memory")
        for risk_index in range(1, min(len(risks), 3) + 1):
            add_edge(f"risk_{risk_index}", node_id, "风险入库", "memory")

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "knowledge_count": len(knowledge_items),
            "kol_count": len(matches),
            "risk_count": len(risks),
            "memory_count": len(memory.get("suggestions") or []),
        },
        "ontology": {
            "brief": "甲方输入的原始需求",
            "intent": "系统解析出的传播目标和约束",
            "knowledge": "公司知识库和历史项目证据",
            "creator": "候选 KOL",
            "tag": "影响匹配的标签和符号",
            "risk": "风险信号",
            "proposal": "甲方可读方案",
            "memory": "回流知识库的经验",
            "tool_trace": "工具调用证据",
        },
    }


def _collect_risks(matches: list[dict[str, Any]], simulation: dict[str, Any]) -> list[str]:
    risks: list[str] = []
    for item in matches:
        risks.extend(str(risk) for risk in item.get("risk_points") or [] if str(risk).strip())
    risks.extend(str(risk) for risk in simulation.get("risk_points") or [] if str(risk).strip())
    deduped: list[str] = []
    for risk in risks:
        if risk not in deduped:
            deduped.append(risk)
    return deduped


def _plan_id_for_tool(tool_name: str) -> str:
    mapping = {
        "search_knowledge": "search_knowledge",
        "run_project": "run_project",
        "create_proposal": "create_proposal",
        "suggest_memory": "memory_suggestions",
    }
    return mapping.get(tool_name, tool_name)
