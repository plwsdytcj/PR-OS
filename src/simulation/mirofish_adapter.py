from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from src.schemas import stable_id
from src.simulation.schemas import AgentReaction, SimulationEdge, SimulationNode, SimulationReport, SimulationTimelineEvent
from src.simulation.stress_test_adapter import StressTestAdapter


class MiroFishCliAdapter(StressTestAdapter):
    """Optional MiroFish CLI adapter.

    The official MiroFish ecosystem is treated as a replaceable stress-test
    engine. If the executable is unavailable, callers should fall back to
    LlmFallbackStressTest.
    """

    engine_name = "mirofish_cli"

    def __init__(self, executable: str = "mirofish") -> None:
        self.executable = executable

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def run(self, payload: dict[str, Any]) -> SimulationReport:
        if not self.available():
            raise RuntimeError("MiroFish CLI is not installed or not on PATH")
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            seed = workdir / "campaign_seed.md"
            seed.write_text(_seed_markdown(payload), encoding="utf-8")
            requirement = "对该 PR/KOL 投放方案做投放前压力测试，输出正负反馈、误读点、风险和优化建议。不要预测 ROI 或爆款。"
            output = subprocess.run(
                [self.executable, "run", "--files", str(seed), "--requirement", requirement, "--json"],
                cwd=workdir,
                text=True,
                capture_output=True,
                timeout=180,
                check=False,
            )
            if output.returncode != 0:
                raise RuntimeError(output.stderr or output.stdout or "MiroFish CLI failed")
            verdict = _load_first_existing(workdir, ["verdict.json", "summary.json"])
            graph = _load_first_existing(workdir, ["graph.json"])
            timeline_data = _load_first_existing(workdir, ["timeline.json"])
            actions = _load_jsonl(workdir / "actions.jsonl")
            artifacts = _load_artifacts(workdir, ["swarm-overview.svg", "cluster-map.svg", "timeline.svg", "report.md"])
            report_md = (workdir / "report.md").read_text(encoding="utf-8") if (workdir / "report.md").exists() else output.stdout
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
                summary=verdict.get("summary") or report_md[:240],
                positive_reactions=verdict.get("positive_reactions", []),
                negative_reactions=verdict.get("negative_reactions", []),
                misreading_points=verdict.get("misreading_points", []),
                risk_points=verdict.get("risk_points", []),
                optimization_suggestions=verdict.get("optimization_suggestions", []),
                final_recommendation=verdict.get("final_recommendation", "MiroFish 推演结果仅作为压力测试参考。"),
                nodes=_normalize_nodes(graph_nodes),
                edges=_normalize_edges(graph_edges),
                timeline=_normalize_timeline(timeline_items, actions),
                agent_reactions=_normalize_agent_reactions(verdict.get("agent_reactions", []), actions),
                artifacts=artifacts,
                engine_status="mirofish_cli_ready",
            )


def _seed_markdown(payload: dict[str, Any]) -> str:
    return "# Campaign Stress Test Seed\n\n```json\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```\n"


def _load_first_existing(workdir: Path, names: list[str]) -> dict[str, Any]:
    for name in names:
        path = workdir / name
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
    return {}


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


def _load_artifacts(workdir: Path, names: list[str]) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    for name in names:
        path = workdir / name
        if path.exists():
            artifacts[name] = path.read_text(encoding="utf-8")
    return artifacts


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
