# PR AI OS

PR AI OS is a local-first MVP for media agencies managing KOL resources, brand briefs, client collaboration, creator responses, campaign simulation, and post-campaign learning.

## Current Scope

- Phase 1: Excel / CSV / links / manual / API creator ingestion, normalization, governance, dedupe, and recommendations.
- Phase 1.5: creator symbolic profiles, brand symbolic analysis, symbolic matching, graph view, and Simulation Layer.
- Symbolic OS layer: social symbolic network reports, signifier tag ontology, and post-campaign symbolic feedback correction.
- Phase 2: client proposal sharing, feedback, versioning, and preference learning.
- Phase 3: creator commercial profile collection, cases, quotes, schedule, and review.
- Phase 4: Brief distribution to creators and creator response collection.
- Phase 5: Campaign OS dashboard, Campaign Room, multi-plan strategy, deep simulation, Brief distribution bridge, and post-campaign review feedback loop.
- Project Run: one-click PR project workflow from raw brief to symbolic graph, KOL selection, narrative assets, stress test, and Campaign Room.
- Production foundations: workspace-level data isolation, optional access key, and centralized data-source status/testing.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
scripts/run_web.sh
```

Open:

```text
http://127.0.0.1:8601
```

You can also run FastAPI directly:

```bash
python3 -m uvicorn web.server:app --host 127.0.0.1 --port 8601
```

## Configuration

Optional `.env` values:

```bash
GLM_API_KEY=
GLM_MODEL=glm-4-flash
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions

PR_AI_OS_ACCESS_KEY=

ONEAPI_API_KEY=
ONEAPI_BASE_URL=https://api.getoneapi.com

DATABASE_URL=

OBJECT_STORE_PROVIDER=local
OBJECT_STORE_LOCAL_ROOT=data/objects
OBJECT_STORE_BUCKET=
OBJECT_STORE_ENDPOINT_URL=
OBJECT_STORE_REGION=
OBJECT_STORE_ACCESS_KEY_ID=
OBJECT_STORE_SECRET_ACCESS_KEY=
OBJECT_STORE_PUBLIC_BASE_URL=
```

Behavior:

- If `GLM_API_KEY` is missing, symbolic analysis uses local rule fallback.
- If `ONEAPI_API_KEY` is missing, OneAPI status is shown as not configured; Mock API and Excel remain usable.
- If MiroFish CLI is not installed, Campaign stress tests use the OS fallback Simulation Layer.
- If `PR_AI_OS_ACCESS_KEY` is set, private API calls require `X-Access-Key`; public client/creator links remain accessible.
- If `DATABASE_URL` is empty, the app uses local SQLite; if set, storage modules use PostgreSQL JSONB tables.
- `OBJECT_STORE_PROVIDER=local` stores uploaded source files under `data/objects`; `oss`, `r2`, `s3`, and `minio` use the S3-compatible adapter.

## Workspace Isolation

The web UI includes a `Workspace` switcher. API calls send `X-Tenant-ID`.

- `default` uses `data/processed/phase1_web.sqlite3`.
- Other workspaces use `data/processed/tenants/{workspace}/phase1_web.sqlite3`.
- Import templates are also isolated per workspace.

## Data Sources

Use the `数据源设置` page to inspect and test:

- Excel / CSV ingestion
- Mock API
- OneAPI
- GLM
- MiroFish CLI
- Storage adapter status

Related APIs:

- `GET /api/settings/data-sources`
- `POST /api/settings/data-sources/test`
- `GET /api/settings/storage`

## Storage Adapter

Database and object storage are configured independently:

- Database adapter: local SQLite by default, PostgreSQL when `DATABASE_URL` is set.
- Object storage adapter: local filesystem by default, S3-compatible storage when `OBJECT_STORE_PROVIDER` is `oss`, `r2`, `s3`, or `minio`.

Examples:

```bash
# Local development
OBJECT_STORE_PROVIDER=local
OBJECT_STORE_LOCAL_ROOT=data/objects

# Alibaba Cloud OSS via S3-compatible API
OBJECT_STORE_PROVIDER=oss
OBJECT_STORE_BUCKET=your-bucket
OBJECT_STORE_ENDPOINT_URL=https://oss-cn-hangzhou.aliyuncs.com
OBJECT_STORE_REGION=cn-hangzhou
OBJECT_STORE_ACCESS_KEY_ID=...
OBJECT_STORE_SECRET_ACCESS_KEY=...

# Cloudflare R2
OBJECT_STORE_PROVIDER=r2
OBJECT_STORE_BUCKET=your-bucket
OBJECT_STORE_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
OBJECT_STORE_REGION=auto
OBJECT_STORE_ACCESS_KEY_ID=...
OBJECT_STORE_SECRET_ACCESS_KEY=...
```

Uploaded Excel / CSV source files are saved through this adapter when imports are committed. Structured creator data remains in the database.

## PostgreSQL / pgvector Migration

The app remains local-first SQLite by default, but the repo includes a PostgreSQL/pgvector migration path:

- Schema: `db/postgres_schema.sql`
- Migrator: `scripts/migrate_sqlite_to_postgres.py`
- Runtime switch: set `DATABASE_URL` to make storage modules use PostgreSQL JSONB tables
- Deployment guide: `DEPLOYMENT.md`
- Docker Compose: `docker-compose.yml`

Docker run:

```bash
docker compose up --build
```

Dry-run migration:

```bash
python3 scripts/migrate_sqlite_to_postgres.py --sqlite data/processed/phase1_web.sqlite3 --tenant default --dry-run
```

## Core APIs

- `GET /api/status`
- `POST /api/import/file`
- `POST /api/import/manual`
- `POST /api/import/links`
- `POST /api/import/api`
- `GET /api/creators`
- `POST /api/recommend`
- `POST /api/project-run`
- `POST /api/symbolic/brand-profile`
- `POST /api/symbolic/match`
- `POST /api/symbolic/stress-test`
- `GET /api/symbolic-os`
- `POST /api/symbolic-os/social-reports`
- `POST /api/symbolic-os/signifier-tags`
- `GET /api/symbolic-os/products`
- `POST /api/symbolic-os/products`
- `GET /api/symbolic-os/narratives`
- `POST /api/symbolic-os/narratives`
- `GET /api/symbolic-os/matches`
- `POST /api/symbolic-os/matches`
- `POST /api/symbolic/brand-profile/{brand_id}/calibrate`
- `POST /api/platform/campaigns`
- `GET /api/platform/campaigns/{campaign_id}/room`
- `POST /api/platform/campaigns/{campaign_id}/simulations`
- `POST /api/platform/campaigns/{campaign_id}/distribution`
- `POST /api/platform/campaigns/{campaign_id}/reviews`

## Smoke Tests

```bash
python3 scripts/smoke_phase1.py
python3 scripts/smoke_phase1_5.py
python3 scripts/smoke_phase2.py
python3 scripts/smoke_phase3.py
python3 scripts/smoke_phase4.py
python3 scripts/smoke_phase5.py
python3 scripts/smoke_project_run_api.py
python3 scripts/smoke_symbolic_os.py
python3 scripts/smoke_symbolic_os_api.py
python3 scripts/smoke_symbolic_calibration_api.py
python3 scripts/smoke_product_symbolic_api.py
python3 scripts/smoke_narrative_assets_api.py
python3 scripts/smoke_match_assets_api.py
python3 scripts/smoke_tenant_api.py
python3 scripts/smoke_access_key.py
python3 scripts/smoke_data_sources.py
python3 scripts/smoke_storage_adapter.py
python3 scripts/smoke_runtime_config.py
python3 scripts/smoke_postgres_migration.py
DATABASE_URL=postgresql://pr_ai_os:pr_ai_os@localhost:5432/pr_ai_os python3 scripts/smoke_postgres_runtime.py
```

## Notes

This is still a local-first MVP. PostgreSQL / pgvector, managed auth, billing, hosted deployment, and real provider contract validation are the next production hardening steps.
