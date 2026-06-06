# PR AI OS Deployment

## Local Production-Like Run

```bash
cp .env.example .env
scripts/run_web.sh
```

Set `PR_AI_OS_ACCESS_KEY` in `.env` before exposing the app outside localhost.

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

The compose stack starts:

- `app`: FastAPI web app on port `8601`
- `postgres`: PostgreSQL 16 with pgvector

Current runtime remains local-first SQLite by default. PostgreSQL is provisioned for migration, analytics, and the next runtime storage adapter.

If `DATABASE_URL` is set, the runtime storage modules use PostgreSQL JSONB tables instead of SQLite for core business objects. Leave `DATABASE_URL` empty to keep local SQLite mode.

Object files are handled by the object storage adapter:

- `OBJECT_STORE_PROVIDER=local`: write uploaded source files under `OBJECT_STORE_LOCAL_ROOT`
- `OBJECT_STORE_PROVIDER=oss`: Alibaba Cloud OSS through the S3-compatible adapter
- `OBJECT_STORE_PROVIDER=r2`: Cloudflare R2 through the S3-compatible adapter
- `OBJECT_STORE_PROVIDER=s3` or `minio`: generic S3-compatible storage

For cloud object storage, set `OBJECT_STORE_BUCKET`, `OBJECT_STORE_ENDPOINT_URL`, `OBJECT_STORE_REGION`, `OBJECT_STORE_ACCESS_KEY_ID`, and `OBJECT_STORE_SECRET_ACCESS_KEY`.

If local port `5432` is already occupied:

```bash
POSTGRES_PORT=55432 docker compose up -d postgres
DATABASE_URL=postgresql://pr_ai_os:pr_ai_os@localhost:55432/pr_ai_os python3 scripts/smoke_postgres_runtime.py
```

## PostgreSQL Schema

Schema file:

```text
db/postgres_schema.sql
```

It creates JSONB payload tables matching the current SQLite persistence model, plus:

- `tenant_id` on every table
- `creator_embeddings` with `VECTOR(1536)`
- GIN indexes on major JSONB payload tables

## SQLite To PostgreSQL Migration

Dry run:

```bash
python3 scripts/migrate_sqlite_to_postgres.py \
  --sqlite data/processed/phase1_web.sqlite3 \
  --tenant default \
  --dry-run
```

Live migration:

```bash
python3 scripts/migrate_sqlite_to_postgres.py \
  --sqlite data/processed/phase1_web.sqlite3 \
  --tenant default \
  --database-url postgresql://pr_ai_os:pr_ai_os@localhost:5432/pr_ai_os
```

Tenant database example:

```bash
python3 scripts/migrate_sqlite_to_postgres.py \
  --sqlite data/processed/tenants/alpha-media/phase1_web.sqlite3 \
  --tenant alpha-media \
  --database-url postgresql://pr_ai_os:pr_ai_os@localhost:5432/pr_ai_os
```

## Environment Variables

- `PR_AI_OS_ACCESS_KEY`: optional access key for private APIs.
- `GLM_API_KEY`: optional GLM key for symbolic analysis.
- `GLM_MODEL`: defaults to `glm-4-flash`.
- `GLM_BASE_URL`: defaults to BigModel chat completions endpoint.
- `ONEAPI_API_KEY`: optional KOL data API key.
- `ONEAPI_BASE_URL`: defaults to `https://api.getoneapi.com`.

## Verification

```bash
python3 scripts/smoke_runtime_config.py
python3 scripts/smoke_data_sources.py
python3 scripts/smoke_tenant_api.py
python3 scripts/smoke_access_key.py
python3 scripts/smoke_postgres_migration.py
DATABASE_URL=postgresql://pr_ai_os:pr_ai_os@localhost:5432/pr_ai_os python3 scripts/smoke_postgres_runtime.py
```

Run the phase smoke tests before deployment:

```bash
python3 scripts/smoke_phase1.py
python3 scripts/smoke_phase1_5.py
python3 scripts/smoke_phase2.py
python3 scripts/smoke_phase3.py
python3 scripts/smoke_phase4.py
python3 scripts/smoke_phase5.py
```
