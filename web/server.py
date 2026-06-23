from __future__ import annotations

import contextvars
import asyncio
import base64
import html
import json
import os
import re
import secrets
import sys
from dataclasses import asdict
from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import requests
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.auth.schemas import CLIENT_ROLES, INTERNAL_ROLES, AuthUser, Identity
from src.auth.service import (
    can_access_proposal,
    create_client_account,
    create_session,
    create_user,
    grant_project_access,
    link_client_user,
    logout_session,
    resolve_identity,
    reset_user_password,
    role_can,
    update_user,
    users_exist,
)
from src.auth.storage import init_auth_db, load_all_clients, load_all_project_access, load_all_users, load_client_users_for_client, load_user
from src.agent.runtime import (
    approve_agent_run,
    cancel_agent_run,
    commit_agent_memory_suggestion,
    create_agent_thread,
    get_agent_run,
    get_agent_task,
    get_agent_thread,
    list_agent_tasks,
    list_agent_threads,
    update_agent_step_control,
)
from src.agent.runtime_adapter import CUSTOM_RUNTIME, OPENAI_AGENTS_RUNTIME, get_runtime_adapter, requested_runtime_name, runtime_status as agent_runtime_status
from src.agent.schemas import AgentArtifact, artifact_id_for
from src.agent.storage import upsert_artifact
from src.agent.storage import init_agent_db
from src.connectors.excel_connector import load_table_file
from src.connectors.link_connector import parse_links
from src.connectors.mock_api_connector import MockApiConnector
from src.connectors.oneapi_connector import OneApiConnector
from src.brief_distribution.service import (
    apply_response_to_creator,
    client_response_view,
    create_distribution_brief,
    distribution_summary,
    mark_recipient_viewed,
    push_distribution_brief,
    submit_creator_response,
)
from src.brief_distribution.storage import (
    init_distribution_db,
    load_all_distribution_briefs,
    load_distribution_brief,
    load_distribution_brief_by_token,
    load_responses_for_brief,
    upsert_distribution_brief,
)
from src.collaboration.schemas import DEFAULT_VISIBLE_FIELDS, Proposal, ProposalVersion, default_expires_at, version_id_for
from src.collaboration.service import (
    create_proposal_from_brief,
    public_proposal_payload,
    record_feedback,
    update_candidate_decision,
    update_preference_from_feedback,
)
from src.collaboration.storage import (
    init_collaboration_db,
    load_all_proposals,
    load_feedback,
    load_feedback_item,
    load_preference,
    load_proposal,
    load_proposal_by_token,
    load_version,
    load_versions,
    upsert_feedback,
    upsert_preference,
    upsert_proposal,
    upsert_version,
)
from src.creator_commercial.service import (
    create_creator_invitation,
    create_creator_submission,
    mark_invitation_opened,
    review_creator_submission,
    save_creator_case,
)
from src.creator_commercial.storage import (
    delete_case,
    delete_cases_for_creator,
    init_creator_commercial_db,
    load_all_cases,
    load_all_commercial_profiles,
    load_all_invitations,
    load_all_submissions,
    load_case,
    load_commercial_profile,
    load_invitation,
    load_invitation_by_token,
    load_submission,
    load_submissions_for_creator,
    upsert_invitation,
)
from src.intelligence.brief_parser import parse_brief
from src.intelligence.data_quality import find_duplicate_candidates, governance_summary, quality_issues, strong_dedupe_profiles
from src.intelligence.matching import rank_creators
from src.intelligence.creator_multimodal import analyze_creator_image
from src.intelligence.profiling import enrich_profiles
from src.intelligence.tag_classifier import classify_creator_tags
from src.knowledge.service import create_knowledge_document, knowledge_document_detail, knowledge_stats, list_knowledge_documents, search_knowledge_base
from src.knowledge.storage import init_knowledge_db
from src.kol_intelligence.service import (
    analyze_creator_evidence_tags,
    build_kol_knowledge_graph,
    bulk_review_evidence_tags,
    evidence_review_queue,
    kol_intelligence_snapshot,
    list_creator_evidence_tags,
    predict_kol_fit,
    preview_creator_intelligence,
    review_evidence_tag,
    run_conversational_kol_graph,
)
from src.kol_intelligence.storage import init_kol_intelligence_db
from src.normalize.mapper import infer_column_mapping, map_dataframe_to_profiles
from src.openclaw.adapter import OpenClawAdapter
from src.openclaw.schemas import OpenClawConfig, OpenClawSession, OpenClawUserBinding, binding_id_for, now_iso as openclaw_now_iso
from src.openclaw.storage import (
    init_openclaw_db,
    load_all_bindings,
    load_all_runs as load_all_openclaw_runs,
    load_config as load_openclaw_config,
    load_events_for_run as load_openclaw_events_for_run,
    load_run as load_openclaw_run,
    load_runs_for_session as load_openclaw_runs_for_session,
    load_session as load_openclaw_session,
    load_sessions_for_user as load_openclaw_sessions_for_user,
    save_binding as save_openclaw_binding,
    save_config as save_openclaw_config,
    save_session as save_openclaw_session,
)
from src.platform_os.service import (
    add_post_campaign_review,
    campaign_room,
    campaign_os_snapshot,
    create_campaign_project,
    create_distribution_from_campaign,
    platform_dashboard,
    run_campaign_plan_simulation,
)
from src.platform_os.storage import init_platform_db, load_all_campaign_projects, load_campaign_project, upsert_campaign_project
from src.project_run.service import run_pr_project
from src.report.proposal_generator import generate_markdown_proposal
from src.rules.storage import init_rule_db, load_rule_config, reset_rule_config, save_rule_config
from src.schemas import CreatorProfile, split_tags, stable_id
from src.simulation.llm_fallback import LlmFallbackStressTest
from src.simulation.mirofish_adapter import MiroFishCliAdapter
from src.llm.glm_client import GlmClient
from src.storage.db import count_profiles, delete_profiles, init_db, load_profile, load_profiles, merge_profiles, replace_profiles, save_profile, upsert_profiles
from src.storage.import_templates import (
    apply_template_mapping,
    delete_template,
    find_best_template,
    load_templates,
    upsert_template,
)
from src.storage.object_store import get_object_store, guess_content_type, make_upload_key
from src.storage.postgres_payload import tenant_from_path
from src.storage.runtime import storage_runtime_status
from src.symbolic.brand_profiler import generate_brand_symbolic_profile
from src.symbolic.creator_profiler import generate_creator_symbolic_profile
from src.symbolic.narrative_path import generate_narrative_path
from src.symbolic.os_schemas import SignifierTag, tag_id_for
from src.symbolic.os_service import calibrate_brand_with_symbolic_context, create_brand_creator_match_assets, create_content_narrative_assets, generate_product_symbolic_profile, generate_social_symbolic_report, symbolic_os_snapshot
from src.symbolic.os_storage import (
    init_symbolic_os_db,
    load_all_brand_creator_matches,
    load_all_content_narratives,
    load_all_product_symbolic,
    load_all_social_reports,
    load_all_signifier_tags,
    load_content_narrative,
    load_brand_creator_match,
    load_product_symbolic,
    upsert_content_narrative,
    upsert_brand_creator_match,
    upsert_product_symbolic,
    upsert_signifier_tag,
)
from src.symbolic.schemas import BrandSymbolicProfile, CreatorSymbolicProfile
from src.symbolic.storage import (
    init_symbolic_db,
    load_all_brand_symbolic,
    load_all_creator_symbolic,
    load_brand_symbolic,
    load_creator_symbolic,
    upsert_brand_symbolic,
    upsert_creator_symbolic,
)
from src.symbolic.symbolic_matching import rank_symbolic_creators


DEFAULT_DB_PATH = ROOT / "data" / "processed" / "phase1_web.sqlite3"
DEFAULT_TEMPLATE_PATH = ROOT / "data" / "processed" / "import_templates.json"
TENANT_ROOT = ROOT / "data" / "processed" / "tenants"
ACCESS_KEY = os.getenv("PR_AI_OS_ACCESS_KEY", "").strip()
AUTH_ENABLED = os.getenv("PR_AI_OS_AUTH_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
AUTH_COOKIE_NAME = "pr_ai_os_session"
PUBLIC_PATH_PREFIXES = ("/", "/static/", "/favicon.ico", "/creator/brief/", "/creator/invite/")
PUBLIC_API_PREFIXES = ("/api/client/share/", "/api/creator/brief/", "/api/creator/invite/")
_TENANT_RE = re.compile(r"[^a-zA-Z0-9_-]+")
_db_path_ctx: contextvars.ContextVar[Path] = contextvars.ContextVar("db_path", default=DEFAULT_DB_PATH)
_template_path_ctx: contextvars.ContextVar[Path] = contextvars.ContextVar("template_path", default=DEFAULT_TEMPLATE_PATH)
_identity_ctx: contextvars.ContextVar[Any] = contextvars.ContextVar("identity", default=None)
_AGENT_IMPORT_STAGING: dict[str, dict[str, Any]] = {}


class ContextPath(PathLike[str]):
    def __init__(self, ctx: contextvars.ContextVar[Path]) -> None:
        self.ctx = ctx

    @property
    def current(self) -> Path:
        return self.ctx.get()

    @property
    def parent(self) -> Path:
        return self.current.parent

    def __fspath__(self) -> str:
        return str(self.current)

    def __str__(self) -> str:
        return str(self.current)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.current, name)


DB_PATH = ContextPath(_db_path_ctx)
TEMPLATE_PATH = ContextPath(_template_path_ctx)
STATIC_DIR = ROOT / "web" / "static"

app = FastAPI(title="PR AI OS Phase 1 Web API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _sanitize_tenant(value: str | None) -> str:
    tenant = _TENANT_RE.sub("-", (value or "default").strip()).strip("-").lower()
    return tenant[:48] or "default"


def _tenant_paths(tenant: str) -> tuple[Path, Path]:
    if tenant == "default":
        return DEFAULT_DB_PATH, DEFAULT_TEMPLATE_PATH
    tenant_dir = TENANT_ROOT / tenant
    return tenant_dir / "phase1_web.sqlite3", tenant_dir / "import_templates.json"


def _init_db_bundle(path: Path | PathLike[str]) -> None:
    init_db(path)
    init_rule_db(path)
    init_agent_db(path)
    init_knowledge_db(path)
    init_kol_intelligence_db(path)
    init_auth_db(path)
    init_symbolic_db(path)
    init_symbolic_os_db(path)
    init_collaboration_db(path)
    init_creator_commercial_db(path)
    init_distribution_db(path)
    init_platform_db(path)
    init_openclaw_db(path)


_init_db_bundle(DB_PATH)


def _auth_required_for(path: str, db_path: Path) -> bool:
    if not AUTH_ENABLED and not users_exist(db_path):
        return False
    if path == "/api/status":
        return False
    if path.startswith("/api/auth/login") or path.startswith("/api/auth/bootstrap-admin") or path.startswith("/api/auth/me"):
        return False
    if path == "/" or path.startswith(PUBLIC_PATH_PREFIXES[1:]):
        return False
    if path.startswith(PUBLIC_API_PREFIXES):
        return False
    return path.startswith("/api/")


def _access_key_valid(request: Request) -> bool:
    if not ACCESS_KEY:
        return False
    return request.headers.get("X-Access-Key", "") == ACCESS_KEY


def _path_allowed_for_identity(path: str, method: str, identity: Any) -> bool:
    if identity is None:
        return False
    user = identity.user
    if user.user_type == "internal":
        if method in {"POST", "PUT", "PATCH", "DELETE"} and (path.startswith("/api/settings/") or path.startswith("/api/import/") or "/archive" in path):
            return role_can(user, "write")
        if method in {"POST", "PUT", "PATCH", "DELETE"} and request_write_method_hint(path):
            return role_can(user, "write")
        return role_can(user, "read") or role_can(user, "write")
    if user.user_type == "client":
        return path.startswith("/api/client/portal/") or path.startswith("/api/auth/")
    return False


def request_write_method_hint(path: str) -> bool:
    return any(
        marker in path
        for marker in [
            "/project-run",
            "/recommend",
            "/collaboration/",
            "/platform/",
            "/kol-intelligence/",
            "/symbolic/",
            "/distribution/",
            "/creator-commercial/",
            "/kol-intake",
        ]
    )


def current_identity() -> Any:
    return _identity_ctx.get()


def require_identity() -> Any:
    identity = current_identity()
    if identity is None:
        if not _auth_mode_active(_db_path_ctx.get()):
            return _open_mode_identity()
        raise HTTPException(status_code=401, detail="login required")
    return identity


def require_internal(action: str = "read") -> Any:
    identity = require_identity()
    if identity.user.user_type != "internal" or not role_can(identity.user, action):
        raise HTTPException(status_code=403, detail="permission denied")
    return identity


def require_admin() -> Any:
    identity = require_identity()
    if identity.user.user_type != "internal" or identity.user.role != "admin":
        raise HTTPException(status_code=403, detail="admin required")
    return identity


def _open_mode_identity() -> Identity:
    return Identity(
        user=AuthUser(
            user_id="open_demo_admin",
            email="open-demo@pr-ai-os.local",
            name="Open Demo",
            user_type="internal",
            role="admin",
            identity_provider="open",
            external_user_id="open_demo_admin",
        ),
        provider="open",
    )


def _session_cookie_kwargs() -> dict[str, Any]:
    return {
        "httponly": True,
        "path": "/",
        "samesite": "lax",
        "secure": os.getenv("PR_AI_OS_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
    }


def _auth_bypass_for_access_key(request: Request) -> bool:
    return _access_key_valid(request)


def _auth_bypass_for_openclaw_tool_token(request: Request, db_path: Path) -> bool:
    path = request.url.path
    if path.startswith("/api/kolness/chat") and request.client and request.client.host in {"127.0.0.1", "::1", "localhost"}:
        return True
    if not path.startswith("/api/openclaw/tools") and not path.startswith("/api/kolness/chat"):
        return False
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
    if not token:
        return False
    config = load_openclaw_config(db_path)
    return bool(config.admin_token and secrets.compare_digest(token, config.admin_token))


def _auth_mode_active(db_path: Path) -> bool:
    return AUTH_ENABLED or users_exist(db_path)


def _public_status_auth_required(db_path: Path) -> bool:
    return _auth_mode_active(db_path)


def _auth_required_message(db_path: Path) -> str:
    return "login required" if _auth_mode_active(db_path) else "access key required"


def _legacy_access_key_required_for(path: str) -> bool:
    if not ACCESS_KEY:
        return False
    if path == "/api/status":
        return False
    if path == "/" or path.startswith(PUBLIC_PATH_PREFIXES[1:]):
        return False
    if path.startswith(PUBLIC_API_PREFIXES):
        return False
    return path.startswith("/api/")


@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    tenant = _sanitize_tenant(request.headers.get("X-Tenant-ID") or request.query_params.get("tenant"))
    db_path, template_path = _tenant_paths(tenant)
    _init_db_bundle(db_path)
    db_token = _db_path_ctx.set(db_path)
    template_token = _template_path_ctx.set(template_path)
    identity_token = None
    try:
        identity = resolve_identity(db_path, request.cookies.get(AUTH_COOKIE_NAME, ""))
        identity_token = _identity_ctx.set(identity)
        if _legacy_access_key_required_for(request.url.path) and not _auth_mode_active(db_path) and not _access_key_valid(request):
            return JSONResponse({"detail": "access key required"}, status_code=401)
        service_token_bypass = _auth_bypass_for_openclaw_tool_token(request, db_path)
        if _auth_required_for(request.url.path, db_path) and not _auth_bypass_for_access_key(request) and not service_token_bypass:
            if identity is None:
                return JSONResponse({"detail": _auth_required_message(db_path)}, status_code=401)
            if not _path_allowed_for_identity(request.url.path, request.method.upper(), identity):
                return JSONResponse({"detail": "permission denied"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Tenant-ID"] = tenant
        return response
    finally:
        if identity_token is not None:
            _identity_ctx.reset(identity_token)
        _db_path_ctx.reset(db_token)
        _template_path_ctx.reset(template_token)


def profile_payload(profile: CreatorProfile) -> dict[str, Any]:
    data = asdict(profile)
    data["tags"] = {
        "industry": profile.industry_fit_tags,
        "identity": getattr(profile, "identity_tags", []),
        "capability": profile.content_capability_tags,
        "goal": profile.suitable_goals,
        "stage": profile.suitable_stages,
        "budget": profile.budget_fit_tags,
        "risk": profile.risk_tags,
        "delivery": getattr(profile, "delivery_tags", []),
        "personal": getattr(profile, "personal_tags", []),
    }
    data["narrative_position"] = getattr(profile, "narrative_position", "")
    return data


CREATOR_PAYLOAD_FIELDS = {
    "name",
    "platform",
    "platform_user_id",
    "homepage_url",
    "avatar_url",
    "bio",
    "region",
    "follower_count",
    "following_count",
    "total_likes",
    "recent_posts_count",
    "avg_likes",
    "avg_comments",
    "avg_shares",
    "avg_collections",
    "engagement_rate",
    "like_fan_ratio",
    "listed_price",
    "price_source",
    "contact",
    "cooperation_brands",
    "cooperation_formats",
    "delivery_rating",
    "communication_rating",
    "negotiation_space",
    "manual_notes",
    "industry_fit_tags",
    "identity_tags",
    "content_capability_tags",
    "suitable_goals",
    "suitable_stages",
    "budget_fit_tags",
    "risk_tags",
    "personal_tags",
    "delivery_tags",
    "narrative_position",
    "ai_summary",
}


def _apply_creator_payload(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    for field in CREATOR_PAYLOAD_FIELDS:
        if field not in payload:
            continue
        value = payload[field]
        if field in {"follower_count", "following_count", "total_likes", "recent_posts_count", "avg_likes", "avg_comments", "avg_shares", "avg_collections", "listed_price"}:
            data[field] = int(value or 0)
        elif field in {"engagement_rate", "delivery_rating", "communication_rating", "like_fan_ratio"}:
            data[field] = float(value or 0)
        elif field in {"cooperation_brands", "cooperation_formats", "industry_fit_tags", "identity_tags", "content_capability_tags", "suitable_goals", "suitable_stages", "budget_fit_tags", "risk_tags", "personal_tags", "delivery_tags"}:
            if isinstance(value, list):
                data[field] = [str(item).strip() for item in value if str(item).strip()]
            else:
                data[field] = split_tags(value)
        else:
            data[field] = str(value or "").strip()
    return data


IMPORT_FIELDS = [
    ("name", "达人名", True),
    ("platform", "平台", False),
    ("platform_user_id", "平台 ID", False),
    ("homepage_url", "主页链接", False),
    ("bio", "简介", False),
    ("region", "地区", False),
    ("follower_count", "粉丝数", False),
    ("listed_price", "报价", False),
    ("cooperation_brands", "合作品牌", False),
    ("cooperation_formats", "合作形式 / 标签", False),
    ("manual_notes", "备注", False),
]


def _safe_cell(value: Any) -> str | int | float:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


def _preview_rows(df: pd.DataFrame, limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in df.head(limit).to_dict(orient="records"):
        rows.append({str(key): _safe_cell(value) for key, value in row.items()})
    return rows


def _build_import_review(tables: dict[str, pd.DataFrame], template: dict[str, Any] | None = None) -> dict[str, Any]:
    sheets = []
    for sheet_name, df in tables.items():
        detected_mapping = infer_column_mapping(df)
        mapping, applied_template_name = apply_template_mapping(sheet_name, [str(column) for column in df.columns], detected_mapping, template)
        profiles = map_dataframe_to_profiles(df, source=f"file:{sheet_name}", column_mapping=mapping)
        missing_required = [field for field, _, required in IMPORT_FIELDS if required and not mapping.get(field)]
        quality_flags = []
        if missing_required:
            quality_flags.append("缺少达人名列")
        if "follower_count" not in mapping:
            quality_flags.append("未识别粉丝数")
        if "listed_price" not in mapping:
            quality_flags.append("未识别报价")
        sheets.append(
            {
                "sheet": sheet_name,
                "rows": len(df),
                "detected_profiles": len(profiles),
                "columns": [str(column) for column in df.columns],
                "mapping": mapping,
                "auto_mapping": detected_mapping,
                "applied_template": applied_template_name,
                "missing_required": missing_required,
                "quality_flags": quality_flags,
                "preview": _preview_rows(df),
            }
        )
    return {
        "fields": [{"key": key, "label": label, "required": required} for key, label, required in IMPORT_FIELDS],
        "sheets": sheets,
    }


def _quality_report(profiles: list[CreatorProfile], sheet_counts: dict[str, int], skipped_sheets: list[str]) -> dict[str, Any]:
    total = len(profiles)
    return {
        "total_profiles": total,
        "sheet_counts": sheet_counts,
        "skipped_sheets": skipped_sheets,
        "missing": {
            "follower_count": sum(1 for profile in profiles if not profile.follower_count),
            "listed_price": sum(1 for profile in profiles if not profile.listed_price),
            "homepage_url": sum(1 for profile in profiles if not profile.homepage_url),
            "bio": sum(1 for profile in profiles if not profile.bio),
        },
        "completion_rate": {
            "follower_count": round((total - sum(1 for profile in profiles if not profile.follower_count)) / total, 3) if total else 0,
            "listed_price": round((total - sum(1 for profile in profiles if not profile.listed_price)) / total, 3) if total else 0,
            "homepage_url": round((total - sum(1 for profile in profiles if not profile.homepage_url)) / total, 3) if total else 0,
            "bio": round((total - sum(1 for profile in profiles if not profile.bio)) / total, 3) if total else 0,
        },
    }


def _tables_from_upload_content(content: bytes, filename: str) -> dict[str, pd.DataFrame]:
    holder = BytesIO(content)
    holder.name = filename or "upload"
    tables = load_table_file(holder)
    if not tables:
        raise HTTPException(status_code=400, detail="未识别到可导入的表格")
    return tables


def _preview_creator_import(content: bytes, filename: str, template_id: str | None = None, created_by: str = "") -> dict[str, Any]:
    tables = _tables_from_upload_content(content, filename)
    templates = load_templates(TEMPLATE_PATH)
    template = next((item for item in templates if item.get("id") == template_id), None) if template_id else None
    match_score = 0
    if template is None:
        template, match_score = find_best_template(templates, tables)
    else:
        _, match_score = find_best_template([template], tables)
    review = _build_import_review(tables, template=template)
    import_id = stable_id("agent_import", created_by, filename, openclaw_now_iso(), prefix="agent_import")
    review["import_id"] = import_id
    review["filename"] = filename or "upload"
    review["matched_template"] = {"id": template.get("id"), "name": template.get("name"), "score": match_score} if template else None
    review["totals"] = {
        "sheets": len(review.get("sheets", [])),
        "rows": sum(int(sheet.get("rows") or 0) for sheet in review.get("sheets", [])),
        "detected_profiles": sum(int(sheet.get("detected_profiles") or 0) for sheet in review.get("sheets", [])),
    }
    _AGENT_IMPORT_STAGING[import_id] = {
        "content": content,
        "filename": filename or "upload",
        "review": review,
        "created_by": created_by,
        "created_at": openclaw_now_iso(),
    }
    return review


def _commit_creator_import(
    import_id: str,
    mappings: dict[str, Any] | None = None,
    replace: bool = False,
    save_template: bool = False,
    template_name: str = "",
    template_id: str | None = None,
) -> dict[str, Any]:
    staged = _AGENT_IMPORT_STAGING.get(import_id)
    if not staged:
        raise HTTPException(status_code=404, detail="导入预览已失效，请重新上传文件")
    filename = str(staged.get("filename") or "upload")
    content = staged.get("content")
    if not isinstance(content, bytes):
        raise HTTPException(status_code=400, detail="导入文件内容无效")
    tables = _tables_from_upload_content(content, filename)
    source_object = _store_uploaded_object(content, filename, category="imports")
    payload = mappings if isinstance(mappings, dict) else {}

    profiles: list[CreatorProfile] = []
    sheet_counts: dict[str, int] = {}
    skipped_sheets: list[str] = []
    for sheet_name, df in tables.items():
        sheet_payload = payload.get(sheet_name, {}) if isinstance(payload, dict) else {}
        if isinstance(sheet_payload, dict) and sheet_payload.get("enabled") is False:
            skipped_sheets.append(sheet_name)
            continue
        mapping = sheet_payload.get("mapping") if isinstance(sheet_payload, dict) else None
        if not isinstance(mapping, dict):
            staged_sheet = next((sheet for sheet in staged.get("review", {}).get("sheets", []) if sheet.get("sheet") == sheet_name), None)
            mapping = staged_sheet.get("mapping") if isinstance(staged_sheet, dict) and isinstance(staged_sheet.get("mapping"), dict) else infer_column_mapping(df)
        sheet_profiles = map_dataframe_to_profiles(df, source=f"agent_import:{sheet_name}", column_mapping=mapping)
        if not sheet_profiles:
            skipped_sheets.append(sheet_name)
            sheet_counts[sheet_name] = 0
            continue
        profiles.extend(sheet_profiles)
        sheet_counts[sheet_name] = len(sheet_profiles)

    profiles, dedupe_report = strong_dedupe_profiles(profiles)
    profiles = enrich_profiles(profiles)
    saved_template = None
    if save_template:
        saved_template = upsert_template(
            TEMPLATE_PATH,
            template_name or filename or "Agent 导入模板",
            payload,
            template_id=template_id,
        )
    if replace:
        replace_profiles(DB_PATH, profiles)
    else:
        upsert_profiles(DB_PATH, profiles)
    result = {
        "import_id": import_id,
        "filename": filename,
        "imported": len(profiles),
        "sheet_counts": sheet_counts,
        "skipped_sheets": skipped_sheets,
        "sheets": list(tables.keys()),
        "source_object": source_object,
        "saved_template": saved_template,
        "quality_report": _quality_report(profiles, sheet_counts, skipped_sheets) | {"dedupe": dedupe_report},
    }
    _AGENT_IMPORT_STAGING.pop(import_id, None)
    return result


def _number_from_text(text: str) -> int:
    value = str(text or "").strip().replace(",", "")
    multiplier = 1
    if "万" in value or "w" in value.lower():
        multiplier = 10_000
    elif "k" in value.lower():
        multiplier = 1_000
    elif "m" in value.lower():
        multiplier = 1_000_000
    match = re.search(r"\d+(?:\.\d+)?", value)
    return int(float(match.group(0)) * multiplier) if match else 0


def _float_from_text(text: str) -> float:
    match = re.search(r"\d+(?:\.\d+)?", str(text or ""))
    if not match:
        return 0.0
    number = float(match.group(0))
    return number / 100 if "%" in str(text) else number


def _field_after_label(text: str, labels: list[str]) -> str:
    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:：]\s*([^\n|｜；;]+)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _parse_creator_text(text: str, fallback_name: str = "") -> dict[str, Any]:
    text = str(text or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = _field_after_label(text, ["达人", "达人名", "名称", "账号", "昵称", "name"]) or fallback_name
    if not name and lines:
        name = re.sub(r"^(达人|账号|名称|name)\s*[:：]\s*", "", lines[0], flags=re.IGNORECASE).strip()
    platform = _field_after_label(text, ["平台", "渠道", "platform"])
    if not platform:
        for candidate in [
            "小红书",
            "抖音",
            "B站",
            "bilibili",
            "微博",
            "视频号",
            "微信公众号",
            "公众号",
            "知乎",
            "豆瓣",
            "今日头条",
            "推特",
            "twitter",
        ]:
            if candidate.lower() in text.lower():
                if candidate.lower() == "bilibili":
                    platform = "B站"
                elif candidate in {"公众号"}:
                    platform = "微信公众号"
                elif candidate.lower() == "twitter":
                    platform = "推特"
                else:
                    platform = candidate
                break
    follower_count = _number_from_text(_field_after_label(text, ["粉丝", "粉丝数", "粉丝量", "followers", "fans"]))
    listed_price = _number_from_text(_field_after_label(text, ["报价", "价格", "刊例", "price"]))
    engagement_rate = _float_from_text(_field_after_label(text, ["互动率", "engagement"]))
    content_tags = split_tags(_field_after_label(text, ["内容", "内容方向", "内容能力", "标签", "达人标签"]))
    industry_tags = split_tags(_field_after_label(text, ["行业", "垂类", "品类", "适合行业"]))
    suitable_goals = split_tags(_field_after_label(text, ["适合", "目标", "传播目标", "适合目标"]))
    risk_tags = split_tags(_field_after_label(text, ["风险", "注意", "风险点"]))
    bio = _field_after_label(text, ["简介", "bio", "账号简介"]) or text[:280]
    payload = {
        "name": name or "未命名 KOL",
        "platform": platform or "未知",
        "bio": bio,
        "follower_count": follower_count,
        "listed_price": listed_price,
        "engagement_rate": engagement_rate,
        "industry_fit_tags": industry_tags,
        "content_capability_tags": content_tags,
        "suitable_goals": suitable_goals,
        "risk_tags": risk_tags,
        "manual_notes": text,
    }
    return {key: value for key, value in payload.items() if value not in ["", [], 0, 0.0]}


def _profiles_from_payloads(items: list[dict[str, Any]], source: str) -> list[CreatorProfile]:
    if not items:
        return []
    profiles = map_dataframe_to_profiles(pd.DataFrame(items), source=source)
    return enrich_profiles(profiles)


def _intake_tag_summary(profiles: list[CreatorProfile]) -> list[dict[str, Any]]:
    result = []
    for profile in profiles:
        tags = list_creator_evidence_tags(DB_PATH, creator_id=profile.creator_id)
        result.append(
            {
                "creator_id": profile.creator_id,
                "creator_name": profile.name,
                "platform": profile.platform,
                "tags": [tag.to_dict() if hasattr(tag, "to_dict") else dict(tag) for tag in tags[:12]],
                "tag_count": len(tags),
            }
        )
    return result


def _kol_intake_response(profiles: list[CreatorProfile], source: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    for profile in profiles:
        analyze_creator_evidence_tags(DB_PATH, creator_id=profile.creator_id, limit=200)
    graph = build_kol_knowledge_graph(DB_PATH, limit=80).to_dict() if profiles else {"nodes": [], "edges": []}
    response = {
        "source": source,
        "imported": len(profiles),
        "creators": [profile_payload(profile) for profile in profiles],
        "tag_summary": _intake_tag_summary(profiles),
        "graph_summary": {
            "nodes": len(graph.get("nodes") or []),
            "edges": len(graph.get("edges") or []),
        },
    }
    if extra:
        response.update(extra)
    return response


@app.get("/", response_class=HTMLResponse)
def landing() -> FileResponse:
    response = FileResponse(STATIC_DIR / "landing.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page() -> FileResponse:
    response = FileResponse(STATIC_DIR / "login.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


@app.get("/app", response_class=HTMLResponse)
def index() -> FileResponse:
    response = FileResponse(STATIC_DIR / "index.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


@app.get("/favicon.ico")
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/creator/invite/{token}", response_class=HTMLResponse)
def creator_invite_page(token: str) -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/creator/brief/{token}", response_class=HTMLResponse)
def creator_brief_page(token: str) -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status() -> dict[str, Any]:
    total, enriched = count_profiles(DB_PATH)
    return {
        "total_profiles": total,
        "enriched_profiles": enriched,
        "database": str(DB_PATH),
        "tenant": _sanitize_tenant(_db_path_ctx.get().parent.name if _db_path_ctx.get().parent.parent == TENANT_ROOT else "default"),
        "auth_required": _public_status_auth_required(_db_path_ctx.get()) or bool(ACCESS_KEY),
        "auth_mode": "local" if _auth_mode_active(_db_path_ctx.get()) else ("access_key" if ACCESS_KEY else "open"),
        "current_user": current_identity().user.to_dict() if current_identity() else None,
        "agent_runtime": agent_runtime_status(),
        "connectors": ["excel_csv", "manual", "link", "mock_api", "oneapi"],
        "phase_1_5": ["creator_symbolic_profile", "brand_symbolic_profile", "symbolic_matching", "narrative_path", "stress_test"],
        "phase_2": ["proposal_sharing", "client_feedback", "versioning", "brand_preference_profile", "client_portal"],
        "phase_3": ["creator_invitation", "creator_submission", "commercial_profile_review", "case_visibility"],
        "phase_4": ["brief_distribution", "creator_response", "response_summary", "execution_list"],
        "phase_5": [
            "brand_brief_input",
            "campaign_project",
            "multi_plan_generation",
            "execution_scoring",
            "pre_launch_stress_test",
            "brief_distribution_bridge",
            "post_campaign_review",
            "kol_profile_feedback_loop",
            "project_timeline",
            "os_dashboard",
        ],
    }


@app.get("/api/agent/tasks")
def agent_tasks() -> dict[str, Any]:
    require_internal("read")
    return {"items": list_agent_tasks(DB_PATH)}


@app.get("/api/agent/threads")
def agent_threads() -> dict[str, Any]:
    require_internal("read")
    return {"items": list_agent_threads(DB_PATH)}


@app.get("/api/agent/runtime")
def agent_runtime() -> dict[str, Any]:
    require_internal("read")
    return agent_runtime_status()


@app.get("/api/openclaw/status")
def openclaw_status() -> dict[str, Any]:
    require_internal("read")
    adapter = OpenClawAdapter()
    config = load_openclaw_config(DB_PATH)
    return {"status": adapter.status(DB_PATH), "config": config.to_dict(mask_secret=True)}


@app.get("/api/openclaw/me")
def openclaw_me() -> dict[str, Any]:
    identity = require_internal("read")
    adapter = OpenClawAdapter()
    binding = adapter.binding_for_user(DB_PATH, identity.user.user_id)
    return {"binding": binding.to_dict(), "status": adapter.status(DB_PATH)}


@app.get("/api/openclaw/diagnostics")
def openclaw_diagnostics() -> dict[str, Any]:
    identity = require_internal("read")
    adapter = OpenClawAdapter()
    config = load_openclaw_config(DB_PATH)
    status = adapter.status(DB_PATH)
    bindings = load_all_bindings(DB_PATH)
    runs = load_all_openclaw_runs(DB_PATH)
    is_admin = identity.user.role == "admin"
    visible_bindings = bindings if is_admin else [item for item in bindings if item.user_id == identity.user.user_id]
    visible_runs = runs if is_admin else [run for run in runs if run.user_id == identity.user.user_id]
    recent_runs = visible_runs[:8]
    recent_event_counts = {run.run_id: len(load_openclaw_events_for_run(DB_PATH, run.run_id)) for run in recent_runs}
    status_counts: dict[str, int] = {}
    for run in visible_runs:
        status_counts[run.status] = status_counts.get(run.status, 0) + 1
    active_bindings = [item for item in visible_bindings if item.status == "active"]
    issues: list[str] = []
    if not config.enabled:
        issues.append("OpenClaw is disabled")
    if not config.gateway_url:
        issues.append("Gateway URL is missing")
    if not config.default_agent_id:
        issues.append("Default agent id is missing")
    if not visible_bindings:
        issues.append("No OpenClaw binding for this account" if not is_admin else "No internal user bindings yet")
    return {
        "status": status,
        "config": config.to_dict(mask_secret=True),
        "checks": {
            "enabled": bool(config.enabled),
            "gateway_url": bool(config.gateway_url),
            "control_ui_url": bool(config.control_ui_url),
            "default_agent_id": bool(config.default_agent_id),
            "admin_token": bool(config.admin_token),
            "tool_count": len(_openclaw_tool_manifest()),
            "binding_count": len(visible_bindings),
            "active_binding_count": len(active_bindings),
            "run_count": len(visible_runs),
            "issues": issues,
        },
        "bindings": [item.to_dict() for item in visible_bindings],
        "run_summary": {
            "by_status": status_counts,
            "recent": [
                {
                    "run_id": run.run_id,
                    "user_id": run.user_id,
                    "status": run.status,
                    "openclaw_agent_id": run.openclaw_agent_id,
                    "openclaw_session_id": run.openclaw_session_id,
                    "event_count": recent_event_counts.get(run.run_id, 0),
                    "updated_at": run.updated_at,
                    "created_at": run.created_at,
                }
                for run in recent_runs
            ],
        },
    }


@app.get("/api/openclaw/config")
def openclaw_config() -> dict[str, Any]:
    require_admin()
    return {"config": load_openclaw_config(DB_PATH).to_dict(mask_secret=True), "bindings": [item.to_dict() for item in load_all_bindings(DB_PATH)]}


@app.post("/api/openclaw/config")
async def openclaw_save_config(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_admin()
    current = load_openclaw_config(DB_PATH)
    token_value = str(payload.get("admin_token") or "").strip()
    if not token_value:
        token_value = current.admin_token
    elif token_value and set(token_value) == {"*"}:
        token_value = current.admin_token
    elif "..." in token_value and token_value == current.to_dict(mask_secret=True).get("admin_token"):
        token_value = current.admin_token
    config = OpenClawConfig(
        enabled=bool(payload.get("enabled")),
        gateway_url=str(payload.get("gateway_url") or "").strip(),
        control_ui_url=str(payload.get("control_ui_url") or "").strip(),
        admin_token=token_value,
        default_agent_id=str(payload.get("default_agent_id") or "kolness_default").strip() or "kolness_default",
        proxy_base_path=str(payload.get("proxy_base_path") or "/openclaw").strip() or "/openclaw",
        updated_by=identity.user.user_id,
        updated_at=openclaw_now_iso(),
    )
    save_openclaw_config(DB_PATH, config)
    return {"config": config.to_dict(mask_secret=True), "status": OpenClawAdapter().status(DB_PATH)}


@app.post("/api/openclaw/bindings")
async def openclaw_save_binding(payload: dict[str, Any]) -> dict[str, Any]:
    require_admin()
    user_id = str(payload.get("user_id") or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    user = load_user(DB_PATH, user_id)
    if user is None or user.user_type != "internal":
        raise HTTPException(status_code=404, detail="internal user not found")
    config = load_openclaw_config(DB_PATH)
    existing = OpenClawAdapter().binding_for_user(DB_PATH, user_id)
    binding = OpenClawUserBinding(
        binding_id=binding_id_for(user_id),
        user_id=user_id,
        openclaw_gateway_url=str(payload.get("openclaw_gateway_url") or config.gateway_url or existing.openclaw_gateway_url).strip(),
        openclaw_agent_id=str(payload.get("openclaw_agent_id") or existing.openclaw_agent_id or config.default_agent_id).strip(),
        openclaw_session_id=str(payload.get("openclaw_session_id") or existing.openclaw_session_id).strip(),
        status=str(payload.get("status") or existing.status or "active"),
        created_at=existing.created_at,
        updated_at=openclaw_now_iso(),
    )
    save_openclaw_binding(DB_PATH, binding)
    return {"binding": binding.to_dict(), "bindings": [item.to_dict() for item in load_all_bindings(DB_PATH)]}


def _openclaw_session_payload(session: OpenClawSession) -> dict[str, Any]:
    runs = load_openclaw_runs_for_session(DB_PATH, session.session_id)
    events_by_run = {run.run_id: [event.to_dict() for event in load_openclaw_events_for_run(DB_PATH, run.run_id)] for run in runs}
    return {
        "session": session.to_dict(),
        "runs": [run.to_dict() for run in runs],
        "events_by_run": events_by_run,
    }


@app.get("/api/openclaw/sessions")
async def openclaw_session_list() -> dict[str, Any]:
    identity = require_internal("read")
    if identity.user.user_type == "client":
        raise HTTPException(status_code=403, detail="client cannot use OpenClaw")
    sessions = load_openclaw_sessions_for_user(DB_PATH, identity.user.user_id)
    return {"items": [session.to_dict() for session in sessions]}


@app.post("/api/openclaw/sessions")
async def openclaw_session_create(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    identity = require_internal("project_run")
    if identity.user.user_type == "client":
        raise HTTPException(status_code=403, detail="client cannot use OpenClaw")
    payload = payload or {}
    adapter = OpenClawAdapter()
    session = adapter.create_session(
        DB_PATH,
        identity.user.user_id,
        title=str(payload.get("title") or "新对话"),
        openclaw_session_id=str(payload.get("openclaw_session_id") or "").strip(),
    )
    binding = adapter.binding_for_user(DB_PATH, identity.user.user_id)
    binding.openclaw_session_id = session.openclaw_session_id
    binding.status = "active"
    binding.updated_at = openclaw_now_iso()
    save_openclaw_binding(DB_PATH, binding)
    return {"binding": binding.to_dict(), "session": session.to_dict(), "status": adapter.status(DB_PATH)}


@app.get("/api/openclaw/sessions/{session_id}")
async def openclaw_session_detail(session_id: str) -> dict[str, Any]:
    identity = require_internal("read")
    session = load_openclaw_session(DB_PATH, session_id)
    if session is None or session.user_id != identity.user.user_id:
        raise HTTPException(status_code=404, detail="openclaw session not found")
    return _openclaw_session_payload(session)


@app.post("/api/openclaw/chat")
async def openclaw_chat(payload: dict[str, Any], background_tasks: BackgroundTasks) -> dict[str, Any]:
    identity = require_internal("project_run")
    if identity.user.user_type == "client":
        raise HTTPException(status_code=403, detail="client cannot use OpenClaw")
    message = str(payload.get("message") or payload.get("brief") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    adapter = OpenClawAdapter(timeout=180)
    db_path = _db_path_ctx.get()
    run_payload = {
        "db_path": db_path,
        "user_id": identity.user.user_id,
        "message": message,
        "campaign_id": str(payload.get("campaign_id") or ""),
        "session_record_id": str(payload.get("session_record_id") or payload.get("openclaw_chat_session_id") or payload.get("session_id") or ""),
        "session_id": str(payload.get("openclaw_session_id") or ""),
        "history": payload.get("history") if isinstance(payload.get("history"), list) else [],
    }
    if payload.get("async") is True:
        data = adapter.start_chat_async(**run_payload)
        run_id = str((data.get("run") or {}).get("run_id") or "")
        if run_id:
            background_tasks.add_task(OpenClawAdapter(timeout=180).complete_chat, db_path, run_id)
        return data
    return adapter.start_chat(**run_payload)


def _require_kolness_bridge_access(request: Request) -> None:
    client_host = request.client.host if request.client else ""
    if client_host in {"127.0.0.1", "::1", "localhost"}:
        return
    config = load_openclaw_config(DB_PATH)
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
    if config.admin_token and token and secrets.compare_digest(token, config.admin_token):
        return
    raise HTTPException(status_code=403, detail="kolness bridge access denied")


def _is_pr_agent_task(message: str) -> bool:
    text = message.strip().lower()
    if not text:
        return False
    task_keywords = [
        "brief",
        "kol",
        "koc",
        "达人",
        "博主",
        "推荐",
        "匹配",
        "方案",
        "campaign",
        "投放",
        "预算",
        "品牌",
        "新品",
        "上市",
        "预热",
        "小红书",
        "抖音",
        "b站",
        "风险",
        "报价",
        "客户",
    ]
    if any(keyword in text for keyword in task_keywords):
        return True
    return len(message) >= 80


@app.post("/api/kolness/chat")
async def kolness_openclaw_bridge(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    _require_kolness_bridge_access(request)
    message = str(payload.get("message") or payload.get("brief") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    session_id = str(payload.get("session_id") or stable_id("kolness_bridge_session", message[:120], prefix="openclaw_session"))
    if not _is_pr_agent_task(message):
        return {
            "message": "你好，我是 Kolness PR Agent。你可以直接把甲方 brief 发给我，我会帮你推荐 KOL、说明匹配理由、提示主要风险，并整理成客户可看的方案。",
            "session_id": session_id,
            "recommended_kols": [],
            "artifacts": [],
        }
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    top_n = int(metadata.get("top_n") or payload.get("top_n") or 8)
    brief = parse_brief(message)
    results = rank_creators(brief, load_profiles(DB_PATH))[:top_n]
    proposal = generate_markdown_proposal(brief, results)
    recommended = [result.creator.name for result in results]
    score_lines = [
        f"{index}. {result.creator.name}（{result.creator.platform}）- score {result.match_score}：{'; '.join(result.reasons[:3])}"
        for index, result in enumerate(results[:top_n], start=1)
    ]
    risk_notes = []
    for result in results[:top_n]:
        if result.risk_points:
            risk_notes.append(f"{result.creator.name}: {'; '.join(result.risk_points[:2])}")
    response = "\n".join(
        [
            "已完成本次 PR Agent 任务。",
            "",
            "## KOL 推荐",
            *(score_lines or ["暂无匹配达人，请先导入或补充达人资料。"]),
            "",
            "## 主要风险",
            *(risk_notes[:6] or ["当前候选池未发现明显高风险标签，建议进入人工复核。"]),
            "",
            "## 客户可读方案摘要",
            proposal[:1400],
        ]
    )
    return {
        "message": response,
        "session_id": session_id,
        "recommended_kols": recommended,
        "brief": asdict(brief),
        "artifacts": [
            {"artifact_type": "kol_recommendation", "title": "KOL 推荐", "payload": {"items": [_match_result_payload(result) for result in results]}},
            {"artifact_type": "proposal_markdown", "title": "客户可读方案", "payload": {"markdown": proposal}},
        ],
    }


def _require_openclaw_run_access(run_id: str, action: str = "read") -> tuple[Any, Any]:
    identity = require_internal(action)
    run = load_openclaw_run(DB_PATH, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="openclaw run not found")
    if identity.user.role != "admin" and run.user_id != identity.user.user_id:
        raise HTTPException(status_code=403, detail="openclaw run access denied")
    return identity, run


@app.get("/api/openclaw/runs/{run_id}/events")
def openclaw_run_events(run_id: str) -> dict[str, Any]:
    _require_openclaw_run_access(run_id, "read")
    payload = OpenClawAdapter().payload(DB_PATH, run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="openclaw run not found")
    return payload


@app.get("/api/openclaw/runs/{run_id}/stream")
async def openclaw_run_stream(run_id: str) -> StreamingResponse:
    _require_openclaw_run_access(run_id, "read")
    db_path = _db_path_ctx.get()

    async def event_stream():
        last_signature = ""
        while True:
            payload = OpenClawAdapter().payload(db_path, run_id)
            run = payload.get("run") or {}
            events = payload.get("events") or []
            signature = json.dumps({"status": run.get("status"), "events": len(events), "response": run.get("response"), "error": run.get("error")}, ensure_ascii=False, sort_keys=True)
            if signature != last_signature:
                last_signature = signature
                yield f"event: openclaw_run\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            if run.get("status") not in {"running"}:
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/openclaw/runs/{run_id}/save-to-campaign")
async def openclaw_save_run_to_campaign(run_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    identity, run = _require_openclaw_run_access(run_id, "project_run")
    payload = payload or {}
    client_name = str(payload.get("client_name") or "OpenClaw").strip()
    project_name = str(payload.get("project_name") or (run.message[:36] if run.message else "OpenClaw Campaign")).strip()
    top_n = int(payload.get("top_n") or 8)
    project = create_campaign_project(DB_PATH, client_name=client_name, project_name=project_name, raw_brief=run.message, top_n=top_n)
    project.timeline.append(
        {
            "event_type": "openclaw_run_saved",
            "title": "OpenClaw 深度任务已沉淀为 Campaign",
            "payload": {
                "run_id": run.run_id,
                "openclaw_agent_id": run.openclaw_agent_id,
                "openclaw_session_id": run.openclaw_session_id,
                "status": run.status,
                "response": run.response,
                "events": [event.to_dict() for event in load_openclaw_events_for_run(DB_PATH, run_id)],
                "saved_by": identity.user.user_id,
            },
            "created_at": openclaw_now_iso(),
        }
    )
    project.campaign.status = "openclaw_saved"
    project.campaign.updated_at = openclaw_now_iso()
    upsert_campaign_project(DB_PATH, project)
    return {"campaign": project.campaign.to_dict(), "project": project.to_dict(), "target": {"view": "platformOS", "action": "campaign", "id": project.campaign.campaign_id}}


def _require_openclaw_tool_access(request: Request) -> Any:
    config = load_openclaw_config(DB_PATH)
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
    if config.admin_token and token and secrets.compare_digest(token, config.admin_token):
        return _open_mode_identity()
    return require_internal("project_run")


def _match_result_payload(result: Any) -> dict[str, Any]:
    data = asdict(result)
    data["creator"] = profile_payload(result.creator)
    data["table_row"] = result.to_table_row()
    return data


def _find_creator_for_openclaw(payload: dict[str, Any]) -> CreatorProfile | None:
    creator_id = str(payload.get("creator_id") or "").strip()
    if creator_id:
        found = load_profile(DB_PATH, creator_id)
        if found:
            return found
    name = str(payload.get("name") or payload.get("creator_name") or "").strip().lower()
    platform_user_id = str(payload.get("platform_user_id") or "").strip().lower()
    platform = str(payload.get("platform") or "").strip().lower()
    for profile in load_profiles(DB_PATH):
        if platform and profile.platform.lower() != platform:
            continue
        if platform_user_id and profile.platform_user_id.lower() == platform_user_id:
            return profile
        if name and profile.name.lower() == name:
            return profile
    return None


def _evidence_tags_payload(creator_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in list_creator_evidence_tags(DB_PATH, creator_id):
        if hasattr(item, "to_dict"):
            items.append(item.to_dict())
        elif hasattr(item, "__dataclass_fields__"):
            items.append(asdict(item))
        elif isinstance(item, dict):
            items.append(item)
        else:
            items.append({"value": str(item)})
    return items


def _openclaw_tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            "name": "kolness.analyze_brief",
            "description": "解析 PR brief，返回行业、产品、预算、阶段、目标用户和平台偏好。",
            "input_schema": {"brief": "string"},
        },
        {
            "name": "kolness.search_kol",
            "description": "按关键词、平台、标签检索 Kolness 达人库。",
            "input_schema": {"query": "string", "platform": "string optional", "limit": "number optional"},
        },
        {
            "name": "kolness.get_creator_profile",
            "description": "按 creator_id、昵称或平台 ID 读取达人完整档案、标签和证据。",
            "input_schema": {"creator_id": "string optional", "name": "string optional", "platform_user_id": "string optional"},
        },
        {
            "name": "kolness.tag_creator",
            "description": "根据 OpenClaw 分析结果更新达人标签、AI 摘要、备注和风险标签。",
            "input_schema": {"creator_id": "string", "industry_fit_tags": "array optional", "content_capability_tags": "array optional", "risk_tags": "array optional"},
        },
        {
            "name": "kolness.match_kol",
            "description": "根据 brief 对达人库做 KOL 匹配排序。",
            "input_schema": {"brief": "string", "top_n": "number optional"},
        },
        {
            "name": "kolness.generate_kol_graph",
            "description": "根据 brief 和候选达人生成 KOL 决策图谱。",
            "input_schema": {"brief": "string", "creator_ids": "array optional", "limit": "number optional"},
        },
        {
            "name": "kolness.generate_proposal",
            "description": "根据 brief 和 KOL 匹配结果生成客户可读 Markdown 方案。",
            "input_schema": {"brief": "string", "top_n": "number optional"},
        },
        {
            "name": "kolness.get_campaign_history",
            "description": "读取历史 Campaign、Agent Thread、客户方案和 Brief 分发沉淀。",
            "input_schema": {"limit": "number optional", "type": "string optional"},
        },
        {
            "name": "kolness.create_client_share_page",
            "description": "根据 brief 和 KOL 推荐生成甲方可访问的方案页。",
            "input_schema": {"client_name": "string", "project_name": "string", "brief": "string", "top_n": "number optional"},
        },
        {
            "name": "kolness.save_campaign_asset",
            "description": "把 OpenClaw 产物保存为 Kolness Agent artifact，后续可沉淀到 Campaign 资产库。",
            "input_schema": {"title": "string", "artifact_type": "string", "payload": "object"},
        },
        {
            "name": "kolness.preview_creator_import",
            "description": "预览达人表格导入结果，返回识别字段、质量提示、可导入达人数量和 import_id；不会写入达人库。",
            "input_schema": {"filename": "string", "content_base64": "string", "template_id": "string optional"},
        },
        {
            "name": "kolness.commit_creator_import",
            "description": "确认写入一个已经预览过的达人导入任务。",
            "input_schema": {"import_id": "string", "mappings": "object optional", "replace": "boolean optional"},
        },
    ]


@app.get("/api/openclaw/tools")
def openclaw_tools(request: Request) -> dict[str, Any]:
    _require_openclaw_tool_access(request)
    return {"items": _openclaw_tool_manifest()}


@app.post("/api/openclaw/tools/{tool_name:path}")
async def openclaw_call_tool(tool_name: str, payload: dict[str, Any], request: Request) -> dict[str, Any]:
    identity = _require_openclaw_tool_access(request)
    name = tool_name.strip().replace("/", ".")
    if not name.startswith("kolness."):
        name = f"kolness.{name}"

    if name == "kolness.analyze_brief":
        brief_text = str(payload.get("brief") or payload.get("message") or "").strip()
        if not brief_text:
            raise HTTPException(status_code=400, detail="brief is required")
        brief = parse_brief(brief_text)
        return {"tool": name, "brief": asdict(brief)}

    if name == "kolness.search_kol":
        query = str(payload.get("query") or "").strip().lower()
        platform = str(payload.get("platform") or "").strip()
        limit = int(payload.get("limit") or 12)
        profiles = load_profiles(DB_PATH)
        scored: list[tuple[int, CreatorProfile]] = []
        for profile in profiles:
            text = " ".join(
                [
                    profile.name,
                    profile.platform,
                    profile.bio,
                    profile.ai_summary,
                    profile.manual_notes,
                    " ".join(profile.industry_fit_tags + profile.content_capability_tags + profile.suitable_goals + profile.risk_tags),
                ]
            ).lower()
            if platform and profile.platform != platform:
                continue
            score = 1
            if query:
                score = sum(1 for token in split_tags(query.replace(" ", ",")) if token.lower() in text) or (1 if query in text else 0)
            if score:
                scored.append((score, profile))
        scored.sort(key=lambda item: (item[0], item[1].follower_count), reverse=True)
        return {"tool": name, "items": [profile_payload(profile) for _, profile in scored[:limit]], "total": len(scored)}

    if name == "kolness.get_creator_profile":
        profile = _find_creator_for_openclaw(payload)
        if profile is None:
            raise HTTPException(status_code=404, detail="creator not found")
        return {
            "tool": name,
            "creator": profile_payload(profile),
            "evidence_tags": _evidence_tags_payload(profile.creator_id),
        }

    if name == "kolness.tag_creator":
        profile = _find_creator_for_openclaw(payload)
        if profile is None:
            raise HTTPException(status_code=404, detail="creator not found")
        data = asdict(profile)
        tag_fields = ["industry_fit_tags", "content_capability_tags", "suitable_goals", "suitable_stages", "budget_fit_tags", "risk_tags", "cooperation_brands", "cooperation_formats"]
        for field in tag_fields:
            incoming = split_tags(payload.get(field))
            if incoming:
                data[field] = list(dict.fromkeys([*data.get(field, []), *incoming]))[:40]
        for field in ["ai_summary", "manual_notes", "bio", "homepage_url", "avatar_url", "contact"]:
            value = str(payload.get(field) or "").strip()
            if value:
                if field == "manual_notes" and data.get(field):
                    data[field] = f"{data[field]}\nOpenClaw：{value}".strip()
                else:
                    data[field] = value
        sources = data.get("data_sources") or []
        if "openclaw" not in sources:
            sources.append("openclaw")
        data["data_sources"] = sources
        tagged = CreatorProfile(**data)
        save_profile(DB_PATH, tagged)
        try:
            analyze_creator_evidence_tags(DB_PATH, tagged.creator_id)
        except Exception:
            pass
        return {"tool": name, "creator": profile_payload(tagged), "evidence_tags": _evidence_tags_payload(tagged.creator_id)}

    if name == "kolness.match_kol":
        brief_text = str(payload.get("brief") or payload.get("message") or "").strip()
        if not brief_text:
            raise HTTPException(status_code=400, detail="brief is required")
        top_n = int(payload.get("top_n") or 8)
        brief = parse_brief(brief_text)
        results = rank_creators(brief, load_profiles(DB_PATH))[:top_n]
        return {"tool": name, "brief": asdict(brief), "items": [_match_result_payload(result) for result in results], "total": len(results)}

    if name == "kolness.generate_kol_graph":
        brief_text = str(payload.get("brief") or payload.get("message") or "").strip()
        if not brief_text:
            raise HTTPException(status_code=400, detail="brief is required")
        creator_ids = payload.get("creator_ids") if isinstance(payload.get("creator_ids"), list) else []
        graph = build_kol_knowledge_graph(DB_PATH, brief=brief_text, creator_ids=[str(item) for item in creator_ids], limit=int(payload.get("limit") or 80))
        return {"tool": name, "graph": graph.to_dict()}

    if name == "kolness.generate_proposal":
        brief_text = str(payload.get("brief") or payload.get("message") or "").strip()
        if not brief_text:
            raise HTTPException(status_code=400, detail="brief is required")
        top_n = int(payload.get("top_n") or 8)
        brief = parse_brief(brief_text)
        results = rank_creators(brief, load_profiles(DB_PATH))[:top_n]
        markdown = generate_markdown_proposal(brief, results)
        return {
            "tool": name,
            "brief": asdict(brief),
            "markdown": markdown,
            "items": [_match_result_payload(result) for result in results],
        }

    if name == "kolness.get_campaign_history":
        limit = int(payload.get("limit") or 20)
        type_filter = str(payload.get("type") or "").strip()
        items: list[dict[str, Any]] = []
        for project in load_all_campaign_projects(DB_PATH):
            campaign = project.campaign
            items.append(
                {
                    "id": campaign.campaign_id,
                    "type": "campaign",
                    "title": campaign.project_name,
                    "client_name": campaign.client_name,
                    "status": campaign.status,
                    "brief": campaign.raw_brief,
                    "plans": len(project.plans),
                    "timeline": project.timeline[-8:],
                    "updated_at": campaign.updated_at,
                }
            )
        for proposal in load_all_proposals(DB_PATH):
            items.append(
                {
                    "id": proposal.proposal_id,
                    "type": "proposal",
                    "title": proposal.project_name,
                    "client_name": proposal.client_name,
                    "status": proposal.status,
                    "brief": proposal.brief_summary or proposal.brief_text[:180],
                    "share_url": proposal.public_url(),
                    "updated_at": proposal.updated_at or proposal.created_at,
                }
            )
        for thread_payload in list_agent_threads(DB_PATH):
            thread = thread_payload.get("thread") or {}
            task = thread_payload.get("task") or {}
            items.append(
                {
                    "id": thread.get("thread_id") or task.get("task_id") or "",
                    "type": "agent_thread",
                    "title": thread.get("title") or task.get("title") or "Agent Thread",
                    "client_name": thread.get("client_name") or task.get("client_name") or "",
                    "status": thread.get("status") or task.get("status") or "",
                    "brief": thread.get("summary") or task.get("brief") or "",
                    "updated_at": thread.get("updated_at") or task.get("updated_at") or "",
                }
            )
        if type_filter:
            items = [item for item in items if item.get("type") == type_filter]
        items.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
        return {"tool": name, "items": items[:limit], "total": len(items)}

    if name == "kolness.create_client_share_page":
        brief_text = str(payload.get("brief") or payload.get("message") or "").strip()
        if not brief_text:
            raise HTTPException(status_code=400, detail="brief is required")
        client_name = str(payload.get("client_name") or "Demo Client").strip()
        project_name = str(payload.get("project_name") or "KOL 推荐方案").strip()
        top_n = int(payload.get("top_n") or 8)
        proposal, version, markdown = create_proposal_from_brief(
            DB_PATH,
            client_name=client_name,
            project_name=project_name,
            brief_text=brief_text,
            creators=load_profiles(DB_PATH),
            top_n=top_n,
            created_by=identity.user.user_id,
        )
        upsert_proposal(DB_PATH, proposal)
        upsert_version(DB_PATH, version)
        return {
            "tool": name,
            "proposal": asdict(proposal) | {"share_url": proposal.public_url()},
            "version": version.to_dict(),
            "markdown": markdown,
        }

    if name == "kolness.save_campaign_asset":
        title = str(payload.get("title") or "OpenClaw 产物").strip()
        artifact_type = str(payload.get("artifact_type") or "openclaw_asset").strip()
        campaign_id = str(payload.get("campaign_id") or "").strip()
        task_id = str(payload.get("task_id") or stable_id("openclaw", campaign_id, identity.user.user_id, prefix="agent_task"))
        run_id = str(payload.get("run_id") or stable_id("openclaw", task_id, title, prefix="agent_run"))
        artifact = AgentArtifact(
            artifact_id=artifact_id_for(task_id, artifact_type, title),
            task_id=task_id,
            run_id=run_id,
            artifact_type=artifact_type,
            title=title,
            summary=str(payload.get("summary") or "OpenClaw 回写到 Kolness 的产物。"),
            payload={
                "campaign_id": campaign_id,
                "source": "openclaw",
                "content": payload.get("content") or "",
                "payload": payload.get("payload") or {},
                "created_by": identity.user.user_id,
            },
        )
        upsert_artifact(DB_PATH, artifact)
        return {"tool": name, "artifact": artifact.to_dict()}

    if name == "kolness.preview_creator_import":
        filename = str(payload.get("filename") or "agent-upload.csv").strip()
        content_base64 = str(payload.get("content_base64") or "").strip()
        if not content_base64:
            raise HTTPException(status_code=400, detail="content_base64 is required")
        try:
            content = base64.b64decode(content_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="content_base64 must be valid base64") from exc
        review = _preview_creator_import(
            content,
            filename,
            template_id=str(payload.get("template_id") or "").strip() or None,
            created_by=identity.user.user_id,
        )
        return {"tool": name, "review": review}

    if name == "kolness.commit_creator_import":
        import_id = str(payload.get("import_id") or "").strip()
        if not import_id:
            raise HTTPException(status_code=400, detail="import_id is required")
        result = _commit_creator_import(
            import_id,
            mappings=payload.get("mappings") if isinstance(payload.get("mappings"), dict) else None,
            replace=bool(payload.get("replace")),
            save_template=bool(payload.get("save_template")),
            template_name=str(payload.get("template_name") or ""),
            template_id=str(payload.get("template_id") or "").strip() or None,
        )
        return {"tool": name, "result": result}

    raise HTTPException(status_code=404, detail="unknown OpenClaw tool")


@app.api_route("/openclaw/proxy", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
@app.api_route("/openclaw/proxy/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def openclaw_proxy(request: Request, path: str = "") -> StreamingResponse:
    require_internal("read")
    config = load_openclaw_config(DB_PATH)
    upstream = config.control_ui_url.rstrip("/")
    if not config.enabled or not upstream:
        raise HTTPException(status_code=503, detail="OpenClaw native UI is not configured")
    query = request.url.query
    target = f"{upstream}/{path.lstrip('/')}"
    if query:
        target = f"{target}?{query}"
    headers = {key: value for key, value in request.headers.items() if key.lower() not in {"host", "content-length", "cookie", "connection", "accept-encoding"}}
    if config.admin_token and "authorization" not in {key.lower() for key in headers}:
        headers["Authorization"] = f"Bearer {config.admin_token}"
    try:
        response = requests.request(request.method, target, data=await request.body(), headers=headers, timeout=30, allow_redirects=False)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"OpenClaw proxy failed: {exc}") from exc
    response_headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in {"content-encoding", "transfer-encoding", "connection", "content-length", "x-frame-options"}
    }
    return StreamingResponse(BytesIO(response.content), status_code=response.status_code, headers=response_headers, media_type=response.headers.get("content-type"))


@app.get("/openclaw", response_class=HTMLResponse)
def openclaw_workspace() -> Response:
    identity = require_internal("read")
    config = load_openclaw_config(DB_PATH)
    binding = OpenClawAdapter().binding_for_user(DB_PATH, identity.user.user_id)
    url = config.control_ui_url
    user_label = html.escape(identity.user.name or identity.user.email or identity.user.user_id)
    user_email = html.escape(identity.user.email or identity.user.user_id)
    agent_id = html.escape(binding.openclaw_agent_id or config.default_agent_id or "kolness_default")
    session_id = html.escape(binding.openclaw_session_id or "new session")
    if not config.enabled or not url:
        return RedirectResponse(url="/app#agentWorkspace", status_code=307)
    safe_url = html.escape("/openclaw/proxy", quote=True)
    upstream_label = html.escape(config.control_ui_url or config.gateway_url)
    return HTMLResponse(
        f"<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Kolness × OpenClaw Workspace</title>"
        f"<style>"
        f":root{{--ink:#13100c;--paper:#fffaf0;--muted:#746b5e;--mint:#b9ffea;--green:#57e0b1;--yellow:#ffdd58;--red:#ff6348}}"
        f"*{{box-sizing:border-box}}"
        f"html,body{{margin:0;width:100%;height:100%;background:var(--ink);color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}"
        f"body{{display:grid;grid-template-rows:auto 1fr;overflow:hidden}}"
        f".top{{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:14px 18px;background:var(--paper);border-bottom:4px solid var(--ink)}}"
        f".brand{{display:flex;align-items:center;gap:14px;min-width:0}}"
        f".logo{{width:54px;height:54px;display:grid;place-items:center;background:var(--yellow);border:3px solid var(--ink);box-shadow:5px 5px 0 var(--green);font-weight:1000;font-size:22px}}"
        f".brand h1{{margin:0;font-size:25px;line-height:1;letter-spacing:0}}"
        f".brand p{{margin:5px 0 0;color:var(--muted);font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}"
        f".actions{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end}}"
        f".pill,.btn{{border:3px solid var(--ink);background:#fffdf5;box-shadow:4px 4px 0 var(--ink);padding:9px 12px;font-weight:950;text-decoration:none;color:var(--ink)}}"
        f".pill{{background:var(--mint);box-shadow:none;max-width:360px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}"
        f".btn.primary{{background:var(--yellow);box-shadow:4px 4px 0 var(--green)}}"
        f".shell{{min-height:0;display:grid;grid-template-columns:280px minmax(0,1fr) 300px;gap:0;background:var(--paper)}}"
        f"aside{{min-height:0;overflow:auto;background:#17140f;color:var(--paper);padding:18px;border-right:4px solid var(--ink)}}"
        f"aside.right{{border-right:0;border-left:4px solid var(--ink);background:#fffdf5;color:var(--ink)}}"
        f".section{{border:3px solid currentColor;padding:14px;margin-bottom:14px;box-shadow:5px 5px 0 rgba(87,224,177,.6)}}"
        f".section h2{{font-size:18px;margin:0 0 10px;line-height:1}}"
        f".section p,.section li{{font-size:14px;line-height:1.45;color:inherit;opacity:.82;font-weight:750}}"
        f".section ul{{padding-left:18px;margin:8px 0 0}}"
        f".tag{{display:inline-block;background:var(--yellow);color:var(--ink);border:2px solid var(--ink);padding:4px 8px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:900;margin:3px 4px 3px 0}}"
        f".frame{{min-width:0;min-height:0;position:relative;background:#080806}}"
        f".frame-bar{{position:absolute;z-index:2;left:14px;top:14px;right:14px;display:flex;justify-content:space-between;gap:10px;pointer-events:none}}"
        f".frame-bar span{{pointer-events:auto;background:rgba(255,250,240,.92);border:2px solid var(--ink);box-shadow:4px 4px 0 var(--green);padding:7px 10px;font-weight:950}}"
        f"iframe{{width:100%;height:100%;border:0;background:#11100c;display:block}}"
        f"@media (max-width:1100px){{.shell{{grid-template-columns:1fr}}aside{{display:none}}.top{{align-items:flex-start;flex-direction:column}}.actions{{justify-content:flex-start}}}}"
        f"</style>"
        f"<body>"
        f"<header class='top'>"
        f"<div class='brand'><div class='logo'>PR</div><div><h1>Kolness × OpenClaw</h1><p>OpenClaw 原生前端 + Kolness PR/KOL 工具层</p></div></div>"
        f"<div class='actions'><span class='pill'>{user_label} · {agent_id}</span><a class='btn' href='/app'>Kolness 工作台</a><a class='btn primary' href='/app#agentWorkspace'>Agent Workspace</a></div>"
        f"</header>"
        f"<main class='shell'>"
        f"<aside>"
        f"<section class='section'><h2>当前身份</h2><p>{user_email}</p><p>Agent: {agent_id}</p><p>Session: {session_id}</p></section>"
        f"<section class='section'><h2>Kolness 业务上下文</h2><ul><li>内部员工可用，客户侧不可直接访问。</li><li>权限、KOL 数据、Campaign 资产仍由 Kolness 控制。</li><li>这里用于需要 OpenClaw 原生对话/工具卡/工作区时使用。</li></ul></section>"
        f"<section class='section'><h2>推荐使用方式</h2><p>日常 brief 推荐先用 Kolness 浮窗；需要更长任务、原生 OpenClaw 会话或调试工具时打开本页。</p></section>"
        f"</aside>"
        f"<section class='frame' aria-label='OpenClaw Control UI'>"
        f"<div class='frame-bar'><span>Native OpenClaw UI</span><span>{upstream_label}</span></div>"
        f"<iframe src='{safe_url}' title='OpenClaw Control UI'></iframe>"
        f"</section>"
        f"<aside class='right'>"
        f"<section class='section'><h2>已开放 Kolness MCP Tools</h2>"
        f"<span class='tag'>brief</span><span class='tag'>search_kol</span><span class='tag'>match_kol</span><span class='tag'>kol_graph</span><span class='tag'>proposal</span><span class='tag'>campaign_save</span>"
        f"</section>"
        f"<section class='section'><h2>为什么不完全替代 Kolness UI</h2><p>OpenClaw 是执行层；Kolness 是 PR 业务 OS。KOL 档案、客户方案、历史 Campaign、权限和审计必须沉淀回 Kolness。</p></section>"
        f"<section class='section'><h2>资产回写</h2><p>在 Kolness 浮窗里跑 OpenClaw 任务后，可保存到 Campaign。OpenClaw 原生页适合深度任务和原生体验验证。</p></section>"
        f"</aside>"
        f"</main></body></html>"
    )


@app.get("/api/history/workspace")
def workspace_history() -> dict[str, Any]:
    require_internal("read")
    items: list[dict[str, Any]] = []

    for project in load_all_campaign_projects(DB_PATH):
        campaign = project.campaign
        latest_timeline = next((event for event in project.timeline if event.get("created_at")), {})
        updated_at = campaign.updated_at or latest_timeline.get("created_at") or campaign.created_at
        items.append(
            {
                "id": campaign.campaign_id,
                "type": "campaign",
                "label": "Campaign",
                "title": campaign.project_name,
                "subtitle": campaign.client_name,
                "status": "archived" if project.archived else campaign.status,
                "summary": campaign.raw_brief[:180],
                "updated_at": updated_at,
                "created_at": campaign.created_at,
                "metrics": [
                    {"label": "方案", "value": len(project.plans)},
                    {"label": "事件", "value": len(project.timeline)},
                    {"label": "复盘", "value": len(project.reviews)},
                ],
                "target": {"view": "platformOS", "action": "campaign", "id": campaign.campaign_id},
            }
        )

    for payload in list_agent_threads(DB_PATH):
        thread = payload.get("thread") or {}
        task = payload.get("task") or {}
        messages = payload.get("messages") or []
        runs = payload.get("runs") or []
        artifacts = payload.get("artifacts") or []
        latest_run = runs[0] if runs else {}
        items.append(
            {
                "id": thread.get("thread_id") or task.get("task_id") or "",
                "type": "agent_thread",
                "label": "Agent Chat",
                "title": thread.get("title") or task.get("title") or "Agent Thread",
                "subtitle": thread.get("client_name") or task.get("client_name") or "内部 Agent",
                "status": thread.get("status") or task.get("status") or latest_run.get("status") or "active",
                "summary": thread.get("summary") or task.get("brief") or "",
                "updated_at": thread.get("updated_at") or task.get("updated_at") or latest_run.get("updated_at") or "",
                "created_at": thread.get("created_at") or task.get("created_at") or "",
                "metrics": [
                    {"label": "消息", "value": len(messages)},
                    {"label": "运行", "value": len(runs)},
                    {"label": "产物", "value": len(artifacts)},
                ],
                "target": {"view": "agentWorkspace", "action": "agent_thread", "id": thread.get("thread_id") or task.get("task_id") or ""},
            }
        )

    for proposal in load_all_proposals(DB_PATH):
        versions = load_versions(DB_PATH, proposal.proposal_id)
        feedback = load_feedback(DB_PATH, proposal.proposal_id)
        items.append(
            {
                "id": proposal.proposal_id,
                "type": "proposal",
                "label": "Client Proposal",
                "title": proposal.project_name,
                "subtitle": proposal.client_name,
                "status": proposal.status,
                "summary": proposal.brief_summary or proposal.brief_text[:180],
                "updated_at": proposal.updated_at or proposal.created_at,
                "created_at": proposal.created_at,
                "metrics": [
                    {"label": "版本", "value": len(versions)},
                    {"label": "反馈", "value": len(feedback)},
                    {"label": "访问", "value": proposal.access_count},
                ],
                "target": {"view": "collaboration", "action": "proposal", "id": proposal.proposal_id},
            }
        )

    for brief in load_all_distribution_briefs(DB_PATH):
        responses = load_responses_for_brief(DB_PATH, brief.brief_id)
        updated_at = brief.pushed_at or max([item.created_at for item in responses], default="") or brief.created_at
        items.append(
            {
                "id": brief.brief_id,
                "type": "distribution",
                "label": "Brief Distribution",
                "title": brief.project_name,
                "subtitle": brief.client_name,
                "status": brief.status,
                "summary": brief.raw_brief[:180],
                "updated_at": updated_at,
                "created_at": brief.created_at,
                "metrics": [
                    {"label": "博主", "value": len(brief.recipients)},
                    {"label": "响应", "value": len(responses)},
                    {"label": "已看", "value": len([item for item in brief.recipients if item.viewed_at])},
                ],
                "target": {"view": "briefDistribution", "action": "distribution", "id": brief.brief_id},
            }
        )

    items = [item for item in items if item["id"]]
    items.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    summary: dict[str, int] = {}
    for item in items:
        summary[item["type"]] = summary.get(item["type"], 0) + 1
    return {"items": items[:120], "summary": summary, "total": len(items)}


def _runtime_from_payload(payload: dict[str, Any]) -> str:
    return _normalize_runtime_name(str(payload.get("runtime") or payload.get("agent_runtime") or requested_runtime_name()))


def _normalize_runtime_name(value: str) -> str:
    name = value.strip().lower()
    if name in {"", "default", "auto"}:
        return requested_runtime_name()
    if name in {"openai", "openai-agents", "agents_sdk", "agent_sdk"}:
        return OPENAI_AGENTS_RUNTIME
    if name in {CUSTOM_RUNTIME, OPENAI_AGENTS_RUNTIME}:
        return name
    return requested_runtime_name()


def _runtime_comparison_payload(runtime_a: str, first: dict[str, Any], runtime_b: str, second: dict[str, Any]) -> dict[str, Any]:
    first_metrics = _run_compare_metrics(first)
    second_metrics = _run_compare_metrics(second)
    return {
        "runtime_a": runtime_a,
        "runtime_b": runtime_b,
        "runs": {
            runtime_a: first_metrics,
            runtime_b: second_metrics,
        },
        "delta": {
            "candidate_count": second_metrics["candidate_count"] - first_metrics["candidate_count"],
            "tool_count": second_metrics["tool_count"] - first_metrics["tool_count"],
            "graph_nodes": second_metrics["graph_nodes"] - first_metrics["graph_nodes"],
            "sdk_runtime_b": second_metrics["sdk_status"],
        },
    }


def _run_compare_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    artifacts = payload.get("artifacts") or []
    events = payload.get("events") or []
    project = next((item for item in artifacts if item.get("artifact_type") == "project_run"), {})
    proposal = next((item for item in artifacts if item.get("artifact_type") == "proposal"), {})
    trace = next((item for item in artifacts if item.get("artifact_type") == "tool_trace"), {})
    graph = next((item for item in artifacts if item.get("artifact_type") == "reasoning_graph"), {})
    sdk_event = next((item for item in events if item.get("event_type") == "sdk_runtime" and item.get("status") in {"completed", "failed"}), {})
    project_summary = (project.get("payload") or {}).get("summary") or {}
    proposal_summary = (proposal.get("payload") or {}).get("summary") or {}
    trace_payload = trace.get("payload") or {}
    graph_summary = (graph.get("payload") or {}).get("summary") or {}
    return {
        "run_id": (payload.get("run") or {}).get("run_id", ""),
        "status": (payload.get("run") or {}).get("status", ""),
        "candidate_count": int(proposal_summary.get("candidate_count") or project_summary.get("matches") or 0),
        "project_matches": int(project_summary.get("matches") or 0),
        "tool_count": int(trace_payload.get("count") or 0),
        "graph_nodes": int(graph_summary.get("node_count") or project_summary.get("graph_nodes") or 0),
        "sdk_status": sdk_event.get("status") or "",
        "sdk_message": sdk_event.get("title") or "",
    }


@app.post("/api/agent/threads")
async def agent_thread_create(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_internal("project_run")
    message = str(payload.get("message") or payload.get("brief") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    return create_agent_thread(
        DB_PATH,
        message=message,
        client_name=str(payload.get("client_name") or ""),
        project_name=str(payload.get("project_name") or ""),
        created_by=identity.user.user_id,
    )


@app.get("/api/agent/threads/{thread_id}")
def agent_thread_detail(thread_id: str) -> dict[str, Any]:
    require_internal("read")
    thread = get_agent_thread(DB_PATH, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="agent thread not found")
    return thread


@app.post("/api/agent/threads/{thread_id}/messages")
async def agent_thread_message(thread_id: str, payload: dict[str, Any], background_tasks: BackgroundTasks) -> dict[str, Any]:
    identity = require_internal("project_run")
    message = str(payload.get("message") or payload.get("brief") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    top_n = int(payload.get("top_n") or 8)
    db_path = _db_path_ctx.get()
    try:
        adapter = get_runtime_adapter(_runtime_from_payload(payload))
        started = adapter.start_thread_message(
            db_path,
            thread_id,
            message=message,
            top_n=top_n,
            created_by=identity.user.user_id,
            require_plan_approval=bool(payload.get("require_plan_approval")),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    background_tasks.add_task(adapter.execute_run, db_path, started["run"]["run_id"], top_n, bool(payload.get("require_plan_approval")))
    return started


@app.get("/api/agent/tasks/{task_id}")
def agent_task_detail(task_id: str) -> dict[str, Any]:
    require_internal("read")
    task = get_agent_task(DB_PATH, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="agent task not found")
    return task


@app.post("/api/agent/chat")
async def agent_chat(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_internal("project_run")
    message = str(payload.get("message") or payload.get("brief") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    try:
        return get_runtime_adapter(_runtime_from_payload(payload)).run_chat(
            DB_PATH,
            message=message,
            task_id=str(payload.get("task_id") or ""),
            client_name=str(payload.get("client_name") or ""),
            project_name=str(payload.get("project_name") or ""),
            top_n=int(payload.get("top_n") or 8),
            created_by=identity.user.user_id,
            require_plan_approval=bool(payload.get("require_plan_approval")),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/agent/chat/start")
async def agent_chat_start(payload: dict[str, Any], background_tasks: BackgroundTasks) -> dict[str, Any]:
    identity = require_internal("project_run")
    message = str(payload.get("message") or payload.get("brief") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    top_n = int(payload.get("top_n") or 8)
    db_path = _db_path_ctx.get()
    try:
        adapter = get_runtime_adapter(_runtime_from_payload(payload))
        started = adapter.start_chat(
            db_path,
            message=message,
            task_id=str(payload.get("task_id") or ""),
            client_name=str(payload.get("client_name") or ""),
            project_name=str(payload.get("project_name") or ""),
            top_n=top_n,
            created_by=identity.user.user_id,
            require_plan_approval=bool(payload.get("require_plan_approval")),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    background_tasks.add_task(adapter.execute_run, db_path, started["run"]["run_id"], top_n, bool(payload.get("require_plan_approval")))
    return started


@app.post("/api/agent/chat/compare-runtimes")
async def agent_chat_compare_runtimes(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_internal("project_run")
    message = str(payload.get("message") or payload.get("brief") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    top_n = int(payload.get("top_n") or 8)
    client_name = str(payload.get("client_name") or "")
    project_name = str(payload.get("project_name") or "")
    db_path = _db_path_ctx.get()
    first_runtime = str(payload.get("runtime_a") or CUSTOM_RUNTIME)
    second_runtime = str(payload.get("runtime_b") or OPENAI_AGENTS_RUNTIME)
    try:
        first = get_runtime_adapter(_normalize_runtime_name(first_runtime)).run_chat(
            db_path,
            message=message,
            client_name=client_name,
            project_name=f"{project_name} · {first_runtime}",
            top_n=top_n,
            created_by=identity.user.user_id,
            require_plan_approval=False,
        )
        second = get_runtime_adapter(_normalize_runtime_name(second_runtime)).run_chat(
            db_path,
            message=message,
            client_name=client_name,
            project_name=f"{project_name} · {second_runtime}",
            top_n=top_n,
            created_by=identity.user.user_id,
            require_plan_approval=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    comparison = _runtime_comparison_payload(first_runtime, first, second_runtime, second)
    artifact = AgentArtifact(
        artifact_id=artifact_id_for(first["task"]["task_id"], "runtime_comparison", f"{first_runtime}_vs_{second_runtime}"),
        task_id=first["task"]["task_id"],
        run_id=first["run"]["run_id"],
        artifact_type="runtime_comparison",
        title="Runtime A/B 对比",
        summary=f"{first_runtime} vs {second_runtime}：候选、耗时、SDK 状态和图谱规模对比。",
        payload=comparison,
    )
    upsert_artifact(db_path, artifact)
    first = get_agent_run(db_path, first["run"]["run_id"]) or first
    return {"runtime_a": first, "runtime_b": second, "comparison": comparison, "artifact": artifact.to_dict()}


@app.get("/api/agent/runs/{run_id}")
def agent_run_detail(run_id: str) -> dict[str, Any]:
    require_internal("read")
    run = get_agent_run(DB_PATH, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="agent run not found")
    return run


@app.get("/api/agent/runs/{run_id}/events")
def agent_run_events(run_id: str) -> dict[str, Any]:
    require_internal("read")
    run = get_agent_run(DB_PATH, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="agent run not found")
    return {"items": run.get("events", []), "artifacts": run.get("artifacts", [])}


@app.get("/api/agent/runs/{run_id}/stream")
async def agent_run_stream(run_id: str) -> StreamingResponse:
    require_internal("read")
    db_path = _db_path_ctx.get()
    if get_agent_run(db_path, run_id) is None:
        raise HTTPException(status_code=404, detail="agent run not found")

    async def event_stream():
        last_signature = ""
        while True:
            payload = get_agent_run(db_path, run_id)
            if payload is None:
                yield 'event: agent_error\ndata: {"detail":"agent run not found"}\n\n'
                break
            run = payload.get("run") or {}
            signature = json.dumps(
                {
                    "status": run.get("status"),
                    "events": len(payload.get("events") or []),
                    "steps": [(item.get("step_id"), item.get("status"), item.get("updated_at")) for item in payload.get("steps") or []],
                    "artifacts": len(payload.get("artifacts") or []),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            if signature != last_signature:
                last_signature = signature
                yield f"event: agent_run\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            if run.get("status") not in {"running"}:
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/agent/steps/{step_id}/{action}")
async def agent_step_control(step_id: str, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    identity = require_internal("write")
    try:
        return update_agent_step_control(
            _db_path_ctx.get(),
            step_id,
            action,
            input_payload=payload or {},
            created_by=identity.user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/agent/runs/{run_id}/approve")
async def agent_run_approve(run_id: str) -> dict[str, Any]:
    require_internal("write")
    try:
        return approve_agent_run(DB_PATH, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/agent/runs/{run_id}/approve-plan")
async def agent_run_approve_plan(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    require_internal("write")
    try:
        return get_runtime_adapter(_runtime_from_payload(payload)).approve_plan(DB_PATH, run_id, top_n=int(payload.get("top_n") or 8))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/agent/runs/{run_id}/cancel")
async def agent_run_cancel(run_id: str) -> dict[str, Any]:
    require_internal("write")
    try:
        return cancel_agent_run(DB_PATH, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/agent/runs/{run_id}/clarification")
async def agent_run_clarification(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_internal("project_run")
    try:
        return get_runtime_adapter(_runtime_from_payload(payload)).resume_clarification(
            DB_PATH,
            run_id,
            supplement=str(payload.get("supplement") or ""),
            top_n=int(payload.get("top_n") or 8),
            created_by=identity.user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/agent/artifacts/{artifact_id}/knowledge")
async def agent_artifact_to_knowledge(artifact_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_internal("write")
    try:
        return commit_agent_memory_suggestion(
            DB_PATH,
            artifact_id,
            suggestion_index=int(payload.get("suggestion_index") or 0),
            created_by=identity.user.user_id,
            override=payload.get("override") or {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/knowledge")
def knowledge_list() -> dict[str, Any]:
    require_internal("read")
    return {"items": list_knowledge_documents(DB_PATH), "stats": knowledge_stats(DB_PATH)}


@app.post("/api/knowledge")
async def knowledge_create(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_internal("write")
    try:
        result = create_knowledge_document(
            DB_PATH,
            title=str(payload.get("title") or ""),
            content=str(payload.get("content") or ""),
            source_type=str(payload.get("source_type") or "manual"),
            source_ref=str(payload.get("source_ref") or ""),
            client_id=str(payload.get("client_id") or ""),
            project_id=str(payload.get("project_id") or ""),
            industry=str(payload.get("industry") or ""),
            tags=payload.get("tags") or "",
            metadata={"created_by": identity.user.user_id},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@app.get("/api/knowledge/{document_id}")
def knowledge_detail(document_id: str) -> dict[str, Any]:
    require_internal("read")
    result = knowledge_document_detail(DB_PATH, document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="knowledge document not found")
    return result


@app.post("/api/knowledge/search")
async def knowledge_search(payload: dict[str, Any]) -> dict[str, Any]:
    require_internal("read")
    query = str(payload.get("query") or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    return {
        "items": search_knowledge_base(
            DB_PATH,
            query=query,
            top_k=int(payload.get("top_k") or 5),
            client_id=str(payload.get("client_id") or ""),
            project_id=str(payload.get("project_id") or ""),
            industry=str(payload.get("industry") or ""),
            source_type=str(payload.get("source_type") or ""),
        )
    }


@app.post("/api/auth/bootstrap-admin")
async def auth_bootstrap_admin(payload: dict[str, Any]) -> JSONResponse:
    if users_exist(DB_PATH) and not _access_key_valid_request_payload(payload):
        raise HTTPException(status_code=403, detail="admin already exists")
    try:
        user = create_user(
            DB_PATH,
            email=str(payload.get("email") or ""),
            password=str(payload.get("password") or ""),
            name=str(payload.get("name") or "Admin"),
            user_type="internal",
            role="admin",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session = create_session(DB_PATH, user)
    response = JSONResponse({"user": user.to_dict(), "session": session.to_dict(), "auth_mode": "local"})
    response.set_cookie(AUTH_COOKIE_NAME, session.session_id, max_age=14 * 24 * 3600, **_session_cookie_kwargs())
    return response


def _access_key_valid_request_payload(payload: dict[str, Any]) -> bool:
    return bool(ACCESS_KEY and str(payload.get("access_key") or "") == ACCESS_KEY)


@app.post("/api/auth/login")
async def auth_login(payload: dict[str, Any]) -> JSONResponse:
    from src.auth.identity_provider import LocalIdentityProvider

    provider = LocalIdentityProvider()
    user = provider.authenticate(DB_PATH, str(payload.get("email") or ""), str(payload.get("password") or ""))
    if user is None:
        raise HTTPException(status_code=401, detail="invalid email or password")
    session = create_session(DB_PATH, user)
    response = JSONResponse({"user": user.to_dict(), "session": session.to_dict(), "auth_mode": "local"})
    response.set_cookie(AUTH_COOKIE_NAME, session.session_id, max_age=14 * 24 * 3600, **_session_cookie_kwargs())
    return response


@app.post("/api/auth/logout")
async def auth_logout(request: Request) -> JSONResponse:
    session_id = request.cookies.get(AUTH_COOKIE_NAME, "")
    if session_id:
        logout_session(DB_PATH, session_id)
    response = JSONResponse({"ok": True})
    response.delete_cookie(
        AUTH_COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=os.getenv("PR_AI_OS_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
    )
    return response


@app.get("/api/auth/me")
def auth_me() -> dict[str, Any]:
    identity = current_identity()
    return {
        "authenticated": identity is not None,
        "identity": identity.to_dict() if identity else None,
        "auth_required": _auth_mode_active(_db_path_ctx.get()),
        "roles": {
            "internal": sorted(INTERNAL_ROLES),
            "client": sorted(CLIENT_ROLES),
        },
    }


@app.get("/api/auth/users")
def auth_users() -> dict[str, Any]:
    require_admin()
    return {"items": [user.to_dict() for user in load_all_users(DB_PATH)]}


@app.get("/api/rules/config")
def rules_config() -> dict[str, Any]:
    require_admin()
    return {"config": load_rule_config(DB_PATH)}


@app.put("/api/rules/config")
async def rules_save_config(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_admin()
    try:
        config = save_rule_config(DB_PATH, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"config": config, "updated_by": identity.user.user_id}


@app.post("/api/rules/config/reset")
async def rules_reset_config() -> dict[str, Any]:
    identity = require_admin()
    return {"config": reset_rule_config(DB_PATH), "updated_by": identity.user.user_id}


@app.post("/api/auth/users")
async def auth_create_user(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_admin()
    try:
        user = create_user(
            DB_PATH,
            email=str(payload.get("email") or ""),
            password=str(payload.get("password") or ""),
            name=str(payload.get("name") or ""),
            user_type=str(payload.get("user_type") or "internal"),
            role=str(payload.get("role") or "viewer"),
            client_id=str(payload.get("client_id") or ""),
        )
        if user.user_type == "client" and user.client_id:
            link_client_user(DB_PATH, user.client_id, user.user_id, user.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user": user.to_dict(), "created_by": identity.user.user_id}


@app.patch("/api/auth/users/{user_id}")
async def auth_update_user(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_admin()
    current = load_user(DB_PATH, user_id)
    if current is None:
        raise HTTPException(status_code=404, detail="user not found")
    requested_status = str(payload.get("status")) if "status" in payload else None
    requested_role = str(payload.get("role")) if "role" in payload else None
    if identity.user.user_id == user_id and requested_status == "disabled":
        raise HTTPException(status_code=400, detail="cannot disable current admin")
    if identity.user.user_id == user_id and requested_role and requested_role != "admin":
        raise HTTPException(status_code=400, detail="cannot remove current admin role")
    try:
        user = update_user(
            DB_PATH,
            user_id=user_id,
            name=str(payload.get("name")) if "name" in payload else None,
            role=requested_role,
            status=requested_status,
            client_id=str(payload.get("client_id")) if "client_id" in payload else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user": user.to_dict(), "updated_by": identity.user.user_id}


@app.post("/api/auth/users/{user_id}/reset-password")
async def auth_reset_user_password(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_admin()
    try:
        user = reset_user_password(DB_PATH, user_id=user_id, password=str(payload.get("password") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user": user.to_dict(), "updated_by": identity.user.user_id}


@app.get("/api/auth/clients")
def auth_clients() -> dict[str, Any]:
    require_internal("read")
    items = []
    for client in load_all_clients(DB_PATH):
        members = load_client_users_for_client(DB_PATH, client.client_id)
        items.append(client.to_dict() | {"members": [member.to_dict() for member in members]})
    return {"items": items}


@app.post("/api/auth/clients")
async def auth_create_client(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_internal("write")
    try:
        client = create_client_account(DB_PATH, name=str(payload.get("name") or ""), company=str(payload.get("company") or ""), created_by=identity.user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"client": client.to_dict()}


@app.post("/api/auth/clients/{client_id}/users")
async def auth_link_client_user(client_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    require_internal("write")
    email = str(payload.get("email") or "").strip()
    user = load_user_by_email_safe(email)
    try:
        if user is None:
            user = create_user(
                DB_PATH,
                email=email,
                password=str(payload.get("password") or secrets.token_urlsafe(10)),
                name=str(payload.get("name") or ""),
                user_type="client",
                role=str(payload.get("role") or "client_viewer"),
                client_id=client_id,
            )
        link = link_client_user(DB_PATH, client_id, user.user_id, str(payload.get("role") or user.role or "client_viewer"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user": user.to_dict(), "link": link.to_dict()}


def load_user_by_email_safe(email: str) -> Any:
    from src.auth.storage import load_user_by_email

    return load_user_by_email(DB_PATH, email) if email else None


@app.post("/api/auth/project-access")
async def auth_grant_project_access(payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_internal("write")
    try:
        access = grant_project_access(
            DB_PATH,
            user_id=str(payload.get("user_id") or ""),
            client_id=str(payload.get("client_id") or ""),
            proposal_id=str(payload.get("proposal_id") or ""),
            campaign_id=str(payload.get("campaign_id") or ""),
            permissions=[str(item) for item in payload.get("permissions") or ["view"]],
            created_by=identity.user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"access": access.to_dict()}


@app.get("/api/auth/project-access")
def auth_project_access() -> dict[str, Any]:
    require_internal("read")
    return {"items": [access.to_dict() for access in load_all_project_access(DB_PATH)]}


@app.get("/api/client/portal/projects")
def client_portal_projects() -> dict[str, Any]:
    identity = require_identity()
    if identity.user.user_type != "client":
        raise HTTPException(status_code=403, detail="client user required")
    proposals = []
    for proposal in load_all_proposals(DB_PATH):
        if can_access_proposal(DB_PATH, identity, proposal.client_id, proposal.proposal_id):
            proposals.append(asdict(proposal) | {"share_url": proposal.public_url()})
    return {"items": proposals}


@app.get("/api/client/portal/proposals/{proposal_id}")
def client_portal_proposal(proposal_id: str) -> dict[str, Any]:
    identity = require_identity()
    proposal = load_proposal(DB_PATH, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    if not can_access_proposal(DB_PATH, identity, proposal.client_id, proposal.proposal_id):
        raise HTTPException(status_code=403, detail="permission denied")
    version = _current_version(proposal, load_versions(DB_PATH, proposal_id))
    if version is None:
        raise HTTPException(status_code=404, detail="proposal version not found")
    return public_proposal_payload(proposal, version, load_feedback(DB_PATH, proposal_id))


@app.post("/api/client/portal/proposals/{proposal_id}/feedback")
async def client_portal_feedback(proposal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    identity = require_identity()
    proposal = load_proposal(DB_PATH, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    if not can_access_proposal(DB_PATH, identity, proposal.client_id, proposal.proposal_id, action="comment"):
        raise HTTPException(status_code=403, detail="permission denied")
    if identity.user.role == "client_viewer":
        raise HTTPException(status_code=403, detail="comment permission required")
    version = _current_version(proposal, load_versions(DB_PATH, proposal.proposal_id))
    if version is None:
        raise HTTPException(status_code=404, detail="proposal version not found")
    feedback = record_feedback(
        DB_PATH,
        proposal,
        version,
        target_type=str(payload.get("target_type") or "proposal"),
        target_id=str(payload.get("target_id") or ""),
        decision=str(payload.get("decision") or ""),
        reason=str(payload.get("reason") or ""),
        comment=str(payload.get("comment") or ""),
        created_by=identity.user.user_id,
    )
    upsert_version(DB_PATH, version)
    proposal.status = "待调整" if feedback.decision in {"rejected", "maybe"} else proposal.status
    proposal.updated_at = _now()
    upsert_proposal(DB_PATH, proposal)
    return {"feedback": asdict(feedback), "proposal": public_proposal_payload(proposal, version, load_feedback(DB_PATH, proposal.proposal_id))}


def _masked(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _store_uploaded_object(content: bytes, filename: str, category: str = "imports") -> dict[str, Any]:
    tenant = tenant_from_path(DB_PATH)
    key = make_upload_key(tenant, filename or "upload", category=category)
    stored = get_object_store().put_bytes(
        content,
        key,
        content_type=guess_content_type(filename or "upload"),
        metadata={
            "tenant": tenant,
            "filename": filename or "upload",
            "category": category,
        },
    )
    return stored.to_dict()


def _append_creator_media_asset(profile: CreatorProfile, stored: dict[str, Any], image_type: str = "unknown") -> CreatorProfile:
    data = asdict(profile)
    asset = {
        "provider": stored.get("provider", ""),
        "bucket": stored.get("bucket", ""),
        "key": stored.get("key", ""),
        "url": stored.get("url", ""),
        "content_type": stored.get("content_type", ""),
        "size": stored.get("size", 0),
        "image_type": image_type,
        "uploaded_at": _now(),
    }
    media_assets = [item for item in data.get("media_assets", []) if isinstance(item, dict)]
    media_assets.append(asset)
    data["media_assets"] = media_assets[-20:]
    data["data_sources"] = sorted(set(data.get("data_sources", []) + ["image_upload"]))
    if image_type == "avatar" and stored.get("url") and not data.get("avatar_url"):
        data["avatar_url"] = str(stored.get("url"))
    return CreatorProfile(**data)


@app.get("/api/settings/data-sources")
def data_sources_status() -> dict[str, Any]:
    glm = GlmClient()
    mirofish = MiroFishCliAdapter()
    oneapi_key = os.getenv("ONEAPI_API_KEY", "")
    oneapi_base = os.getenv("ONEAPI_BASE_URL", "https://api.getoneapi.com")
    storage_status = storage_runtime_status(DB_PATH)
    agent_status = agent_runtime_status()
    openclaw_status = OpenClawAdapter().status(DB_PATH)
    return {
        "items": [
            {
                "id": "excel",
                "label": "Excel / CSV",
                "type": "file",
                "configured": True,
                "available": True,
                "status": "ready",
                "detail": "支持多 sheet 表格、模板映射和强去重。",
            },
            {
                "id": "mock_api",
                "label": "Mock API",
                "type": "api",
                "configured": True,
                "available": True,
                "status": "ready",
                "detail": "本地演示用达人 API，不依赖外部网络。",
            },
            {
                "id": "oneapi",
                "label": "OneAPI KOL 数据",
                "type": "api",
                "configured": bool(oneapi_key),
                "available": bool(oneapi_key),
                "status": "configured" if oneapi_key else "missing_key",
                "detail": "支持抖音、小红书、B站、快手、微博 ID 查询；生产前需核验套餐和字段覆盖。",
                "env": {"ONEAPI_API_KEY": _masked(oneapi_key), "ONEAPI_BASE_URL": oneapi_base},
                "platforms": list(OneApiConnector.ENDPOINTS.keys()),
            },
            {
                "id": "glm",
                "label": "GLM 符号分析",
                "type": "llm",
                "configured": glm.available,
                "available": glm.available,
                "status": "configured" if glm.available else "fallback",
                "detail": "用于符号档案和品牌分析；未配置时自动使用规则 fallback。",
                "env": {"GLM_API_KEY": _masked(glm.api_key), "GLM_MODEL": glm.model, "GLM_BASE_URL": glm.base_url},
            },
            {
                "id": "agent_runtime",
                "label": "Agent Runtime Adapter",
                "type": "agent",
                "configured": True,
                "available": agent_status["active"]["available"],
                "status": agent_status["active"]["mode"],
                "detail": agent_status["active"]["message"],
                "env": agent_status["env"],
                "runtimes": agent_status["available_runtimes"],
            },
            {
                "id": "openclaw",
                "label": "OpenClaw Sidecar",
                "type": "agent",
                "configured": openclaw_status["configured"],
                "available": openclaw_status["available"],
                "status": "enabled" if openclaw_status["enabled"] else "disabled",
                "detail": openclaw_status["message"],
                "env": {
                    "OPENCLAW_GATEWAY_URL": openclaw_status["gateway_url"],
                    "OPENCLAW_CONTROL_UI_URL": openclaw_status.get("control_ui_url", ""),
                    "OPENCLAW_DEFAULT_AGENT_ID": openclaw_status["default_agent_id"],
                },
            },
            {
                "id": "mirofish",
                "label": "MiroFish CLI",
                "type": "simulation",
                "configured": mirofish.available(),
                "available": mirofish.available(),
                "status": "installed" if mirofish.available() else "not_installed",
                "detail": "可选推演引擎；未安装时使用 OS fallback simulation layer。",
            },
            {
                "id": "object_store",
                "label": "对象存储 Adapter",
                "type": "storage",
                "configured": storage_status["object_store"]["configured"],
                "available": storage_status["object_store"]["available"],
                "status": storage_status["object_store"]["provider"],
                "detail": storage_status["object_store"]["detail"],
                "env": storage_status["env"],
            },
        ]
    }


@app.get("/api/settings/storage")
def storage_settings() -> dict[str, Any]:
    return storage_runtime_status(DB_PATH)


@app.post("/api/settings/data-sources/test")
async def test_data_source(payload: dict[str, Any]) -> dict[str, Any]:
    source_id = str(payload.get("source_id") or payload.get("id") or "").strip()
    if source_id == "excel":
        return {"source_id": source_id, "ok": True, "message": "Excel / CSV 导入模块可用。"}
    if source_id == "mock_api":
        connector = MockApiConnector()
        profile = connector.fetch_creator(str(payload.get("platform") or "小红书"), str(payload.get("identifier") or "demo_001"))
        return {"source_id": source_id, "ok": True, "message": "Mock API 可用。", "sample": profile_payload(profile)}
    if source_id == "agent_runtime":
        status = agent_runtime_status()
        return {"source_id": source_id, "ok": True, "message": status["active"]["message"], "runtime": status}
    if source_id == "openclaw":
        status = OpenClawAdapter().status(DB_PATH)
        return {"source_id": source_id, "ok": bool(status["available"]), "message": status["message"], "status": status}
    if source_id == "oneapi":
        api_key = str(payload.get("api_key") or os.getenv("ONEAPI_API_KEY", ""))
        base_url = str(payload.get("base_url") or os.getenv("ONEAPI_BASE_URL", "https://api.getoneapi.com"))
        platform = str(payload.get("platform") or "小红书")
        identifier = str(payload.get("identifier") or "")
        if not api_key:
            return {"source_id": source_id, "ok": False, "message": "缺少 ONEAPI_API_KEY。"}
        if not identifier:
            return {"source_id": source_id, "ok": True, "message": "OneAPI key 已配置；填写平台 ID 后可做真实查询。"}
        try:
            profile = OneApiConnector(api_key=api_key, base_url=base_url, timeout=20).fetch_creator(platform, identifier)
            return {"source_id": source_id, "ok": True, "message": "OneAPI 查询成功。", "sample": profile_payload(profile)}
        except Exception as exc:
            return {"source_id": source_id, "ok": False, "message": str(exc)}
    if source_id == "glm":
        glm = GlmClient()
        if not glm.available:
            return {"source_id": source_id, "ok": False, "message": "缺少 GLM_API_KEY，当前会使用规则 fallback。"}
        return {"source_id": source_id, "ok": True, "message": f"GLM 已配置：{glm.model}。"}
    if source_id == "mirofish":
        mirofish = MiroFishCliAdapter()
        return {
            "source_id": source_id,
            "ok": mirofish.available(),
            "message": "MiroFish CLI 可用。" if mirofish.available() else "MiroFish CLI 未安装，当前使用 OS fallback simulation layer。",
        }
    if source_id == "object_store":
        status = storage_runtime_status(DB_PATH)["object_store"]
        return {"source_id": source_id, "ok": bool(status.get("available")), "message": status.get("detail", ""), "status": status}
    raise HTTPException(status_code=400, detail="unknown data source")


@app.get("/api/creators")
def creators() -> dict[str, Any]:
    profiles = load_profiles(DB_PATH)
    return {"items": [profile_payload(profile) for profile in profiles]}


@app.get("/api/creators/{creator_id}")
def creator_detail(creator_id: str) -> dict[str, Any]:
    profile = load_profile(DB_PATH, creator_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="creator not found")
    return {"creator": profile_payload(profile), "evidence_tags": list_creator_evidence_tags(DB_PATH, creator_id=creator_id)}


@app.post("/api/creators/{creator_id}/media/analyze")
async def analyze_creator_media(creator_id: str, file: UploadFile = File(...)) -> dict[str, Any]:
    profile = load_profile(DB_PATH, creator_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="creator not found")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty upload")
    content_type = file.content_type or guess_content_type(file.filename or "upload")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="only image uploads are supported")
    stored = _store_uploaded_object(content, file.filename or "creator-image", category="creator-media")
    analysis = analyze_creator_image(
        content,
        content_type,
        filename=file.filename or "",
        context={
            "creator_id": profile.creator_id,
            "name": profile.name,
            "platform": profile.platform,
            "homepage_url": profile.homepage_url,
            "bio": profile.bio,
        },
    )
    updated = _append_creator_media_asset(profile, stored, image_type=analysis.get("image_type", "unknown"))
    save_profile(DB_PATH, updated)
    return {
        "creator": profile_payload(updated),
        "stored_object": stored,
        "analysis": analysis,
        "suggested_patch": analysis.get("extracted_fields", {}),
    }


@app.patch("/api/creators/{creator_id}")
async def update_creator(creator_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    profile = load_profile(DB_PATH, creator_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="creator not found")
    data = asdict(profile)
    data = _apply_creator_payload(data, payload)
    updated = enrich_profiles([CreatorProfile(**data)])[0]
    save_profile(DB_PATH, updated)
    return {"creator": profile_payload(updated)}


@app.delete("/api/creators/{creator_id}")
async def delete_creator(creator_id: str) -> dict[str, Any]:
    profile = load_profile(DB_PATH, creator_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="creator not found")
    delete_cases_for_creator(DB_PATH, creator_id)
    delete_profiles(DB_PATH, [creator_id])
    return {"deleted": True, "creator_id": creator_id, "name": profile.name}


def _case_payload(case: object) -> dict[str, Any]:
    from src.creator_commercial.schemas import CreatorCase

    return case.to_dict() if isinstance(case, CreatorCase) else asdict(case)


@app.get("/api/cases")
def list_creator_cases(q: str = "", creator_id: str = "") -> dict[str, Any]:
    items = load_all_cases(DB_PATH)
    if creator_id:
        items = [item for item in items if item.creator_id == creator_id]
    if q:
        query = q.strip().lower()
        items = [
            item
            for item in items
            if query
            in " ".join(
                [
                    item.creator_name,
                    item.brand_name,
                    item.industry,
                    item.product,
                    item.platform,
                    item.content_format,
                    item.content_topic,
                    item.cooperation_goal,
                    item.comment_feedback,
                    item.reuse_suggestion,
                    " ".join(item.active_tags),
                ]
            ).lower()
        ]
    return {"items": [_case_payload(item) for item in items], "total": len(items)}


@app.post("/api/cases")
async def create_creator_case(payload: dict[str, Any]) -> dict[str, Any]:
    creator_id = str(payload.get("creator_id") or "").strip()
    if not creator_id:
        raise HTTPException(status_code=400, detail="creator_id is required")
    creator = load_profile(DB_PATH, creator_id)
    if creator is None:
        raise HTTPException(status_code=404, detail="creator not found")
    case = save_creator_case(DB_PATH, creator, payload)
    return {"case": _case_payload(case)}


@app.patch("/api/cases/{case_id}")
async def update_creator_case(case_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = load_case(DB_PATH, case_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="case not found")
    creator = load_profile(DB_PATH, str(payload.get("creator_id") or existing.creator_id))
    if creator is None:
        raise HTTPException(status_code=404, detail="creator not found")
    merged = {**existing.to_dict(), **payload, "case_id": case_id}
    case = save_creator_case(DB_PATH, creator, merged)
    return {"case": _case_payload(case)}


@app.delete("/api/cases/{case_id}")
async def remove_creator_case(case_id: str) -> dict[str, Any]:
    existing = load_case(DB_PATH, case_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="case not found")
    delete_case(DB_PATH, case_id)
    return {"deleted": True, "case_id": case_id, "brand_name": existing.brand_name}


@app.get("/api/governance/summary")
def governance_status() -> dict[str, Any]:
    return governance_summary(load_profiles(DB_PATH))


@app.get("/api/governance/duplicates")
def governance_duplicates(limit: int = 100) -> dict[str, Any]:
    return {"items": find_duplicate_candidates(load_profiles(DB_PATH), limit=limit)}


@app.get("/api/governance/quality")
def governance_quality(limit: int = 200) -> dict[str, Any]:
    return {"items": quality_issues(load_profiles(DB_PATH), limit=limit)}


@app.post("/api/governance/merge")
async def governance_merge(payload: dict[str, Any]) -> dict[str, Any]:
    primary_id = str(payload.get("primary_id") or "").strip()
    duplicate_ids = [str(item).strip() for item in payload.get("duplicate_ids") or [] if str(item).strip()]
    if not primary_id or not duplicate_ids:
        raise HTTPException(status_code=400, detail="primary_id and duplicate_ids are required")
    try:
        merged = merge_profiles(DB_PATH, primary_id, duplicate_ids)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="primary profile not found") from exc
    return {"merged": profile_payload(merged)}


@app.get("/api/symbolic/creators")
def symbolic_creators() -> dict[str, Any]:
    profiles = load_all_creator_symbolic(DB_PATH)
    return {"items": [profile.to_dict() for profile in profiles]}


@app.get("/api/symbolic/brands")
def symbolic_brands() -> dict[str, Any]:
    profiles = load_all_brand_symbolic(DB_PATH)
    return {"items": [profile.to_dict() for profile in profiles]}


@app.get("/api/symbolic-os")
def symbolic_os() -> dict[str, Any]:
    return symbolic_os_snapshot(DB_PATH)


@app.get("/api/kol-intelligence")
def kol_intelligence() -> dict[str, Any]:
    return kol_intelligence_snapshot(DB_PATH)


@app.get("/api/kol-intelligence/tags")
def kol_intelligence_tags(creator_id: str = "") -> dict[str, Any]:
    return {"items": list_creator_evidence_tags(DB_PATH, creator_id=creator_id)}


@app.get("/api/kol-intelligence/review-queue")
def kol_intelligence_review_queue(status: str = "", creator_id: str = "", limit: int = 80) -> dict[str, Any]:
    return evidence_review_queue(DB_PATH, status=status, creator_id=creator_id, limit=limit)


@app.post("/api/kol-intelligence/analyze-tags")
async def kol_intelligence_analyze_tags(payload: dict[str, Any]) -> dict[str, Any]:
    return analyze_creator_evidence_tags(
        DB_PATH,
        creator_id=str(payload.get("creator_id") or ""),
        limit=int(payload.get("limit") or 200),
    )


@app.patch("/api/kol-intelligence/tags/{tag_id}")
async def kol_intelligence_review_tag(tag_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    identity = current_identity()
    reviewer = identity.user.email if identity else ""
    try:
        tag = review_evidence_tag(DB_PATH, tag_id, payload, reviewer=reviewer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="tag not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"tag": tag.to_dict(), "snapshot": kol_intelligence_snapshot(DB_PATH)}


@app.post("/api/kol-intelligence/tags/bulk-review")
async def kol_intelligence_bulk_review_tags(payload: dict[str, Any]) -> dict[str, Any]:
    identity = current_identity()
    reviewer = identity.user.email if identity else ""
    try:
        result = bulk_review_evidence_tags(DB_PATH, payload, reviewer=reviewer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["snapshot"] = kol_intelligence_snapshot(DB_PATH)
    return result


@app.post("/api/kol-intelligence/graph")
async def kol_intelligence_graph(payload: dict[str, Any]) -> dict[str, Any]:
    creator_ids = payload.get("creator_ids") if isinstance(payload.get("creator_ids"), list) else []
    snapshot = build_kol_knowledge_graph(
        DB_PATH,
        brief=str(payload.get("brief") or ""),
        creator_ids=[str(item) for item in creator_ids],
        limit=int(payload.get("limit") or 80),
    )
    return snapshot.to_dict()


@app.post("/api/kol-intelligence/predict")
async def kol_intelligence_predict(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        prediction = predict_kol_fit(
            DB_PATH,
            brief=str(payload.get("brief") or ""),
            top_n=int(payload.get("top_n") or 8),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return prediction.to_dict()


@app.post("/api/kol-intelligence/conversation/run")
async def kol_intelligence_conversation_run(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return run_conversational_kol_graph(DB_PATH, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/symbolic-os/social-reports")
def symbolic_os_social_reports() -> dict[str, Any]:
    return {"items": [item.to_dict() for item in load_all_social_reports(DB_PATH)]}


@app.post("/api/symbolic-os/social-reports")
async def create_symbolic_os_social_report(payload: dict[str, Any]) -> dict[str, Any]:
    report = generate_social_symbolic_report(DB_PATH, payload)
    return {"report": report.to_dict(), "snapshot": symbolic_os_snapshot(DB_PATH)}


@app.get("/api/symbolic-os/signifier-tags")
def symbolic_os_signifier_tags() -> dict[str, Any]:
    return {"items": [item.to_dict() for item in load_all_signifier_tags(DB_PATH)]}


@app.post("/api/symbolic-os/signifier-tags")
async def create_symbolic_os_signifier_tag(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    tag_type = str(payload.get("tag_type") or "传播标签")
    tag = SignifierTag(
        tag_id=str(payload.get("tag_id") or tag_id_for(name, tag_type)),
        name=name,
        tag_type=tag_type,
        parent=str(payload.get("parent") or ""),
        children=_coerce_symbolic_value("children", payload.get("children") or []),
        related_tags=_coerce_symbolic_value("related_tags", payload.get("related_tags") or []),
        opposite_tags=_coerce_symbolic_value("opposite_tags", payload.get("opposite_tags") or []),
        metaphor_relations=_coerce_symbolic_value("metaphor_relations", payload.get("metaphor_relations") or []),
        metonymy_relations=_coerce_symbolic_value("metonymy_relations", payload.get("metonymy_relations") or []),
        emotion=str(payload.get("emotion") or ""),
        suitable_industries=_coerce_symbolic_value("suitable_industries", payload.get("suitable_industries") or []),
        suitable_creator_types=_coerce_symbolic_value("suitable_creator_types", payload.get("suitable_creator_types") or []),
        suitable_content_forms=_coerce_symbolic_value("suitable_content_forms", payload.get("suitable_content_forms") or []),
        risk_notes=str(payload.get("risk_notes") or ""),
        examples=_coerce_symbolic_value("examples", payload.get("examples") or []),
        source=str(payload.get("source") or "manual"),
    )
    upsert_signifier_tag(DB_PATH, tag)
    return {"tag": tag.to_dict(), "snapshot": symbolic_os_snapshot(DB_PATH)}


@app.get("/api/symbolic-os/products")
def symbolic_os_products() -> dict[str, Any]:
    return {"items": [item.to_dict() for item in load_all_product_symbolic(DB_PATH)]}


@app.post("/api/symbolic-os/products")
async def create_symbolic_os_product(payload: dict[str, Any]) -> dict[str, Any]:
    profile = generate_product_symbolic_profile(DB_PATH, payload)
    return {"profile": profile.to_dict(), "snapshot": symbolic_os_snapshot(DB_PATH)}


@app.patch("/api/symbolic-os/products/{product_id}")
async def update_symbolic_os_product(product_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    profile = load_product_symbolic(DB_PATH, product_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="product symbolic profile not found")
    data = profile.to_dict()
    editable = {
        "brand_id",
        "brand_name",
        "product_name",
        "category",
        "physical_attributes",
        "use_scenarios",
        "target_users",
        "functional_value",
        "emotional_value",
        "identity_value",
        "metaphors",
        "metonymies",
        "association_words",
        "anti_association_words",
        "suitable_content_scenarios",
        "suitable_creator_types",
        "unsuitable_creator_types",
        "social_issue_hooks",
        "risk_notes",
        "evidence",
        "confidence",
        "source",
    }
    for field in editable:
        if field in payload:
            data[field] = _coerce_symbolic_value(field, payload[field])
    from src.symbolic.os_schemas import ProductSymbolicProfile

    updated = ProductSymbolicProfile.from_json(json.dumps(data, ensure_ascii=False))
    upsert_product_symbolic(DB_PATH, updated)
    return {"profile": updated.to_dict(), "snapshot": symbolic_os_snapshot(DB_PATH)}


@app.get("/api/symbolic-os/narratives")
def symbolic_os_narratives() -> dict[str, Any]:
    return {"items": [item.to_dict() for item in load_all_content_narratives(DB_PATH)]}


@app.post("/api/symbolic-os/narratives")
async def create_symbolic_os_narratives(payload: dict[str, Any]) -> dict[str, Any]:
    assets = create_content_narrative_assets(DB_PATH, payload)
    return {"items": [item.to_dict() for item in assets], "snapshot": symbolic_os_snapshot(DB_PATH)}


@app.patch("/api/symbolic-os/narratives/{narrative_id}")
async def update_symbolic_os_narrative(narrative_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    asset = load_content_narrative(DB_PATH, narrative_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="content narrative asset not found")
    data = asset.to_dict()
    editable = {
        "project",
        "brand_id",
        "brand_name",
        "product_id",
        "product_name",
        "creator_id",
        "creator_name",
        "target_tag",
        "start_tag",
        "mediating_tags",
        "narrative_path",
        "metaphor_strategy",
        "metonymy_strategy",
        "emotion_strategy",
        "title_directions",
        "content_brief",
        "suitable_creator_types",
        "must_include",
        "must_avoid",
        "comment_guidance",
        "risk_words",
        "client_status",
        "source",
    }
    for field in editable:
        if field in payload:
            data[field] = _coerce_symbolic_value(field, payload[field])
    from src.symbolic.os_schemas import ContentNarrativeAsset

    updated = ContentNarrativeAsset.from_json(json.dumps(data, ensure_ascii=False))
    upsert_content_narrative(DB_PATH, updated)
    return {"asset": updated.to_dict(), "snapshot": symbolic_os_snapshot(DB_PATH)}


@app.get("/api/symbolic-os/matches")
def symbolic_os_matches() -> dict[str, Any]:
    return {"items": [item.to_dict() for item in load_all_brand_creator_matches(DB_PATH)]}


@app.post("/api/symbolic-os/matches")
async def create_symbolic_os_matches(payload: dict[str, Any]) -> dict[str, Any]:
    assets = create_brand_creator_match_assets(DB_PATH, payload)
    return {"items": [item.to_dict() for item in assets], "snapshot": symbolic_os_snapshot(DB_PATH)}


@app.patch("/api/symbolic-os/matches/{match_id}")
async def update_symbolic_os_match(match_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    asset = load_brand_creator_match(DB_PATH, match_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="brand creator match asset not found")
    data = asset.to_dict()
    editable = {
        "manual_status",
        "client_status",
        "suggested_priority",
        "match_reason",
        "risk_points",
        "suggested_content_direction",
        "case_basis",
        "evidence",
    }
    for field in editable:
        if field in payload:
            data[field] = _coerce_symbolic_value(field, payload[field])
    from src.symbolic.os_schemas import BrandCreatorMatchAsset

    updated = BrandCreatorMatchAsset.from_json(json.dumps(data, ensure_ascii=False))
    upsert_brand_creator_match(DB_PATH, updated)
    return {"asset": updated.to_dict(), "snapshot": symbolic_os_snapshot(DB_PATH)}


@app.post("/api/import/sample")
def import_sample(replace: bool = True) -> dict[str, Any]:
    sample = ROOT / "data" / "raw" / "sample_creators.csv"
    df = pd.read_csv(sample)
    profiles = enrich_profiles(map_dataframe_to_profiles(df, source="sample_csv"))
    if replace:
        replace_profiles(DB_PATH, profiles)
    else:
        upsert_profiles(DB_PATH, profiles)
    return {"imported": len(profiles)}


@app.get("/api/import/templates")
def import_templates() -> dict[str, Any]:
    return {"items": load_templates(TEMPLATE_PATH)}


@app.delete("/api/import/templates/{template_id}")
def remove_import_template(template_id: str) -> dict[str, Any]:
    if not delete_template(TEMPLATE_PATH, template_id):
        raise HTTPException(status_code=404, detail="template not found")
    return {"deleted": template_id}


@app.post("/api/import/templates")
async def save_import_template(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or "").strip()
    sheets = payload.get("sheets") or {}
    if not isinstance(sheets, dict):
        raise HTTPException(status_code=400, detail="sheets must be an object")
    template = upsert_template(TEMPLATE_PATH, name, sheets, template_id=payload.get("template_id"))
    return {"template": template}


@app.post("/api/import/file/preview")
async def preview_file_import(file: UploadFile = File(...), template_id: Optional[str] = Form(None)) -> dict[str, Any]:
    content = await file.read()
    holder = BytesIO(content)
    holder.name = file.filename or "upload"
    tables = load_table_file(holder)
    if not tables:
        raise HTTPException(status_code=400, detail="未识别到可导入的表格")
    templates = load_templates(TEMPLATE_PATH)
    template = next((item for item in templates if item.get("id") == template_id), None) if template_id else None
    match_score = 0
    if template is None:
        template, match_score = find_best_template(templates, tables)
    else:
        _, match_score = find_best_template([template], tables)
    review = _build_import_review(tables, template=template)
    review["filename"] = file.filename or "upload"
    review["matched_template"] = {"id": template.get("id"), "name": template.get("name"), "score": match_score} if template else None
    return review


@app.post("/api/agent/import/preview")
async def preview_agent_creator_import(request: Request, file: UploadFile = File(...), template_id: Optional[str] = Form(None)) -> dict[str, Any]:
    identity = require_internal("write")
    content = await file.read()
    return _preview_creator_import(content, file.filename or "upload", template_id=template_id, created_by=identity.user.user_id)


@app.post("/api/agent/import/{import_id}/commit")
async def commit_agent_creator_import(import_id: str, payload: dict[str, Any], request: Request) -> dict[str, Any]:
    require_internal("write")
    return _commit_creator_import(
        import_id,
        mappings=payload.get("mappings") if isinstance(payload.get("mappings"), dict) else None,
        replace=bool(payload.get("replace")),
        save_template=bool(payload.get("save_template")),
        template_name=str(payload.get("template_name") or ""),
        template_id=str(payload.get("template_id") or "").strip() or None,
    )


@app.post("/api/import/file/commit")
async def commit_file_import(
    file: UploadFile = File(...),
    mappings: str = Form("{}"),
    replace: bool = Form(False),
    save_template: bool = Form(False),
    template_name: str = Form(""),
    template_id: Optional[str] = Form(None),
) -> dict[str, Any]:
    content = await file.read()
    source_object = _store_uploaded_object(content, file.filename or "upload", category="imports")
    holder = BytesIO(content)
    holder.name = file.filename or "upload"
    tables = load_table_file(holder)
    if not tables:
        raise HTTPException(status_code=400, detail="未识别到可导入的表格")
    try:
        payload = json.loads(mappings or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="mappings must be valid JSON") from exc

    profiles = []
    sheet_counts: dict[str, int] = {}
    skipped_sheets: list[str] = []
    for sheet_name, df in tables.items():
        sheet_payload = payload.get(sheet_name, {}) if isinstance(payload, dict) else {}
        if sheet_payload.get("enabled") is False:
            skipped_sheets.append(sheet_name)
            continue
        mapping = sheet_payload.get("mapping") if isinstance(sheet_payload, dict) else None
        if not isinstance(mapping, dict):
            mapping = infer_column_mapping(df)
        sheet_profiles = map_dataframe_to_profiles(df, source=f"file:{sheet_name}", column_mapping=mapping)
        if not sheet_profiles:
            skipped_sheets.append(sheet_name)
            sheet_counts[sheet_name] = 0
            continue
        profiles.extend(sheet_profiles)
        sheet_counts[sheet_name] = len(sheet_profiles)

    profiles, dedupe_report = strong_dedupe_profiles(profiles)
    profiles = enrich_profiles(profiles)
    saved_template = None
    if save_template:
        saved_template = upsert_template(
            TEMPLATE_PATH,
            template_name or (file.filename or "导入模板"),
            payload if isinstance(payload, dict) else {},
            template_id=template_id,
        )
    if replace:
        replace_profiles(DB_PATH, profiles)
    else:
        upsert_profiles(DB_PATH, profiles)
    return {
        "imported": len(profiles),
        "sheet_counts": sheet_counts,
        "skipped_sheets": skipped_sheets,
        "sheets": list(tables.keys()),
        "source_object": source_object,
        "saved_template": saved_template,
        "quality_report": _quality_report(profiles, sheet_counts, skipped_sheets) | {"dedupe": dedupe_report},
    }


@app.post("/api/import/file")
async def import_file(
    file: UploadFile = File(...),
    sheet: Optional[str] = Form(None),
    replace: bool = Form(False),
    all_sheets: bool = Form(True),
) -> dict[str, Any]:
    content = await file.read()
    source_object = _store_uploaded_object(content, file.filename or "upload", category="imports")
    holder = BytesIO(content)
    holder.name = file.filename or "upload"
    tables = load_table_file(holder)
    selected_sheets = list(tables.keys()) if all_sheets or not sheet else [sheet if sheet in tables else next(iter(tables))]
    profiles = []
    sheet_counts: dict[str, int] = {}
    for selected_sheet in selected_sheets:
        sheet_profiles = map_dataframe_to_profiles(tables[selected_sheet], source=f"file:{selected_sheet}")
        profiles.extend(sheet_profiles)
        sheet_counts[selected_sheet] = len(sheet_profiles)
    profiles = enrich_profiles(profiles)
    if replace:
        replace_profiles(DB_PATH, profiles)
    else:
        upsert_profiles(DB_PATH, profiles)
    return {"imported": len(profiles), "sheet_counts": sheet_counts, "sheets": list(tables.keys()), "source_object": source_object}


@app.post("/api/import/links")
async def import_links(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("links", "")
    lines = raw.splitlines() if isinstance(raw, str) else list(raw or [])
    profiles = enrich_profiles(parse_links(lines))
    upsert_profiles(DB_PATH, profiles)
    return {"imported": len(profiles)}


@app.post("/api/kol-intake")
async def kol_intake(
    input_type: str = Form("auto"),
    text: str = Form(""),
    name: str = Form(""),
    replace: bool = Form(False),
    file: UploadFile | None = File(None),
) -> dict[str, Any]:
    require_internal("write")
    content = await file.read() if file is not None else b""
    filename = file.filename if file is not None else ""
    content_type = file.content_type or guess_content_type(filename or "upload") if file is not None else ""
    mode = (input_type or "auto").strip().lower()
    if mode == "auto":
        if content and content_type.startswith("image/"):
            mode = "image"
        elif content:
            mode = "file"
        else:
            mode = "text"

    if mode == "text":
        payload = _parse_creator_text(text, fallback_name=name)
        profiles = _profiles_from_payloads([payload], source="kol_intake:text")
        if not profiles:
            raise HTTPException(status_code=400, detail="未识别到可保存的 KOL 信息")
        upsert_profiles(DB_PATH, profiles)
        return _kol_intake_response(profiles, "text", {"parsed_fields": payload})

    if mode == "file":
        if not content:
            raise HTTPException(status_code=400, detail="file is required")
        source_object = _store_uploaded_object(content, filename or "upload", category="kol-intake")
        holder = BytesIO(content)
        holder.name = filename or "upload"
        tables = load_table_file(holder)
        if not tables:
            raise HTTPException(status_code=400, detail="未识别到可导入的表格")
        profiles: list[CreatorProfile] = []
        sheet_counts: dict[str, int] = {}
        for sheet_name, df in tables.items():
            sheet_profiles = map_dataframe_to_profiles(df, source=f"kol_intake:file:{sheet_name}", column_mapping=infer_column_mapping(df))
            profiles.extend(sheet_profiles)
            sheet_counts[sheet_name] = len(sheet_profiles)
        profiles, dedupe_report = strong_dedupe_profiles(profiles)
        profiles = enrich_profiles(profiles)
        if replace:
            replace_profiles(DB_PATH, profiles)
        else:
            upsert_profiles(DB_PATH, profiles)
        return _kol_intake_response(
            profiles,
            "file",
            {
                "sheet_counts": sheet_counts,
                "source_object": source_object,
                "quality_report": _quality_report(profiles, sheet_counts, []) | {"dedupe": dedupe_report},
            },
        )

    if mode == "image":
        if not content:
            raise HTTPException(status_code=400, detail="image file is required")
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="only image uploads are supported")
        stored = _store_uploaded_object(content, filename or "creator-image", category="creator-media")
        seed_payload = _parse_creator_text(text, fallback_name=name or Path(filename or "图片达人").stem)
        seed_profiles = _profiles_from_payloads([seed_payload], source="kol_intake:image_seed")
        if not seed_profiles:
            raise HTTPException(status_code=400, detail="未识别到图片对应的达人名称")
        profile = seed_profiles[0]
        analysis = analyze_creator_image(
            content,
            content_type,
            filename=filename or "",
            context={
                "creator_id": profile.creator_id,
                "name": profile.name,
                "platform": profile.platform,
                "bio": profile.bio,
            },
        )
        patch = analysis.get("extracted_fields") if isinstance(analysis.get("extracted_fields"), dict) else {}
        merged_payload = seed_payload | {key: value for key, value in patch.items() if value not in ["", [], 0, 0.0]}
        if not merged_payload.get("name"):
            merged_payload["name"] = profile.name
        profiles = _profiles_from_payloads([merged_payload], source="kol_intake:image")
        if not profiles:
            profiles = [profile]
        updated = _append_creator_media_asset(profiles[0], stored, image_type=analysis.get("image_type", "unknown"))
        upsert_profiles(DB_PATH, [updated])
        return _kol_intake_response(
            [updated],
            "image",
            {
                "image_analysis": analysis,
                "suggested_patch": patch,
                "source_object": stored,
                "parsed_fields": merged_payload,
            },
        )

    raise HTTPException(status_code=400, detail="input_type must be auto, text, file, or image")


@app.post("/api/creators/tags/classify")
async def classify_creator_tags_api(payload: dict[str, Any]) -> dict[str, Any]:
    tags = payload.get("tags") or payload.get("personal_tags") or []
    existing = {
        "industry_fit_tags": split_tags(payload.get("industry_fit_tags", [])),
        "identity_tags": split_tags(payload.get("identity_tags", [])),
        "content_capability_tags": split_tags(payload.get("content_capability_tags", [])),
        "delivery_tags": split_tags(payload.get("delivery_tags", [])),
        "risk_tags": split_tags(payload.get("risk_tags", [])),
        "suitable_goals": split_tags(payload.get("suitable_goals", [])),
        "cooperation_formats": split_tags(payload.get("cooperation_formats", [])),
        "budget_fit_tags": split_tags(payload.get("budget_fit_tags", [])),
        "cooperation_brands": split_tags(payload.get("cooperation_brands", [])),
        "narrative_position": str(payload.get("narrative_position", "")).strip(),
    }
    result = classify_creator_tags(tags, platform=str(payload.get("platform", "")).strip(), existing=existing)
    return {"classification": result}


@app.post("/api/creators/intake/preview")
async def preview_creator_intake(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    platform = str(payload.get("platform", "")).strip() or "未知"
    platform_user_id = str(payload.get("platform_user_id", "")).strip()
    homepage_url = str(payload.get("homepage_url", "")).strip()
    creator_id = stable_id(platform, platform_user_id or homepage_url or name)
    data = asdict(
        CreatorProfile(
            creator_id=creator_id,
            name=name,
            platform=platform,
            data_sources=["manual:preview"],
        )
    )
    data = _apply_creator_payload(data, payload)
    profile = enrich_profiles([CreatorProfile(**data)])[0]
    preview = preview_creator_intelligence(DB_PATH, profile)
    return {
        "creator": profile_payload(profile),
        "evidence_tags": preview["evidence_tags"],
        "suggested_patch": preview["suggested_patch"],
    }


@app.post("/api/creators/intake/media/analyze")
async def analyze_intake_media(
    file: UploadFile = File(...),
    context: str = Form("{}"),
) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty upload")
    content_type = file.content_type or guess_content_type(file.filename or "upload")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="only image uploads are supported")
    try:
        ctx = json.loads(context) if context else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid context json") from exc
    if not isinstance(ctx, dict):
        ctx = {}
    stored = _store_uploaded_object(content, file.filename or "creator-image", category="creator-media")
    analysis = analyze_creator_image(
        content,
        content_type,
        filename=file.filename or "",
        context={
            "name": ctx.get("name", ""),
            "platform": ctx.get("platform", ""),
            "homepage_url": ctx.get("homepage_url", ""),
            "bio": ctx.get("bio", ""),
        },
    )
    return {
        "stored_object": stored,
        "analysis": analysis,
        "suggested_patch": analysis.get("extracted_fields", {}),
    }


@app.post("/api/import/manual")
async def import_manual(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    platform = str(payload.get("platform", "")).strip() or "未知"
    platform_user_id = str(payload.get("platform_user_id", "")).strip()
    homepage_url = str(payload.get("homepage_url", "")).strip()
    creator_id = stable_id(platform, platform_user_id or homepage_url or name)
    data = asdict(
        CreatorProfile(
            creator_id=creator_id,
            name=name,
            platform=platform,
            data_sources=["manual"],
        )
    )
    data = _apply_creator_payload(data, payload)
    profiles = enrich_profiles([CreatorProfile(**data)])
    upsert_profiles(DB_PATH, profiles)
    return {"imported": len(profiles), "creator": profile_payload(profiles[0])}


@app.post("/api/import/api")
async def import_api(payload: dict[str, Any]) -> dict[str, Any]:
    provider = payload.get("provider", "mock")
    platform = payload.get("platform", "")
    identifier = payload.get("identifier", "")
    if not platform or not identifier:
        raise HTTPException(status_code=400, detail="platform and identifier are required")
    try:
        if provider == "oneapi":
            connector = OneApiConnector(api_key=str(payload.get("api_key", "")), base_url=str(payload.get("base_url") or "https://api.getoneapi.com"))
        else:
            connector = MockApiConnector()
        profile = enrich_profiles([connector.fetch_creator(platform, identifier)])[0]
        upsert_profiles(DB_PATH, [profile])
        return {"imported": 1, "provider": connector.provider_name, "creator": profile_payload(profile)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/recommend")
async def recommend(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("brief", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="brief is required")
    profiles = load_profiles(DB_PATH)
    if not profiles:
        raise HTTPException(status_code=400, detail="no creators imported")
    brief = parse_brief(text)
    if payload.get("budget"):
        brief.budget = int(payload["budget"])
    rankings = rank_creators(brief, profiles)
    top_n = int(payload.get("top_n", 20))
    proposal = generate_markdown_proposal(brief, rankings[:top_n])
    return {
        "brief": json.loads(brief.to_json()),
        "results": [result.to_table_row() | {"creator_id": result.creator.creator_id} for result in rankings[:top_n]],
        "proposal": proposal,
    }


@app.get("/api/collaboration/proposals")
def collaboration_proposals() -> dict[str, Any]:
    items = []
    for proposal in load_all_proposals(DB_PATH):
        versions = load_versions(DB_PATH, proposal.proposal_id)
        feedback = load_feedback(DB_PATH, proposal.proposal_id)
        items.append(
            asdict(proposal)
            | {
                "share_url": proposal.public_url(),
                "versions_count": len(versions),
                "feedback_count": len(feedback),
                "open_feedback_count": sum(1 for item in feedback if item.status == "open"),
            }
        )
    return {"items": items}


@app.post("/api/collaboration/proposals")
async def create_collaboration_proposal(payload: dict[str, Any]) -> dict[str, Any]:
    client_name = str(payload.get("client_name") or "未命名客户").strip()
    project_name = str(payload.get("project_name") or "未命名项目").strip()
    brief_text = str(payload.get("brief") or payload.get("brief_text") or "").strip()
    if not brief_text:
        raise HTTPException(status_code=400, detail="brief is required")
    proposal, version, markdown = create_proposal_from_brief(
        DB_PATH,
        client_name=client_name,
        project_name=project_name,
        brief_text=brief_text,
        creators=load_profiles(DB_PATH),
        top_n=int(payload.get("top_n") or 12),
        created_by=str(payload.get("created_by") or "media_user"),
    )
    upsert_proposal(DB_PATH, proposal)
    upsert_version(DB_PATH, version)
    return {"proposal": asdict(proposal) | {"share_url": proposal.public_url()}, "version": version.to_dict(), "markdown": markdown}


@app.get("/api/collaboration/proposals/{proposal_id}")
def collaboration_proposal_detail(proposal_id: str) -> dict[str, Any]:
    proposal = load_proposal(DB_PATH, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    versions = load_versions(DB_PATH, proposal_id)
    version = _current_version(proposal, versions)
    feedback = load_feedback(DB_PATH, proposal_id)
    preference = load_preference(DB_PATH, proposal.client_id)
    return {
        "proposal": asdict(proposal) | {"share_url": proposal.public_url()},
        "versions": [item.to_dict() for item in versions],
        "current": version.to_dict() if version else None,
        "feedback": [asdict(item) for item in feedback],
        "preference": asdict(preference) if preference else None,
    }


@app.patch("/api/collaboration/proposals/{proposal_id}/share")
async def update_proposal_share(proposal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    proposal = _require_proposal(proposal_id)
    if "visible_fields" in payload and isinstance(payload["visible_fields"], dict):
        visible = dict(DEFAULT_VISIBLE_FIELDS)
        visible.update({str(key): bool(value) for key, value in payload["visible_fields"].items()})
        proposal.visible_fields = visible
    if "share_enabled" in payload:
        proposal.share_enabled = bool(payload["share_enabled"])
    if "allow_comments" in payload:
        proposal.allow_comments = bool(payload["allow_comments"])
    if "allow_download" in payload:
        proposal.allow_download = bool(payload["allow_download"])
    if payload.get("expires_days"):
        proposal.expires_at = default_expires_at(int(payload["expires_days"]))
    proposal.status = "shared" if proposal.share_enabled else "draft"
    proposal.updated_at = _now()
    upsert_proposal(DB_PATH, proposal)
    return {"proposal": asdict(proposal) | {"share_url": proposal.public_url()}}


@app.post("/api/collaboration/proposals/{proposal_id}/versions")
async def create_proposal_version(proposal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    proposal = _require_proposal(proposal_id)
    versions = load_versions(DB_PATH, proposal_id)
    current = _current_version(proposal, versions)
    if current is None:
        raise HTTPException(status_code=400, detail="no base version")
    version_number = max([item.version_number for item in versions] or [0]) + 1
    candidates_payload = payload.get("candidates")
    candidates = current.candidates
    if isinstance(candidates_payload, list):
        existing = {item.creator_id: item for item in current.candidates}
        candidates = [existing[item["creator_id"]] for item in candidates_payload if isinstance(item, dict) and item.get("creator_id") in existing]
    version = ProposalVersion(
        version_id=version_id_for(proposal_id, version_number),
        proposal_id=proposal_id,
        version_number=version_number,
        summary=str(payload.get("summary") or f"v{version_number} 调整版本"),
        candidates=candidates,
        budget_total=sum(item.suggested_budget or item.listed_price for item in candidates),
    )
    proposal.current_version = version_number
    proposal.status = "待调整" if proposal.status != "已确认" else proposal.status
    proposal.updated_at = _now()
    upsert_version(DB_PATH, version)
    upsert_proposal(DB_PATH, proposal)
    return {"proposal": asdict(proposal), "version": version.to_dict()}


@app.post("/api/collaboration/proposals/{proposal_id}/finalize")
async def finalize_proposal(proposal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    proposal = _require_proposal(proposal_id)
    versions = load_versions(DB_PATH, proposal_id)
    version = _current_version(proposal, versions)
    if version is None:
        raise HTTPException(status_code=400, detail="no version to finalize")
    version.is_final = True
    proposal.status = "已确认"
    proposal.confirmed_at = _now()
    proposal.confirmed_by = str(payload.get("confirmed_by") or "client_user")
    proposal.updated_at = _now()
    upsert_version(DB_PATH, version)
    upsert_proposal(DB_PATH, proposal)
    update_preference_from_feedback(DB_PATH, proposal, version)
    return {"proposal": asdict(proposal), "version": version.to_dict()}


@app.get("/api/collaboration/proposals/{proposal_id}/versions/compare")
def compare_proposal_versions(proposal_id: str, from_version: int, to_version: int) -> dict[str, Any]:
    _require_proposal(proposal_id)
    versions = {item.version_number: item for item in load_versions(DB_PATH, proposal_id)}
    left = versions.get(from_version)
    right = versions.get(to_version)
    if left is None or right is None:
        raise HTTPException(status_code=404, detail="version not found")
    left_ids = {item.creator_id for item in left.candidates}
    right_ids = {item.creator_id for item in right.candidates}
    left_lookup = {item.creator_id: item for item in left.candidates}
    right_lookup = {item.creator_id: item for item in right.candidates}
    return {
        "from": left.to_dict(),
        "to": right.to_dict(),
        "added": [asdict(right_lookup[item]) for item in sorted(right_ids - left_ids)],
        "removed": [asdict(left_lookup[item]) for item in sorted(left_ids - right_ids)],
        "budget_delta": right.budget_total - left.budget_total,
    }


@app.post("/api/collaboration/proposals/{proposal_id}/versions/{version_number}/restore")
def restore_proposal_version(proposal_id: str, version_number: int) -> dict[str, Any]:
    proposal = _require_proposal(proposal_id)
    versions = load_versions(DB_PATH, proposal_id)
    if not any(item.version_number == version_number for item in versions):
        raise HTTPException(status_code=404, detail="version not found")
    proposal.current_version = version_number
    proposal.status = "待调整"
    proposal.updated_at = _now()
    upsert_proposal(DB_PATH, proposal)
    return collaboration_proposal_detail(proposal_id)


@app.patch("/api/collaboration/feedback/{feedback_id}")
async def update_feedback_status(feedback_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    feedback = load_feedback_item(DB_PATH, feedback_id)
    if feedback is None:
        raise HTTPException(status_code=404, detail="feedback not found")
    if payload.get("status"):
        feedback.status = str(payload["status"])
    if payload.get("comment"):
        feedback.comment = str(payload["comment"])
    if payload.get("reason"):
        feedback.reason = str(payload["reason"])
    feedback.updated_at = _now()
    upsert_feedback(DB_PATH, feedback)
    return {"feedback": asdict(feedback)}


@app.get("/api/collaboration/proposals/{proposal_id}/export")
def export_proposal_markdown(proposal_id: str) -> dict[str, Any]:
    proposal = _require_proposal(proposal_id)
    version = _current_version(proposal, load_versions(DB_PATH, proposal_id))
    if version is None:
        raise HTTPException(status_code=404, detail="version not found")
    lines = [
        f"# {proposal.project_name}",
        "",
        f"客户：{proposal.client_name}",
        f"状态：{proposal.status}",
        f"Brief：{proposal.brief_summary}",
        "",
        "## 最终候选达人",
    ]
    for item in version.candidates:
        if item.client_decision in {"approved", "pending", "maybe"}:
            lines.append(f"- {item.creator_name}｜{item.platform}｜{item.recommendation_level}｜预算 {item.suggested_budget or item.listed_price}｜状态 {item.client_decision}")
    return {"filename": f"{proposal.project_name}_final.md", "markdown": "\n".join(lines)}


@app.get("/api/client/share/{token}")
def client_share(token: str) -> dict[str, Any]:
    proposal = load_proposal_by_token(DB_PATH, token)
    if proposal is None or not proposal.share_enabled:
        raise HTTPException(status_code=404, detail="share link not available")
    versions = load_versions(DB_PATH, proposal.proposal_id)
    version = _current_version(proposal, versions)
    if version is None:
        raise HTTPException(status_code=404, detail="proposal version not found")
    proposal.access_count += 1
    proposal.last_accessed_at = _now()
    if proposal.status == "shared":
        proposal.status = "甲方已查看"
    upsert_proposal(DB_PATH, proposal)
    return public_proposal_payload(proposal, version, load_feedback(DB_PATH, proposal.proposal_id))


@app.post("/api/client/share/{token}/feedback")
async def client_feedback(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    proposal = load_proposal_by_token(DB_PATH, token)
    if proposal is None or not proposal.share_enabled:
        raise HTTPException(status_code=404, detail="share link not available")
    if not proposal.allow_comments:
        raise HTTPException(status_code=403, detail="comments are disabled")
    version = _current_version(proposal, load_versions(DB_PATH, proposal.proposal_id))
    if version is None:
        raise HTTPException(status_code=404, detail="proposal version not found")
    feedback = record_feedback(
        DB_PATH,
        proposal,
        version,
        target_type=str(payload.get("target_type") or "proposal"),
        target_id=str(payload.get("target_id") or ""),
        decision=str(payload.get("decision") or ""),
        reason=str(payload.get("reason") or ""),
        comment=str(payload.get("comment") or ""),
        created_by=str(payload.get("created_by") or "client_user"),
    )
    upsert_version(DB_PATH, version)
    proposal.status = "待调整" if feedback.decision in {"rejected", "maybe"} else proposal.status
    proposal.updated_at = _now()
    upsert_proposal(DB_PATH, proposal)
    return {"feedback": asdict(feedback), "proposal": public_proposal_payload(proposal, version, load_feedback(DB_PATH, proposal.proposal_id))}


@app.get("/api/collaboration/preferences/{client_id}")
def collaboration_preference(client_id: str) -> dict[str, Any]:
    preference = load_preference(DB_PATH, client_id)
    return {"preference": asdict(preference) if preference else None}


@app.get("/api/creator-commercial/invitations")
def creator_commercial_invitations() -> dict[str, Any]:
    return {
        "items": [
            asdict(item) | {"invite_url": f"/creator/invite/{item.token}"}
            for item in load_all_invitations(DB_PATH)
        ]
    }


@app.post("/api/creator-commercial/invitations")
async def create_commercial_invitation(payload: dict[str, Any]) -> dict[str, Any]:
    creator_ids = [str(item).strip() for item in payload.get("creator_ids") or [] if str(item).strip()]
    if not creator_ids and payload.get("creator_id"):
        creator_ids = [str(payload["creator_id"]).strip()]
    if not creator_ids:
        raise HTTPException(status_code=400, detail="creator_id or creator_ids is required")
    invitations = []
    for creator_id in creator_ids:
        creator = _find_creator(creator_id)
        invitation = create_creator_invitation(
            DB_PATH,
            creator,
            invited_by=str(payload.get("invited_by") or "media_user"),
            expires_days=int(payload.get("expires_days") or 14),
        )
        invitations.append(asdict(invitation) | {"invite_url": f"/creator/invite/{invitation.token}"})
    return {"invitation": invitations[0], "items": invitations}


@app.patch("/api/creator-commercial/invitations/{invitation_id}")
async def update_commercial_invitation(invitation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    invitation = load_invitation(DB_PATH, invitation_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="invitation not found")
    if payload.get("status"):
        invitation.status = str(payload["status"])
    if payload.get("expires_days"):
        from src.creator_commercial.schemas import expires_at

        invitation.expires_at = expires_at(int(payload["expires_days"]))
    upsert_invitation(DB_PATH, invitation)
    return {"invitation": asdict(invitation) | {"invite_url": f"/creator/invite/{invitation.token}"}}


@app.get("/api/creator/invite/{token}")
def creator_invite(token: str) -> dict[str, Any]:
    invitation = load_invitation_by_token(DB_PATH, token)
    if invitation is None or invitation.status == "revoked":
        raise HTTPException(status_code=404, detail="invitation not available")
    invitation = mark_invitation_opened(DB_PATH, invitation)
    creator = _find_creator(invitation.creator_id)
    commercial = load_commercial_profile(DB_PATH, invitation.creator_id)
    submissions = load_submissions_for_creator(DB_PATH, invitation.creator_id)
    return {
        "invitation": asdict(invitation),
        "creator": profile_payload(creator),
        "commercial_profile": commercial.to_dict() if commercial else None,
        "submissions": [asdict(item) for item in submissions],
    }


@app.post("/api/creator/invite/{token}/submit")
async def submit_creator_invite(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    invitation = load_invitation_by_token(DB_PATH, token)
    if invitation is None or invitation.status == "revoked":
        raise HTTPException(status_code=404, detail="invitation not available")
    submission = create_creator_submission(DB_PATH, invitation, payload)
    return {"submission": asdict(submission)}


@app.get("/api/creator-commercial/submissions")
def creator_commercial_submissions() -> dict[str, Any]:
    return {"items": [asdict(item) for item in load_all_submissions(DB_PATH)]}


@app.post("/api/creator-commercial/submissions/{submission_id}/review")
async def review_commercial_submission(submission_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    submission = load_submission(DB_PATH, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="submission not found")
    if isinstance(payload.get("profile_fields"), dict):
        submission.profile_fields.update(payload["profile_fields"])
    if isinstance(payload.get("ai_profile"), dict):
        submission.ai_profile.update(payload["ai_profile"])
    creator = _find_creator(submission.creator_id)
    reviewed, commercial, updated = review_creator_submission(
        DB_PATH,
        creator,
        submission,
        decision=str(payload.get("decision") or "approved"),
        reviewed_by=str(payload.get("reviewed_by") or "media_user"),
        review_note=str(payload.get("review_note") or ""),
    )
    return {
        "submission": asdict(reviewed),
        "commercial_profile": commercial.to_dict() if commercial else None,
        "creator": profile_payload(updated) if updated else None,
    }


@app.get("/api/creator-commercial/profile/{creator_id}")
def creator_commercial_profile(creator_id: str) -> dict[str, Any]:
    creator = _find_creator(creator_id)
    commercial = load_commercial_profile(DB_PATH, creator_id)
    submissions = load_submissions_for_creator(DB_PATH, creator_id)
    return {
        "creator": profile_payload(creator),
        "commercial_profile": commercial.to_dict() if commercial else None,
        "submissions": [asdict(item) for item in submissions],
    }


@app.get("/api/distribution/briefs")
def distribution_briefs() -> dict[str, Any]:
    briefs = load_all_distribution_briefs(DB_PATH)
    return {
        "items": [
            item.to_dict()
            | {
                "response_count": len(load_responses_for_brief(DB_PATH, item.brief_id)),
                "recipient_count": len(item.recipients),
            }
            for item in briefs
        ]
    }


@app.post("/api/distribution/briefs")
async def create_distribution(payload: dict[str, Any]) -> dict[str, Any]:
    raw_brief = str(payload.get("brief") or payload.get("raw_brief") or "").strip()
    if not raw_brief:
        raise HTTPException(status_code=400, detail="brief is required")
    brief = create_distribution_brief(
        DB_PATH,
        client_name=str(payload.get("client_name") or "未命名客户"),
        project_name=str(payload.get("project_name") or "未命名项目"),
        raw_brief=raw_brief,
        creators=load_profiles(DB_PATH),
        creator_ids=[str(item) for item in payload.get("creator_ids") or [] if str(item).strip()],
        top_n=int(payload.get("top_n") or 8),
        created_by=str(payload.get("created_by") or "media_user"),
    )
    return {"brief": brief.to_dict()}


@app.get("/api/distribution/briefs/{brief_id}")
def distribution_detail(brief_id: str) -> dict[str, Any]:
    brief = load_distribution_brief(DB_PATH, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="brief not found")
    responses = load_responses_for_brief(DB_PATH, brief_id)
    return {"brief": brief.to_dict(), "responses": [asdict(item) for item in responses], "summary": distribution_summary(brief, responses)}


@app.post("/api/distribution/briefs/{brief_id}/push")
async def push_distribution(brief_id: str) -> dict[str, Any]:
    brief = load_distribution_brief(DB_PATH, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="brief not found")
    brief = push_distribution_brief(DB_PATH, brief)
    return {"brief": brief.to_dict()}


@app.get("/api/creator/brief/{token}")
def creator_brief(token: str) -> dict[str, Any]:
    result = load_distribution_brief_by_token(DB_PATH, token)
    if result is None:
        raise HTTPException(status_code=404, detail="brief link not available")
    brief, recipient_id = result
    try:
        brief, recipient = mark_recipient_viewed(DB_PATH, brief, recipient_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="recipient not found") from exc
    return {"brief": brief.to_dict(), "recipient": recipient.to_dict()}


@app.post("/api/creator/brief/{token}/respond")
async def respond_creator_brief(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = load_distribution_brief_by_token(DB_PATH, token)
    if result is None:
        raise HTTPException(status_code=404, detail="brief link not available")
    brief, recipient_id = result
    try:
        response = submit_creator_response(DB_PATH, brief, recipient_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="recipient not found") from exc
    creator = load_profile(DB_PATH, response.creator_id)
    updated = apply_response_to_creator(DB_PATH, creator, response, brief) if creator else None
    return {"response": asdict(response), "creator": profile_payload(updated) if updated else None}


@app.get("/api/distribution/briefs/{brief_id}/summary")
def distribution_brief_summary(brief_id: str) -> dict[str, Any]:
    brief = load_distribution_brief(DB_PATH, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="brief not found")
    return distribution_summary(brief, load_responses_for_brief(DB_PATH, brief_id))


@app.get("/api/distribution/briefs/{brief_id}/client-view")
def distribution_client_view(brief_id: str) -> dict[str, Any]:
    brief = load_distribution_brief(DB_PATH, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="brief not found")
    return client_response_view(brief, load_responses_for_brief(DB_PATH, brief_id))


@app.get("/api/platform/dashboard")
def platform_dashboard_api() -> dict[str, Any]:
    return platform_dashboard(DB_PATH)


@app.post("/api/platform/campaign-os")
async def platform_campaign_os(payload: dict[str, Any]) -> dict[str, Any]:
    return campaign_os_snapshot(DB_PATH, brief_text=str(payload.get("brief") or ""))


@app.post("/api/project-run")
async def project_run(payload: dict[str, Any]) -> dict[str, Any]:
    raw_brief = str(payload.get("brief") or payload.get("raw_brief") or "").strip()
    if not raw_brief:
        raise HTTPException(status_code=400, detail="brief is required")
    try:
        result = run_pr_project(
            DB_PATH,
            client_name=str(payload.get("client_name") or "未命名客户"),
            project_name=str(payload.get("project_name") or "未命名项目"),
            raw_brief=raw_brief,
            top_n=int(payload.get("top_n") or 8),
            simulation_engine=str(payload.get("simulation_engine") or "auto"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    result["graph"] = _build_symbolic_graph(
        result.get("brand", {}),
        result.get("matches", []),
        result.get("narratives", []),
        result.get("social_report", {}),
        result.get("product", {}),
    )
    return {"run": result}


@app.get("/api/platform/campaigns")
def platform_campaigns() -> dict[str, Any]:
    return {"items": [item.to_dict() for item in load_all_campaign_projects(DB_PATH)]}


@app.post("/api/platform/campaigns")
async def create_platform_campaign(payload: dict[str, Any]) -> dict[str, Any]:
    raw_brief = str(payload.get("brief") or payload.get("raw_brief") or "").strip()
    if not raw_brief:
        raise HTTPException(status_code=400, detail="brief is required")
    project = create_campaign_project(
        DB_PATH,
        client_name=str(payload.get("client_name") or "未命名客户"),
        project_name=str(payload.get("project_name") or "未命名项目"),
        raw_brief=raw_brief,
        top_n=int(payload.get("top_n") or 12),
    )
    return {"project": project.to_dict()}


@app.get("/api/platform/campaigns/{campaign_id}")
def platform_campaign_detail(campaign_id: str) -> dict[str, Any]:
    project = load_campaign_project(DB_PATH, campaign_id)
    if project is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    return {"project": project.to_dict()}


@app.get("/api/platform/campaigns/{campaign_id}/room")
def platform_campaign_room(campaign_id: str) -> dict[str, Any]:
    try:
        return {"room": campaign_room(DB_PATH, campaign_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/platform/campaigns/{campaign_id}/distribution")
async def platform_campaign_distribution(campaign_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return create_distribution_from_campaign(DB_PATH, campaign_id, plan_id=str(payload.get("plan_id") or ""))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/platform/campaigns/{campaign_id}/simulations")
async def platform_campaign_simulation(campaign_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        project = run_campaign_plan_simulation(DB_PATH, campaign_id, plan_id=str(payload.get("plan_id") or ""))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"project": project.to_dict()}


@app.post("/api/platform/campaigns/{campaign_id}/reviews")
async def platform_campaign_review(campaign_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        project = add_post_campaign_review(DB_PATH, campaign_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"project": project.to_dict()}


@app.post("/api/platform/campaigns/{campaign_id}/archive")
async def platform_campaign_archive(campaign_id: str) -> dict[str, Any]:
    project = load_campaign_project(DB_PATH, campaign_id)
    if project is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    project.archived = True
    project.campaign.status = "archived"
    upsert_campaign_project(DB_PATH, project)
    return {"project": project.to_dict()}


@app.post("/api/symbolic/creator-profile")
async def create_creator_symbolic_profile(payload: dict[str, Any]) -> dict[str, Any]:
    creator_id = str(payload.get("creator_id", "")).strip()
    profile = _find_creator(creator_id)
    symbolic = generate_creator_symbolic_profile(
        profile,
        content_sample=str(payload.get("content_sample") or ""),
        comment_sample=str(payload.get("comment_sample") or ""),
        case_sample=str(payload.get("case_sample") or ""),
        rule_config=load_rule_config(DB_PATH),
    )
    upsert_creator_symbolic(DB_PATH, symbolic)
    return {"profile": symbolic.to_dict()}


@app.patch("/api/symbolic/creator-profile/{creator_id}")
async def update_creator_symbolic_profile(creator_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    symbolic = load_creator_symbolic(DB_PATH, creator_id)
    if symbolic is None:
        symbolic = generate_creator_symbolic_profile(_find_creator(creator_id), rule_config=load_rule_config(DB_PATH))
    data = symbolic.to_dict()
    editable = {
        "primary_tags",
        "secondary_tags",
        "persona_structure",
        "emotional_tone",
        "narrative_style",
        "audience_fantasy",
        "common_metaphors",
        "common_metonymies",
        "suitable_brand_types",
        "unsuitable_brand_types",
        "risk_tags",
        "confidence",
        "visibility",
        "manual_status",
        "content_sample",
        "comment_sample",
        "case_sample",
    }
    for field in editable:
        if field in payload:
            data[field] = _coerce_symbolic_value(field, payload[field])
    updated = CreatorSymbolicProfile.from_json(json.dumps(data, ensure_ascii=False))
    upsert_creator_symbolic(DB_PATH, updated)
    return {"profile": updated.to_dict()}


@app.post("/api/symbolic/brand-profile")
async def create_brand_symbolic_profile(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload["rule_config"] = load_rule_config(DB_PATH)
    profile = generate_brand_symbolic_profile(payload)
    upsert_brand_symbolic(DB_PATH, profile)
    return {"profile": profile.to_dict()}


@app.patch("/api/symbolic/brand-profile/{brand_id}")
async def update_brand_symbolic_profile(brand_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    profile = load_brand_symbolic(DB_PATH, brand_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="brand symbolic profile not found")
    data = profile.to_dict()
    editable = {
        "brand_name",
        "product",
        "industry",
        "current_tags",
        "target_tags",
        "danger_tags",
        "emotional_value",
        "identity_value",
        "product_metaphors",
        "product_metonymies",
        "suitable_social_issues",
        "unsafe_social_issues",
        "suitable_creator_types",
        "communication_path",
        "confidence",
        "raw_input",
    }
    for field in editable:
        if field in payload:
            data[field] = _coerce_symbolic_value(field, payload[field])
    updated = BrandSymbolicProfile.from_json(json.dumps(data, ensure_ascii=False))
    upsert_brand_symbolic(DB_PATH, updated)
    return {"profile": updated.to_dict()}


@app.post("/api/symbolic/brand-profile/{brand_id}/calibrate")
async def calibrate_symbolic_brand_profile(brand_id: str, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    profile = load_brand_symbolic(DB_PATH, brand_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="brand symbolic profile not found")
    calibrated, calibration = calibrate_brand_with_symbolic_context(DB_PATH, profile, report_id=str((payload or {}).get("report_id") or ""))
    if calibration.get("applied"):
        upsert_brand_symbolic(DB_PATH, calibrated)
    return {"profile": calibrated.to_dict(), "calibration": calibration}


@app.post("/api/symbolic/match")
async def symbolic_match(payload: dict[str, Any]) -> dict[str, Any]:
    brand_id = str(payload.get("brand_id") or "").strip()
    brand = load_brand_symbolic(DB_PATH, brand_id) if brand_id else None
    if brand is None:
        brand_payload = payload.get("brand") if isinstance(payload.get("brand"), dict) else payload
        brand_payload = dict(brand_payload)
        brand_payload["rule_config"] = load_rule_config(DB_PATH)
        brand = generate_brand_symbolic_profile(brand_payload)
        upsert_brand_symbolic(DB_PATH, brand)
    if payload.get("use_social_context"):
        brand, calibration = calibrate_brand_with_symbolic_context(DB_PATH, brand, report_id=str(payload.get("report_id") or ""))
        if calibration.get("applied"):
            upsert_brand_symbolic(DB_PATH, brand)
    else:
        calibration = None

    creator_symbolics = load_all_creator_symbolic(DB_PATH)
    existing_ids = {item.creator_id for item in creator_symbolics}
    for creator in load_profiles(DB_PATH):
        if creator.creator_id not in existing_ids:
            symbolic = generate_creator_symbolic_profile(creator, rule_config=load_rule_config(DB_PATH))
            upsert_creator_symbolic(DB_PATH, symbolic)
            creator_symbolics.append(symbolic)
    results = rank_symbolic_creators(brand, creator_symbolics)
    top_n = int(payload.get("top_n", 10))
    narratives = [generate_narrative_path(brand, load_creator_symbolic(DB_PATH, item.creator_id) or creator_symbolics[0]).to_dict() for item in results[: min(3, top_n)]]
    return {
        "brand": brand.to_dict(),
        "results": [result.to_dict() for result in results[:top_n]],
        "narratives": narratives,
        "calibration": calibration,
    }


@app.post("/api/symbolic/narrative")
async def symbolic_narrative(payload: dict[str, Any]) -> dict[str, Any]:
    brand_id = str(payload.get("brand_id") or "").strip()
    creator_id = str(payload.get("creator_id") or "").strip()
    brand = load_brand_symbolic(DB_PATH, brand_id)
    creator = load_creator_symbolic(DB_PATH, creator_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="brand symbolic profile not found")
    if creator is None:
        creator = generate_creator_symbolic_profile(_find_creator(creator_id), rule_config=load_rule_config(DB_PATH))
        upsert_creator_symbolic(DB_PATH, creator)
    path = generate_narrative_path(brand, creator, project_name=str(payload.get("project") or ""))
    return {"narrative": path.to_dict()}


@app.post("/api/symbolic/graph")
async def symbolic_graph(payload: dict[str, Any]) -> dict[str, Any]:
    brand = payload.get("brand") if isinstance(payload.get("brand"), dict) else {}
    if not brand and payload.get("brand_id"):
        stored_brand = load_brand_symbolic(DB_PATH, str(payload["brand_id"]))
        brand = stored_brand.to_dict() if stored_brand else {}
    matches = payload.get("matches") if isinstance(payload.get("matches"), list) else []
    narratives = payload.get("narratives") if isinstance(payload.get("narratives"), list) else []
    social_context = payload.get("social_context") if isinstance(payload.get("social_context"), dict) else {}
    product_context = payload.get("product_context") if isinstance(payload.get("product_context"), dict) else {}
    return _build_symbolic_graph(brand, matches, narratives, social_context, product_context)


@app.get("/api/symbolic/engines")
def symbolic_engines() -> dict[str, Any]:
    glm = GlmClient()
    mirofish = MiroFishCliAdapter()
    return {
        "glm": {
            "configured": glm.available,
            "model": glm.model,
        },
        "stress_engines": [
            {"id": "llm_fallback", "label": "LLM 多角色 fallback", "available": True},
            {"id": "mirofish", "label": "MiroFish CLI", "available": mirofish.available()},
        ],
    }


@app.post("/api/symbolic/stress-test")
async def symbolic_stress_test(payload: dict[str, Any]) -> dict[str, Any]:
    engine = str(payload.get("engine") or "llm_fallback")
    if engine == "mirofish":
        executable = str(payload.get("executable") or "").strip() or None
        adapter = MiroFishCliAdapter(executable=executable)
        try:
            report = adapter.run(payload)
        except Exception as exc:
            fallback = LlmFallbackStressTest().run(payload)
            data = fallback.to_dict()
            data["engine"] = "llm_fallback_after_mirofish_error"
            data["mirofish_error"] = str(exc)
            return {"report": data}
    else:
        report = LlmFallbackStressTest().run(payload)
    return {"report": report.to_dict()}


def _find_creator(creator_id: str) -> CreatorProfile:
    if not creator_id:
        raise HTTPException(status_code=400, detail="creator_id is required")
    for profile in load_profiles(DB_PATH):
        if profile.creator_id == creator_id:
            return profile
    raise HTTPException(status_code=404, detail="creator not found")


def _coerce_symbolic_value(field: str, value: Any) -> Any:
    list_fields = {
        "primary_tags",
        "secondary_tags",
        "common_metaphors",
        "common_metonymies",
        "suitable_brand_types",
        "unsuitable_brand_types",
        "risk_tags",
        "current_tags",
        "target_tags",
        "danger_tags",
        "emotional_value",
        "identity_value",
        "product_metaphors",
        "product_metonymies",
        "suitable_social_issues",
        "unsafe_social_issues",
        "suitable_creator_types",
        "children",
        "related_tags",
        "opposite_tags",
        "metaphor_relations",
        "metonymy_relations",
        "suitable_industries",
        "suitable_content_forms",
        "examples",
        "physical_attributes",
        "use_scenarios",
        "target_users",
        "functional_value",
        "metaphors",
        "metonymies",
        "association_words",
        "anti_association_words",
        "suitable_content_scenarios",
        "unsuitable_creator_types",
        "social_issue_hooks",
        "evidence",
        "mediating_tags",
        "title_directions",
        "must_include",
        "must_avoid",
        "risk_words",
        "matched_brand_tags",
        "case_basis",
    }
    if field in list_fields:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [item.strip() for item in str(value or "").replace("，", ",").split(",") if item.strip()]
    if field == "confidence":
        return float(value or 0)
    return str(value or "").strip()


def _build_symbolic_graph(
    brand: dict[str, Any],
    matches: list[dict[str, Any]],
    narratives: list[dict[str, Any]],
    social_context: Optional[dict[str, Any]] = None,
    product_context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_node(
        node_id: str,
        label: str,
        node_type: str,
        score: int | None = None,
        detail: str = "",
        stage: str = "",
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        if not node_id or node_id in seen:
            return
        seen.add(node_id)
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "type": node_type,
                "score": score,
                "detail": detail,
                "stage": stage or _graph_stage_for_type(node_type),
                "payload": payload or {},
            }
        )

    def add_edge(source: str, target: str, label: str, edge_type: str = "relation") -> None:
        if source and target:
            edges.append({"source": source, "target": target, "label": label, "type": edge_type})

    brand_id = str(brand.get("brand_id") or "brand")
    brand_label = str(brand.get("brand_name") or brand.get("product") or "品牌")
    add_node(
        brand_id,
        brand_label,
        "brand",
        detail=str(brand.get("communication_path") or "品牌符号档案"),
        stage="brand_calibration",
        payload=_graph_payload(
            brand,
            [
                "brand_name",
                "product",
                "industry",
                "current_tags",
                "target_tags",
                "danger_tags",
                "emotional_value",
                "identity_value",
                "suitable_creator_types",
                "communication_path",
                "confidence",
            ],
        ),
    )

    product = str(brand.get("product") or "")
    if product:
        product_id = f"{brand_id}:product"
        add_node(product_id, product, "product", detail="从 brief 抽取的产品对象", stage="brief_parse", payload={"product": product})
        add_edge(brand_id, product_id, "产品")
    else:
        product_id = ""

    product_context = product_context or {}
    if product_context:
        product_id = f"product_profile:{product_context.get('product_id') or product_context.get('product_name') or 'product'}"
        add_node(
            product_id,
            str(product_context.get("product_name") or product_context.get("product") or "产品符号档案"),
            "product",
            detail="产品的功能、情绪、身份和隐喻结构",
            stage="product_profile",
            payload=_graph_payload(
                product_context,
                [
                    "product_name",
                    "category",
                    "physical_attributes",
                    "use_scenarios",
                    "target_users",
                    "functional_value",
                    "emotional_value",
                    "identity_value",
                    "metaphors",
                    "metonymies",
                    "risk_notes",
                    "confidence",
                ],
            ),
        )
        add_edge(brand_id, product_id, "产品符号档案", "product")
        for tag in (product_context.get("emotional_value") or [])[:4]:
            tag_id = f"product_emotion:{tag}"
            add_node(tag_id, str(tag), "target_tag", detail="产品情绪价值", stage="product_profile", payload={"tag": tag})
            add_edge(product_id, tag_id, "情绪价值", "target")
        for metaphor in (product_context.get("metaphors") or [])[:4]:
            metaphor_id = f"product_metaphor:{metaphor}"
            add_node(metaphor_id, str(metaphor), "narrative", detail="产品隐喻，可转化为内容表达", stage="product_profile", payload={"metaphor": metaphor})
            add_edge(product_id, metaphor_id, "产品隐喻", "narrative")
        for risk in (product_context.get("risk_notes") or product_context.get("anti_association_words") or [])[:4]:
            risk_id = f"product_risk:{risk}"
            add_node(risk_id, str(risk)[:38], "risk_tag", detail="产品传播风险", stage="risk_test", payload={"risk": risk})
            add_edge(product_id, risk_id, "产品风险", "risk")

    social_context = social_context or {}
    if social_context:
        social_id = f"social:{social_context.get('report_id') or 'latest'}"
        add_node(
            social_id,
            str(social_context.get("title") or "社会符号网络"),
            "social_context",
            detail="从输入 brief 生成的社会语境和议题场",
            stage="social_context",
            payload=_graph_payload(social_context, ["title", "period", "summary", "confidence"]),
        )
        add_edge(social_id, brand_id, "校准品牌语境", "context")
        for issue in (social_context.get("issues") or [])[:5]:
            issue_id = f"social_issue:{issue.get('issue')}"
            add_node(
                issue_id,
                str(issue.get("issue") or "社会议题"),
                "social_issue",
                detail=str(issue.get("opportunity") or issue.get("core_emotion") or ""),
                stage="social_context",
                payload=_graph_payload(issue, ["issue", "keywords", "core_emotion", "public_fantasy", "rupture_point", "opportunity", "risk_direction"]),
            )
            add_edge(social_id, issue_id, "包含议题", "context")
            add_edge(issue_id, brand_id, "可借势", "context")
            if issue.get("risk_direction"):
                risk_id = f"social_risk:{issue.get('issue')}"
                add_node(risk_id, str(issue.get("risk_direction"))[:38], "risk_tag", detail="社会议题风险方向", stage="risk_test", payload={"risk_direction": issue.get("risk_direction")})
                add_edge(issue_id, risk_id, "风险方向", "risk")
            if issue.get("opportunity"):
                opportunity_id = f"social_opportunity:{issue.get('issue')}"
                add_node(opportunity_id, str(issue.get("opportunity"))[:38], "narrative", detail="可借势的叙事机会", stage="narrative_asset", payload={"opportunity": issue.get("opportunity")})
                add_edge(issue_id, opportunity_id, "借势方向", "narrative")

    for tag in (brand.get("target_tags") or [])[:8]:
        tag_id = f"tag:{tag}"
        add_node(tag_id, str(tag), "target_tag", detail="品牌希望被用户记住的目标标签", stage="brand_calibration", payload={"tag": tag})
        add_edge(brand_id, tag_id, "目标标签", "target")

    for tag in (brand.get("danger_tags") or [])[:6]:
        tag_id = f"danger:{tag}"
        add_node(tag_id, str(tag), "risk_tag", detail="品牌需要避开的危险标签", stage="risk_test", payload={"tag": tag})
        add_edge(brand_id, tag_id, "避开", "risk")

    for match in matches[:12]:
        creator_key = str(match.get("creator_id") or match.get("creator_name") or "")
        creator_node = f"creator:{creator_key}"
        add_node(
            creator_node,
            str(match.get("creator_name") or "博主"),
            "creator",
            int(match.get("symbolic_score") or 0),
            detail=str(match.get("match_reason") or match.get("suggested_content_direction") or ""),
            stage="kol_match",
            payload=_graph_payload(
                match,
                [
                    "creator_id",
                    "creator_name",
                    "symbolic_score",
                    "recommendation_level",
                    "matched_brand_tags",
                    "metaphor_relation",
                    "metonymy_relation",
                    "match_reason",
                    "risk_points",
                    "suggested_content_direction",
                    "needs_manual_review",
                ],
            ),
        )
        add_edge(brand_id, creator_node, f"符号匹配 {match.get('symbolic_score', '-')}", "match")
        for tag in (match.get("matched_brand_tags") or [])[:4]:
            tag_id = f"tag:{tag}"
            add_node(tag_id, str(tag), "target_tag", detail="KOL 能承接的品牌标签", stage="kol_match", payload={"tag": tag, "creator": match.get("creator_name")})
            add_edge(creator_node, tag_id, "承接标签", "target")
        for risk in (match.get("risk_points") or [])[:3]:
            risk_id = f"risk:{creator_key}:{risk}"
            add_node(risk_id, str(risk), "risk_tag", detail="KOL 侧需要提前处理的风险", stage="risk_test", payload={"risk": risk, "creator": match.get("creator_name")})
            add_edge(creator_node, risk_id, "风险", "risk")

    for narrative in narratives[:6]:
        creator_key = str(narrative.get("creator_id") or narrative.get("creator_name") or "")
        creator_node = f"creator:{creator_key}"
        path_id = f"path:{creator_key}:{narrative.get('target_tag') or narrative.get('start_tag') or len(nodes)}"
        label = str(narrative.get("narrative_path") or narrative.get("target_tag") or "叙事路径")
        add_node(
            path_id,
            label[:38],
            "narrative",
            detail=str(narrative.get("content_brief") or narrative.get("narrative_path") or ""),
            stage="narrative_asset",
            payload=_graph_payload(
                narrative,
                [
                    "project",
                    "creator_name",
                    "start_tag",
                    "mediating_tags",
                    "target_tag",
                    "narrative_path",
                    "metaphor_strategy",
                    "metonymy_strategy",
                    "title_directions",
                    "must_include",
                    "must_avoid",
                    "comment_guidance",
                ],
            ),
        )
        add_edge(creator_node, path_id, "内容路径", "narrative")
        if narrative.get("target_tag"):
            tag_id = f"tag:{narrative['target_tag']}"
            add_node(tag_id, str(narrative["target_tag"]), "target_tag", detail="叙事路径最终导向的品牌标签", stage="narrative_asset", payload={"target_tag": narrative["target_tag"]})
            add_edge(path_id, tag_id, "导向", "target")

    return {"nodes": nodes, "edges": edges}


def _graph_stage_for_type(node_type: str) -> str:
    return {
        "brand": "brand_calibration",
        "product": "product_profile",
        "social_context": "social_context",
        "social_issue": "social_context",
        "creator": "kol_match",
        "narrative": "narrative_asset",
        "target_tag": "brand_calibration",
        "risk_tag": "risk_test",
    }.get(node_type, "analysis")


def _graph_payload(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: data.get(field) for field in fields if data.get(field) not in (None, "", [])}


def _current_version(proposal: Proposal, versions: list[ProposalVersion]) -> ProposalVersion | None:
    if not versions:
        return None
    for version in versions:
        if version.version_number == proposal.current_version:
            return version
    return versions[-1]


def _require_proposal(proposal_id: str) -> Proposal:
    proposal = load_proposal(DB_PATH, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    return proposal


def _now() -> str:
    from src.collaboration.schemas import now_iso

    return now_iso()


@app.exception_handler(Exception)
async def catch_all(_, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})
