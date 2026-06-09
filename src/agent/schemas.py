from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from src.schemas import stable_id


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def task_id_for(title: str, brief: str) -> str:
    return stable_id(title.strip(), brief.strip()[:240], prefix="agent_task")


def thread_id_for(client_name: str, project_name: str, seed: str) -> str:
    return stable_id(client_name.strip(), project_name.strip(), seed.strip()[:240], now_iso(), prefix="agent_thread")


def message_id_for(thread_id: str, role: str, content: str) -> str:
    return stable_id(thread_id, role, content.strip()[:240], now_iso(), prefix="agent_msg")


def assistant_message_id_for(thread_id: str, run_id: str) -> str:
    return stable_id(thread_id, "assistant", run_id, prefix="agent_msg")


def run_id_for(task_id: str, user_message: str) -> str:
    return stable_id(task_id, user_message.strip(), now_iso(), prefix="agent_run")


def event_id_for(run_id: str, index: int, title: str) -> str:
    return stable_id(run_id, str(index), title, prefix="agent_event")


def artifact_id_for(task_id: str, artifact_type: str, title: str) -> str:
    return stable_id(task_id, artifact_type, title, now_iso(), prefix="agent_artifact")


@dataclass
class AgentTask:
    task_id: str
    title: str
    status: str = "active"
    client_name: str = ""
    project_name: str = ""
    brief: str = ""
    created_by: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    current_run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "AgentTask":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentThread:
    thread_id: str
    task_id: str
    title: str
    status: str = "active"
    client_name: str = ""
    project_name: str = ""
    summary: str = ""
    created_by: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    current_run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "AgentThread":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentMessage:
    message_id: str
    thread_id: str
    role: str
    content: str
    run_id: str = ""
    status: str = "completed"
    created_by: str = ""
    created_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "AgentMessage":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentRun:
    run_id: str
    task_id: str
    status: str = "running"
    user_message: str = ""
    final_answer: str = ""
    created_by: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "AgentRun":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentEvent:
    event_id: str
    run_id: str
    task_id: str
    sequence: int
    event_type: str
    status: str
    title: str
    summary: str = ""
    tool_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    artifact_id: str = ""
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "AgentEvent":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentArtifact:
    artifact_id: str
    task_id: str
    run_id: str
    artifact_type: str
    title: str
    summary: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "AgentArtifact":
        return cls(**json.loads(value))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
