from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.schemas import stable_id
from src.simulation.schemas import AgentReaction, SimulationEdge, SimulationNode, SimulationReport, SimulationTimelineEvent
from src.simulation.stress_test_adapter import StressTestAdapter

load_dotenv()


class MiroFishCliAdapter(StressTestAdapter):
    """Optional MiroFish CLI adapter.

    The official MiroFish ecosystem is treated as a replaceable stress-test
    engine. If the executable is unavailable, callers should fall back to
    LlmFallbackStressTest.
    """

    engine_name = "mirofish_cli"

    def __init__(self, executable: str | None = None, timeout_seconds: int | None = None) -> None:
        self.command = shlex.split(executable or os.getenv("MIROFISH_COMMAND") or "mirofish")
        self.timeout_seconds = timeout_seconds or int(os.getenv("MIROFISH_TIMEOUT_SECONDS", "420"))
        self.max_rounds = int(os.getenv("MIROFISH_MAX_ROUNDS", "2"))

    def available(self) -> bool:
        return bool(self.command) and shutil.which(self.command[0]) is not None

    def run(self, payload: dict[str, Any]) -> SimulationReport:
        if not self.available():
            raise RuntimeError("MiroFish CLI is not installed or not on PATH")
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            output_dir = workdir / "runs"
            seed = workdir / "campaign_seed.md"
            seed.write_text(_seed_markdown(payload), encoding="utf-8")
            requirement = "对该 PR/KOL 投放方案做投放前压力测试，输出正负反馈、误读点、风险和优化建议。不要预测 ROI 或爆款。"
            env = os.environ.copy()
            env["LLM_PROVIDER"] = os.getenv("MIROFISH_LLM_PROVIDER") or _valid_mirofish_provider(env.get("LLM_PROVIDER"))
            command = [
                *self.command,
                "run",
                "--files",
                str(seed),
                "--requirement",
                requirement,
                "--platform",
                os.getenv("MIROFISH_PLATFORM", "parallel"),
                "--max-rounds",
                str(self.max_rounds),
                "--output-dir",
                str(output_dir),
                "--json",
            ]
            try:
                output = subprocess.run(
                    command,
                    cwd=workdir,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f"MiroFish CLI timed out after {self.timeout_seconds}s") from exc
            if output.returncode != 0:
                raise RuntimeError(output.stderr or output.stdout or "MiroFish CLI failed")
            manifest = _resolve_mirofish_manifest(output.stdout, output_dir)
            run_dir = output_dir / manifest.get("run_id", "") if manifest else _latest_child_dir(output_dir)
            artifact_paths = _resolve_manifest_artifacts(run_dir, manifest)
            verdict = _load_json_path(artifact_paths.get("verdict") or run_dir / "report" / "verdict.json")
            summary = _load_json_path(artifact_paths.get("report_summary") or run_dir / "report" / "summary.json")
            graph = _load_json_path(artifact_paths.get("graph_json") or run_dir / "graph" / "graph.json")
            timeline_data = _load_json_path(artifact_paths.get("timeline_json") or run_dir / "simulation" / "timeline.json")
            actions = _load_jsonl(artifact_paths.get("actions_log") or run_dir / "simulation" / "actions.jsonl")
            artifacts = _load_artifacts_from_paths(
                {
                    "swarm-overview.svg": artifact_paths.get("swarm_overview") or run_dir / "visuals" / "swarm-overview.svg",
                    "cluster-map.svg": artifact_paths.get("cluster_map") or run_dir / "visuals" / "cluster-map.svg",
                    "timeline.svg": artifact_paths.get("timeline") or run_dir / "visuals" / "timeline.svg",
                    "report.md": artifact_paths.get("report_markdown") or run_dir / "report" / "report.md",
                }
            )
            report_md = artifacts.get("report.md") or output.stdout
            graph_nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
            graph_edges = graph.get("edges", []) if isinstance(graph, dict) else []
            if isinstance(timeline_data, dict):
                timeline_items = timeline_data.get("timeline", [])
            elif isinstance(timeline_data, list):
                timeline_items = timeline_data
            else:
                timeline_items = []
            return SimulationReport(
                report_id=stable_id(json.dumps(payload, ensure_ascii=False), "mirofish", prefix="sim"),
                engine=self.engine_name,
                summary=_mirofish_summary(verdict, summary, report_md),
                positive_reactions=_extract_signals(verdict, "positive"),
                negative_reactions=_extract_signals(verdict, "negative"),
                misreading_points=summary.get("key_dynamics", []) if isinstance(summary, dict) else [],
                risk_points=_extract_signals(verdict, "negative")[:5],
                optimization_suggestions=verdict.get("key_dynamics", []) if isinstance(verdict, dict) else [],
                final_recommendation=verdict.get("prediction", "MiroFish 推演结果仅作为压力测试参考。") if isinstance(verdict, dict) else "MiroFish 推演结果仅作为压力测试参考。",
                nodes=_normalize_nodes(graph_nodes),
                edges=_normalize_edges(graph_edges),
                timeline=_normalize_timeline(timeline_items, actions),
                agent_reactions=_normalize_agent_reactions(verdict.get("agent_reactions", []), actions),
                artifacts=artifacts,
                engine_status="mirofish_cli_ready",
            )


def _seed_markdown(payload: dict[str, Any]) -> str:
    seed = _compact_seed_payload(payload)
    return "# Campaign Stress Test Seed\n\n```json\n" + json.dumps(seed, ensure_ascii=False, indent=2) + "\n```\n"


def _compact_seed_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep MiroFish grounded without sending the full PR OS object graph.

    The full project payload contains nested reports, assets, campaign rooms and
    generated plans. Feeding all of that into MiroFish makes ontology extraction
    and persona generation too slow for a campaign run. This seed keeps only the
    business facts needed for stress testing.
    """
    brief = payload.get("brief") if isinstance(payload.get("brief"), dict) else {}
    brand = payload.get("brand") if isinstance(payload.get("brand"), dict) else {}
    product = payload.get("product") if isinstance(payload.get("product"), dict) else {}
    social_report = payload.get("social_report") if isinstance(payload.get("social_report"), dict) else {}
    matches = payload.get("matches") if isinstance(payload.get("matches"), list) else []
    narratives = payload.get("narratives") if isinstance(payload.get("narratives"), list) else []

    return {
        "client_name": _clip(payload.get("client_name"), 80),
        "project_name": _clip(payload.get("project_name"), 120),
        "raw_brief": _clip(payload.get("raw_brief"), 900),
        "brief": {
            "industry": _clip(brief.get("industry"), 80),
            "product": _clip(brief.get("product"), 120),
            "budget": brief.get("budget", 0),
            "goals": _compact_list(brief.get("goals"), 8),
            "target_audience": _compact_list(brief.get("target_audience"), 8),
            "platform_preference": _compact_list(brief.get("platform_preference"), 6),
            "content_preference": _compact_list(brief.get("content_preference"), 8),
        },
        "brand": {
            "brand_name": _clip(brand.get("brand_name"), 100),
            "industry": _clip(brand.get("industry"), 80),
            "product": _clip(brand.get("product"), 120),
            "target_tags": _compact_list(brand.get("target_tags"), 10),
            "suitable_creator_types": _compact_list(brand.get("suitable_creator_types"), 8),
            "risk_tags": _compact_list(brand.get("risk_tags"), 8),
        },
        "product": {
            "product_name": _clip(product.get("product_name"), 120),
            "category": _clip(product.get("category"), 80),
            "metaphors": _compact_list(product.get("metaphors"), 8),
            "use_scenarios": _compact_list(product.get("use_scenarios"), 8),
        },
        "social_context": {
            "title": _clip(social_report.get("title"), 160),
            "issues": _compact_list(social_report.get("issues"), 8, item_limit=160),
            "risk_points": _compact_list(social_report.get("risk_points"), 8, item_limit=160),
        },
        "top_kol_candidates": [_compact_match(item) for item in matches[:8] if isinstance(item, dict)],
        "narrative_paths": [_compact_narrative(item) for item in narratives[:3] if isinstance(item, dict)],
    }


def _compact_match(item: dict[str, Any]) -> dict[str, Any]:
    creator = item.get("creator") if isinstance(item.get("creator"), dict) else item
    return {
        "creator_id": _clip(item.get("creator_id") or creator.get("creator_id"), 80),
        "creator_name": _clip(item.get("creator_name") or creator.get("name"), 120),
        "platform": _clip(creator.get("platform") or item.get("platform"), 60),
        "score": item.get("score") or item.get("match_score"),
        "tags": _compact_list(
            creator.get("content_capability_tags")
            or creator.get("industry_fit_tags")
            or item.get("matched_tags")
            or item.get("tags"),
            10,
        ),
        "reason": _clip(item.get("reason") or item.get("recommended_role") or item.get("suggested_content"), 180),
        "risks": _compact_list(item.get("risk_points") or item.get("risk_flags"), 5, item_limit=140),
    }


def _compact_narrative(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": _clip(item.get("title") or item.get("path_name"), 160),
        "summary": _clip(item.get("summary") or item.get("content_path") or item.get("core_message"), 260),
        "platform": _clip(item.get("platform"), 60),
    }


def _compact_list(value: Any, limit: int, item_limit: int = 80) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_clip(item, item_limit) for item in value[:limit] if _clip(item, item_limit)]


def _clip(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _valid_mirofish_provider(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"claude-cli", "codex-cli"}:
        return normalized
    return "claude-cli"


def _resolve_mirofish_manifest(stdout: str, output_dir: Path) -> dict[str, Any]:
    try:
        payload = json.loads(stdout)
        if isinstance(payload, dict) and payload.get("run_id"):
            return payload
    except json.JSONDecodeError:
        pass
    run_dir = _latest_child_dir(output_dir)
    if run_dir:
        return _load_json_path(run_dir / "manifest.json")
    return {}


def _latest_child_dir(output_dir: Path) -> Path:
    if not output_dir.exists():
        return output_dir
    children = [path for path in output_dir.iterdir() if path.is_dir()]
    if not children:
        return output_dir
    return max(children, key=lambda path: path.stat().st_mtime)


def _resolve_manifest_artifacts(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    for key, rel_path in (manifest.get("artifacts") or {}).items():
        path = run_dir / str(rel_path)
        if path.exists():
            artifacts[str(key)] = path
    return artifacts


def _load_json_path(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {"timeline": payload}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _load_artifacts_from_paths(paths: dict[str, Path]) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    for name, path in paths.items():
        if path and path.exists():
            artifacts[name] = path.read_text(encoding="utf-8")
    return artifacts


def _mirofish_summary(verdict: dict[str, Any], summary: dict[str, Any], report_md: str) -> str:
    if isinstance(verdict, dict):
        for key in ("summary", "prediction"):
            if verdict.get(key):
                return str(verdict[key])
    if isinstance(summary, dict) and summary.get("verdict", {}).get("prediction"):
        return str(summary["verdict"]["prediction"])
    return report_md[:240]


def _extract_signals(verdict: dict[str, Any], direction: str) -> list[str]:
    signals = verdict.get("signals", []) if isinstance(verdict, dict) else []
    rows: list[str] = []
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        if signal.get("direction") == direction and signal.get("signal"):
            rows.append(str(signal["signal"]))
    return rows


def _normalize_nodes(items: list[Any]) -> list[SimulationNode]:
    nodes: list[SimulationNode] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        nodes.append(
            SimulationNode(
                node_id=str(item.get("node_id") or item.get("id") or f"node_{index}"),
                label=str(item.get("label") or item.get("name") or f"节点 {index}"),
                node_type=str(item.get("node_type") or item.get("type") or "agent"),
                stance=str(item.get("stance") or "neutral"),
                risk_level=str(item.get("risk_level") or item.get("risk") or "medium"),
                score=int(item.get("score") or item.get("weight") or 50),
                summary=str(item.get("summary") or item.get("description") or ""),
            )
        )
    return nodes


def _normalize_edges(items: list[Any]) -> list[SimulationEdge]:
    edges: list[SimulationEdge] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        source = item.get("source") or item.get("from")
        target = item.get("target") or item.get("to")
        if not source or not target:
            continue
        edges.append(
            SimulationEdge(
                source=str(source),
                target=str(target),
                label=str(item.get("label") or item.get("relation") or "影响"),
                edge_type=str(item.get("edge_type") or item.get("type") or "influence"),
                intensity=int(item.get("intensity") or item.get("weight") or 50),
            )
        )
    return edges


def _normalize_timeline(items: list[Any], actions: list[dict[str, Any]]) -> list[SimulationTimelineEvent]:
    source_items = items or actions
    timeline: list[SimulationTimelineEvent] = []
    for index, item in enumerate(source_items, start=1):
        if not isinstance(item, dict):
            continue
        timeline.append(
            SimulationTimelineEvent(
                event_id=str(item.get("event_id") or item.get("id") or f"event_{index}"),
                step=int(item.get("step") or index),
                actor=str(item.get("actor") or item.get("agent") or item.get("role") or "agent"),
                event_type=str(item.get("event_type") or item.get("type") or "action"),
                title=str(item.get("title") or item.get("action") or f"推演事件 {index}"),
                detail=str(item.get("detail") or item.get("content") or item.get("message") or ""),
                sentiment=str(item.get("sentiment") or "neutral"),
                risk_level=str(item.get("risk_level") or "medium"),
            )
        )
    return timeline


def _normalize_agent_reactions(items: list[Any], actions: list[dict[str, Any]]) -> list[AgentReaction]:
    source_items = items or [item for item in actions if item.get("agent") or item.get("role")]
    reactions: list[AgentReaction] = []
    for index, item in enumerate(source_items, start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("agent_name") or item.get("agent") or item.get("role") or f"Agent {index}")
        reactions.append(
            AgentReaction(
                agent_id=str(item.get("agent_id") or item.get("id") or f"agent_{index}"),
                agent_name=name,
                role=str(item.get("role") or item.get("agent_role") or "simulation_agent"),
                stance=str(item.get("stance") or item.get("sentiment") or "neutral"),
                quote=str(item.get("quote") or item.get("message") or item.get("content") or ""),
                concerns=_as_list(item.get("concerns")),
                positive_points=_as_list(item.get("positive_points") or item.get("positives")),
                risk_flags=_as_list(item.get("risk_flags") or item.get("risks")),
            )
        )
    return reactions


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []
