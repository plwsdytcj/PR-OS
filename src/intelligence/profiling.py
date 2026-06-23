from __future__ import annotations

from src.schemas import CreatorProfile, split_tags


def compute_like_fan_ratio(follower_count: int, total_likes: int) -> float:
    followers = int(follower_count or 0)
    likes = int(total_likes or 0)
    if followers <= 0 or likes <= 0:
        return 0.0
    return round(likes / followers, 4)


INDUSTRY_KEYWORDS = {
    "汽车": ["汽车", "新能源", "试驾", "智能座舱", "懂车", "车主", "SUV", "蔚来", "小鹏", "理想", "特斯拉", "极氪", "问界"],
    "3C数码": ["数码", "手机", "电脑", "智能硬件", "耳机", "相机", "科技"],
    "AI软件": ["AI", "AIGC", "软件", "效率", "工具", "自动化", "大模型"],
    "美妆护肤": ["美妆", "护肤", "成分", "抗老", "精华", "彩妆"],
    "母婴亲子": ["母婴", "亲子", "育儿", "宝宝", "儿童"],
    "食品饮料": ["食品", "饮料", "咖啡", "零食", "餐饮"],
    "家居家电": ["家居", "家电", "装修", "收纳", "清洁"],
    "职场教育": ["职场", "教育", "学习", "求职", "管理", "商业"],
    "文旅出行": ["旅行", "酒店", "文旅", "探店", "城市", "出行"],
    "生活方式": ["生活方式", "穿搭", "日常", "家庭", "城市", "消费"],
}

CAPABILITY_KEYWORDS = {
    "测评": ["测评", "横评", "试用", "体验", "开箱"],
    "种草": ["种草", "推荐", "好物", "分享"],
    "口播解释": ["口播", "解释", "科普", "拆解", "观点"],
    "剧情植入": ["剧情", "短剧", "段子", "植入"],
    "创意TVC": ["TVC", "大片", "创意", "视觉"],
    "专业科普": ["专业", "科普", "知识", "原理", "分析"],
    "探店": ["探店", "到店", "门店"],
    "直播带货": ["直播", "带货", "团购"],
    "场景体验": ["场景", "通勤", "家庭", "真实体验"],
}


def _text(profile: CreatorProfile) -> str:
    parts = [
        profile.name,
        profile.platform,
        profile.bio,
        profile.manual_notes,
        " ".join(profile.cooperation_brands),
        " ".join(profile.cooperation_formats),
    ]
    return " ".join(parts)


def _tags_from_keywords(text: str, mapping: dict[str, list[str]]) -> list[str]:
    tags = []
    lowered = text.lower()
    for tag, keywords in mapping.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            tags.append(tag)
    return tags


def _budget_tags(profile: CreatorProfile) -> list[str]:
    price = profile.listed_price
    followers = profile.follower_count
    tags: list[str] = []
    if price and price <= 10_000:
        tags.append("小预算测试")
    if 10_000 < price <= 60_000 or 100_000 <= followers <= 1_000_000:
        tags.append("中预算扩散")
    if price > 60_000 or followers > 1_000_000:
        tags.append("大预算品牌战役")
    if followers > 1_000_000:
        tags.append("头部背书")
    elif followers >= 100_000:
        tags.append("腰部扩散")
    else:
        tags.append("KOC铺量")
    if price and followers and price / max(followers, 1) < 0.08:
        tags.append("高性价比投放")
    return sorted(set(tags))


def _risk_tags(profile: CreatorProfile) -> list[str]:
    tags = set(profile.risk_tags)
    if not profile.listed_price:
        tags.add("报价数据缺失，需人工核验")
    if not profile.follower_count:
        tags.add("粉丝数据缺失，需人工核验")
    if profile.listed_price and profile.follower_count and profile.listed_price / max(profile.follower_count, 1) > 0.2:
        tags.add("报价偏高风险")
    if "广告" in profile.manual_notes or "硬广" in profile.manual_notes:
        tags.add("广告密度待核验")
    if not profile.cooperation_brands:
        tags.add("案例背书不足")
    return sorted(tags)


def enrich_profile(profile: CreatorProfile) -> CreatorProfile:
    text = _text(profile)
    industries = sorted(set(profile.industry_fit_tags + _tags_from_keywords(text, INDUSTRY_KEYWORDS)))
    capabilities = sorted(set(profile.content_capability_tags + _tags_from_keywords(text, CAPABILITY_KEYWORDS)))
    if not industries:
        industries = ["生活方式"]
    if not capabilities:
        capabilities = ["种草"] if profile.platform == "小红书" else ["口播解释"]
    goals = set(profile.suitable_goals)
    if "测评" in capabilities or "专业科普" in capabilities:
        goals.update(["品牌背书", "用户教育"])
    if "种草" in capabilities or profile.platform == "小红书":
        goals.update(["种草", "搜索沉淀"])
    if "创意TVC" in capabilities:
        goals.update(["曝光", "公关破圈", "新品预热"])
    if not goals:
        goals.update(["曝光", "新品预热"])
    stages = set(profile.suitable_stages)
    if "测评" in capabilities or "场景体验" in capabilities:
        stages.update(["内测", "预热", "种草"])
    if "直播带货" in capabilities:
        stages.add("转化")
    if not stages:
        stages.update(["预热", "种草"])
    profile.industry_fit_tags = industries
    profile.content_capability_tags = capabilities
    profile.suitable_goals = sorted(goals)
    profile.suitable_stages = sorted(stages)
    profile.budget_fit_tags = _budget_tags(profile)
    profile.risk_tags = _risk_tags(profile)
    profile.like_fan_ratio = compute_like_fan_ratio(profile.follower_count, profile.total_likes)
    profile.ai_summary = (
        f"适合{ '、'.join(profile.industry_fit_tags[:3]) }品牌做"
        f"{ '、'.join(profile.suitable_goals[:3]) }，主要内容能力是"
        f"{ '、'.join(profile.content_capability_tags[:3]) }。"
    )
    return profile


def enrich_profiles(profiles: list[CreatorProfile]) -> list[CreatorProfile]:
    return [enrich_profile(profile) for profile in profiles]
