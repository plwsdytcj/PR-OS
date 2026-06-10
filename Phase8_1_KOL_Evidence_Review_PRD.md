# PR AI OS Phase 8.1 PRD: KOL Evidence Review

阶段：**Phase 8.1 / KOL Evidence Operations**

## 1. 一句话

Phase 8.1 把 Phase 8 生成的达人证据标签变成可运营资产：媒介同事可以审核、确认、拒绝、要求补证据和调整权重，人工判断会真实影响后续图谱和预测推荐。

## 2. 为什么做

Phase 8 已经跑通：

- Creator Profile / Symbolic Profile -> Evidence Tag；
- Brief -> 标签激活；
- 标签 -> KOL 知识图谱；
- 图谱 -> KOL 预测推荐。

但自动标签如果不能被人工确认，就无法成为 PR 公司的私有判断资产。Phase 8.1 解决的是“可信”和“可运营”。

## 3. 核心用户故事

媒介同事进入“达人智能图谱”，看到系统自动生成的标签队列。每个标签都有达人、类别、置信度、证据和来源。同事可以确认标签、拒绝标签、要求补证据，或批量确认一组标签。

当标签被确认后，系统在预测推荐中提高它的权重；当标签被拒绝后，它不会进入图谱和推荐。这样系统会逐步沉淀公司内部的 KOL 判断资产。

## 4. 功能范围

### 4.1 审核状态

每个 `KolEvidenceTag` 增加：

- `status`: `suggested` / `confirmed` / `rejected` / `needs_more_evidence`
- `reviewer_note`
- `reviewed_by`
- `reviewed_at`
- `weight_delta`
- `version`

### 4.2 审核 API

- `GET /api/kol-intelligence/review-queue`
- `PATCH /api/kol-intelligence/tags/{tag_id}`
- `POST /api/kol-intelligence/tags/bulk-review`

### 4.3 审核工作台

在“达人智能图谱”页面新增 Evidence Tag Review：

- 按状态筛选；
- 按达人筛选；
- 展示证据、来源、置信度和分数；
- 单条确认 / 拒绝 / 补证据；
- 批量确认；
- 审核备注。

### 4.4 达人详情增强

达人详情弹窗新增“证据标签审核”：

- 展示该达人的证据标签；
- 展示状态和证据；
- 支持确认 / 拒绝；
- 与工作台共用同一套审核 API。

### 4.5 预测权重接入

- `confirmed` 标签提高预测权重；
- `needs_more_evidence` 标签降低预测权重；
- `rejected` 标签排除在图谱和预测之外；
- `weight_delta` 可人工微调标签影响力。

## 5. 不做

- 不做复杂 RBAC 审批流；
- 不做投后效果自动学习；
- 不做多 Agent 标签争议裁判；
- 不做第三方 API 数据校验。

这些留给 Phase 8.2 / Phase 9。

## 6. 成功标准

- 自动标签可以进入审核队列；
- 单条和批量审核可以改变标签状态；
- 达人详情页可以查看并审核该达人证据标签；
- 审核状态会影响图谱和预测；
- smoke test 覆盖导入、打标、审核、图谱、预测和详情返回。
