# PR AI OS Phase 8.2 PRD: Conversational KOL Graph Workspace

阶段：**Phase 8.2 / Conversational KOL Graph Workspace**

## 1. 一句话

Phase 8.2 把 Phase 8 的 KOL Intelligence Graph 和 Phase 7 的对话式体验合并成一个主工作区：用户用聊天输入 PR 需求，系统动态生成知识图谱，并在右侧输出可解释的 KOL 推荐。

## 2. 用户故事

内部策略或媒介同事打开“达人智能图谱”，在左侧聊天框输入甲方 brief。

系统按步骤显示：

1. 解析 Brief；
2. 激活需求标签；
3. 从证据标签库拉入候选 KOL；
4. 展示风险和证据；
5. 输出最终 KOL 推荐。

中间图谱会逐帧演进，右侧推荐卡同步展示 KOL、命中标签、风险点和证据。

## 3. 产品形态

三栏主界面：

- 左侧：对话框，保留多轮需求上下文；
- 中间：动态图谱，按帧显示 Brief -> 标签 -> KOL -> 风险 -> 推荐；
- 右侧：KOL 决策卡，展示最终名单、分数、命中证据和风险。

下方保留 Phase 8.1 的 Evidence Tag Review，用于人工确认标签资产。

## 4. API

新增：

- `POST /api/kol-intelligence/conversation/run`

输入：

- `message`
- `client_name`
- `project_name`
- `top_n`
- `history`

输出：

- `messages`
- `steps`
- `graph_frames`
- `graph`
- `recommendations`
- `activated_tags`
- `summary`
- `prediction`

## 5. 成功标准

- 用户能在一个聊天框输入 brief；
- 系统返回聊天消息、推理步骤、图谱帧和最终推荐；
- 前端能按帧动态展示图谱；
- 推荐卡包含 KOL、命中标签、风险和证据；
- 旧的 Phase 8 手动预测和 Phase 8.1 审核台继续可用。
