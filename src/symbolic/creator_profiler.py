from __future__ import annotations

import json

from src.schemas import CreatorProfile
from src.llm.glm_client import GlmClient
from src.symbolic.schemas import CreatorSymbolicProfile, Evidence


SYMBOLIC_PATTERNS = {
    "城市通勤": {
        "keywords": ["通勤", "城市", "车", "SUV", "试驾", "智能座舱", "家庭", "周末", "露营"],
        "persona": "城市生活方式型",
        "emotion": "在高压城市生活中寻找安全感和可控生活半径",
        "fantasy": "通过更好的工具、空间和路线获得稳定生活",
        "metaphors": ["移动客厅", "城市避难所", "第二生活空间"],
        "metonymies": ["车钥匙", "通勤路线", "后备箱", "儿童座椅", "露营装备"],
        "brands": ["新能源车", "家居", "香氛", "城市生活方式"],
    },
    "科技解释": {
        "keywords": ["AI", "AIGC", "科技", "智能", "软件", "效率", "工具", "产品", "解释"],
        "persona": "技术解释型",
        "emotion": "用理性解释降低不确定性和技术焦虑",
        "fantasy": "普通人借助工具获得外部能力和组织放大器",
        "metaphors": ["外部大脑", "组织放大器", "第二生产力"],
        "metonymies": ["工作流", "提示词", "仪表盘", "自动化按钮"],
        "brands": ["AI软件", "3C数码", "效率工具", "B端SaaS"],
    },
    "审美生活": {
        "keywords": ["生活方式", "质感", "松弛", "审美", "治愈", "香氛", "家居", "穿搭"],
        "persona": "审美生活型",
        "emotion": "通过审美秩序和消费细节补偿安全感缺口",
        "fantasy": "通过审美和消费获得更高级、更稳定的自己",
        "metaphors": ["生活样板间", "审美庇护所", "日常仪式"],
        "metonymies": ["香氛", "餐桌", "灯光", "衣橱", "咖啡杯"],
        "brands": ["高端家居", "香氛", "轻奢", "城市生活方式", "新能源车"],
    },
    "成分信任": {
        "keywords": ["护肤", "美妆", "成分", "抗老", "精华", "测评", "敏感肌"],
        "persona": "消费决策型",
        "emotion": "在不确定消费中寻找专业背书和可验证安全感",
        "fantasy": "通过专业知识降低变美和消费决策风险",
        "metaphors": ["皮肤秩序", "成分护城河", "时间管理"],
        "metonymies": ["成分表", "实验室", "瓶身", "使用前后"],
        "brands": ["美妆护肤", "高端护肤", "个护", "健康消费"],
    },
    "财经信任": {
        "keywords": ["财经", "商业", "投资", "资产", "创业", "管理", "公司", "中年"],
        "persona": "财经理性型",
        "emotion": "在资产和身份不确定中寻找理性解释和可信担保",
        "fantasy": "通过结构化判断重新获得商业世界的确定性",
        "metaphors": ["安全垫", "现金流机器", "第二曲线"],
        "metonymies": ["财报", "估值", "办公室", "商业计划书"],
        "brands": ["金融服务", "企业服务", "知识付费", "AI软件"],
    },
}


def _source_text(profile: CreatorProfile, content_sample: str, comment_sample: str, case_sample: str) -> str:
    return " ".join(
        [
            profile.name,
            profile.platform,
            profile.bio,
            profile.manual_notes,
            " ".join(profile.industry_fit_tags),
            " ".join(profile.content_capability_tags),
            " ".join(profile.cooperation_brands),
            " ".join(profile.cooperation_formats),
            content_sample,
            comment_sample,
            case_sample,
        ]
    )


def _match_patterns(text: str) -> list[tuple[str, int]]:
    lowered = text.lower()
    scored: list[tuple[str, int]] = []
    for tag, pattern in SYMBOLIC_PATTERNS.items():
        score = sum(1 for keyword in pattern["keywords"] if keyword.lower() in lowered)
        if score:
            scored.append((tag, score))
    return sorted(scored, key=lambda item: item[1], reverse=True)


def generate_creator_symbolic_profile(
    profile: CreatorProfile,
    content_sample: str = "",
    comment_sample: str = "",
    case_sample: str = "",
    use_llm: bool = True,
) -> CreatorSymbolicProfile:
    text = _source_text(profile, content_sample, comment_sample, case_sample)
    matches = _match_patterns(text)
    primary = [item[0] for item in matches[:2]] or profile.industry_fit_tags[:1] or ["通用传播节点"]
    secondary = [item[0] for item in matches[2:5]]
    top = SYMBOLIC_PATTERNS.get(primary[0], SYMBOLIC_PATTERNS["审美生活"])

    capabilities = set(profile.content_capability_tags)
    if "专业科普" in capabilities or "口播解释" in capabilities:
        narrative = "通过解释、拆解和证据建立信任"
    elif "创意TVC" in capabilities:
        narrative = "通过视觉化和高概念表达制造记忆点"
    elif "测评" in capabilities or "场景体验" in capabilities:
        narrative = "通过真实场景和体验细节建立可信样本"
    else:
        narrative = "通过日常分享和情绪共鸣完成种草"

    evidence = [
        Evidence(
            claim=f"主标签：{primary[0]}",
            source="达人资料 / 内容样本",
            quote=_evidence_quote(text, top["keywords"]),
        )
    ]
    if profile.cooperation_brands:
        evidence.append(
            Evidence(
                claim="案例背书",
                source="历史合作品牌",
                quote="、".join(profile.cooperation_brands[:4]),
            )
        )

    confidence = min(0.92, 0.45 + len(matches) * 0.1 + (0.12 if content_sample else 0) + (0.12 if profile.cooperation_brands else 0))
    risk_tags = sorted(set(profile.risk_tags + ["硬广破坏真实感"] if profile.listed_price else profile.risk_tags + ["商业报价待确认"]))
    unsuitable = ["低价促销", "强冲突议题"] if primary[0] in {"审美生活", "城市通勤"} else ["无证据背书的强转化承诺"]
    fallback = CreatorSymbolicProfile(
        creator_id=profile.creator_id,
        creator_name=profile.name,
        primary_tags=primary,
        secondary_tags=secondary,
        persona_structure=str(top["persona"]),
        emotional_tone=str(top["emotion"]),
        narrative_style=narrative,
        audience_fantasy=str(top["fantasy"]),
        common_metaphors=list(top["metaphors"]),
        common_metonymies=list(top["metonymies"]),
        suitable_brand_types=sorted(set(list(top["brands"]) + profile.industry_fit_tags[:3])),
        unsuitable_brand_types=unsuitable,
        risk_tags=risk_tags[:6],
        evidence=evidence,
        confidence=round(confidence, 2),
        content_sample=content_sample,
        comment_sample=comment_sample,
        case_sample=case_sample,
    )
    if not use_llm:
        return fallback
    return _try_llm_creator_profile(fallback, profile, content_sample, comment_sample, case_sample)


def _evidence_quote(text: str, keywords: list[str]) -> str:
    hits = [keyword for keyword in keywords if keyword.lower() in text.lower()]
    if hits:
        return f"资料中出现：{'、'.join(hits[:6])}"
    return text[:80] if text else "资料不足，需人工补充内容样本。"


def _try_llm_creator_profile(
    fallback: CreatorSymbolicProfile,
    profile: CreatorProfile,
    content_sample: str,
    comment_sample: str,
    case_sample: str,
) -> CreatorSymbolicProfile:
    client = GlmClient()
    if not client.available:
        return fallback
    system = "你是PR AI OS的符号策略分析器。只输出JSON，不要输出解释文字。"
    user = f"""
基于以下达人资料生成符号档案。字段必须包含：
primary_tags, secondary_tags, persona_structure, emotional_tone, narrative_style, audience_fantasy,
common_metaphors, common_metonymies, suitable_brand_types, unsuitable_brand_types, risk_tags, confidence。
列表字段输出字符串数组，confidence为0到1之间的小数。

达人资料：
名称：{profile.name}
平台：{profile.platform}
简介：{profile.bio}
基础标签：{profile.industry_fit_tags + profile.content_capability_tags}
合作品牌：{profile.cooperation_brands}
媒介备注：{profile.manual_notes}
内容样本：{content_sample}
评论样本：{comment_sample}
案例样本：{case_sample}
规则底稿：{fallback.to_json()}
"""
    try:
        data = client.complete_json(system, user)
    except Exception:
        return fallback
    base = fallback.to_dict()
    for field in [
        "primary_tags",
        "secondary_tags",
        "persona_structure",
        "emotional_tone",
        "narrative_style",
        "audience_fantasy",
        "common_metaphors",
        "common_metonymies",
        "suitable_brand_types",
        "unsuitable_brand_types",
        "risk_tags",
        "confidence",
    ]:
        if field in data:
            base[field] = data[field]
    base["evidence"].append(
        {
            "claim": "LLM增强",
            "source": "GLM",
            "quote": "已基于规则底稿和样本进行符号档案增强",
        }
    )
    return CreatorSymbolicProfile.from_json(json.dumps(base, ensure_ascii=False))
