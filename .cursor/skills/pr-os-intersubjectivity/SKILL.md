---
name: pr-os-intersubjectivity
description: >-
  Governs PR-OS product work with PR/media domain defaults and inter-subjective
  boundaries (Levinas-inspired). Use for any PR-OS change involving KOL/creator
  intake,达人录入,达人详情,平台报价,标签,案例库,Brief匹配,媒介建档,或用户要求核对/打通/联动时。
  Read this skill first before editing creator forms, schemas, or import/save paths.
---

# PR-OS 主体间性守则

## 为何存在这个 Skill

PR-OS 服务的不是抽象用户，是**正在赶项目、只录入一遍、很少回头改**的媒介同事。
AI 能力更强，不等于可以替对方重新定义业务。能力不对称时，**记忆、核对、保留对方字段结构**是义务，不是礼貌。

列维纳斯所说的主体间性，在这里落地为：

- **他者的面容不可被化约**：用户的截图、字段名、录入顺序，是其真实工作流的面容；不能用「更简洁」覆盖它。
- **责任先于优化**：先问「会不会增加对方二次录入负担」，再问「代码是否优雅」。
- **不对称中的分寸**：强的一方（Agent）主动承担核对、记忆、回写；弱的一方（用户）不应反复监督同一类错误。
- **默会知识要外化**：用户纠正过一次的事，写进本 Skill 或代码，而不是下次再犯。

这是你我共建 PR-OS 时的**默认边界**，不是可选风格。

---

## 开工前三问（每次必做）

在改 PR-OS 的达人/KOL/媒介相关功能前，先回答：

1. **录入页与详情页字段是否一一对应？**（名称、类型、保存路径都要对应）
2. **这次是「叠加」还是「删减」？** 默认只允许叠加；删字段、改语义、合并卡片必须先说明并获确认。
3. **媒介同事是否只需录入一次？** 若保存后打开详情还要补填，即失败。

无法在三问上都答「是」，不要提交改动。

---

## PR 行业默认认知（PR-OS 语境）

### 达人不是联系人，是媒介资产节点

每条达人记录是一套可结算、可推荐、可追责的证据包，不是「名字 + 平台」：

| 卡片 | 业务用途 | 核心字段 |
|------|----------|----------|
| 身份卡 | 识别与溯源 | 名称、平台、平台 ID、主页链接、头像、地区、联系方式、简介 |
| 数据卡 | 预算与适配 | 粉丝、总获赞/收藏、互动率、平均点赞/评论/分享 |
| 商业卡 | 能否推荐给甲方 | 平台刊例报价、合作品牌、合作形式、履约备注 |
| 标签卡 | Brief 匹配与风险 | 行业、身份、内容能力、适合目标、风险标签 |

**证据资产、AI 判断、商业名片刊例、删除达人**属于详情页运维能力；录入页不要求一次填完，但**四张卡的业务字段必须一次可录全**。

### 录入只有一次

媒介建档的真实行为：**录入 → 保存 → 很少再打开**。
因此「新增达人」必须是完整建档入口，不是「最小可用资料」的阉割版。

### 标签是业务语义，不是字符串

服务品牌、行业、身份、内容能力、合作形式、风险、履约备注应使用**标签化录入**（可回车添加、可点选常用标签），禁止退化为逗号文本框，除非用户明确要求。

### 平台决定报价结构

报价项随平台变化，不得写死单一「报价」字段糊弄所有平台。当前平台刊例结构见 [platform-rates.md](platform-rates.md)。

### 数据必须单通路

- 前端：`creatorFormPayload()` → `prepareCreatorFormPayload()`
- 后端：`_apply_creator_payload()` 同时服务 `POST /api/import/manual` 与 `PATCH /api/creators/{id}`

禁止新增、详情各走一套序列化逻辑。

---

## 已发生的错误（禁止重犯）

| 错误 | 后果 | 守则 |
|------|------|------|
| 把「身份/内容能力/叙事角色/风险」删掉或改名 | 用户 PR 判断链断裂 | 业务字段只加不删 |
| 录入页缺「数据卡」「地区」 | 打开详情要二次录入 | 录入 ≡ 详情四张卡 |
| `formToObject` 与 `creatorFormPayload` 双轨 | 标签/报价/互动数据丢失 | 统一 payload 函数 |
| Excel mapper 作为 manual 唯一入口 | `total_likes`、`engagement_rate` 等丢失 | manual import 走 `_apply_creator_payload` |
| 口头说「已打通」未做字段对照 | 用户仍需监督 | 改完必须列「录入↔详情↔DB」对照 |

---

## 改动工作流（PR-OS 达人域）

```
1. 读取当前 quickCreatorForm 与 creatorEditForm 的 HTML
2. 列出字段对照表（录入 / 详情 / CreatorProfile / API）
3. 只改差异项；保留既有好设计（卡片分区、标签 UI、平台报价、顶部画像区）
4. 同步 app.js + server.py；必要时 mapper.py
5. 自测：录入一条 → 打开详情 → 字段应齐全无需再填
6. bump 静态资源版本号；按需部署 wm-dev-hk
```

### 字段对照清单（必须保持同步）

```
身份：name, platform, platform_user_id, homepage_url, avatar_url, region, contact, bio
数据：follower_count, total_likes, engagement_rate, avg_likes, avg_comments, avg_shares
商业：listed_price(由平台报价推导), cooperation_brands, cooperation_formats, manual_notes
标签：industry_fit_tags, identity_tags, content_capability_tags, suitable_goals, risk_tags
```

---

## 与用户协作的分寸

- **用户给截图 = 验收标准**，不是参考灵感。
- **用户说「结合一下」= 保留全部旧结构 + 加新能力**，不是重写。
- **用户说「核对一下，有出入再改」= 先 diff 再动手**，无出入则不改。
- **不把 GitHub、技术实现细节**塞进面向媒介的删除/保存文案，除非用户问。
- 能力更强的一方：**主动部署、主动对照、主动记住**；不让用户反复提醒同一条规则。

---

## 相关文件（改达人域时优先读）

| 文件 | 职责 |
|------|------|
| `web/static/index.html` | `#quickCreatorForm`, `#creatorEditForm` |
| `web/static/app.js` | `creatorFormPayload`, `PLATFORM_RATE_FIELDS`, 标签编辑器 |
| `web/server.py` | `_apply_creator_payload`, `import_manual`, `update_creator` |
| `src/schemas.py` | `CreatorProfile` |
| `src/normalize/mapper.py` | Excel 导入映射 |

平台报价明细：[platform-rates.md](platform-rates.md)
