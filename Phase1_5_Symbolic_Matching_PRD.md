# PR AI OS Phase 1.5 PRD：符号标签与传播推演增强

产品暂定名：**PR AI OS - Symbolic Media Agent**  
阶段：**Phase 1.5 / M1.5**  
目标用户：**PR 公司、媒介公司、品牌策略团队、KOL 投放团队**  
文档版本：v0.1  
日期：2026-06-05

---

## 1. Phase 1.5 一句话

**Phase 1.5 在 Phase 1 的媒介公司私有 KOL 工作台之上，增加博主符号档案、品牌/产品符号分析、符号适配评分、内容叙事路径和投放前压力测试，让系统从“根据数据推荐达人”升级为“判断谁能承接品牌叙事、产品隐喻、社会情绪和用户心智位置”。**

---

## 2. 为什么需要 Phase 1.5

Phase 1 已经跑通：

```text
Excel / CSV 导入
→ 统一 KOL Profile
→ 基础商业标签
→ Brief 匹配
→ KOL 推荐
→ Markdown 方案生成
→ 网页版工作台
```

但 Phase 1 仍然偏“媒介数据工作台”。

真正的产品内核不是热度、粉丝、排名和 ROI，而是：

```text
品牌标签
产品标签
博主符号标签
社会情绪
叙事结构
隐喻 / 转喻
联想链
风险误读
合作案例证据
投后标签修正
```

所以在进入 Phase 2 甲方协作之前，需要先把内部工作台升级成：

> **品牌符号网络媒介匹配系统。**

Phase 1.5 的任务不是推翻 Phase 1，而是在 Phase 1 的数据底座上加一层“符号判断层”。

---

## 3. 产品定位升级

### 3.1 Phase 1 的定位

> 媒介公司的私有 KOL 数据工作台。

核心问题：

```text
有哪些达人？
他们在哪个平台？
报价是多少？
适合什么行业？
适合什么内容形式？
给某个 brief 推荐谁？
```

### 3.2 Phase 1.5 的定位

> 品牌—产品—社会情绪—博主符号节点之间的符号适配与传播推演系统。

核心问题：

```text
品牌当前在什么符号位置？
产品应该被放进什么叙事？
博主能不能承接这个叙事？
博主的受众幻想和品牌目标标签是否一致？
这个投放会激活什么联想？
会不会出现误读、污染或反噬？
内容应该走什么隐喻和转喻路径？
```

---

## 4. 核心原则

### 4.1 数据是辅助，不是核心

公关、口碑、品牌传播的核心不是先看：

```text
曝光量
点击率
转化率
ROI
CPM
CPE
GMV
```

而是先判断：

```text
我是谁？
我被谁说？
我和谁站在一起？
我被放进什么叙事？
我激活什么联想？
我避免什么误读？
我在符号网络里的位置有没有改变？
```

数据用于事后校准：

```text
符号假设
→ 内容投放
→ 用户反馈
→ 标签修正
→ 案例沉淀
```

### 4.2 内部语言和外部语言必须分层

内部可以使用高密度分析语言：

```text
能指链
欲望对象
受众幻想
通缩 / 通胀倾向
高结构 / 低结构倾向
叙事滑动
符号污染
```

外部给甲方必须翻译成商业语言：

```text
情绪共鸣型
身份表达型
专业背书型
生活方式型
冲突议题型
消费决策型
财经信任型
技术解释型
审美生活型
焦虑承接型
```

严禁在外部交付中对真实博主使用医学化、病理化或人格审判式标签。

### 4.3 AI 必须给证据

AI 不能只输出结论。

每个关键判断必须包含：

```text
判断
证据摘录
证据来源
置信度
是否需人工确认
```

---

## 5. Phase 1.5 核心模块

Phase 1.5 包含 5 个模块：

```text
博主符号档案生成器
品牌 / 产品符号分析器
符号适配推荐器
内容叙事路径生成器
Campaign Stress Test / MiroFish Adapter
```

---

## 6. 模块一：博主符号档案生成器

### 6.1 输入

输入来自 Phase 1 的 KOL Profile 和补充材料：

- 博主基础信息；
- 平台；
- 主页链接；
- 简介；
- 近 10-30 条内容标题 / 正文；
- 历史合作品牌；
- 合作案例；
- 评论区样本；
- 媒介备注；
- 报价和合作方式。

第一版不要求自动抓取全量内容，可先支持人工粘贴内容样本。

### 6.2 输出字段

```json
{
  "creator_id": "creator_001",
  "primary_tags": ["精致生活方式", "城市通勤"],
  "secondary_tags": ["中产焦虑", "安全感补偿"],
  "persona_structure": "审美生活型",
  "emotional_tone": "安全感缺失后的秩序补偿",
  "narrative_style": "通过场景细节建立可信生活样本",
  "audience_fantasy": "通过审美和消费获得更高级的自己",
  "common_metaphors": ["移动客厅", "城市避难所"],
  "common_metonymies": ["车钥匙", "通勤路线", "露营装备"],
  "suitable_brand_types": ["新能源车", "高端家居", "香氛"],
  "unsuitable_brand_types": ["低价促销", "强冲突话题"],
  "risk_tags": ["过度商业化会破坏审美信任"],
  "evidence": [
    {
      "claim": "审美生活型",
      "source": "内容样本",
      "quote": "高频出现松弛感、质感、通勤、治愈等表达"
    }
  ],
  "confidence": 0.82,
  "manual_status": "pending_review"
}
```

### 6.3 页面能力

- 选择已有博主；
- 粘贴内容样本；
- 粘贴评论样本；
- 粘贴合作案例；
- 点击“生成符号档案”；
- 展示 AI 输出；
- 支持人工修正；
- 支持保存到博主档案；
- 标记对外可见 / 内部可见字段。

---

## 7. 模块二：品牌 / 产品符号分析器

### 7.1 输入

- 品牌名称；
- 行业；
- 产品介绍；
- 目标用户；
- 价格带；
- 传播目标；
- 竞品；
- 历史传播内容；
- 客户 brief；
- 希望获得的品牌标签；
- 希望摆脱的危险标签。

### 7.2 输出字段

```json
{
  "brand_name": "某新能源汽车品牌",
  "product": "新能源 SUV",
  "current_tags": ["智能化", "高端感", "家庭安全"],
  "target_tags": ["移动自由", "城市身份升级", "科技信任"],
  "danger_tags": ["价格争议", "参数空转", "伪高端"],
  "emotional_value": ["安全感", "控制感", "生活半径扩大"],
  "identity_value": ["城市中产", "家庭责任", "男性结构表达"],
  "product_metaphors": ["移动城堡", "第二生活空间"],
  "product_metonymies": ["车钥匙", "智能座舱", "露营装备"],
  "suitable_social_issues": ["城市通勤", "家庭出行", "AI智能化"],
  "unsafe_social_issues": ["价格刺客", "智驾事故", "油电争议"],
  "suitable_creator_types": ["汽车测评", "城市生活方式", "科技解释型"],
  "communication_path": "从城市通勤压力切入，经由智能座舱和安全感叙事，转向家庭生活半径扩张。"
}
```

### 7.3 页面能力

- 输入品牌 / 产品资料；
- 点击“生成品牌符号档案”；
- 查看当前标签、目标标签、危险标签；
- 查看隐喻、转喻、联想链；
- 支持人工修正；
- 保存为项目符号档案。

---

## 8. 模块三：符号适配推荐器

### 8.1 匹配逻辑

Phase 1 的匹配维度是：

```text
行业匹配
内容能力匹配
传播阶段匹配
报价合理性
风险控制
```

Phase 1.5 新增符号适配维度：

```text
领域适配
情绪适配
叙事适配
受众幻想适配
隐喻适配
转喻适配
案例适配
风险可控
```

### 8.2 第一版评分

第一版不用复杂算法，使用：

```text
LLM 标签抽取
+ 规则评分
+ 向量相似度，可选
+ 人工确认
```

评分建议：

| 维度 | 权重 |
|---|---:|
| 领域适配 | 15% |
| 情绪适配 | 15% |
| 叙事适配 | 15% |
| 受众幻想适配 | 15% |
| 隐喻 / 转喻适配 | 15% |
| 案例适配 | 10% |
| 风险可控 | 10% |
| 数据 / 证据可信度 | 5% |

### 8.3 输出

每个推荐博主输出：

- 符号匹配分；
- 推荐等级；
- 符号适配理由；
- 可承接的品牌标签；
- 对应隐喻 / 转喻关系；
- 建议内容方向；
- 风险提示；
- 案例证据；
- 是否建议人工复核。

示例：

```json
{
  "creator_name": "城市通勤研究所",
  "symbolic_score": 88,
  "recommendation_level": "强推荐",
  "matched_brand_tags": ["移动自由", "家庭安全", "城市身份升级"],
  "metaphor_relation": "将新能源 SUV 转译为城市生活中的第二空间",
  "metonymy_relation": "通过通勤路线、车钥匙、周末露营等局部物件承接产品叙事",
  "narrative_fit": "博主长期用城市生活细节建立可信生活样本，适合承接家庭和通勤场景。",
  "risk_points": ["过度硬广会破坏真实生活方式信任"],
  "suggested_content": "围绕一周城市通勤和周末家庭出行，做真实场景体验。"
}
```

---

## 9. 模块四：内容叙事路径生成器

### 9.1 目标

不只是告诉甲方“投谁”，还要告诉：

```text
为什么是这条叙事？
博主应该怎么说？
内容从哪个标签滑向哪个标签？
哪些话不能说？
评论区希望激活什么联想？
```

### 9.2 输出字段

```json
{
  "project": "新能源 SUV 新品预热",
  "creator_name": "城市通勤研究所",
  "start_tag": "城市通勤压力",
  "mediating_tags": ["智能座舱", "家庭安全", "生活半径"],
  "target_tag": "移动自由",
  "narrative_path": "从日常通勤疲惫切入，经由智能座舱和空间舒适感，转向家庭周末出行自由。",
  "metaphor_strategy": "车是移动生活空间",
  "metonymy_strategy": "车钥匙、后备箱、儿童座椅、露营装备",
  "title_directions": [
    "一台车如何改变一个家庭的周末半径",
    "通勤之后，我开始重新理解车里的时间"
  ],
  "must_include": ["真实场景", "智能座舱", "安全感"],
  "must_avoid": ["参数堆砌", "过度豪华", "价格刺激"],
  "comment_guidance": "引导用户讨论通勤、家庭出行和智能化体验，而不是单纯价格。"
}
```

---

## 10. 模块五：Campaign Stress Test / MiroFish Adapter

### 10.1 定位

Campaign Stress Test 是投放前压力测试模块。

MiroFish 可以作为可插拔推演引擎，但不是主系统、不是达人库、不是 ROI 预测工具。

对外表达：

```text
投放前压力测试
舆论风险模拟
传播路径推演
多角色反馈模拟
```

禁止表达：

```text
爆款预测
ROI 预测
真实传播结果预测
```

### 10.2 第一版实现

第一版先支持：

```text
LLM 多角色模拟 fallback
```

角色：

- 目标消费者；
- 平台评论区用户；
- 甲方市场负责人；
- 媒介执行人员；
- 竞品观察者；
- 舆情风险观察者；
- 品牌合规观察者。

### 10.3 MiroFish Adapter

后续支持 MiroFish CLI / 服务化调用。

输入：

```text
品牌符号档案
产品符号档案
推荐博主组合
内容叙事路径
已知风险
推演要求
```

输出：

```text
正向反馈
负向反馈
风险点
误读点
争议路径
优化建议
是否建议调整方案
```

集成方式：

```text
Campaign Plan
      ↓
Stress Test Adapter
      ↓
LLM fallback / MiroFish / OASIS
      ↓
Simulation Report
      ↓
方案风险提示和优化建议
```

### 10.4 输出示例

```json
{
  "summary": "该方案能建立城市通勤和家庭安全叙事，但存在价格争议和智驾安全误读风险。",
  "positive_reactions": [
    "目标用户容易被真实通勤场景吸引",
    "家庭安全叙事有助于提高品牌信任"
  ],
  "negative_reactions": [
    "部分用户可能质疑价格过高",
    "如果过度强调智能驾驶，可能引发安全争议"
  ],
  "misreading_points": [
    "被理解成伪高端",
    "被认为只是在堆参数"
  ],
  "optimization_suggestions": [
    "减少参数表达，增加真实家庭使用细节",
    "保留垂类测评达人解释安全和技术边界",
    "避免用绝对化语言描述智驾能力"
  ]
}
```

---

## 11. 数据模型

### 11.1 Creator Symbolic Profile

```json
{
  "creator_id": "creator_001",
  "primary_tags": ["城市通勤", "家庭生活方式"],
  "secondary_tags": ["安全感补偿", "中产生活秩序"],
  "persona_structure": "生活方式审美型",
  "emotional_tone": "安全感缺失后的秩序补偿",
  "narrative_style": "真实场景细节叙事",
  "audience_fantasy": "通过更好的工具和空间获得稳定生活",
  "common_metaphors": ["移动客厅", "城市避难所"],
  "common_metonymies": ["车钥匙", "通勤路线", "后备箱"],
  "suitable_brand_types": ["新能源车", "家居", "香氛", "城市生活方式"],
  "unsuitable_brand_types": ["低价促销", "强冲突议题"],
  "risk_tags": ["硬广破坏真实感"],
  "evidence": [],
  "confidence": 0.82,
  "visibility": "internal"
}
```

### 11.2 Brand Symbolic Profile

```json
{
  "brand_id": "brand_001",
  "brand_name": "某新能源汽车品牌",
  "product": "新能源 SUV",
  "current_tags": ["智能化", "高端感"],
  "target_tags": ["移动自由", "家庭安全", "城市身份升级"],
  "danger_tags": ["价格争议", "伪高端"],
  "emotional_value": ["安全感", "控制感"],
  "identity_value": ["城市中产", "家庭责任"],
  "product_metaphors": ["移动城堡", "第二生活空间"],
  "product_metonymies": ["车钥匙", "智能座舱", "露营装备"],
  "communication_path": "从城市通勤压力切入，转向家庭生活半径扩张。"
}
```

### 11.3 Symbolic Match Result

```json
{
  "project_id": "project_001",
  "creator_id": "creator_001",
  "symbolic_score": 88,
  "domain_fit": 5,
  "emotion_fit": 4,
  "narrative_fit": 5,
  "audience_fit": 4,
  "metaphor_fit": 5,
  "case_fit": 4,
  "risk_control": 4,
  "match_reason": "博主的城市通勤和家庭生活方式叙事能够承接新能源 SUV 的移动自由与安全感标签。",
  "risk_points": ["硬广化会破坏真实感"],
  "suggested_content_direction": "真实通勤 + 周末家庭出行场景体验"
}
```

### 11.4 Simulation Report

```json
{
  "project_id": "project_001",
  "plan_id": "plan_001",
  "engine": "llm_fallback",
  "summary": "方案风险中等，可执行性较高。",
  "positive_reactions": [],
  "negative_reactions": [],
  "misreading_points": [],
  "optimization_suggestions": [],
  "created_at": "2026-06-05"
}
```

---

## 12. 页面设计

### 12.1 博主符号档案页

功能：

- 从达人库选择博主；
- 查看基础 KOL Profile；
- 粘贴内容样本；
- 粘贴合作案例；
- 生成符号档案；
- 查看证据和置信度；
- 人工修正；
- 保存。

### 12.2 品牌符号分析页

功能：

- 输入品牌/产品信息；
- 输入传播目标；
- 输入竞品和危险联想；
- 生成品牌符号档案；
- 人工修正；
- 保存为项目。

### 12.3 符号匹配页

功能：

- 选择品牌符号档案；
- 选择博主库；
- 生成符号匹配推荐；
- 展示匹配分和理由；
- 展示隐喻/转喻关系；
- 展示建议内容方向；
- 加入方案。

### 12.4 内容叙事路径页

功能：

- 对单个博主生成内容 brief；
- 输出标题方向；
- 输出必须出现 / 不能出现；
- 输出评论区引导；
- 支持复制给媒介或客户。

### 12.5 压力测试页

功能：

- 选择方案；
- 选择推演引擎：LLM fallback / MiroFish；
- 运行压力测试；
- 输出正负反馈、误读点、风险和优化建议；
- 回写方案。

---

## 13. MVP 范围

### 13.1 必须做

1. Creator Symbolic Profile 数据结构；
2. Brand Symbolic Profile 数据结构；
3. 博主符号档案生成器，LLM 或规则 fallback；
4. 品牌/产品符号分析器，LLM 或规则 fallback；
5. 符号匹配评分；
6. 内容叙事路径生成；
7. LLM 多角色压力测试 fallback；
8. Web 页面入口；
9. 内部/外部语言字段分层；
10. 证据摘录和置信度字段。

### 13.2 可选做

1. MiroFish CLI Adapter；
2. OASIS Adapter；
3. pgvector 相似检索；
4. 社会符号网络表；
5. 飞书多维表格同步；
6. 博主刊例 PDF / 网页导出；
7. 投后标签修正器。

### 13.3 暂不做

1. 不做全网自动爬虫；
2. 不做医学化标签外显；
3. 不做真实 ROI 预测；
4. 不做爆款预测；
5. 不做完全自动投放决策；
6. 不做甲方协作入口，留到 Phase 2；
7. 不做博主开放注册。

---

## 14. 技术实现建议

### 14.1 当前项目上增量实现

保留现有：

```text
FastAPI
SQLite
静态 Web UI
CreatorProfile
brief_parser
matching
proposal_generator
```

新增：

```text
src/symbolic/
  schemas.py
  creator_profiler.py
  brand_profiler.py
  symbolic_matching.py
  narrative_path.py
  prompts.py

src/simulation/
  stress_test_adapter.py
  llm_fallback.py
  mirofish_adapter.py
```

### 14.2 后续产品化技术栈

```text
Frontend: Next.js + React
Backend: FastAPI
LLM: OpenAI Responses API / Claude / 通义
Database: PostgreSQL
Vector: pgvector
Queue: Redis + RQ / Celery
Simulation: LLM fallback + MiroFish / OASIS Adapter
Storage: S3 / Supabase Storage
```

第一版不强制上 Neo4j。符号网络先用关系表和 JSON 字段实现，后续复杂后再考虑图数据库。

---

## 15. 成功标准

Phase 1.5 成功标准：

1. 系统能为博主生成符号档案；
2. 系统能为品牌/产品生成符号档案；
3. 推荐理由从“数据适配”升级为“符号适配”；
4. 每个关键判断有证据和置信度；
5. 系统能生成内容叙事路径；
6. 系统能做投放前压力测试；
7. 内部分析语言和外部交付语言分离；
8. 用户能感知：这不是普通达人库，而是品牌叙事和媒介节点的匹配系统。

---

## 16. 核心结论

Phase 1.5 不是重做 Phase 1。

Phase 1 是数据底座：

```text
谁是博主？
有哪些资料？
怎么导入？
怎么统一成 Profile？
```

Phase 1.5 是判断层：

```text
这个博主是什么符号节点？
这个品牌想进入哪条叙事链？
二者之间有没有隐喻、转喻、情绪和受众幻想的适配？
投放后可能出现什么误读？
内容应该如何设计？
```

Phase 1.5 完成后，再进入 Phase 2 甲方协作入口，甲方看到的就不再只是“推荐达人表”，而是：

```text
品牌符号诊断
媒介符号匹配
内容叙事路径
投放前压力测试
```

这才是 PR AI OS 的真正差异化。
