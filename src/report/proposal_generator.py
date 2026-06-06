from __future__ import annotations

from collections import defaultdict

from src.schemas import BrandBrief, MatchResult


def _budget_allocation(brief: BrandBrief, results: list[MatchResult]) -> list[tuple[str, int]]:
    total = brief.budget or sum(max(r.suggested_budget, 0) for r in results[:10]) or 100_000
    platforms = brief.platform_preference or sorted({r.creator.platform for r in results[:10] if r.creator.platform})
    if not platforms:
        return [("待定", total)]
    reserve = int(total * 0.1)
    usable = total - reserve
    each = int(usable / len(platforms))
    allocation = [(platform, each) for platform in platforms]
    allocation.append(("机动测试", reserve))
    return allocation


def generate_markdown_proposal(brief: BrandBrief, results: list[MatchResult]) -> str:
    allocation = _budget_allocation(brief, results)
    grouped: dict[str, list[MatchResult]] = defaultdict(list)
    for result in results:
        grouped[result.creator.platform].append(result)

    lines: list[str] = [
        "# KOL 投放推荐方案",
        "",
        "## 1. Brief 摘要",
        "",
        f"- 行业：{brief.industry or '待确认'}",
        f"- 产品：{brief.product or '待确认'}",
        f"- 预算：{brief.budget or '待确认'}",
        f"- 传播阶段：{brief.campaign_stage or '待确认'}",
        f"- 传播目标：{', '.join(brief.goals) or '待确认'}",
        f"- 目标人群：{', '.join(brief.target_audience) or '待确认'}",
        f"- 平台偏好：{', '.join(brief.platform_preference) or '待确认'}",
        "",
        "## 2. 平台与预算建议",
        "",
    ]
    for platform, amount in allocation:
        lines.append(f"- {platform}：{amount:,} 元")

    lines.extend(["", "## 3. 推荐达人组合", ""])
    for idx, result in enumerate(results[:20], start=1):
        lines.extend(
            [
                f"### {idx}. {result.creator.name}（{result.creator.platform}）",
                "",
                f"- 匹配分：{result.match_score} / 100，{result.recommendation_level}",
                f"- 推荐角色：{result.recommended_role}",
                f"- 建议内容：{result.suggested_content}",
                f"- 建议预算：{result.suggested_budget:,} 元",
                f"- 报价判断：{result.price_judgement}",
                f"- 数据可信度：{result.data_confidence}",
                f"- 推荐理由：{'; '.join(result.reasons)}",
                f"- 风险提示：{'; '.join(result.risk_points)}",
                "",
            ]
        )

    lines.extend(
        [
            "## 4. 风险与人工核验",
            "",
            "- API 和公开数据只能作为初筛依据，报价、联系方式、履约反馈仍需媒介人工确认。",
            "- 对低可信度达人，建议核验主页、近期内容、评论区、历史商单和真实报价。",
            "- 本方案不承诺真实 ROI 预测，只作为投放前决策和沟通材料。",
            "",
            "## 5. 下一步",
            "",
            "1. 媒介复核推荐名单和报价。",
            "2. 与甲方确认平台策略和预算。",
            "3. 补充缺失案例和风险备注。",
            "4. 进入 Phase 2 的甲方协作确认流程。",
        ]
    )
    return "\n".join(lines)
