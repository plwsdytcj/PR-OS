"""Generate topic cards, quote skeletons, and client cards from PR briefs."""

from __future__ import annotations

import json
import re
from typing import Any

from src.intelligence.brief_parser import parse_brief
from src.intelligence.business_type import BUSINESS_TYPES, classify_business_type
from src.llm.glm_client import GlmClient
from src.schemas import BrandBrief

_PACKAGE_BY_TYPE: dict[str, dict[str, str]] = {
    "pr": {
        "name": "专业媒体解释包",
        "scope": "行业媒体解读稿、专家观点、采访提纲、 spokesperson 口径",
        "deliverables": "3-5 篇解释型稿件 / 专访 / 圆桌；媒体链接与截图证据包",
    },
    "marketing": {
        "name": "基础声量包",
        "scope": "多平台内容种草、话题策划、KOL 组合投放",
        "deliverables": "8-15 位 KOL 内容；话题词与传播节奏表；阶段数据截图",
    },
    "brand": {
        "name": "品牌故事包",
        "scope": "品牌理念转译、长期内容栏目、高信任节点背书",
        "deliverables": "品牌故事主线 + 3 条内容支线；可复用品牌语义素材",
    },
    "performance": {
        "name": "KOL 效果种草包",
        "scope": "可追踪转化的达人组合、内容 CTA、投放数据回收",
        "deliverables": "达人内容链接、转化/线索数据、ROI 复盘表",
    },
    "goodwill": {
        "name": "商誉沟通包",
        "scope": "投资者/合作方沟通、第三方背书、预期管理内容",
        "deliverables": "沟通口径、权威媒体露出、关键节点声明与证据",
    },
    "operations": {
        "name": "社群运营包",
        "scope": "私域/社群激活、内容栏目、用户互动机制",
        "deliverables": "运营排期、互动数据、留存/复购指标截图",
    },
}

_TOPIC_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "pr": [
        {"angle": "行业问题定义", "claim": "把产品放进行业真问题，而不是硬广", "format": "深度稿 / 专访"},
        {"angle": "技术/产品解释", "claim": "用专业节点把复杂信息转译给目标受众", "format": "测评 / 科普"},
        {"angle": "第三方背书", "claim": "借媒体或专家视角建立可信度", "format": "采访 / 圆桌"},
    ],
    "marketing": [
        {"angle": "场景种草", "claim": "把产品放进真实生活场景", "format": "短视频 / 图文"},
        {"angle": "话题引爆", "claim": "设计可参与的话题钩子", "format": "话题帖 / 挑战"},
        {"angle": "组合扩散", "claim": "头腰尾达人组合覆盖不同圈层", "format": "多平台联动"},
    ],
    "brand": [
        {"angle": "品牌主张", "claim": "讲清品牌长期想被记住什么", "format": "品牌片 / 故事稿"},
        {"angle": "价值共鸣", "claim": "连接受众身份与品牌理念", "format": "专栏 / 纪录片风"},
        {"angle": "符号一致性", "claim": "统一视觉、叙事与口吻", "format": "系列内容"},
    ],
    "performance": [
        {"angle": "痛点切入", "claim": "从用户痛点引出产品解决方案", "format": "口播 / 测评"},
        {"angle": "对比验证", "claim": "用可感知差异支撑购买理由", "format": "对比测评"},
        {"angle": "转化收口", "claim": "明确 CTA 与承接路径", "format": "直播 / 挂车视频"},
    ],
    "goodwill": [
        {"angle": "信心叙事", "claim": "稳定外界对品牌/公司的预期", "format": "权威报道"},
        {"angle": "里程碑解释", "claim": "把关键进展放进可理解语境", "format": "深度稿"},
        {"angle": "风险边界", "claim": "提前说明什么能说什么不能说", "format": "口径稿"},
    ],
    "operations": [
        {"angle": "激活机制", "claim": "设计用户愿意参与的动作", "format": "社群话题"},
        {"angle": "内容栏目", "claim": "固定栏目降低运营摩擦", "format": "周刊 / 直播"},
        {"angle": "复购链路", "claim": "从内容到留存到复购", "format": "私域内容"},
    ],
}


def _audience_label(brief: BrandBrief) -> str:
    if brief.target_audience:
        return "、".join(brief.target_audience[:3])
    return "核心目标人群"


def _platform_label(brief: BrandBrief) -> str:
    if brief.platform_preference:
        return "、".join(brief.platform_preference[:3])
    return "待确认平台"


def _product_label(brief: BrandBrief) -> str:
    return brief.product or brief.industry or "本次推广产品"


def generate_topic_cards(brief: BrandBrief, business: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    business = business or classify_business_type(brief)
    type_id = str(business.get("business_type") or "marketing")
    templates = list(_TOPIC_TEMPLATES.get(type_id) or _TOPIC_TEMPLATES["marketing"])
    product = _product_label(brief)
    audience = _audience_label(brief)
    platform = _platform_label(brief)
    settlement = str(business.get("settlement_target") or "")

    if brief.industry and "汽车" in brief.industry:
        templates.insert(0, {"angle": "试驾体验", "claim": f"用真实体验建立{product}可信度", "format": "试驾视频 / 长测评"})
    if "预热" in " ".join(brief.goals) or "预热" in str(brief.campaign_stage):
        templates.insert(0, {"angle": "上市预热", "claim": f"在正式上市前完成{product}认知铺垫", "format": "预告 / 悬念内容"})

    cards: list[dict[str, Any]] = []
    for index, template in enumerate(templates[:5], start=1):
        title = f"{product} · {template['angle']}"
        cards.append(
            {
                "topic_id": f"topic_{index}",
                "topic_title": title,
                "business_type": business.get("business_type_label") or "",
                "client_product": product,
                "brand_tag": brief.industry or "品牌",
                "product_tag": product,
                "audience_tag": audience,
                "platform": platform,
                "creator_fit": "高信任转译节点 / 行业专家 / 垂类头部" if business.get("recommend_two_stage") else "垂类达人 / 场景种草号",
                "core_claim": template["claim"],
                "evidence_needed": "产品事实、可公开数据、过往案例链接、客户确认口径",
                "content_format": template["format"],
                "risk_line": "避免夸大功效、未披露商单、敏感议题与竞品拉踩",
                "settlement_target": settlement,
            }
        )
    return cards


def generate_quote_skeleton(
    brief: BrandBrief,
    business: dict[str, Any] | None = None,
    *,
    creator_count: int = 8,
) -> dict[str, Any]:
    business = business or classify_business_type(brief)
    type_id = str(business.get("business_type") or "marketing")
    package = dict(_PACKAGE_BY_TYPE.get(type_id) or _PACKAGE_BY_TYPE["marketing"])
    budget = int(brief.budget or 0)
    per_creator = max(8_000, budget // max(creator_count, 1)) if budget else 0
    management_rate = 0.12
    resource_subtotal = per_creator * creator_count if per_creator else 0
    management_fee = int(resource_subtotal * management_rate) if resource_subtotal else 0
    total = resource_subtotal + management_fee if resource_subtotal else 0

    milestones = [
        {"stage": "立项确认", "ratio": "30%", "condition": "Brief 确认、名单确认、合同签署"},
        {"stage": "内容发布", "ratio": "50%", "condition": "达人内容发布完成并提交链接截图"},
        {"stage": "结案验收", "ratio": "20%", "condition": "数据回收、客户确认、案例回写"},
    ]

    return {
        "package_name": package["name"],
        "business_type": business.get("business_type_label") or "",
        "client_goal": "、".join(brief.goals[:4]) or str(business.get("settlement_target") or ""),
        "scope": package["scope"],
        "deliverable_units": package["deliverables"],
        "creator_count": creator_count,
        "budget_total": budget,
        "resource_cost": resource_subtotal,
        "management_fee": management_fee,
        "quoted_total": total or budget,
        "timeline": "立项后 2 周出名单，4-6 周完成发布与证据回收",
        "revision_boundary": "每个达人内容 1 次合理修改；重大方向变更需重新确认范围",
        "evidence_package": "发布链接、截图、核心数据、客户确认记录",
        "payment_milestones": milestones,
        "exclusions": "不含素材拍摄制作、不含平台投流费用、不含线下活动执行",
        "exit_rule": "若客户连续 2 周未确认关键节点，项目可暂停并按已完成交付结算",
        "settlement_target": business.get("settlement_target") or "",
    }


def build_client_card(
    brief: BrandBrief,
    business: dict[str, Any] | None = None,
    *,
    client_name: str = "",
) -> dict[str, Any]:
    business = business or classify_business_type(brief)
    text = str(brief.raw_text or "")
    must_not = []
    for token in ["不能说", "禁止", "避免", "不要提", "不可"]:
        if token in text:
            must_not.append("见 Brief 禁区描述")
            break
    if "竞品" in text:
        must_not.append("不主动对比拉踩竞品")

    return {
        "client_name": client_name.strip() or "待填写客户",
        "industry": brief.industry or "",
        "decision_maker": _extract_field(text, r"决策人[：:]\s*([^\n，,]+)") or "",
        "contact_person": _extract_field(text, r"联系人[：:]\s*([^\n，,]+)") or "",
        "budget_range": f"{brief.budget:,} 元" if brief.budget else "",
        "demand_type": business.get("business_type_label") or "",
        "product_service": _product_label(brief),
        "product_facts": _extract_field(text, r"产品[^，。\n]{0,8}[：:]\s*([^\n。]+)") or brief.product or "",
        "brand_meaning": "、".join(brief.content_preference[:4]) or "",
        "target_audience": _audience_label(brief),
        "required_platforms": _platform_label(brief),
        "must_say": "、".join(brief.goals[:4]) or "",
        "must_not_say": "；".join(must_not) if must_not else "",
        "proof_evidence": "产品参数、检测报告、过往案例、可公开数据",
        "deadline": _extract_field(text, r"(上线|发布|截止)[时间日期]*[：:]\s*([^\n，,]+)") or "",
        "payment_status": "待确认",
        "risk_notes": "商单披露、事实可证、平台合规、舆情边界",
        "settlement_target": business.get("settlement_target") or "",
        "next_action": "确认业务类型与结算标准 → 出达人短名单 → 报价骨架 → 客户确认",
        "brief_excerpt": text[:500],
    }


def _extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    if not match:
        return ""
    return match.group(match.lastindex or 1).strip()


def generate_brief_deliverables(
    brief_text: str,
    *,
    client_name: str = "",
    creator_count: int = 8,
    use_llm: bool = False,
) -> dict[str, Any]:
    brief = parse_brief(brief_text)
    business = classify_business_type(brief)
    topics = generate_topic_cards(brief, business)
    if use_llm:
        topics = _glm_enrich_topic_cards(brief, business, topics)
    quote = generate_quote_skeleton(brief, business, creator_count=creator_count)
    client_card = build_client_card(brief, business, client_name=client_name)
    return {
        "brief": {
            "industry": brief.industry,
            "product": brief.product,
            "budget": brief.budget,
            "goals": brief.goals,
            "platform_preference": brief.platform_preference,
        },
        "business": business,
        "client_card": client_card,
        "topic_cards": topics,
        "quote_skeleton": quote,
        "ai_enriched": use_llm,
        "markdown": render_deliverables_markdown(client_card, business, topics, quote),
    }


def _glm_enrich_topic_cards(brief: BrandBrief, business: dict[str, Any], topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    client = GlmClient()
    if not client.available or not topics:
        return topics
    try:
        payload = client.complete_json(
            "你是公关传媒项目经理。根据 Brief 润色选题卡，保持 JSON 数组结构，每项保留 topic_id/topic_title/core_claim/content_format/creator_fit/evidence_needed/risk_line/settlement_target 字段。",
            json.dumps(
                {
                    "brief": brief.raw_text[:1200],
                    "business_type": business.get("business_type_label"),
                    "topics": topics,
                },
                ensure_ascii=False,
            ),
            timeout=45,
        )
        enriched = payload.get("topics") or payload.get("topic_cards") or payload
        if isinstance(enriched, list) and enriched:
            merged: list[dict[str, Any]] = []
            for index, item in enumerate(enriched[:5]):
                base = topics[index] if index < len(topics) else topics[-1]
                if isinstance(item, dict):
                    merged.append({**base, **item, "topic_id": base.get("topic_id") or f"topic_{index + 1}"})
            return merged or topics
    except Exception:
        return topics
    return topics


def render_deliverables_markdown(
    client_card: dict[str, Any],
    business: dict[str, Any],
    topics: list[dict[str, Any]],
    quote: dict[str, Any],
) -> str:
    lines = [
        f"# 媒介交付包 · {client_card.get('product_service') or '项目'}",
        "",
        "## 客户卡",
        "",
        f"- 客户：{client_card.get('client_name')}",
        f"- 行业：{client_card.get('industry') or '待确认'}",
        f"- 业务类型：{client_card.get('demand_type')}",
        f"- 预算：{client_card.get('budget_range') or '待确认'}",
        f"- 目标人群：{client_card.get('target_audience')}",
        f"- 平台：{client_card.get('required_platforms')}",
        f"- 结算目标：{client_card.get('settlement_target')}",
        f"- 下一步：{client_card.get('next_action')}",
        "",
        "## 选题卡",
        "",
    ]
    for index, topic in enumerate(topics, start=1):
        lines.extend(
            [
                f"### {index}. {topic.get('topic_title')}",
                "",
                f"- 核心主张：{topic.get('core_claim')}",
                f"- 内容形式：{topic.get('content_format')}",
                f"- 达人适配：{topic.get('creator_fit')}",
                f"- 需备证据：{topic.get('evidence_needed')}",
                f"- 风险线：{topic.get('risk_line')}",
                "",
            ]
        )
    lines.extend(
        [
            "## 报价骨架",
            "",
            f"- 套餐：{quote.get('package_name')}",
            f"- 范围：{quote.get('scope')}",
            f"- 交付单元：{quote.get('deliverable_units')}",
            f"- 达人数量：{quote.get('creator_count')}",
            f"- 资源成本：{quote.get('resource_cost') or '待测算'}",
            f"- 管理费：{quote.get('management_fee') or '待测算'}",
            f"- 报价合计：{quote.get('quoted_total') or quote.get('budget_total') or '待测算'}",
            f"- 时间线：{quote.get('timeline')}",
            f"- 修订边界：{quote.get('revision_boundary')}",
            f"- 付款节点："
            + "；".join(f"{item['stage']} {item['ratio']}" for item in quote.get("payment_milestones", [])),
            f"- 不含项：{quote.get('exclusions')}",
            f"- 退出规则：{quote.get('exit_rule')}",
        ]
    )
    return "\n".join(lines)
