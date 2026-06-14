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
- Phase 6A: local identity adapter, internal roles, client portal login, project access grants, and authenticated client feedback.
- Phase 6B: organization management console for internal users, client accounts, client portal members, and project access grants.
- Phase 7A: PR Project Manager Agent workspace with task/run/event/artifact runtime, local RAG placeholder, tool execution, and human approval.
- Phase 7B: streaming-style Agent execution with async run start, background tool execution, and polling event updates.
- Phase 7C: Knowledge RAG layer with document/chunk storage, local embedding fallback, knowledge search APIs, frontend knowledge console, and Agent RAG integration.
- Phase 7D: Agent planner, missing-field clarification, and detailed tool trace artifacts.
- Phase 7E: Agent memory feedback loop with human-confirmed artifact-to-knowledge writeback.
- Phase 7F: Agent experience hardening with plan approval, run controls, clarification resume, artifact detail, and editable memory review.
- Phase 7G: Agent reasoning graph view linking brief, intent, knowledge evidence, KOL tags, risks, proposal, tool trace, and memory writeback.
- Phase 7H: Agent thread chat with message history, linked runs, artifacts, and graph state.
- Phase 7I-A: replaceable Agent Runtime Adapter boundary.
- Phase 7I-B: OpenAI Agents SDK POC runtime with PR OS tool calling and native runtime fallback.
- Phase 7I-C: per-run runtime override and Custom vs Agents SDK A/B comparison.
- Phase 7J: Manus-like Agent task space with SSE live updates, editable/retryable tool steps, multi-agent handoff artifacts, memory recall display, and live graph highlighting.
- OpenClaw Agent Dock PRD: see `OpenClaw_Agent_Dock_PRD.md` for the sidecar plan to embed an OpenClaw-backed Manus-like floating chat/workspace for internal staff.
- Phase 8: KOL Intelligence Graph with evidence-based creator tags, graph evolution, and brief-driven prediction recommendations.
- Phase 8.1: KOL Evidence Review with tag confirmation, rejection, reviewer notes, weight adjustments, and creator detail evidence tags.
- Phase 8.2: Conversational KOL Graph Workspace with chat-driven graph frames and final KOL decision cards.
- KOL Intake: one unified entry for pasted text, Excel/CSV files, and screenshots/images; it creates creator profiles, derives evidence tags, and refreshes the KOL graph.
- Phase 8 PRD: see `Phase8_KOL_Intelligence_PRD.md`.
- Phase 8.1 PRD: see `Phase8_1_KOL_Evidence_Review_PRD.md`.
- Phase 8.2 PRD: see `Phase8_2_Conversational_KOL_Graph_PRD.md`.
- Phase 7 PRD: see `Phase7_Agent_OS_PRD.md` for the Agent OS roadmap from 7A to 7E.
- Production foundations: workspace-level data isolation, optional access key, centralized data-source status/testing, and pluggable storage/auth adapters.

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

AGENT_PROVIDER=glm
AGENT_API_KEY=
AGENT_MODEL=
AGENT_BASE_URL=
AGENT_RUNTIME=openai_agents
AGENT_RUNTIME_ADAPTER=
AGENT_SDK_MODEL=
AGENT_SDK_API_KEY=
AGENT_SDK_BASE_URL=
AGENT_SDK_MAX_TURNS=8
AGENT_SDK_TRACING=false
OPENAI_DEFAULT_MODEL=

OPENCLAW_ENABLED=false
OPENCLAW_GATEWAY_URL=
OPENCLAW_CONTROL_UI_URL=
OPENCLAW_ADMIN_TOKEN=
OPENCLAW_DEFAULT_AGENT_ID=kolness_default
OPENCLAW_PROXY_BASE_PATH=/openclaw

PR_AI_OS_ACCESS_KEY=
PR_AI_OS_AUTH_ENABLED=false
PR_AI_OS_COOKIE_SECURE=false

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

MIROFISH_COMMAND=mirofish
MIROFISH_LLM_PROVIDER=glm
MIROFISH_PLATFORM=twitter
MIROFISH_MAX_ROUNDS=1
MIROFISH_TIMEOUT_SECONDS=420
```

Behavior:

- If `GLM_API_KEY` is missing, symbolic analysis uses local rule fallback.
- `AGENT_PROVIDER=glm` makes the Agent Workspace use GLM for final reasoning summaries; `AGENT_API_KEY`, `AGENT_MODEL`, and `AGENT_BASE_URL` can override the `GLM_*` values.
- `AGENT_RUNTIME=openai_agents` is the production primary runtime. It uses OpenAI Agents SDK when `openai-agents` and a compatible API key are configured; missing SDK config or SDK failures automatically fall back to the native `custom` runtime. Set `AGENT_RUNTIME=custom` only when you want to force the native fallback path.
- `AGENT_SDK_API_KEY`, `AGENT_SDK_MODEL`, and `AGENT_SDK_BASE_URL` configure the SDK runtime. For GLM/OpenAI-compatible providers, set `AGENT_SDK_BASE_URL` to the API root, for example `https://open.bigmodel.cn/api/paas/v4`; if omitted, the app also derives it from `AGENT_BASE_URL` or `GLM_BASE_URL`.
- `AGENT_SDK_TRACING=false` disables OpenAI trace export by default, which avoids noisy logs when running the SDK against GLM or another OpenAI-compatible provider.
- `OPENCLAW_ENABLED=true` enables the OpenClaw sidecar runtime for the Agent Dock. One Gateway can serve multiple internal users through per-user `openclaw_agent_id` bindings managed in Admin Console.
- `OPENCLAW_GATEWAY_URL` points to the OpenClaw Gateway. `OPENCLAW_CONTROL_UI_URL` optionally points to the OpenClaw Control UI for `/openclaw` embedding.
- If `ONEAPI_API_KEY` is missing, OneAPI status is shown as not configured; Mock API and Excel remain usable.
- If MiroFish CLI is not installed or times out, Campaign stress tests use the OS fallback Simulation Layer in Auto mode.
- `MIROFISH_COMMAND` points to the external MiroFish runtime. For the current CLI-only fork, prefer a source checkout command such as `uv --directory /opt/mirofish run mirofish`, because the wheel install does not include the OASIS `scripts/` directory needed by the simulation subprocess.
- `MIROFISH_LLM_PROVIDER=glm` uses the patched MiroFish runtime in `vendor/mirofish-openai-compatible.patch`, which adds OpenAI-compatible model support and reuses `GLM_API_KEY`, `GLM_BASE_URL`, and `GLM_MODEL`.
- Run `scripts/install_mirofish_runtime.sh /opt/mirofish` on a server to install the patched external runtime, then set `MIROFISH_COMMAND="uv --directory /opt/mirofish run mirofish"`.
- If `PR_AI_OS_ACCESS_KEY` is set, private API calls require `X-Access-Key`; public client/creator links remain accessible.
- If `PR_AI_OS_AUTH_ENABLED=true`, private APIs require login. If it is false, auth activates automatically after the first local user is created with `/api/auth/bootstrap-admin`.
- `PR_AI_OS_COOKIE_SECURE=true` should be used only behind HTTPS.
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

## Phase 8 KOL Intelligence Graph

The `达人智能图谱` page is the core KOL intelligence layer:

- `POST /api/kol-intelligence/analyze-tags`: derive evidence tags from creator profiles and symbolic profiles.
- `GET /api/kol-intelligence/review-queue`: review suggested, confirmed, rejected, or evidence-needed tags.
- `PATCH /api/kol-intelligence/tags/{tag_id}` and `POST /api/kol-intelligence/tags/bulk-review`: confirm, reject, request more evidence, or tune tag weight.
- `POST /api/kol-intelligence/conversation/run`: run the chat-driven KOL graph workspace and return messages, graph frames, and final KOL decisions.
- `POST /api/kol-intake`: unified KOL intake for text, Excel/CSV, and image uploads; returns created creators, generated evidence tags, and graph summary.
- `POST /api/kol-intelligence/graph`: build the brief-to-tag-to-KOL knowledge graph and evolution steps.
- `POST /api/kol-intelligence/predict`: activate tags from a PR brief and return KOL recommendations with evidence and risks.
- `GET /api/kol-intelligence`: inspect current tag, graph, and prediction snapshot.

This layer is intentionally independent of one specific data provider. Excel, manual import, mock API, future official APIs, or third-party data APIs can all feed the same Creator Profile and evidence tag model.

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

## Phase 6A Auth And Client Portal

The current auth layer is intentionally local-first:

- Identity provider: local email/password sessions now; Authing, Feishu SSO, OIDC, or SAML can be added later behind the same adapter.
- Internal roles: `admin`, `strategist`, `media_buyer`, `viewer`.
- Client roles: `client_owner`, `client_reviewer`, `client_viewer`.
- Client access: internal users grant a client access to selected proposals/projects; client users only see their portal routes.
- Public routes: existing share-token proposal links, creator invite links, and creator brief links remain accessible without login.

Bootstrap the first internal admin:

```bash
curl -X POST http://127.0.0.1:8601/api/auth/bootstrap-admin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"change-me","name":"Admin"}'
```

Core auth APIs:

- `POST /api/auth/bootstrap-admin`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/auth/users`
- `POST /api/auth/users`
- `GET /api/auth/clients`
- `POST /api/auth/clients`
- `POST /api/auth/clients/{client_id}/users`
- `POST /api/auth/project-access`
- `GET /api/auth/project-access`
- `GET /api/client/portal/projects`
- `GET /api/client/portal/proposals/{proposal_id}`
- `POST /api/client/portal/proposals/{proposal_id}/feedback`

## Phase 6B Organization Console

The `组织管理` page turns the Phase 6A auth layer into an operable internal admin workflow:

- Create internal agency users and assign roles.
- Create client accounts.
- Create client portal users under a client account.
- Grant a proposal/project to a specific client user with `view` and `comment` permissions.
- Inspect the current access matrix: user, client, proposal, permissions, and created time.

This is the intended path before managed SSO: use local auth for the internal PR team, keep the identity provider adapter boundary, and later replace the provider with Authing, Feishu SSO, OIDC, or SAML without changing campaign/client business logic.

## Phase 7A Agent Workspace

The `AI Agent` page is the first Manus-like PR Agent OS layer:

- Create a PR task from a natural-language brief.
- Run a PR Project Manager Agent through a task/run/event/artifact runtime.
- Search local organization memory across proposals, client feedback, campaign rooms, and creator profiles.
- Call existing PR OS tools: project run, KOL matching, risk simulation, Campaign Room creation, and proposal generation.
- Show each step as an event stream and save outputs as artifacts.
- Stop at a human approval point before client delivery/authorization.
- Use the Agent model adapter for final reasoning summaries. The current default is GLM via `AGENT_PROVIDER=glm`, with deterministic fallback if no model key is configured.

This version deliberately keeps the runtime local and replaceable. Phase 7I-A adds an Agent Runtime Adapter boundary, and Phase 7I-B adds a real OpenAI Agents SDK POC path so later phases can plug in OpenAI-compatible GLM, Qwen/DeepSeek adapters, pgvector RAG, streaming, and more complex workflow engines without changing the business tool layer.

## Phase 7H Thread Chat Agent

The Agent Workspace now has a thread layer:

- `GET /api/agent/threads` lists PR Agent conversations.
- `POST /api/agent/threads` creates a conversation from an initial brief.
- `POST /api/agent/threads/{thread_id}/messages` appends a user message and starts a new run in the same project context.
- Messages, runs, artifacts, and reasoning graphs remain linked to the same PR project thread.

## Phase 7I-A Agent Runtime Adapter

The Agent execution path now goes through a replaceable adapter:

- `openai_agents`: production primary runtime through OpenAI Agents SDK. If the SDK package and a compatible key are configured, it runs the SDK path. If not configured, or if SDK execution fails, it delegates execution to `custom`.
- `custom`: native PR OS runtime. This is the deterministic fallback and manual override path.

The runtime status is available through:

- `GET /api/agent/runtime`
- `GET /api/status` under `agent_runtime`
- `GET /api/settings/data-sources` as `agent_runtime`

This gives a safe migration path: PR OS tools, DB, memory, artifacts, client portal, and reasoning graph stay stable while orchestration can move to Agents SDK or another runtime.

## Phase 7I-B OpenAI Agents SDK POC

The SDK runtime is intentionally narrow and measurable:

- `openai_agents` uses OpenAI Agents SDK `Agent`, `Runner`, and `function_tool`.
- The SDK can call PR OS tools for brief parsing, organization memory search, and KOL/project matching.
- PR OS still owns proposal generation, memory suggestions, artifact persistence, and the reasoning graph.
- The run writes a `sdk_run` artifact and SDK-tagged `tool_trace` entries.
- If the SDK package/key is missing or the provider fails, the adapter records a fallback event and completes the run with the native `custom` runtime.

For GLM or another OpenAI-compatible provider:

```bash
AGENT_RUNTIME=openai_agents
AGENT_SDK_API_KEY=...
AGENT_SDK_MODEL=glm-4-flash
AGENT_SDK_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

## Phase 7I-C Runtime A/B Control

The Agent Workspace can now test runtimes without changing production defaults:

- The Agent Chat form includes a runtime selector: `auto`, `custom`, or `openai_agents`.
- A single run can override the default runtime through `runtime` in the request payload.
- `POST /api/agent/chat/compare-runtimes` runs the same brief through `custom` and `openai_agents`.
- The comparison response includes candidate count, tool count, graph node count, SDK status, both run IDs, and a `runtime_comparison` artifact.

This keeps `custom` available as the safe fallback while making `openai_agents` the production primary runtime.

## Phase 7J Manus-Like Task Space

The Agent Workspace now exposes the execution path as a controllable task space:

- `GET /api/agent/runs/{run_id}/stream` streams run snapshots over SSE for live event, artifact, step, and graph updates.
- `POST /api/agent/steps/{step_id}/retry`, `/edit`, and `/skip` let internal users control individual tool steps.
- SDK runs write `agent_handoffs`, `memory_recall`, `tool_trace`, and `reasoning_graph` artifacts so the UI can show roles, memory evidence, tools, and graph state together.
- The frontend renders a live step strip, multi-agent handoff cards, memory recall cards, and graph node highlighting for the currently active tool.

This is the first production-shaped Manus-style layer: the user sees the conversation, the task steps, the reasoning graph, and the generated deliverables in one workspace.

## Phase 7B Streaming Agent Execution

The Agent Workspace now supports a Manus-like live execution loop:

- `POST /api/agent/chat/start` creates a run immediately and returns `run_id`.
- FastAPI background execution writes events and artifacts as each tool step completes.
- The frontend polls `GET /api/agent/runs/{run_id}` every second and updates the event stream.
- The confirmation button appears when the run reaches `waiting_approval`.

This uses polling first for deployment simplicity. It can later be upgraded to SSE or WebSocket without changing the event/artifact persistence model.

## Phase 7C Knowledge RAG

The `知识库` page turns company materials into searchable Agent memory:

- Create knowledge documents from internal cases, client preferences, creator history, risk policies, and proposal templates.
- Automatically split documents into chunks and generate deterministic local embeddings as a fallback.
- Search knowledge with hybrid keyword/vector scoring.
- Keep tenant/workspace isolation for documents and chunks.
- Feed knowledge search results into the Agent before it runs KOL selection, project execution, and proposal generation.

Core knowledge APIs:

- `GET /api/knowledge`
- `POST /api/knowledge`
- `GET /api/knowledge/{document_id}`
- `POST /api/knowledge/search`

## Phase 7D / 7E Agent Planning And Memory Loop

The Agent layer now behaves more like a PR project manager instead of a fixed automation button:

- Generates a `plan` artifact before running tools.
- Returns a `clarification` artifact and pauses at `waiting_clarification` when the brief misses critical fields such as budget, platform, or product.
- Records a `tool_trace` artifact with tool name, input summary, output summary, latency, status, and linked artifact.
- Generates `memory_suggestions` from the run so internal users can confirm which project knowledge should be written back.
- Commits selected memory suggestions into the Knowledge RAG layer through a human-confirmed API.

Core memory API:

- `POST /api/agent/artifacts/{artifact_id}/knowledge`

## Phase 7F Agent Experience Hardening

The Agent Workspace now has operator controls for real internal use:

- Optional plan approval before tool execution.
- `waiting_plan_approval` state with a confirm-and-run action.
- Run cancellation.
- Clarification resume from the same task when required fields are missing.
- Copy current brief back into the input box.
- Artifact detail modal for full payload inspection.
- Editable memory writeback review before knowledge-base commit.

Core 7F APIs:

- `POST /api/agent/runs/{run_id}/approve-plan`
- `POST /api/agent/runs/{run_id}/cancel`
- `POST /api/agent/runs/{run_id}/clarification`

## Phase 7G Agent Reasoning Graph

The Agent run now generates a `reasoning_graph` artifact and renders it in the Agent Workspace:

- Brief node: the original internal or client-provided requirement.
- Intent node: parsed objective, budget, product, platform, and stage.
- Plan nodes: Agent execution plan steps.
- Knowledge nodes: evidence from the company knowledge base.
- KOL nodes: recommended creators and scores.
- Tag nodes: matched brand/KOL tags that explain fit.
- Risk nodes: risks from matching and simulation.
- Proposal node: client-facing proposal output.
- Tool trace nodes: evidence of tool execution.
- Memory nodes: knowledge writeback suggestions.

This is the current MiroFish-like explanatory graph for Agent reasoning. It is not a hidden chain-of-thought; it is an inspectable business reasoning graph built from artifacts and tool outputs.

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
- `POST /api/auth/bootstrap-admin`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/agent/tasks`
- `GET /api/agent/tasks/{task_id}`
- `GET /api/agent/runtime`
- `GET /api/agent/threads`
- `POST /api/agent/threads`
- `GET /api/agent/threads/{thread_id}`
- `POST /api/agent/threads/{thread_id}/messages`
- `POST /api/agent/chat`
- `POST /api/agent/chat/start`
- `GET /api/agent/runs/{run_id}`
- `GET /api/agent/runs/{run_id}/events`
- `POST /api/agent/runs/{run_id}/approve`
- `POST /api/agent/runs/{run_id}/approve-plan`
- `POST /api/agent/runs/{run_id}/cancel`
- `POST /api/agent/runs/{run_id}/clarification`
- `POST /api/agent/artifacts/{artifact_id}/knowledge`
- `GET /api/knowledge`
- `POST /api/knowledge`
- `GET /api/knowledge/{document_id}`
- `POST /api/knowledge/search`
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
python3 scripts/smoke_openclaw_async.py
python3 scripts/smoke_openclaw_workspace.py
python3 scripts/smoke_agent_model_provider.py
python3 scripts/smoke_data_sources.py
python3 scripts/smoke_storage_adapter.py
python3 scripts/smoke_runtime_config.py
python3 scripts/smoke_postgres_migration.py
DATABASE_URL=postgresql://pr_ai_os:pr_ai_os@localhost:5432/pr_ai_os python3 scripts/smoke_postgres_runtime.py
```

## Notes

This is still a local-first MVP. PostgreSQL / pgvector, managed auth, billing, hosted deployment, and real provider contract validation are the next production hardening steps.
