from __future__ import annotations

from src.schemas import BrandBrief, CreatorProfile, MatchResult


def _overlap_score(a: list[str], b: list[str], full: int) -> tuple[int, list[str]]:
    if not a or not b:
        return 0, []
    hits = [item for item in a if any(item in target or target in item for target in b)]
    if not hits:
        return 0, []
    return min(full, int(full * len(hits) / max(len(a), 1))), hits


def _level(score: int) -> str:
    if score >= 85:
        return "强推荐"
    if score >= 70:
        return "推荐"
    if score >= 55:
        return "备选"
    if score >= 40:
        return "谨慎使用"
    return "不推荐"


def _price_judgement(brief: BrandBrief, creator: CreatorProfile, suggested_budget: int) -> str:
    if not creator.listed_price:
        return "数据不足，需人工核验"
    if suggested_budget and creator.listed_price > suggested_budget * 1.35:
        return "偏高"
    if suggested_budget and creator.listed_price < suggested_budget * 0.65:
        return "明显偏低"
    if creator.follower_count and creator.listed_price / max(creator.follower_count, 1) > 0.2:
        return "略高"
    return "合理"


def _data_confidence(creator: CreatorProfile) -> str:
    score = 0
    if creator.follower_count:
        score += 1
    if creator.listed_price:
        score += 1
    if creator.cooperation_brands:
        score += 1
    if any(source.startswith("excel") or source == "manual" for source in creator.data_sources):
        score += 1
    if creator.ai_summary:
        score += 1
    return "高" if score >= 4 else ("中" if score >= 2 else "低")


def _recommended_role(creator: CreatorProfile) -> str:
    caps = creator.content_capability_tags
    if "测评" in caps or "专业科普" in caps:
        return "专业背书 / 用户教育"
    if "创意TVC" in caps:
        return "视觉破圈 / 声量扩散"
    if "种草" in caps:
        return "种草转化 / 搜索沉淀"
    return "曝光扩散"


def rank_creator(brief: BrandBrief, creator: CreatorProfile) -> MatchResult:
    score = 0
    reasons: list[str] = []

    industry_score, industry_hits = _overlap_score([brief.industry] if brief.industry else [], creator.industry_fit_tags, 20)
    score += industry_score
    if industry_hits:
        reasons.append(f"行业标签匹配：{ '、'.join(industry_hits) }")
    elif brief.industry:
        score -= 15

    content_score, content_hits = _overlap_score(brief.content_preference, creator.content_capability_tags + creator.ai_summary.split("、"), 15)
    if not content_score and creator.content_capability_tags:
        content_score = 6
    score += content_score
    if creator.content_capability_tags:
        reasons.append(f"内容能力：{ '、'.join(creator.content_capability_tags[:3]) }")

    stage_score, stage_hits = _overlap_score([brief.campaign_stage] + brief.goals, creator.suitable_stages + creator.suitable_goals, 15)
    score += stage_score
    if stage_hits:
        reasons.append(f"传播目标匹配：{ '、'.join(stage_hits[:3]) }")

    audience_score = 0
    text = " ".join([creator.bio, creator.manual_notes, creator.ai_summary] + creator.industry_fit_tags)
    for audience in brief.target_audience:
        if audience.replace("人群", "") in text or ("男性" in audience and "汽车" in text) or ("女性" in audience and "美妆" in text):
            audience_score += 5
    audience_score = min(15, audience_score)
    score += audience_score

    case_score = 10 if creator.cooperation_brands else 3
    score += case_score
    if creator.cooperation_brands:
        reasons.append(f"有历史合作背书：{ '、'.join(creator.cooperation_brands[:3]) }")

    if brief.budget:
        suggested_budget = min(max(int(brief.budget * 0.08), 3000), creator.listed_price or int(brief.budget * 0.12))
    else:
        suggested_budget = creator.listed_price or 10_000
    price_judgement = _price_judgement(brief, creator, suggested_budget)
    price_score = {"合理": 10, "明显偏低": 8, "略高": 6, "数据不足，需人工核验": 4, "偏高": 2}.get(price_judgement, 3)
    score += price_score

    risk_penalty = min(10, len(creator.risk_tags) * 2)
    risk_score = max(0, 10 - risk_penalty)
    score += risk_score

    confidence = _data_confidence(creator)
    score += {"高": 5, "中": 3, "低": 1}[confidence]
    score = max(0, min(100, score))

    if not reasons:
        reasons.append("基础数据可用，但需要补充更多案例和平台数据。")
    if creator.platform in brief.platform_preference:
        score = min(100, score + 5)
        reasons.append(f"符合平台偏好：{creator.platform}")
    if brief.industry and not industry_hits:
        reasons.append(f"行业不完全匹配，需确认是否适合{brief.industry}项目。")

    return MatchResult(
        creator=creator,
        match_score=int(score),
        recommendation_level=_level(int(score)),
        recommended_role=_recommended_role(creator),
        suggested_content=f"建议采用{ '、'.join(creator.content_capability_tags[:2]) }内容，围绕{brief.product or brief.industry or '产品'}做场景化表达。",
        suggested_budget=suggested_budget,
        price_judgement=price_judgement,
        reasons=reasons[:5],
        risk_points=creator.risk_tags[:5] or ["暂无明显风险，仍建议人工复核评论区和历史履约。"],
        data_confidence=confidence,
        needs_manual_review=confidence == "低" or "需人工核验" in " ".join(creator.risk_tags),
    )


def rank_creators(brief: BrandBrief, creators: list[CreatorProfile]) -> list[MatchResult]:
    rankings = [rank_creator(brief, creator) for creator in creators]
    return sorted(rankings, key=lambda item: item.match_score, reverse=True)
