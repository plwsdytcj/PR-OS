from __future__ import annotations

import re

from src.intelligence.profiling import INDUSTRY_KEYWORDS
from src.schemas import BrandBrief


PLATFORMS = ["抖音", "小红书", "B站", "快手", "微博", "视频号", "公众号", "懂车帝"]
GOALS = ["曝光", "种草", "转化", "新品预热", "品牌背书", "公关破圈", "舆情修复", "搜索沉淀", "用户教育"]
CONTENT_PREFS = ["科技感", "智能化", "高端感", "真实体验", "专业测评", "成分科技", "口播解释", "视觉大片", "生活方式"]


def _extract_budget(text: str) -> int:
    patterns = [
        r"预算\s*(\d+(?:\.\d+)?)\s*万",
        r"(\d+(?:\.\d+)?)\s*万\s*预算",
        r"预算\s*(\d{5,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            return int(value * 10_000 if "万" in match.group(0) else value)
    return 0


def _extract_industry(text: str) -> str:
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            return industry
    return ""


def _extract_product(text: str) -> str:
    product_patterns = [r"推广一款([^，。,.\n]+)", r"发布一款([^，。,.\n]+)", r"做([^，。,.\n]+)新品", r"产品是([^，。,.\n]+)"]
    for pattern in product_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    if "新能源" in text and "SUV" in text.upper():
        return "新能源 SUV"
    return ""


def parse_brief(text: str) -> BrandBrief:
    industry = _extract_industry(text)
    goals = [goal for goal in GOALS if goal in text]
    if "预热" in text and "新品预热" not in goals:
        goals.append("新品预热")
    if not goals:
        goals = ["曝光", "新品预热"]
    platforms = [platform for platform in PLATFORMS if platform in text]
    prefs = [pref for pref in CONTENT_PREFS if pref in text]
    audience = []
    age = re.search(r"(\d{2}\s*-\s*\d{2}\s*岁)", text)
    if age:
        audience.append(age.group(1).replace(" ", ""))
    for token in ["一二线城市", "男性", "女性", "科技兴趣人群", "汽车兴趣人群", "职场人群", "年轻家庭", "高消费"]:
        if token in text:
            audience.append(token)
    stage = "新品上市预热" if "新品" in text and "预热" in text else ("种草" if "种草" in text else "")
    return BrandBrief(
        raw_text=text,
        industry=industry,
        product=_extract_product(text),
        budget=_extract_budget(text),
        campaign_stage=stage,
        goals=goals,
        target_audience=audience,
        platform_preference=platforms,
        content_preference=prefs,
    )
