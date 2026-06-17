from __future__ import annotations

from pathlib import Path
import re
from typing import Any

try:
    import requests
except ModuleNotFoundError:
    class _MissingRequests:
        RequestException = Exception

        @staticmethod
        def post(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("Python package 'requests' is required for real OpenClaw Gateway calls.")

    requests = _MissingRequests()  # type: ignore[assignment]

from src.agent.schemas import now_iso
from src.openclaw.schemas import (
    OpenClawConfig,
    OpenClawEvent,
    OpenClawRun,
    OpenClawSession,
    OpenClawUserBinding,
    binding_id_for,
    event_id_for,
    run_id_for,
    session_id_for,
)
from src.openclaw.storage import load_binding, load_config, load_events_for_run, load_run, load_session, save_binding, save_event, save_run, save_session


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

    def create_session(self, db_path: Path, user_id: str, title: str = "", openclaw_session_id: str = "") -> OpenClawSession:
        config = load_config(db_path)
        binding = self.binding_for_user(db_path, user_id)
        session = OpenClawSession(
            session_id=session_id_for(user_id, title),
            user_id=user_id,
            title=title.strip()[:80] or "新对话",
            openclaw_agent_id=binding.openclaw_agent_id or config.default_agent_id,
            openclaw_session_id=openclaw_session_id.strip(),
            status="ready",
        )
        save_session(db_path, session)
        return session

    def session_for_chat(self, db_path: Path, user_id: str, session_record_id: str = "", title: str = "", openclaw_session_id: str = "") -> OpenClawSession:
        if session_record_id:
            existing = load_session(db_path, session_record_id)
            if existing and existing.user_id == user_id:
                if openclaw_session_id and not existing.openclaw_session_id:
                    existing.openclaw_session_id = openclaw_session_id
                    existing.updated_at = now_iso()
                    save_session(db_path, existing)
                return existing
        return self.create_session(db_path, user_id, title=title, openclaw_session_id=openclaw_session_id)

    def create_chat(
        self,
        db_path: Path,
        user_id: str,
        message: str,
        campaign_id: str = "",
        session_id: str = "",
        session_record_id: str = "",
        history: list[dict[str, str]] | None = None,
    ) -> OpenClawRun:
        config = load_config(db_path)
        binding = self.binding_for_user(db_path, user_id)
        session = self.session_for_chat(db_path, user_id, session_record_id=session_record_id, title=message, openclaw_session_id=session_id)
        if session.openclaw_session_id:
            binding.openclaw_session_id = session.openclaw_session_id
        run = OpenClawRun(
            run_id=run_id_for(user_id, message),
            user_id=user_id,
            session_id=session.session_id,
            campaign_id=campaign_id,
            openclaw_agent_id=session.openclaw_agent_id or binding.openclaw_agent_id or config.default_agent_id,
            openclaw_session_id=session.openclaw_session_id,
            status="running",
            message=message,
            history=self._normalize_history(history or []),
        )
        session.status = "running"
        session.updated_at = now_iso()
        save_session(db_path, session)
        save_run(db_path, run)
        self._event(db_path, run.run_id, 1, "message.created", {"role": "user", "content": message})
        return run

    def start_chat(
        self,
        db_path: Path,
        user_id: str,
        message: str,
        campaign_id: str = "",
        session_id: str = "",
        session_record_id: str = "",
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        run = self.create_chat(db_path, user_id, message, campaign_id=campaign_id, session_id=session_id, session_record_id=session_record_id, history=history)
        return self.complete_chat(db_path, run.run_id)

    def start_chat_async(
        self,
        db_path: Path,
        user_id: str,
        message: str,
        campaign_id: str = "",
        session_id: str = "",
        session_record_id: str = "",
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        run = self.create_chat(db_path, user_id, message, campaign_id=campaign_id, session_id=session_id, session_record_id=session_record_id, history=history)
        return self.payload(db_path, run.run_id)

    def complete_chat(self, db_path: Path, run_id: str) -> dict[str, Any]:
        config = load_config(db_path)
        run = load_run(db_path, run_id)
        if run is None:
            return {}
        if run.status != "running":
            return self.payload(db_path, run.run_id)
        binding = self.binding_for_user(db_path, run.user_id)
        if not config.enabled or not config.gateway_url:
            run.status = "failed"
            run.error = "OpenClaw 未启用或未配置 Gateway URL。"
            run.updated_at = now_iso()
            save_run(db_path, run)
            self._update_session_from_run(db_path, run)
            self._event(db_path, run.run_id, self._next_sequence(db_path, run.run_id), "run.failed", {"error": run.error})
            return self.payload(db_path, run.run_id)

        try:
            self._event(db_path, run.run_id, self._next_sequence(db_path, run.run_id), "gateway.started", {"tool_name": "openclaw.gateway", "agent_id": run.openclaw_agent_id})
            response = self._send_message(config, run, run.message)
            run.response = response.get("message") or response.get("response") or response.get("content") or "OpenClaw 已接收任务。"
            run.openclaw_session_id = response.get("session_id") or response.get("thread_id") or run.openclaw_session_id
            binding.openclaw_session_id = run.openclaw_session_id
            binding.updated_at = now_iso()
            save_binding(db_path, binding)
            save_run(db_path, run)
            self._update_session_from_run(db_path, run)
            self._event(db_path, run.run_id, self._next_sequence(db_path, run.run_id), "gateway.completed", {"tool_name": "openclaw.gateway", "agent_id": run.openclaw_agent_id})
            next_sequence = self._next_sequence(db_path, run.run_id)
            self._event(db_path, run.run_id, next_sequence, "message.completed", {"role": "assistant", "content": run.response})
            self._event(db_path, run.run_id, next_sequence + 1, "run.completed", {"session_id": run.openclaw_session_id})
            run.status = "completed"
            run.updated_at = now_iso()
            save_run(db_path, run)
            self._update_session_from_run(db_path, run)
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
            run.updated_at = now_iso()
            save_run(db_path, run)
            self._update_session_from_run(db_path, run)
            sequence = self._next_sequence(db_path, run.run_id)
            self._event(db_path, run.run_id, sequence, "tool.failed", {"tool_name": "openclaw.gateway", "error": run.error})
            self._event(db_path, run.run_id, sequence + 1, "run.failed", {"error": run.error})
        return self.payload(db_path, run.run_id)

    def payload(self, db_path: Path, run_id: str) -> dict[str, Any]:
        run = load_run(db_path, run_id)
        if run is None:
            return {}
        events = [item.to_dict() for item in load_events_for_run(db_path, run_id)]
        return {"run": run.to_dict(), "events": events}

    def _update_session_from_run(self, db_path: Path, run: OpenClawRun) -> None:
        if not run.session_id:
            return
        session = load_session(db_path, run.session_id)
        if session is None:
            return
        session.status = run.status
        session.openclaw_session_id = run.openclaw_session_id or session.openclaw_session_id
        if session.title == "新对话" and run.message:
            session.title = run.message.strip().replace("\n", " ")[:80]
        session.updated_at = now_iso()
        save_session(db_path, session)

    def _send_message(self, config: OpenClawConfig, run: OpenClawRun, message: str) -> dict[str, Any]:
        url = config.gateway_url.rstrip("/")
        bridge_payload = {
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
                    "kolness.get_creator_profile",
                    "kolness.tag_creator",
                    "kolness.match_kol",
                    "kolness.generate_kol_graph",
                    "kolness.generate_proposal",
                    "kolness.get_campaign_history",
                    "kolness.create_client_share_page",
                    "kolness.save_campaign_asset",
                ],
            },
        }
        headers = {"Content-Type": "application/json"}
        if config.admin_token:
            headers["Authorization"] = f"Bearer {config.admin_token}"
        # The production path is the real OpenClaw Gateway. Kolness only supplies tools/MCP;
        # it must not answer through the local bridge before OpenClaw has a chance to run.
        errors: list[str] = []
        try:
            return self._send_chat_completions(url, headers, run, message)
        except requests.RequestException as exc:
            errors.append(f"/v1/chat/completions: {exc}")
        except RuntimeError as exc:
            errors.append(f"/v1/chat/completions: {exc}")
        for path in ("/api/chat", "/chat", "/message"):
            try:
                response = requests.post(f"{url}{path}", json=bridge_payload, headers=headers, timeout=self.timeout)
                if response.status_code == 404:
                    errors.append(f"{path}: 404")
                    continue
                response.raise_for_status()
                data = response.json() if response.content else {}
                return data if isinstance(data, dict) else {"response": str(data)}
            except requests.RequestException as exc:
                errors.append(f"{path}: {exc}")
        raise RuntimeError("OpenClaw Gateway 调用失败：" + " | ".join(errors[-3:]))

    def _send_chat_completions(self, url: str, headers: dict[str, str], run: OpenClawRun, message: str) -> dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Kolness PR Agent. Help PR teams turn briefs into KOL recommendations, "
                    "risk notes, and client-readable next steps. Use the available Kolness tools when "
                    "the user asks for creator data, KOL matching, proposals, client pages, or campaign assets. "
                    "Do not answer with a plan or say you will do the work later. Return concrete deliverables in "
                    "the current response: recommended KOLs, matching reasons, budget guidance, risks, and next steps. "
                    "If the required Kolness tools or data are unavailable, say that clearly and ask for the missing input."
                ),
            },
        ]
        messages.extend(self._normalize_history(run.history))
        messages.append({"role": "user", "content": message})
        payload = {
            "model": "openclaw",
            "messages": messages,
            "user": run.openclaw_session_id or run.run_id,
            "stream": False,
        }
        request_headers = dict(headers)
        if run.openclaw_session_id:
            request_headers["x-openclaw-session-key"] = run.openclaw_session_id
        if run.openclaw_agent_id:
            request_headers["x-openclaw-agent-id"] = run.openclaw_agent_id
        response = requests.post(f"{url}/v1/chat/completions", json=payload, headers=request_headers, timeout=max(self.timeout, 60))
        if response.status_code == 404:
            raise RuntimeError("404")
        response.raise_for_status()
        data = response.json() if response.content else {}
        choices = data.get("choices") if isinstance(data, dict) else []
        first = choices[0] if choices else {}
        message_payload = first.get("message") or {}
        content = message_payload.get("content") if isinstance(message_payload, dict) else ""
        session_id = response.headers.get("x-openclaw-session-key") or run.openclaw_session_id
        return {"response": content or "OpenClaw 已完成任务。", "session_id": session_id, "raw": data}

    def _normalize_history(self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for item in history[-12:]:
            role = str(item.get("role") or "").strip().lower()
            content = str(item.get("content") or "").strip()
            if role not in {"user", "assistant"} or not content:
                continue
            messages.append({"role": role, "content": content[:4000]})
        return messages

    def _extract_kol_names(self, text: str) -> list[str]:
        names: list[str] = []
        for line in text.splitlines():
            raw_value = line.strip()
            if not raw_value:
                continue
            structured_line = bool(re.match(r"^[\s>*-]*(\d+[.、)]\s*)", raw_value)) or bool(re.match(r"^[\s>*-]*(KOL(?!ness)|达人|账号)\b", raw_value, flags=re.IGNORECASE))
            if not structured_line:
                continue
            value = re.sub(r"^[\s>*-]*(\d+[.、)]\s*)?", "", raw_value).strip()
            value = value.replace("**", "").strip()
            match = re.match(r"^(?:KOL(?!ness)|达人|账号)?\s*([^：:，,。；;（）()\-|]{2,18})", value, flags=re.IGNORECASE)
            if not match:
                continue
            name = match.group(1).strip()
            if name in {"推荐以下", "推荐名单", "匹配理由", "主要风险", "下一步"} or re.search(r"Kolness|OpenClaw|Bridge", name, flags=re.IGNORECASE):
                continue
            if name and name not in names:
                names.append(name)
        return names[:8]

    def _next_sequence(self, db_path: Path, run_id: str) -> int:
        events = load_events_for_run(db_path, run_id)
        return max((event.sequence for event in events), default=0) + 1

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
