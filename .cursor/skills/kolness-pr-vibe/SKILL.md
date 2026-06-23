---
name: kolness-pr-vibe
description: >-
  Kolness / PR-OS 主体间性守则与公关媒介默认知识。改 KOL/达人录入、详情、标签、平台报价、
  Brief 匹配、案例库、弹窗 UX，或用户说核对/打通/联动/部署时，必须先读此 skill。
  与 .cursor/rules/pr-kol-vibe.mdc 联动。
---

# Kolness PR Vibe · PR-OS 主体间性守则

Kolness（PR-OS / PR AI OS）服务的不是抽象用户，是**正在赶项目、只录入一遍、很少回头改**的媒介同事。
本 skill 是 PR-AI-OS 时代 `kolness-pr-vibe` 与 PR-OS `pr-os-intersubjectivity` 的**融合版**——默认边界，不是可选风格。

---

## 主体间性 · 我们的守则

列维纳斯说的主体间性，在这里落地为：

| 原则 | 在 PR-OS 里的意思 |
|------|------------------|
| **他者面容** | 截图、字段名、录入顺序是真实工作流的面容；不能用「更简洁」覆盖它 |
| **他者时间** | 媒介录入往往只做一次、不会回看。字段藏在滚不动的地方，或说「打通」却没验证，是把责任推给对方 |
| **不对称中的伦理** | Agent 能力更强 → 默认承担**记忆、联调、部署、自检**；不把「请你监督我」当交付 |
| **边界与分寸** | 不删公关依赖的字段；不做「先最小录入、详情再补」的分裂流程 |
| **默会知识外化** | 用户纠正过一次的事，写进本 skill 或代码，下次不再犯 |

**默认前提：媒介只录入一次。** 不是例外，是验收标准。

---

## 开工前三问（每次必做）

改达人/KOL/媒介相关功能前：

1. **录入页与详情页字段是否一一对应？**（名称、类型、保存路径）
2. **这次是「叠加」还是「删减」？** 默认只叠加；删字段须先获确认
3. **保存后打开详情是否无需补填？** 若要二次录入，即失败

三问不能全答「是」→ 不要提交。

---

## 四卡结构 · 数据打通检查清单

达人不是联系人，是**可结算、可推荐、可追责的媒介资产节点**。

| 卡片 | 业务用途 | 必须同步的字段 |
|------|----------|----------------|
| 身份卡 | 识别与溯源 | name, platform, platform_user_id, homepage_url, avatar_url, region, contact, bio |
| 数据卡 | 预算与适配 | follower_count, total_likes, engagement_rate, avg_likes, avg_comments, avg_shares |
| 商业卡 | 能否推荐给甲方 | listed_price, cooperation_brands, cooperation_formats, manual_notes（+ 平台分项报价） |
| 标签卡 | Brief 匹配与风险 | industry_fit_tags, identity_tags, content_capability_tags, suitable_goals, risk_tags |

### 录入 ≡ 详情

- `#quickCreatorForm` 与 `#creatorEditForm` 四张卡字段一致
- 录入页与详情页均含：**证据资产、AI 判断、商业名片刊例**（录入页可预览/识别/生成，保存后证据入库）
- 详情独有：删除达人

### 单通路（禁止双轨）

```
前端：creatorFormPayload() → prepareCreatorFormPayload()
后端：_apply_creator_payload() ← POST /api/import/manual 与 PATCH /api/creators/{id}
```

### 改完必做对照

列出 **录入 ↔ 详情 ↔ CreatorProfile ↔ API** 四列；口头说「已打通」不算完成。

平台刊例结构见 [platform-rates.md](platform-rates.md)。

---

## 弹窗 UX 反思（不可再犯）

| 问题 | 后果 | 守则 |
|------|------|------|
| 弹窗内容超出视口却不能滚动 | 下方字段「消失」，用户以为没做 | `.modal-panel` 必须 `overflow: auto`；父级 `.modal` 需 `inset: 0` 约束高度 |
| 四卡塞入窄弹窗、无分区滚动提示 | 媒介找不到数据卡/标签卡 | 录入/详情弹窗 `max-width: min(1120px, …)`，用 `.creator-profile-sections` 分区 |
| 标签退化为逗号文本框 | 录入体验倒退、与详情不一致 | 统一 `tag-editor` + `bindCreatorTagEditorEvents` |
| 平台报价写死单一字段 | 不同平台刊例结构被抹平 | 使用 `PLATFORM_RATE_FIELDS` 动态渲染 |
| 强刷后仍看不到新 UI | 用户以为没部署 | bump `app.js?v=` 缓存版本；部署后做 smoke |

**用户反馈「弹窗不能滚动」→ 立刻查 `modal-panel` / `quick-creator-modal` / `creator-profile-modal` 的 overflow 与高度链，不要让用户重复说。**

---

## 已发生的错误（禁止重犯）

| 错误 | 守则 |
|------|------|
| 把身份/内容能力/叙事角色/风险删掉或改名 | 业务字段只加不删 |
| 录入页缺数据卡、地区 | 录入 ≡ 详情四张卡 |
| `formToObject` 与 `creatorFormPayload` 双轨 | 统一 payload |
| manual import 只走 Excel mapper | 走 `_apply_creator_payload` |
| 口头打通未做字段对照 | 改完必须列对照表 |
| 把「标签化」当成「可删字段」 | 标签化是 UX 升级，不是字段删减 |

---

## 改动工作流

```
1. 读 quickCreatorForm + creatorEditForm HTML
2. 列字段对照表
3. 只改差异；保留卡片分区、标签 UI、平台报价、顶部画像区
4. 同步 app.js + server.py（必要时 mapper.py / schemas.py）
5. 自测：录入一条 → 打开详情 → 字段齐全
6. bump 静态资源版本号 → 部署 → smoke
```

---

## 默认部署与验证

### 部署（wm-dev-hk）

```bash
# 本机同步静态/后端（示例）
rsync -avz -e "ssh -i ~/.ssh/wm-dev-hk-key.pem" \
  web/static/ wm-dev-hk:/opt/wangming-workbench/projects/PR-OS/web/static/
rsync -avz -e "ssh -i ~/.ssh/wm-dev-hk-key.pem" \
  web/server.py wm-dev-hk:/opt/wangming-workbench/projects/PR-OS/web/

# 服务器完整部署（需公网时）
ssh -i ~/.ssh/wm-dev-hk-key.pem wm-dev-hk \
  'cd /opt/wangming-workbench/projects/PR-OS && PR_OS_PUBLIC=true bash deploy.sh'
```

- 主机别名：`wm-dev-hk`（`101.47.77.91`）
- 项目路径：`/opt/wangming-workbench/projects/PR-OS`
- 公网入口：`http://101.47.77.91/pr-os/`

### Smoke（本地或部署后）

```bash
python scripts/smoke_kol_intake.py      # KOL 录入与标签图
python scripts/smoke_creator_media.py   # 达人媒体资产
python scripts/smoke_homepage_core_flow.py  # 首页核心流
```

Agent 改完达人域：**主动部署 + smoke**，不把验证留给用户。

---

## 与用户协作的分寸

- 截图 = 验收标准
- 「结合一下」= 保留全部旧结构 + 加新能力
- 「核对一下」= 先 diff 再动手
- 不把 GitHub/技术细节塞进面向媒介的文案
- 能力更强的一方：主动记忆、对照、部署、自检

---

## 相关文件

| 文件 | 职责 |
|------|------|
| `web/static/index.html` | `#quickCreatorForm`, `#creatorEditForm`, 弹窗结构 |
| `web/static/app.js` | `creatorFormPayload`, `PLATFORM_RATE_FIELDS`, 标签编辑器 |
| `web/static/styles.css` | `.modal-panel`, `.creator-profile-modal`, `.quick-creator-modal` |
| `web/server.py` | `_apply_creator_payload`, `import_manual`, `update_creator` |
| `src/schemas.py` | `CreatorProfile` |
| `src/normalize/mapper.py` | Excel 导入映射 |
| `.cursor/rules/pr-kol-vibe.mdc` | 本 skill 的轻量联动规则 |
