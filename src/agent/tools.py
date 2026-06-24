from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.agent.rag import search_pr_knowledge
from src.collaboration.service import create_proposal_from_brief
from src.collaboration.storage import upsert_proposal, upsert_version
from src.intelligence.brief_deliverables import generate_brief_deliverables
from src.intelligence.business_type import classify_business_type
from src.intelligence.pr_os_judgment import agent_judgment_context
from src.project_run.service import run_pr_project
from src.storage.db import load_profiles


def search_knowledge_tool(db_path: Path, query: str, top_k: int = 5) -> dict[str, Any]:
    docs = search_pr_knowledge(db_path, query=query, top_k=top_k)
    return {"items": docs, "count": len(docs), "judgment": agent_judgment_context()}


def brief_deliverables_tool(
    db_path: Path,
    brief: str,
    client_name: str = "",
    top_n: int = 8,
) -> dict[str, Any]:
    _ = db_path
    result = generate_brief_deliverables(brief, client_name=client_name, creator_count=top_n, use_llm=True)
    return {
        "brief": result.get("brief"),
        "business": result.get("business"),
        "client_card": result.get("client_card"),
        "topic_cards": result.get("topic_cards"),
        "quote_skeleton": result.get("quote_skeleton"),
        "markdown": result.get("markdown"),
        "summary": {
            "business_type": (result.get("business") or {}).get("business_type_label"),
            "topic_count": len(result.get("topic_cards") or []),
            "package_name": (result.get("quote_skeleton") or {}).get("package_name"),
            "ai_enriched": bool(result.get("ai_enriched")),
        },
    }


def classify_business_tool(brief: str) -> dict[str, Any]:
    return classify_business_type(brief)


def run_project_tool(db_path: Path, client_name: str, project_name: str, brief: str, top_n: int = 8) -> dict[str, Any]:
    result = run_pr_project(db_path, client_name=client_name, project_name=project_name, raw_brief=brief, top_n=top_n)
    return {
        "run": result,
        "summary": {
            "steps": len(result.get("steps", [])),
            "matches": len(result.get("matches", [])),
            "narratives": len(result.get("narratives", [])),
            "graph_nodes": _graph_node_count(result),
            "campaign_id": result.get("campaign", {}).get("campaign", {}).get("campaign_id", ""),
        },
    }


def create_proposal_tool(
    db_path: Path,
    client_name: str,
    project_name: str,
    brief: str,
    top_n: int = 8,
    created_by: str = "agent",
) -> dict[str, Any]:
    proposal, version, markdown = create_proposal_from_brief(
        db_path,
        client_name=client_name,
        project_name=project_name,
        brief_text=brief,
        creators=load_profiles(db_path),
        top_n=top_n,
        created_by=created_by,
    )
    upsert_proposal(db_path, proposal)
    upsert_version(db_path, version)
    return {
        "proposal": asdict(proposal) | {"share_url": proposal.public_url()},
        "version": version.to_dict(),
        "markdown": markdown,
        "summary": {
            "proposal_id": proposal.proposal_id,
            "share_token": proposal.share_token,
            "candidate_count": len(version.candidates),
            "budget_total": version.budget_total,
        },
    }


def _graph_node_count(result: dict[str, Any]) -> int:
    graph = result.get("graph") or {}
    if isinstance(graph, dict):
        return len(graph.get("nodes") or [])
    return 0
