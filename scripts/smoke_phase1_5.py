from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.intelligence.profiling import enrich_profiles
from src.normalize.mapper import map_dataframe_to_profiles
from src.simulation.llm_fallback import LlmFallbackStressTest
from src.storage.db import init_db, load_profiles, replace_profiles
from src.symbolic.brand_profiler import generate_brand_symbolic_profile
from src.symbolic.creator_profiler import generate_creator_symbolic_profile
from src.symbolic.narrative_path import generate_narrative_path
from src.symbolic.storage import init_symbolic_db, upsert_brand_symbolic, upsert_creator_symbolic
from src.symbolic.symbolic_matching import rank_symbolic_creators


DB = ROOT / "data" / "processed" / "phase1_5_smoke.sqlite3"
SAMPLE = ROOT / "data" / "raw" / "sample_creators.csv"


def main() -> None:
    init_db(DB)
    init_symbolic_db(DB)
    df = pd.read_csv(SAMPLE)
    profiles = enrich_profiles(map_dataframe_to_profiles(df, source="sample_csv"))
    replace_profiles(DB, profiles)
    creators = load_profiles(DB)
    symbolic_creators = []
    for creator in creators:
        symbolic = generate_creator_symbolic_profile(
            creator,
            content_sample="通勤 城市 智能座舱 家庭 安全感 真实体验 周末露营",
            case_sample="新能源汽车试驾、城市通勤体验、家庭出行内容",
        )
        assert symbolic.primary_tags
        assert symbolic.evidence
        upsert_creator_symbolic(DB, symbolic)
        symbolic_creators.append(symbolic)

    brand = generate_brand_symbolic_profile(
        {
            "brand_name": "某新能源汽车品牌",
            "industry": "汽车",
            "product": "新能源 SUV",
            "brief": "预算50万，准备做新能源SUV新品上市预热，突出科技感、智能化和高端感。",
        }
    )
    upsert_brand_symbolic(DB, brand)
    matches = rank_symbolic_creators(brand, symbolic_creators)
    assert matches
    assert matches[0].symbolic_score > 0
    narrative = generate_narrative_path(brand, symbolic_creators[0])
    assert narrative.narrative_path
    report = LlmFallbackStressTest().run(
        {
            "brand": brand.to_dict(),
            "matches": [item.to_dict() for item in matches[:3]],
            "narratives": [narrative.to_dict()],
        }
    )
    assert report.summary
    assert report.nodes
    assert report.edges
    assert report.timeline
    assert report.agent_reactions
    assert "ROI" in report.final_recommendation
    assert "预测" in report.final_recommendation
    print(f"OK symbolic_creators={len(symbolic_creators)} top={matches[0].creator_name} score={matches[0].symbolic_score}")
    print(f"stress_engine={report.engine} nodes={len(report.nodes)} timeline={len(report.timeline)} agents={len(report.agent_reactions)}")


if __name__ == "__main__":
    main()
