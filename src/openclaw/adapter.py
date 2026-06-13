from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from src.agent.schemas import now_iso
from src.openclaw.schemas import (
    OpenClawConfig,
    OpenClawEvent,
    OpenClawRun,
    OpenClawUserBinding,
    binding_id_for,
    event_id_for,
    run_id_for,
)
from src.openclaw.storage import load_binding, load_config, load_events_for_run, load_run, save_binding, save_event, save_run


class OpenClawAdapter:
    def __init__(self, timeout: int = 25) -> None:
        self.timeout = timeout

    def status(self, db_path: Path) -> dict[str, Any]:
        config = load_config(db_path)
        configured = bool(config.gateway_url)
        return {
            "enabled": bool(config.enabled),
            "configured": configured,
            "available": bool(config.enabled and configured),
            "gateway_url": config.gateway_url,
            "control_ui_url": config.control_ui_url,
            "default_agent_id": config.default_agent_id,
            "proxy_base_path": config.proxy_base_path,
            "message": "OpenClaw 已启用。" if config.enabled and configured else "OpenClaw 未启用或未配置 Gateway。",
        }

    def binding_for_user(self, db_path: Path, user_id: str) -> OpenClawUserBinding:
        config = load_config(db_path)
        existing = load_binding(db_path, user_id)
        if existing:
            return existing
        agent_id = f"kolness_{user_id}".replace("@", "_").replace(".", "_")[:80]
        binding = OpenClawUserBinding(
            binding_id=binding_id_for(user_id),
            user_id=user_id,
            openclaw_gateway_url=config.gateway_url,
            openclaw_agent_id=agent_id or config.default_agent_id,
            openclaw_session_id="",
        )
        save_binding(db_path, binding)
        return binding

    def start_chat(self, db_path: Path, user_id: str, message: str, campaign_id: str = "", session_id: str = "") -> dict[str, Any]:
        config = load_config(db_path)
        binding = self.binding_for_user(db_path, user_id)
        if session_id:
            binding.openclaw_session_id = session_id
        run = OpenClawRun(
            run_id=run_id_for(user_id, message),
            user_id=user_id,
            campaign_id=campaign_id,
            openclaw_agent_id=binding.openclaw_agent_id or config.default_agent_id,
            openclaw_session_id=binding.openclaw_session_id,
            status="running",
            message=message,
        )
        save_run(db_path, run)
        self._event(db_path, run.run_id, 1, "message.created", {"role": "user", "content": message})
        if not config.enabled or not config.gateway_url:
            run.status = "failed"
            run.error = "OpenClaw 未启用或未配置 Gateway URL。"
            run.updated_at = now_iso()
            save_run(db_path, run)
            self._event(db_path, run.run_id, 2, "run.failed", {"error": run.error})
            return self.payload(db_path, run.run_id)

        try:
            response = self._send_message(config, run, message)
            run.response = response.get("message") or response.get("response") or response.get("content") or "OpenClaw 已接收任务。"
            run.openclaw_session_id = response.get("session_id") or response.get("thread_id") or run.openclaw_session_id
            binding.openclaw_session_id = run.openclaw_session_id
            binding.updated_at = now_iso()
            save_binding(db_path, binding)
            run.status = "completed"
            run.updated_at = now_iso()
            save_run(db_path, run)
            self._event(db_path, run.run_id, 2, "tool.started", {"tool_name": "openclaw.gateway", "agent_id": run.openclaw_agent_id})
            self._event(db_path, run.run_id, 3, "message.completed", {"role": "assistant", "content": run.response})
            self._event(db_path, run.run_id, 4, "run.completed", {"session_id": run.openclaw_session_id})
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
            run.updated_at = now_iso()
            save_run(db_path, run)
            self._event(db_path, run.run_id, 2, "tool.failed", {"tool_name": "openclaw.gateway", "error": run.error})
            self._event(db_path, run.run_id, 3, "run.failed", {"error": run.error})
        return self.payload(db_path, run.run_id)

    def payload(self, db_path: Path, run_id: str) -> dict[str, Any]:
        run = load_run(db_path, run_id)
        if run is None:
            return {}
        events = [item.to_dict() for item in load_events_for_run(db_path, run_id)]
        return {"run": run.to_dict(), "events": events}

    def _send_message(self, config: OpenClawConfig, run: OpenClawRun, message: str) -> dict[str, Any]:
        url = config.gateway_url.rstrip("/")
        payload = {
            "agent_id": run.openclaw_agent_id or config.default_agent_id,
            "session_id": run.openclaw_session_id,
            "message": message,
            "metadata": {
                "source": "kolness",
                "run_id": run.run_id,
                "campaign_id": run.campaign_id,
                "tool_base_path": "/api/openclaw/tools",
                "tool_names": [
                    "kolness.analyze_brief",
                    "kolness.search_kol",
                    "kolness.match_kol",
                    "kolness.generate_kol_graph",
                    "kolness.generate_proposal",
                    "kolness.save_campaign_asset",
                ],
            },
        }
        headers = {"Content-Type": "application/json"}
        if config.admin_token:
            headers["Authorization"] = f"Bearer {config.admin_token}"
        # OpenClaw deployments can expose different HTTP facades. Try the explicit Kolness bridge first,
        # then common chat/message paths before surfacing a clear failure.
        errors: list[str] = []
        for path in ("/api/kolness/chat", "/api/chat", "/chat", "/message"):
            try:
                response = requests.post(f"{url}{path}", json=payload, headers=headers, timeout=self.timeout)
                if response.status_code == 404:
                    errors.append(f"{path}: 404")
                    continue
                response.raise_for_status()
                data = response.json() if response.content else {}
                return data if isinstance(data, dict) else {"response": str(data)}
            except requests.RequestException as exc:
                errors.append(f"{path}: {exc}")
        raise RuntimeError("OpenClaw Gateway 调用失败：" + " | ".join(errors[-3:]))

    def _event(self, db_path: Path, run_id: str, sequence: int, event_type: str, payload: dict[str, Any]) -> None:
        save_event(
            db_path,
            OpenClawEvent(
                event_id=event_id_for(run_id, sequence, event_type),
                run_id=run_id,
                sequence=sequence,
                event_type=event_type,
                payload=payload,
            ),
        )
