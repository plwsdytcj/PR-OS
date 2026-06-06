from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.collaboration.service import create_proposal_from_brief, public_proposal_payload, record_feedback, update_preference_from_feedback
from src.collaboration.storage import (
    init_collaboration_db,
    load_feedback,
    load_preference,
    load_versions,
    upsert_proposal,
    upsert_version,
)
from src.intelligence.profiling import enrich_profiles
from src.normalize.mapper import map_dataframe_to_profiles
from src.storage.db import init_db, load_profiles, replace_profiles


DB = ROOT / "data" / "processed" / "phase2_smoke.sqlite3"
SAMPLE = ROOT / "data" / "raw" / "sample_creators.csv"


def main() -> None:
    init_db(DB)
    init_collaboration_db(DB)
    profiles = enrich_profiles(map_dataframe_to_profiles(pd.read_csv(SAMPLE), source="sample_csv"))
    replace_profiles(DB, profiles)
    proposal, version, markdown = create_proposal_from_brief(
        DB,
        client_name="Phase2 Smoke 客户",
        project_name="新能源 SUV 协作方案",
        brief_text="预算50万，新能源SUV上市预热，强调智能化、高端感和城市生活。平台优先抖音、小红书。",
        creators=load_profiles(DB),
        top_n=4,
    )
    upsert_proposal(DB, proposal)
    upsert_version(DB, version)
    assert proposal.share_token
    assert version.candidates
    assert markdown
    feedback = record_feedback(
        DB,
        proposal,
        version,
        target_type="creator",
        target_id=version.candidates[0].creator_id,
        decision="rejected",
        reason="报价偏高",
        comment="请换成更有汽车测评背书的达人",
    )
    upsert_version(DB, version)
    preference = update_preference_from_feedback(DB, proposal, version)
    payload = public_proposal_payload(proposal, version, load_feedback(DB, proposal.proposal_id))
    assert feedback.decision == "rejected"
    assert preference.budget_sensitivity == "high"
    assert payload["candidates"][0]["feedback"]
    assert load_preference(DB, proposal.client_id)
    assert load_versions(DB, proposal.proposal_id)
    print(f"OK proposal={proposal.proposal_id} candidates={len(version.candidates)} feedback={feedback.decision}")
    print(f"preference_budget={preference.budget_sensitivity}")


if __name__ == "__main__":
    main()
