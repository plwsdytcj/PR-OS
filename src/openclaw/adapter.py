from __future__ import annotations

from pathlib import Path
import re
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
            self._event(db_path, run.run_id, 2, "gateway.started", {"tool_name": "openclaw.gateway", "agent_id": run.openclaw_agent_id})
            response = self._send_message(config, run, message)
            run.response = response.get("message") or response.get("response") or response.get("content") or "OpenClaw 已接收任务。"
            run.openclaw_session_id = response.get("session_id") or response.get("thread_id") or run.openclaw_session_id
            binding.openclaw_session_id = run.openclaw_session_id
            binding.updated_at = now_iso()
            save_binding(db_path, binding)
            run.status = "completed"
            run.updated_at = now_iso()
            save_run(db_path, run)
            self._event(db_path, run.run_id, 3, "gateway.completed", {"tool_name": "openclaw.gateway", "agent_id": run.openclaw_agent_id})
            next_sequence = self._record_response_events(db_path, run, response, start_sequence=4)
            self._event(db_path, run.run_id, next_sequence, "message.completed", {"role": "assistant", "content": run.response})
            self._event(db_path, run.run_id, next_sequence + 1, "run.completed", {"session_id": run.openclaw_session_id})
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
        # OpenClaw deployments can expose different HTTP facades. Try the explicit Kolness bridge first,
        # then the official OpenAI-compatible Gateway endpoint, then common chat/message paths.
        errors: list[str] = []
        for path in ("/api/kolness/chat",):
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
        payload = {
            "model": f"openclaw/{run.openclaw_agent_id}" if run.openclaw_agent_id else "openclaw/default",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Kolness PR Agent. Help PR teams turn briefs into KOL recommendations, "
                        "risk notes, and client-readable next steps. Use Kolness context from the user message."
                    ),
                },
                {"role": "user", "content": message},
            ],
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

    def _record_response_events(self, db_path: Path, run: OpenClawRun, response: dict[str, Any], start_sequence: int) -> int:
        sequence = start_sequence
        text = str(response.get("message") or response.get("response") or response.get("content") or run.response or "")
        recommended_kols = self._extract_kol_names(text)
        if recommended_kols:
            self._event(
                db_path,
                run.run_id,
                sequence,
                "kolness.match.completed",
                {
                    "tool_name": "kolness.match_kol",
                    "source": "agent_response",
                    "result_count": len(recommended_kols),
                    "recommended_kols": recommended_kols,
                },
            )
            sequence += 1
        if text:
            self._event(
                db_path,
                run.run_id,
                sequence,
                "artifact.preview.created",
                {
                    "artifact_type": "kol_recommendation",
                    "source": "agent_response",
                    "title": "KOL 推荐结果",
                    "preview": text[:900],
                },
            )
            sequence += 1
        return sequence

    def _extract_kol_names(self, text: str) -> list[str]:
        names: list[str] = []
        for line in text.splitlines():
            raw_value = line.strip()
            if not raw_value:
                continue
            structured_line = bool(re.match(r"^[\s>*-]*(\d+[.、)]\s*)", raw_value)) or bool(re.match(r"^[\s>*-]*(KOL|达人|账号)", raw_value, flags=re.IGNORECASE))
            if not structured_line:
                continue
            value = re.sub(r"^[\s>*-]*(\d+[.、)]\s*)?", "", raw_value).strip()
            value = value.replace("**", "").strip()
            match = re.match(r"^(?:KOL|达人|账号)?\s*([^：:，,。；;（）()\-|]{2,18})", value, flags=re.IGNORECASE)
            if not match:
                continue
            name = match.group(1).strip()
            if name in {"推荐以下", "推荐名单", "匹配理由", "主要风险", "下一步"}:
                continue
            if name and name not in names:
                names.append(name)
        return names[:8]

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
