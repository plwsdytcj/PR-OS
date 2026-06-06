from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.intelligence.brief_parser import parse_brief
from src.intelligence.matching import rank_creators
from src.intelligence.profiling import enrich_profiles
from src.normalize.mapper import map_dataframe_to_profiles
from src.report.proposal_generator import generate_markdown_proposal
from src.storage.db import init_db, load_profiles, replace_profiles


DB = ROOT / "data" / "processed" / "phase1_smoke.sqlite3"
SAMPLE = ROOT / "data" / "raw" / "sample_creators.csv"


def main() -> None:
    init_db(DB)
    df = pd.read_csv(SAMPLE)
    profiles = enrich_profiles(map_dataframe_to_profiles(df, source="sample_csv"))
    replace_profiles(DB, profiles)
    loaded = load_profiles(DB)
    assert len(loaded) == len(df), f"expected {len(df)} profiles, got {len(loaded)}"
    assert all(p.ai_summary for p in loaded), "all profiles should be enriched"

    brief = parse_brief(
        "我们是新能源汽车品牌，预算50万，准备做新能源SUV新品上市预热。"
        "目标用户是25-40岁一二线城市男性，希望突出科技感、智能化和高端感。"
        "平台优先抖音、小红书、懂车帝。"
    )
    rankings = rank_creators(brief, loaded)
    assert rankings, "rankings should not be empty"
    assert rankings[0].match_score > 0, "top match should have a score"
    proposal = generate_markdown_proposal(brief, rankings[:5])
    assert "KOL 投放推荐方案" in proposal
    assert rankings[0].creator.name in proposal
    out = ROOT / "data" / "processed" / "sample_proposal.md"
    out.write_text(proposal, encoding="utf-8")
    print(f"OK profiles={len(loaded)} top={rankings[0].creator.name} score={rankings[0].match_score}")
    print(f"proposal={out}")


if __name__ == "__main__":
    main()
