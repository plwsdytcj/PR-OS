from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    run_web = ROOT / "scripts" / "run_web.sh"
    deploy = (ROOT / "DEPLOYMENT.md").read_text(encoding="utf-8")
    for key in [
        "GLM_API_KEY",
        "AGENT_PROVIDER",
        "AGENT_MODEL",
        "AGENT_BASE_URL",
        "PR_AI_OS_ACCESS_KEY",
        "PR_AI_OS_AUTH_ENABLED",
        "PR_AI_OS_COOKIE_SECURE",
        "ONEAPI_API_KEY",
        "ONEAPI_BASE_URL",
        "DATABASE_URL",
        "OBJECT_STORE_PROVIDER",
        "OBJECT_STORE_BUCKET",
        "OBJECT_STORE_ENDPOINT_URL",
        "OBJECT_STORE_ACCESS_KEY_ID",
        "OBJECT_STORE_SECRET_ACCESS_KEY",
    ]:
        assert key in env
        assert key in readme
    for text in [
        "Campaign Room",
        "Workspace",
        "数据源设置",
        "组织管理",
        "AI Agent",
        "smoke_data_sources.py",
        "smoke_storage_adapter.py",
        "smoke_phase6a_auth.py",
        "smoke_phase6b_org.py",
        "smoke_phase7a_agent.py",
        "smoke_phase7b_agent_streaming.py",
        "smoke_agent_model_provider.py",
    ]:
        assert text in readme
    for text in [
        "db/postgres_schema.sql",
        "migrate_sqlite_to_postgres.py",
        "smoke_postgres_runtime.py",
        "docker compose up",
        "DATABASE_URL",
        "PR_AI_OS_AUTH_ENABLED",
        "Phase 6B",
        "Phase 7A",
        "Phase 7B",
        "AGENT_PROVIDER",
    ]:
        assert text in readme
        assert text in deploy
    assert "POSTGRES_PORT=55432" in deploy
    assert run_web.exists()
    assert run_web.stat().st_mode & 0o111
    print("OK runtime config docs and launcher")


if __name__ == "__main__":
    main()
