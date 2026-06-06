from __future__ import annotations

from typing import Any

from src.schemas import stable_id
from src.simulation.schemas import AgentReaction, SimulationEdge, SimulationNode, SimulationReport, SimulationTimelineEvent
from src.simulation.stress_test_adapter import StressTestAdapter


class LlmFallbackStressTest(StressTestAdapter):
    """Deterministic multi-role fallback for Phase 1.5.

    This is intentionally conservative: it does not predict ROI or virality.
    It translates symbolic profiles and narrative paths into pressure-test risks.
    """

    engine_name = "llm_fallback"

    def run(self, payload: dict[str, Any]) -> SimulationReport:
        brand = payload.get("brand", {})
        matches = payload.get("matches", [])
        narratives = payload.get("narratives", [])
        danger_tags = brand.get("danger_tags", []) or []
        target_tags = brand.get("target_tags", []) or []
        product = brand.get("product") or brand.get("brand_name") or "该产品"
        brand_name = brand.get("brand_name") or product
        top_creator = matches[0].get("creator_name") if matches else "推荐博主"
        risk_points = list(dict.fromkeys(danger_tags[:3] + _collect(match.get("risk_points", []) for match in matches)))[:6]
        if not risk_points:
            risk_points = ["硬广感过强导致信任下降", "评论区偏离预设叙事"]
        narrative_path = narratives[0].get("narrative_path") if narratives else ""
        positive = [
            f"目标用户可能被{target_tags[0] if target_tags else '核心品牌标签'}叙事吸引。",
            f"{top_creator} 的内容结构有助于降低用户理解成本。",
        ]
        negative = [
            f"如果内容过度强调卖点，{product} 可能被理解为参数堆砌。",
            f"若评论区聚焦{danger_tags[0] if danger_tags else '价格'}，可能削弱品牌叙事。",
        ]
        misread = [
            f"被误读为{danger_tags[0] if danger_tags else '硬广投放'}",
            "用户只记住单点卖点，没有进入预设联想链",
        ]
        suggestions = [
            "增加真实使用细节，减少抽象口号。",
            "保留专业解释型内容节点，提前处理评论区疑问。",
            "避免绝对化承诺，把高风险表达改成边界清晰的体验描述。",
        ]
        if narrative_path:
            suggestions.insert(0, f"围绕叙事路径推进：{narrative_path}")

        nodes = _build_nodes(brand_name, product, top_creator, target_tags, risk_points, matches, narrative_path)
        edges = _build_edges(nodes, risk_points, matches)
        timeline = _build_timeline(product, top_creator, target_tags, risk_points, narrative_path)
        agent_reactions = _build_agent_reactions(product, top_creator, target_tags, risk_points)

        return SimulationReport(
            report_id=stable_id(product, top_creator, "stress", prefix="sim"),
            engine=self.engine_name,
            summary=f"该方案具备符号承接潜力，但需要重点控制{risk_points[0]}等压力点。",
            positive_reactions=positive,
            negative_reactions=negative,
            misreading_points=misread,
            risk_points=risk_points,
            optimization_suggestions=suggestions,
            final_recommendation="建议作为投放前压力测试结果使用，不作为 ROI 或爆款预测。",
            nodes=nodes,
            edges=edges,
            timeline=timeline,
            agent_reactions=agent_reactions,
            engine_status="fallback_ready",
        )


def _collect(iterables) -> list[str]:
    items: list[str] = []
    for iterable in iterables:
        items.extend(iterable or [])
    return items


def _build_nodes(
    brand_name: str,
    product: str,
    top_creator: str,
    target_tags: list[str],
    risk_points: list[str],
    matches: list[dict[str, Any]],
    narrative_path: str,
) -> list[SimulationNode]:
    nodes = [
        SimulationNode("brand", brand_name, "brand", "positive", "low", 82, "甲方输入的品牌叙事中心"),
        SimulationNode("product", product, "product", "positive", "medium", 76, "需要被转译成可感知体验"),
        SimulationNode("creator_primary", top_creator, "creator", "positive", "medium", 78, "首选承接内容的人格化节点"),
        SimulationNode("audience_core", "目标用户", "audience", "curious", "medium", 68, "会先判断内容是否真实可信"),
        SimulationNode("comment_field", "评论区", "comment", "mixed", "high", 62, "误读和补充解释会在这里放大"),
        SimulationNode("compliance", "品牌安全", "guardrail", "cautious", "high", 70, "检查绝对化承诺和争议表达"),
    ]
    for index, tag in enumerate(target_tags[:3], start=1):
        nodes.append(SimulationNode(f"target_{index}", tag, "target_tag", "positive", "low", 72 - index, "希望被用户记住的符号"))
    for index, risk in enumerate(risk_points[:4], start=1):
        nodes.append(SimulationNode(f"risk_{index}", risk, "risk_tag", "negative", "high", 66 + index, "需要提前降噪的传播压力点"))
    for index, match in enumerate(matches[1:4], start=2):
        nodes.append(
            SimulationNode(
                f"creator_{index}",
                match.get("creator_name") or f"备选博主 {index}",
                "creator",
                "neutral",
                "medium",
                int(match.get("symbolic_score") or match.get("match_score") or 60),
                match.get("recommended_role") or "备选内容节点",
            )
        )
    if narrative_path:
        nodes.append(SimulationNode("narrative_path", narrative_path, "narrative", "positive", "medium", 74, "当前建议的传播叙事路径"))
    return nodes


def _build_edges(nodes: list[SimulationNode], risk_points: list[str], matches: list[dict[str, Any]]) -> list[SimulationEdge]:
    node_ids = {node.node_id for node in nodes}
    edges = [
        SimulationEdge("brand", "product", "定义卖点", "influence", 76),
        SimulationEdge("product", "creator_primary", "内容转译", "influence", 82),
        SimulationEdge("creator_primary", "audience_core", "建立信任", "positive", 70),
        SimulationEdge("audience_core", "comment_field", "提问/复述", "feedback", 66),
        SimulationEdge("comment_field", "compliance", "放大风险", "risk", 78),
    ]
    if "narrative_path" in node_ids:
        edges.extend(
            [
                SimulationEdge("product", "narrative_path", "叙事组织", "positive", 72),
                SimulationEdge("narrative_path", "audience_core", "降低理解成本", "positive", 68),
            ]
        )
    for index, _risk in enumerate(risk_points[:4], start=1):
        risk_id = f"risk_{index}"
        if risk_id in node_ids:
            edges.append(SimulationEdge("comment_field", risk_id, "可能误读", "risk", 72 + index))
            edges.append(SimulationEdge(risk_id, "compliance", "需要预案", "risk", 75 + index))
    for index, _match in enumerate(matches[1:4], start=2):
        creator_id = f"creator_{index}"
        if creator_id in node_ids:
            edges.append(SimulationEdge("product", creator_id, "备选承接", "influence", 58 + index))
            edges.append(SimulationEdge(creator_id, "audience_core", "补充触达", "positive", 55 + index))
    return edges


def _build_timeline(
    product: str,
    top_creator: str,
    target_tags: list[str],
    risk_points: list[str],
    narrative_path: str,
) -> list[SimulationTimelineEvent]:
    target = target_tags[0] if target_tags else "核心价值"
    risk = risk_points[0] if risk_points else "硬广感"
    return [
        SimulationTimelineEvent("t1", 1, "品牌方", "brief", "输入传播目标", f"{product} 需要从卖点表达转成{target}感知。", "positive", "medium"),
        SimulationTimelineEvent("t2", 2, top_creator, "content", "博主发布内容", narrative_path or f"围绕真实体验解释 {product} 的使用场景。", "positive", "medium"),
        SimulationTimelineEvent("t3", 3, "目标用户", "reaction", "用户开始归因", f"用户会判断这是否只是广告，还是能解决自己的{target}需求。", "mixed", "medium"),
        SimulationTimelineEvent("t4", 4, "评论区", "amplification", "评论区分叉", f"如果前置信息不足，讨论可能转向{risk}。", "negative", "high"),
        SimulationTimelineEvent("t5", 5, "运营团队", "intervention", "补充解释和降噪", "用真实细节、边界说明和 FAQ 回复把争议拉回产品体验。", "positive", "medium"),
    ]


def _build_agent_reactions(
    product: str,
    top_creator: str,
    target_tags: list[str],
    risk_points: list[str],
) -> list[AgentReaction]:
    target = target_tags[0] if target_tags else "核心价值"
    risk = risk_points[0] if risk_points else "硬广感过强"
    return [
        AgentReaction(
            "agent_consumer",
            "目标用户 Agent",
            "target_consumer",
            "curious",
            f"我会先看 {top_creator} 是不是真的用过，而不是只听 {product} 的卖点。",
            concerns=[risk, "是否有真实使用证据"],
            positive_points=[f"{target}表达清楚时更容易被记住"],
            risk_flags=[risk],
        ),
        AgentReaction(
            "agent_marketing",
            "甲方市场 Agent",
            "client_marketing",
            "positive",
            "方向可以推进，但需要把口号改成用户可复述的场景语言。",
            concerns=["品牌主张是否被稀释"],
            positive_points=["博主人设能承接品牌符号", "内容路径有解释空间"],
            risk_flags=["表达过满"],
        ),
        AgentReaction(
            "agent_comment",
            "评论区 Agent",
            "platform_commenter",
            "mixed",
            "评论会追问价格、体验细节和是不是广告，需要提前准备回答。",
            concerns=["价格讨论抢走叙事", "单条负评被放大"],
            positive_points=["真实问答可以增强可信度"],
            risk_flags=[risk],
        ),
        AgentReaction(
            "agent_compliance",
            "品牌安全 Agent",
            "compliance_observer",
            "cautious",
            "避免绝对化、功效化和未经证明的领先表达。",
            concerns=["绝对化承诺", "竞品对比不清晰"],
            positive_points=["边界清楚的体验表达风险较低"],
            risk_flags=["合规表达"],
        ),
    ]
