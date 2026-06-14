# Kolness × OpenClaw Agent Dock PRD

文档版本：v0.3  
日期：2026-06-14  
阶段：OpenClaw Sidecar MVP  
目标用户：Kolness 内部 PR 团队成员  

实现状态：v0.3 已接入 Kolness 后端桥、异步 OpenClaw run、Kolness Agent 浮窗、`/openclaw` 原生控制台壳和页面级 smoke test。真实 OpenClaw Control UI / Gateway 仍由独立服务提供，通过 Admin Console 配置 URL。

---

## 1. 一句话

**在 Kolness 里加一个类似 Manus 的 Agent 浮窗，让内部员工可以直接和背后的 OpenClaw Agent 对话；OpenClaw 负责长任务、流式执行和工具调用，Kolness 负责 PR/KOL 数据、权限和资产沉淀。**

---

## 2. 背景判断

Kolness 现在已经有：

- 登录和内部角色；
- PR brief 输入；
- KOL 推荐；
- 达人库和标签；
- MiroFish-like / 决策图谱；
- Campaign 历史资产；
- Agent runtime 和 OpenAI Agents SDK POC。

但当前 Agent UI 仍然偏 Kolness 自己实现的轻量工作台。用户期望更接近 Manus：

- 纯对话式；
- 输入一个 brief 后自动跑；
- 能看到流式过程；
- 能看到工具调用；
- 能沉淀产物；
- 能恢复历史任务。

因此引入 OpenClaw 的方式不应该是替换 Kolness，而是作为内部员工的 **Agent Sidecar**。

---

## 3. 产品边界

### 3.1 Kolness 负责什么

Kolness 是 PR/KOL 业务 OS，继续负责：

- 用户登录和权限；
- 员工 / Admin / 客户账号管理；
- Campaign；
- KOL 数据库；
- 达人标签和证据；
- KOL 匹配；
- 决策图谱；
- 客户方案；
- 历史资产；
- 对象存储和数据库。

### 3.2 OpenClaw 负责什么

OpenClaw 是 Agent 执行层，负责：

- 对话式任务空间；
- 长任务执行；
- 流式输出；
- 工具调用过程；
- session / workspace；
- memory；
- Canvas / tool cards；
- 外部 agent 执行体验。

### 3.3 不做什么

第一阶段不做：

- 不把 Kolness 整体迁移到 OpenClaw；
- 不让客户侧直接使用 OpenClaw；
- 不开放通用 shell / terminal 给所有员工；
- 不做复杂计费；
- 不做多个 OpenClaw Gateway 的自动调度；
- 不把第三方 OpenClaw UI 当成 Kolness 长期主前端。

---

## 4. 核心 User Story

### 4.1 内部 PR 员工

作为内部 PR 员工，我希望在 Kolness 里点一个浮窗，直接把甲方 brief 丢进去，让 Agent 帮我跑 KOL 推荐、风险分析和方案草稿。

验收标准：

- 页面右下角有 `Ask Agent`；
- 点击后出现 Agent 浮窗；
- 输入 brief 后可以发送给 OpenClaw；
- 浮窗显示 Agent 回复和运行状态；
- OpenClaw 产物能回写 Kolness Campaign 资产库。

### 4.2 媒介员工

作为媒介员工，我希望 Agent 能调用 Kolness 的达人库和标签，而不是凭空推荐。

验收标准：

- OpenClaw 可调用 `kolness.search_kol`；
- OpenClaw 可调用 `kolness.match_kol`；
- 推荐结果包含达人、标签、预算、风险理由；
- 推荐结果保存到 Campaign。

### 4.3 Admin

作为 Admin，我希望一个 OpenClaw Gateway 可以服务多个内部员工，每个员工有隔离的 agent/session。

验收标准：

- Admin Console 可配置 OpenClaw Gateway；
- Admin Console 可配置用户到 `openclaw_agent_id` 的映射；
- 不同员工默认进入不同 agent；
- Kolness 仍然控制工具权限。

---

## 5. OpenClaw 分配方案

### 5.1 第一阶段推荐：一个 Gateway，多 Agent

第一阶段采用：

```text
One OpenClaw Gateway
  ├── agent_kolness_admin
  ├── agent_alice
  ├── agent_bob
  └── agent_media_team
```

原因：

- 内部自用，风险可控；
- 部署简单；
- 成本低；
- 一个 Gateway 可以管理多个 isolated agent/session；
- 先验证体验比先做复杂运维更重要。

Kolness 做真正的权限控制：

- 哪个用户能绑定哪个 OpenClaw agent；
- 哪个用户能调用哪些 Kolness tools；
- 哪个用户能看哪些 Campaign；
- 哪个用户能导出数据或发布客户方案。

OpenClaw 做运行隔离：

- 每个 agent 独立 workspace；
- 每个 agent 独立 session；
- 每个 agent 独立 memory；
- 每个 agent 独立 model / auth profile。

### 5.2 第二阶段：关键员工独立 Gateway

当内部使用变重后，可以升级：

```text
Kolness
  ├── Shared OpenClaw Gateway
  │   ├── normal_staff_a
  │   └── normal_staff_b
  ├── Alice Dedicated Gateway
  └── Strategy Team Dedicated Gateway
```

适用条件：

- 某些员工任务很重；
- 某些团队需要更强数据隔离；
- 某些 agent 需要特殊工具或模型；
- Gateway 资源瓶颈明显。

### 5.3 第三阶段：团队 + 个人混合

长期推荐：

```text
Team Agents
  ├── strategy_agent
  ├── media_agent
  └── proposal_agent

Personal Agents
  ├── alice_agent
  └── bob_agent
```

团队 agent 沉淀公共知识，个人 agent 保留个人工作上下文。

---

## 6. 前端形态

### 6.1 Phase OC-1：快速浮窗

目标：先让用户在 Kolness 里打开一个浮窗，能和 OpenClaw 对话。

入口：

```text
右下角 Ask Agent
```

浮窗结构：

```text
┌────────────────────────────┐
│ PR Copilot                 │
│ OpenClaw 深度任务           │
├────────────────────────────┤
│ Agent: 把 brief 发给我       │
│                            │
│ You: 预算50万...            │
│                            │
│ Agent: 我开始分析需求...     │
│ Tool: kolness.search_kol    │
│ Tool: kolness.match_kol     │
│ Asset: KOL 推荐名单          │
├────────────────────────────┤
│ 输入 brief / 继续追问         │
└────────────────────────────┘
```

按钮：

- `发送`：发送消息给当前 OpenClaw agent；
- `全屏`：打开 OpenClaw Workspace；
- `新任务`：创建新的 OpenClaw session；
- `保存到 Campaign`：把产物回写 Kolness；
- `查看资产`：打开 Kolness Campaign 资产页。

### 6.2 Phase OC-1.1：嵌入 OpenClaw Control UI

如果 OpenClaw Control UI 已部署，可以先做嵌入页：

```text
/openclaw
```

页面布局：

```text
┌──────────────┬────────────────────┬──────────────┐
│ Kolness      │ OpenClaw Control UI │ Kolness      │
│ Campaign     │ iframe/proxy        │ Assets       │
│ Context      │                     │              │
└──────────────┴────────────────────┴──────────────┘
```

优点：

- 最快看到 Manus-like 体验；
- 复用 OpenClaw 的流式输出和工具卡；
- 不需要马上自己写 WebSocket renderer。

缺点：

- UI 风格与 Kolness 不完全一致；
- 权限和资产需要 Kolness 外层兜住；
- 体验像“Kolness 内嵌另一个工具”。

### 6.3 Phase OC-2：Kolness 原生 Manus-like UI

后续不再 iframe，而是 Kolness 自己渲染 OpenClaw event stream：

```text
OpenClaw Gateway WebSocket
  -> Kolness OpenClaw Adapter
  -> Kolness SSE / WebSocket
  -> AgentDock / AgentWorkspace
```

前端事件类型：

```text
message.delta
message.completed
tool.started
tool.delta
tool.completed
artifact.created
canvas.updated
approval.required
run.completed
run.failed
```

---

## 7. 后端对接设计

### 7.1 配置

新增环境变量：

```bash
OPENCLAW_ENABLED=false
OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789
OPENCLAW_CONTROL_UI_URL=http://127.0.0.1:18789
OPENCLAW_ADMIN_TOKEN=
OPENCLAW_DEFAULT_AGENT_ID=kolness_default
OPENCLAW_PROXY_BASE_PATH=/openclaw
```

### 7.2 数据表

新增配置表：

```text
openclaw_user_bindings
  id
  user_id
  openclaw_gateway_url
  openclaw_agent_id
  openclaw_session_id
  status
  created_at
  updated_at
```

新增事件映射表：

```text
openclaw_runs
  id
  user_id
  campaign_id
  openclaw_agent_id
  openclaw_session_id
  status
  last_event_at
  created_at
  updated_at
```

新增事件日志表：

```text
openclaw_events
  id
  run_id
  event_type
  payload_json
  created_at
```

### 7.3 API

Kolness 后端新增：

```text
GET  /api/openclaw/status
GET  /api/openclaw/me
POST /api/openclaw/sessions
POST /api/openclaw/chat
GET  /api/openclaw/runs/{run_id}/events
POST /api/openclaw/runs/{run_id}/save-to-campaign
GET  /openclaw/*
```

说明：

- `/api/openclaw/me` 返回当前用户绑定的 `openclaw_agent_id`；
- `/api/openclaw/sessions` 创建或恢复 OpenClaw session；
- `/api/openclaw/chat` 发送用户消息；
- `/api/openclaw/runs/{run_id}/events` 用 SSE 返回过程；
- `/openclaw/*` 代理 OpenClaw Control UI。

---

## 8. Kolness Tools 给 OpenClaw

第一批工具：

```text
kolness.analyze_brief
kolness.search_kol
kolness.match_kol
kolness.get_creator_profile
kolness.tag_creator
kolness.generate_kol_graph
kolness.generate_proposal
kolness.save_campaign_asset
kolness.get_campaign_history
kolness.create_client_share_page
```

工具调用需要带：

```json
{
  "user_id": "internal_user_id",
  "workspace_id": "default",
  "campaign_id": "optional_campaign_id",
  "tool_name": "kolness.match_kol",
  "input": {}
}
```

Kolness 后端必须校验：

- 当前用户是否登录；
- 当前用户是否能访问 workspace；
- 当前用户是否能访问 campaign；
- 当前用户是否有 tool 权限；
- 工具输出是否需要脱敏。

---

## 9. 权限模型

### 9.1 用户角色

```text
admin
internal_staff
strategy_staff
media_staff
client
```

第一阶段：

- `client` 不允许使用 OpenClaw；
- `admin` 可以配置 OpenClaw；
- `internal_staff` 可以使用自己的 OpenClaw agent；
- `media_staff` 可以使用达人相关工具；
- `strategy_staff` 可以使用策略和方案工具。

### 9.2 Tool 权限

| Tool | Admin | Internal | Strategy | Media | Client |
| --- | --- | --- | --- | --- | --- |
| analyze_brief | yes | yes | yes | no | no |
| search_kol | yes | yes | yes | yes | no |
| match_kol | yes | yes | yes | yes | no |
| tag_creator | yes | no | no | yes | no |
| generate_kol_graph | yes | yes | yes | yes | no |
| generate_proposal | yes | yes | yes | no | no |
| save_campaign_asset | yes | yes | yes | yes | no |
| create_client_share_page | yes | limited | no | no | no |

---

## 10. 快速实现路径

### Step 1：Admin 配置

在 Admin Console 增加：

- OpenClaw enabled；
- Gateway URL；
- Control UI URL；
- Admin token；
- 默认 agent id；
- 用户到 agent id 映射。

### Step 2：后端 Adapter

新增：

```text
src/lib/openclaw_adapter.py
```

职责：

- 读取 OpenClaw 配置；
- 创建 session；
- 发送 chat message；
- 拉取或订阅 event；
- 把 event 标准化成 Kolness 事件；
- 回写 campaign asset。

### Step 3：浮窗模式切换

Agent Dock 增加运行模式：

```text
快速推荐
OpenClaw 深度任务
```

选择 `OpenClaw 深度任务` 时：

```text
用户输入
  -> /api/openclaw/chat
  -> OpenClaw Gateway
  -> OpenClaw agent
  -> Kolness tool API
  -> event stream
  -> Agent Dock
```

### Step 4：OpenClaw Workspace 页面

新增页面：

```text
view: openclawWorkspace
route: /openclaw
```

第一版直接嵌入 Control UI。

### Step 5：资产回写

OpenClaw 工具产物回写到：

- Campaign；
- Agent thread；
- Artifact；
- KOL recommendation；
- Graph asset；
- Proposal asset。

---

## 11. MVP 验收标准

第一版完成后，必须满足：

- Admin 可以配置 OpenClaw Gateway；
- 当前登录用户可以绑定一个 `openclaw_agent_id`；
- 右下角 Agent 浮窗可以选择 `OpenClaw 深度任务`；
- 用户可以在浮窗里发送 brief；
- OpenClaw 可以收到消息并返回回复；
- 浮窗可以看到至少一种流式或轮询更新；
- OpenClaw 可以调用至少一个 Kolness tool；
- 结果可以保存到 Campaign 资产；
- Client 账号不能访问 OpenClaw；
- 不同内部用户默认进入不同 agent/session。

---

## 12. 风险

### 12.1 第三方 UI 风格割裂

短期接受，长期用 Kolness 原生 UI 替代。

### 12.2 OpenClaw 权限不是 Kolness 权限

必须让 Kolness 后端做工具权限校验，不能只依赖 OpenClaw。

### 12.3 通用 Agent 工具过强

默认只开放 PR 白名单工具，不给普通员工开放 shell / arbitrary browser / filesystem。

### 12.4 资产没有沉淀

所有 OpenClaw 产物必须回写 Kolness，否则只是一个聊天工具。

---

## 13. 推荐结论

第一阶段不要重构整站，也不要一开始每个员工部署一个独立 OpenClaw。

推荐方案：

```text
一个 OpenClaw Gateway
  + 多个 OpenClaw agent/session
  + Kolness 权限控制
  + Kolness Agent Dock 浮窗
  + OpenClaw Control UI 嵌入页
  + Kolness tool API
```

这样最快能实现：

- 点击浮窗；
- 和 OpenClaw 聊；
- 看到类似 Manus 的过程；
- 调用 Kolness 的 PR/KOL 工具；
- 把结果沉淀回 Campaign。

---

## 14. 2026-06-13 实现状态

### 已完成

- 右下角 Agent 浮窗支持切换 `OpenClaw 深度任务` runtime。
- Admin Console 支持配置 OpenClaw Gateway、Control UI、Admin Token、默认 Agent ID。
- Admin Console 支持给内部员工绑定 `openclaw_agent_id` 和 `openclaw_session_id`。
- 后端已提供：
  - `GET /api/openclaw/status`
  - `GET /api/openclaw/me`
  - `POST /api/openclaw/sessions`
  - `POST /api/openclaw/chat`
  - `GET /api/openclaw/runs/{run_id}/events`
  - `GET /api/openclaw/runs/{run_id}/stream`
  - `POST /api/openclaw/runs/{run_id}/save-to-campaign`
  - `GET /api/openclaw/tools`
  - `POST /api/openclaw/tools/{tool_name}`
  - `GET /openclaw`
  - `/openclaw/proxy/*`
- OpenClaw 可调用 Kolness 工具：
  - `kolness.analyze_brief`
  - `kolness.search_kol`
  - `kolness.get_creator_profile`
  - `kolness.tag_creator`
  - `kolness.match_kol`
  - `kolness.generate_kol_graph`
  - `kolness.generate_proposal`
  - `kolness.get_campaign_history`
  - `kolness.create_client_share_page`
  - `kolness.save_campaign_asset`
- OpenClaw run 可以保存成 Kolness Campaign Project，并进入历史资产 / Campaign Room。
- 浮窗支持：
  - `新任务`
  - `保存到 Campaign`
  - `查看资产`
  - `全屏` 打开 Kolness 自己的 Agent Workspace，用于查看 Thread、过程日志和交付产物
  - `OpenClaw 原生` 打开 `/openclaw`，用于进入 OpenClaw Control UI 壳页面
- `/openclaw` 已从纯 iframe 升级为 Kolness × OpenClaw Workspace：
  - 顶部显示 Kolness / OpenClaw 入口；
  - 左侧显示当前内部账号、agent id、session id 和使用边界；
  - 中间 iframe/proxy 嵌入 OpenClaw Control UI；
  - 右侧显示已开放的 Kolness MCP tools 和资产回写说明；
  - 未配置 Gateway / Control UI 时显示明确的配置提示页。

### 已验证

- `python3 -m py_compile web/server.py src/openclaw/*.py`
- `node --check web/static/app.js`
- `python3 -m unittest tests.test_openclaw_adapter`
- `python3 scripts/smoke_openclaw_async.py`
- `python3 scripts/smoke_openclaw_workspace.py`
- `python3 scripts/smoke_openclaw_permissions.py`
- `python3 scripts/smoke_openclaw_campaign_asset.py`
- `python3 scripts/smoke_openclaw_async_save_flow.py`
- 浏览器会话验证：
  - OpenClaw session 创建返回 200；
  - 10 个 Kolness tools 可见；
  - brief 解析返回行业/产品；
  - KOL 匹配返回候选达人；
  - 历史 Campaign 读取返回结果；
  - OpenClaw run event 和 SSE stream 可读；
  - run 可保存到 Campaign；
  - 达人档案读取和标签写入可用；
  - 甲方 share page 可生成。
  - `/app` 存在 OpenClaw 原生入口按钮；
  - `/openclaw` 未配置 / 已配置状态均可渲染正确页面。
  - 甲方账号不能访问 `/openclaw`、OpenClaw chat/session/status/tools；
  - OpenClaw service token 只能访问 `/api/openclaw/tools/*`。
  - OpenClaw run 可以通过 `save-to-campaign` 保存为 Campaign；
  - 保存后的 Campaign 能进入历史资产，并保留 OpenClaw response/events。
  - 从历史资产打开 Campaign Room 后，仍能读取 `openclaw_run_saved` timeline 和原始 OpenClaw response/events。
  - 浮窗同等的 `async:true` OpenClaw run 完成后，也可以保存为 Campaign 并在 Campaign Room 找回。

### 仍需真实 Gateway 才能验收

- OpenClaw 的真实流式 token 输出；
- OpenClaw 自己的工具卡 / Canvas / workspace 体验；
- OpenClaw memory 和长任务恢复；
- OpenClaw 多 agent 工作区隔离；
- Gateway 侧对 Kolness tool manifest 的自动发现和调用。
