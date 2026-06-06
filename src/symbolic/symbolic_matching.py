from __future__ import annotations

from src.symbolic.schemas import BrandSymbolicProfile, CreatorSymbolicProfile, Evidence, SymbolicMatchResult


def level(score: int) -> str:
    if score >= 85:
        return "强推荐"
    if score >= 70:
        return "推荐"
    if score >= 55:
        return "备选"
    if score >= 40:
        return "谨慎使用"
    return "不推荐"


def symbolic_overlap(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    text_b = " ".join(b)
    hits = 0
    for item in a:
        if item in text_b or any(part in text_b for part in item.split()):
            hits += 1
    return hits


def score_1_to_5(hits: int, baseline: int = 1) -> int:
    return min(5, max(baseline, baseline + hits))


def match_symbolic_creator(brand: BrandSymbolicProfile, creator: CreatorSymbolicProfile) -> SymbolicMatchResult:
    domain_hits = symbolic_overlap(brand.suitable_creator_types + [brand.industry], creator.suitable_brand_types + creator.primary_tags)
    emotion_hits = symbolic_overlap(brand.emotional_value, [creator.emotional_tone, creator.audience_fantasy] + creator.secondary_tags)
    narrative_hits = symbolic_overlap(brand.target_tags, creator.primary_tags + creator.secondary_tags + [creator.narrative_style])
    audience_hits = symbolic_overlap(brand.identity_value, [creator.audience_fantasy, creator.persona_structure] + creator.secondary_tags)
    metaphor_hits = symbolic_overlap(brand.product_metaphors + brand.product_metonymies, creator.common_metaphors + creator.common_metonymies)
    case_hits = symbolic_overlap(brand.current_tags + brand.target_tags + [brand.industry], creator.evidence[0].quote.split("、") if creator.evidence else [])
    risk_conflicts = symbolic_overlap(brand.danger_tags + brand.unsafe_social_issues, creator.risk_tags)

    domain_fit = score_1_to_5(domain_hits, 2)
    emotion_fit = score_1_to_5(emotion_hits, 2)
    narrative_fit = score_1_to_5(narrative_hits, 2)
    audience_fit = score_1_to_5(audience_hits, 2)
    metaphor_fit = score_1_to_5(metaphor_hits, 2)
    case_fit = score_1_to_5(case_hits, 2 if creator.evidence else 1)
    risk_control = max(1, 5 - risk_conflicts)
    confidence_fit = 5 if creator.confidence >= 0.8 else (4 if creator.confidence >= 0.65 else 2)
    score = int(
        domain_fit * 3
        + emotion_fit * 3
        + narrative_fit * 3
        + audience_fit * 3
        + metaphor_fit * 3
        + case_fit * 2
        + risk_control * 2
        + confidence_fit
    )
    score = min(100, int(score / 95 * 100))

    matched_tags = _matched_tags(brand, creator)
    metaphor_relation = _relation(brand.product_metaphors, creator.common_metaphors, "可通过共享隐喻承接品牌叙事")
    metonymy_relation = _relation(brand.product_metonymies, creator.common_metonymies, "可通过局部物件和场景完成转喻连接")
    match_reason = (
        f"{creator.creator_name} 的{creator.persona_structure or '内容结构'}和"
        f"{creator.narrative_style or '叙事方式'}，可以承接 {brand.brand_name} "
        f"{'、'.join(matched_tags[:3]) or '目标标签'} 的传播需求。"
    )
    risk_points = list(dict.fromkeys(creator.risk_tags + [f"需避开：{tag}" for tag in brand.danger_tags[:2]]))[:6]
    evidence = creator.evidence[:2] + brand.evidence[:1]
    return SymbolicMatchResult(
        creator_id=creator.creator_id,
        creator_name=creator.creator_name,
        symbolic_score=score,
        recommendation_level=level(score),
        domain_fit=domain_fit,
        emotion_fit=emotion_fit,
        narrative_fit=narrative_fit,
        audience_fit=audience_fit,
        metaphor_fit=metaphor_fit,
        case_fit=case_fit,
        risk_control=risk_control,
        matched_brand_tags=matched_tags,
        metaphor_relation=metaphor_relation,
        metonymy_relation=metonymy_relation,
        match_reason=match_reason,
        risk_points=risk_points,
        suggested_content_direction=_suggest_content(brand, creator),
        evidence=evidence,
        needs_manual_review=creator.confidence < 0.65 or risk_control <= 2,
    )


def rank_symbolic_creators(
    brand: BrandSymbolicProfile,
    creators: list[CreatorSymbolicProfile],
) -> list[SymbolicMatchResult]:
    return sorted([match_symbolic_creator(brand, creator) for creator in creators], key=lambda item: item.symbolic_score, reverse=True)


def _matched_tags(brand: BrandSymbolicProfile, creator: CreatorSymbolicProfile) -> list[str]:
    tags: list[str] = []
    creator_text = " ".join(creator.primary_tags + creator.secondary_tags + creator.suitable_brand_types + [creator.emotional_tone, creator.audience_fantasy])
    for tag in brand.target_tags + brand.current_tags + brand.emotional_value:
        if any(part and part in creator_text for part in tag.split()):
            tags.append(tag)
    return tags or brand.target_tags[:3]


def _relation(a: list[str], b: list[str], fallback: str) -> str:
    shared = [item for item in a if item in b]
    if shared:
        return f"共享符号：{'、'.join(shared[:3])}"
    if a and b:
        return f"{a[0]} 可转译为 {b[0]}，形成叙事连接。"
    return fallback


def _suggest_content(brand: BrandSymbolicProfile, creator: CreatorSymbolicProfile) -> str:
    start = brand.suitable_social_issues[0] if brand.suitable_social_issues else "用户真实场景"
    target = brand.target_tags[0] if brand.target_tags else "品牌目标标签"
    style = creator.narrative_style or "真实体验"
    return f"从{start}切入，用{style}承接，最终导向{target}。"
