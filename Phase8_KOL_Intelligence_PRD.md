# PR AI OS Phase 8 PRD: KOL Intelligence Graph

阶段：**Phase 8 / KOL Intelligence Layer**

## 1. 一句话

Phase 8 把 PR AI OS 的重心收回到达人智能：不管达人数据来自 Excel、API、人工录入还是后续爬取，都统一沉淀为有证据的 KOL 标签，并通过知识图谱演进和预测推荐解释“为什么这个达人适合这个 brief”。

## 2. 核心问题

过去系统已经具备导入、推荐、符号匹配、客户协作和 Agent 操作层，但真正的产品壁垒不应是通用聊天框，而是：

- 能不能解析不标准的达人数据；
- 能不能自动给达人打标签；
- 标签有没有来源和证据；
- 能不能看到标签、品牌需求、风险和 KOL 之间如何演进；
- 能不能预测某个 brief 应该选择哪些 KOL。

## 3. 用户故事

内部媒介或策略同事导入一批达人数据后，点击“分析达人标签”，系统把结构化字段、合作案例、报价、平台表现和符号档案统一成证据标签。

当甲方给出一个 PR brief 时，用户把 brief 输入“达人智能图谱”，系统自动激活相关标签，生成类似 MiroFish 的图谱演进过程，并给出 Top KOL 推荐、命中标签、风险点和证据链。

Agent 后续只是入口和操作层，可以调用这套 KOL Intelligence API，而不是替代它。

## 4. Phase 8 范围

### 4.1 证据标签层

- 从 Creator Profile 生成 `kol_evidence_tags`。
- 支持来源：Excel/API/manual profile、symbolic profile、合作案例、报价、指标。
- 每个标签包含：达人、标签、类别、置信度、分数、来源、证据、状态、版本。

### 4.2 KOL 知识图谱

- 节点：Brief、标签本体、证据标签、KOL、风险。
- 边：包含、激活、推理、匹配。
- 演进步骤：数据接入、标签本体、brief 激活、风险抑制、预测推荐。

### 4.3 预测推荐

- 输入：PR brief。
- 输出：推荐 KOL、匹配分、推荐等级、命中标签、风险点、证据、图谱。
- 预测逻辑先采用可解释规则，后续可接 LLM/embedding/真实效果回流。

### 4.4 UI

- 新增“达人智能图谱”页面。
- 支持分析标签、生成图谱、预测推荐。
- 展示高频标签、最近证据标签、图谱演进、推荐卡片。

## 5. API

- `GET /api/kol-intelligence`
- `GET /api/kol-intelligence/tags`
- `POST /api/kol-intelligence/analyze-tags`
- `POST /api/kol-intelligence/graph`
- `POST /api/kol-intelligence/predict`

## 6. 不做

- 不把 Phase 8 做成通用 Manus clone。
- 不依赖某一个达人数据 API。
- 不在此阶段做复杂多智能体沙箱。
- 不承诺预测为真实投放效果，只输出可解释推荐和待验证假设。

## 7. 成功标准

- Excel/manual/API 导入后的达人可以生成证据标签。
- 任意 brief 可以激活标签并生成图谱。
- 推荐列表必须包含标签、风险和证据。
- UI 能让用户看到从数据到标签、从标签到 KOL 的演进过程。
- smoke test 覆盖完整链路。
