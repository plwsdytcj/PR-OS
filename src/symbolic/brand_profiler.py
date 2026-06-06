from __future__ import annotations

import json

from src.llm.glm_client import GlmClient
from src.schemas import stable_id
from src.symbolic.schemas import BrandSymbolicProfile, Evidence


BRAND_ARCHETYPES = {
    "汽车": {
        "current": ["智能化", "高端感", "家庭安全"],
        "target": ["移动自由", "城市身份升级", "科技信任"],
        "danger": ["价格争议", "参数空转", "伪高端", "智驾安全误读"],
        "emotion": ["安全感", "控制感", "生活半径扩大"],
        "identity": ["城市中产", "家庭责任", "效率生活"],
        "metaphor": ["移动城堡", "第二生活空间", "城市避难所"],
        "metonymy": ["车钥匙", "智能座舱", "后备箱", "露营装备"],
        "issues": ["城市通勤", "家庭出行", "智能化生活"],
        "unsafe": ["价格刺客", "智驾事故", "油电争议"],
        "creator": ["汽车测评", "城市生活方式", "科技解释型"],
        "path": "从城市通勤压力切入，经由智能座舱和安全感叙事，转向家庭生活半径扩张。",
    },
    "AI软件": {
        "current": ["效率工具", "智能化", "技术红利"],
        "target": ["外部大脑", "组织放大器", "个人能力升级"],
        "danger": ["替代焦虑", "技术空转", "工具同质化"],
        "emotion": ["确定性", "掌控感", "效率安全感"],
        "identity": ["高效个体", "小团队创业者", "职场升级者"],
        "metaphor": ["外部大脑", "第二生产力", "组织放大器"],
        "metonymy": ["提示词", "工作流", "仪表盘", "自动化按钮"],
        "issues": ["AI时代职业变化", "个人效率", "小公司组织能力"],
        "unsafe": ["失业焦虑", "AI泡沫", "隐私风险"],
        "creator": ["科技解释型", "职场教育型", "商业分析型"],
        "path": "从工作焦虑切入，经由 AI 中介能力，转向个人和小团队的组织能力升级。",
    },
    "美妆护肤": {
        "current": ["成分科技", "真实功效", "精致消费"],
        "target": ["专业可信", "时间管理", "稳定变美"],
        "danger": ["智商税", "过度承诺", "硬广不信任"],
        "emotion": ["确定性", "安全感", "自我照料"],
        "identity": ["精致女性", "成分党", "抗老焦虑人群"],
        "metaphor": ["皮肤秩序", "时间管理", "成分护城河"],
        "metonymy": ["成分表", "实验室", "瓶身", "使用前后"],
        "issues": ["抗老焦虑", "成分安全", "真实测评"],
        "unsafe": ["容貌焦虑过度刺激", "功效夸大"],
        "creator": ["成分测评", "真实种草", "审美生活型"],
        "path": "从用户不确定的护肤决策切入，经由成分证据和真实使用，转向稳定自我照料。",
    },
}


def generate_brand_symbolic_profile(payload: dict, use_llm: bool = True) -> BrandSymbolicProfile:
    brand_name = str(payload.get("brand_name") or payload.get("brand") or "未命名品牌").strip()
    product = str(payload.get("product") or "").strip()
    industry = str(payload.get("industry") or _infer_industry(" ".join(map(str, payload.values())))).strip()
    raw = "\n".join(f"{key}: {value}" for key, value in payload.items() if value)
    archetype = BRAND_ARCHETYPES.get(industry, BRAND_ARCHETYPES["AI软件"])

    target_extra = _splitish(payload.get("target_tags"))
    danger_extra = _splitish(payload.get("danger_tags"))
    evidence = [
        Evidence(
            claim="品牌符号分析",
            source="品牌输入",
            quote=raw[:180] or "使用行业默认符号模板生成，需人工补充品牌资料。",
        )
    ]
    fallback = BrandSymbolicProfile(
        brand_id=stable_id(brand_name, product, prefix="brand"),
        brand_name=brand_name,
        product=product,
        industry=industry,
        current_tags=sorted(set(archetype["current"] + _splitish(payload.get("current_tags")))),
        target_tags=sorted(set(archetype["target"] + target_extra)),
        danger_tags=sorted(set(archetype["danger"] + danger_extra)),
        emotional_value=list(archetype["emotion"]),
        identity_value=list(archetype["identity"]),
        product_metaphors=list(archetype["metaphor"]),
        product_metonymies=list(archetype["metonymy"]),
        suitable_social_issues=list(archetype["issues"]),
        unsafe_social_issues=list(archetype["unsafe"]),
        suitable_creator_types=list(archetype["creator"]),
        communication_path=str(payload.get("communication_path") or archetype["path"]),
        evidence=evidence,
        confidence=0.76 if raw else 0.55,
        raw_input=raw,
    )
    if not use_llm:
        return fallback
    return _try_llm_brand_profile(fallback, payload)


def _infer_industry(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["车", "汽车", "suv", "智驾", "座舱"]):
        return "汽车"
    if any(token.lower() in lowered for token in ["ai", "软件", "效率", "工具", "大模型"]):
        return "AI软件"
    if any(token in lowered for token in ["护肤", "美妆", "成分", "抗老"]):
        return "美妆护肤"
    return "AI软件"


def _splitish(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value)
    for sep in ["，", "、", ";", "；", "|", "\n"]:
        text = text.replace(sep, ",")
    return [item.strip() for item in text.split(",") if item.strip()]


def _try_llm_brand_profile(fallback: BrandSymbolicProfile, payload: dict) -> BrandSymbolicProfile:
    client = GlmClient()
    if not client.available:
        return fallback
    system = "你是PR AI OS的品牌符号策略分析器。只输出JSON，不要输出解释文字。"
    user = f"""
基于品牌输入生成品牌/产品符号档案。字段必须包含：
current_tags, target_tags, danger_tags, emotional_value, identity_value,
product_metaphors, product_metonymies, suitable_social_issues, unsafe_social_issues,
suitable_creator_types, communication_path, confidence。
列表字段输出字符串数组，confidence为0到1之间的小数。

品牌输入：{json.dumps(payload, ensure_ascii=False)}
规则底稿：{fallback.to_json()}
"""
    try:
        data = client.complete_json(system, user)
    except Exception:
        return fallback
    base = fallback.to_dict()
    for field in [
        "current_tags",
        "target_tags",
        "danger_tags",
        "emotional_value",
        "identity_value",
        "product_metaphors",
        "product_metonymies",
        "suitable_social_issues",
        "unsafe_social_issues",
        "suitable_creator_types",
        "communication_path",
        "confidence",
    ]:
        if field in data:
            base[field] = data[field]
    base["evidence"].append(
        {
            "claim": "LLM增强",
            "source": "GLM",
            "quote": "已基于规则底稿和品牌输入进行符号档案增强",
        }
    )
    return BrandSymbolicProfile.from_json(json.dumps(base, ensure_ascii=False))
