from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.connectors.excel_connector import load_table_file
from src.connectors.link_connector import parse_links
from src.connectors.mock_api_connector import MockApiConnector
from src.connectors.oneapi_connector import OneApiConnector
from src.intelligence.brief_parser import parse_brief
from src.intelligence.matching import rank_creators
from src.intelligence.profiling import enrich_profiles
from src.normalize.mapper import map_dataframe_to_profiles
from src.report.proposal_generator import generate_markdown_proposal
from src.storage.db import (
    count_profiles,
    init_db,
    load_profiles,
    replace_profiles,
    upsert_profiles,
)


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "phase1.sqlite3"


st.set_page_config(page_title="PR AI OS - Media Copilot", layout="wide")
init_db(DB_PATH)

st.title("PR AI OS - Media Copilot")
st.caption("Phase 1: 多源达人数据接入 -> KOL Profile -> AI 商业画像 -> Brief 匹配 -> 方案生成")


def _profiles_df() -> pd.DataFrame:
    profiles = load_profiles(DB_PATH)
    if not profiles:
        return pd.DataFrame()
    rows = []
    for p in profiles:
        rows.append(
            {
                "creator_id": p.creator_id,
                "name": p.name,
                "platform": p.platform,
                "followers": p.follower_count,
                "price": p.listed_price,
                "industries": ", ".join(p.industry_fit_tags),
                "capabilities": ", ".join(p.content_capability_tags),
                "risks": ", ".join(p.risk_tags),
                "sources": ", ".join(p.data_sources),
                "summary": p.ai_summary,
            }
        )
    return pd.DataFrame(rows)


tabs = st.tabs(["工作台", "数据接入", "达人库", "Brief 推荐", "方案导出"])

with tabs[0]:
    total, enriched = count_profiles(DB_PATH)
    c1, c2, c3 = st.columns(3)
    c1.metric("已接入达人数", total)
    c2.metric("已完成画像数", enriched)
    c3.metric("数据源状态", "Mock API 可用")
    st.markdown(
        """
        **第一期闭环**

        1. 通过 Excel / CSV、主页链接、Mock API、人工录入接入达人数据。
        2. 系统清洗、去重并统一成 KOL Profile。
        3. 规则画像引擎生成商业标签、风险和摘要。
        4. 输入甲方 brief，系统推荐达人组合并生成方案。
        """
    )

with tabs[1]:
    st.subheader("Excel / CSV 导入")
    upload = st.file_uploader("拖拽上传达人表、刊例表、报价表或历史合作表", type=["xlsx", "csv"])
    replace_existing = st.checkbox("导入后替换当前达人库", value=False)
    if upload:
        tables = load_table_file(upload)
        sheet_name = st.selectbox("选择 Sheet / 表", list(tables.keys()))
        raw_df = tables[sheet_name]
        st.dataframe(raw_df.head(30), use_container_width=True)
        st.caption("系统会自动识别常见字段，如达人名、平台、链接、粉丝、报价、简介、案例、备注。")
        if st.button("确认导入并生成画像", type="primary"):
            profiles = map_dataframe_to_profiles(raw_df, source=f"excel:{sheet_name}")
            profiles = enrich_profiles(profiles)
            if replace_existing:
                replace_profiles(DB_PATH, profiles)
            else:
                upsert_profiles(DB_PATH, profiles)
            st.success(f"已导入 {len(profiles)} 个 KOL Profile")

    st.divider()
    st.subheader("达人主页 / 内容链接录入")
    links_text = st.text_area("每行一个达人主页或内容链接", height=120)
    if st.button("解析链接并入库"):
        link_profiles = enrich_profiles(parse_links(links_text.splitlines()))
        upsert_profiles(DB_PATH, link_profiles)
        st.success(f"已解析 {len(link_profiles)} 条链接")

    st.divider()
    st.subheader("API Connector")
    st.caption("支持真实 OneAPI Connector；没有 API Key 时可用 Mock API 验证流程。")
    api_provider = st.selectbox("数据源", ["Mock API", "OneAPI / GetOneAPI"])
    api_platform = st.selectbox("平台", ["抖音", "小红书", "B站", "快手", "微博"])
    api_id = st.text_input("达人 ID / handle / 主页链接")
    oneapi_key = ""
    if api_provider.startswith("OneAPI"):
        oneapi_key = st.text_input("OneAPI API Key", type="password")
    if st.button("调用 API 并入库"):
        try:
            connector = OneApiConnector(oneapi_key) if api_provider.startswith("OneAPI") else MockApiConnector()
            profile = connector.fetch_creator(api_platform, api_id)
            upsert_profiles(DB_PATH, enrich_profiles([profile]))
            st.success(f"已通过 {connector.provider_name} 接入：{profile.name}")
        except Exception as exc:
            st.error(f"API 调用失败：{exc}")

    st.divider()
    st.subheader("人工补充")
    with st.form("manual_creator"):
        name = st.text_input("达人名称")
        platform = st.selectbox("平台 ", ["抖音", "小红书", "B站", "快手", "微博", "视频号", "公众号", "其他"])
        homepage = st.text_input("主页链接")
        bio = st.text_area("简介 / 内容方向")
        followers = st.number_input("粉丝数", min_value=0, step=1000)
        price = st.number_input("报价", min_value=0, step=1000)
        brands = st.text_input("历史合作品牌，逗号分隔")
        notes = st.text_area("媒介备注 / 风险 / 履约反馈")
        submitted = st.form_submit_button("保存人工资料")
        if submitted and name:
            manual_df = pd.DataFrame(
                [
                    {
                        "name": name,
                        "platform": platform,
                        "homepage_url": homepage,
                        "bio": bio,
                        "follower_count": followers,
                        "listed_price": price,
                        "cooperation_brands": brands,
                        "manual_notes": notes,
                    }
                ]
            )
            profiles = enrich_profiles(map_dataframe_to_profiles(manual_df, source="manual"))
            upsert_profiles(DB_PATH, profiles)
            st.success("已保存并生成画像")

with tabs[2]:
    st.subheader("达人库")
    df = _profiles_df()
    if df.empty:
        st.info("暂无达人数据。请先在「数据接入」导入或录入。")
    else:
        platform_filter = st.multiselect("平台筛选", sorted(df["platform"].dropna().unique().tolist()))
        query = st.text_input("搜索名称 / 标签 / 摘要")
        view = df.copy()
        if platform_filter:
            view = view[view["platform"].isin(platform_filter)]
        if query:
            mask = view.apply(lambda row: query.lower() in " ".join(map(str, row.values)).lower(), axis=1)
            view = view[mask]
        st.dataframe(view, use_container_width=True, hide_index=True)

        selected = st.selectbox("查看达人详情", df["creator_id"].tolist())
        profile = next((p for p in load_profiles(DB_PATH) if p.creator_id == selected), None)
        if profile:
            st.json(json.loads(profile.to_json()), expanded=False)

with tabs[3]:
    st.subheader("甲方 Brief 输入与推荐")
    default_brief = "我们是新能源汽车品牌，预算50万，准备做新能源SUV新品上市预热。目标用户是25-40岁一二线城市男性，希望突出科技感、智能化和高端感。平台优先抖音、小红书、懂车帝。"
    brief_text = st.text_area("自然语言 Brief", value=default_brief, height=140)
    budget_override = st.number_input("预算补充 / 覆盖", min_value=0, step=10000, value=0)
    if st.button("解析 Brief 并推荐", type="primary"):
        profiles = load_profiles(DB_PATH)
        if not profiles:
            st.warning("请先接入达人数据。")
        else:
            brief = parse_brief(brief_text)
            if budget_override:
                brief.budget = budget_override
            rankings = rank_creators(brief, profiles)
            st.session_state["last_brief"] = brief.to_json()
            st.session_state["last_rankings"] = [r.to_json() for r in rankings]
            st.json(json.loads(brief.to_json()))
            st.dataframe(pd.DataFrame([r.to_table_row() for r in rankings[:30]]), use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("方案导出")
    if "last_brief" not in st.session_state or "last_rankings" not in st.session_state:
        st.info("请先在「Brief 推荐」生成推荐结果。")
    else:
        from src.schemas import BrandBrief, MatchResult

        brief = BrandBrief.from_json(st.session_state["last_brief"])
        rankings = [MatchResult.from_json(item) for item in st.session_state["last_rankings"]]
        md = generate_markdown_proposal(brief, rankings[:20])
        st.text_area("Markdown 方案", value=md, height=500)
        st.download_button("下载 Markdown 方案", data=md.encode("utf-8"), file_name="pr_ai_os_proposal.md")
