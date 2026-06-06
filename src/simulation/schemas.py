from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SimulationNode:
    node_id: str
    label: str
    node_type: str
    stance: str = "neutral"
    risk_level: str = "medium"
    score: int = 50
    summary: str = ""


@dataclass
class SimulationEdge:
    source: str
    target: str
    label: str
    edge_type: str = "influence"
    intensity: int = 50


@dataclass
class SimulationTimelineEvent:
    event_id: str
    step: int
    actor: str
    event_type: str
    title: str
    detail: str
    sentiment: str = "neutral"
    risk_level: str = "medium"


@dataclass
class AgentReaction:
    agent_id: str
    agent_name: str
    role: str
    stance: str
    quote: str
    concerns: list[str] = field(default_factory=list)
    positive_points: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)


@dataclass
class SimulationReport:
    report_id: str
    engine: str
    summary: str
    positive_reactions: list[str] = field(default_factory=list)
    negative_reactions: list[str] = field(default_factory=list)
    misreading_points: list[str] = field(default_factory=list)
    risk_points: list[str] = field(default_factory=list)
    optimization_suggestions: list[str] = field(default_factory=list)
    final_recommendation: str = ""
    nodes: list[SimulationNode | dict[str, Any]] = field(default_factory=list)
    edges: list[SimulationEdge | dict[str, Any]] = field(default_factory=list)
    timeline: list[SimulationTimelineEvent | dict[str, Any]] = field(default_factory=list)
    agent_reactions: list[AgentReaction | dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    engine_status: str = "ok"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
