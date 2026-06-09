from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from dotenv import load_dotenv

from src.agent import runtime as custom_runtime


CUSTOM_RUNTIME = "custom"
OPENAI_AGENTS_RUNTIME = "openai_agents"
SUPPORTED_RUNTIMES = {CUSTOM_RUNTIME, OPENAI_AGENTS_RUNTIME}


@dataclass(frozen=True)
class RuntimeAdapterStatus:
    name: str
    active: bool
    available: bool
    mode: str
    message: str
    package: str = ""
    model: str = ""
    fallback_runtime: str = CUSTOM_RUNTIME

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "active": self.active,
            "available": self.available,
            "mode": self.mode,
            "message": self.message,
            "package": self.package,
            "model": self.model,
            "fallback_runtime": self.fallback_runtime,
        }


class AgentRuntimeAdapter(Protocol):
    name: str

    def status(self) -> RuntimeAdapterStatus:
        ...

    def run_chat(
        self,
        db_path: Path,
        message: str,
        task_id: str = "",
        client_name: str = "",
        project_name: str = "",
        top_n: int = 8,
        created_by: str = "",
        require_plan_approval: bool = False,
    ) -> dict[str, Any]:
        ...

    def start_chat(
        self,
        db_path: Path,
        message: str,
        task_id: str = "",
        client_name: str = "",
        project_name: str = "",
        top_n: int = 8,
        created_by: str = "",
        require_plan_approval: bool = False,
    ) -> dict[str, Any]:
        ...

    def execute_run(self, db_path: Path, run_id: str, top_n: int = 8, require_plan_approval: bool = False) -> None:
        ...

    def approve_plan(self, db_path: Path, run_id: str, top_n: int = 8) -> dict[str, Any]:
        ...

    def resume_clarification(self, db_path: Path, run_id: str, supplement: str, top_n: int = 8, created_by: str = "") -> dict[str, Any]:
        ...

    def start_thread_message(
        self,
        db_path: Path,
        thread_id: str,
        message: str,
        top_n: int = 8,
        created_by: str = "",
        require_plan_approval: bool = False,
    ) -> dict[str, Any]:
        ...


class CustomRuntimeAdapter:
    name = CUSTOM_RUNTIME

    def status(self) -> RuntimeAdapterStatus:
        return RuntimeAdapterStatus(
            name=self.name,
            active=True,
            available=True,
            mode="native",
            message="Using PR OS native runtime: planner, PR OS tools, events, artifacts, memory, and reasoning graph.",
            model=os.getenv("AGENT_MODEL") or os.getenv("GLM_MODEL") or "glm-4-flash",
        )

    def run_chat(
        self,
        db_path: Path,
        message: str,
        task_id: str = "",
        client_name: str = "",
        project_name: str = "",
        top_n: int = 8,
        created_by: str = "",
        require_plan_approval: bool = False,
    ) -> dict[str, Any]:
        return custom_runtime.run_agent_chat(
            db_path,
            message=message,
            task_id=task_id,
            client_name=client_name,
            project_name=project_name,
            top_n=top_n,
            created_by=created_by,
            require_plan_approval=require_plan_approval,
        )

    def start_chat(
        self,
        db_path: Path,
        message: str,
        task_id: str = "",
        client_name: str = "",
        project_name: str = "",
        top_n: int = 8,
        created_by: str = "",
        require_plan_approval: bool = False,
    ) -> dict[str, Any]:
        return custom_runtime.start_agent_chat(
            db_path,
            message=message,
            task_id=task_id,
            client_name=client_name,
            project_name=project_name,
            top_n=top_n,
            created_by=created_by,
            require_plan_approval=require_plan_approval,
        )

    def execute_run(self, db_path: Path, run_id: str, top_n: int = 8, require_plan_approval: bool = False) -> None:
        custom_runtime.execute_agent_run(db_path, run_id, top_n=top_n, require_plan_approval=require_plan_approval)

    def approve_plan(self, db_path: Path, run_id: str, top_n: int = 8) -> dict[str, Any]:
        return custom_runtime.approve_agent_plan(db_path, run_id, top_n=top_n)

    def resume_clarification(self, db_path: Path, run_id: str, supplement: str, top_n: int = 8, created_by: str = "") -> dict[str, Any]:
        return custom_runtime.resume_agent_clarification(db_path, run_id, supplement=supplement, top_n=top_n, created_by=created_by)

    def start_thread_message(
        self,
        db_path: Path,
        thread_id: str,
        message: str,
        top_n: int = 8,
        created_by: str = "",
        require_plan_approval: bool = False,
    ) -> dict[str, Any]:
        return custom_runtime.start_agent_thread_message(
            db_path,
            thread_id,
            message=message,
            top_n=top_n,
            created_by=created_by,
            require_plan_approval=require_plan_approval,
        )


class OpenAIAgentsRuntimeAdapter(CustomRuntimeAdapter):
    """Adapter boundary for OpenAI Agents SDK.

    Phase 7I-A keeps PR OS business tools and persistence stable while making the
    orchestration runtime replaceable. Until the SDK path is fully enabled and
    validated, execution deliberately delegates to the native runtime.
    """

    name = OPENAI_AGENTS_RUNTIME
    package_name = "agents"

    def status(self) -> RuntimeAdapterStatus:
        available = importlib.util.find_spec(self.package_name) is not None
        configured = bool(os.getenv("OPENAI_API_KEY") or os.getenv("AGENT_SDK_API_KEY") or os.getenv("AGENT_API_KEY"))
        if available and configured:
            message = "OpenAI Agents SDK package/config detected; Phase 7I-A delegates execution to native PR OS runtime until SDK tool parity is validated."
            mode = "sdk_detected_delegate"
        elif available:
            message = "OpenAI Agents SDK package detected, but no API key is configured; native PR OS runtime will execute."
            mode = "sdk_missing_key_delegate"
        else:
            message = "OpenAI Agents SDK package is not installed; native PR OS runtime will execute."
            mode = "sdk_missing_delegate"
        return RuntimeAdapterStatus(
            name=self.name,
            active=True,
            available=available and configured,
            mode=mode,
            message=message,
            package=self.package_name,
            model=os.getenv("AGENT_SDK_MODEL") or os.getenv("OPENAI_DEFAULT_MODEL") or os.getenv("AGENT_MODEL") or "",
            fallback_runtime=CUSTOM_RUNTIME,
        )


def requested_runtime_name() -> str:
    load_dotenv()
    name = (os.getenv("AGENT_RUNTIME") or os.getenv("AGENT_RUNTIME_ADAPTER") or CUSTOM_RUNTIME).strip().lower()
    if name in {"openai", "openai-agents", "agents_sdk", "agent_sdk"}:
        return OPENAI_AGENTS_RUNTIME
    if name not in SUPPORTED_RUNTIMES:
        return CUSTOM_RUNTIME
    return name


def get_runtime_adapter(name: str | None = None) -> AgentRuntimeAdapter:
    runtime = (name or requested_runtime_name()).strip().lower()
    if runtime == OPENAI_AGENTS_RUNTIME:
        return OpenAIAgentsRuntimeAdapter()
    return CustomRuntimeAdapter()


def runtime_status() -> dict[str, Any]:
    requested = requested_runtime_name()
    active = get_runtime_adapter(requested)
    statuses = [CustomRuntimeAdapter().status().to_dict(), OpenAIAgentsRuntimeAdapter().status().to_dict()]
    active_status = active.status().to_dict()
    return {
        "requested_runtime": requested,
        "active_runtime": active.name,
        "active": active_status,
        "available_runtimes": statuses,
        "env": {
            "AGENT_RUNTIME": os.getenv("AGENT_RUNTIME") or "",
            "AGENT_RUNTIME_ADAPTER": os.getenv("AGENT_RUNTIME_ADAPTER") or "",
            "AGENT_SDK_MODEL": os.getenv("AGENT_SDK_MODEL") or "",
            "OPENAI_DEFAULT_MODEL": os.getenv("OPENAI_DEFAULT_MODEL") or "",
        },
    }
