from __future__ import annotations

from dataclasses import asdict
from typing import Any

from src.intelligence.brief_parser import parse_brief
from src.intelligence.business_type import classify_business_type
from src.intelligence.pr_os_judgment import PR_OS_OUTPUT_CHECKLIST, PR_OS_RED_LINES


CRITICAL_FIELDS = {
    "budget": "预算范围",
    "platform_preference": "优先平台",
    "product": "产品/服务",
}


def build_agent_plan(message: str, client_name: str = "", project_name: str = "", top_n: int = 8) -> dict[str, Any]:
    parsed = parse_brief(message)
    business = classify_business_type(parsed)
    missing = missing_brief_fields(message, parsed)
    status = "needs_clarification" if missing else "ready"
    steps = [
        {
            "id": "parse_brief",
            "label": "解析 brief",
            "tool_name": "parse_brief",
            "status": "completed",
            "reason": "把自然语言需求转成预算、平台、产品、目标人群等结构化字段。",
        },
        {
            "id": "classify_business",
            "label": "判断业务类型与结算目标",
            "tool_name": "classify_business",
            "status": "completed",
            "reason": f"当前判断为「{business['business_type_label']}」，结算看：{business['settlement_target']}。",
        },
        {
            "id": "search_knowledge",
            "label": "检索公司知识库",
            "tool_name": "search_knowledge",
            "status": "pending" if not missing else "blocked",
            "reason": "先查公司案例、客户偏好、风险规则和 OS 判准，避免凭空推荐。",
        },
        {
            "id": "generate_deliverables",
            "label": "生成媒介交付包",
            "tool_name": "generate_deliverables",
            "status": "pending" if not missing else "blocked",
            "reason": "输出客户卡、选题卡、报价骨架，作为内部与客户沟通底稿。",
        },
        {
            "id": "run_project",
            "label": "运行 PR 项目链路",
            "tool_name": "run_project",
            "status": "pending" if not missing else "blocked",
            "reason": "调用已有 PR OS 能力完成 KOL 选择、符号图谱、叙事资产和风险推演。",
        },
        {
            "id": "create_proposal",
            "label": "生成甲方方案",
            "tool_name": "create_proposal",
            "status": "pending" if not missing else "blocked",
            "reason": "把推荐结果转成甲方可查看、可反馈的协作方案。",
        },
        {
            "id": "memory_suggestions",
            "label": "生成记忆回流建议",
            "tool_name": "suggest_memory",
            "status": "pending" if not missing else "blocked",
            "reason": "把本次项目的方案、偏好、风险与案例回写沉淀为可确认入库的知识。",
        },
        {
            "id": "wait_for_approval",
            "label": "等待人工确认",
            "tool_name": "",
            "status": "pending" if not missing else "blocked",
            "reason": "产物默认停在内部确认；项目结束后执行结算回写与案例沉淀。",
        },
    ]
    return {
        "goal": _goal(client_name, project_name, parsed, business),
        "status": status,
        "client_name": client_name,
        "project_name": project_name,
        "top_n": top_n,
        "parsed_brief": asdict(parsed),
        "business": business,
        "output_checklist": PR_OS_OUTPUT_CHECKLIST,
        "red_lines": PR_OS_RED_LINES,
        "missing_fields": missing,
        "steps": steps,
    }


def missing_brief_fields(message: str, parsed: Any) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    if not getattr(parsed, "budget", 0):
        missing.append({"field": "budget", "label": CRITICAL_FIELDS["budget"], "question": "本次预算范围是多少？比如 30 万、50 万或 100 万。"})
    if not getattr(parsed, "platform_preference", []):
        missing.append({"field": "platform_preference", "label": CRITICAL_FIELDS["platform_preference"], "question": "优先投放哪些平台？比如小红书、抖音、微博、B站。"})
    if not getattr(parsed, "product", ""):
        missing.append({"field": "product", "label": CRITICAL_FIELDS["product"], "question": "这次要传播的产品或服务是什么？"})
    return missing


def clarification_payload(plan: dict[str, Any]) -> dict[str, Any]:
    questions = [item["question"] for item in plan.get("missing_fields", [])]
    return {
        "status": "needs_clarification",
        "title": "需要补充关键信息",
        "missing_fields": plan.get("missing_fields", []),
        "questions": questions,
        "suggested_reply_format": "请补充：预算、平台、产品、目标人群。补充后再次启动 Agent。",
    }


def _goal(client_name: str, project_name: str, parsed: Any, business: dict[str, Any] | None = None) -> str:
    project = project_name or getattr(parsed, "product", "") or "PR 项目"
    client = client_name or "未命名客户"
    product = getattr(parsed, "product", "") or project
    settlement = (business or {}).get("settlement_target") or "可审计交付与案例回写"
    label = (business or {}).get("business_type_label") or "传播"
    return f"为「{client}」的「{project}」完成 {product} 的 {label} 方案：KOL 推荐、媒介交付包、风险说明与客户交付草稿；结算标准：{settlement}。"
