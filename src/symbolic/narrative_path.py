from __future__ import annotations

from src.symbolic.schemas import BrandSymbolicProfile, CreatorSymbolicProfile, NarrativePath


def generate_narrative_path(
    brand: BrandSymbolicProfile,
    creator: CreatorSymbolicProfile,
    project_name: str = "",
) -> NarrativePath:
    start = brand.suitable_social_issues[0] if brand.suitable_social_issues else brand.current_tags[0]
    mediating = list(dict.fromkeys((brand.product_metonymies[:2] + creator.common_metonymies[:2] + brand.emotional_value[:1])))[:4]
    target = brand.target_tags[0] if brand.target_tags else "品牌目标标签"
    metaphor = brand.product_metaphors[0] if brand.product_metaphors else (creator.common_metaphors[0] if creator.common_metaphors else "产品作为生活工具")
    metonymy = "、".join(mediating) if mediating else "具体使用场景"
    project = project_name or f"{brand.brand_name}{brand.product}传播"
    narrative = f"从{start}切入，经由{'、'.join(mediating) or '真实使用细节'}，转向{target}。"
    return NarrativePath(
        project=project,
        creator_id=creator.creator_id,
        creator_name=creator.creator_name,
        start_tag=start,
        mediating_tags=mediating,
        target_tag=target,
        narrative_path=narrative,
        metaphor_strategy=f"{brand.product or brand.brand_name}被表达为{metaphor}",
        metonymy_strategy=f"用{metonymy}等局部物件和场景完成转喻连接",
        title_directions=[
            f"{start}之后，我重新理解了{brand.product or brand.brand_name}",
            f"一个真实场景，如何把{target}讲清楚",
        ],
        must_include=list(dict.fromkeys(brand.emotional_value[:2] + brand.product_metonymies[:2])),
        must_avoid=brand.danger_tags[:4],
        comment_guidance=f"引导用户讨论{start}、{target}和真实体验，避免把讨论导向{'、'.join(brand.danger_tags[:2]) or '单纯价格'}。",
    )
