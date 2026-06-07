from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.agent.rag import search_pr_knowledge
from src.collaboration.service import create_proposal_from_brief
from src.collaboration.storage import upsert_proposal, upsert_version
from src.project_run.service import run_pr_project
from src.storage.db import load_profiles


def search_knowledge_tool(db_path: Path, query: str, top_k: int = 5) -> dict[str, Any]:
    docs = search_pr_knowledge(db_path, query=query, top_k=top_k)
    return {"items": docs, "count": len(docs)}


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
