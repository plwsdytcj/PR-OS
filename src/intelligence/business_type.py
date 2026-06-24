"""Classify PR briefs into Wang Ming OS business types and settlement targets."""

from __future__ import annotations

import re
from typing import Any

from src.intelligence.brief_parser import parse_brief
from src.schemas import BrandBrief

BUSINESS_TYPES: dict[str, dict[str, str]] = {
    "pr": {
        "label": "公关",
        "settlement": "可审计发布链接、叙事站位、关系方态度变化、风险可控",
    },
    "marketing": {
        "label": "营销",
        "settlement": "活动产出、有效触达、话题参与、可量化传播反馈",
    },
    "brand": {
        "label": "品牌",
        "settlement": "品牌语义沉淀、识别度提升、长期信任与溢价感",
    },
    "performance": {
        "label": "效果",
        "settlement": "ROI、线索、转化、订单或其他约定量化指标",
    },
    "goodwill": {
        "label": "商誉",
        "settlement": "投资人/合作方/公众信心稳定、第三方背书、预期管理",
    },
    "operations": {
        "label": "运营",
        "settlement": "激活、留存、复购、社群参与或流程完成率",
    },
}

_TYPE_SIGNALS: dict[str, list[str]] = {
    "pr": [
        "公关",
        "舆情",
        "危机",
        "声明",
        "回应",
        "媒体关系",
        "解释",
        "澄清",
        "议题",
        "破圈",
        "背书",
        "权威",
        "专业媒体",
        "采访",
        "专访",
        "发言人",
        "声誉",
        "口碑修复",
    ],
    "marketing": [
        "营销",
        "campaign",
        "活动",
        "曝光",
        "种草",
        "预热",
        "上市",
        "传播",
        "话题",
        "破圈",
        "声量",
        "节点",
        "大促",
        "节点营销",
    ],
    "brand": [
        "品牌",
        "定位",
        "理念",
        "价值观",
        "长期",
        "形象",
        "升级",
        "焕新",
        "认知",
        "心智",
        "溢价",
        "故事",
    ],
    "performance": [
        "转化",
        "roi",
        "线索",
        "留资",
        "下单",
        "成交",
        "销售",
        "cpa",
        "cps",
        "带货",
        "效果",
        "投产",
        "gmv",
    ],
    "goodwill": [
        "投资者",
        "投资人",
        "股东",
        "资本",
        "商誉",
        "信心",
        "融资",
        "ipo",
        "年报",
        "市值",
        "资本市场",
    ],
    "operations": [
        "运营",
        "私域",
        "社群",
        "留存",
        "复购",
        "拉新",
        "激活",
        "会员",
        "日活",
        "月活",
        "转化漏斗",
    ],
}

_GOAL_TYPE_HINTS: dict[str, str] = {
    "舆情修复": "pr",
    "公关破圈": "pr",
    "品牌背书": "pr",
    "搜索沉淀": "marketing",
    "曝光": "marketing",
    "种草": "marketing",
    "新品预热": "marketing",
    "转化": "performance",
    "用户教育": "brand",
}


def _score_type(text: str, brief: BrandBrief) -> dict[str, int]:
    lowered = text.lower()
    scores = {key: 0 for key in BUSINESS_TYPES}
    for type_id, signals in _TYPE_SIGNALS.items():
        for signal in signals:
            if signal.lower() in lowered or signal in text:
                scores[type_id] += 2 if len(signal) >= 3 else 1
    for goal in brief.goals:
        hinted = _GOAL_TYPE_HINTS.get(goal)
        if hinted:
            scores[hinted] += 3
    if brief.campaign_stage and "预热" in brief.campaign_stage:
        scores["marketing"] += 2
    if "专业测评" in brief.content_preference or "口播解释" in brief.content_preference:
        scores["pr"] += 2
    if re.search(r"预算\s*\d+.*万", text) and any(token in text for token in ("转化", "线索", "成交")):
        scores["performance"] += 3
    return scores


def classify_business_type(brief: BrandBrief | str) -> dict[str, Any]:
    parsed = parse_brief(brief) if isinstance(brief, str) else brief
    text = str(parsed.raw_text or "")
    scores = _score_type(text, parsed)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_id, top_score = ranked[0]
    second_id, second_score = ranked[1] if len(ranked) > 1 else ("", 0)

    if top_score <= 0:
        top_id = "marketing"
        confidence = "low"
        reason = "Brief 未出现明确业务类型信号，默认按营销传播处理。"
    elif top_score == second_score and top_score > 0:
        confidence = "medium"
        reason = f"同时命中「{BUSINESS_TYPES[top_id]['label']}」与「{BUSINESS_TYPES[second_id]['label']}」，建议先确认结算标准。"
    elif top_score >= second_score + 4:
        confidence = "high"
        reason = f"需求更接近「{BUSINESS_TYPES[top_id]['label']}」类项目。"
    else:
        confidence = "medium"
        reason = f"主判断为「{BUSINESS_TYPES[top_id]['label']}」，次选为「{BUSINESS_TYPES[second_id]['label']}」。"

    meta = BUSINESS_TYPES[top_id]
    secondary = BUSINESS_TYPES.get(second_id, {}) if second_score > 0 else {}
    recommend_two_stage = top_id in {"pr", "brand", "goodwill"} or any(
        token in text for token in ("解释", "专业", "权威", "背书", "转译", "教育")
    )

    return {
        "business_type": top_id,
        "business_type_label": meta["label"],
        "settlement_target": meta["settlement"],
        "secondary_type": second_id if second_score > 0 else "",
        "secondary_type_label": secondary.get("label", ""),
        "confidence": confidence,
        "reason": reason,
        "scores": scores,
        "recommend_two_stage": recommend_two_stage,
        "recommendation_mode": "two_stage_propagation" if recommend_two_stage else "reach_first",
    }


def enrich_brief_analysis(brief: BrandBrief) -> dict[str, Any]:
    business = classify_business_type(brief)
    return {
        "brief": {
            "raw_text": brief.raw_text,
            "industry": brief.industry,
            "product": brief.product,
            "budget": brief.budget,
            "campaign_stage": brief.campaign_stage,
            "goals": brief.goals,
            "target_audience": brief.target_audience,
            "platform_preference": brief.platform_preference,
            "content_preference": brief.content_preference,
        },
        "business": business,
    }
