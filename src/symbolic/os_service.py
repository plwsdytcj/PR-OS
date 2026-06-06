from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.platform_os.schemas import CampaignProject, PostCampaignReview
from src.schemas import CreatorProfile, split_tags
from src.storage.db import load_profile
from src.symbolic.creator_profiler import generate_creator_symbolic_profile
from src.symbolic.schemas import BrandSymbolicProfile, Evidence
from src.symbolic.os_schemas import (
    BrandCreatorMatchAsset,
    ContentNarrativeAsset,
    FeedbackCorrection,
    ProductSymbolicProfile,
    SignifierTag,
    SocialSymbolicIssue,
    SocialSymbolicReport,
    correction_id_for,
    match_id_for,
    narrative_id_for,
    product_id_for,
    report_id_for,
    tag_id_for,
)
from src.symbolic.os_storage import (
    load_all_brand_creator_matches,
    load_all_content_narratives,
    load_all_feedback_corrections,
    load_all_product_symbolic,
    load_all_signifier_tags,
    load_all_social_reports,
    upsert_feedback_correction,
    upsert_content_narrative,
    upsert_brand_creator_match,
    upsert_product_symbolic,
    upsert_signifier_tag,
    upsert_social_report,
)
from src.symbolic.storage import load_creator_symbolic, upsert_creator_symbolic


SEED_TAGS = [
    {
        "name": "安全感缺失",
        "tag_type": "情绪标签",
        "related_tags": ["确定性", "秩序补偿", "家庭安全"],
        "opposite_tags": ["冒险", "自由探索"],
        "metaphor_relations": ["避难所", "安全垫", "移动城堡"],
        "emotion": "焦虑后的稳定需求",
        "suitable_industries": ["汽车", "护肤", "保险", "家居", "AI软件"],
        "suitable_creator_types": ["生活方式型", "专业解释型", "真实测评型"],
        "risk_notes": "不要过度制造焦虑，否则容易被理解为恐吓式营销。",
    },
    {
        "name": "外部大脑",
        "tag_type": "隐喻标签",
        "related_tags": ["组织放大器", "个人能力升级", "效率安全感"],
        "opposite_tags": ["工具空转", "替代焦虑"],
        "metonymy_relations": ["提示词", "工作流", "自动化按钮"],
        "emotion": "把复杂判断外包给可信系统",
        "suitable_industries": ["AI软件", "教育", "企业服务"],
        "suitable_creator_types": ["科技解释型", "职场教育型", "商业分析型"],
        "risk_notes": "需要解释具体场景，不要停留在抽象效率口号。",
    },
    {
        "name": "精致生活补偿",
        "tag_type": "消费标签",
        "related_tags": ["审美秩序", "自我照料", "身份表达"],
        "opposite_tags": ["低价促销", "土味转化"],
        "metaphor_relations": ["生活样板间", "审美庇护所"],
        "emotion": "用审美和消费细节恢复可控感",
        "suitable_industries": ["美妆护肤", "家居", "香氛", "汽车"],
        "suitable_creator_types": ["审美生活型", "真实种草型"],
        "risk_notes": "过度商业化会破坏审美信任。",
    },
    {
        "name": "硬广不信任",
        "tag_type": "风险标签",
        "related_tags": ["评论区反噬", "商业密度过高", "真实感不足"],
        "opposite_tags": ["真实试用", "长期案例"],
        "metonymy_relations": ["口播", "挂链", "统一话术"],
        "emotion": "用户对商业内容的预设防御",
        "suitable_industries": ["全行业"],
        "suitable_creator_types": ["评论区管理", "真实体验型"],
        "risk_notes": "需要用场景、证据和边界说明降低防御。",
    },
    {
        "name": "城市自由",
        "tag_type": "身份标签",
        "related_tags": ["生活半径扩大", "移动自由", "城市中产"],
        "opposite_tags": ["通勤压迫", "空间受限"],
        "metaphor_relations": ["第二生活空间", "移动客厅"],
        "emotion": "从拥挤秩序里恢复选择权",
        "suitable_industries": ["汽车", "旅行", "户外", "本地生活"],
        "suitable_creator_types": ["城市生活方式", "汽车测评", "户外生活型"],
        "risk_notes": "避免把阶层表达做得过重。",
    },
]


ISSUE_PATTERNS = [
    {
        "triggers": ["ai", "大模型", "自动化", "效率", "工具"],
        "issue": "AI 工具爆发",
        "keywords": ["AI", "效率", "外部大脑", "自动化"],
        "core_emotion": "能力焦虑和确定性渴望并存",
        "symptom": "个人中介能力外包",
        "public_fantasy": "普通人也能拥有组织级生产力",
        "rupture_point": "替代焦虑和工具同质化会削弱信任",
        "opportunity": "把产品解释成外部大脑或组织放大器",
        "risk_direction": "不要制造失业恐惧，不要只讲技术参数",
        "suitable_brand_types": ["AI软件", "企业服务", "教育"],
        "suitable_creator_types": ["科技解释型", "职场教育型", "商业分析型"],
    },
    {
        "triggers": ["车", "汽车", "智驾", "suv", "通勤", "露营"],
        "issue": "城市出行与家庭安全",
        "keywords": ["通勤", "家庭", "智驾", "生活半径"],
        "core_emotion": "安全感、控制感和空间自由需求",
        "symptom": "城市中产用移动空间修复生活秩序",
        "public_fantasy": "一辆车带来更大的生活半径和家庭确定性",
        "rupture_point": "价格、智驾安全和伪高端表达容易被质疑",
        "opportunity": "从真实通勤和家庭场景切入",
        "risk_direction": "不要堆参数，不要夸大智驾能力",
        "suitable_brand_types": ["汽车", "户外", "家居"],
        "suitable_creator_types": ["汽车测评", "城市生活方式", "科技解释型"],
    },
    {
        "triggers": ["护肤", "美妆", "成分", "抗老", "香氛"],
        "issue": "稳定变美与自我照料",
        "keywords": ["成分", "抗老", "自我照料", "审美"],
        "core_emotion": "容貌焦虑后的专业可信需求",
        "symptom": "用科学和审美秩序管理不确定的身体感受",
        "public_fantasy": "通过正确消费获得可验证的稳定变好",
        "rupture_point": "智商税和功效夸大会触发反感",
        "opportunity": "用证据、边界和长期体验建立信任",
        "risk_direction": "不要过度刺激焦虑，不要承诺绝对功效",
        "suitable_brand_types": ["美妆护肤", "香氛", "健康"],
        "suitable_creator_types": ["成分测评", "真实种草", "审美生活型"],
    },
    {
        "triggers": ["消费降级", "不买", "省钱", "性价比", "中产"],
        "issue": "消费降级与反精致",
        "keywords": ["消费降级", "性价比", "反精致", "中产焦虑"],
        "core_emotion": "安全感缺失和身份叙事收缩",
        "symptom": "旧中产幻觉退潮，用户重新审视消费必要性",
        "public_fantasy": "既不被收割，又保留体面生活",
        "rupture_point": "高端叙事容易被质疑为脱离现实",
        "opportunity": "讲真实价值、长期成本和可验证体验",
        "risk_direction": "不要说教，不要用精英口吻压迫用户",
        "suitable_brand_types": ["家居", "汽车", "消费品", "AI软件"],
        "suitable_creator_types": ["真实测评型", "财经信任型", "生活方式型"],
    },
]


PRODUCT_ARCHETYPES = {
    "汽车": {
        "category": "汽车",
        "physical": ["交通工具", "智能座舱", "移动空间"],
        "scenarios": ["城市通勤", "家庭出行", "周末露营"],
        "users": ["城市家庭", "效率生活人群", "年轻中产"],
        "functional": ["出行效率", "安全辅助", "空间承载"],
        "emotion": ["安全感", "控制感", "生活半径扩大"],
        "identity": ["家庭责任", "城市自由", "科技生活"],
        "metaphors": ["移动城堡", "第二生活空间", "城市避难所"],
        "metonymies": ["车钥匙", "智能座舱", "后备箱", "露营装备"],
        "content": ["真实通勤测试", "家庭场景体验", "智能座舱解释"],
        "creators": ["汽车测评", "城市生活方式", "科技解释型"],
        "unsuitable": ["强冲突娱乐型", "低价促销型"],
        "risks": ["价格争议", "智驾安全误读", "参数堆砌"],
    },
    "AI软件": {
        "category": "AI软件",
        "physical": ["软件工具", "工作流", "自动化界面"],
        "scenarios": ["内容生产", "团队协作", "知识管理"],
        "users": ["职场人", "创业团队", "内容创作者"],
        "functional": ["提高效率", "降低执行成本", "辅助判断"],
        "emotion": ["确定性", "掌控感", "效率安全感"],
        "identity": ["高效个体", "小团队创业者", "技术尝鲜者"],
        "metaphors": ["外部大脑", "组织放大器", "第二生产力"],
        "metonymies": ["提示词", "工作流", "仪表盘", "自动化按钮"],
        "content": ["工作流拆解", "真实任务挑战", "小团队案例"],
        "creators": ["科技解释型", "职场教育型", "商业分析型"],
        "unsuitable": ["纯情绪吐槽型", "无场景种草型"],
        "risks": ["替代焦虑", "工具同质化", "隐私风险"],
    },
    "美妆护肤": {
        "category": "美妆护肤",
        "physical": ["成分", "肤感", "包装", "使用步骤"],
        "scenarios": ["日常护肤", "抗老管理", "敏感期修护"],
        "users": ["成分党", "精致生活人群", "抗老焦虑人群"],
        "functional": ["保湿修护", "稳定肤况", "抗老管理"],
        "emotion": ["安全感", "自我照料", "稳定变好"],
        "identity": ["精致女性", "专业消费", "审美秩序"],
        "metaphors": ["皮肤秩序", "时间管理", "成分护城河"],
        "metonymies": ["成分表", "实验室", "瓶身", "使用前后"],
        "content": ["成分解释", "长期使用记录", "真实肤质测评"],
        "creators": ["成分测评", "真实种草", "审美生活型"],
        "unsuitable": ["强冲突议题型", "低信任带货型"],
        "risks": ["智商税", "功效夸大", "容貌焦虑过度刺激"],
    },
}


def ensure_seed_signifier_tags(db_path: Path) -> list[SignifierTag]:
    existing = {tag.name: tag for tag in load_all_signifier_tags(db_path)}
    for item in SEED_TAGS:
        if item["name"] in existing:
            continue
        tag = SignifierTag(tag_id=tag_id_for(item["name"], item["tag_type"]), **item)
        upsert_signifier_tag(db_path, tag)
        existing[tag.name] = tag
    return list(existing.values())


def generate_social_symbolic_report(db_path: Path, payload: dict[str, Any]) -> SocialSymbolicReport:
    period = str(payload.get("period") or "当前周期").strip()
    raw = str(payload.get("raw_input") or payload.get("signals") or "").strip()
    text = raw.lower()
    issues = []
    for pattern in ISSUE_PATTERNS:
        if any(trigger.lower() in text for trigger in pattern["triggers"]):
            data = {key: value for key, value in pattern.items() if key != "triggers"}
            data["evidence"] = _evidence_snippets(raw, pattern["triggers"])
            issues.append(SocialSymbolicIssue(**data))
    if not issues:
        issues.append(
            SocialSymbolicIssue(
                issue="泛品牌信任压力",
                keywords=split_tags(raw)[:8] or ["信任", "真实感", "评论区"],
                core_emotion="用户对商业传播保持防御",
                symptom="商业内容需要更强证据链和更低理解成本",
                public_fantasy="希望品牌既专业又不压迫用户",
                rupture_point="口号化表达会被看作硬广",
                opportunity="用真实案例、具体场景和评论区回应建立信任",
                risk_direction="不要只讲热度和流量",
                suitable_brand_types=["全行业"],
                suitable_creator_types=["真实体验型", "专业解释型"],
                evidence=[raw[:160]] if raw else [],
            )
        )
    mood_map = list(dict.fromkeys(issue.core_emotion for issue in issues if issue.core_emotion))
    report = SocialSymbolicReport(
        report_id=report_id_for(period, raw),
        period=period,
        title=str(payload.get("title") or f"{period}社会符号网络报告"),
        raw_input=raw,
        overall_symptom="；".join(issue.symptom for issue in issues[:3]),
        mood_map=mood_map,
        issues=issues,
        borrowable_directions=list(dict.fromkeys(issue.opportunity for issue in issues)),
        high_risk_directions=list(dict.fromkeys(issue.risk_direction for issue in issues)),
        brand_implications=[
            f"{brand_type}可借势：{issue.opportunity}"
            for issue in issues
            for brand_type in issue.suitable_brand_types[:2]
        ][:8],
        confidence=0.72 if raw else 0.45,
    )
    upsert_social_report(db_path, report)
    ensure_seed_signifier_tags(db_path)
    return report


def symbolic_os_snapshot(db_path: Path) -> dict[str, Any]:
    tags = ensure_seed_signifier_tags(db_path)
    reports = load_all_social_reports(db_path)
    corrections = load_all_feedback_corrections(db_path)
    products = load_all_product_symbolic(db_path)
    narratives = load_all_content_narratives(db_path)
    matches = load_all_brand_creator_matches(db_path)
    latest = reports[0].to_dict() if reports else None
    return {
        "metrics": {
            "social_reports": len(reports),
            "signifier_tags": len(tags),
            "product_symbolic_profiles": len(products),
            "content_narrative_assets": len(narratives),
            "brand_creator_match_assets": len(matches),
            "feedback_corrections": len(corrections),
        },
        "latest_report": latest,
        "tags": [tag.to_dict() for tag in tags[:80]],
        "products": [item.to_dict() for item in products[:30]],
        "narratives": [item.to_dict() for item in narratives[:30]],
        "matches": [item.to_dict() for item in matches[:50]],
        "corrections": [item.to_dict() for item in corrections[:30]],
        "next_actions": _symbolic_next_actions(reports, tags, corrections),
    }


def create_brand_creator_match_assets(db_path: Path, payload: dict[str, Any]) -> list[BrandCreatorMatchAsset]:
    brand = payload.get("brand") if isinstance(payload.get("brand"), dict) else {}
    product = payload.get("product") if isinstance(payload.get("product"), dict) else {}
    results = payload.get("results") if isinstance(payload.get("results"), list) else []
    assets = []
    for item in results:
        if not isinstance(item, dict):
            continue
        brand_id = str(brand.get("brand_id") or item.get("brand_id") or "")
        product_id = str(product.get("product_id") or item.get("product_id") or "")
        creator_id = str(item.get("creator_id") or "")
        evidence_items = item.get("evidence") if isinstance(item.get("evidence"), list) else []
        asset = BrandCreatorMatchAsset(
            match_id=str(item.get("match_id") or match_id_for(brand_id, product_id, creator_id)),
            brand_id=brand_id,
            brand_name=str(brand.get("brand_name") or item.get("brand_name") or ""),
            product_id=product_id,
            product_name=str(product.get("product_name") or brand.get("product") or item.get("product_name") or ""),
            creator_id=creator_id,
            creator_name=str(item.get("creator_name") or ""),
            symbolic_score=int(item.get("symbolic_score") or 0),
            recommendation_level=str(item.get("recommendation_level") or ""),
            domain_fit=int(item.get("domain_fit") or 0),
            emotion_fit=int(item.get("emotion_fit") or 0),
            narrative_fit=int(item.get("narrative_fit") or 0),
            audience_fit=int(item.get("audience_fit") or 0),
            metaphor_fit=int(item.get("metaphor_fit") or 0),
            case_fit=int(item.get("case_fit") or 0),
            risk_control=int(item.get("risk_control") or 0),
            matched_brand_tags=_split_payload(item.get("matched_brand_tags")),
            metaphor_relation=str(item.get("metaphor_relation") or ""),
            metonymy_relation=str(item.get("metonymy_relation") or ""),
            emotion_relation=_match_emotion_relation(brand, item),
            audience_relation=_match_audience_relation(brand, item),
            case_basis=[str(evidence.get("quote") or evidence.get("claim") or evidence) for evidence in evidence_items[:4]],
            match_reason=str(item.get("match_reason") or ""),
            risk_points=_split_payload(item.get("risk_points")),
            suggested_content_direction=str(item.get("suggested_content_direction") or ""),
            suggested_priority=_priority_from_score(int(item.get("symbolic_score") or 0)),
            manual_status="needs_review" if item.get("needs_manual_review") else "pending_review",
            evidence=[str(evidence.get("source") or evidence.get("claim") or evidence) for evidence in evidence_items[:6]],
        )
        upsert_brand_creator_match(db_path, asset)
        assets.append(asset)
    return assets


def create_content_narrative_assets(db_path: Path, payload: dict[str, Any]) -> list[ContentNarrativeAsset]:
    brand = payload.get("brand") if isinstance(payload.get("brand"), dict) else {}
    product = payload.get("product") if isinstance(payload.get("product"), dict) else {}
    narratives = payload.get("narratives") if isinstance(payload.get("narratives"), list) else []
    assets = []
    for item in narratives:
        if not isinstance(item, dict):
            continue
        project = str(item.get("project") or payload.get("project") or f"{brand.get('brand_name') or '品牌'}传播路径")
        brand_id = str(brand.get("brand_id") or item.get("brand_id") or "")
        creator_id = str(item.get("creator_id") or "")
        target_tag = str(item.get("target_tag") or (brand.get("target_tags") or [""])[0] or "")
        asset = ContentNarrativeAsset(
            narrative_id=str(item.get("narrative_id") or narrative_id_for(project, brand_id, creator_id, target_tag)),
            project=project,
            brand_id=brand_id,
            brand_name=str(brand.get("brand_name") or item.get("brand_name") or ""),
            product_id=str(product.get("product_id") or item.get("product_id") or ""),
            product_name=str(product.get("product_name") or brand.get("product") or item.get("product_name") or ""),
            creator_id=creator_id,
            creator_name=str(item.get("creator_name") or ""),
            target_tag=target_tag,
            start_tag=str(item.get("start_tag") or ""),
            mediating_tags=_split_payload(item.get("mediating_tags")),
            narrative_path=str(item.get("narrative_path") or ""),
            metaphor_strategy=str(item.get("metaphor_strategy") or ""),
            metonymy_strategy=str(item.get("metonymy_strategy") or ""),
            emotion_strategy=str(item.get("emotion_strategy") or _emotion_strategy_from_brand(brand)),
            title_directions=_split_payload(item.get("title_directions")),
            content_brief=str(item.get("content_brief") or _content_brief_from_narrative(item)),
            suitable_creator_types=_split_payload(product.get("suitable_creator_types") or brand.get("suitable_creator_types")),
            must_include=_split_payload(item.get("must_include")),
            must_avoid=_split_payload(item.get("must_avoid")),
            comment_guidance=str(item.get("comment_guidance") or ""),
            risk_words=_split_payload(item.get("risk_words") or item.get("must_avoid") or brand.get("danger_tags")),
            client_status=str(item.get("client_status") or "draft"),
        )
        upsert_content_narrative(db_path, asset)
        assets.append(asset)
    return assets


def generate_product_symbolic_profile(db_path: Path, payload: dict[str, Any]) -> ProductSymbolicProfile:
    brand_name = str(payload.get("brand_name") or payload.get("brand") or "").strip()
    brand_id = str(payload.get("brand_id") or "").strip()
    product_name = str(payload.get("product_name") or payload.get("product") or "未命名产品").strip()
    category = str(payload.get("category") or payload.get("industry") or "").strip()
    raw = "\n".join(f"{key}: {value}" for key, value in payload.items() if value)
    reports = load_all_social_reports(db_path)
    report = reports[0] if reports else None
    tags = ensure_seed_signifier_tags(db_path)
    relevant_tags = _relevant_tags_for_product(product_name, category, raw, tags)
    relevant_issues = _relevant_issues_for_product(product_name, category, raw, report) if report else []
    archetype = _product_archetype(category or raw)
    profile = ProductSymbolicProfile(
        product_id=str(payload.get("product_id") or product_id_for(brand_name, product_name)),
        brand_id=brand_id,
        brand_name=brand_name,
        product_name=product_name,
        category=category or str(archetype["category"]),
        physical_attributes=_dedupe(_split_payload(payload.get("physical_attributes")) + list(archetype["physical"])),
        use_scenarios=_dedupe(_split_payload(payload.get("use_scenarios")) + list(archetype["scenarios"]) + [issue.issue for issue in relevant_issues[:2]]),
        target_users=_dedupe(_split_payload(payload.get("target_users")) + list(archetype["users"])),
        functional_value=_dedupe(_split_payload(payload.get("functional_value")) + list(archetype["functional"])),
        emotional_value=_dedupe(_split_payload(payload.get("emotional_value")) + list(archetype["emotion"]) + [tag.emotion for tag in relevant_tags[:3] if tag.emotion]),
        identity_value=_dedupe(_split_payload(payload.get("identity_value")) + list(archetype["identity"])),
        metaphors=_dedupe(_split_payload(payload.get("metaphors")) + list(archetype["metaphors"]) + [item for tag in relevant_tags for item in tag.metaphor_relations[:2]]),
        metonymies=_dedupe(_split_payload(payload.get("metonymies")) + list(archetype["metonymies"]) + [item for tag in relevant_tags for item in tag.metonymy_relations[:2]]),
        association_words=_dedupe(_split_payload(payload.get("association_words")) + [tag.name for tag in relevant_tags[:5]] + [keyword for issue in relevant_issues for keyword in issue.keywords[:2]]),
        anti_association_words=_dedupe(_split_payload(payload.get("anti_association_words")) + [tag.name for tag in relevant_tags if tag.tag_type == "风险标签"] + [issue.rupture_point for issue in relevant_issues if issue.rupture_point]),
        suitable_content_scenarios=_dedupe(_split_payload(payload.get("suitable_content_scenarios")) + list(archetype["content"]) + [issue.opportunity for issue in relevant_issues if issue.opportunity]),
        suitable_creator_types=_dedupe(_split_payload(payload.get("suitable_creator_types")) + list(archetype["creators"]) + [creator for issue in relevant_issues for creator in issue.suitable_creator_types] + [creator for tag in relevant_tags for creator in tag.suitable_creator_types]),
        unsuitable_creator_types=_dedupe(_split_payload(payload.get("unsuitable_creator_types")) + list(archetype["unsuitable"])),
        social_issue_hooks=_dedupe([issue.issue for issue in relevant_issues]),
        risk_notes=_dedupe(_split_payload(payload.get("risk_notes")) + list(archetype["risks"]) + [issue.risk_direction for issue in relevant_issues if issue.risk_direction]),
        evidence=[raw[:220] or "基于产品名称、品类和符号标签库生成。"],
        confidence=0.76 if raw else 0.55,
    )
    upsert_product_symbolic(db_path, profile)
    return profile


def calibrate_brand_with_symbolic_context(
    db_path: Path,
    brand: BrandSymbolicProfile,
    report_id: str = "",
) -> tuple[BrandSymbolicProfile, dict[str, Any]]:
    reports = load_all_social_reports(db_path)
    report = next((item for item in reports if item.report_id == report_id), None) if report_id else (reports[0] if reports else None)
    tags = ensure_seed_signifier_tags(db_path)
    if report is None:
        return brand, {
            "applied": False,
            "reason": "missing_social_report",
            "message": "尚未生成社会符号网络报告，品牌档案未校准。",
        }

    relevant_issues = _relevant_issues_for_brand(brand, report)
    relevant_tags = _relevant_tags_for_brand(brand, tags)
    if not relevant_issues:
        relevant_issues = report.issues[:2]
    data = brand.to_dict()
    data["target_tags"] = _dedupe(
        data.get("target_tags", [])
        + [tag.name for tag in relevant_tags[:4] if tag.tag_type != "风险标签"]
        + [keyword for issue in relevant_issues for keyword in issue.keywords[:2]]
    )[:12]
    data["danger_tags"] = _dedupe(
        data.get("danger_tags", [])
        + [tag.name for tag in relevant_tags if tag.tag_type == "风险标签"]
        + [issue.rupture_point for issue in relevant_issues if issue.rupture_point]
    )[:12]
    data["emotional_value"] = _dedupe(
        data.get("emotional_value", []) + [issue.core_emotion for issue in relevant_issues if issue.core_emotion] + [tag.emotion for tag in relevant_tags[:4] if tag.emotion]
    )[:12]
    data["suitable_social_issues"] = _dedupe(data.get("suitable_social_issues", []) + [issue.issue for issue in relevant_issues])[:12]
    data["unsafe_social_issues"] = _dedupe(data.get("unsafe_social_issues", []) + [issue.risk_direction for issue in relevant_issues if issue.risk_direction])[:12]
    data["suitable_creator_types"] = _dedupe(
        data.get("suitable_creator_types", []) + [creator_type for issue in relevant_issues for creator_type in issue.suitable_creator_types] + [creator_type for tag in relevant_tags for creator_type in tag.suitable_creator_types]
    )[:12]
    data["communication_path"] = _calibrated_communication_path(brand, report, relevant_issues)
    data["confidence"] = min(0.95, max(float(data.get("confidence") or 0.55), float(report.confidence or 0.45)) + 0.04)
    evidence = data.get("evidence") or []
    evidence.append(
        asdict(
            Evidence(
                claim="社会符号网络校准",
                source=report.title,
                quote="；".join([issue.opportunity for issue in relevant_issues[:3] if issue.opportunity])[:220],
            )
        )
    )
    data["evidence"] = evidence
    calibrated = BrandSymbolicProfile.from_json(json.dumps(data, ensure_ascii=False))
    return calibrated, {
        "applied": True,
        "report": report.to_dict(),
        "relevant_issues": [issue.to_dict() for issue in relevant_issues],
        "relevant_tags": [tag.to_dict() for tag in relevant_tags[:8]],
        "added_target_tags": [tag for tag in calibrated.target_tags if tag not in brand.target_tags],
        "added_danger_tags": [tag for tag in calibrated.danger_tags if tag not in brand.danger_tags],
        "message": f"已用《{report.title}》校准 {brand.brand_name} 的社会议题、风险和博主类型。",
    }


def create_feedback_correction(
    db_path: Path,
    project: CampaignProject,
    review: PostCampaignReview,
) -> FeedbackCorrection:
    creator = load_profile(db_path, review.creator_id)
    creator_symbolic = load_creator_symbolic(db_path, review.creator_id)
    if creator and creator_symbolic is None:
        creator_symbolic = generate_creator_symbolic_profile(creator)
    assumed = _assumed_tags(project, creator, creator_symbolic)
    feedback_text = " ".join([review.brand_feedback, review.comment_feedback])
    activated = _extract_activated_tags(feedback_text, project)
    missing = [tag for tag in assumed[:8] if tag not in activated]
    misreads = _extract_misreads(feedback_text)
    delivery = review.delivery_rating or 0
    confidence_delta = 0.08 if delivery >= 4 and not misreads else (-0.08 if delivery and delivery <= 2.5 else 0.0)
    creator_updates = list(dict.fromkeys(activated + ([f"风险:{point}" for point in misreads[:2]])))[:8]
    brand_updates = [f"继续强化:{tag}" for tag in activated[:3]] + [f"下次规避:{point}" for point in misreads[:2]]
    correction = FeedbackCorrection(
        correction_id=correction_id_for(project.campaign.campaign_id, review.creator_id, review.review_id),
        campaign_id=project.campaign.campaign_id,
        creator_id=review.creator_id,
        review_id=review.review_id,
        assumed_tags=assumed[:12],
        activated_tags=activated[:8],
        missing_tags=missing[:8],
        misread_points=misreads[:6],
        creator_tag_updates=creator_updates,
        brand_tag_updates=brand_updates[:8],
        next_suggestion=_next_suggestion(activated, missing, misreads),
        confidence_delta=confidence_delta,
        evidence_summary=f"曝光{review.views}，互动{review.likes + review.comments}；{feedback_text[:180]}",
    )
    upsert_feedback_correction(db_path, correction)
    if creator_symbolic:
        _apply_correction_to_creator_symbolic(db_path, creator_symbolic, correction)
    return correction


def _apply_correction_to_creator_symbolic(db_path: Path, profile: Any, correction: FeedbackCorrection) -> None:
    data = profile.to_dict()
    positives = [tag for tag in correction.activated_tags if not tag.startswith("风险:")]
    risks = [tag.replace("风险:", "") for tag in correction.creator_tag_updates if tag.startswith("风险:")]
    data["secondary_tags"] = list(dict.fromkeys((data.get("secondary_tags") or []) + positives))[:12]
    data["risk_tags"] = list(dict.fromkeys((data.get("risk_tags") or []) + risks + correction.misread_points))[:10]
    data["comment_sample"] = "\n".join(filter(None, [data.get("comment_sample", ""), correction.evidence_summary])).strip()[-1200:]
    data["confidence"] = min(0.95, max(0.2, float(data.get("confidence") or 0.55) + correction.confidence_delta))
    data["manual_status"] = "post_review_adjusted"
    upsert_creator_symbolic(db_path, type(profile).from_json(__import__("json").dumps(data, ensure_ascii=False)))


def _assumed_tags(project: CampaignProject, creator: CreatorProfile | None, symbolic: Any | None) -> list[str]:
    tags: list[str] = []
    tags.extend(project.campaign.goals)
    tags.extend(project.campaign.content_preferences)
    tags.extend(project.campaign.target_audience)
    if creator:
        tags.extend(creator.industry_fit_tags + creator.content_capability_tags + creator.suitable_goals)
    if symbolic:
        tags.extend(symbolic.primary_tags + symbolic.secondary_tags)
    return list(dict.fromkeys(tag for tag in tags if tag))


def _extract_activated_tags(text: str, project: CampaignProject) -> list[str]:
    source = text or ""
    candidates = list(
        dict.fromkeys(
            project.campaign.goals
            + project.campaign.content_preferences
            + project.campaign.target_audience
            + ["真实感", "专业可信", "安全感", "城市自由", "种草", "解释清楚", "评论区互动"]
        )
    )
    hits = [tag for tag in candidates if tag and tag in source]
    if "好评" in source or "喜欢" in source or "认可" in source:
        hits.append("正向信任")
    if "真实" in source:
        hits.append("真实感")
    if "专业" in source:
        hits.append("专业可信")
    return list(dict.fromkeys(hits)) or candidates[:3]


def _extract_misreads(text: str) -> list[str]:
    risks = []
    mapping = {
        "硬广": "硬广感过强",
        "贵": "价格争议",
        "价格": "价格争议",
        "夸大": "功效或卖点夸大",
        "不信": "信任不足",
        "争议": "评论区争议",
        "翻车": "品牌安全风险",
    }
    for token, risk in mapping.items():
        if token in text:
            risks.append(risk)
    return list(dict.fromkeys(risks))


def _next_suggestion(activated: list[str], missing: list[str], misreads: list[str]) -> str:
    if misreads:
        return f"下一轮先处理{misreads[0]}，在 brief 中加入边界说明和评论区 FAQ。"
    if missing:
        return f"下一轮强化{missing[0]}，让博主用更具体的场景承接该标签。"
    if activated:
        return f"该博主可继续用于{activated[0]}方向，建议沉淀为可复用案例。"
    return "补充评论样本和客户反馈后再修正标签。"


def _evidence_snippets(raw: str, triggers: list[str]) -> list[str]:
    if not raw:
        return []
    snippets = []
    for line in raw.splitlines():
        if any(trigger.lower() in line.lower() for trigger in triggers):
            snippets.append(line.strip()[:160])
    return snippets[:3] or [raw[:160]]


def _symbolic_next_actions(reports: list[Any], tags: list[Any], corrections: list[Any]) -> list[str]:
    actions = []
    if not reports:
        actions.append("输入本周舆情、客户背景或行业观察，生成第一份社会符号网络报告。")
    if len(tags) < 20:
        actions.append("继续补充你们内部常用传播标签，建立上下级、相反和隐喻/转喻关系。")
    if not corrections:
        actions.append("录入真实投后反馈，让系统开始修正博主符号档案。")
    if not actions:
        actions.append("用最新社会符号报告校准 Campaign brief，再观察投后修正是否符合人工判断。")
    return actions


def _relevant_issues_for_brand(brand: BrandSymbolicProfile, report: SocialSymbolicReport) -> list[SocialSymbolicIssue]:
    haystack = " ".join([brand.industry, brand.product, brand.brand_name] + brand.current_tags + brand.target_tags + brand.suitable_creator_types)
    relevant = []
    for issue in report.issues:
        issue_text = " ".join([issue.issue] + issue.keywords + issue.suitable_brand_types + issue.suitable_creator_types)
        if any(token and token in issue_text for token in [brand.industry, brand.product, brand.brand_name]):
            relevant.append(issue)
            continue
        if any(keyword and keyword in haystack for keyword in issue.keywords + issue.suitable_brand_types):
            relevant.append(issue)
    return relevant[:4]


def _relevant_issues_for_product(product_name: str, category: str, raw: str, report: SocialSymbolicReport | None) -> list[SocialSymbolicIssue]:
    if report is None:
        return []
    haystack = " ".join([product_name, category, raw])
    relevant = []
    for issue in report.issues:
        issue_text = " ".join([issue.issue] + issue.keywords + issue.suitable_brand_types + issue.suitable_creator_types)
        if any(token and token in issue_text for token in [product_name, category]):
            relevant.append(issue)
            continue
        if any(keyword and keyword in haystack for keyword in issue.keywords + issue.suitable_brand_types):
            relevant.append(issue)
    return relevant[:4]


def _relevant_tags_for_brand(brand: BrandSymbolicProfile, tags: list[SignifierTag]) -> list[SignifierTag]:
    haystack = " ".join(
        [
            brand.industry,
            brand.product,
            brand.brand_name,
            brand.communication_path,
            *brand.current_tags,
            *brand.target_tags,
            *brand.emotional_value,
            *brand.identity_value,
            *brand.suitable_creator_types,
        ]
    )
    relevant = []
    for tag in tags:
        tag_text = " ".join(
            [
                tag.name,
                tag.tag_type,
                tag.emotion,
                *tag.related_tags,
                *tag.suitable_industries,
                *tag.suitable_creator_types,
            ]
        )
        if any(item and item in haystack for item in [tag.name] + tag.related_tags + tag.suitable_industries):
            relevant.append(tag)
            continue
        if brand.industry and brand.industry in tag_text:
            relevant.append(tag)
    return relevant[:10]


def _relevant_tags_for_product(product_name: str, category: str, raw: str, tags: list[SignifierTag]) -> list[SignifierTag]:
    haystack = " ".join([product_name, category, raw])
    relevant = []
    for tag in tags:
        tag_text = " ".join([tag.name, tag.tag_type, tag.emotion, *tag.related_tags, *tag.suitable_industries, *tag.suitable_creator_types])
        if any(item and item in haystack for item in [tag.name] + tag.related_tags + tag.suitable_industries):
            relevant.append(tag)
            continue
        if category and category in tag_text:
            relevant.append(tag)
    return relevant[:10]


def _product_archetype(text: str) -> dict[str, list[str] | str]:
    lowered = text.lower()
    if any(token in lowered for token in ["车", "汽车", "suv", "智驾", "座舱"]):
        return PRODUCT_ARCHETYPES["汽车"]
    if any(token.lower() in lowered for token in ["ai", "软件", "效率", "工具", "大模型"]):
        return PRODUCT_ARCHETYPES["AI软件"]
    if any(token in lowered for token in ["护肤", "美妆", "成分", "抗老"]):
        return PRODUCT_ARCHETYPES["美妆护肤"]
    return PRODUCT_ARCHETYPES["AI软件"]


def _split_payload(value: Any) -> list[str]:
    return split_tags(value)


def _emotion_strategy_from_brand(brand: dict[str, Any]) -> str:
    values = brand.get("emotional_value") or []
    if values:
        return f"优先激活{'、'.join(map(str, values[:3]))}，把产品卖点转译成用户可感知情绪。"
    return "用真实场景降低硬广感，把卖点转成用户可复述的体验语言。"


def _match_emotion_relation(brand: dict[str, Any], item: dict[str, Any]) -> str:
    tags = item.get("matched_brand_tags") or []
    emotions = brand.get("emotional_value") or []
    if emotions and tags:
        return f"用{'、'.join(map(str, tags[:2]))}承接{'、'.join(map(str, emotions[:2]))}。"
    if emotions:
        return f"重点承接品牌情绪：{'、'.join(map(str, emotions[:3]))}。"
    return "需要结合内容样本继续判断情绪承接方式。"


def _match_audience_relation(brand: dict[str, Any], item: dict[str, Any]) -> str:
    identities = brand.get("identity_value") or []
    if identities:
        return f"适合向{'、'.join(map(str, identities[:3]))}人群解释品牌位置。"
    return "需要补充目标用户和受众幻想样本。"


def _priority_from_score(score: int) -> str:
    if score >= 85:
        return "priority_a"
    if score >= 70:
        return "priority_b"
    if score >= 55:
        return "backup"
    return "watchlist"


def _content_brief_from_narrative(item: dict[str, Any]) -> str:
    path = str(item.get("narrative_path") or "")
    include = "、".join(_split_payload(item.get("must_include")))
    avoid = "、".join(_split_payload(item.get("must_avoid")))
    parts = [path]
    if include:
        parts.append(f"必须包含：{include}")
    if avoid:
        parts.append(f"避免：{avoid}")
    return "；".join(part for part in parts if part)


def _calibrated_communication_path(
    brand: BrandSymbolicProfile,
    report: SocialSymbolicReport,
    issues: list[SocialSymbolicIssue],
) -> str:
    base = brand.communication_path.strip()
    if not issues:
        return base
    issue = issues[0]
    calibrated = (
        f"社会校准：基于{report.period}的{issue.issue}，先从{issue.core_emotion or '用户真实情绪'}切入，"
        f"借势{issue.opportunity or '可验证体验'}，同时避开{issue.risk_direction or '硬广误读'}。"
    )
    if base and calibrated not in base:
        return f"{base}\n{calibrated}"
    return base or calibrated


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(str(item).strip() for item in items if str(item).strip()))
