#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
from typing import Any


API_BASE = os.getenv("KOLNESS_API_BASE", "http://pr-ai-os-app:8601").rstrip("/")


def _load_api_token() -> str:
    token = os.getenv("OPENCLAW_ADMIN_TOKEN", "").strip()
    if token:
        return token
    token_file = Path(os.getenv("KOLNESS_API_TOKEN_FILE", "/home/node/.openclaw/gateway-token"))
    try:
        return token_file.read_text().strip()
    except OSError:
        return ""


API_TOKEN = _load_api_token()


TOOLS: dict[str, dict[str, Any]] = {
    "kolness_analyze_brief": {
        "path": "/api/openclaw/tools/kolness.analyze_brief",
        "description": "解析 PR brief，返回行业、产品、预算、阶段、目标用户和平台偏好。",
        "schema": {
            "type": "object",
            "properties": {"brief": {"type": "string", "description": "PR brief 原文"}},
            "required": ["brief"],
        },
    },
    "kolness_search_kol": {
        "path": "/api/openclaw/tools/kolness.search_kol",
        "description": "按关键词、平台、标签检索 Kolness 达人库。",
        "schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "platform": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
            },
            "required": ["query"],
        },
    },
    "kolness_get_creator_profile": {
        "path": "/api/openclaw/tools/kolness.get_creator_profile",
        "description": "按 creator_id、昵称或平台 ID 读取达人完整档案、标签和证据。",
        "schema": {
            "type": "object",
            "properties": {
                "creator_id": {"type": "string"},
                "name": {"type": "string"},
                "platform_user_id": {"type": "string"},
                "platform": {"type": "string"},
            },
        },
    },
    "kolness_tag_creator": {
        "path": "/api/openclaw/tools/kolness.tag_creator",
        "description": "根据分析结果更新达人标签、AI 摘要、备注和风险标签。",
        "schema": {
            "type": "object",
            "properties": {
                "creator_id": {"type": "string"},
                "name": {"type": "string"},
                "industry_fit_tags": {"type": "array", "items": {"type": "string"}},
                "content_capability_tags": {"type": "array", "items": {"type": "string"}},
                "risk_tags": {"type": "array", "items": {"type": "string"}},
                "ai_summary": {"type": "string"},
                "manual_notes": {"type": "string"},
            },
        },
    },
    "kolness_match_kol": {
        "path": "/api/openclaw/tools/kolness.match_kol",
        "description": "根据 brief 对达人库做 KOL 匹配排序。",
        "schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "string"},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 30},
            },
            "required": ["brief"],
        },
    },
    "kolness_generate_kol_graph": {
        "path": "/api/openclaw/tools/kolness.generate_kol_graph",
        "description": "根据 brief 和候选达人生成 KOL 决策图谱。",
        "schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "string"},
                "creator_ids": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
            "required": ["brief"],
        },
    },
    "kolness_generate_proposal": {
        "path": "/api/openclaw/tools/kolness.generate_proposal",
        "description": "根据 brief 和 KOL 匹配结果生成客户可读 Markdown 方案。",
        "schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "string"},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 30},
            },
            "required": ["brief"],
        },
    },
    "kolness_get_campaign_history": {
        "path": "/api/openclaw/tools/kolness.get_campaign_history",
        "description": "读取历史 Campaign、Agent Thread、客户方案和 Brief 分发沉淀。",
        "schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                "type": {"type": "string"},
            },
        },
    },
    "kolness_create_client_share_page": {
        "path": "/api/openclaw/tools/kolness.create_client_share_page",
        "description": "根据 brief 和 KOL 推荐生成甲方可访问的方案页。",
        "schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string"},
                "project_name": {"type": "string"},
                "brief": {"type": "string"},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 30},
            },
            "required": ["client_name", "project_name", "brief"],
        },
    },
    "kolness_save_campaign_asset": {
        "path": "/api/openclaw/tools/kolness.save_campaign_asset",
        "description": "把 OpenClaw 产物保存为 Kolness Agent artifact，后续可沉淀到 Campaign 资产库。",
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "artifact_type": {"type": "string"},
                "campaign_id": {"type": "string"},
                "summary": {"type": "string"},
                "content": {"type": "string"},
                "payload": {"type": "object"},
            },
            "required": ["title"],
        },
    },
}


def _send(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _error(request_id: Any, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def _tool_descriptions() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["schema"],
        }
        for name, spec in TOOLS.items()
    ]


def _call_kolness(path: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if not API_TOKEN:
        raise RuntimeError("OPENCLAW_ADMIN_TOKEN is not configured for Kolness MCP server")
    body = json.dumps(arguments or {}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Kolness API {exc.code}: {detail[:500]}") from exc


def _handle(request: dict[str, Any]) -> None:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        _send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": params.get("protocolVersion") or "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "kolness-mcp", "version": "0.1.0"},
                },
            }
        )
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        _send({"jsonrpc": "2.0", "id": request_id, "result": {"tools": _tool_descriptions()}})
        return

    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        spec = TOOLS.get(name)
        if spec is None:
            _error(request_id, -32602, f"Unknown tool: {name}")
            return
        try:
            result = _call_kolness(spec["path"], arguments)
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                        "isError": False,
                    },
                }
            )
        except Exception as exc:
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True},
                }
            )
        return

    if method in {"ping"}:
        _send({"jsonrpc": "2.0", "id": request_id, "result": {}})
        return

    _error(request_id, -32601, f"Method not found: {method}")


def main() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            _handle(request)
        except Exception as exc:
            print(f"kolness-mcp error: {exc}", file=sys.stderr, flush=True)
            _error(None, -32603, str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
