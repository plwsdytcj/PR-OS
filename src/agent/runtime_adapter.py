from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from dotenv import load_dotenv

from src.agent import runtime as custom_runtime
from src.agent import sdk_runtime
from src.agent.schemas import AgentEvent, event_id_for, now_iso
from src.agent.storage import load_events_for_run, load_run, upsert_event


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

    Phase 7I-B enables a real SDK orchestration POC when the SDK package and a
    compatible API key are configured. If either is missing, or SDK execution
    fails, PR OS delegates back to the native runtime.
    """

    name = OPENAI_AGENTS_RUNTIME
    package_name = "agents"

    def status(self) -> RuntimeAdapterStatus:
        package_found = importlib.util.find_spec(self.package_name) is not None
        package_available = _sdk_package_importable()
        configured = bool(_sdk_api_key())
        if package_available and configured:
            message = "OpenAI Agents SDK package/config detected; Phase 7I-B will execute the SDK POC path and fall back to native runtime on failure."
            mode = "sdk_ready"
        elif package_available:
            message = "OpenAI Agents SDK package detected, but no compatible API key is configured; native PR OS runtime will execute."
            mode = "sdk_missing_key_delegate"
        elif package_found:
            message = "OpenAI Agents SDK package was found but is not importable; native PR OS runtime will execute."
            mode = "sdk_import_failed_delegate"
        else:
            message = "OpenAI Agents SDK package is not installed; native PR OS runtime will execute."
            mode = "sdk_missing_delegate"
        return RuntimeAdapterStatus(
            name=self.name,
            active=True,
            available=package_available and configured,
            mode=mode,
            message=message,
            package=self.package_name,
            model=os.getenv("AGENT_SDK_MODEL") or os.getenv("OPENAI_DEFAULT_MODEL") or os.getenv("AGENT_MODEL") or os.getenv("GLM_MODEL") or "",
            fallback_runtime=CUSTOM_RUNTIME,
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
        started = custom_runtime.start_agent_chat(
            db_path,
            message=message,
            task_id=task_id,
            client_name=client_name,
            project_name=project_name,
            top_n=top_n,
            created_by=created_by,
            require_plan_approval=require_plan_approval,
        )
        self.execute_run(db_path, started["run"]["run_id"], top_n=top_n, require_plan_approval=require_plan_approval)
        return custom_runtime.get_agent_run(db_path, started["run"]["run_id"]) or started

    def execute_run(self, db_path: Path, run_id: str, top_n: int = 8, require_plan_approval: bool = False) -> None:
        if not self.status().available:
            custom_runtime.execute_agent_run(db_path, run_id, top_n=top_n, require_plan_approval=require_plan_approval)
            return
        try:
            sdk_runtime.execute_agent_run_with_sdk(db_path, run_id, top_n=top_n, require_plan_approval=require_plan_approval)
        except Exception as exc:
            _record_sdk_fallback_event(db_path, run_id, exc)
            custom_runtime.execute_agent_run(db_path, run_id, top_n=top_n, require_plan_approval=require_plan_approval)


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
            "AGENT_SDK_BASE_URL": os.getenv("AGENT_SDK_BASE_URL") or "",
            "AGENT_SDK_MAX_TURNS": os.getenv("AGENT_SDK_MAX_TURNS") or "",
            "AGENT_SDK_TRACING": os.getenv("AGENT_SDK_TRACING") or "",
            "OPENAI_DEFAULT_MODEL": os.getenv("OPENAI_DEFAULT_MODEL") or "",
        },
    }


def _sdk_api_key() -> str:
    load_dotenv()
    return (
        os.getenv("AGENT_SDK_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("AGENT_API_KEY")
        or os.getenv("GLM_API_KEY")
        or ""
    )


def _sdk_package_importable() -> bool:
    if importlib.util.find_spec(OpenAIAgentsRuntimeAdapter.package_name) is None:
        return False
    try:
        import agents  # noqa: F401
        return True
    except Exception:
        return False


def _record_sdk_fallback_event(db_path: Path, run_id: str, exc: Exception) -> None:
    run = load_run(db_path, run_id)
    if run is None:
        return
    sequence = len(load_events_for_run(db_path, run_id)) + 1
    upsert_event(
        db_path,
        AgentEvent(
            event_id=event_id_for(run_id, sequence, "SDK 回退原生 Runtime"),
            run_id=run_id,
            task_id=run.task_id,
            sequence=sequence,
            event_type="sdk_runtime",
            status="failed",
            title="SDK 回退原生 Runtime",
            summary=f"OpenAI Agents SDK 执行失败，已回退原生 runtime：{type(exc).__name__}",
            tool_name="openai_agents",
            payload={"error_type": type(exc).__name__, "error": str(exc)[:500], "fallback_runtime": CUSTOM_RUNTIME},
            created_at=now_iso(),
        ),
    )
