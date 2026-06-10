# PR AI OS Deployment

## Local Production-Like Run

```bash
cp .env.example .env
scripts/run_web.sh
```

Set `PR_AI_OS_ACCESS_KEY` or enable local auth before exposing the app outside localhost.

For Phase 6A local auth:

```bash
PR_AI_OS_AUTH_ENABLED=true
PR_AI_OS_COOKIE_SECURE=false
```

Use `PR_AI_OS_COOKIE_SECURE=true` only behind HTTPS.

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

Authentication is also adapter-shaped:

- Current provider: local email/password sessions.
- Internal users can manage creators, campaigns, proposals, and client access.
- Client users can only enter `/api/client/portal/*` and see projects explicitly granted to their client account.
- Phase 6B adds the `组织管理` page for creating internal users, client accounts, client portal members, and project access grants.
- Phase 7A adds the `AI Agent` page with local task/run/event/artifact storage and a replaceable agent runtime. Set `AGENT_PROVIDER=glm` to use GLM for Agent reasoning summaries.
- Phase 7B makes Agent execution streaming-style with `POST /api/agent/chat/start`, background execution, and polling event updates.
- Phase 7C adds the `知识库` page, knowledge document/chunk storage, hybrid RAG search, and Agent integration through `POST /api/knowledge/search`.
- Phase 7D adds Agent plan artifacts, missing-field clarification, and detailed tool trace artifacts.
- Phase 7E adds human-confirmed Agent memory writeback into the knowledge base.
- Phase 7F adds plan approval, run cancellation, clarification resume, artifact detail, and editable memory review controls.
- Phase 7G adds an Agent reasoning graph artifact and visual canvas linking brief, knowledge, KOL tags, risks, proposal, trace, and memory.
- Phase 7H adds Agent Thread Chat: multi-turn PR project conversations with message history, linked runs, artifacts, and graph state.
- Phase 7I-A adds Agent Runtime Adapter selection. `AGENT_RUNTIME=openai_agents` is the production primary runtime; `AGENT_RUNTIME=custom` forces the native fallback runtime.
- Phase 7I-B adds a real OpenAI Agents SDK POC runtime. When `openai-agents` and a compatible key are configured, SDK calls PR OS tools for brief parsing, memory search, and KOL/project matching; failures fall back to the native runtime.
- Phase 7I-C adds per-run runtime override and Custom vs Agents SDK A/B comparison.
- Phase 7J adds the Manus-like Agent task space: SSE run streaming, retry/edit/skip tool steps, multi-agent handoff artifacts, memory recall cards, and live reasoning-graph highlighting.
- Phase 8 adds the KOL Intelligence Graph: evidence-based KOL tags, brief-activated graph evolution, and prediction recommendations.
- Phase 8.1 adds KOL Evidence Review: tag confirmation/rejection, reviewer notes, weight tuning, and creator detail evidence-tag operations.
- Phase 8.2 adds the Conversational KOL Graph Workspace: chat input, dynamic graph frames, and final KOL decision cards.
- Future providers such as Authing, Feishu SSO, OIDC, and SAML should plug into the identity provider layer instead of rewriting business permissions.

Object files are handled by the object storage adapter:

- `OBJECT_STORE_PROVIDER=local`: write uploaded source files under `OBJECT_STORE_LOCAL_ROOT`
- `OBJECT_STORE_PROVIDER=oss`: Alibaba Cloud OSS through the S3-compatible adapter
- `OBJECT_STORE_PROVIDER=r2`: Cloudflare R2 through the S3-compatible adapter
- `OBJECT_STORE_PROVIDER=s3` or `minio`: generic S3-compatible storage

For cloud object storage, set `OBJECT_STORE_BUCKET`, `OBJECT_STORE_ENDPOINT_URL`, `OBJECT_STORE_REGION`, `OBJECT_STORE_ACCESS_KEY_ID`, and `OBJECT_STORE_SECRET_ACCESS_KEY`.

## PostgreSQL Backup To Object Storage

For the Docker deployment, keep PostgreSQL as the local primary database and write backups to a separate object-store prefix:

```text
backups/postgres/
```

Manual backup:

```bash
cd /opt/pr-ai-os
docker compose -f docker-compose.pr-ai-os.yml exec -T postgres \
  pg_dump -U pr_ai_os -d pr_ai_os \
  | docker compose -f docker-compose.pr-ai-os.yml exec -T app \
      python scripts/upload_backup_to_object_store.py --prefix backups/postgres
```

This keeps business data in the local PostgreSQL volume while storing recoverable dumps in R2 / OSS / S3.

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
- `PR_AI_OS_AUTH_ENABLED`: optional Phase 6A login enforcement. If false, auth activates after the first local user is bootstrapped.
- `PR_AI_OS_COOKIE_SECURE`: set true for HTTPS deployments.
- `GLM_API_KEY`: optional GLM key for symbolic analysis.
- `GLM_MODEL`: defaults to `glm-4-flash`.
- `GLM_BASE_URL`: defaults to BigModel chat completions endpoint.
- `AGENT_PROVIDER`: defaults to `glm`.
- `AGENT_API_KEY`, `AGENT_MODEL`, `AGENT_BASE_URL`: optional Agent model override; empty values fall back to `GLM_*`.
- `AGENT_RUNTIME`: defaults to `openai_agents`; set `custom` only to force the native runtime.
- `AGENT_RUNTIME_ADAPTER`: optional alias for `AGENT_RUNTIME`.
- `AGENT_SDK_MODEL`, `AGENT_SDK_API_KEY`, `AGENT_SDK_BASE_URL`, `AGENT_SDK_MAX_TURNS`, `AGENT_SDK_TRACING`, `OPENAI_DEFAULT_MODEL`: optional SDK runtime settings. For GLM/OpenAI-compatible endpoints, use the API root in `AGENT_SDK_BASE_URL`, for example `https://open.bigmodel.cn/api/paas/v4`. Tracing is disabled by default unless `AGENT_SDK_TRACING=true`.
- `ONEAPI_API_KEY`: optional KOL data API key.
- `ONEAPI_BASE_URL`: defaults to `https://api.getoneapi.com`.

## Verification

```bash
python3 scripts/smoke_runtime_config.py
python3 scripts/smoke_phase6a_auth.py
python3 scripts/smoke_phase6b_org.py
python3 scripts/smoke_phase7a_agent.py
python3 scripts/smoke_phase7b_agent_streaming.py
python3 scripts/smoke_phase7c_knowledge_rag.py
python3 scripts/smoke_phase7d_7e_agent_planner_memory.py
python3 scripts/smoke_phase7f_agent_experience.py
python3 scripts/smoke_phase7g_agent_reasoning_graph.py
python3 scripts/smoke_phase7h_agent_threads.py
python3 scripts/smoke_phase7i_runtime_adapter.py
python3 scripts/smoke_phase7i_b_agent_sdk.py
python3 scripts/smoke_phase7i_c_runtime_ab.py
python3 scripts/smoke_phase7j_manus_workspace.py
python3 scripts/smoke_agent_model_provider.py
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
