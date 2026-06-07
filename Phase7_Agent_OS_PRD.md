# PR AI OS 第七期 PRD：Agent OS 层

产品暂定名：**PR AI OS Agent Layer**  
阶段：**Phase 7 / M7**  
目标用户：**PR 公司内部项目经理、媒介策略、客户负责人，后续扩展到甲方协作用户**  
文档版本：v0.1  
日期：2026-06-07

---

## 1. 第七期一句话

**第七期把 PR AI OS 从“多个可用工作台”升级成“一个会理解需求、查知识、调用工具、展示过程、等待人工确认、自动沉淀经验的 PR 项目经理 Agent”。**

Phase 7 的核心不是再做一个聊天窗口，而是在已有 Phase 1-5 的业务工具之上，增加一个 AI Native 的操作层：

```text
用户输入 PR 需求
→ Agent 理解任务
→ 查公司知识库
→ 调用 KOL / 符号 / 推演 / 方案工具
→ 展示执行过程
→ 生成交付产物
→ 人工确认
→ 项目结果回流知识库
```

---

## 2. 阶段定位

Phase 1-5 已经完成了 PR OS 的业务骨架：

- 达人数据接入；
- KOL Profile 和标签；
- brief 匹配；
- 符号图谱；
- 甲方方案；
- 博主商业档案；
- Brief 分发；
- Campaign Room；
- 投后复盘。

但这些仍然是多个功能模块。

Phase 7 要解决的是：

> **让用户不需要知道每个模块在哪里，而是只需要表达一个 PR 需求，系统自己组织工作流。**

所以 Phase 7 是 PR AI OS 的 Agent OS 层。

---

## 3. 产品形态

### 3.1 第一形态：Agent 工作台

内部用户进入 `AI Agent` 页面后，可以输入自然语言需求：

```text
预算 40 万，新能源 SUV 上市预热，平台优先小红书，
希望找 8 个 KOL，帮我生成推荐名单、风险说明和甲方方案。
```

系统返回的不是一段普通文本，而是一组结构化执行过程：

- 任务；
- 执行计划；
- 工具调用过程；
- 知识检索结果；
- KOL 推荐；
- 符号分析；
- 风险推演；
- 甲方方案；
- 等待人工确认。

### 3.2 第二形态：Manus-like 执行过程

用户应该能看到 Agent 正在做什么：

```text
Step 1 解析 brief
Step 2 检索公司知识库
Step 3 调用 KOL 推荐工具
Step 4 调用符号图谱工具
Step 5 调用风险推演工具
Step 6 生成甲方方案
Step 7 等待人工确认
```

每一步都应该有：

- 状态；
- 输入摘要；
- 输出摘要；
- 工具名；
- 关键证据；
- 失败原因或重试提示。

### 3.3 第三形态：AI Native PR 公司控制台

长期看，这个 Agent 不只是一个页面，而是整个 PR 公司内部的操作入口。

PR 团队可以通过 Agent：

- 新建项目；
- 查询客户历史偏好；
- 找 KOL；
- 查达人过往履约；
- 生成方案；
- 比较多套策略；
- 推演舆论风险；
- 给甲方输出方案；
- 把项目经验沉淀回知识库。

---

## 4. 用户故事

### 4.1 内部 PR 项目经理

作为 PR 项目经理，我希望只输入一个客户需求，系统就能自动拆解任务、调用内部工具、生成推荐方案，这样我不用在多个页面之间来回操作。

验收标准：

- 支持自然语言输入；
- 自动生成任务和 run；
- 自动调用至少 3 个工具；
- 最终生成可读的方案产物；
- 执行完成后进入人工确认状态。

### 4.2 媒介策略

作为媒介策略，我希望 Agent 在推荐达人前先查询公司知识库和历史项目，这样推荐不是凭空生成，而是基于内部经验。

验收标准：

- Agent 执行时先调用知识检索；
- 知识检索结果出现在产物面板；
- KOL 推荐和风险说明能引用知识库信息；
- 知识库为空时有 fallback。

### 4.3 客户负责人

作为客户负责人，我希望 Agent 生成的方案可以人工确认后再交付给甲方，这样系统不会自动把未经审核的内容发出去。

验收标准：

- Agent run 完成后默认停在 `waiting_approval`；
- 需要内部用户点击确认；
- 确认前不自动对外发送；
- 确认记录可追踪。

### 4.4 公司管理者

作为 PR 公司管理者，我希望每次项目结束后，客户反馈、最终方案、投后复盘能沉淀为公司知识资产，这样公司越用越聪明。

验收标准：

- 支持从项目产物生成知识文档；
- 支持客户偏好、风险规则、案例、方案模板等知识类型；
- 后续 Agent 能检索这些知识；
- 不同 workspace 数据隔离。

---

## 5. 分期路线

Phase 7 拆成 5 个子阶段：

```text
Phase 7A Agent Workspace
Phase 7B Streaming Agent Execution
Phase 7C Knowledge RAG
Phase 7D Agent Planner / Tool Trace / Clarification
Phase 7E Memory Feedback Loop
```

---

## 6. Phase 7A：Agent Workspace

状态：**已完成**

### 6.1 目标

建立 PR 项目经理 Agent 的最小可用工作台。

### 6.2 Scope

- AI Agent 页面；
- task / run / event / artifact runtime；
- Agent 同步执行；
- 本地 RAG 占位；
- 调用现有 PR OS 工具；
- 生成事件流；
- 生成产物；
- 人工确认。

### 6.3 已实现能力

- 自然语言创建 PR Agent 任务；
- 生成 task；
- 生成 run；
- 记录 events；
- 记录 artifacts；
- 调用 project run；
- 生成 proposal；
- 停在 waiting approval。

### 6.4 不做

- 不做复杂 planner；
- 不做多 Agent 协作；
- 不做真正长期记忆；
- 不做工具调用细节可编辑；
- 不做自动追问。

---

## 7. Phase 7B：Streaming Agent Execution

状态：**已完成**

### 7.1 目标

让 Agent 执行过程从一次性返回，升级为可实时观察的执行流。

### 7.2 Scope

- `POST /api/agent/chat/start`；
- 后台执行；
- 事件轮询；
- 前端实时更新；
- run 状态刷新；
- artifact 刷新；
- 完成后人工确认。

### 7.3 已实现能力

- Agent 启动后立即返回 run_id；
- 后台执行工具链；
- 前端每秒轮询；
- 事件流实时出现；
- 产物面板更新；
- 结束状态可见。

### 7.4 不做

- 暂不做 SSE；
- 暂不做 WebSocket；
- 暂不做多用户协同观察同一个 run；
- 暂不做中途暂停/恢复。

---

## 8. Phase 7C：Knowledge RAG

状态：**已完成**

### 8.1 目标

把公司知识、案例、客户偏好、风险规则和模板变成 Agent 可检索的记忆层。

### 8.2 Scope

- 知识库页面；
- 知识文档写入；
- 文档自动 chunk；
- 本地 deterministic embedding fallback；
- hybrid keyword/vector search；
- 知识统计；
- 知识详情；
- Agent RAG 接入；
- PostgreSQL schema 支持。

### 8.3 已实现能力

- `GET /api/knowledge`；
- `POST /api/knowledge`；
- `GET /api/knowledge/{document_id}`；
- `POST /api/knowledge/search`；
- `src/knowledge` 模块；
- Agent 执行时优先检索 knowledge base；
- 前端 `知识库` 页面；
- Phase 7C smoke 测试。

### 8.4 知识类型

第一期支持：

- `manual`：人工录入；
- `case`：项目案例；
- `client_preference`：客户偏好；
- `creator_history`：达人履约历史；
- `risk_policy`：风险规则；
- `template`：方案模板。

### 8.5 不做

- 暂不接云端 embedding 模型；
- 暂不做 pgvector 真实向量索引；
- 暂不做自动从所有项目产物回流；
- 暂不做知识版本审核流。

---

## 9. Phase 7D：Agent Planner / Tool Trace / Clarification

状态：**下一步建议实现**

### 9.1 目标

让 Agent 从“固定流程自动化”升级成“会规划、会追问、过程可解释的 PR 项目经理”。

### 9.2 为什么需要 7D

现在 Agent 已经能跑完整链路，但仍然偏固定流程：

- 用户输入什么，系统尽量直接跑；
- brief 缺字段时不会主动追问；
- 工具调用过程还不够细；
- 计划不是显式对象；
- 用户无法在执行前审查计划。

7D 要补上 Agent 的“项目经理感”。

### 9.3 核心模块

#### 9.3.1 Planner

Agent 先生成执行计划：

```json
{
  "goal": "为新能源 SUV 上市预热生成 KOL 推荐和甲方方案",
  "steps": [
    "parse_brief",
    "search_knowledge",
    "check_missing_fields",
    "run_project",
    "generate_proposal",
    "wait_for_approval"
  ]
}
```

计划需要展示给用户。

#### 9.3.2 Clarification

如果 brief 缺少关键字段，Agent 先追问，不直接硬跑。

关键字段包括：

- 客户/品牌；
- 产品；
- 预算；
- 平台；
- 目标人群；
- 传播阶段；
- KPI；
- 禁忌和风险点。

例子：

```text
你的 brief 缺少预算和目标平台。
请补充：本次预算范围是多少？优先小红书、抖音、微博还是 B 站？
```

#### 9.3.3 Tool Trace

每个工具调用都要记录：

- tool_name；
- input_summary；
- output_summary；
- status；
- latency；
- error；
- linked_artifact_id。

前端要能看到更细的工具过程。

#### 9.3.4 Plan Approval

对于高风险项目，可以先确认计划再执行。

第一版可以默认自动执行，只在 UI 上展示计划。

后续支持：

- 执行前确认；
- 跳过某一步；
- 调整 top_n；
- 改预算；
- 改平台偏好。

### 9.4 7D 验收标准

- Agent run 中有 plan artifact；
- 前端能展示计划；
- brief 缺关键字段时返回 clarification，而不是直接执行；
- 工具调用 trace 细节可见；
- 至少支持 `search_knowledge`、`project_run`、`proposal` 三类工具 trace；
- smoke 测试覆盖 clarification 和正常执行两条路径。

### 9.5 7D 不做

- 不做多 Agent 协同；
- 不做用户拖拽编辑流程图；
- 不做复杂 LangGraph 编排；
- 不做自动发给甲方；
- 不做长期任务队列。

---

## 10. Phase 7E：Memory Feedback Loop

状态：**后续阶段**

### 10.1 目标

让项目结果自动回流到知识库，形成 PR 公司的经验飞轮。

### 10.2 为什么需要 7E

如果知识库只靠人工写入，很快会断。

真正的 AI Native PR 公司应该是：

```text
每次项目执行
→ 产生方案
→ 产生甲方反馈
→ 产生达人选择
→ 产生执行结果
→ 产生投后复盘
→ 自动沉淀为知识
→ 下次 Agent 推荐更准
```

### 10.3 核心模块

#### 10.3.1 Artifact To Knowledge

把 Agent artifact 转成知识文档。

来源包括：

- KOL 推荐产物；
- 甲方方案；
- 风险推演；
- 客户反馈；
- Campaign Room；
- 投后复盘。

#### 10.3.2 Knowledge Suggestion

系统不应该所有内容都自动入库。

第一版建议：

- Agent 生成“建议入库知识”；
- 内部用户点击确认；
- 确认后写入知识库。

#### 10.3.3 Client Preference Learning

从甲方反馈中提取：

- 喜欢的平台；
- 不喜欢的达人类型；
- 预算敏感点；
- 风险敏感点；
- 常用表达；
- 决策偏好。

#### 10.3.4 Creator Performance Memory

从投后复盘中提取：

- 达人履约质量；
- 报价合理性；
- 内容表现；
- 评论区风险；
- 是否适合再次合作；
- 适合什么类型项目。

### 10.4 7E 验收标准

- Agent 产物可以生成知识入库建议；
- 用户可以确认入库；
- 入库后可被 `/api/knowledge/search` 检索；
- 客户反馈可以形成 `client_preference`；
- 投后复盘可以形成 `creator_history`；
- 下次 Agent 执行能检索到这些知识。

### 10.5 7E 不做

- 不做完全自动无审核入库；
- 不做复杂知识图谱推理；
- 不做跨租户知识共享；
- 不做外部数据 API 自动爬取；
- 不做收费计量。

---

## 11. 技术架构

### 11.1 当前技术选择

当前 Phase 7 采用轻量、可替换的本地优先架构：

```text
FastAPI
Vanilla JS frontend
SQLite local runtime
PostgreSQL JSONB migration path
Local auth adapter
Agent model adapter
Knowledge RAG module
Object storage adapter
```

### 11.2 为什么暂不直接上 LangGraph

当前阶段不需要过早引入复杂工作流框架。

原因：

- 业务工具还在快速变化；
- Agent 步骤数量有限；
- 当前重点是产品体验，不是复杂多 Agent 编排；
- 本地可控更重要；
- 未来仍可把 planner/runtime 替换为 LangGraph 或 OpenAI Agents SDK。

### 11.3 未来可替换点

未来可以替换：

- LLM provider：GLM / Qwen / DeepSeek / OpenAI；
- RAG：local embedding fallback → real embedding API → pgvector；
- Streaming：polling → SSE → WebSocket；
- Auth：local auth → Authing / Feishu SSO / OIDC；
- Storage：SQLite → PostgreSQL；
- Agent runtime：local runtime → OpenAI Agents SDK / LangGraph。

---

## 12. 数据模型

### 12.1 Agent

核心对象：

- `agent_tasks`；
- `agent_runs`；
- `agent_events`；
- `agent_artifacts`。

### 12.2 Knowledge

核心对象：

- `knowledge_documents`；
- `knowledge_chunks`。

### 12.3 7D 新增建议

建议新增：

- `agent_plans`；
- `agent_tool_traces`；
- `agent_clarifications`。

也可以第一版先存在 `agent_artifacts` 和 `agent_events` 的 payload 中，等模型稳定后再拆表。

---

## 13. 页面结构

### 13.1 已有页面

- `AI Agent`：Agent 任务、事件流、产物；
- `知识库`：知识写入、搜索、文档列表；
- `新建项目`：完整 PR 项目链路；
- `Campaign OS`：项目作战室；
- `组织管理`：用户和客户权限。

### 13.2 7D 页面增强

`AI Agent` 页面需要新增：

- 计划面板；
- 追问面板；
- 工具 trace 面板；
- artifact detail；
- plan approval 状态。

---

## 14. 成功标准

Phase 7 整体成功标准：

- 用户可以从一个自然语言 PR 需求启动完整项目链路；
- Agent 能先查知识库；
- Agent 能调用多个 PR OS 工具；
- 用户能看到过程；
- 产物能人工确认；
- 项目经验能逐步回流；
- 系统越用越像公司内部的 PR 操作系统。

---

## 15. 当前状态

截至 2026-06-07：

- Phase 7A：已实现；
- Phase 7B：已实现；
- Phase 7C：已实现；
- Phase 7D：建议下一步实现；
- Phase 7E：建议后续实现。

当前最新代码提交：

```text
db6c9cd Add knowledge RAG layer
```

---

## 16. 下一步建议

下一步优先做：

```text
Phase 7D Agent Planner / Tool Trace / Clarification
```

原因：

- 现在已经有 Agent、streaming、知识库；
- 但 Agent 还不够像真正项目经理；
- 用户需要看到它怎么计划、怎么查、怎么调用工具；
- brief 缺字段时需要追问；
- 这一步会明显提升 AI Native 体验。

7D 完成后，再进入：

```text
Phase 7E Memory Feedback Loop
```

让项目结果自动变成公司知识资产。
