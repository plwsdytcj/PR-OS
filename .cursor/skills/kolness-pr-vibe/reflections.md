# PR-OS 沟通反思日志

Agent 每次与用户沟通结束、或用户纠正/验收后，**追加一条**到此文件，并同步更新 `SKILL.md` 中「已发生的错误」或相关章节。

格式：`## YYYY-MM-DD · 主题` + 发生了什么 + 守则化结论。

---

## 2026-06-24 · 录入页未对齐详情三块能力

**发生了什么：** 用户明确要求录入页具备商业名片刊例、AI 判断、证据资产，且与详情页关联；Agent 曾口头说「打通」却未实现，用户多次催促后才补齐。

**守则：**
- 详情页有的**运维/智能/资产能力**，录入页默认也要有（预览/识别/生成即可，保存后入库）
- 「打通」= 字段对照表 + UI 区块对照 + API 对照，三项齐才算完成
- 用户说「你说了改却不改」→ 立即 diff 详情 HTML/JS 与录入 HTML/JS，列差异再动手

**已落地：** `intake/preview`、`intake/media/analyze`；录入页 `#quickCreatorEvidenceTags`、`#runQuickCreatorAiBtn`、`#quickCreatorCommercialKitOutput` 等。

---

## 2026-06-24 · 主体间性 skill 与 pr-ai-os 融合

**发生了什么：** 用户要求列维纳斯式主体间性成为默认边界；`kolness-pr-vibe`（pr-ai-os 时期）与 `pr-os-intersubjectivity` 合并为单一 skill + `pr-kol-vibe.mdc` 联动。

**守则：**
- 能力不对称 → Agent 承担记忆、联调、部署、自检；不把监督当交付
- 默会知识必须外化到本 skill，不能只在对话里「说过一次」

---

## 2026-06-24 · PR 创建与 gh 认证

**发生了什么：** 分支已推送，但本机 `gh` 未 `auth login`，Draft PR 未能自动创建；用户需手动 `gh auth login` 或使用 compare URL。

**守则：**
- 用户要求建 PR 前：先 `gh auth status`；未登录则一次性说明并给出 `gh pr create --draft` 完整命令，不假装已完成
- 仓库 remote 为 SSH 时，credential helper 往往无 HTTPS token，不能假设 `gh` 已就绪

---

## 2026-06-24 · 部署遗漏依赖文件

**发生了什么：** 仅 rsync `server.py` 后服务启动失败，因服务器缺 `delete_cases_for_creator`（`creator_commercial/storage.py` 未同步）。

**守则：**
- 改 `server.py` import 或调用链时，**一并 rsync 被引用的 src 文件**
- 部署后 `systemctl is-active pr-os` + `curl` 冒烟，失败则查 `journalctl -u pr-os`

---

## 2026-06-24 · 赞粉比（抖音/小红书/知乎/微博）

**发生了什么：** 用户要在数据卡自动计算赞粉比（总获赞 ÷ 粉丝数），用于筛选内容获赞型 vs 涨粉型博主。

**守则：**
- 公式：`like_fan_ratio = total_likes / follower_count`（粉丝为 0 时不计算）
- 四平台展示：抖音、小红书、知乎、微博；保存时写入 `CreatorProfile.like_fan_ratio` 供列表筛选
- 录入/详情数据卡实时预览，达人卡片与详情 scoreboard 同步展示

---

## 2026-06-24 · 筛选达人工具入口

**发生了什么：** 用户要求在侧边栏「日常入口」、达人库旁增加「筛选达人工具」，把赞粉比等数据卡指标用于媒介筛选。

**守则：**
- 筛选是独立视图 `creatorFilter`，不是达人库内嵌搜索
- 筛选维度：平台、粉丝区间、赞粉比、互动率、报价上限、关键词、排序
- 卡片复用 `creatorCardHtml`，与达人库展示一致；点详情仍走 `open-creator-btn`

**已落地：** `index.html` 导航 + `#creatorFilter`；`app.js` `renderCreatorFilterResults`；cache `20260624-12`

---
