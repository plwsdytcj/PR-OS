const state = {
  tenant: localStorage.getItem("pr_ai_os_tenant") || "default",
  accessKey: localStorage.getItem("pr_ai_os_access_key") || "",
  sessionToken: localStorage.getItem("pr_ai_os_session_token") || "",
  sidebarCollapsed: localStorage.getItem("pr_ai_os_sidebar_collapsed") === "1",
  authRequired: false,
  currentIdentity: null,
  workspaceHistory: [],
  historySummary: {},
  historyFilter: "all",
  historyLoaded: false,
  historyLoading: false,
  activeView: "workspace",
  authUsers: [],
  authClients: [],
  projectAccess: [],
  ruleConfig: null,
  agentTasks: [],
  agentThreads: [],
  activeAgentThread: null,
  activeAgentRun: null,
  activeAgentArtifacts: [],
  activeAgentSteps: [],
  activeArtifactDetail: null,
  activeAgentGraphNodeId: "",
  activeAgentToolName: "",
  agentFloatOpen: localStorage.getItem("pr_ai_os_agent_float_open") === "1",
  agentFloatFrame: loadAgentFloatFrame(),
  agentPollTimer: null,
  agentEventSource: null,
  agentRuntime: null,
  agentRuntimeComparison: null,
  openClaw: null,
  openClawDiagnostics: null,
  openClawMe: null,
  activeOpenClawRun: null,
  openClawSessions: loadOpenClawSessions(),
  activeOpenClawSessionId: localStorage.getItem("pr_ai_os_openclaw_active_session") || "",
  openClawConversation: [],
  activeOpenClawCampaignTarget: null,
  activeAgentImportPreview: null,
  openClawEventSource: null,
  openClawPollTimer: null,
  knowledgeDocuments: [],
  knowledgeStats: null,
  knowledgeSearchResults: [],
  clientPortalProjects: [],
  creators: [],
  creatorsFetchAttempted: false,
  creatorFilterTags: {},
  creatorFilterStep: 1,
  creatorFilterSelected: {},
  creatorFilterRecommendations: {},
  creatorFilterNarrativeAnalysis: null,
  creatorFilterBusinessType: null,
  creatorFilterDeliverables: null,
  settlementWizardCreators: [],
  cases: [],
  activeCase: null,
  lastProposal: "",
  lastBrand: null,
  lastSymbolicResults: [],
  lastNarratives: [],
  lastCreatorSymbolic: null,
  lastSymbolicGraph: null,
  lastSimulationReport: null,
  importFile: null,
  importReview: null,
  importTemplates: [],
  duplicateCandidates: [],
  qualityIssues: [],
  activeCreator: null,
  activeCreatorEvidenceTags: [],
  activeCreatorImageSuggestion: null,
  quickCreatorEvidenceTags: [],
  quickCreatorImageSuggestion: null,
  quickCreatorPendingAssets: [],
  quickCreatorAiPreview: null,
  collabProposals: [],
  activeProposal: null,
  activeClientShare: null,
  commercialInvitations: [],
  commercialSubmissions: [],
  activeCreatorInvite: null,
  distributionBriefs: [],
  activeDistribution: null,
  activeCreatorBrief: null,
  platformDashboard: null,
  platformCampaigns: [],
  activePlatformCampaign: null,
  activeCampaignRoom: null,
  dataSources: [],
  symbolicOS: null,
  kolIntelligence: null,
  phase8Prediction: null,
  phase8ReviewQueue: [],
  phase8SelectedTagIds: new Set(),
  phase82Conversation: null,
  phase82Messages: [],
  phase82ActiveFrame: 0,
  phase82FrameTimer: null,
  kolIntakeResult: null,
  homeBriefConversation: null,
  homeBriefShare: null,
  projectRun: null,
  projectRunSelectedNodeId: "",
  projectRunStageFilter: "",
  projectRunProgressTimer: null,
  projectRunGraphScale: 1,
  projectRunGraphAutoFit: true,
  projectRunGraphDrag: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const PLATFORM_OPTIONS = [
  "抖音",
  "快手",
  "小红书",
  "B站",
  "微博",
  "视频号",
  "微信公众号",
  "知乎",
  "豆瓣",
  "今日头条",
  "推特",
];

function normalizePlatformValue(value) {
  const text = String(value || "").trim();
  if (!text || text === "未知") return PLATFORM_OPTIONS[0];
  if (text === "公众号" || text === "微信") return "微信公众号";
  if (text.toLowerCase() === "twitter" || text === "Twitter" || text === "X") return "推特";
  return PLATFORM_OPTIONS.includes(text) ? text : text;
}

function renderPlatformSelectOptions(select, selected = "") {
  if (!select) return;
  const value = normalizePlatformValue(selected || select.value || PLATFORM_OPTIONS[0]);
  select.innerHTML = PLATFORM_OPTIONS.map(
    (platform) => `<option${platform === value ? " selected" : ""}>${escapeHTML(platform)}</option>`,
  ).join("");
}

function initPlatformSelects() {
  $$('select[name="platform"]').forEach((select) => renderPlatformSelectOptions(select, select.value));
  initCreatorFilterForm();
}

function initCreatorFilterForm() {
  const select = $("#creatorFilterPlatform");
  if (!select) return;
  const current = select.value;
  select.innerHTML =
    '<option value="">全部平台</option>' +
    PLATFORM_OPTIONS.map((platform) => `<option value="${escapeHTML(platform)}">${escapeHTML(platform)}</option>`).join("");
  if (current) select.value = current;
}

const QUICK_CREATOR_TAG_PRESETS = {
  cooperation_brands: ["腾讯", "华为", "美团", "minimax", "爱奇艺", "字节跳动", "网易", "万里汇"],
  industry_fit_tags: ["科技互联网", "电影", "AI产业", "公关", "游戏", "消费", "法律", "新闻"],
  identity_tags: ["记者", "影评人", "科技博主", "行业专家", "专栏作者", "创作者", "公关", "网红"],
  content_capability_tags: ["深度稿", "观点文", "快评", "专访", "影评", "人物稿", "案例拆解", "科普解释"],
  cooperation_formats: ["约稿", "代发", "原创发", "转发", "专栏", "合集", "圆桌", "访谈"],
  suitable_goals: ["技术解释者", "高知信任入口", "圈层扩散", "品牌故事转译", "议题引爆", "专业背书", "搜索沉淀", "风险缓冲"],
  risk_tags: ["拖稿", "观点强", "争议大", "报价波动", "审核风险", "需提前确认立场", "商业痕迹敏感", "不适合硬广"],
  manual_notes: ["出稿慢", "内容精品", "响应快", "需提前沟通", "适合深稿", "报价需核实", "配合度高", "需人工复核"],
  delivery_tags: ["出稿快", "出稿慢", "内容精品", "沟通顺畅", "需要催", "容易改稿", "配合度高", "响应快"],
  budget_fit_tags: ["适合高预算", "适合中预算", "适合低预算", "报价稳定", "报价浮动"],
};

const PLATFORM_RATE_FIELDS = {
  知乎: [
    { key: "rate_repost", label: "代发报价" },
    { key: "rate_original", label: "原创发报价", primary: true },
  ],
  抖音: [
    { key: "rate_60s", label: "60秒以内报价" },
    { key: "rate_120s", label: "120秒以内报价" },
    { key: "rate_long", label: "长视频报价", primary: true },
  ],
  微博: [
    { key: "rate_repost", label: "转发报价" },
    { key: "rate_original", label: "原创发布报价", primary: true },
  ],
  微信公众号: [
    { key: "rate_headline", label: "头条报价", primary: true },
    { key: "rate_second", label: "次条报价" },
    { key: "rate_other", label: "其他报价" },
  ],
  豆瓣: [
    { key: "rate_short", label: "短评打分报价" },
    { key: "rate_long_review", label: "长评报价", primary: true },
  ],
  小红书: [
    { key: "rate_note", label: "笔记报价", primary: true },
    { key: "rate_video", label: "视频报价" },
  ],
  今日头条: [
    { key: "rate_micro", label: "微头条报价" },
    { key: "rate_article", label: "图文报价", primary: true },
  ],
  视频号: [
    { key: "rate_60s", label: "60秒以内报价" },
    { key: "rate_120s", label: "120秒以内报价", primary: true },
  ],
  推特: [
    { key: "rate_quote", label: "quote转发报价" },
    { key: "rate_thread", label: "thread讨论报价" },
    { key: "rate_original", label: "原创发布报价", primary: true },
    { key: "rate_article", label: "推特文章报价" },
  ],
};

const DEFAULT_PLATFORM_RATE_FIELDS = [{ key: "rate_base", label: "基础报价", primary: true }];

const LIKE_FAN_RATIO_PLATFORMS = new Set(["抖音", "小红书", "知乎", "微博"]);

const PLATFORM_DATA_CARD_HINTS = {
  抖音: "抖音重点看视频完播、转发和评论，适合用粉丝量、互动率与赞粉比做扩散判断。",
  小红书: "小红书可看总获赞/收藏与互动率，赞粉比偏高通常代表内容获赞与沉淀更强。",
  知乎: "知乎重专业内容与赞同积累，赞粉比用于区分单粉认可度高低的答主。",
  微博: "微博看粉丝规模与总获赞，赞粉比可区分舆论声量型与涨粉型账号。",
  default: "粉丝、互动和内容表现，用来做预算和平台适配判断。",
};

function computeLikeFanRatio(followerCount, totalLikes) {
  const followers = Number(followerCount || 0);
  const likes = Number(totalLikes || 0);
  if (!followers || followers <= 0 || !likes) return null;
  return likes / followers;
}

function formatLikeFanRatio(value) {
  if (value == null || Number.isNaN(value)) return "—";
  if (value >= 100) return value.toFixed(1);
  if (value >= 10) return value.toFixed(2);
  return value.toFixed(3);
}

function likeFanRatioInsight(value) {
  if (value == null || Number.isNaN(value)) return "填写粉丝数与总获赞后自动计算：赞粉比 = 总获赞 ÷ 粉丝数。";
  if (value >= 50) return "赞粉比偏高：历史获赞相对粉丝更丰满，偏内容获赞 / 沉淀型。";
  if (value >= 10) return "赞粉比中等：获赞与粉丝规模较均衡，可结合互动率一起看。";
  return "赞粉比偏低：粉丝规模相对获赞更大，偏涨粉 / 扩散型。";
}

function supportsLikeFanRatio(platform) {
  return LIKE_FAN_RATIO_PLATFORMS.has(normalizePlatformValue(platform));
}

function syncCreatorDataCardPanel(form) {
  if (!form) return;
  const platform = normalizePlatformValue(form.elements.platform?.value);
  const hint = form.querySelector("[data-data-card-hint]");
  if (hint) hint.textContent = PLATFORM_DATA_CARD_HINTS[platform] || PLATFORM_DATA_CARD_HINTS.default;
  const panel = form.querySelector("[data-like-fan-ratio-panel]");
  const valueNode = form.querySelector("[data-like-fan-ratio-value]");
  const insightNode = form.querySelector("[data-like-fan-ratio-insight]");
  const hidden = form.elements.like_fan_ratio;
  const supported = supportsLikeFanRatio(platform);
  if (panel) panel.classList.toggle("hidden", !supported);
  if (!supported) {
    if (hidden) hidden.value = "";
    return;
  }
  const ratio = computeLikeFanRatio(form.elements.follower_count?.value, form.elements.total_likes?.value);
  if (valueNode) valueNode.textContent = formatLikeFanRatio(ratio);
  if (insightNode) insightNode.textContent = likeFanRatioInsight(ratio);
  if (hidden) hidden.value = ratio == null ? "" : String(Number(ratio.toFixed(4)));
}

function bindCreatorDataCardEvents(form) {
  if (!form || form.dataset.dataCardBound === "true") return;
  form.dataset.dataCardBound = "true";
  form.addEventListener("input", (event) => {
    if (["follower_count", "total_likes"].includes(event.target.name)) syncCreatorDataCardPanel(form);
  });
}

const QUICK_CREATOR_RECENT_TAGS_KEY = "pr_os_quick_creator_recent_tags";
const PERSONAL_TAG_RECENT_KEY = "pr_os_personal_tags_recent";

const PERSONAL_TAG_PRESETS = [
  "电影",
  "公关",
  "出稿慢",
  "内容精品",
  "科技互联网",
  "AI产业",
  "记者",
  "影评人",
  "科技博主",
  "深度稿",
  "观点强",
  "争议大",
  "知乎科技",
  "配合度高",
  "技术解释者",
  "圈层扩散",
  "网易",
  "腾讯",
];

const TAG_FRAMEWORK_ROWS = [
  { field: "industry_fit_tags", label: "领域", hint: "电影、科技互联网、AI产业、游戏、消费…", essential: true },
  { field: "identity_tags", label: "身份", hint: "记者、影评人、科技博主、行业专家…", essential: true },
  { field: "content_capability_tags", label: "内容能力", hint: "深度稿、专访、快评、测评、种草…", essential: true },
  { field: "delivery_tags", label: "履约", hint: "出稿慢、内容精品、配合度高、需要催…", essential: false },
  { field: "risk_tags", label: "风险", hint: "观点强、争议大、审核风险、报价波动…", essential: false },
  { field: "budget_fit_tags", label: "商业判断", hint: "适合高/中/低预算、报价稳定或浮动…", essential: false },
];

const TAG_NARRATIVE_FRAMEWORK_ROW = {
  field: "suitable_goals",
  label: "叙事角色",
  hint: "技术解释者、圈层扩散、专业背书、品牌故事转译…",
  essential: false,
};

/** 录入与筛选共用：类内 OR、类间 AND。fields 支持多字段（如商业 = budget + 合作品牌） */
const CREATOR_TAG_FILTER_GROUPS = [
  { id: "industry", label: "领域", fields: ["industry_fit_tags"], essential: true },
  { id: "identity", label: "身份", fields: ["identity_tags"], essential: true },
  { id: "capability", label: "内容能力", fields: ["content_capability_tags"], essential: true },
  { id: "commercial", label: "商业", fields: ["budget_fit_tags", "cooperation_brands"], essential: false },
  { id: "delivery", label: "履约", fields: ["delivery_tags"], essential: false },
  { id: "risk", label: "风险", fields: ["risk_tags"], essential: false },
  { id: "narrative", label: "叙事角色", fields: ["suitable_goals"], essential: false },
];

const CREATOR_FILTER_PRESETS_KEY = "pr_os_creator_filter_presets";

const BUILTIN_CREATOR_FILTER_PRESETS = [
  {
    id: "builtin_two_stage_propagation",
    name: "二段传播模式",
    builtin: true,
    snapshot: {
      step: 2,
      platform: "",
      query: "",
      sort: "avg_likes_desc",
      min_like_fan_ratio: "3",
      min_recent_posts_count: "10",
      min_avg_likes: "",
      narrative_brief: "",
      text_tags: "专业解释, 深度测评, 行业背书",
      tags: {
        identity: ["行业专家", "科技博主", "记者"],
        capability: ["测评", "科普解释", "深度稿"],
        narrative: ["专业背书", "技术解释者", "品牌故事转译", "高知信任入口"],
      },
    },
  },
];

const CREATOR_NARRATIVE_FILTER_GROUP_IDS = ["industry", "identity", "capability", "narrative"];
const CREATOR_EXTRA_FILTER_GROUP_IDS = ["commercial", "delivery", "risk"];

function appBasePath() {
  const path = window.location.pathname || "";
  if (path === "/pr-os" || path.startsWith("/pr-os/")) return "/pr-os";
  return "";
}

function creatorKitShareUrl(creatorId) {
  const id = String(creatorId || "").trim();
  if (!id) return "";
  return new URL(`/creator-kit/${encodeURIComponent(id)}`, window.location.origin).href;
}

function buildCreatorKitStandalonePage({ cardHtml, title, meta, shareUrl = "" }) {
  const cssHref = `${window.location.origin}/static/creator-kit-standalone.css?v=${window.prOsBuildVersion()}`;
  const safeTitle = String(title || "达人").replace(/[\\/:*?"<>|\\s]+/g, "_");
  const toolbar = `
    <div class="creator-kit-toolbar">
      ${shareUrl ? `<button class="secondary" type="button" id="copyShareBtn">复制网页链接</button>` : ""}
      <button class="primary" type="button" id="downloadPdfBtn">下载 PDF</button>
    </div>`;
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHTML(title || "商业名片刊例")}</title>
  <link rel="stylesheet" href="${cssHref}" />
</head>
<body>
  <main class="creator-kit-page">
    <header class="creator-kit-page-head">
      <div class="card-kicker">PR-OS · business rate card</div>
      <h1>${escapeHTML(title || "商业名片刊例")}</h1>
      ${meta ? `<p class="meta">${escapeHTML(meta)}</p>` : ""}
    </header>
    ${toolbar}
    <div class="commercial-kit-output">${cardHtml}</div>
  </main>
  <script>
    const shareUrl = ${JSON.stringify(shareUrl)};
    const pdfName = ${JSON.stringify(`${safeTitle}_商业名片刊例.pdf`)};
    document.getElementById("copyShareBtn")?.addEventListener("click", async () => {
      const btn = document.getElementById("copyShareBtn");
      try {
        await navigator.clipboard.writeText(shareUrl);
        if (btn) btn.textContent = "已复制";
      } catch {
        alert(shareUrl);
      }
    });
    document.getElementById("downloadPdfBtn")?.addEventListener("click", async () => {
      const card = document.querySelector(".creator-commercial-card");
      if (!card) return;
      if (!window.html2pdf) {
        await new Promise((resolve, reject) => {
          const script = document.createElement("script");
          script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js";
          script.onload = resolve;
          script.onerror = reject;
          document.head.appendChild(script);
        });
      }
      await window.html2pdf()
        .set({
          margin: [10, 10, 10, 10],
          filename: pdfName,
          image: { type: "jpeg", quality: 0.95 },
          html2canvas: { scale: 2, useCORS: true },
          jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        })
        .from(card)
        .save();
    });
  </script>
</body>
</html>`;
}

function openCreatorKitPreviewBlob(card, creator, shareUrl = "") {
  const title = `${creator?.name || "达人"} · 商业名片刊例`;
  const meta = [creator?.platform, creator?.follower_count ? `${fmtNumber(creator.follower_count)} 粉丝` : ""]
    .filter(Boolean)
    .join(" · ");
  const html = buildCreatorKitStandalonePage({ cardHtml: card.outerHTML, title, meta, shareUrl });
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, "_blank", "noopener,noreferrer");
  if (!win) {
    toast("请允许弹窗后重试", true);
    return;
  }
  setTimeout(() => URL.revokeObjectURL(url), 120000);
}

async function loadHtml2PdfLib() {
  if (window.html2pdf) return window.html2pdf;
  await new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js";
    script.onload = resolve;
    script.onerror = () => reject(new Error("PDF 组件加载失败"));
    document.head.appendChild(script);
  });
  return window.html2pdf;
}

async function readCreatorFilterUploadFile(input) {
  const file = input?.files?.[0];
  if (!file) return "";
  const text = await file.text();
  return String(text || "").trim();
}

function getCreatorFilterNarrativeBriefText() {
  return String($("#creatorFilterNarrativeBrief")?.value || $("#creatorFilterBriefInput")?.value || "").trim();
}

function getCreatorFilterTextTagsValue() {
  return String($("#creatorFilterTextTags")?.value || "").trim();
}

const SYMBOLIC_EDITOR_FIELDS = {
  creator: [
    ["primary_tags", "主标签", "tags"],
    ["secondary_tags", "副标签", "tags"],
    ["common_metaphors", "常见隐喻", "tags"],
    ["common_metonymies", "常见转喻", "tags"],
    ["suitable_brand_types", "适合品牌类型", "tags"],
    ["unsuitable_brand_types", "不适合品牌类型", "tags"],
    ["risk_tags", "风险标签", "tags"],
    ["persona_structure", "人设结构", "text"],
    ["emotional_tone", "情绪基调", "textarea"],
    ["narrative_style", "叙事风格", "textarea"],
    ["audience_fantasy", "受众幻想", "textarea"],
    ["manual_status", "审核状态", "text"],
  ],
  brand: [
    ["current_tags", "当前标签", "tags"],
    ["target_tags", "目标标签", "tags"],
    ["danger_tags", "危险标签", "tags"],
    ["emotional_value", "情绪价值", "tags"],
    ["identity_value", "身份价值", "tags"],
    ["product_metaphors", "产品隐喻", "tags"],
    ["product_metonymies", "产品转喻", "tags"],
    ["suitable_social_issues", "适合议题", "tags"],
    ["unsafe_social_issues", "不安全议题", "tags"],
    ["suitable_creator_types", "适合博主类型", "tags"],
    ["communication_path", "传播路径", "textarea"],
  ],
};

const VIEW_TITLES = {
  workspace: ["工作台", "从达人库到 Campaign OS 的五段式闭环。"],
  agentWorkspace: ["AI Agent", "让 PR 项目经理 Agent 调用工具、生成过程日志和交付产物。"],
  knowledge: ["知识库", "把公司案例、客户偏好、风险规则和方案模板变成 Agent 可检索的 RAG 记忆。"],
  history: ["Campaign 资产", "统一查看 Campaign、Agent 会话、方案版本和 Brief 分发记录。"],
  projectRun: ["新建 PR 项目", "输入一个需求，自动跑完 brief、符号图谱、KOL 选择和 Campaign Room。"],
  ingest: ["数据接入", "把 Excel、链接和 API 变成统一 KOL Profile。"],
  creators: ["达人库", "扫描、修正和调用你的私有 KOL 资产。"],
  creatorFilter: ["筛选达人工具", "平台 → 叙事 → 数据：三步漏斗筛出合作候选。"],
  caseLibrary: ["案例库", "沉淀达人历史合作案例，供 Brief 匹配和方案背书引用。"],
  kolIntelligence: ["KOL 决策图谱", "证据标签、图谱演进和 KOL 预测推荐。"],
  governance: ["数据治理", "清理重复、补齐字段、提高推荐可信度。"],
  brief: ["Brief 推荐", "把甲方需求转成可解释的达人组合。"],
  proposal: ["方案导出", "把推荐结果打包成甲方可读方案。"],
  collaboration: ["客户协作", "让甲方在线查看、反馈和确认名单。"],
  clientPortal: ["甲方方案页", "模拟客户视角的方案确认体验。"],
  creatorCommercial: ["博主商业档案", "邀请博主补充报价、档期和案例。"],
  briefDistribution: ["Brief 分发", "把确认的需求推给博主并收集响应。"],
  platformOS: ["OS 总控台", "管理 Campaign、多方案、推演和投后回流。"],
  organization: ["Admin Console", "管理内部账号、甲方客户、客户成员和项目授权。"],
  dataSources: ["数据源设置", "检查达人 API、LLM、推演引擎和导入能力。"],
  symbolicOS: ["符号 OS", "维护社会符号网络、能指标签库和投后修正。"],
  symbolicCreator: ["博主符号档案", "把内容风格、受众幻想和风险变成标签。"],
  symbolicBrand: ["品牌符号分析", "识别品牌想获得和想避开的传播符号。"],
  symbolicMatch: ["符号匹配", "用符号关系解释品牌和博主为什么适合。"],
  symbolicGraph: ["符号图谱", "把品牌、博主、内容路径和风险连成图。"],
  stressTest: ["压力测试", "投放前模拟评论区、竞品和品牌安全风险。"],
};

const NAV_SHORT_LABELS = {
  workspace: "首",
  projectRun: "PR",
  history: "史",
  kolIntelligence: "KOL",
  creators: "人",
  creatorFilter: "筛",
  caseLibrary: "案",
  agentWorkspace: "AI",
  brief: "B",
  platformOS: "OS",
  symbolicOS: "符",
  ingest: "入",
  knowledge: "知",
  governance: "治",
  creatorCommercial: "商",
  proposal: "案",
  collaboration: "协",
  clientPortal: "甲",
  briefDistribution: "发",
  symbolicCreator: "博",
  symbolicBrand: "牌",
  symbolicMatch: "配",
  symbolicGraph: "图",
  stressTest: "测",
  organization: "组",
  dataSources: "源",
};

const PROJECT_RUN_DEMO_VALUES = {
  client_name: "某新能源汽车品牌",
  project_name: "新能源 SUV 年轻化预热",
  brief:
    "预算50万，新能源SUV新品上市预热，目标用户是25-40岁一二线城市年轻家庭和科技兴趣人群。希望突出科技感、智能化、高端感和城市生活方式。平台优先抖音、小红书、B站，需要选择合适KOL并做投放前风险推演。",
  top_n: "8",
};

const PROJECT_RUN_RANDOM_BRIEFS = [
  {
    client_name: "新锐国货美妆品牌",
    project_name: "修护精华新品种草",
    brief:
      "预算30万，主推一款屏障修护精华，目标用户是22-32岁敏感肌、熬夜党和成分党。希望突出温和修护、真实使用前后对比、国货科研感。平台优先小红书、抖音，需要选择适合种草和测评的KOL，并规避夸大功效、医美擦边和虚假对比风险。",
    top_n: "8",
  },
  {
    client_name: "独立咖啡连锁品牌",
    project_name: "城市快闪店开业传播",
    brief:
      "预算18万，上海新店开业和周末快闪活动，目标用户是20-35岁城市白领、咖啡爱好者和生活方式人群。希望突出城市松弛感、社交打卡、限定菜单和好拍空间。平台优先小红书、抖音，需要推荐探店、摄影、生活方式KOL，并评估排队体验和价格争议风险。",
    top_n: "6",
  },
  {
    client_name: "二次元手游发行团队",
    project_name: "新角色上线预热",
    brief:
      "预算45万，手游新角色上线预热，目标用户是18-28岁二次元、剧情党、抽卡玩家。希望突出角色人设、世界观、声优和二创潜力。平台优先B站、抖音、小红书，需要选择游戏解说、剧情分析、画师和coser类KOL，并提前推演抽卡争议、角色强度争议和饭圈化风险。",
    top_n: "10",
  },
  {
    client_name: "高端宠物食品品牌",
    project_name: "冻干新品信任背书",
    brief:
      "预算25万，推出猫狗冻干新品，目标用户是25-40岁一二线养宠人群。希望突出配方安全、适口性、营养透明和真实喂养反馈。平台优先小红书、抖音、视频号，需要推荐养宠知识、宠物日常和兽医科普类KOL，并规避宠物健康承诺和竞品拉踩风险。",
    top_n: "8",
  },
  {
    client_name: "企业 AI SaaS 公司",
    project_name: "销售 Copilot 行业方案发布",
    brief:
      "预算60万，发布面向制造业和消费品企业的销售 Copilot 方案，目标用户是CEO、销售VP、数字化负责人。希望突出降本增效、CRM集成、销售知识库和可控AI。平台优先公众号、视频号、B站、知乎，需要推荐企业服务、AI转型和管理咨询类KOL，并说明技术可信度、数据安全和ROI夸大风险。",
    top_n: "8",
  },
  {
    client_name: "户外运动生活方式品牌",
    project_name: "轻量徒步鞋春季种草",
    brief:
      "预算35万，推广轻量徒步鞋春季新品，目标用户是24-38岁城市户外、周末徒步和露营人群。希望突出舒适、轻量、防滑、城市到山野的穿搭场景。平台优先小红书、抖音、B站，需要推荐户外、穿搭、旅行和测评KOL，并规避功能参数夸大和专业户外安全风险。",
    top_n: "8",
  },
];

function toast(message, isError = false) {
  const node = $("#toast");
  node.textContent = message;
  node.style.background = isError ? "#9f1239" : "#101820";
  node.classList.add("show");
  setTimeout(() => node.classList.remove("show"), 2600);
}

function normalizeTenant(value) {
  return String(value || "default")
    .trim()
    .replace(/[^a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48)
    .toLowerCase() || "default";
}

function renderTenantStatus(tenant = state.tenant) {
  const input = $("#tenantInput");
  const accessKeyInput = $("#accessKeyInput");
  const status = $("#tenantStatus");
  if (input) input.value = tenant || "default";
  if (accessKeyInput) accessKeyInput.value = state.accessKey || "";
  if (status) status.textContent = tenant || "default";
}

function showAccessGate(message = "") {
  const gate = $("#accessGate");
  if (!gate) return;
  $("#serverStatus").textContent = "需要登录";
  gate.classList.remove("hidden");
  if ($("#gateAccessKeyInput")) $("#gateAccessKeyInput").value = state.accessKey || "";
  const title = gate.querySelector("p");
  if (title && message) title.textContent = message === "login required" ? "请用内部或甲方账号登录后继续使用。" : message;
}

function hideAccessGate() {
  $("#accessGate")?.classList.add("hidden");
}

function loadAgentFloatFrame() {
  try {
    const frame = JSON.parse(localStorage.getItem("pr_ai_os_agent_float_frame") || "null");
    if (!frame || typeof frame !== "object") return null;
    return {
      left: Number(frame.left) || 0,
      top: Number(frame.top) || 0,
      width: Number(frame.width) || 0,
      height: Number(frame.height) || 0,
    };
  } catch {
    return null;
  }
}

function clampAgentFloatFrame(frame) {
  const minWidth = 560;
  const minHeight = 460;
  const margin = 16;
  const maxWidth = Math.max(minWidth, window.innerWidth - margin * 2);
  const maxHeight = Math.max(minHeight, window.innerHeight - margin * 2);
  const width = Math.min(Math.max(Number(frame?.width) || 880, minWidth), maxWidth);
  const height = Math.min(Math.max(Number(frame?.height) || 680, minHeight), maxHeight);
  const left = Math.min(Math.max(Number(frame?.left) || window.innerWidth - width - 22, margin), window.innerWidth - width - margin);
  const top = Math.min(Math.max(Number(frame?.top) || window.innerHeight - height - 22, margin), window.innerHeight - height - margin);
  return { left, top, width, height };
}

function saveAgentFloatFrame(frame) {
  state.agentFloatFrame = clampAgentFloatFrame(frame);
  localStorage.setItem("pr_ai_os_agent_float_frame", JSON.stringify(state.agentFloatFrame));
  applyAgentFloatFrame();
}

function applyAgentFloatFrame() {
  const dock = $("#agentFloatDock");
  const panel = $("#agentFloatPanel");
  if (!dock || !panel) return;
  if (window.innerWidth <= 760 || !state.agentFloatFrame) {
    dock.classList.remove("agent-float-custom-frame");
    dock.style.removeProperty("--agent-float-left");
    dock.style.removeProperty("--agent-float-top");
    panel.style.removeProperty("--agent-float-width");
    panel.style.removeProperty("--agent-float-height");
    return;
  }
  const frame = clampAgentFloatFrame(state.agentFloatFrame);
  state.agentFloatFrame = frame;
  dock.classList.add("agent-float-custom-frame");
  dock.style.setProperty("--agent-float-left", `${frame.left}px`);
  dock.style.setProperty("--agent-float-top", `${frame.top}px`);
  panel.style.setProperty("--agent-float-width", `${frame.width}px`);
  panel.style.setProperty("--agent-float-height", `${frame.height}px`);
}

function frameFromFloatElement(element) {
  const rect = element.getBoundingClientRect();
  const existing = state.agentFloatFrame || {};
  return clampAgentFloatFrame({
    left: rect.left,
    top: rect.top,
    width: existing.width || 880,
    height: existing.height || 680,
  });
}

function persistAuthSession(session) {
  const token = String(session?.session_id || "").trim();
  if (!token) return;
  state.sessionToken = token;
  localStorage.setItem("pr_ai_os_session_token", token);
}

function clearAuthSession() {
  state.sessionToken = "";
  localStorage.removeItem("pr_ai_os_session_token");
}

function syncAppBuildVersionInUrl() {
  const version = window.prOsBuildVersion();
  const query = new URLSearchParams(window.location.search);
  if (query.get("v") === version) return;
  query.set("v", version);
  const next = `${window.location.pathname}?${query.toString()}${window.location.hash}`;
  window.history.replaceState({}, document.title, next);
}

function hydrateAuthSessionFromLocation() {
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const query = new URLSearchParams(window.location.search);
  const token = String(hash.get("session") || query.get("session") || "").trim();
  if (!token) return;
  persistAuthSession({ session_id: token });
  const version = window.prOsBuildVersion();
  const cleanUrl = `${window.location.pathname}?v=${encodeURIComponent(version)}`;
  window.history.replaceState({}, document.title, cleanUrl);
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("X-Tenant-ID", state.tenant || "default");
  if (state.accessKey) headers.set("X-Access-Key", state.accessKey);
  if (state.sessionToken) headers.set("X-Session-Token", state.sessionToken);
  const response = await fetch(path, { ...options, headers, credentials: "include" });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      const authPath = String(path).startsWith("/api/auth/");
      if (!authPath && state.sessionToken) clearAuthSession();
      if (!authPath) showAccessGate(data.detail || "login required");
      throw new Error(data.detail === "login required" ? "需要登录" : data.detail || "需要登录");
    }
    throw new Error(data.detail || `请求失败：${response.status}`);
  }
  return data;
}

function isAuthBlocked() {
  return state.authRequired && !state.currentIdentity?.user && !state.accessKey && !state.sessionToken;
}

function resolveCreatorIdFromClick(event) {
  if (event.target.closest("a[href]")) return "";
  const target = event.target.closest(".open-creator-btn, .open-creator-card, [data-creator-id]");
  if (!target) return "";
  return String(target.dataset.creatorId || "").trim();
}

async function handleCreatorOpenClick(event) {
  const creatorId = resolveCreatorIdFromClick(event);
  if (!creatorId) return;
  event.preventDefault();
  event.stopPropagation();
  try {
    await openCreatorModal(creatorId);
  } catch (error) {
    toast(error.message || "打不开达人详情", true);
  }
}

async function apiWithTimeout(path, options = {}, timeoutMs = 20000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await api(path, { ...options, signal: controller.signal });
  } catch (error) {
    if (error?.name === "AbortError") throw new Error("请求超时，请稍后重试");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function fmtNumber(value) {
  if (value === null || value === undefined || value === "") return "-";
  const n = Number(value);
  return Number.isFinite(n) ? n.toLocaleString("zh-CN") : "-";
}

function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function loadOpenClawSessions() {
  try {
    const raw = JSON.parse(localStorage.getItem("pr_ai_os_openclaw_sessions") || "[]");
    if (!Array.isArray(raw)) return [];
    return raw
      .filter((item) => item && item.id)
      .map((item) => ({
        id: String(item.id),
        title: String(item.title || "新对话"),
        status: String(item.status || "ready"),
        openclawSessionId: String(item.openclawSessionId || ""),
        conversation: Array.isArray(item.conversation) ? item.conversation : [],
        activeRun: item.activeRun || null,
        importPreview: item.importPreview || null,
        createdAt: item.createdAt || new Date().toISOString(),
        updatedAt: item.updatedAt || item.createdAt || new Date().toISOString(),
      }))
      .slice(0, 20);
  } catch {
    return [];
  }
}

function normalizeOpenClawSession(item) {
  const sessionId = item?.session_id || item?.id || "";
  if (!sessionId) return null;
  return {
    id: String(sessionId),
    title: String(item.title || "新对话"),
    status: String(item.status || "ready"),
    openclawSessionId: String(item.openclaw_session_id || item.openclawSessionId || ""),
    conversation: Array.isArray(item.conversation) ? item.conversation : [],
    activeRun: item.activeRun || null,
    importPreview: item.importPreview || null,
    createdAt: item.created_at || item.createdAt || new Date().toISOString(),
    updatedAt: item.updated_at || item.updatedAt || item.created_at || item.createdAt || new Date().toISOString(),
  };
}

async function loadOpenClawSessionsFromServer() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  const data = await api("/api/openclaw/sessions").catch(() => null);
  if (!data) return;
  const localById = new Map((state.openClawSessions || []).map((session) => [session.id, session]));
  const sessions = (data.items || [])
    .map(normalizeOpenClawSession)
    .filter(Boolean)
    .map((session) => ({ ...session, importPreview: localById.get(session.id)?.importPreview || session.importPreview || null }));
  state.openClawSessions = sessions;
  if (!sessions.some((session) => session.id === state.activeOpenClawSessionId)) {
    state.activeOpenClawSessionId = sessions[0]?.id || "";
    state.openClawConversation = [];
    state.activeOpenClawRun = null;
  }
  saveOpenClawSessions();
  renderOpenClawSessionList();
}

function openClawConversationFromDetail(detail) {
  const runs = detail?.runs || [];
  const eventsByRun = detail?.events_by_run || {};
  return runs.map((run) => {
    const events = eventsByRun[run.run_id] || [];
    return {
      runId: run.run_id,
      user: stripOpenClawDisplayMessage(run.message || ""),
      assistant: run.response || run.error ? formatOpenClawChatResponse(run.response || run.error) : "",
      status: run.status || "running",
      eventCount: events.length,
      pending: false,
    };
  });
}

function activeRunFromSessionDetail(detail) {
  const runs = detail?.runs || [];
  const last = runs[runs.length - 1];
  if (!last) return null;
  return { run: last, events: (detail?.events_by_run || {})[last.run_id] || [] };
}

async function loadOpenClawSessionDetail(sessionId) {
  const detail = await api(`/api/openclaw/sessions/${encodeURIComponent(sessionId)}`);
  const session = normalizeOpenClawSession(detail.session || {});
  if (!session) return null;
  session.conversation = openClawConversationFromDetail(detail);
  session.activeRun = activeRunFromSessionDetail(detail);
  session.importPreview = state.openClawSessions.find((item) => item.id === session.id)?.importPreview || null;
  const index = state.openClawSessions.findIndex((item) => item.id === session.id);
  if (index >= 0) state.openClawSessions[index] = { ...state.openClawSessions[index], ...session };
  else state.openClawSessions.unshift(session);
  saveOpenClawSessions();
  return session;
}

function saveOpenClawSessions() {
  localStorage.setItem("pr_ai_os_openclaw_sessions", JSON.stringify((state.openClawSessions || []).slice(0, 20)));
  localStorage.setItem("pr_ai_os_openclaw_active_session", state.activeOpenClawSessionId || "");
}

function openClawSessionId() {
  return `openclaw_chat_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

function openClawSessionTitleFromText(text) {
  const value = String(text || "").replace(/\s+/g, " ").trim();
  return value ? value.slice(0, 24) : "新对话";
}

function ensureOpenClawSession() {
  let session = (state.openClawSessions || []).find((item) => item.id === state.activeOpenClawSessionId);
  if (!session) {
    session = {
      id: openClawSessionId(),
      title: "新对话",
      status: "ready",
      openclawSessionId: "",
      conversation: [],
      activeRun: null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    state.openClawSessions = [session, ...(state.openClawSessions || [])].slice(0, 20);
    state.activeOpenClawSessionId = session.id;
    state.openClawConversation = [];
    state.activeOpenClawRun = null;
    saveOpenClawSessions();
  } else if (!state.activeOpenClawRun && !(state.openClawConversation || []).length) {
    state.openClawConversation = Array.isArray(session.conversation) ? session.conversation : [];
    state.activeOpenClawRun = session.activeRun || null;
  }
  return session;
}

function syncActiveOpenClawSession(patch = {}) {
  const session = ensureOpenClawSession();
  const run = state.activeOpenClawRun?.run || {};
  if (run.session_id && run.session_id !== session.id) {
    session.id = run.session_id;
  }
  session.conversation = state.openClawConversation || [];
  session.activeRun = state.activeOpenClawRun || null;
  session.importPreview = state.activeAgentImportPreview || null;
  session.status = patch.status || run.status || session.status || "ready";
  session.openclawSessionId = patch.openclawSessionId || run.openclaw_session_id || session.openclawSessionId || "";
  const firstUser = session.conversation.find((item) => item.user)?.user || "";
  if (!session.title || session.title === "新对话") session.title = openClawSessionTitleFromText(firstUser);
  session.updatedAt = new Date().toISOString();
  state.openClawSessions = [session, ...state.openClawSessions.filter((item) => item.id !== session.id)].slice(0, 20);
  state.activeOpenClawSessionId = session.id;
  saveOpenClawSessions();
  renderOpenClawSessionList();
}

async function activateOpenClawSession(sessionId) {
  const session = (state.openClawSessions || []).find((item) => item.id === sessionId);
  if (!session) return;
  stopOpenClawPolling();
  state.activeOpenClawSessionId = session.id;
  state.openClawConversation = Array.isArray(session.conversation) ? session.conversation : [];
  state.activeOpenClawRun = session.activeRun || null;
  state.activeAgentImportPreview = session.importPreview || null;
  state.activeOpenClawCampaignTarget = null;
  saveOpenClawSessions();
  renderAgentFloatDock();
  if (session.activeRun?.run?.status === "running" && session.activeRun?.run?.run_id) startOpenClawPolling(session.activeRun.run.run_id);
  loadOpenClawSessionDetail(sessionId)
    .then((freshSession) => {
      if (!freshSession || state.activeOpenClawSessionId !== sessionId) return;
      state.openClawConversation = Array.isArray(freshSession.conversation) ? freshSession.conversation : [];
      state.activeOpenClawRun = freshSession.activeRun || null;
      state.activeAgentImportPreview = freshSession.importPreview || null;
      saveOpenClawSessions();
      renderAgentFloatDock();
      if (freshSession.activeRun?.run?.status === "running" && freshSession.activeRun?.run?.run_id) startOpenClawPolling(freshSession.activeRun.run.run_id);
    })
    .catch(() => {});
}

function ensureOpenClawSessionShell() {
  const panel = $("#agentFloatPanel");
  const messages = $("#agentFloatMessages");
  if (!panel || !messages) return;
  if ($("#agentFloatSessionList")) return;
  const shell = document.createElement("div");
  shell.className = "agent-float-session-shell";
  const sessions = document.createElement("aside");
  sessions.className = "agent-float-sessions";
  sessions.setAttribute("aria-label", "OpenClaw 对话 Sessions");
  sessions.innerHTML = `
    <div class="agent-float-sessions-head">
      <span>Sessions</span>
    </div>
    <div id="agentFloatSessionList" class="agent-float-session-list"></div>
  `;
  messages.parentNode?.insertBefore(shell, messages);
  shell.appendChild(sessions);
  shell.appendChild(messages);
}

function renderOpenClawSessionList() {
  ensureOpenClawSessionShell();
  const node = $("#agentFloatSessionList");
  if (!node) return;
  ensureOpenClawSession();
  node.innerHTML = (state.openClawSessions || [])
    .map((session) => {
      const active = session.id === state.activeOpenClawSessionId;
      const count = (session.conversation || []).length;
      return `
        <button class="agent-float-session-item ${active ? "active" : ""}" type="button" data-openclaw-session="${escapeHTML(session.id)}">
          <strong>${escapeHTML(session.title || "新对话")}</strong>
          <span>${escapeHTML(session.status || "ready")} · ${fmtNumber(count)} 条</span>
        </button>
      `;
    })
    .join("");
}

function setView(viewId) {
  if (state.currentIdentity?.user?.user_type === "client" && viewId !== "clientPortal") {
    viewId = "clientPortal";
  }
  state.activeView = viewId;
  $$(".view").forEach((node) => node.classList.toggle("active", node.id === viewId));
  $$(".nav-item").forEach((node) => node.classList.toggle("active", node.dataset.view === viewId));
  const activeNav = $(`.nav-item[data-view="${viewId}"]`);
  $$(".nav-group").forEach((group) => {
    group.open = Boolean(activeNav && group.contains(activeNav));
  });
  if (viewId === "history") ensureWorkspaceHistoryLoaded();
  if (viewId === "creators" || viewId === "creatorFilter") ensureCreatorsLoaded().catch(() => {});
  if (viewId === "caseLibrary") {
    ensureCreatorsLoaded().catch(() => {});
    if (!state.cases.length) loadCases().catch(() => {});
    else renderCases();
  }
  renderAgentFloatDock();
}

function applySidebarState() {
  const collapsed = Boolean(state.sidebarCollapsed);
  document.body.classList.toggle("sidebar-collapsed", collapsed);
  $$(".nav-item").forEach((item) => {
    const short = NAV_SHORT_LABELS[item.dataset.view] || (item.textContent || "?").trim().slice(0, 2);
    item.dataset.short = short;
    item.title = item.textContent.trim();
  });
  const button = $("#sidebarToggleBtn");
  if (!button) return;
  button.setAttribute("aria-pressed", collapsed ? "true" : "false");
  button.setAttribute("aria-label", collapsed ? "展开侧边栏" : "折叠侧边栏");
  button.title = collapsed ? "展开侧边栏" : "折叠侧边栏";
  button.textContent = collapsed ? "›" : "‹";
}

function decorateViews() {
  $$(".view").forEach((view) => {
    if (view.querySelector(":scope > .view-poster")) return;
    const meta = VIEW_TITLES[view.id];
    if (!meta || view.id === "workspace" || view.id === "agentWorkspace") return;
    const header = document.createElement("div");
    header.className = "view-poster";
    header.innerHTML = `
      <div>
        <div class="eyebrow">module / ${escapeHTML(view.id)}</div>
        <h2>${escapeHTML(meta[0])}</h2>
        <p>${escapeHTML(meta[1])}</p>
      </div>
      <span>${escapeHTML(String(Object.keys(VIEW_TITLES).indexOf(view.id) + 1).padStart(2, "0"))}</span>
    `;
    view.prepend(header);
  });
}

async function refreshStatus() {
  const status = await api("/api/status");
  $("#serverStatus").textContent = "已连接";
  state.authRequired = Boolean(status.auth_required);
  state.tenant = status.tenant || state.tenant || "default";
  localStorage.setItem("pr_ai_os_tenant", state.tenant);
  renderTenantStatus(state.tenant);
  if (status.auth_required && !state.accessKey && !state.currentIdentity) $("#serverStatus").textContent = "需要登录";
  $("#totalProfiles").textContent = status.total_profiles;
  $("#enrichedProfiles").textContent = status.enriched_profiles;
  $("#connectorCount").textContent = status.connectors.length;
}

async function loadAuthMe() {
  const data = await api("/api/auth/me");
  state.authRequired = Boolean(data.auth_required);
  state.currentIdentity = data.identity || null;
  if (data.authenticated && data.session?.session_id) {
    persistAuthSession(data.session);
  } else if (data.auth_required && !data.authenticated && state.sessionToken) {
    clearAuthSession();
  }
  renderAuthUser();
  return data;
}

function renderAuthUser() {
  const box = $("#authUserBox");
  if (!box) return;
  const user = state.currentIdentity?.user;
  document.body.classList.toggle("client-session", user?.user_type === "client");
  document.body.classList.toggle("internal-session", user?.user_type === "internal");
  renderAgentFloatDock();
  if (!user) {
    document.body.classList.remove("client-session", "internal-session");
    if (state.authRequired) $("#serverStatus").textContent = "需要登录";
    box.innerHTML = `
      <span>未登录</span>
      <button id="authOpenLoginBtn" class="secondary" type="button">登录</button>
    `;
    return;
  }
  $("#serverStatus").textContent = "已连接";
  box.innerHTML = `
    <span>${escapeHTML(user.name || user.email)} · ${escapeHTML(user.role)}</span>
    <button id="authLogoutBtn" class="secondary" type="button">退出</button>
  `;
}

function initCreatorListShell() {
  const list = $("#creatorList");
  if (!list || list.querySelector(".empty-state")) return;
  list.innerHTML = emptyState("正在准备达人库…", "正在连接服务并拉取达人数据。");
  const summary = $("#creatorListSummary");
  if (summary) summary.textContent = "正在准备达人库…";
}

function renderCreatorListAuthRequired() {
  const list = $("#creatorList");
  if (!list) return;
  list.innerHTML = emptyState("请先登录", "登录后可查看、搜索和管理达人库。点击左下角「登录」。");
  const summary = $("#creatorListSummary");
  if (summary) summary.textContent = "登录后加载达人库";
}

async function loadCreators() {
  state.creatorsFetchAttempted = true;
  setCreatorListLoading(true);
  try {
    const data = await api("/api/creators");
    state.creators = data.items || [];
    renderCreators();
    if (state.activeView === "creatorFilter") {
      renderCreatorFilterTagFramework();
      renderCreatorFilterStepper();
      renderCreatorFilterFunnel();
      renderCreatorFilterResults();
    }
    renderCreatorOptions();
    renderCaseCreatorOptions();
  } catch (error) {
    const list = $("#creatorList");
    if (list) {
      list.innerHTML = emptyState("达人库加载失败", error.message || "请检查网络或登录状态后重试。");
    }
    throw error;
  } finally {
    setCreatorListLoading(false);
  }
}

async function ensureCreatorsLoaded() {
  const list = $("#creatorList");
  if (!list) return;
  if (list.dataset.loading === "true") return;
  if (state.authRequired && !state.currentIdentity?.user && !state.accessKey && !state.sessionToken) {
    renderCreatorListAuthRequired();
    return;
  }
  if (state.creatorsFetchAttempted) {
    renderCreators();
    return;
  }
  await loadCreators();
}

async function loadCases() {
  const data = await api("/api/cases");
  state.cases = data.items || [];
  renderCases();
}

function renderCaseCreatorOptions() {
  const select = $("#caseCreatorSelect");
  if (!select) return;
  const current = select.value;
  select.innerHTML =
    '<option value="">选择达人</option>' +
    state.creators.map((creator) => `<option value="${creator.creator_id}">${escapeHTML(creator.name)} · ${escapeHTML(creator.platform)}</option>`).join("");
  if (current) select.value = current;
}

function caseSuccessLabel(value) {
  if (value === "success") return "成功";
  if (value === "partial") return "部分达成";
  if (value === "failed") return "未达预期";
  return "待评估";
}

function caseVisibilityLabel(value) {
  if (value === "public") return "公开";
  if (value === "client_summary") return "客户方案";
  if (value === "internal") return "内部";
  return "公开";
}

function caseDisplayTitle(item) {
  return (item.case_title || item.content_topic || "").trim() || item.brand_name || "合作案例";
}

function caseDisplaySummary(item) {
  return (item.case_summary || item.cooperation_goal || item.comment_feedback || item.reuse_suggestion || "").trim();
}

function emptyCommercialCaseRow() {
  return {
    case_id: "",
    brand_name: "",
    case_title: "",
    case_summary: "",
    content_url: "",
    content_format: "",
    visibility: "public",
    featured_on_kit: true,
  };
}

function commercialCaseRowHtml(caseItem, index, creatorId = "") {
  const featured = caseItem.featured_on_kit !== false;
  const visibility = caseItem.visibility || "public";
  const resolvedCreatorId = creatorId || caseItem.creator_id || "";
  return `
    <article class="commercial-case-row" data-case-index="${index}">
      <input type="hidden" data-field="case_id" value="${escapeHTML(caseItem.case_id || "")}" />
      <p class="meta commercial-case-creator-id">博主 ID：${resolvedCreatorId ? escapeHTML(resolvedCreatorId) : "保存后自动关联"}</p>
      <div class="field-row">
        <input data-field="brand_name" placeholder="合作品牌" value="${escapeHTML(caseItem.brand_name || "")}" />
        <input data-field="case_title" placeholder="案例标题" value="${escapeHTML(caseItem.case_title || caseItem.content_topic || "")}" />
      </div>
      <textarea data-field="case_summary" rows="2" placeholder="案例介绍">${escapeHTML(caseItem.case_summary || caseItem.cooperation_goal || "")}</textarea>
      <div class="field-row">
        <input data-field="content_url" placeholder="案例链接" value="${escapeHTML(caseItem.content_url || "")}" />
        <input data-field="content_format" placeholder="合作形式" value="${escapeHTML(caseItem.content_format || "")}" />
      </div>
      <div class="field-row commercial-case-row-meta">
        <label class="checkline"><input data-field="featured_on_kit" type="checkbox" ${featured ? "checked" : ""} /> 刊例页展示</label>
        <select data-field="visibility">
          <option value="public" ${visibility === "public" ? "selected" : ""}>对外公开</option>
          <option value="client_summary" ${visibility === "client_summary" ? "selected" : ""}>仅客户方案</option>
          <option value="internal" ${visibility === "internal" ? "selected" : ""}>仅内部</option>
        </select>
        <button type="button" class="secondary danger-text" data-remove-commercial-case>删除</button>
      </div>
    </article>
  `;
}

function renderCommercialCasesEditor(form, cases = []) {
  const list = form?.querySelector("[data-commercial-case-list]");
  if (!list) return;
  const rows = Array.isArray(cases) ? cases : [];
  const creatorId = String(form.elements.creator_id?.value || "").trim();
  list.innerHTML = rows.length
    ? rows.map((item, index) => commercialCaseRowHtml(item, index, creatorId)).join("")
    : '<p class="meta commercial-cases-empty">暂无案例，点击「添加案例」录入品牌合作。</p>';
}

async function loadCommercialCasesForCreator(creatorId, form) {
  if (!form) return;
  if (!creatorId) {
    renderCommercialCasesEditor(form, []);
    return;
  }
  try {
    const data = await api(`/api/cases?creator_id=${encodeURIComponent(creatorId)}`);
    renderCommercialCasesEditor(form, data.items || []);
  } catch {
    renderCommercialCasesEditor(form, []);
  }
}

function collectCommercialCasesFromForm(form) {
  const list = form?.querySelector("[data-commercial-case-list]");
  if (!list) return [];
  return [...list.querySelectorAll(".commercial-case-row")]
    .map((row) => {
      const get = (field) => {
        const el = row.querySelector(`[data-field="${field}"]`);
        if (!el) return "";
        if (el.type === "checkbox") return el.checked;
        return String(el.value || "").trim();
      };
      const brand = get("brand_name");
      if (!brand) return null;
      return {
        case_id: get("case_id") || undefined,
        brand_name: brand,
        case_title: get("case_title"),
        case_summary: get("case_summary"),
        content_url: get("content_url"),
        content_format: get("content_format"),
        visibility: get("visibility") || "public",
        featured_on_kit: Boolean(get("featured_on_kit")),
      };
    })
    .filter(Boolean);
}

function bindCommercialCasesEditor(form) {
  if (!form || form.dataset.commercialCasesBound === "true") return;
  form.dataset.commercialCasesBound = "true";
  form.addEventListener("click", (event) => {
    const addBtn = event.target.closest("[data-add-commercial-case-btn]");
    if (addBtn && form.contains(addBtn)) {
      const list = form.querySelector("[data-commercial-case-list]");
      if (!list) return;
      list.querySelector(".commercial-cases-empty")?.remove();
      const index = list.querySelectorAll(".commercial-case-row").length;
      const creatorId = String(form.elements.creator_id?.value || "").trim();
      list.insertAdjacentHTML("beforeend", commercialCaseRowHtml(emptyCommercialCaseRow(), index, creatorId));
      refreshCommercialKitPreview(form);
      return;
    }
    const removeBtn = event.target.closest("[data-remove-commercial-case]");
    if (!removeBtn || !form.contains(removeBtn)) return;
    removeBtn.closest(".commercial-case-row")?.remove();
    const list = form.querySelector("[data-commercial-case-list]");
    if (list && !list.querySelector(".commercial-case-row")) {
      list.innerHTML = '<p class="meta commercial-cases-empty">暂无案例，点击「添加案例」录入品牌合作。</p>';
    }
    refreshCommercialKitPreview(form);
  });
  form.addEventListener("input", (event) => {
    if (!event.target.closest("[data-commercial-case-list]")) return;
    window.clearTimeout(form.__commercialCasesPreviewTimer);
    form.__commercialCasesPreviewTimer = window.setTimeout(() => refreshCommercialKitPreview(form), 220);
  });
  form.addEventListener("change", (event) => {
    if (!event.target.closest("[data-commercial-case-list]")) return;
    refreshCommercialKitPreview(form);
  });
}

function renderCases() {
  const query = ($("#caseSearch")?.value || "").toLowerCase();
  const list = $("#caseList");
  if (!list) return;
  const items = state.cases.filter((item) => {
    const text = [
      item.creator_name,
      item.brand_name,
      item.industry,
      item.product,
      item.platform,
      item.content_format,
      item.content_topic,
      item.cooperation_goal,
      item.comment_feedback,
      item.reuse_suggestion,
      ...(item.active_tags || []),
    ]
      .join(" ")
      .toLowerCase();
    return text.includes(query);
  });
  $("#caseTotalCount").textContent = String(state.cases.length);
  $("#caseBrandCount").textContent = String(new Set(state.cases.map((item) => item.brand_name).filter(Boolean)).size);
  $("#caseCreatorCount").textContent = String(new Set(state.cases.map((item) => item.creator_id).filter(Boolean)).size);
  if (!items.length) {
    list.innerHTML = emptyState("暂无合作案例", "点击「新增案例」录入达人历史合作，或在博主商业档案审核通过后自动沉淀。");
    return;
  }
  list.innerHTML = items
    .map((item) => {
      const tags = [...(item.active_tags || [])]
        .slice(0, 4)
        .map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`)
        .join("");
      const metrics = Object.entries(item.performance || {})
        .filter(([, value]) => value)
        .slice(0, 3)
        .map(([key, value]) => `<span class="meta">${escapeHTML(key)}: ${escapeHTML(String(value))}</span>`)
        .join("");
      const visibility = item.visibility || "public";
      const publicPath = visibility !== "internal" && item.case_id ? `/cases/${encodeURIComponent(item.case_id)}` : "";
      return `
        <article class="case-card">
          <div class="case-card-top">
            <div>
              <div class="card-kicker">${escapeHTML(item.brand_name || item.industry || item.platform || "合作案例")}</div>
              <h3>${escapeHTML(caseDisplayTitle(item))}</h3>
              <div class="meta">${escapeHTML(item.creator_name || "未关联达人")}${item.product ? ` · ${escapeHTML(item.product)}` : ""}</div>
            </div>
            <div class="case-card-badges">
              <span class="case-visibility ${escapeHTML(visibility)}">${escapeHTML(caseVisibilityLabel(visibility))}</span>
              <span class="case-status ${escapeHTML(item.is_successful || "unknown")}">${escapeHTML(caseSuccessLabel(item.is_successful))}</span>
            </div>
          </div>
          <p>${escapeHTML(caseDisplaySummary(item) || item.content_format || "待补充案例说明")}</p>
          <div class="case-card-meta">${metrics}</div>
          <div class="tag-list">${tags}</div>
          ${item.reuse_suggestion ? `<p class="meta case-reuse">复用：${escapeHTML(item.reuse_suggestion)}</p>` : ""}
          <div class="button-row">
            ${item.content_url ? `<a class="text-btn" href="${escapeHTML(item.content_url)}" target="_blank" rel="noreferrer">原内容</a>` : ""}
            ${publicPath ? `<a class="text-btn" href="${escapeHTML(publicPath)}" target="_blank" rel="noreferrer">公开页</a>` : ""}
            <button class="secondary open-case-btn" data-case-id="${escapeHTML(item.case_id)}" type="button">编辑</button>
            ${item.creator_id ? `<button class="secondary open-creator-from-case-btn" data-creator-id="${escapeHTML(item.creator_id)}" type="button">看达人</button>` : ""}
          </div>
        </article>
      `;
    })
    .join("");
}

function openCaseModal(caseItem = null) {
  const modal = $("#caseModal");
  const form = $("#caseForm");
  if (!modal || !form) return;
  renderCaseCreatorOptions();
  form.reset();
  $("#caseModalTitle").textContent = caseItem ? "编辑合作案例" : "新增合作案例";
  $("#deleteCaseBtn")?.classList.toggle("hidden", !caseItem?.case_id);
  state.activeCase = caseItem;
  if (caseItem) {
    form.elements.case_id.value = caseItem.case_id || "";
    form.elements.creator_id.value = caseItem.creator_id || "";
    form.elements.brand_name.value = caseItem.brand_name || "";
    form.elements.case_title.value = caseItem.case_title || caseItem.content_topic || "";
    form.elements.case_summary.value = caseItem.case_summary || caseItem.cooperation_goal || "";
    form.elements.industry.value = caseItem.industry || "";
    form.elements.product.value = caseItem.product || "";
    form.elements.content_format.value = caseItem.content_format || "";
    form.elements.content_topic.value = caseItem.content_topic || "";
    form.elements.content_url.value = caseItem.content_url || "";
    form.elements.cooperation_goal.value = caseItem.cooperation_goal || "";
    form.elements.active_tags.value = (caseItem.active_tags || []).join("，");
    form.elements.performance_views.value = caseItem.performance?.views || caseItem.performance?.exposure || caseItem.performance?.reads || "";
    form.elements.is_successful.value = caseItem.is_successful || "";
    form.elements.comment_feedback.value = caseItem.comment_feedback || "";
    form.elements.reuse_suggestion.value = caseItem.reuse_suggestion || "";
    if (form.elements.featured_on_kit) form.elements.featured_on_kit.checked = caseItem.featured_on_kit !== false;
    if (form.elements.visibility) form.elements.visibility.value = caseItem.visibility || "public";
  } else if (form.elements.featured_on_kit) {
    form.elements.featured_on_kit.checked = true;
    if (form.elements.visibility) form.elements.visibility.value = "public";
  }
  modal.classList.remove("hidden");
}

function closeCaseModal() {
  $("#caseModal")?.classList.add("hidden");
  state.activeCase = null;
}

function caseFormPayload(form) {
  const performance = {};
  const views = String(form.elements.performance_views.value || "").trim();
  if (views) performance.views = views;
  return {
    case_id: form.elements.case_id.value || undefined,
    creator_id: form.elements.creator_id.value,
    brand_name: form.elements.brand_name.value,
    case_title: form.elements.case_title?.value || "",
    case_summary: form.elements.case_summary?.value || "",
    industry: form.elements.industry.value,
    product: form.elements.product.value,
    content_format: form.elements.content_format.value,
    content_topic: form.elements.content_topic.value,
    content_url: form.elements.content_url.value,
    cooperation_goal: form.elements.cooperation_goal.value,
    active_tags: form.elements.active_tags.value,
    performance,
    is_successful: form.elements.is_successful.value,
    comment_feedback: form.elements.comment_feedback.value,
    reuse_suggestion: form.elements.reuse_suggestion.value,
    featured_on_kit: Boolean(form.elements.featured_on_kit?.checked),
    visibility: form.elements.visibility?.value || "public",
  };
}

async function saveCaseForm(form) {
  const payload = caseFormPayload(form);
  if (!payload.creator_id) return toast("请选择达人", true);
  if (!payload.brand_name?.trim()) return toast("请填写合作品牌", true);
  if (!payload.case_title?.trim()) return toast("请填写案例标题", true);
  const isEdit = Boolean(payload.case_id);
  const data = await api(isEdit ? `/api/cases/${encodeURIComponent(payload.case_id)}` : "/api/cases", {
    method: isEdit ? "PATCH" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  closeCaseModal();
  await loadCases();
  toast(isEdit ? "案例已更新" : "案例已新增");
  return data.case;
}

async function deleteActiveCase() {
  const caseItem = state.activeCase;
  if (!caseItem?.case_id) return;
  const confirmed = window.confirm(`确认删除「${caseItem.brand_name || "这个案例"}」吗？`);
  if (!confirmed) return;
  await api(`/api/cases/${encodeURIComponent(caseItem.case_id)}`, { method: "DELETE" });
  closeCaseModal();
  await loadCases();
  toast("案例已删除");
}

function getSelectedCreatorFilterIds() {
  return Object.keys(state.creatorFilterSelected || {}).filter((id) => state.creatorFilterSelected[id]);
}

function settlementCreatorsForWizard(explicitIds = []) {
  const ids = explicitIds.length ? explicitIds : getSelectedCreatorFilterIds();
  return ids.map((id) => state.creators.find((creator) => creator.creator_id === id)).filter(Boolean);
}

function renderSettlementWizardBusinessMeta(business) {
  const node = $("#settlementWizardBusinessMeta");
  if (!node) return;
  if (!business?.business_type_label) {
    node.classList.add("hidden");
    node.innerHTML = "";
    return;
  }
  node.classList.remove("hidden");
  node.innerHTML = `
    <p><strong>业务类型：</strong>${escapeHTML(business.business_type_label)}</p>
    <p class="meta"><strong>结算目标：</strong>${escapeHTML(business.settlement_target || "")}</p>
  `;
}

function renderSettlementWizardItems(creators) {
  const node = $("#settlementWizardItems");
  if (!node) return;
  if (!creators.length) {
    node.innerHTML = '<div class="commercial-card-empty">请先在筛选结果中勾选合作达人。</div>';
    return;
  }
  node.innerHTML = creators
    .map(
      (creator) => `
    <article class="settlement-wizard-item" data-creator-id="${escapeHTML(creator.creator_id)}">
      <h3>${escapeHTML(creator.name)} <span class="meta">· ${escapeHTML(creator.platform || "未知平台")}</span></h3>
      <div class="field-row two">
        <input data-field="content_url" placeholder="发布链接" />
        <input data-field="content_format" placeholder="合作形式，如 深度稿 / 测评视频" />
      </div>
      <input data-field="content_topic" placeholder="内容主题" />
      <div class="field-row two">
        <input data-field="performance_views" placeholder="曝光 / 阅读 / 播放" />
        <select data-field="is_successful">
          <option value="">合作结果</option>
          <option value="success">成功</option>
          <option value="partial">部分达成</option>
          <option value="failed">未达预期</option>
        </select>
      </div>
      <textarea data-field="reuse_suggestion" rows="2" placeholder="复用建议，如 适合科技新品解释型传播"></textarea>
    </article>
  `,
    )
    .join("");
}

function openSettlementWizard(creators = []) {
  const modal = $("#settlementWizardModal");
  const form = $("#settlementWizardForm");
  if (!modal || !form) return;
  state.settlementWizardCreators = creators.length ? creators : settlementCreatorsForWizard();
  form.reset();
  const brief = state.creatorFilterNarrativeAnalysis?.brief || state.creatorFilterDeliverables?.brief || {};
  const business = state.creatorFilterBusinessType || state.creatorFilterNarrativeAnalysis?.business || state.creatorFilterDeliverables?.business || null;
  if (form.elements.project_name) {
    form.elements.project_name.value =
      brief.product ? `${brief.product} 传播项目` : state.creatorFilterDeliverables?.client_card?.product_service || "";
  }
  const clientCard = state.creatorFilterDeliverables?.client_card || {};
  if (form.elements.brand_name) form.elements.brand_name.value = clientCard.product_service || brief.product || "";
  if (form.elements.client_name) form.elements.client_name.value = clientCard.client_name || "";
  if (form.elements.industry) form.elements.industry.value = clientCard.industry || brief.industry || "";
  if (form.elements.product) form.elements.product.value = clientCard.product_service || brief.product || "";
  if (form.elements.payment_status && clientCard.payment_status) form.elements.payment_status.value = clientCard.payment_status;
  renderSettlementWizardBusinessMeta(business);
  renderSettlementWizardCreatorPicker();
  renderSettlementWizardItems(state.settlementWizardCreators);
  modal.classList.remove("hidden");
}

function renderSettlementWizardCreatorPicker() {
  const node = $("#settlementWizardCreatorPicker");
  if (!node) return;
  const creators = state.creators || [];
  node.innerHTML = `
    <div class="field-row two settlement-wizard-picker-row">
      <select id="settlementWizardAddCreatorSelect">
        <option value="">选择达人加入回写列表…</option>
        ${creators.map((creator) => `<option value="${escapeHTML(creator.creator_id)}">${escapeHTML(creator.name)} · ${escapeHTML(creator.platform || "")}</option>`).join("")}
      </select>
      <button type="button" class="secondary" id="settlementWizardAddCreatorBtn">添加达人</button>
    </div>
    <p class="meta">${state.settlementWizardCreators.length ? `已选 ${state.settlementWizardCreators.length} 位达人` : "可从达人库添加，或在「筛选达人工具」中勾选后打开本向导。"}</p>
  `;
  $("#settlementWizardAddCreatorBtn")?.addEventListener("click", () => {
    const creatorId = $("#settlementWizardAddCreatorSelect")?.value || "";
    if (!creatorId) return toast("请选择达人", true);
    const creator = creators.find((item) => item.creator_id === creatorId);
    if (!creator) return;
    if (state.settlementWizardCreators.some((item) => item.creator_id === creatorId)) {
      return toast("该达人已在列表中", true);
    }
    state.settlementWizardCreators = [...state.settlementWizardCreators, creator];
    renderSettlementWizardCreatorPicker();
    renderSettlementWizardItems(state.settlementWizardCreators);
  });
}

function closeSettlementWizard() {
  $("#settlementWizardModal")?.classList.add("hidden");
  state.settlementWizardCreators = [];
}

async function submitSettlementWizard(form) {
  const business = state.creatorFilterBusinessType || state.creatorFilterNarrativeAnalysis?.business || state.creatorFilterDeliverables?.business || {};
  const items = [...form.querySelectorAll(".settlement-wizard-item")]
    .map((row) => {
      const creatorId = row.dataset.creatorId || "";
      const read = (field) => row.querySelector(`[data-field="${field}"]`)?.value || "";
      const performance = {};
      const views = String(read("performance_views")).trim();
      if (views) performance.views = views;
      return {
        creator_id: creatorId,
        content_url: read("content_url"),
        content_format: read("content_format"),
        content_topic: read("content_topic"),
        is_successful: read("is_successful"),
        reuse_suggestion: read("reuse_suggestion"),
        performance,
        cooperation_goal: business.settlement_target || "",
      };
    })
    .filter((item) => item.creator_id);
  if (!items.length) return toast("没有可回写的达人", true);
  const brandName = String(form.elements.brand_name?.value || "").trim();
  if (!brandName) return toast("请填写合作品牌", true);
  const payload = {
    project_name: String(form.elements.project_name?.value || "").trim(),
    client_name: String(form.elements.client_name?.value || "").trim(),
    brand_name: brandName,
    industry: String(form.elements.industry?.value || "").trim(),
    product: String(form.elements.product?.value || "").trim(),
    business_type: business.business_type_label || business.business_type || "",
    settlement_target: business.settlement_target || "",
    client_confirmed: Boolean(form.elements.client_confirmed?.checked),
    payment_status: String(form.elements.payment_status?.value || "").trim(),
    items,
  };
  const result = await api("/api/cases/settlement-writeback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  closeSettlementWizard();
  await Promise.all([loadCases(), loadCreators().catch(() => {})]);
  toast(`已回写 ${result.total_cases || items.length} 条案例`);
}

async function loadImportTemplates() {
  const data = await api("/api/import/templates");
  state.importTemplates = data.items || [];
  renderImportTemplates();
}

async function loadGovernance() {
  const [summary, duplicates, quality] = await Promise.all([
    api("/api/governance/summary"),
    api("/api/governance/duplicates"),
    api("/api/governance/quality"),
  ]);
  state.duplicateCandidates = duplicates.items || [];
  state.qualityIssues = quality.items || [];
  renderGovernance(summary);
}

async function loadSymbolicEngines() {
  const data = await api("/api/symbolic/engines");
  renderSymbolicEngines(data);
}

async function loadCollaboration() {
  const data = await api("/api/collaboration/proposals");
  state.collabProposals = data.items || [];
  renderCollaborationList();
}

async function loadWorkspaceHistory() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  state.historyLoading = true;
  renderWorkspaceHistory();
  try {
    const data = await api("/api/history/workspace");
    state.workspaceHistory = data.items || [];
    state.historySummary = data.summary || {};
    state.historyLoaded = true;
  } finally {
    state.historyLoading = false;
    renderWorkspaceHistory();
  }
}

async function ensureWorkspaceHistoryLoaded() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  if (state.historyLoaded || state.historyLoading) return;
  try {
    await loadWorkspaceHistory();
  } catch (error) {
    state.historyLoading = false;
    renderWorkspaceHistory();
    toast(error.message || "历史资产加载失败", true);
  }
}

async function refreshWorkspaceHistoryIfVisible() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  state.historyLoaded = false;
  state.historySummary = {};
  state.workspaceHistory = [];
  if ($("#history")?.classList.contains("active")) {
    await loadWorkspaceHistory();
  }
}

async function loadOrganization() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  const [clients, proposals, access] = await Promise.all([
    api("/api/auth/clients"),
    api("/api/collaboration/proposals"),
    api("/api/auth/project-access"),
  ]);
  let users = { items: [] };
  try {
    users = await api("/api/auth/users");
  } catch (error) {
    users = { items: state.currentIdentity?.user ? [state.currentIdentity.user] : [] };
  }
  try {
    const rules = await api("/api/rules/config");
    state.ruleConfig = rules.config || null;
  } catch (error) {
    state.ruleConfig = null;
  }
  try {
    state.openClaw = await api("/api/openclaw/config");
  } catch (error) {
    state.openClaw = null;
  }
  try {
    state.openClawDiagnostics = await api("/api/openclaw/diagnostics");
  } catch (error) {
    state.openClawDiagnostics = null;
  }
  state.authUsers = users.items || [];
  state.authClients = clients.items || [];
  state.collabProposals = proposals.items || [];
  state.projectAccess = access.items || [];
  renderOrganization();
}

async function loadRuleConfig() {
  if (!isCurrentUserAdmin()) {
    renderRuleConfig();
    return;
  }
  const data = await api("/api/rules/config");
  state.ruleConfig = data.config || null;
  renderRuleConfig();
}

async function loadAgentTasks() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  const data = await api("/api/agent/threads");
  state.agentThreads = data.items || [];
  state.agentTasks = state.agentThreads;
  renderAgentTasks();
}

async function loadAgentRuntime() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  const [data, openClaw, openClawMe, openClawDiagnostics] = await Promise.all([
    api("/api/agent/runtime"),
    api("/api/openclaw/status").catch(() => null),
    api("/api/openclaw/me").catch(() => null),
    api("/api/openclaw/diagnostics").catch(() => null),
  ]);
  state.agentRuntime = data;
  if (openClaw) state.openClaw = { ...(state.openClaw || {}), ...openClaw };
  state.openClawMe = openClawMe;
  if (openClawDiagnostics) state.openClawDiagnostics = openClawDiagnostics;
  await loadOpenClawSessionsFromServer();
  renderAgentRuntimeControls();
}

async function loadKnowledge() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  const data = await api("/api/knowledge");
  state.knowledgeDocuments = data.items || [];
  state.knowledgeStats = data.stats || null;
  renderKnowledge();
}

async function loadCommercial() {
  const [invitations, submissions] = await Promise.all([
    api("/api/creator-commercial/invitations"),
    api("/api/creator-commercial/submissions"),
  ]);
  state.commercialInvitations = invitations.items || [];
  state.commercialSubmissions = submissions.items || [];
  renderCommercial();
}

async function loadDistribution() {
  const data = await api("/api/distribution/briefs");
  state.distributionBriefs = data.items || [];
  renderDistributionList();
}

async function loadPlatformDashboard() {
  const [data, campaigns] = await Promise.all([api("/api/platform/dashboard"), api("/api/platform/campaigns")]);
  state.platformDashboard = data;
  state.platformCampaigns = campaigns.items || [];
  renderPlatformDashboard(data);
}

async function loadDataSources() {
  const data = await api("/api/settings/data-sources");
  state.dataSources = data.items || [];
  renderDataSources();
}

async function loadSymbolicOS() {
  const data = await api("/api/symbolic-os");
  state.symbolicOS = data;
  renderSymbolicOS(data);
}

async function loadKolIntelligence() {
  const data = await api("/api/kol-intelligence");
  state.kolIntelligence = data;
  renderKolIntelligence(data);
  await loadPhase8ReviewQueue();
}

async function loadPhase8ReviewQueue() {
  const status = $("#phase8ReviewStatus")?.value || "";
  const creatorId = $("#phase8ReviewCreator")?.value || "";
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (creatorId) params.set("creator_id", creatorId);
  params.set("limit", "80");
  const data = await api(`/api/kol-intelligence/review-queue?${params.toString()}`);
  state.phase8ReviewQueue = data.items || [];
  renderPhase8ReviewQueue(data);
}

function renderSymbolicOS(data) {
  const output = $("#symbolicOSOutput");
  if (output) output.textContent = JSON.stringify(data || {}, null, 2);
  renderSocialReport(data?.latest_report);
  renderSignifierTags(data?.tags || []);
  renderProductSymbolics(data?.products || []);
  renderNarrativeAssets(data?.narratives || []);
  renderMatchAssets(data?.matches || []);
  renderFeedbackCorrections(data?.corrections || []);
}

function renderKolIntelligence(data) {
  const metrics = data?.metrics || {};
  const setText = (id, value) => {
    const node = $(id);
    if (node) node.textContent = fmtNumber(value);
  };
  setText("#phase8CreatorsWithTags", metrics.creators_with_tags || 0);
  setText("#phase8EvidenceTags", metrics.evidence_tags || 0);
  setText("#phase8SuggestedTags", metrics.suggested_tags || 0);
  setText("#phase8ConfirmedTags", metrics.confirmed_tags || 0);
  setText("#phase8GraphSnapshots", metrics.graph_snapshots || 0);
  setText("#phase8Predictions", metrics.predictions || 0);
  renderPhase8TopTags(data?.top_tags || []);
  renderPhase8RecentTags(data?.recent_tags || []);
  if (data?.latest_graph) {
    renderSymbolicGraphInto("#phase8GraphCanvas", data.latest_graph);
    renderPhase8Evolution(data.latest_graph.evolution || []);
  }
  if (data?.latest_prediction) renderPhase8Prediction(data.latest_prediction);
}

function renderPhase8ReviewQueue(data) {
  const node = $("#phase8ReviewQueue");
  if (!node) return;
  const items = data?.items || state.phase8ReviewQueue || [];
  state.phase8ReviewQueue = items;
  if (!items.length) {
    node.innerHTML = emptyState("暂无待审核标签", "先分析达人标签，或切换审核状态筛选。");
    return;
  }
  node.innerHTML = items
    .map(
      (tag) => `
        <article class="phase8-review-card ${escapeHTML(tag.status || "suggested")}">
          <label class="checkline phase8-review-check">
            <input class="phase8-tag-check" data-tag-id="${escapeHTML(tag.tag_id)}" type="checkbox" ${state.phase8SelectedTagIds.has(tag.tag_id) ? "checked" : ""} />
            <span class="status-pill ${phase8StatusTone(tag.status)}">${escapeHTML(tag.status || "suggested")}</span>
          </label>
          <div class="phase8-review-main">
            <div class="phase8-card-head">
              <strong>${escapeHTML(tag.tag)}</strong>
              <span class="meta">${escapeHTML(tag.creator_name || tag.creator_id)} · ${escapeHTML(tag.category)}</span>
            </div>
            <div class="phase8-review-score">
              <span>confidence ${Math.round((tag.confidence || 0) * 100)}%</span>
              <span>score ${escapeHTML(tag.score || 0)}</span>
              <span>weight ${escapeHTML(tag.weight_delta || 0)}</span>
            </div>
            <small>${escapeHTML((tag.evidence || []).slice(0, 3).join("；"))}</small>
            ${tag.reviewer_note ? `<div class="meta">备注：${escapeHTML(tag.reviewer_note)}</div>` : ""}
          </div>
          <div class="phase8-review-actions">
            <button class="secondary phase8-review-btn" data-status="confirmed" data-tag-id="${escapeHTML(tag.tag_id)}" type="button">确认</button>
            <button class="secondary phase8-review-btn" data-status="needs_more_evidence" data-tag-id="${escapeHTML(tag.tag_id)}" type="button">补证据</button>
            <button class="secondary phase8-review-btn danger" data-status="rejected" data-tag-id="${escapeHTML(tag.tag_id)}" type="button">拒绝</button>
          </div>
        </article>
      `
    )
    .join("");
}

function phase8StatusTone(status) {
  if (status === "confirmed") return "ok";
  if (status === "rejected") return "danger";
  if (status === "needs_more_evidence") return "warn";
  return "";
}

async function reviewPhase8Tags(tagIds, status) {
  const reviewerNote = $("#phase8ReviewNote")?.value || "";
  const payload = { tag_ids: tagIds, status, reviewer_note: reviewerNote };
  const data =
    tagIds.length === 1
      ? await api(`/api/kol-intelligence/tags/${encodeURIComponent(tagIds[0])}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status, reviewer_note: reviewerNote }),
        })
      : await api("/api/kol-intelligence/tags/bulk-review", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
  state.phase8SelectedTagIds.clear();
  if (data.snapshot) {
    state.kolIntelligence = data.snapshot;
    renderKolIntelligence(data.snapshot);
  }
  await loadPhase8ReviewQueue();
  toast(`${tagIds.length} 个标签已更新为 ${status}`);
}

function renderPhase8TopTags(tags) {
  const node = $("#phase8TopTags");
  if (!node) return;
  if (!tags.length) {
    node.innerHTML = emptyState("暂无标签", "先分析达人库，系统会生成证据标签。");
    return;
  }
  node.innerHTML = tags
    .map(
      (item) => `
        <article class="tag-card">
          <strong>${escapeHTML(item.tag)}</strong>
          <span>${fmtNumber(item.count)} creators</span>
        </article>
      `
    )
    .join("");
}

function renderPhase8RecentTags(tags) {
  const node = $("#phase8RecentTags");
  if (!node) return;
  if (!tags.length) {
    node.innerHTML = emptyState("暂无证据", "证据标签会显示来源、置信度和原始依据。");
    return;
  }
  node.innerHTML = tags
    .slice(0, 24)
    .map(
      (tag) => `
        <article class="phase8-tag-card">
          <div>
            <span class="status-pill">${escapeHTML(tag.category)}</span>
            <strong>${escapeHTML(tag.tag)}</strong>
          </div>
          <p>${escapeHTML(tag.creator_name || tag.creator_id)}</p>
          <div class="meta">confidence ${Math.round((tag.confidence || 0) * 100)}% · ${escapeHTML(tag.source || "")}</div>
          <small>${escapeHTML((tag.evidence || []).slice(0, 2).join("；"))}</small>
        </article>
      `
    )
    .join("");
}

function renderPhase8Evolution(items) {
  const node = $("#phase8Evolution");
  if (!node) return;
  if (!items.length) {
    node.innerHTML = emptyState("等待推演", "生成图谱或预测后会展示演进步骤。");
    return;
  }
  node.innerHTML = items
    .map(
      (item) => `
        <article class="phase8-step">
          <span>${escapeHTML(item.step || "")}</span>
          <div>
            <strong>${escapeHTML(item.title || "")}</strong>
            <p>${escapeHTML(item.detail || "")}</p>
          </div>
        </article>
      `
    )
    .join("");
}

function renderPhase8Prediction(prediction) {
  state.phase8Prediction = prediction;
  const node = $("#phase8PredictionList");
  if (!node) return;
  const recommendations = prediction?.recommendations || [];
  if (!recommendations.length) {
    node.innerHTML = emptyState("暂无推荐", "输入 brief 后运行预测。");
    return;
  }
  node.innerHTML = `
    <div class="phase8-summary">${escapeHTML(prediction.summary || "")}</div>
    ${recommendations
      .map(
        (item, index) => `
          <article class="phase8-prediction-card">
            <div class="rank-badge">${String(index + 1).padStart(2, "0")}</div>
            <div>
              <div class="phase8-card-head">
                <strong>${escapeHTML(item.creator_name || item.creator_id)}</strong>
                <span class="status-pill ok">${escapeHTML(item.recommendation_level || "")} · ${escapeHTML(item.score || "")}</span>
              </div>
              <p>${escapeHTML(item.platform || "未知平台")}</p>
              <div class="tag-list">${(item.reasons || []).slice(0, 6).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
              ${(item.risk_points || []).length ? `<div class="meta danger-text">风险：${escapeHTML(item.risk_points.join("；"))}</div>` : ""}
              <small>${escapeHTML((item.evidence || []).slice(0, 2).join(" / "))}</small>
            </div>
          </article>
        `
      )
      .join("")}
  `;
  if (prediction.graph) {
    renderSymbolicGraphInto("#phase8GraphCanvas", prediction.graph);
    renderPhase8Evolution(prediction.graph.evolution || []);
  }
}

function renderPhase82Conversation(data) {
  state.phase82Conversation = data;
  state.phase82Messages = data?.messages || state.phase82Messages || [];
  state.phase82ActiveFrame = 0;
  renderPhase82Messages();
  renderPhase82Steps();
  renderPhase82Recommendations();
  renderPhase82Frame();
  startPhase82FramePlayback();
}

function renderPhase82Messages() {
  const node = $("#phase82Messages");
  if (!node) return;
  const messages = state.phase82Messages || [];
  node.innerHTML = messages.length
    ? messages
        .map(
          (message) => `
            <article class="phase82-message ${escapeHTML(message.role || "assistant")} ${escapeHTML(message.status || "completed")}">
              <span>${escapeHTML(message.role === "user" ? "You" : "KOL OS")}</span>
              <p>${escapeHTML(message.content || "")}</p>
            </article>
          `
        )
        .join("")
    : emptyState("还没有对话", "输入一个甲方 brief，图谱会跟着对话长出来。");
  node.scrollTop = node.scrollHeight;
}

function renderPhase82Steps() {
  const node = $("#phase82Steps");
  if (!node) return;
  const steps = state.phase82Conversation?.steps || [];
  node.innerHTML = steps.length
    ? steps
        .map((step, index) => {
          const active = index <= state.phase82ActiveFrame ? " active" : "";
          return `
            <button class="phase82-step${active}" data-frame-index="${index}" type="button">
              <span>${String(index + 1).padStart(2, "0")}</span>
              <strong>${escapeHTML(step.label || step.id)}</strong>
            </button>
          `;
        })
        .join("")
    : "";
}

function renderPhase82Frame() {
  const frames = state.phase82Conversation?.graph_frames || [];
  const frame = frames[state.phase82ActiveFrame];
  const meta = $("#phase82FrameMeta");
  if (!frame) {
    if (meta) meta.textContent = "等待输入 brief。";
    $("#phase82GraphCanvas").innerHTML = '<div class="meta">输入需求后，Brief、标签、KOL 和风险会逐步出现。</div>';
    return;
  }
  if (meta) meta.textContent = `${frame.title} · ${frame.detail || ""}`;
  renderSymbolicGraphInto("#phase82GraphCanvas", frame);
  renderPhase82Steps();
}

function startPhase82FramePlayback() {
  if (state.phase82FrameTimer) clearInterval(state.phase82FrameTimer);
  const frames = state.phase82Conversation?.graph_frames || [];
  if (frames.length <= 1) return;
  state.phase82FrameTimer = setInterval(() => {
    if (state.phase82ActiveFrame >= frames.length - 1) {
      clearInterval(state.phase82FrameTimer);
      state.phase82FrameTimer = null;
      return;
    }
    state.phase82ActiveFrame += 1;
    renderPhase82Frame();
  }, 950);
}

function movePhase82Frame(delta) {
  const frames = state.phase82Conversation?.graph_frames || [];
  if (!frames.length) return;
  if (state.phase82FrameTimer) {
    clearInterval(state.phase82FrameTimer);
    state.phase82FrameTimer = null;
  }
  state.phase82ActiveFrame = Math.max(0, Math.min(frames.length - 1, state.phase82ActiveFrame + delta));
  renderPhase82Frame();
}

function renderPhase82Recommendations() {
  const summary = $("#phase82Summary");
  const list = $("#phase82RecommendationList");
  const data = state.phase82Conversation || {};
  if (summary) summary.textContent = data.summary || "等待推荐。";
  if (!list) return;
  const recommendations = data.recommendations || [];
  list.innerHTML = recommendations.length
    ? recommendations
        .map(
          (item, index) => `
            <article class="phase8-prediction-card phase82-rec-card">
              <div class="rank-badge">${String(index + 1).padStart(2, "0")}</div>
              <div>
                <div class="phase8-card-head">
                  <strong>${escapeHTML(item.creator_name || item.creator_id)}</strong>
                  <span class="status-pill ok">${escapeHTML(item.recommendation_level || "")} · ${escapeHTML(item.score || "")}</span>
                </div>
                <p>${escapeHTML(item.platform || "未知平台")}</p>
                <div class="tag-list">${(item.reasons || []).slice(0, 6).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
                ${(item.risk_points || []).length ? `<div class="meta danger-text">风险：${escapeHTML(item.risk_points.join("；"))}</div>` : ""}
                <small>${escapeHTML((item.evidence || []).slice(0, 2).join(" / "))}</small>
              </div>
            </article>
          `
        )
        .join("")
    : emptyState("暂无推荐", "运行对话图谱后会出现 KOL 决策卡。");
}

function renderKolIntakeResult(data) {
  state.kolIntakeResult = data;
  const node = $("#kolIntakeResult");
  if (!node) return;
  if (!data) {
    node.innerHTML = "";
    return;
  }
  const creators = data.creators || [];
  const tagSummary = data.tag_summary || [];
  const patchKeys = Object.keys(data.suggested_patch || data.parsed_fields || {});
  const sourceLabel = {
    text: "文字录入",
    file: "Excel / CSV",
    image: "图片识别",
  }[data.source] || data.source || "intake";
  node.innerHTML = `
    <div class="kol-intake-summary">
      <div>
        <span>已建档</span>
        <strong>${fmtNumber(data.imported)}</strong>
      </div>
      <div>
        <span>证据标签</span>
        <strong>${fmtNumber(tagSummary.reduce((sum, item) => sum + Number(item.tag_count || 0), 0))}</strong>
      </div>
      <div>
        <span>图谱节点</span>
        <strong>${fmtNumber(data.graph_summary?.nodes || 0)}</strong>
      </div>
    </div>
    <div class="kol-intake-next">
      <div>
        <strong>${escapeHTML(sourceLabel)}已进入达人库</strong>
        <span>生成的画像字段和证据标签会被 PR Brief 匹配、KOL 决策图谱、Campaign Room 复用。</span>
      </div>
      <div class="button-row">
        <button class="secondary" data-view-jump="creators" type="button">查看达人库</button>
        <button class="secondary" data-view-jump="kolIntelligence" type="button">查看决策图谱</button>
        <button class="primary" data-view-jump="projectRun" type="button">用 Brief 匹配</button>
      </div>
    </div>
    <div class="kol-intake-cards">
      ${creators
        .map((creator) => {
          const summary = tagSummary.find((item) => item.creator_id === creator.creator_id) || {};
          const groupedTags = groupKolEvidenceTags(summary.tags || []);
          const profileTags = [
            ...asTagList(creator.industry_fit_tags),
            ...asTagList(creator.content_capability_tags),
            ...asTagList(creator.suitable_goals),
            ...asTagList(creator.delivery_tags),
            ...asTagList(creator.personal_tags),
            ...asTagList(creator.risk_tags),
          ].slice(0, 10);
          return `
            <article class="creator-card kol-intake-card">
              <div class="card-kicker">${escapeHTML(sourceLabel)} · ${escapeHTML(creator.platform || "未知平台")}</div>
              <div class="creator-card-head">
                <h3>${escapeHTML(creator.name || "未命名 KOL")}</h3>
                <button class="secondary open-creator-btn" data-creator-id="${escapeHTML(creator.creator_id)}" type="button">详情</button>
              </div>
              <div class="meta">粉丝 ${fmtNumber(creator.follower_count)} · 报价 ${fmtNumber(creator.listed_price)}</div>
              <p>${escapeHTML(creator.ai_summary || creator.bio || "已完成基础画像。")}</p>
              <div class="kol-intake-field-grid">
                <div><span>行业标签</span><strong>${escapeHTML(asTagList(creator.industry_fit_tags).slice(0, 3).join(" / ") || "-")}</strong></div>
                <div><span>内容能力</span><strong>${escapeHTML(asTagList(creator.content_capability_tags).slice(0, 3).join(" / ") || "-")}</strong></div>
                <div><span>预算适配</span><strong>${escapeHTML(asTagList(creator.budget_fit_tags).slice(0, 2).join(" / ") || "-")}</strong></div>
                <div><span>风险</span><strong>${escapeHTML(asTagList(creator.risk_tags).slice(0, 2).join(" / ") || "暂无")}</strong></div>
              </div>
              <div class="tag-list">${profileTags.map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
              ${groupedTags.length ? `<div class="kol-intake-evidence">${groupedTags.join("")}</div>` : ""}
            </article>
          `;
        })
        .join("")}
    </div>
    ${
      patchKeys.length
        ? `<div class="meta">识别字段：${patchKeys.map((key) => escapeHTML(key)).join(" / ")}</div>`
        : ""
    }
  `;
}

function groupKolEvidenceTags(tags) {
  const labels = {
    industry: "行业",
    content: "内容",
    goal: "目标",
    stage: "阶段",
    budget: "预算",
    risk: "风险",
    platform: "平台",
    symbolic: "符号",
    persona: "人设",
    case: "案例",
    metric: "数据",
  };
  const groups = {};
  (tags || []).forEach((tag) => {
    const category = tag.category || "tag";
    if (!groups[category]) groups[category] = [];
    groups[category].push(tag);
  });
  return Object.entries(groups)
    .slice(0, 6)
    .map(([category, items]) => {
      const chips = items
        .slice(0, 5)
        .map((tag) => `<span class="tag ${category === "risk" ? "risk" : ""}">${escapeHTML(tag.tag || "")}</span>`)
        .join("");
      return `<div class="kol-intake-evidence-row"><strong>${escapeHTML(labels[category] || category)}</strong><div>${chips}</div></div>`;
    });
}

function renderHomeBriefResult(data) {
  state.homeBriefConversation = data;
  state.homeBriefShare = null;
  const node = $("#homeBriefResult");
  if (!node) return;
  if (!data) {
    node.innerHTML = "";
    return;
  }
  const frames = data.graph_frames || [];
  const finalFrame = frames[frames.length - 1] || data.graph || null;
  const recommendations = data.recommendations || [];
  const proposal = buildHomeBriefProposal(data);
  state.lastProposal = proposal;
  const proposalPreview = proposal.split("\n").slice(0, 18).join("\n");
  node.innerHTML = `
    <div class="home-brief-meta">
      <span>${escapeHTML(data.project_name || "PR Brief")}</span>
      <strong>${escapeHTML(data.summary || "已完成 KOL 推演。")}</strong>
      <button class="secondary home-brief-to-filter-btn" type="button">带入筛选达人</button>
    </div>
    <div class="home-brief-steps">
      ${(data.steps || [])
        .map(
          (step, index) => `
            <div class="home-brief-step">
              <span>${String(index + 1).padStart(2, "0")}</span>
              <strong>${escapeHTML(step.label || step.id)}</strong>
            </div>
          `
        )
        .join("")}
    </div>
    <div class="home-brief-output">
      <div id="homeBriefGraphCanvas" class="symbolic-graph home-brief-graph"></div>
      <div class="home-brief-recs">
        ${recommendations.length
          ? recommendations
              .slice(0, 5)
              .map(
                (item, index) => `
                  <article class="phase8-prediction-card home-brief-rec">
                    <div class="rank-badge">${String(index + 1).padStart(2, "0")}</div>
                    <div>
                      <div class="phase8-card-head">
                        <strong>${escapeHTML(item.creator_name || item.creator_id)}</strong>
                        <span class="status-pill ok">${escapeHTML(item.recommendation_level || "")} · ${escapeHTML(item.score || "")}</span>
                      </div>
                      <p>${escapeHTML(item.platform || "未知平台")}</p>
                      <div class="tag-list">${(item.reasons || []).slice(0, 5).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
                    </div>
                  </article>
                `
              )
              .join("")
          : emptyState("暂无推荐", "先导入 KOL 或补充 brief。")}
      </div>
    </div>
    <div class="home-brief-proposal">
      <div class="panel-header">
        <div>
          <h3>客户方案草稿</h3>
          <p>基于本次图谱推荐自动整理，可复制给甲方或继续编辑。</p>
        </div>
        <div class="button-row">
          <button class="secondary home-proposal-copy-btn" type="button">复制方案</button>
          <button class="secondary home-proposal-download-btn" type="button">下载方案</button>
          <button class="secondary home-proposal-share-btn" type="button">生成甲方链接</button>
          <button class="secondary home-proposal-open-btn" type="button">打开方案页</button>
        </div>
      </div>
      <pre>${escapeHTML(proposalPreview)}${proposal.split("\n").length > 18 ? "\n..." : ""}</pre>
      <div id="homeProposalShareBox" class="home-proposal-share hidden"></div>
    </div>
  `;
  if (finalFrame) renderSymbolicGraphInto("#homeBriefGraphCanvas", finalFrame);
}

function renderHomeProposalShare(data) {
  state.homeBriefShare = data;
  const box = $("#homeProposalShareBox");
  if (!box) return;
  const proposal = data?.proposal || {};
  const shareUrl = proposal.share_url ? new URL(proposal.share_url, window.location.origin).toString() : "";
  box.classList.toggle("hidden", !shareUrl);
  box.innerHTML = shareUrl
    ? `
      <span>甲方链接</span>
      <code>${escapeHTML(shareUrl)}</code>
      <button class="secondary home-share-copy-btn" type="button">复制链接</button>
    `
    : "";
}

function buildHomeBriefProposal(data) {
  const recommendations = data?.recommendations || [];
  const lines = [
    `# ${data?.project_name || "KOL 推荐方案"}`,
    "",
    `客户：${data?.client_name || "待确认"}`,
    "",
    "## 1. Brief 摘要",
    "",
    data?.brief || "待补充 brief。",
    "",
    "## 2. 图谱推演结论",
    "",
    data?.summary || "系统已完成 KOL 决策图谱推演。",
    "",
    "## 3. 推荐 KOL",
    "",
  ];
  if (!recommendations.length) {
    lines.push("- 暂无推荐，请补充 KOL 数据或细化 brief。", "");
  }
  recommendations.slice(0, 12).forEach((item, index) => {
    lines.push(
      `### ${index + 1}. ${item.creator_name || item.creator_id}（${item.platform || "未知平台"}）`,
      "",
      `- 推荐等级：${item.recommendation_level || "待判断"}`,
      `- 匹配分：${item.score || "-"}`,
      `- 推荐理由：${(item.reasons || []).join("、") || "待补充"}`,
      `- 证据：${(item.evidence || []).slice(0, 4).join("；") || "待补充"}`,
      `- 风险：${(item.risk_points || []).join("；") || "暂无明显风险"}`,
      ""
    );
  });
  lines.push(
    "## 4. 下一步",
    "",
    "1. 媒介复核推荐名单、报价和档期。",
    "2. 补充真实案例、历史合作和内容样稿。",
    "3. 与甲方确认平台组合、预算分配和风险边界。",
    "4. 进入 Campaign Room 跟进执行和投后复盘。"
  );
  return lines.join("\n");
}

function renderSocialReport(report) {
  const node = $("#socialReportCard");
  if (!node) return;
  if (!report) {
    node.innerHTML = emptyState("暂无社会符号报告", "粘贴本周舆情、行业观察或评论摘要后生成。");
    return;
  }
  const issues = (report.issues || [])
    .slice(0, 4)
    .map(
      (issue) => `
        <article class="symbolic-os-issue">
          <div class="card-kicker">${escapeHTML(issue.core_emotion || "社会情绪")}</div>
          <strong>${escapeHTML(issue.issue)}</strong>
          <p>${escapeHTML(issue.symptom || "")}</p>
          <div class="tag-list">${(issue.keywords || []).slice(0, 5).map((item) => `<span class="tag">${escapeHTML(item)}</span>`).join("")}</div>
          <div class="meta">机会：${escapeHTML(issue.opportunity || "")}</div>
          <div class="meta danger-text">风险：${escapeHTML(issue.risk_direction || "")}</div>
        </article>
      `
    )
    .join("");
  node.innerHTML = `
    <div class="symbolic-os-summary">
      <div>
        <div class="card-kicker">${escapeHTML(report.period || "当前周期")}</div>
        <h3>${escapeHTML(report.title || "社会符号网络报告")}</h3>
        <p>${escapeHTML(report.overall_symptom || "")}</p>
      </div>
      <span class="status-pill">confidence ${Math.round((report.confidence || 0) * 100)}%</span>
    </div>
    <div class="tag-list">${(report.mood_map || []).map((item) => `<span class="tag">${escapeHTML(item)}</span>`).join("")}</div>
    <div class="symbolic-os-issues">${issues}</div>
  `;
}

function renderSignifierTags(tags) {
  const node = $("#signifierTagList");
  if (!node) return;
  if (!tags.length) {
    node.innerHTML = emptyState("暂无能指标签", "系统会先注入一组种子标签，也可以手动新增。");
    return;
  }
  node.innerHTML = tags
    .slice(0, 24)
    .map(
      (tag) => `
        <article class="tag-card">
          <div class="card-kicker">${escapeHTML(tag.tag_type || "传播标签")}</div>
          <strong>${escapeHTML(tag.name)}</strong>
          <p>${escapeHTML(tag.emotion || tag.risk_notes || "")}</p>
          <div class="tag-list">${(tag.related_tags || []).slice(0, 4).map((item) => `<span class="tag">${escapeHTML(item)}</span>`).join("")}</div>
          ${(tag.opposite_tags || []).length ? `<div class="meta">相反：${escapeHTML((tag.opposite_tags || []).slice(0, 3).join("、"))}</div>` : ""}
        </article>
      `
    )
    .join("");
}

function renderFeedbackCorrections(corrections) {
  const node = $("#feedbackCorrectionList");
  if (!node) return;
  if (!corrections.length) {
    node.innerHTML = emptyState("暂无投后修正", "录入 Campaign 投后复盘后，这里会沉淀符号假设和标签修正。");
    return;
  }
  node.innerHTML = corrections
    .slice(0, 20)
    .map(
      (item) => `
        <article class="correction-card">
          <div class="card-kicker">${escapeHTML(item.campaign_id)} · ${escapeHTML(item.creator_id)}</div>
          <strong>${escapeHTML(item.next_suggestion || "已生成修正建议")}</strong>
          <div class="tag-list">${(item.activated_tags || []).slice(0, 5).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
          ${(item.misread_points || []).length ? `<div class="tag-list">${item.misread_points.slice(0, 4).map((tag) => `<span class="tag danger">${escapeHTML(tag)}</span>`).join("")}</div>` : ""}
          <p>${escapeHTML(item.evidence_summary || "")}</p>
        </article>
      `
    )
    .join("");
}

function renderProductSymbolics(products) {
  const node = $("#productSymbolicList");
  if (!node) return;
  if (!products.length) {
    node.innerHTML = emptyState("暂无产品符号档案", "生成后会进入符号图谱，帮助品牌-产品-博主关系更清楚。");
    return;
  }
  node.innerHTML = products
    .slice(0, 10)
    .map(
      (item) => `
        <article class="product-symbolic-card">
          <div class="card-kicker">${escapeHTML(item.category || "产品")}</div>
          <strong>${escapeHTML(item.product_name || "未命名产品")}</strong>
          <p>${escapeHTML((item.emotional_value || []).slice(0, 2).join("、") || "等待补充情绪价值")}</p>
          <div class="tag-list">${(item.metaphors || []).slice(0, 4).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
          <div class="tag-list">${(item.risk_notes || []).slice(0, 3).map((tag) => `<span class="tag danger">${escapeHTML(tag)}</span>`).join("")}</div>
        </article>
      `
    )
    .join("");
}

function renderNarrativeAssets(narratives) {
  const node = $("#narrativeAssetList");
  if (!node) return;
  if (!narratives.length) {
    node.innerHTML = emptyState("暂无内容叙事资产", "在符号匹配页生成叙事路径后保存，这里会变成可复用 brief 资产。");
    return;
  }
  node.innerHTML = narratives
    .slice(0, 20)
    .map(
      (item) => `
        <article class="narrative-asset-card">
          <div class="card-kicker">${escapeHTML(item.project || "传播项目")} · ${escapeHTML(item.creator_name || "通用路径")}</div>
          <strong>${escapeHTML(item.narrative_path || item.target_tag || "叙事路径")}</strong>
          <p>${escapeHTML(item.content_brief || "")}</p>
          <div class="tag-list">${(item.mediating_tags || []).slice(0, 5).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
          <div class="tag-list">${(item.risk_words || []).slice(0, 4).map((tag) => `<span class="tag danger">${escapeHTML(tag)}</span>`).join("")}</div>
        </article>
      `
    )
    .join("");
}

function renderMatchAssets(matches) {
  const node = $("#matchAssetList");
  if (!node) return;
  if (!matches.length) {
    node.innerHTML = emptyState("暂无匹配资产", "在符号匹配页保存结果后，这里会沉淀品牌-博主适配关系。");
    return;
  }
  node.innerHTML = matches
    .slice(0, 30)
    .map(
      (item) => `
        <article class="match-asset-card">
          <div class="card-kicker">${escapeHTML(item.recommendation_level || item.suggested_priority || "pending")} · score ${escapeHTML(item.symbolic_score)}</div>
          <strong>${escapeHTML(item.brand_name || "品牌")} × ${escapeHTML(item.creator_name || "博主")}</strong>
          <p>${escapeHTML(item.match_reason || "")}</p>
          <div class="tag-list">${(item.matched_brand_tags || []).slice(0, 5).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
          <div class="tag-list">${(item.risk_points || []).slice(0, 4).map((tag) => `<span class="tag danger">${escapeHTML(tag)}</span>`).join("")}</div>
          <div class="meta">${escapeHTML(item.manual_status || "pending_review")} · ${escapeHTML(item.client_status || "not_shared")}</div>
        </article>
      `
    )
    .join("");
}

function renderCreatorOptions() {
  const select = $("#symbolicCreatorSelect");
  if (select) {
    select.innerHTML = state.creators
      .map((creator) => `<option value="${creator.creator_id}">${creator.name} · ${creator.platform}</option>`)
      .join("");
  }
  const commercialSelect = $("#commercialCreatorSelect");
  if (commercialSelect) {
    commercialSelect.innerHTML = state.creators
    .map((creator) => `<option value="${creator.creator_id}">${creator.name} · ${creator.platform}</option>`)
    .join("");
  }
  const reviewSelect = $("#postReviewCreatorSelect");
  if (reviewSelect) {
    reviewSelect.innerHTML = state.creators
      .map((creator) => `<option value="${creator.creator_id}">${creator.name} · ${creator.platform}</option>`)
      .join("");
  }
  const phase8ReviewSelect = $("#phase8ReviewCreator");
  if (phase8ReviewSelect) {
    phase8ReviewSelect.innerHTML =
      '<option value="">全部达人</option>' +
      state.creators.map((creator) => `<option value="${creator.creator_id}">${creator.name} · ${creator.platform}</option>`).join("");
  }
}

function creatorTagsFromFields(creator, fields) {
  return fields.flatMap((field) => asTagList(creator[field]));
}

function creatorFilterTagOptions(group) {
  const presets = group.fields.flatMap((field) => QUICK_CREATOR_TAG_PRESETS[field] || []);
  const fromCreators = state.creators.flatMap((creator) => creatorTagsFromFields(creator, group.fields));
  const selected = state.creatorFilterTags[group.id] || [];
  return [...selected, ...presets, ...fromCreators].filter((tag, index, list) => list.indexOf(tag) === index).slice(0, 28);
}

function getCreatorFilterTagCriteria() {
  const criteria = {};
  for (const group of CREATOR_TAG_FILTER_GROUPS) {
    const tags = (state.creatorFilterTags[group.id] || []).map((tag) => String(tag).trim()).filter(Boolean);
    if (tags.length) criteria[group.id] = { fields: group.fields, tags };
  }
  return criteria;
}

function creatorMatchesTagFilters(creator, tagCriteria) {
  for (const { fields, tags } of Object.values(tagCriteria)) {
    const creatorTags = new Set(creatorTagsFromFields(creator, fields));
    if (!tags.some((tag) => creatorTags.has(tag))) return false;
  }
  return true;
}

function renderCreatorFilterTagGroupPanel(nodeId, groupIds, head = null) {
  const node = $(nodeId);
  if (!node) return;
  const groups = CREATOR_TAG_FILTER_GROUPS.filter((group) => groupIds.includes(group.id));
  const headHtml = head
    ? `
    <div class="creator-filter-tag-head">
      <strong>${escapeHTML(head.title || "")}</strong>
      ${head.hint ? `<span class="meta">${escapeHTML(head.hint)}</span>` : ""}
    </div>
  `
    : "";
  node.innerHTML = `
    ${headHtml}
    ${groups
      .map((group) => {
        const selected = new Set(state.creatorFilterTags[group.id] || []);
        const options = creatorFilterTagOptions(group);
        const chips = options.length
          ? options
              .map((tag) => {
                const active = selected.has(tag) ? " active" : "";
                return `<button type="button" class="tag-chip small creator-filter-tag-chip${active}" data-filter-group="${escapeHTML(group.id)}" data-filter-tag="${escapeHTML(tag)}">${escapeHTML(tag)}</button>`;
              })
              .join("")
          : '<span class="meta">暂无标签，请先在达人库录入</span>';
        return `
          <div class="creator-filter-tag-row" data-filter-group-row="${escapeHTML(group.id)}">
            <span class="creator-filter-tag-label">${escapeHTML(group.label)}${group.essential ? "<em>*</em>" : ""}</span>
            <div class="creator-filter-tag-chips">${chips}</div>
          </div>
        `;
      })
      .join("")}
  `;
}

function renderCreatorFilterTagFramework() {
  renderCreatorFilterTagGroupPanel("#creatorFilterTagFramework", CREATOR_NARRATIVE_FILTER_GROUP_IDS);
  renderCreatorFilterTagGroupPanel("#creatorFilterTagFrameworkExtra", CREATOR_EXTRA_FILTER_GROUP_IDS);
}

function toggleCreatorFilterTag(groupId, tag) {
  const current = [...(state.creatorFilterTags[groupId] || [])];
  const index = current.indexOf(tag);
  if (index >= 0) current.splice(index, 1);
  else current.push(tag);
  state.creatorFilterTags[groupId] = current;
  renderCreatorFilterTagFramework();
  renderCreatorFilterResults();
}

function clearCreatorFilterTags() {
  state.creatorFilterTags = {};
  renderCreatorFilterTagFramework();
}

function loadCreatorFilterPresets() {
  let saved = [];
  try {
    const raw = localStorage.getItem(CREATOR_FILTER_PRESETS_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    saved = Array.isArray(parsed) ? parsed : [];
  } catch {
    saved = [];
  }
  return [...BUILTIN_CREATOR_FILTER_PRESETS, ...saved.filter((item) => !item.builtin)];
}

function saveCreatorFilterPresetsToStorage(presets) {
  const savedOnly = presets.filter((item) => !item.builtin);
  localStorage.setItem(CREATOR_FILTER_PRESETS_KEY, JSON.stringify(savedOnly));
}

function renderCreatorFilterBusinessType(business) {
  const node = $("#creatorFilterBusinessType");
  if (!node) return;
  if (!business?.business_type_label) {
    node.classList.add("hidden");
    node.innerHTML = "";
    return;
  }
  state.creatorFilterBusinessType = business;
  node.classList.remove("hidden");
  const confidenceLabel = business.confidence === "high" ? "高" : business.confidence === "medium" ? "中" : "低";
  node.innerHTML = `
    <div class="creator-filter-business-card">
      <div class="creator-filter-business-head">
        <strong>业务类型判断</strong>
        <span class="status-pill">${escapeHTML(business.business_type_label)}</span>
        <span class="meta">置信 ${escapeHTML(confidenceLabel)}</span>
      </div>
      <p><strong>本次结算目标：</strong>${escapeHTML(business.settlement_target || "待确认")}</p>
      <p class="meta">${escapeHTML(business.reason || "")}</p>
      ${
        business.recommend_two_stage
          ? `<p class="meta creator-filter-business-tip">建议优先采用<strong>二段传播</strong>：通过高信任节点转译信息，而非纯流量曝光。</p>`
          : ""
      }
    </div>
  `;
}

function applyTwoStagePropagationPreset() {
  const preset = BUILTIN_CREATOR_FILTER_PRESETS[0];
  if (!preset) return;
  applyCreatorFilterSnapshot(preset.snapshot);
  toast(`已载入「${preset.name}」`);
}

function applyCreatorFilterBusinessFromData(data) {
  const business = data?.business || null;
  renderCreatorFilterBusinessType(business);
  if (business?.recommend_two_stage && !Object.keys(state.creatorFilterTags || {}).length) {
    const preset = BUILTIN_CREATOR_FILTER_PRESETS[0];
    if (preset?.snapshot?.tags) {
      state.creatorFilterTags = JSON.parse(JSON.stringify(preset.snapshot.tags));
      renderCreatorFilterTagFramework();
    }
  }
}

const CLIENT_CARDS_STORAGE_KEY = "pr_os_client_cards";

function loadStoredClientCards() {
  try {
    const raw = localStorage.getItem(CLIENT_CARDS_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveStoredClientCards(cards) {
  localStorage.setItem(CLIENT_CARDS_STORAGE_KEY, JSON.stringify(cards.slice(0, 30)));
}

function persistClientCardDraft(card) {
  if (!card?.client_name) return;
  const cards = loadStoredClientCards().filter((item) => item.client_name !== card.client_name);
  cards.unshift({ ...card, saved_at: new Date().toISOString() });
  saveStoredClientCards(cards);
}

function normalizeDeliverablesPayload(data) {
  if (!data || typeof data !== "object") return data;
  const business = data.business || {};
  const quote = data.quote_skeleton || {};
  const topics = data.topic_cards || [];
  const summary = {
    business_type: business.business_type_label || data.summary?.business_type || "",
    topic_count: topics.length,
    package_name: quote.package_name || data.summary?.package_name || "",
    ai_enriched: Boolean(data.ai_enriched ?? data.summary?.ai_enriched),
  };
  return { ...data, business, summary };
}

function syncDeliverablesLinkage(data) {
  const payload = normalizeDeliverablesPayload(data);
  if (!payload) return null;
  if (payload.business?.business_type_label) {
    state.creatorFilterBusinessType = payload.business;
    renderCreatorFilterBusinessType(payload.business);
    applyCreatorFilterBusinessFromData({ business: payload.business });
  }
  return payload;
}

function businessTypeFromClientCard(card) {
  if (!card) return null;
  const label = String(card.demand_type || "").trim();
  if (!label) return null;
  return {
    business_type_label: label,
    settlement_target: card.settlement_target || "",
    recommend_two_stage: /公关|品牌|商誉/.test(label),
  };
}

async function fetchClientCardsList(query = "") {
  try {
    const data = await api(`/api/client-cards${query ? `?q=${encodeURIComponent(query)}` : ""}`);
    return Array.isArray(data.items) ? data.items : [];
  } catch {
    return loadStoredClientCards();
  }
}

function applyClientCardToDeliverables(card) {
  if (!card || !state.creatorFilterDeliverables) return;
  state.creatorFilterDeliverables.client_card = { ...(state.creatorFilterDeliverables.client_card || {}), ...card };
  const business = businessTypeFromClientCard(card);
  if (business) {
    state.creatorFilterBusinessType = business;
    renderCreatorFilterBusinessType(business);
  }
  renderCreatorFilterDeliverables(state.creatorFilterDeliverables);
}

async function renderCreatorFilterDeliverables(data) {
  const node = $("#creatorFilterDeliverables");
  if (!node) return;
  if (!data) {
    node.classList.add("hidden");
    node.innerHTML = "";
    return;
  }
  state.creatorFilterDeliverables = normalizeDeliverablesPayload(data);
  const client = state.creatorFilterDeliverables.client_card || {};
  const quote = state.creatorFilterDeliverables.quote_skeleton || {};
  const topics = state.creatorFilterDeliverables.topic_cards || [];
  const summary = state.creatorFilterDeliverables.summary || {};
  const savedCards = await fetchClientCardsList();
  node.classList.remove("hidden");
  node.innerHTML = `
    <div class="creator-filter-deliverables-card">
      <div class="creator-filter-deliverables-head">
        <strong>媒介交付包</strong>
        <span class="meta">${escapeHTML(quote.package_name || "报价骨架")}${summary.ai_enriched ? " · AI 润色" : ""}</span>
        <div class="button-row compact-row">
          <label class="inline-check"><input type="checkbox" id="deliverableUseLlm" /> AI 润色选题</label>
          <select id="deliverableClientCardPicker" class="secondary compact-select">
            <option value="">载入已存客户卡…</option>
            ${savedCards.map((item) => `<option value="${escapeHTML(item.card_id || "")}">${escapeHTML(item.client_name || "未命名")}</option>`).join("")}
          </select>
          <button type="button" class="secondary" id="creatorFilterSaveClientCardBtn">保存客户卡</button>
          <button type="button" class="secondary" id="creatorFilterCopyDeliverablesBtn">复制 Markdown</button>
          <button type="button" class="secondary" id="creatorFilterDownloadDeliverablesBtn">下载媒介包</button>
        </div>
      </div>
      <details class="creator-filter-deliverable-block" open>
        <summary>客户卡</summary>
        <div class="creator-filter-client-card-grid">
          <label>客户名称<input id="deliverableClientName" value="${escapeHTML(client.client_name || "")}" /></label>
          <label>行业<input id="deliverableIndustry" value="${escapeHTML(client.industry || "")}" /></label>
          <label>决策人<input id="deliverableDecisionMaker" value="${escapeHTML(client.decision_maker || "")}" /></label>
          <label>预算<input id="deliverableBudget" value="${escapeHTML(client.budget_range || "")}" /></label>
          <label>目标人群<input id="deliverableAudience" value="${escapeHTML(client.target_audience || "")}" /></label>
          <label>平台<input id="deliverablePlatforms" value="${escapeHTML(client.required_platforms || "")}" /></label>
          <label class="full">必须说<textarea id="deliverableMustSay" rows="2">${escapeHTML(client.must_say || "")}</textarea></label>
          <label class="full">不能说<textarea id="deliverableMustNotSay" rows="2">${escapeHTML(client.must_not_say || "")}</textarea></label>
        </div>
      </details>
      <details class="creator-filter-deliverable-block" open>
        <summary>选题卡（${topics.length}）</summary>
        <div class="creator-filter-topic-list">
          ${topics
            .map(
              (topic, index) => `
            <article class="creator-filter-topic-card">
              <h4>${index + 1}. ${escapeHTML(topic.topic_title || "选题")}</h4>
              <p><strong>主张：</strong>${escapeHTML(topic.core_claim || "")}</p>
              <p class="meta">${escapeHTML(topic.content_format || "")} · ${escapeHTML(topic.creator_fit || "")}</p>
              <p class="meta">证据：${escapeHTML(topic.evidence_needed || "")}</p>
            </article>
          `,
            )
            .join("")}
        </div>
      </details>
      <details class="creator-filter-deliverable-block">
        <summary>报价骨架 · ${escapeHTML(quote.package_name || "")}</summary>
        <ul class="creator-filter-quote-list">
          <li><strong>范围：</strong>${escapeHTML(quote.scope || "")}</li>
          <li><strong>交付：</strong>${escapeHTML(quote.deliverable_units || "")}</li>
          <li><strong>达人数量：</strong>${escapeHTML(String(quote.creator_count || ""))}</li>
          <li><strong>报价合计：</strong>${quote.quoted_total ? `${Number(quote.quoted_total).toLocaleString()} 元` : "待测算"}</li>
          <li><strong>时间线：</strong>${escapeHTML(quote.timeline || "")}</li>
          <li><strong>付款节点：</strong>${escapeHTML((quote.payment_milestones || []).map((item) => `${item.stage} ${item.ratio}`).join("；"))}</li>
          <li><strong>退出规则：</strong>${escapeHTML(quote.exit_rule || "")}</li>
        </ul>
      </details>
    </div>
  `;
  $("#creatorFilterSaveClientCardBtn")?.addEventListener("click", () => saveDeliverableClientCard());
  $("#creatorFilterCopyDeliverablesBtn")?.addEventListener("click", copyDeliverablesMarkdown);
  $("#creatorFilterDownloadDeliverablesBtn")?.addEventListener("click", downloadDeliverablesMarkdown);
  $("#deliverableClientCardPicker")?.addEventListener("change", (event) => {
    const cardId = event.target.value;
    if (!cardId) return;
    const card = savedCards.find((item) => item.card_id === cardId);
    if (card) applyClientCardToDeliverables(card);
  });
  if ($("#deliverableUseLlm")) {
    $("#deliverableUseLlm").checked = Boolean(summary.ai_enriched);
    $("#deliverableUseLlm").onchange = async () => {
      const briefText = getCreatorFilterNarrativeBriefText() || $("#creatorFilterBriefInput")?.value || "";
      if (!briefText) return toast("请先填写 Brief", true);
      await loadCreatorFilterDeliverables(briefText);
    };
  }
  syncDeliverablesLinkage(state.creatorFilterDeliverables);
}

function collectDeliverableClientCard() {
  const base = state.creatorFilterDeliverables?.client_card || {};
  return {
    ...base,
    client_name: $("#deliverableClientName")?.value || base.client_name || "",
    industry: $("#deliverableIndustry")?.value || base.industry || "",
    decision_maker: $("#deliverableDecisionMaker")?.value || base.decision_maker || "",
    budget_range: $("#deliverableBudget")?.value || base.budget_range || "",
    target_audience: $("#deliverableAudience")?.value || base.target_audience || "",
    required_platforms: $("#deliverablePlatforms")?.value || base.required_platforms || "",
    must_say: $("#deliverableMustSay")?.value || base.must_say || "",
    must_not_say: $("#deliverableMustNotSay")?.value || base.must_not_say || "",
  };
}

async function saveDeliverableClientCard() {
  const card = collectDeliverableClientCard();
  if (!card.client_name?.trim()) {
    toast("请填写客户名称", true);
    return;
  }
  if (state.creatorFilterDeliverables) {
    state.creatorFilterDeliverables.client_card = card;
  }
  try {
    const data = await api("/api/client-cards", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(card),
    });
    const saved = data.card || card;
    persistClientCardDraft(saved);
    toast(`客户卡「${saved.client_name}」已保存`);
  } catch (error) {
    persistClientCardDraft(card);
    toast(error.message || `客户卡「${card.client_name}」已本地保存`, true);
  }
}

function getDeliverablesMarkdown() {
  return state.creatorFilterDeliverables?.markdown || "";
}

async function copyDeliverablesMarkdown() {
  const markdown = getDeliverablesMarkdown();
  if (!markdown) return toast("请先生成媒介交付包", true);
  try {
    await navigator.clipboard.writeText(markdown);
    toast("媒介包 Markdown 已复制");
  } catch {
    toast("复制失败，请改用下载", true);
  }
}

function downloadDeliverablesMarkdown() {
  const markdown = getDeliverablesMarkdown();
  if (!markdown) return toast("请先生成媒介交付包", true);
  const name = (collectDeliverableClientCard().client_name || "媒介交付包").replace(/[\\/:*?"<>|\\s]+/g, "_");
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${name}_媒介交付包.md`;
  a.click();
  URL.revokeObjectURL(url);
  toast("媒介包已下载");
}

async function loadCreatorFilterDeliverables(briefText, options = {}) {
  const brief = String(briefText || "").trim();
  if (!brief) {
    renderCreatorFilterDeliverables(null);
    return;
  }
  const selectedCount = getSelectedCreatorFilterIds().length;
  const useLlm = Boolean($("#deliverableUseLlm")?.checked || options.useLlm);
  try {
    const data = normalizeDeliverablesPayload(
      await api("/api/brief/deliverables", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          brief,
          client_name: options.clientName || collectDeliverableClientCard().client_name || "",
          creator_count: selectedCount || options.creatorCount || 8,
          use_llm: useLlm,
        }),
      }),
    );
    await renderCreatorFilterDeliverables(data);
  } catch (error) {
    renderCreatorFilterDeliverables(null);
    toast(error.message || "媒介交付包生成失败", true);
  }
}

function snapshotCreatorFilter() {
  const form = $("#creatorFilterForm");
  if (!form) return null;
  return {
    platform: String(form.elements.platform?.value || ""),
    sort: form.elements.sort?.value || "follower_desc",
    query: String(form.elements.query?.value || ""),
    min_followers: form.elements.min_followers?.value || "",
    max_followers: form.elements.max_followers?.value || "",
    max_price: form.elements.max_price?.value || "",
    min_like_fan_ratio: form.elements.min_like_fan_ratio?.value || "",
    max_like_fan_ratio: form.elements.max_like_fan_ratio?.value || "",
    min_engagement: form.elements.min_engagement?.value || "",
    min_avg_likes: form.elements.min_avg_likes?.value || "",
    min_recent_posts_count: form.elements.min_recent_posts_count?.value || "",
    max_sync_age_days: form.elements.max_sync_age_days?.value || "",
    narrative_brief: getCreatorFilterNarrativeBriefText(),
    text_tags: getCreatorFilterTextTagsValue(),
    step: state.creatorFilterStep,
    tags: JSON.parse(JSON.stringify(state.creatorFilterTags)),
  };
}

function applyCreatorFilterSnapshot(snapshot) {
  const form = $("#creatorFilterForm");
  if (!form || !snapshot) return;
  if (snapshot.platform != null) form.elements.platform.value = snapshot.platform;
  if (snapshot.sort) form.elements.sort.value = snapshot.sort;
  if (snapshot.query != null) form.elements.query.value = snapshot.query;
  ["min_followers", "max_followers", "max_price", "min_like_fan_ratio", "max_like_fan_ratio", "min_engagement", "min_avg_likes", "min_recent_posts_count", "max_sync_age_days"].forEach(
    (name) => {
      if (snapshot[name] != null) form.elements[name].value = snapshot[name];
    },
  );
  if (snapshot.step) state.creatorFilterStep = Number(snapshot.step) || 1;
  if (snapshot.narrative_brief != null) {
    const narrative = $("#creatorFilterNarrativeBrief");
    if (narrative) narrative.value = snapshot.narrative_brief;
  }
  if (snapshot.text_tags != null) {
    const tags = $("#creatorFilterTextTags");
    if (tags) tags.value = snapshot.text_tags;
  }
  state.creatorFilterTags =
    snapshot.tags && typeof snapshot.tags === "object" ? JSON.parse(JSON.stringify(snapshot.tags)) : {};
  renderCreatorFilterTagFramework();
  renderCreatorFilterStepper();
  setCreatorFilterStep(state.creatorFilterStep || 1);
  renderCreatorFilterResults();
}

function renderCreatorFilterPresetSelect() {
  const select = $("#creatorFilterPresetSelect");
  if (!select) return;
  const presets = loadCreatorFilterPresets();
  const current = select.value;
  select.innerHTML =
    '<option value="">已保存的方案…</option>' +
    presets.map((preset) => `<option value="${escapeHTML(preset.id)}">${escapeHTML(preset.name)}</option>`).join("");
  if (current && presets.some((preset) => preset.id === current)) select.value = current;
}

function saveCreatorFilterPreset() {
  const name = window.prompt("筛选方案名称", "");
  if (!name || !name.trim()) return;
  const snapshot = snapshotCreatorFilter();
  if (!snapshot) return;
  const presets = loadCreatorFilterPresets();
  const id = `preset_${Date.now()}`;
  presets.unshift({ id, name: name.trim(), savedAt: new Date().toISOString(), snapshot });
  if (presets.length > 20) presets.length = 20;
  saveCreatorFilterPresetsToStorage(presets);
  renderCreatorFilterPresetSelect();
  const select = $("#creatorFilterPresetSelect");
  if (select) select.value = id;
  toast(`已保存「${name.trim()}」`);
}

function loadSelectedCreatorFilterPreset() {
  const select = $("#creatorFilterPresetSelect");
  const id = select?.value;
  if (!id) {
    toast("请先选择一个方案", true);
    return;
  }
  const preset = loadCreatorFilterPresets().find((item) => item.id === id);
  if (!preset) {
    toast("方案不存在", true);
    return;
  }
  applyCreatorFilterSnapshot(preset.snapshot);
  toast(`已载入「${preset.name}」`);
}

function deleteSelectedCreatorFilterPreset() {
  const select = $("#creatorFilterPresetSelect");
  const id = select?.value;
  if (!id) {
    toast("请先选择要删除的方案", true);
    return;
  }
  const preset = loadCreatorFilterPresets().find((item) => item.id === id);
  if (preset?.builtin) {
    toast("内置方案不能删除", true);
    return;
  }
  const presets = loadCreatorFilterPresets().filter((item) => item.id !== id && !item.builtin);
  saveCreatorFilterPresetsToStorage(presets);
  renderCreatorFilterPresetSelect();
  toast("方案已删除");
}

function applyCreatorFilterFromBriefResult(data) {
  const form = $("#creatorFilterForm");
  if (!form || !data) return;
  const hard = data.hard || {};
  if (hard.platform) {
    const platform = normalizePlatformValue(hard.platform);
    form.elements.platform.value = PLATFORM_OPTIONS.includes(platform) ? platform : "";
  }
  if (hard.query) form.elements.query.value = hard.query;
  if (hard.maxPrice != null) form.elements.max_price.value = String(hard.maxPrice);
  if (hard.minLikeFanRatio != null) form.elements.min_like_fan_ratio.value = String(hard.minLikeFanRatio);
  if (hard.minRecentPostsCount != null) form.elements.min_recent_posts_count.value = String(hard.minRecentPostsCount);
  else if (hard.minLikeFanRatio != null && !form.elements.min_recent_posts_count.value) {
    form.elements.min_recent_posts_count.value = "10";
  }
  const narrativeBrief = $("#creatorFilterNarrativeBrief");
  const briefTop = $("#creatorFilterBriefInput");
  const briefText = data.brief?.raw_text || briefTop?.value || "";
  if (narrativeBrief && briefText) narrativeBrief.value = briefText;
  if (briefTop && briefText) briefTop.value = briefText;

  state.creatorFilterTags = {};
  const tags = data.tags || {};
  for (const group of CREATOR_TAG_FILTER_GROUPS) {
    const values = tags[group.id];
    if (Array.isArray(values) && values.length) state.creatorFilterTags[group.id] = [...values];
  }
  renderCreatorFilterTagFramework();
  const hasTags = Object.keys(state.creatorFilterTags).length > 0;
  const hasData =
    hard.minLikeFanRatio != null ||
    hard.maxPrice != null ||
    hard.minRecentPostsCount != null ||
    hard.minAvgLikes != null ||
    hard.maxSyncAgeDays != null;
  if (hasData) setCreatorFilterStep(3);
  else if (hasTags || hard.platform) setCreatorFilterStep(2);
  else setCreatorFilterStep(1);
  renderCreatorFilterResults();

  const hints = $("#creatorFilterBriefHints");
  if (hints) {
    const hintText = (data.hints || []).join(" · ");
    hints.textContent = hintText || "已从 Brief 解析并点亮标签";
    hints.classList.toggle("hidden", !hintText);
  }
  applyCreatorFilterBusinessFromData(data);
  loadCreatorFilterDeliverables(briefText || getCreatorFilterNarrativeBriefText());
  toast("Brief 已带入筛选");
}

async function applyCreatorFilterFromBriefText(text, options = {}) {
  const brief = String(text || "").trim();
  if (!brief && !options.parsedBrief) {
    toast("请先粘贴 Brief", true);
    return;
  }
  const btn = $("#creatorFilterBriefApplyBtn");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "解析中…";
  }
  try {
    const payload = options.parsedBrief ? { parsed_brief: options.parsedBrief, brief } : { brief };
    const data = await api("/api/creators/filter/from-brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    applyCreatorFilterFromBriefResult(data);
  } catch (error) {
    toast(error.message || "Brief 解析失败", true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "一键带入";
    }
  }
}

async function openCreatorFilterWithBrief(text, options = {}) {
  setView("creatorFilter");
  await ensureCreatorsLoaded().catch(() => {});
  const input = $("#creatorFilterBriefInput");
  const narrativeInput = $("#creatorFilterNarrativeBrief");
  if (input && text) input.value = text;
  if (narrativeInput && text) narrativeInput.value = text;
  await applyCreatorFilterFromBriefText(text, options);
  if (options.clientName && state.creatorFilterDeliverables?.client_card) {
    state.creatorFilterDeliverables.client_card.client_name = options.clientName;
    await renderCreatorFilterDeliverables(state.creatorFilterDeliverables);
  }
}

function renderCreatorFilterNarrativeAnalysis(data) {
  const node = $("#creatorFilterNarrativeAnalysis");
  if (!node) return;
  if (!data) {
    node.classList.add("hidden");
    node.innerHTML = "";
    return;
  }
  const tagLines = Object.entries(data.narrative_tags || data.tags || {})
    .map(([groupId, tags]) => {
      const group = CREATOR_TAG_FILTER_GROUPS.find((item) => item.id === groupId);
      return tags?.length ? `<li><strong>${escapeHTML(group?.label || groupId)}</strong>：${escapeHTML(tags.join("、"))}</li>` : "";
    })
    .filter(Boolean)
    .join("");
  node.classList.remove("hidden");
  node.innerHTML = `
    <div class="creator-filter-analysis-card">
      <div class="creator-filter-analysis-head">
        <strong>AI 叙事分析</strong>
        ${data.ai_used ? '<span class="status-pill ok">LLM</span>' : '<span class="status-pill">规则</span>'}
      </div>
      <p>${escapeHTML(data.summary || "已完成叙事标签建议。")}</p>
      ${data.narrative_strategy ? `<p class="meta">${escapeHTML(data.narrative_strategy)}</p>` : ""}
      ${tagLines ? `<ul class="creator-filter-analysis-tags">${tagLines}</ul>` : ""}
    </div>
  `;
  if (data.business) renderCreatorFilterBusinessType(data.business);
}

function applyCreatorFilterNarrativeAnalysis(data) {
  if (!data) return;
  const form = $("#creatorFilterForm");
  const hard = data.hard || {};
  if (form && hard.platform) {
    const platform = normalizePlatformValue(hard.platform);
    form.elements.platform.value = PLATFORM_OPTIONS.includes(platform) ? platform : form.elements.platform.value;
  }
  if (form && hard.query) form.elements.query.value = hard.query;
  if (form && hard.maxPrice != null) form.elements.max_price.value = String(hard.maxPrice);
  if (form && hard.minLikeFanRatio != null) form.elements.min_like_fan_ratio.value = String(hard.minLikeFanRatio);
  if (form && hard.minRecentPostsCount != null) form.elements.min_recent_posts_count.value = String(hard.minRecentPostsCount);

  state.creatorFilterTags = {};
  const tags = data.tags || {};
  for (const group of CREATOR_TAG_FILTER_GROUPS) {
    const values = tags[group.id];
    if (Array.isArray(values) && values.length) state.creatorFilterTags[group.id] = [...values];
  }
  state.creatorFilterNarrativeAnalysis = data;
  applyCreatorFilterBusinessFromData(data);
  renderCreatorFilterNarrativeAnalysis(data);
  const briefText = data.brief?.raw_text || getCreatorFilterNarrativeBriefText();
  loadCreatorFilterDeliverables(briefText);
  renderCreatorFilterTagFramework();
  setCreatorFilterStep(2);
  renderCreatorFilterResults();
}

async function runCreatorFilterNarrativeAnalyze() {
  const brief = getCreatorFilterNarrativeBriefText();
  const textTags = getCreatorFilterTextTagsValue();
  if (!brief) {
    toast("请先填写或上传 Brief", true);
    return;
  }
  const btn = $("#creatorFilterNarrativeAnalyzeBtn");
  const status = $("#creatorFilterNarrativeAnalyzeStatus");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "AI 分析中…";
  }
  if (status) status.textContent = "正在解析 Brief、文字标签并生成叙事筛选建议…";
  try {
    const criteria = getCreatorFilterCriteria();
    const data = await api("/api/creators/filter/narrative-analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brief,
        text_tags: textTags,
        platform: criteria.platform,
      }),
    });
    applyCreatorFilterNarrativeAnalysis(data);
    if (status) status.textContent = data.ai_used ? "AI 已给出叙事标签建议，请确认后进入数据验证。" : "规则引擎已给出叙事标签建议，可继续微调。";
    toast("叙事 AI 分析完成");
  } catch (error) {
    if (status) status.textContent = error.message || "分析失败";
    toast(error.message || "叙事 AI 分析失败", true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "启动 AI 分析";
    }
  }
}

async function refreshCreatorFilterRecommendations(creatorIds) {
  const brief = getCreatorFilterNarrativeBriefText();
  if (!brief || !creatorIds.length) {
    state.creatorFilterRecommendations = {};
    return;
  }
  try {
    const data = await api("/api/creators/filter/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brief,
        text_tags: getCreatorFilterTextTagsValue(),
        creator_ids: creatorIds,
      }),
    });
    const map = {};
    (data.items || []).forEach((item) => {
      map[item.creator_id] = item;
    });
    state.creatorFilterRecommendations = map;
  } catch {
    state.creatorFilterRecommendations = {};
  }
}

function getCreatorFilterRecommendationText(creatorId) {
  const item = state.creatorFilterRecommendations[creatorId];
  if (!item) return "";
  return item.reason_text || (item.reasons || []).join("；");
}

function isCreatorFilterSelected(creatorId) {
  return Boolean(state.creatorFilterSelected[creatorId]);
}

function setCreatorFilterSelected(creatorId, selected) {
  if (selected) state.creatorFilterSelected[creatorId] = true;
  else delete state.creatorFilterSelected[creatorId];
  const criteria = getCreatorFilterCriteria();
  const items = state.creators.filter((creator) => creatorMatchesFilter(creator, criteria));
  renderCreatorFilterExportBar(items);
}

function renderCreatorFilterExportBar(items = []) {
  const bar = $("#creatorFilterExportBar");
  const countNode = $("#creatorFilterSelectedCount");
  const selectAll = $("#creatorFilterSelectAll");
  if (!bar) return;
  const visibleIds = items.map((item) => item.creator_id);
  const selectedCount = visibleIds.filter((id) => isCreatorFilterSelected(id)).length;
  bar.classList.toggle("hidden", !items.length);
  if (countNode) countNode.textContent = `已选 ${selectedCount} 人`;
  if (selectAll) {
    selectAll.checked = visibleIds.length > 0 && selectedCount === visibleIds.length;
    selectAll.indeterminate = selectedCount > 0 && selectedCount < visibleIds.length;
  }
}

function exportSelectedCreatorFilterList() {
  const criteria = getCreatorFilterCriteria();
  const items = sortFilteredCreators(
    state.creators.filter((creator) => creatorMatchesFilter(creator, criteria)),
    criteria.sort,
  ).filter((creator) => isCreatorFilterSelected(creator.creator_id));
  if (!items.length) {
    toast("请先勾选要导出的博主", true);
    return;
  }
  const rows = items.map((creator) => {
    const rec = state.creatorFilterRecommendations[creator.creator_id] || {};
    return {
      达人: creator.name || "",
      平台: creator.platform || "",
      粉丝: creator.follower_count || 0,
      报价: creator.listed_price || 0,
      赞粉比: creator.like_fan_ratio || "",
      近期均赞: creator.avg_likes || 0,
      近N条样本: creator.recent_posts_count || 0,
      叙事角色: asTagList(creator.suitable_goals).join("、"),
      领域: asTagList(creator.industry_fit_tags).join("、"),
      推荐理由: rec.reason_text || getCreatorFilterRecommendationText(creator.creator_id) || "",
      推荐等级: rec.recommendation_level || "",
      匹配分: rec.match_score || "",
      名片刊例网页: creatorKitShareUrl(creator.creator_id),
      主页: creator.homepage_url || "",
    };
  });
  const csvHeader = Object.keys(rows[0]);
  const csvBody = rows
    .map((row) => csvHeader.map((key) => `"${String(row[key] ?? "").replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const csv = `\ufeff${csvHeader.join(",")}\n${csvBody}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `合作候选博主_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  toast(`已导出 ${rows.length} 位博主`);
}

function creatorSearchText(creator) {
  return [
    creator.name,
    creator.platform,
    creator.ai_summary,
    creator.bio,
    creator.narrative_position,
    ...asTagList(creator.industry_fit_tags),
    ...asTagList(creator.identity_tags),
    ...asTagList(creator.content_capability_tags),
    ...asTagList(creator.suitable_goals),
    ...asTagList(creator.suitable_stages),
    ...asTagList(creator.delivery_tags),
    ...asTagList(creator.personal_tags),
    ...asTagList(creator.risk_tags),
    ...asTagList(creator.budget_fit_tags),
    ...asTagList(creator.cooperation_brands),
    ...asTagList(creator.cooperation_formats),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function updateCreatorListSummary(shownCount, query = "") {
  const summary = $("#creatorListSummary");
  const sampleBtn = $("#creatorImportSampleBtn");
  const total = state.creators.length;
  if (summary) {
    if (!total) {
      summary.textContent = "达人库为空 · 可手动新增或导入示例数据";
    } else if (query) {
      summary.textContent = `搜索「${query}」· 显示 ${shownCount} / ${total} 位达人`;
    } else {
      summary.textContent = `共 ${total} 位达人 · 点击「详情」查看标签框架与画像`;
    }
  }
  if (sampleBtn) sampleBtn.classList.toggle("hidden", total > 0);
}

function creatorCardHtml(creator) {
      const tags = [
        ...asTagList(creator.industry_fit_tags),
        ...asTagList(creator.identity_tags),
        ...asTagList(creator.content_capability_tags),
        ...asTagList(creator.suitable_goals),
      ]
    .slice(0, 6)
    .map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`)
    .join("");
      const risks = asTagList(creator.risk_tags)
    .slice(0, 2)
    .map((tag) => `<span class="tag risk">${escapeHTML(tag)}</span>`)
    .join("");
  const initials = creator.name ? creator.name.slice(0, 2).toUpperCase() : "KOL";
  const avatar = creator.avatar_url
    ? `<img src="${escapeHTML(creator.avatar_url)}" alt="${escapeHTML(creator.name || "达人")}头像" loading="lazy" />`
    : `<span>${escapeHTML(initials)}</span>`;
  const ratioMetric = supportsLikeFanRatio(creator.platform)
    ? `<div><span>赞粉比</span><strong>${creator.like_fan_ratio ? formatLikeFanRatio(Number(creator.like_fan_ratio)) : "-"}</strong></div>`
    : `<div><span>互动率</span><strong>${creator.engagement_rate ? `${Math.round(Number(creator.engagement_rate) * 1000) / 10}%` : "-"}</strong></div>`;
  return `
    <article class="creator-card kol-profile-card open-creator-card" data-creator-id="${escapeHTML(creator.creator_id)}">
      <div class="kol-card-top">
        <div class="kol-card-avatar">${avatar}</div>
        <div>
          <div class="card-kicker">${escapeHTML(creator.platform || "未知平台")}</div>
          <h3>${escapeHTML(creator.name || "未命名达人")}</h3>
          <div class="meta">${escapeHTML(creator.region || creator.platform_user_id || "未补充地区 / ID")}</div>
        </div>
        <button class="secondary open-creator-btn" data-creator-id="${escapeHTML(creator.creator_id)}" type="button">详情</button>
      </div>
      <div class="kol-card-metrics">
        <div><span>粉丝</span><strong>${fmtNumber(creator.follower_count)}</strong></div>
        <div><span>报价</span><strong>${fmtNumber(creator.listed_price)}</strong></div>
        ${ratioMetric}
      </div>
      <p>${escapeHTML(creator.ai_summary || creator.bio || "待生成画像")}</p>
      <div class="kol-card-links">
        ${creator.homepage_url ? `<a class="text-btn" href="${escapeHTML(creator.homepage_url)}" target="_blank" rel="noreferrer">主页</a>` : '<span class="meta">未填主页</span>'}
        ${creator.contact ? `<span class="meta">${escapeHTML(creator.contact)}</span>` : ""}
      </div>
      <div class="tag-list">${tags}${risks}</div>
    </article>
  `;
}

function creatorSyncAgeDays(creator) {
  const raw = String(creator.last_synced_at || "").trim();
  if (!raw) return null;
  const synced = new Date(raw.includes("T") ? raw : `${raw}T00:00:00`);
  if (Number.isNaN(synced.getTime())) return null;
  const diffMs = Date.now() - synced.getTime();
  if (diffMs < 0) return 0;
  return Math.floor(diffMs / 86400000);
}

function formatCreatorSyncAgeLabel(creator) {
  const age = creatorSyncAgeDays(creator);
  if (age == null) return "更新时间待补";
  if (age === 0) return "今天更新";
  return `${age} 天前更新`;
}

function creatorMatchedFilterTags(creator, tagCriteria) {
  const matched = [];
  for (const { fields, tags } of Object.values(tagCriteria || {})) {
    const creatorTags = new Set(creatorTagsFromFields(creator, fields));
    tags.forEach((tag) => {
      if (creatorTags.has(tag)) matched.push(tag);
    });
  }
  return matched;
}

function creatorFilterCardHtml(creator, criteria) {
  const matchedTags = creatorMatchedFilterTags(creator, criteria.tagCriteria);
  const narrativeText =
    matchedTags.slice(0, 4).join(" · ") ||
    String(creator.narrative_position || "").trim() ||
    "叙事标签待补";
  const recommendation = getCreatorFilterRecommendationText(creator.creator_id);
  const recMeta = state.creatorFilterRecommendations[creator.creator_id];
  const recentPosts = Number(creator.recent_posts_count || 0);
  const avgLikes = Number(creator.avg_likes || 0);
  const ratioText = supportsLikeFanRatio(creator.platform)
    ? creator.like_fan_ratio
      ? `赞粉比 ${formatLikeFanRatio(Number(creator.like_fan_ratio))}`
      : "赞粉比待补"
    : creator.engagement_rate
      ? `互动率 ${Math.round(Number(creator.engagement_rate) * 1000) / 10}%`
      : "互动率待补";
  const recentDataText = [
    ratioText,
    recentPosts ? `近 ${recentPosts} 条样本` : "近期条数待补",
    avgLikes ? `均赞 ${fmtNumber(avgLikes)}` : "",
    formatCreatorSyncAgeLabel(creator),
  ]
    .filter(Boolean)
    .join(" · ");
  const kitUrl = creatorKitShareUrl(creator.creator_id);
  const tags = [
    ...asTagList(creator.industry_fit_tags),
    ...asTagList(creator.identity_tags),
    ...asTagList(creator.content_capability_tags),
    ...asTagList(creator.suitable_goals),
  ]
    .slice(0, 5)
    .map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`)
    .join("");
  const risks = asTagList(creator.risk_tags)
    .slice(0, 2)
    .map((tag) => `<span class="tag risk">${escapeHTML(tag)}</span>`)
    .join("");
  const initials = creator.name ? creator.name.slice(0, 2).toUpperCase() : "KOL";
  const avatar = creator.avatar_url
    ? `<img src="${escapeHTML(creator.avatar_url)}" alt="${escapeHTML(creator.name || "达人")}头像" loading="lazy" />`
    : `<span>${escapeHTML(initials)}</span>`;
  const checked = isCreatorFilterSelected(creator.creator_id) ? " checked" : "";
  return `
    <article class="creator-card kol-profile-card creator-filter-card open-creator-card" data-creator-id="${escapeHTML(creator.creator_id)}">
      <div class="creator-filter-card-toolbar">
        <label class="creator-filter-select-wrap">
          <input class="creator-filter-select" type="checkbox" data-creator-id="${escapeHTML(creator.creator_id)}"${checked} />
          <span>纳入导出</span>
        </label>
        ${recMeta?.recommendation_level ? `<span class="status-pill ok">${escapeHTML(recMeta.recommendation_level)}</span>` : '<span class="status-pill ok">合作候选</span>'}
      </div>
      <div class="kol-card-top">
        <div class="kol-card-avatar">${avatar}</div>
        <div>
          <div class="card-kicker">${escapeHTML(creator.platform || "未知平台")}</div>
          <h3>${escapeHTML(creator.name || "未命名达人")}</h3>
          <div class="meta">${escapeHTML(creator.region || creator.platform_user_id || "未补充地区 / ID")}</div>
        </div>
        <button class="secondary open-creator-btn" data-creator-id="${escapeHTML(creator.creator_id)}" type="button">详情</button>
      </div>
      <div class="creator-filter-judgment">
        <div class="creator-filter-judgment-row narrative">
          <span>叙事匹配</span>
          <strong>${escapeHTML(narrativeText)}</strong>
        </div>
        <div class="creator-filter-judgment-row data">
          <span>近期流量信号</span>
          <strong>${escapeHTML(recentDataText)}</strong>
        </div>
        ${recommendation ? `<div class="creator-filter-judgment-row reason"><span>推荐理由</span><strong>${escapeHTML(recommendation)}</strong></div>` : ""}
      </div>
      <div class="kol-card-metrics">
        <div><span>粉丝</span><strong>${fmtNumber(creator.follower_count)}</strong></div>
        <div><span>报价</span><strong>${fmtNumber(creator.listed_price)}</strong></div>
        <div><span>均赞</span><strong>${avgLikes ? fmtNumber(avgLikes) : "-"}</strong></div>
      </div>
      <p>${escapeHTML(creator.ai_summary || creator.bio || "待生成画像")}</p>
      <div class="kol-card-links">
        ${kitUrl ? `<a class="text-btn" href="${escapeHTML(kitUrl)}" target="_blank" rel="noreferrer">名片刊例</a>` : ""}
        ${creator.homepage_url ? `<a class="text-btn" href="${escapeHTML(creator.homepage_url)}" target="_blank" rel="noreferrer">主页</a>` : ""}
      </div>
      <div class="tag-list">${tags}${risks}</div>
    </article>
  `;
}

function parseCreatorFilterNumber(value) {
  if (value === "" || value == null) return null;
  const number = Number(value);
  return Number.isNaN(number) ? null : number;
}

function getCreatorFilterCriteria() {
  const form = $("#creatorFilterForm");
  if (!form) return { sort: "follower_desc", query: "", platform: "", tagCriteria: {} };
  return {
    platform: String(form.elements.platform?.value || "").trim(),
    query: String(form.elements.query?.value || "")
      .toLowerCase()
      .trim(),
    minFollowers: parseCreatorFilterNumber(form.elements.min_followers?.value),
    maxFollowers: parseCreatorFilterNumber(form.elements.max_followers?.value),
    maxPrice: parseCreatorFilterNumber(form.elements.max_price?.value),
    minLikeFanRatio: parseCreatorFilterNumber(form.elements.min_like_fan_ratio?.value),
    maxLikeFanRatio: parseCreatorFilterNumber(form.elements.max_like_fan_ratio?.value),
    minEngagement: parseCreatorFilterNumber(form.elements.min_engagement?.value),
    minAvgLikes: parseCreatorFilterNumber(form.elements.min_avg_likes?.value),
    minRecentPostsCount: parseCreatorFilterNumber(form.elements.min_recent_posts_count?.value),
    maxSyncAgeDays: parseCreatorFilterNumber(form.elements.max_sync_age_days?.value),
    sort: form.elements.sort?.value || "like_fan_ratio_desc",
    tagCriteria: getCreatorFilterTagCriteria(),
  };
}

function creatorMatchesPlatformFilter(creator, criteria) {
  if (criteria.platform && normalizePlatformValue(creator.platform) !== criteria.platform) return false;
  if (criteria.query && !creatorSearchText(creator).includes(criteria.query)) return false;
  return true;
}

function creatorMatchesNarrativeFilter(creator, criteria) {
  if (!creatorMatchesPlatformFilter(creator, criteria)) return false;
  if (criteria.tagCriteria && Object.keys(criteria.tagCriteria).length && !creatorMatchesTagFilters(creator, criteria.tagCriteria)) {
    return false;
  }
  return true;
}

function creatorMatchesDataFilter(creator, criteria) {
  const followers = Number(creator.follower_count || 0);
  if (criteria.minFollowers != null && followers < criteria.minFollowers) return false;
  if (criteria.maxFollowers != null && followers > criteria.maxFollowers) return false;
  const price = Number(creator.listed_price || 0);
  if (criteria.maxPrice != null && price > criteria.maxPrice) return false;
  if (criteria.minLikeFanRatio != null || criteria.maxLikeFanRatio != null) {
    const ratio = Number(creator.like_fan_ratio);
    if (criteria.minLikeFanRatio != null && (Number.isNaN(ratio) || ratio < criteria.minLikeFanRatio)) return false;
    if (criteria.maxLikeFanRatio != null && (Number.isNaN(ratio) || ratio > criteria.maxLikeFanRatio)) return false;
  }
  if (criteria.minEngagement != null) {
    const rate = Number(creator.engagement_rate || 0) * 100;
    if (rate < criteria.minEngagement) return false;
  }
  const avgLikes = Number(creator.avg_likes || 0);
  if (criteria.minAvgLikes != null && avgLikes < criteria.minAvgLikes) return false;
  const recentPosts = Number(creator.recent_posts_count || 0);
  if (criteria.minRecentPostsCount != null && recentPosts < criteria.minRecentPostsCount) return false;
  if (criteria.maxSyncAgeDays != null) {
    const syncAge = creatorSyncAgeDays(creator);
    if (syncAge == null || syncAge > criteria.maxSyncAgeDays) return false;
  }
  return true;
}

function getCreatorFilterFunnel() {
  const total = state.creators.length;
  const criteria = getCreatorFilterCriteria();
  const platformCriteria = { platform: criteria.platform, query: criteria.query };
  const afterPlatform = state.creators.filter((creator) => creatorMatchesPlatformFilter(creator, platformCriteria));
  const afterNarrative = afterPlatform.filter((creator) => creatorMatchesNarrativeFilter(creator, criteria));
  const finalists = afterNarrative.filter((creator) => creatorMatchesDataFilter(creator, criteria));
  return {
    total,
    afterPlatform: afterPlatform.length,
    afterNarrative: afterNarrative.length,
    finalists: finalists.length,
  };
}

function renderCreatorFilterFunnel() {
  const node = $("#creatorFilterFunnel");
  if (!node) return;
  const funnel = getCreatorFilterFunnel();
  const step = state.creatorFilterStep || 1;
  const nodes = [
    { id: "total", label: "全库", count: funnel.total, step: 0 },
    { id: "platform", label: "① 平台", count: funnel.afterPlatform, step: 1 },
    { id: "narrative", label: "② 叙事", count: funnel.afterNarrative, step: 2 },
    { id: "data", label: "③ 数据", count: funnel.finalists, step: 3 },
  ];
  node.innerHTML = `
    <div class="creator-filter-funnel-head">
      <strong>筛选漏斗</strong>
      <span class="meta">先平台、再叙事、最后看近期流量信号</span>
    </div>
    <div class="creator-filter-funnel-track">
      ${nodes
        .map((item, index) => {
          const active = item.step === step || (step === 3 && item.id === "data");
          const arrow = index < nodes.length - 1 ? '<span class="creator-filter-funnel-arrow">→</span>' : "";
          return `
            <button type="button" class="creator-filter-funnel-node${active ? " active" : ""}" data-filter-step="${item.step || 1}">
              <span>${escapeHTML(item.label)}</span>
              <strong>${item.count}</strong>
            </button>
            ${arrow}
          `;
        })
        .join("")}
    </div>
  `;
}

function renderCreatorFilterStepper() {
  const node = $("#creatorFilterStepper");
  if (!node) return;
  const step = state.creatorFilterStep || 1;
  const steps = [
    { id: 1, label: "平台", hint: "先定渠道" },
    { id: 2, label: "叙事", hint: "能否纳入商业叙事" },
    { id: 3, label: "数据", hint: "近期有没有流量" },
  ];
  node.innerHTML = steps
    .map((item) => {
      const active = item.id === step;
      const done = item.id < step;
      return `
        <button type="button" class="creator-filter-step-tab${active ? " active" : ""}${done ? " done" : ""}" data-filter-step="${item.id}">
          <span>${item.id}</span>
          <div>
            <strong>${escapeHTML(item.label)}</strong>
            <em>${escapeHTML(item.hint)}</em>
          </div>
        </button>
      `;
    })
    .join("");
  $$(".creator-filter-step-panel").forEach((panel) => {
    panel.classList.toggle("active", Number(panel.dataset.step) === step);
  });
}

function setCreatorFilterStep(step) {
  const next = Math.max(1, Math.min(3, Number(step) || 1));
  state.creatorFilterStep = next;
  renderCreatorFilterStepper();
  renderCreatorFilterFunnel();
  const panel = $(`#creatorFilterStep${next}`);
  panel?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function formatCreatorFilterSummary(items, total, criteria, funnel) {
  const tagCount = Object.values(state.creatorFilterTags).reduce((sum, tags) => sum + (tags?.length || 0), 0);
  const parts = [`入围 ${items.length}${total ? ` / ${total}` : ""} 人`];
  if (funnel) {
    parts.push(`漏斗 ${funnel.afterPlatform}→${funnel.afterNarrative}→${funnel.finalists}`);
  }
  if (criteria.platform) parts.push(`平台=${criteria.platform}`);
  if (tagCount) parts.push(`叙事标签 ${tagCount} 项`);
  if (criteria.minLikeFanRatio != null) parts.push(`赞粉比≥${criteria.minLikeFanRatio}`);
  if (criteria.minRecentPostsCount != null) parts.push(`近${criteria.minRecentPostsCount}条样本`);
  if (criteria.maxSyncAgeDays != null) parts.push(`更新≤${criteria.maxSyncAgeDays}天`);
  return parts.join(" · ");
}

function creatorMatchesFilter(creator, criteria) {
  return creatorMatchesNarrativeFilter(creator, criteria) && creatorMatchesDataFilter(creator, criteria);
}

function sortFilteredCreators(items, sortKey) {
  const sorted = [...items];
  const num = (value) => Number(value) || 0;
  switch (sortKey) {
    case "follower_asc":
      return sorted.sort((a, b) => num(a.follower_count) - num(b.follower_count));
    case "like_fan_ratio_desc":
      return sorted.sort((a, b) => num(b.like_fan_ratio) - num(a.like_fan_ratio));
    case "like_fan_ratio_asc":
      return sorted.sort((a, b) => num(a.like_fan_ratio) - num(b.like_fan_ratio));
    case "engagement_desc":
      return sorted.sort((a, b) => num(b.engagement_rate) - num(a.engagement_rate));
    case "avg_likes_desc":
      return sorted.sort((a, b) => num(b.avg_likes) - num(a.avg_likes));
    case "price_asc":
      return sorted.sort((a, b) => num(a.listed_price) - num(b.listed_price));
    case "price_desc":
      return sorted.sort((a, b) => num(b.listed_price) - num(a.listed_price));
    case "follower_desc":
    default:
      return sorted.sort((a, b) => num(b.follower_count) - num(a.follower_count));
  }
}

function renderCreatorFilterResults() {
  const list = $("#creatorFilterList");
  const summary = $("#creatorFilterSummary");
  const listTitle = $("#creatorFilterListTitle");
  if (!list) return;
  const criteria = getCreatorFilterCriteria();
  const funnel = getCreatorFilterFunnel();
  const total = state.creators.length;
  renderCreatorFilterFunnel();
  const items = sortFilteredCreators(
    state.creators.filter((creator) => creatorMatchesFilter(creator, criteria)),
    criteria.sort,
  );
  if (summary) {
    summary.textContent = total ? formatCreatorFilterSummary(items, total, criteria, funnel) : "达人库暂无数据";
  }
  if (listTitle) {
    listTitle.textContent =
      items.length > 0
        ? `合作候选名单 · ${items.length} 人（投前判断完成，可勾选导出）`
        : "合作候选名单";
  }
  if (!items.length) {
    renderCreatorFilterExportBar([]);
    const step = state.creatorFilterStep || 1;
    const hints = [
      "全库暂无数据，先去达人库导入。",
      "没有符合平台条件的达人，换平台或清空平台筛选。",
      "叙事标签过严，放宽标签或先只保留领域/叙事角色。",
      "数据门槛过高，降低赞粉比、均赞、更新天数或近期样本条数要求。",
    ];
    list.innerHTML = emptyState(
      total ? "当前暂无入围达人" : "暂无达人数据",
      total ? hints[step] || hints[3] : "先导入 Excel / CSV 或使用示例数据启动达人雷达。",
    );
    return;
  }
  renderCreatorFilterExportBar(items);
  list.innerHTML = items.map((creator) => creatorFilterCardHtml(creator, criteria)).join("");
  refreshCreatorFilterRecommendations(items.map((creator) => creator.creator_id)).then(() => {
    if ($("#creatorFilterList")) {
      list.innerHTML = items.map((creator) => creatorFilterCardHtml(creator, criteria)).join("");
    }
  });
}

function setCreatorListLoading(loading) {
  const list = $("#creatorList");
  if (!list) return;
  list.dataset.loading = loading ? "true" : "false";
  if (loading && !state.creators.length) {
    list.innerHTML = emptyState("正在加载达人库…", "首次打开会稍慢，数据返回后会自动展示。");
  }
}

function bindModalDismiss(modal, selector, closeFn) {
  modal?.addEventListener("click", (event) => {
    if (event.target.closest(selector)) closeFn();
  });
}

function bindModalEscape(closeChecks) {
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    for (const [modalId, closeFn] of closeChecks) {
      const modal = $(modalId);
      if (modal && !modal.classList.contains("hidden")) {
        event.preventDefault();
        closeFn();
        return;
      }
    }
  });
}

function showCreatorModalLoading(creatorId = "") {
  $("#creatorModal")?.classList.remove("hidden");
  $("#creatorModalTitle").textContent = "加载达人详情…";
  $("#creatorModalMeta").textContent = creatorId || "请稍候";
  const summary = $("#creatorProfileSummary");
  if (summary) summary.textContent = "正在拉取档案、标签与证据资产。";
}

function renderCreators() {
  const query = ($("#creatorSearch")?.value || "").trim();
  const queryKey = query.toLowerCase();
  const list = $("#creatorList");
  if (!list) return;
  const items = (state.creators || []).filter((creator) => !queryKey || creatorSearchText(creator).includes(queryKey));
  updateCreatorListSummary(items.length, query);
  if (!items.length) {
    const total = state.creators.length;
    list.innerHTML = emptyState(
      total ? "没有匹配的达人" : "暂无达人数据",
      total ? "试试换个关键词，或清空搜索框。" : "点击「+ 新增达人」录入，或使用「导入示例达人」快速体验。",
    );
    return;
  }
  list.innerHTML = items.map((creator) => creatorCardHtml(creator)).join("");
}

function renderCreatorProfileHeader(creator) {
  const avatar = $("#creatorProfileAvatar");
  const name = $("#creatorProfileName");
  const kicker = $("#creatorProfileKicker");
  const summary = $("#creatorProfileSummary");
  const links = $("#creatorProfileLinks");
  const scoreboard = $("#creatorProfileScoreboard");
  if (avatar) {
    avatar.innerHTML = creator.avatar_url
      ? `<img src="${escapeHTML(creator.avatar_url)}" alt="${escapeHTML(creator.name || "达人")}头像" />`
      : `<span>${escapeHTML((creator.name || "KOL").slice(0, 2).toUpperCase())}</span>`;
  }
  if (name) name.textContent = creator.name || "未命名达人";
  if (kicker) kicker.textContent = `${creator.platform || "未知平台"} · ${creator.creator_id || ""}`;
  const narrativeNode = $("#creatorProfileNarrative");
  if (narrativeNode) {
    const narrative = String(creator.narrative_position || "").trim();
    narrativeNode.textContent = narrative;
    narrativeNode.classList.toggle("hidden", !narrative);
  }
  if (summary) summary.textContent = creator.ai_summary || creator.bio || "暂无 AI 摘要，补充主页、案例、截图或内部备注后可重新画像。";
  if (links) {
    links.innerHTML = [
      creator.homepage_url ? `<a class="secondary" href="${escapeHTML(creator.homepage_url)}" target="_blank" rel="noreferrer">打开主页</a>` : "",
      creator.avatar_url ? `<a class="secondary" href="${escapeHTML(creator.avatar_url)}" target="_blank" rel="noreferrer">查看头像</a>` : "",
      creator.contact ? `<span>${escapeHTML(creator.contact)}</span>` : "",
    ]
      .filter(Boolean)
      .join("");
  }
  if (scoreboard) {
    const metrics = [
      ["粉丝", fmtNumber(creator.follower_count)],
      ["报价", fmtNumber(creator.listed_price)],
    ];
    if (supportsLikeFanRatio(creator.platform)) {
      metrics.push([
        "赞粉比",
        creator.like_fan_ratio ? formatLikeFanRatio(Number(creator.like_fan_ratio)) : "-",
      ]);
    } else {
      metrics.push([
        "互动率",
        creator.engagement_rate ? `${Math.round(Number(creator.engagement_rate) * 1000) / 10}%` : "-",
      ]);
    }
    metrics.push(["平均点赞", fmtNumber(creator.avg_likes)]);
    scoreboard.innerHTML = metrics
      .map(([label, value]) => `<div><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong></div>`)
      .join("");
  }
  const aiSummary = $("#creatorAiSummary");
  if (aiSummary) aiSummary.textContent = creator.ai_summary || "暂无 AI 摘要。保存字段并重新画像后，这里会变成可用于 Brief 匹配的判断。";
}

function emptyState(title, detail = "") {
  return `
    <div class="empty-state">
      <strong>${escapeHTML(title)}</strong>
      <span>${escapeHTML(detail)}</span>
    </div>
  `;
}

function userById(userId) {
  return state.authUsers.find((user) => user.user_id === userId);
}

function clientById(clientId) {
  return state.authClients.find((client) => client.client_id === clientId);
}

function proposalById(proposalId) {
  return state.collabProposals.find((proposal) => proposal.proposal_id === proposalId);
}

function renderRolePill(role) {
  const label = escapeHTML(role || "viewer");
  const tone = String(role || "").includes("admin") || String(role || "").includes("owner") ? "hot" : String(role || "").includes("viewer") ? "quiet" : "cool";
  return `<span class="role-pill ${tone}">${label}</span>`;
}

function renderOrganization() {
  renderOrgAdminNotice();
  renderOrgMetrics();
  renderInternalUsers();
  renderClientAccounts();
  renderOrgSelects();
  renderProjectAccessTable();
  renderRuleConfig();
  renderOpenClawAdmin();
}

function isCurrentUserAdmin() {
  const user = state.currentIdentity?.user;
  return user?.user_type === "internal" && user?.role === "admin";
}

function renderOrgAdminNotice() {
  const node = $("#orgAdminNotice");
  const internalForm = $("#internalUserForm");
  if (internalForm) {
    Array.from(internalForm.querySelectorAll("input, select, button")).forEach((field) => {
      field.disabled = !isCurrentUserAdmin();
    });
  }
  if (!node) return;
  if (isCurrentUserAdmin()) {
    node.innerHTML = `
      <strong>Admin mode</strong>
      <span>你可以创建员工、甲方账号、重置密码、启用/禁用账号并分配项目访问。</span>
    `;
    node.dataset.tone = "ok";
  } else {
    node.innerHTML = `
      <strong>Read-only</strong>
      <span>当前账号不是 admin，只能查看部分组织信息；员工管理、重置密码和账号状态调整需要 admin。</span>
    `;
    node.dataset.tone = "warn";
  }
}

function renderOrgMetrics() {
  const node = $("#orgMetrics");
  if (!node) return;
  const internalCount = state.authUsers.filter((user) => user.user_type === "internal").length;
  const clientUserCount = state.authUsers.filter((user) => user.user_type === "client").length;
  node.innerHTML = `
    <div class="metric">
      <span>内部成员</span>
      <strong>${fmtNumber(internalCount)}</strong>
    </div>
    <div class="metric">
      <span>甲方客户</span>
      <strong>${fmtNumber(state.authClients.length)}</strong>
    </div>
    <div class="metric">
      <span>甲方账号</span>
      <strong>${fmtNumber(clientUserCount)}</strong>
    </div>
    <div class="metric">
      <span>项目授权</span>
      <strong>${fmtNumber(state.projectAccess.length)}</strong>
    </div>
  `;
}

function renderInternalUsers() {
  const list = $("#internalUserList");
  if (!list) return;
  const users = state.authUsers.filter((user) => user.user_type === "internal");
  const canAdmin = isCurrentUserAdmin();
  list.innerHTML = users.length
    ? users
        .map(
          (user) => `
            <article class="org-card">
              <div>
                <strong>${escapeHTML(user.name || user.email)}</strong>
                <span>${escapeHTML(user.email)}</span>
              </div>
              <div class="org-card-side">
                ${renderRolePill(user.role)}
                <span class="meta">${escapeHTML(user.status || "active")}</span>
                ${
                  canAdmin
                    ? `<div class="org-actions">
                        <button class="secondary mini-action" data-auth-action="toggle-user" data-user-id="${escapeHTML(user.user_id)}" data-next-status="${user.status === "disabled" ? "active" : "disabled"}" type="button">${user.status === "disabled" ? "启用" : "禁用"}</button>
                        <button class="secondary mini-action" data-auth-action="reset-password" data-user-id="${escapeHTML(user.user_id)}" type="button">重置密码</button>
                      </div>`
                    : ""
                }
              </div>
            </article>
          `
        )
        .join("")
    : emptyState("暂无内部成员", "创建第一个 admin 后可继续添加团队成员。");
}

function renderClientAccounts() {
  const list = $("#clientAccountList");
  if (!list) return;
  const canAdmin = isCurrentUserAdmin();
  list.innerHTML = state.authClients.length
    ? state.authClients
        .map((client) => {
          const members = (client.members || [])
            .map((member) => {
              const user = userById(member.user_id);
              return `
                <span class="mini-member ${user?.status === "disabled" ? "disabled" : ""}">
                  <span>${escapeHTML(user?.name || user?.email || member.user_id)}</span>
                  ${renderRolePill(member.role)}
                  ${user ? `<em>${escapeHTML(user.status || "active")}</em>` : ""}
                  ${
                    canAdmin && user
                      ? `<button class="secondary mini-action" data-auth-action="toggle-user" data-user-id="${escapeHTML(user.user_id)}" data-next-status="${user.status === "disabled" ? "active" : "disabled"}" type="button">${user.status === "disabled" ? "启用" : "禁用"}</button>
                         <button class="secondary mini-action" data-auth-action="reset-password" data-user-id="${escapeHTML(user.user_id)}" type="button">重置密码</button>`
                      : ""
                  }
                </span>
              `;
            })
            .join("");
          return `
            <article class="org-card client">
              <div>
                <strong>${escapeHTML(client.name)}</strong>
                <span>${escapeHTML(client.company || "未填写公司主体")}</span>
                <div class="member-strip">${members || '<span class="meta">暂无甲方账号</span>'}</div>
              </div>
              <div class="org-card-side">
                <span class="meta">${escapeHTML(client.status || "active")}</span>
              </div>
            </article>
          `;
        })
        .join("")
    : emptyState("暂无客户", "先创建客户公司，再给甲方开账号。");
}

function renderOrgSelects() {
  const clients = state.authClients;
  const clientUsers = state.authUsers.filter((user) => user.user_type === "client");
  const proposals = state.collabProposals;
  const clientOptions = clients.map((client) => `<option value="${escapeHTML(client.client_id)}">${escapeHTML(client.name)}</option>`).join("");
  const userOptions = clientUsers
    .map((user) => {
      const client = clientById(user.client_id);
      const suffix = client ? ` · ${client.name}` : "";
      return `<option value="${escapeHTML(user.user_id)}" data-client-id="${escapeHTML(user.client_id || "")}">${escapeHTML(user.name || user.email)}${escapeHTML(suffix)}</option>`;
    })
    .join("");
  const proposalOptions = proposals
    .map((proposal) => `<option value="${escapeHTML(proposal.proposal_id)}">${escapeHTML(proposal.project_name)} · ${escapeHTML(proposal.client_name)}</option>`)
    .join("");

  const clientUserClientSelect = $("#clientUserClientSelect");
  const accessClientSelect = $("#accessClientSelect");
  const accessUserSelect = $("#accessUserSelect");
  const accessProposalSelect = $("#accessProposalSelect");
  if (clientUserClientSelect) clientUserClientSelect.innerHTML = clientOptions || '<option value="">先创建客户</option>';
  if (accessClientSelect) accessClientSelect.innerHTML = clientOptions || '<option value="">先创建客户</option>';
  if (accessUserSelect) accessUserSelect.innerHTML = userOptions || '<option value="">先创建甲方账号</option>';
  if (accessProposalSelect) accessProposalSelect.innerHTML = proposalOptions || '<option value="">先创建协作方案</option>';
}

function renderProjectAccessTable() {
  const tbody = $("#projectAccessTable tbody");
  if (!tbody) return;
  tbody.innerHTML = state.projectAccess.length
    ? state.projectAccess
        .map((access) => {
          const user = userById(access.user_id);
          const client = clientById(access.client_id || user?.client_id);
          const proposal = proposalById(access.proposal_id);
          return `
            <tr>
              <td>
                <strong>${escapeHTML(user?.name || user?.email || access.user_id)}</strong>
                <div class="meta">${escapeHTML(user?.email || "")}</div>
              </td>
              <td>${escapeHTML(client?.name || access.client_id || "-")}</td>
              <td>
                <strong>${escapeHTML(proposal?.project_name || access.proposal_id || "-")}</strong>
                <div class="meta">${escapeHTML(proposal?.client_name || "")}</div>
              </td>
              <td>${(access.permissions || []).map((item) => `<span class="tag">${escapeHTML(item)}</span>`).join("")}</td>
              <td>${escapeHTML(access.created_at || "-")}</td>
            </tr>
          `;
        })
        .join("")
    : `<tr><td colspan="5">${emptyState("暂无项目授权", "选择甲方账号和协作方案后即可授权。")}</td></tr>`;
}

function renderRuleConfig() {
  const editor = $("#ruleConfigEditor");
  const meta = $("#ruleConfigMeta");
  const canAdmin = isCurrentUserAdmin();
  if (editor) {
    editor.disabled = !canAdmin;
    editor.value = state.ruleConfig ? JSON.stringify(state.ruleConfig, null, 2) : "";
    editor.placeholder = canAdmin ? "规则配置加载中..." : "只有 admin 可以查看和编辑规则配置。";
  }
  ["reloadRuleConfigBtn", "resetRuleConfigBtn", "saveRuleConfigBtn"].forEach((id) => {
    const button = $(`#${id}`);
    if (button) button.disabled = !canAdmin;
  });
  if (!meta) return;
  if (!canAdmin) {
    meta.textContent = "当前账号不是 admin，规则工作台不可编辑。";
    return;
  }
  const config = state.ruleConfig || {};
  const creatorPatterns = Object.keys(config.creator_symbolic_patterns || {}).length;
  const briefKeywords = Object.keys(config.brief_keywords || {}).length;
  const categoryLabels = Object.keys(config.category_labels || {}).length;
  const brandArchetypes = Object.keys(config.brand_archetypes || {}).length;
  meta.textContent = `已加载 ${creatorPatterns} 组达人符号规则 · ${briefKeywords} 组 Brief 激活词 · ${categoryLabels} 个分类名称 · ${brandArchetypes} 组品牌 archetype`;
}

function renderOpenClawAdmin() {
  const form = $("#openClawConfigForm");
  const meta = $("#openClawConfigMeta");
  const bindingSelect = $("#openClawBindingUserSelect");
  const bindingList = $("#openClawBindingList");
  const diagnosticsPanel = $("#openClawDiagnosticsPanel");
  const canAdmin = isCurrentUserAdmin();
  const config = state.openClaw?.config || {};
  const status = state.openClaw?.status || {};
  if (form) {
    form.elements.enabled.checked = Boolean(config.enabled);
    form.elements.gateway_url.value = config.gateway_url || "";
    form.elements.control_ui_url.value = config.control_ui_url || "";
    form.elements.default_agent_id.value = config.default_agent_id || "kolness_default";
    form.elements.proxy_base_path.value = config.proxy_base_path || "/openclaw";
    form.elements.admin_token.value = "";
    Array.from(form.querySelectorAll("input, select, button")).forEach((field) => {
      field.disabled = !canAdmin;
    });
  }
  ["reloadOpenClawConfigBtn", "saveOpenClawConfigBtn"].forEach((id) => {
    const button = $(`#${id}`);
    if (button) button.disabled = !canAdmin;
  });
  const bindingForm = $("#openClawBindingForm");
  if (bindingForm) {
    Array.from(bindingForm.querySelectorAll("input, select, button")).forEach((field) => {
      field.disabled = !canAdmin;
    });
  }
  if (bindingSelect) {
    const internalUsers = state.authUsers.filter((user) => user.user_type === "internal");
    bindingSelect.innerHTML = internalUsers
      .map((user) => `<option value="${escapeHTML(user.user_id)}">${escapeHTML(user.name || user.email)} · ${escapeHTML(user.role)}</option>`)
      .join("");
  }
  if (meta) {
    if (!canAdmin) {
      meta.textContent = "当前账号不是 admin，不能修改 OpenClaw 配置。";
    } else {
      meta.textContent = `${status.enabled ? "已启用" : "未启用"} · ${status.configured ? "Gateway 已配置" : "缺 Gateway"} · 默认 Agent ${escapeHTML(config.default_agent_id || "kolness_default")}`;
    }
  }
  if (bindingList) {
    const bindings = state.openClaw?.bindings || [];
    bindingList.innerHTML = bindings.length
      ? bindings
          .map((binding) => {
            const user = userById(binding.user_id);
            return `
              <article class="org-card">
                <div>
                  <strong>${escapeHTML(user?.name || user?.email || binding.user_id)}</strong>
                  <span>${escapeHTML(binding.openclaw_agent_id || "-")}</span>
                </div>
                <div class="org-card-side">
                  ${renderRolePill(binding.status || "active")}
                  <span class="meta">${escapeHTML(binding.openclaw_session_id || "no session")}</span>
                </div>
              </article>
            `;
          })
          .join("")
      : emptyState("暂无 OpenClaw 绑定", "保存配置后，可以给每个内部员工绑定自己的 OpenClaw agent。");
  }
  renderOpenClawDiagnostics(diagnosticsPanel);
}

function renderOpenClawDiagnostics(target) {
  if (!target) return;
  const diagnostics = state.openClawDiagnostics;
  if (!diagnostics) {
    target.innerHTML = emptyState("暂无 OpenClaw 诊断", "只有内部账号可读取 diagnostics；admin 进入后会显示配置、绑定、工具和最近运行状态。");
    return;
  }
  const checks = diagnostics.checks || {};
  const status = diagnostics.status || {};
  const issues = checks.issues || [];
  const recent = diagnostics.run_summary?.recent || [];
  const metricItems = [
    ["enabled", checks.enabled ? "ON" : "OFF"],
    ["gateway", checks.gateway_url ? "ready" : "missing"],
    ["tools", fmtNumber(checks.tool_count || 0)],
    ["bindings", `${fmtNumber(checks.active_binding_count || 0)}/${fmtNumber(checks.binding_count || 0)}`],
    ["runs", fmtNumber(checks.run_count || 0)],
  ];
  target.innerHTML = `
    <div class="openclaw-diagnostics-head">
      <div>
        <span class="card-kicker">diagnostics</span>
        <strong>${escapeHTML(status.available ? "OpenClaw 可用" : "OpenClaw 未就绪")}</strong>
        <p>${escapeHTML(status.message || "等待 OpenClaw 状态。")}</p>
      </div>
      <span class="status-pill ${status.available ? "ok" : "warn"}">${escapeHTML(status.configured ? "configured" : "setup needed")}</span>
    </div>
    <div class="openclaw-diagnostics-grid">
      ${metricItems.map(([label, value]) => `<span><strong>${escapeHTML(value)}</strong><small>${escapeHTML(label)}</small></span>`).join("")}
    </div>
    ${
      issues.length
        ? `<div class="openclaw-diagnostics-issues">${issues.map((issue) => `<span>${escapeHTML(issue)}</span>`).join("")}</div>`
        : `<div class="openclaw-diagnostics-issues ok"><span>配置、工具和绑定检查通过</span></div>`
    }
    <div class="openclaw-run-log">
      ${
        recent.length
          ? recent
              .slice(0, 4)
              .map(
                (run) => `
                  <article>
                    <strong>${escapeHTML(run.status || "unknown")}</strong>
                    <span>${escapeHTML(run.openclaw_agent_id || "default agent")} · ${fmtNumber(run.event_count || 0)} events</span>
                  </article>
                `
              )
              .join("")
          : "<p>还没有 OpenClaw run。启动一次 Agent 后，这里会出现最近任务。</p>"
      }
    </div>
  `;
}

function renderAgentTasks() {
  const list = $("#agentTaskList");
  if (!list) return;
  list.innerHTML = state.agentThreads.length
    ? state.agentThreads
        .map(({ thread, task, runs, artifacts, messages }) => {
          const latestRun = runs?.[0];
          const active = state.activeAgentThread?.thread?.thread_id === thread.thread_id ? " active" : "";
          return `
            <button class="agent-task-item${active}" data-thread-id="${escapeHTML(thread.thread_id)}" data-run-id="${escapeHTML(latestRun?.run_id || "")}" data-task-id="${escapeHTML(task?.task_id || thread.task_id)}" type="button">
              <strong>${escapeHTML(thread.title || task?.title || "Agent Thread")}</strong>
              <span>${escapeHTML(thread.status || task?.status || "active")} · ${messages?.length || 0} 条消息 · ${artifacts?.length || 0} 个产物</span>
            </button>
          `;
        })
        .join("")
    : emptyState("暂无 Agent 会话", "输入一个 PR 需求后会生成 Thread、消息、执行和产物。");
  renderAgentMessages();
}

const HISTORY_TYPE_LABELS = {
  campaign: "Campaign",
  agent_thread: "Agent",
  proposal: "方案",
  distribution: "分发",
};

function renderWorkspaceHistory() {
  const metrics = $("#historyMetrics");
  if (metrics) {
    const summary = state.historySummary || {};
    metrics.innerHTML = [
      ["全部资产", state.workspaceHistory.length],
      ["Campaign", summary.campaign || 0],
      ["Agent 会话", summary.agent_thread || 0],
      ["甲方方案", summary.proposal || 0],
      ["Brief 分发", summary.distribution || 0],
    ]
      .map(([label, value]) => `<div class="metric"><span>${escapeHTML(label)}</span><strong>${fmtNumber(value)}</strong></div>`)
      .join("");
  }
  $$(".history-filter").forEach((button) => {
    button.classList.toggle("active", button.dataset.historyType === state.historyFilter);
  });
  const list = $("#historyList");
  if (!list) return;
  if (state.historyLoading) {
    list.innerHTML = emptyState("正在加载历史资产", "正在读取 Campaign、Agent 会话、甲方方案和 Brief 分发记录。");
    return;
  }
  if (!state.historyLoaded) {
    list.innerHTML = emptyState("历史资产按需加载", "打开历史任务后会自动加载，也可以点击刷新历史。");
    return;
  }
  const items = state.workspaceHistory.filter((item) => state.historyFilter === "all" || item.type === state.historyFilter);
  list.innerHTML = items.length
    ? items
        .map((item) => {
          const metricsHtml = (item.metrics || [])
            .map((metric) => `<span>${escapeHTML(metric.label)} ${fmtNumber(metric.value)}</span>`)
            .join("");
          return `
            <article class="history-card ${escapeHTML(item.type || "")}">
              <button class="history-card-main open-history-item-btn" data-history-type="${escapeHTML(item.type)}" data-history-id="${escapeHTML(item.id)}" type="button">
                <span class="card-kicker">${escapeHTML(item.label || HISTORY_TYPE_LABELS[item.type] || item.type)}</span>
                <h3>${escapeHTML(item.title || "未命名资产")}</h3>
                <p>${escapeHTML(item.subtitle || "")} · ${escapeHTML(item.status || "active")}</p>
                <div class="history-summary">${escapeHTML(item.summary || "暂无摘要。")}</div>
              </button>
              <div class="history-card-side">
                <div class="history-time">${escapeHTML(item.updated_at || item.created_at || "-")}</div>
                <div class="asset-history-stats">${metricsHtml}</div>
                <button class="secondary open-history-item-btn" data-history-type="${escapeHTML(item.type)}" data-history-id="${escapeHTML(item.id)}" type="button">打开</button>
              </div>
            </article>
          `;
        })
        .join("")
    : emptyState("暂无历史资产", "跑一次 PR brief、启动 Agent 或生成甲方方案后，这里会自动出现记录。");
}

function renderAgentRuntimeControls() {
  const meta = $("#agentRuntimeMeta");
  const select = $("#agentRuntimeSelect");
  const floatSelect = $("#agentFloatRuntimeSelect");
  if (!meta || !select) return;
  const runtime = state.agentRuntime;
  if (!runtime) {
    meta.textContent = "Runtime 状态读取中...";
    return;
  }
  const sdk = (runtime.available_runtimes || []).find((item) => item.name === "openai_agents");
  const active = runtime.active || {};
  const openClawAvailable = Boolean(state.openClaw?.status?.available);
  meta.textContent = `当前默认 ${runtime.active_runtime || "custom"} · ${active.mode || "native"} · SDK ${sdk?.mode || "unknown"}`;
  select.querySelector('option[value="openai_agents"]').disabled = !(sdk?.available);
  select.querySelector('option[value="openclaw"]').disabled = !openClawAvailable;
  if (floatSelect) {
    floatSelect.querySelector('option[value="openai_agents"]').disabled = !(sdk?.available);
    floatSelect.querySelector('option[value="openclaw"]').disabled = !openClawAvailable;
  }
  renderAgentOpenClawStatus();
}

function renderAgentOpenClawStatus() {
  const node = $("#agentOpenClawStatusPanel");
  if (!node) return;
  const status = state.openClaw?.status || state.openClawMe?.status || {};
  const binding = state.openClawMe?.binding || {};
  const checks = state.openClawDiagnostics?.checks || {};
  const recentRuns = state.openClawDiagnostics?.run_summary?.recent || [];
  const available = Boolean(status.available);
  const issues = checks.issues || [];
  const latestRun = recentRuns[0];
  const activeRun = state.activeOpenClawRun?.run || null;
  const hasActiveRun = Boolean(activeRun?.run_id);
  const hasSavedTarget = Boolean(state.activeOpenClawCampaignTarget?.id);
  node.innerHTML = `
    <div class="agent-openclaw-status-head">
      <div>
        <span class="card-kicker">my agent binding</span>
        <strong>${escapeHTML(available ? "OpenClaw ready" : "OpenClaw needs setup")}</strong>
        <p>${escapeHTML(status.message || "等待 OpenClaw Gateway 状态。")}</p>
      </div>
      <span class="agent-float-status-pill ${available ? "completed" : "failed"}">${escapeHTML(available ? "ready" : "blocked")}</span>
    </div>
    <div class="agent-openclaw-status-grid">
      <span><strong>${escapeHTML(binding.openclaw_agent_id || status.default_agent_id || "kolness_default")}</strong><small>agent</small></span>
      <span><strong>${escapeHTML(binding.openclaw_session_id || "new session")}</strong><small>session</small></span>
      <span><strong>${fmtNumber(checks.tool_count || 0)}</strong><small>tools</small></span>
      <span><strong>${fmtNumber(checks.run_count || 0)}</strong><small>runs</small></span>
    </div>
    ${
      issues.length
        ? `<div class="agent-openclaw-status-note">${issues.map((issue) => `<span>${escapeHTML(issue)}</span>`).join("")}</div>`
        : `<div class="agent-openclaw-status-note ok"><span>Kolness tools、Gateway 和员工绑定状态可用</span></div>`
    }
    ${
      latestRun
        ? `<div class="agent-openclaw-latest"><strong>最近任务</strong><span>${escapeHTML(latestRun.status || "unknown")} · ${escapeHTML(latestRun.openclaw_agent_id || "default")} · ${fmtNumber(latestRun.event_count || 0)} events</span></div>`
        : ""
    }
    ${
      hasActiveRun
        ? `<div class="agent-openclaw-actions">
            <div>
              <strong>${escapeHTML(activeRun.status || "running")}</strong>
              <span>${escapeHTML(activeRun.openclaw_agent_id || "OpenClaw")} · ${fmtNumber((state.activeOpenClawRun?.events || []).length)} events</span>
            </div>
            <button id="agentSaveOpenClawCampaignBtn" class="secondary" type="button">${hasSavedTarget ? "已保存" : "保存到 Campaign"}</button>
            <button id="agentViewOpenClawAssetsBtn" class="secondary${hasSavedTarget ? "" : " hidden"}" type="button">查看资产</button>
          </div>`
        : ""
    }
  `;
}

function renderAgentRuntimeComparison() {
  const node = $("#agentRuntimeComparison");
  if (!node) return;
  const comparison = state.agentRuntimeComparison;
  if (!comparison) {
    node.classList.add("hidden");
    node.innerHTML = "";
    return;
  }
  const payload = comparison.comparison || {};
  const runs = payload.runs || {};
  const runtimeNames = Object.keys(runs);
  node.classList.remove("hidden");
  node.innerHTML = `
    <div class="agent-runtime-comparison-head">
      <strong>Runtime A/B 对比</strong>
      <span>${escapeHTML(payload.runtime_a || "custom")} vs ${escapeHTML(payload.runtime_b || "openai_agents")}</span>
    </div>
    <div class="runtime-compare-grid">
      ${runtimeNames
        .map((name) => {
          const item = runs[name] || {};
          return `
            <article>
              <span>${escapeHTML(name)}</span>
              <strong>${escapeHTML(item.status || "-")}</strong>
              <div class="meta">候选 ${fmtNumber(item.candidate_count || 0)} · 工具 ${fmtNumber(item.tool_count || 0)} · 图谱 ${fmtNumber(item.graph_nodes || 0)}</div>
              ${item.sdk_status ? `<div class="meta">SDK ${escapeHTML(item.sdk_status)} · ${escapeHTML(item.sdk_message || "")}</div>` : ""}
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderAgentRun(data) {
  state.activeAgentRun = data;
  state.activeAgentArtifacts = data.artifacts || [];
  state.activeAgentSteps = data.steps || [];
  if (data.thread) state.activeAgentThread = data;
  const run = data.run || {};
  const task = data.task || {};
  const events = data.events || [];
  const runningStep = state.activeAgentSteps.find((step) => step.status === "running");
  const lastToolEvent = [...events].reverse().find((event) => event.tool_name);
  state.activeAgentToolName = runningStep?.tool_name || lastToolEvent?.tool_name || "";
  const meta = $("#agentRunMeta");
  if (meta) meta.textContent = task.title ? `${task.title} · ${run.status || "running"} · ${state.activeAgentSteps.length} steps` : "等待 Agent 执行。";
  const approveBtn = $("#agentApproveBtn");
  if (approveBtn) {
    approveBtn.classList.toggle("hidden", !run.run_id || !["waiting_approval", "completed"].includes(run.status));
    approveBtn.dataset.runId = run.run_id || "";
  }
  const approvePlanBtn = $("#agentApprovePlanBtn");
  if (approvePlanBtn) {
    approvePlanBtn.classList.toggle("hidden", run.status !== "waiting_plan_approval");
    approvePlanBtn.dataset.runId = run.run_id || "";
  }
  const cancelBtn = $("#agentCancelRunBtn");
  if (cancelBtn) {
    cancelBtn.classList.toggle("hidden", !run.run_id || ["approved", "cancelled", "failed"].includes(run.status));
    cancelBtn.dataset.runId = run.run_id || "";
  }
  const copyBtn = $("#agentCopyBriefBtn");
  if (copyBtn) {
    copyBtn.classList.toggle("hidden", !task.brief);
    copyBtn.dataset.brief = task.brief || "";
  }
  const clarificationForm = $("#agentClarificationForm");
  if (clarificationForm) {
    clarificationForm.classList.toggle("hidden", run.status !== "waiting_clarification");
    clarificationForm.dataset.runId = run.run_id || "";
  }
  const stream = $("#agentEventStream");
  if (stream) {
    stream.innerHTML = events.length
      ? events
          .map(
            (event) => `
              <article class="agent-event ${escapeHTML(event.status)}">
                <div class="agent-event-index">${String(event.sequence).padStart(2, "0")}</div>
                <div>
                  <div class="agent-event-head">
                    <strong>${escapeHTML(event.title)}</strong>
                    <span>${escapeHTML(event.status)}</span>
                  </div>
                  <p>${escapeHTML(event.summary || "")}</p>
                  ${event.tool_name ? `<div class="meta">tool: ${escapeHTML(event.tool_name)}</div>` : ""}
                </div>
              </article>
            `
          )
          .join("")
      : emptyState("暂无执行事件", "启动 Agent 后会显示每一步工具调用。");
  }
  renderAgentArtifacts();
  renderAgentSteps();
  renderAgentReasoningGraph();
  renderAgentMessages();
  renderAgentFloatDock();
}

function renderAgentSteps() {
  const list = $("#agentStepList");
  if (!list) return;
  const steps = state.activeAgentSteps || [];
  if (!steps.length) {
    list.innerHTML = emptyState("暂无工具步骤", "Agent 启动后会把工具调用拆成可重试、可跳过、可编辑的步骤。");
    return;
  }
  list.innerHTML = steps
    .map((step, index) => {
      const canControl = Boolean(step.editable !== false);
      return `
        <article class="agent-step-card ${escapeHTML(step.status || "pending")}">
          <div class="agent-step-rail">${String(index + 1).padStart(2, "0")}</div>
          <div class="agent-step-body">
            <div class="agent-step-head">
              <div>
                <span>${escapeHTML(step.agent_role || "PR Agent")}</span>
                <strong>${escapeHTML(step.title || step.tool_name || "工具步骤")}</strong>
              </div>
              <em>${escapeHTML(step.status || "pending")}</em>
            </div>
            <p>${escapeHTML(step.output_summary || step.input_summary || "等待执行结果。")}</p>
            ${step.error ? `<div class="agent-step-error">${escapeHTML(step.error)}</div>` : ""}
            <div class="agent-step-meta">
              <span>${escapeHTML(step.tool_name || "tool")}</span>
              ${step.artifact_id ? `<span>artifact ${escapeHTML(step.artifact_id.slice(0, 10))}</span>` : ""}
            </div>
            ${
              canControl
                ? `<div class="agent-step-actions">
                    <button class="secondary agent-step-action" data-step-id="${escapeHTML(step.step_id)}" data-action="retry" type="button">重试</button>
                    <button class="secondary agent-step-action" data-step-id="${escapeHTML(step.step_id)}" data-action="edit" type="button">编辑输入</button>
                    <button class="secondary agent-step-action danger" data-step-id="${escapeHTML(step.step_id)}" data-action="skip" type="button">跳过</button>
                  </div>`
                : ""
            }
          </div>
        </article>
      `;
    })
    .join("");
}

function renderAgentMessages() {
  const list = $("#agentMessageList");
  if (!list) return;
  if (renderOpenClawMainMessages()) return;
  list.classList.remove("openclaw-thread");
  const thread = state.activeAgentThread?.thread;
  const messages = state.activeAgentThread?.messages || [];
  const meta = $("#agentThreadMeta");
  if (meta) {
    meta.textContent = thread
      ? `${thread.title} · ${thread.status} · ${messages.length} 条消息`
      : "新会话会自动创建 Thread；继续输入会基于同一个项目上下文重跑。";
  }
  list.innerHTML = messages.length
    ? messages
        .map(
          (message) => `
            <article class="agent-message ${escapeHTML(message.role)} ${escapeHTML(message.status || "completed")}">
              <div class="agent-message-role">${escapeHTML(message.role === "user" ? "You" : "Agent")}</div>
              <div>
                <p>${escapeHTML(message.content || "")}</p>
                ${message.run_id ? `<span>run ${escapeHTML(message.run_id)}</span>` : ""}
              </div>
            </article>
          `
        )
        .join("")
    : emptyState("暂无聊天消息", "输入甲方 brief 后，这里会保留多轮对话历史。");
  list.scrollTop = list.scrollHeight;
}

function renderAgentArtifacts() {
  const list = $("#agentArtifactList");
  if (!list) return;
  list.innerHTML = state.activeAgentArtifacts.length
    ? state.activeAgentArtifacts.map((artifact) => renderAgentArtifact(artifact)).join("")
    : emptyState("等待 Agent 产物", "启动 OpenClaw 后，这里会沉淀 KOL 推荐、风险判断、图谱快照和可保存到 Campaign 的方案资产。");
}

function renderAgentFloatDock() {
  const dock = $("#agentFloatDock");
  if (!dock) return;
  const user = state.currentIdentity?.user;
  const visible = user?.user_type === "internal" && state.activeView !== "agentWorkspace";
  dock.classList.toggle("hidden", !visible);
  if (!visible) return;
  const panel = $("#agentFloatPanel");
  const toggle = $("#agentFloatToggle");
  if (panel) panel.classList.toggle("hidden", !state.agentFloatOpen);
  if (toggle) toggle.setAttribute("aria-expanded", state.agentFloatOpen ? "true" : "false");
  applyAgentFloatFrame();
  renderAgentFloatContent();
}

function setAgentFloatOpen(open) {
  state.agentFloatOpen = Boolean(open);
  localStorage.setItem("pr_ai_os_agent_float_open", state.agentFloatOpen ? "1" : "0");
  renderAgentFloatDock();
}

function initAgentFloatFrameControls() {
  const panel = $("#agentFloatPanel");
  const dock = $("#agentFloatDock");
  const toggle = $("#agentFloatToggle");
  const head = panel?.querySelector(".agent-float-head");
  if (!panel || !dock || !head || panel.dataset.frameControlsReady === "1") return;
  panel.dataset.frameControlsReady = "1";

  const frameFromPanel = () => {
    const rect = panel.getBoundingClientRect();
    return clampAgentFloatFrame({ left: rect.left, top: rect.top, width: rect.width, height: rect.height });
  };

  const startMove = (event, sourceElement, frame) => {
    if (window.innerWidth <= 760) return;
    const startFrame = frame || frameFromPanel();
    const startX = event.clientX;
    const startY = event.clientY;
    panel.classList.add("agent-float-moving");
    sourceElement.setPointerCapture?.(event.pointerId);
    const onMove = (moveEvent) => {
      saveAgentFloatFrame({
        ...startFrame,
        left: startFrame.left + moveEvent.clientX - startX,
        top: startFrame.top + moveEvent.clientY - startY,
      });
    };
    const onUp = () => {
      panel.classList.remove("agent-float-moving");
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
  };

  head.addEventListener("pointerdown", (event) => {
    if (event.target.closest("button, input, select, textarea, a, summary")) return;
    startMove(event, head, frameFromPanel());
  });

  toggle?.addEventListener("pointerdown", (event) => {
    if (event.target.closest("input, select, textarea, a")) return;
    const startFrame = state.agentFloatFrame || frameFromFloatElement(toggle);
    let moved = false;
    const startX = event.clientX;
    const startY = event.clientY;
    const onFirstMove = (moveEvent) => {
      if (Math.abs(moveEvent.clientX - startX) + Math.abs(moveEvent.clientY - startY) < 4) return;
      moved = true;
      toggle.dataset.suppressClick = "1";
      window.removeEventListener("pointermove", onFirstMove);
      startMove(event, toggle, startFrame);
    };
    const onUp = () => {
      window.removeEventListener("pointermove", onFirstMove);
      window.removeEventListener("pointerup", onUp);
      if (moved) {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    window.addEventListener("pointermove", onFirstMove);
    window.addEventListener("pointerup", onUp);
  });

  panel.querySelectorAll("[data-agent-float-resize]").forEach((resize) => {
    resize.addEventListener("pointerdown", (event) => {
    if (window.innerWidth <= 760) return;
    event.preventDefault();
    const mode = resize.dataset.agentFloatResize || "corner";
    const startFrame = frameFromPanel();
    const startX = event.clientX;
    const startY = event.clientY;
    panel.classList.add("agent-float-resizing");
    resize.setPointerCapture?.(event.pointerId);
    const onMove = (moveEvent) => {
      const dx = moveEvent.clientX - startX;
      const dy = moveEvent.clientY - startY;
      saveAgentFloatFrame({
        ...startFrame,
        width: mode === "bottom" ? startFrame.width : startFrame.width + dx,
        height: mode === "right" ? startFrame.height : startFrame.height + dy,
      });
    };
    const onUp = () => {
      panel.classList.remove("agent-float-resizing");
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    });
  });

  window.addEventListener("resize", () => {
    if (!state.agentFloatFrame) return;
    saveAgentFloatFrame(state.agentFloatFrame);
  });
}

function renderAgentFloatContent() {
  const summary = $("#agentFloatSummary");
  $("#agentFloatPanel")?.classList.toggle("agent-float-has-sessions", activeFloatRuntime() === "openclaw");
  renderAgentFloatActions();
  if (activeFloatRuntime() === "openclaw") {
    ensureOpenClawSession();
    renderOpenClawSessionList();
    renderOpenClawFloatContent(summary);
    return;
  }
  const run = state.activeAgentRun?.run || {};
  const task = state.activeAgentRun?.task || state.activeAgentThread?.task || {};
  const thread = state.activeAgentThread?.thread || {};
  if (summary) {
    const status = run.status || thread.status || "idle";
    const title = task.title || thread.title || "新 PR Agent 任务";
    const artifactCount = state.activeAgentArtifacts.length;
    summary.innerHTML = `
      <strong>${escapeHTML(title)}</strong>
      <span>${escapeHTML(status)} · ${fmtNumber(state.activeAgentSteps.length)} steps · ${fmtNumber(artifactCount)} assets</span>
    `;
  }
  renderAgentFloatMessages();
}

function renderAgentFloatActions() {
  const isOpenClaw = activeFloatRuntime() === "openclaw";
  const hasOpenClawRun = Boolean(state.activeOpenClawRun?.run?.run_id);
  $("#agentFloatNewTaskBtn")?.classList.toggle("hidden", !isOpenClaw);
  $("#agentFloatSaveCampaignBtn")?.classList.toggle("hidden", !(isOpenClaw && hasOpenClawRun));
  $("#agentFloatViewAssetsBtn")?.classList.toggle("hidden", !(isOpenClaw && hasOpenClawRun));
}

function activeFloatRuntime() {
  return $("#agentFloatRuntimeSelect")?.value || "auto";
}

function displayOpenClawMessage(run) {
  return stripOpenClawDisplayMessage(state.activeOpenClawRun?.displayMessage || run?.display_message || run?.message || "");
}

function stripOpenClawDisplayMessage(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  return text
    .split(/\n\s*执行方式：/)[0]
    .split(/\n\s*执行方式:/)[0]
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function enrichOpenClawPayload(payload) {
  const session = ensureOpenClawSession();
  const message = String(payload.message || payload.brief || "").trim();
  const history = (state.openClawConversation || [])
    .filter((item) => !item.pending)
    .flatMap((item) => {
      const rows = [];
      if (item.user) rows.push({ role: "user", content: item.user });
      if (item.assistant) rows.push({ role: "assistant", content: item.assistant });
      return rows;
    })
    .slice(-12);
  return {
    ...payload,
    message,
    history,
    session_id: session.id,
    openclaw_session_id: session.openclawSessionId || payload.openclaw_session_id || "",
  };
}

function optimisticOpenClawRun(payload) {
  const now = new Date().toISOString();
  const message = String(payload.message || payload.brief || "").trim();
  return {
    displayMessage: message,
    run: {
      run_id: `local_openclaw_${Date.now()}`,
      status: "running",
      message,
      response: "",
      error: "",
      openclaw_agent_id: "kolness_openclaw",
      openclaw_session_id: "",
      created_at: now,
      updated_at: now,
    },
    events: [
      { event_type: "message.created", sequence: 1, created_at: now, payload: { role: "user", content: message } },
      {
        event_type: "gateway.started",
        sequence: 2,
        created_at: now,
        payload: { tool_name: "openclaw.gateway", optimistic: true },
      },
    ],
  };
}

function openClawStepLabel(event) {
  const eventType = event?.event_type || "";
  const toolName = event?.payload?.tool_name || "";
  if (eventType === "gateway.started") return "连接 Agent Gateway";
  if (eventType === "gateway.completed") return "Agent Gateway 返回";
  if (eventType === "kolness.match.completed") return "KOL 匹配完成";
  if (eventType === "artifact.preview.created") return "生成推荐预览";
  if (eventType === "message.created") return "接收 brief";
  if (eventType === "tool.started" && /kolness.*match/i.test(toolName)) return "调用达人匹配工具";
  if (eventType === "tool.started") return toolName.includes("openclaw") ? "连接 OpenClaw Gateway" : toolName;
  if (eventType === "message.completed") return "整理推荐结论";
  if (eventType === "tool.failed" || eventType === "run.failed") return "任务失败";
  if (eventType === "run.completed") return "完成任务";
  return eventType || "任务事件";
}

function openClawStepStatus(event, run) {
  const type = event?.event_type || "";
  if (type.includes("failed") || run?.status === "failed") return "failed";
  if (type === "tool.started" && run?.status === "running") return "running";
  if (type === "run.completed" || type === "message.completed" || type.endsWith(".completed") || type.includes(".created")) return "completed";
  return run?.status === "running" ? "running" : "completed";
}

function hasRealKolnessToolEvent(events) {
  return (events || []).some((event) => {
    const type = String(event?.event_type || "");
    const payload = event?.payload || {};
    const toolName = String(payload.tool_name || "");
    if (payload.source === "agent_response") return false;
    return /kolness/i.test(toolName) || (type.startsWith("tool.") && /kolness/i.test(JSON.stringify(payload)));
  });
}

function buildOpenClawSteps(run, events) {
  const baseSteps = [
    { label: "接收 brief", status: events.length ? "completed" : "running", meta: "user message" },
    {
      label: "连接 OpenClaw Gateway",
      status: run?.status === "failed" ? "failed" : events.some((event) => event.event_type === "gateway.started") ? "completed" : "running",
      meta: "agent runtime",
    },
  ];
  if (hasRealKolnessToolEvent(events)) {
    baseSteps.push({ label: "调用 Kolness 工具", status: run?.status === "running" ? "running" : "completed", meta: "MCP / tools" });
  }
  const eventSteps = (events || []).slice(-5).map((event) => ({
    label: openClawStepLabel(event),
    status: openClawStepStatus(event, run),
    meta: event?.payload?.tool_name || event?.event_type || "",
  }));
  return [...baseSteps, ...eventSteps].slice(-7);
}

function openClawRunElapsedSeconds(run) {
  const started = Date.parse(run?.created_at || run?.updated_at || "");
  if (!Number.isFinite(started)) return 0;
  return Math.max(0, Math.round((Date.now() - started) / 1000));
}

function currentOpenClawStep(run, events) {
  const steps = buildOpenClawSteps(run, events);
  const running = steps.findLast?.((step) => step.status === "running") || [...steps].reverse().find((step) => step.status === "running");
  if (running) return running;
  if (run?.status === "completed") return { label: "完成任务", status: "completed", meta: "ready" };
  if (run?.status === "failed") return { label: "任务失败", status: "failed", meta: run.error || "error" };
  return steps[steps.length - 1] || { label: "准备执行", status: "running", meta: "queued" };
}

function openClawWaitingText(run, events) {
  if (run?.status === "failed") return "这条消息执行失败，请稍后重试。";
  const step = currentOpenClawStep(run, events);
  const label = step.label || "";
  if (/brief|接收/.test(label)) return "我正在读取 brief，提取预算、平台和目标人群。";
  if (/Gateway|连接/.test(label)) return "我正在连接 OpenClaw，并准备调用 Kolness 工具。";
  if (/匹配|Kolness|工具|达人/.test(label)) return "我正在读取达人库并匹配 KOL。";
  if (/推荐|结论|完成/.test(label)) return "我正在整理推荐理由、风险和下一步动作。";
  return `正在处理：${label || "Agent 执行中"}`;
}

function renderOpenClawLiveCard(run, events) {
  const status = run?.status || "running";
  const steps = buildOpenClawSteps(run, events).slice(-5);
  const current = currentOpenClawStep(run, events);
  const elapsed = openClawRunElapsedSeconds(run);
  return `
    <article class="agent-float-live-card ${escapeHTML(status)}">
      <div class="agent-float-live-head">
        <div>
          <span>Agent running</span>
          <strong>${escapeHTML(current.label || "处理中")}</strong>
        </div>
        <em>${fmtNumber(elapsed)}s · ${fmtNumber((events || []).length)} events</em>
      </div>
      <p>${escapeHTML(openClawWaitingText(run, events))}</p>
      <div class="agent-float-live-steps">
        ${steps
          .map(
            (step) => `
              <div class="agent-float-live-step ${escapeHTML(step.status || "pending")}">
                <i></i>
                <span>${escapeHTML(step.label || "任务步骤")}</span>
              </div>
            `
          )
          .join("")}
      </div>
    </article>
  `;
}

function renderOpenClawQuickActions(run) {
  const status = run?.status || "";
  if (status !== "completed") return "";
  return `
    <div class="agent-float-quick-actions">
      <button class="secondary" type="button" data-agent-openclaw-action="save-campaign">保存到 Campaign</button>
      <button class="secondary" type="button" data-agent-openclaw-action="view-assets">查看资产</button>
      <button class="secondary" type="button" data-agent-prompt="继续基于这次结果，帮我补充预算分配、风险控制和客户沟通话术。">继续追问</button>
    </div>
  `;
}

function extractOpenClawKols(text) {
  const value = String(text || "");
  if (!value) return [];
  const rawLines = value.split(/\n+/).map((line) => line.trim()).filter(Boolean);
  const candidates = [];
  for (const rawLine of rawLines) {
    const structuredLine =
      /^[\s>*-]*\d+[.、)]\s*/.test(rawLine) ||
      /^[\s>*-]*(KOL(?!ness)|达人|账号)\b/i.test(rawLine);
    if (!structuredLine) continue;
    const line = rawLine.replace(/^[\s>*-]*(\d+[.、)]\s*)?/, "").trim();
    const match = line.match(/^([^：:，,。；;\-|]+)(?:[：:，,。；;\-|]|\s+-\s+).{0,120}$/);
    const name = (match ? match[1] : line).replace(/^(KOL(?!ness)|达人|推荐|账号)\s*/i, "").trim();
    if (name.length >= 2 && name.length <= 18 && !/[。！？]$/.test(name) && !/Kolness|OpenClaw|Bridge|推荐名单|匹配理由|主要风险|下一步/.test(name)) {
      candidates.push(name);
    }
  }
  return [...new Set(candidates)].slice(0, 6);
}

function openClawEventKols(events) {
  const names = [];
  for (const event of events || []) {
    const eventNames = Array.isArray(event?.payload?.recommended_kols) ? event.payload.recommended_kols : [];
    for (const name of eventNames) {
      const value = String(name || "").trim();
      if (value && !names.includes(value)) names.push(value);
    }
  }
  return names.slice(0, 6);
}

function renderOpenClawWorkspace(run, events) {
  const status = run.status || "running";
  const steps = buildOpenClawSteps(run, events);
  const response = run.response || run.error || "";
  const kols = openClawEventKols(events).length ? openClawEventKols(events) : extractOpenClawKols(response);
  const isFailed = status === "failed";
  return `
    <section class="agent-float-workspace">
      <div class="agent-float-workspace-head">
        <div>
          <span class="agent-float-status-pill ${escapeHTML(status)}">${escapeHTML(status)}</span>
          <strong>Agent Task Space</strong>
        </div>
        <span>${fmtNumber(events.length)} events</span>
      </div>
      <div class="agent-float-tool-rail">
        <span>brief</span>
        <i></i>
        <span>Kolness MCP</span>
        <i></i>
        <span>KOL picks</span>
      </div>
      <div class="agent-float-step-stack compact">
        ${steps
          .map(
            (step, index) => `
              <div class="agent-float-step ${escapeHTML(step.status)}">
                <em>${String(index + 1).padStart(2, "0")}</em>
                <span>${escapeHTML(step.label)}</span>
                <small>${escapeHTML(step.meta || "")}</small>
              </div>
            `
          )
          .join("")}
      </div>
      <article class="agent-float-output-card ${isFailed ? "failed" : ""}">
        <span class="card-kicker">${isFailed ? "error" : "deliverable"}</span>
        <strong>${isFailed ? "Agent 返回错误" : "推荐结果预览"}</strong>
        ${
          response
            ? `<p>${escapeHTML(response).slice(0, 680)}${response.length > 680 ? "..." : ""}</p>`
            : `<p>OpenClaw 正在拆 brief、调用 Kolness 工具和整理推荐。完成后这里会出现推荐名单、理由和风险。</p>`
        }
        ${
          kols.length
            ? `<div class="agent-float-kol-chips">${kols.map((kol) => `<span>${escapeHTML(kol)}</span>`).join("")}</div>`
            : ""
        }
      </article>
    </section>
  `;
}

function summarizeOpenClawResponse(response, events = []) {
  const text = String(response || "").trim();
  if (!text) return "";
  if (/返回错误|失败|error/i.test(text) && text.length < 360) return text;
  const eventKols = openClawEventKols(events);
  const fallbackKols = extractOpenClawKols(text);
  const kols = (eventKols.length ? eventKols : fallbackKols).slice(0, 8);
  const lines = [];
  const firstLine = text.split(/\n+/).find((line) => line.trim() && !line.trim().startsWith("#"));
  lines.push(firstLine || "已完成本次 PR Agent 任务。");
  if (kols.length) lines.push(`推荐 KOL：${kols.join("、")}`);
  const riskMatch = text.match(/##\s*主要风险\s*([\s\S]*?)(?:\n##\s|$)/);
  if (riskMatch) {
    const risk = riskMatch[1]
      .split(/\n+/)
      .map((line) => line.replace(/^[\s>*-]+/, "").trim())
      .find(Boolean);
    if (risk) lines.push(`风险提示：${risk.slice(0, 110)}${risk.length > 110 ? "..." : ""}`);
  }
  if (kols.length || riskMatch) lines.push("完整推荐理由、预算建议和客户方案已生成，可保存到 Campaign。");
  return lines.join("\n");
}

function formatOpenClawChatResponse(response) {
  return String(response || "").trim();
}

function renderOpenClawFloatContent(summary) {
  const run = state.activeOpenClawRun?.run || {};
  const events = state.activeOpenClawRun?.events || [];
  if (summary) {
    const hasToolEvent = hasRealKolnessToolEvent(events);
    const currentStep = currentOpenClawStep(run, events);
    const statusLabel =
      run.status === "completed"
        ? "Agent 已返回"
        : run.status === "failed"
          ? "执行失败"
          : hasToolEvent
            ? `正在执行 · ${currentStep.label || "Kolness 工具"}`
            : run.status === "running"
              ? `正在执行 · ${currentStep.label || "准备任务"}`
              : run.status || "ready";
    summary.innerHTML = `
      <strong>${escapeHTML(displayOpenClawMessage(run) || "和 PR Agent 对话")}</strong>
      <span>${escapeHTML(statusLabel)}</span>
    `;
  }
  renderOpenClawFloatMessages();
}

function summarizeImportPreview(review) {
  const sheets = Array.isArray(review?.sheets) ? review.sheets : [];
  const totals = review?.totals || {};
  return {
    filename: review?.filename || "上传文件",
    importId: review?.import_id || "",
    sheetCount: Number(totals.sheets || sheets.length || 0),
    rowCount: Number(totals.rows || sheets.reduce((sum, sheet) => sum + Number(sheet.rows || 0), 0)),
    profileCount: Number(totals.detected_profiles || sheets.reduce((sum, sheet) => sum + Number(sheet.detected_profiles || 0), 0)),
    flags: sheets.flatMap((sheet) => sheet.quality_flags || []).filter(Boolean),
  };
}

function renderAgentImportPreviewCard(review) {
  if (!review?.import_id) return "";
  const summary = summarizeImportPreview(review);
  const committed = review.status === "committed";
  const failed = review.status === "failed";
  const sheets = (review.sheets || []).slice(0, 4);
  const flagText = summary.flags.length ? Array.from(new Set(summary.flags)).slice(0, 4).join("、") : "字段识别正常";
  return `
    <article class="agent-float-import-card ${committed ? "committed" : ""} ${failed ? "failed" : ""}">
      <div class="agent-float-import-head">
        <div>
          <span>达人导入预览</span>
          <strong>${escapeHTML(summary.filename)}</strong>
        </div>
        <em>${escapeHTML(committed ? "已导入" : failed ? "导入失败" : "待确认")}</em>
      </div>
      <div class="agent-float-import-metrics">
        <span><b>${fmtNumber(summary.profileCount)}</b> 可导入达人</span>
        <span><b>${fmtNumber(summary.rowCount)}</b> 行</span>
        <span><b>${fmtNumber(summary.sheetCount)}</b> sheets</span>
      </div>
      <p>${escapeHTML(flagText)}</p>
      ${
        sheets.length
          ? `<ul>${sheets
              .map((sheet) => `<li>${escapeHTML(sheet.sheet || "Sheet")} · ${fmtNumber(sheet.detected_profiles || 0)} 达人 · ${escapeHTML((sheet.quality_flags || []).join("、") || "OK")}</li>`)
              .join("")}</ul>`
          : ""
      }
      ${
        committed
          ? `<p>已写入 ${fmtNumber(review.imported || 0)} 个达人，达人库已刷新。</p>`
          : failed
            ? `<p>${escapeHTML(review.error || "导入失败，请重新上传。")}</p>`
            : `<button class="primary" type="button" data-agent-import-commit="${escapeHTML(summary.importId)}">确认导入达人库</button>`
      }
    </article>
  `;
}

function renderOpenClawFloatMessages() {
  const node = $("#agentFloatMessages");
  if (!node) return;
  const run = state.activeOpenClawRun?.run || {};
  const events = state.activeOpenClawRun?.events || [];
  const conversation = state.openClawConversation || [];
  if (!conversation.length && !run.run_id && !state.activeAgentImportPreview) {
    node.classList.remove("agent-float-openclaw-space");
    node.innerHTML = `
      <article class="agent-float-welcome">
        <strong>直接和 PR Agent 对话。</strong>
        <p>输入 brief 或问题后，Agent 会调用 Kolness 工具，并把推荐、风险和下一步直接写回聊天里。</p>
        <div class="agent-float-suggestions">
          <button type="button" data-agent-prompt="帮我把这个 PR brief 跑成一条对话任务，先推荐 KOL，再解释推荐理由和风险。">跑 brief</button>
          <button type="button" data-agent-prompt="用 Kolness 的达人库帮我查适合这个项目的 KOL，并生成客户可读解释。">查达人库</button>
        </div>
      </article>
    `;
    return;
  }
  node.classList.remove("agent-float-openclaw-space");
  const rows = conversation.length
    ? conversation
    : run.run_id
      ? [
        {
          user: displayOpenClawMessage(run),
          assistant: run.response || run.error ? formatOpenClawChatResponse(run.response || run.error) : "",
          status: run.status || "running",
        },
      ]
      : [];
  node.innerHTML = `
    <section class="agent-float-transcript">
      ${rows
        .map(
          (item) => `
            ${
              item.user
                ? `<article class="agent-float-message user"><span>You</span><p>${escapeHTML(item.user)}</p></article>`
                : ""
            }
            ${
              item.assistant
                ? `<article class="agent-float-message assistant"><span>Agent</span><p>${escapeHTML(item.assistant)}</p>${item.runId === run.run_id ? renderOpenClawQuickActions(run) : ""}</article>`
                : item.runId === run.run_id
                  ? renderOpenClawLiveCard(run, events)
                  : `<article class="agent-float-message assistant thinking"><span>Agent</span><p>${escapeHTML(item.status === "failed" ? "这条消息执行失败，请稍后重试。" : "正在处理这条消息。")}</p></article>`
            }
          `
        )
        .join("")}
      ${renderAgentImportPreviewCard(state.activeAgentImportPreview)}
    </section>
  `;
  node.scrollTop = node.scrollHeight;
}

function upsertOpenClawConversation(data, fallbackMessage = "") {
  const run = data?.run || {};
  const events = data?.events || [];
  const runId = run.run_id || data?.run_id || "";
  if (!runId) return;
  const user = stripOpenClawDisplayMessage(fallbackMessage || data.displayMessage || run.display_message || run.message || "");
  const assistant = run.response || run.error ? formatOpenClawChatResponse(run.response || run.error) : "";
  const index = state.openClawConversation.findIndex((item) => item.runId === runId || (item.pending && user && item.user === user));
  const item = {
    runId,
    user,
    assistant,
    status: run.status || "running",
    eventCount: events.length,
    pending: false,
  };
  if (index >= 0) {
    state.openClawConversation[index] = { ...state.openClawConversation[index], ...item };
  } else {
    state.openClawConversation.push(item);
  }
}

function renderOpenClawMainMessages() {
  const list = $("#agentMessageList");
  if (!list) return false;
  const run = state.activeOpenClawRun?.run || {};
  if (!run.run_id) return false;
  const events = state.activeOpenClawRun?.events || [];
  renderOpenClawExecutionPanel(run, events);
  const status = run.status || "running";
  const displayMessage = displayOpenClawMessage(run);
  const response = run.response || run.error || "";
  const assistantResponse = formatOpenClawChatResponse(response);
  const currentStep = currentOpenClawStep(run, events);
  const meta = $("#agentThreadMeta");
  if (meta) {
    meta.textContent = `${displayMessage || "OpenClaw 深度任务"} · ${status} · ${currentStep.label || "执行中"} · ${fmtNumber(events.length)} events`;
  }
  list.classList.add("openclaw-thread");
  list.innerHTML = `
    <article class="agent-message user completed">
      <div class="agent-message-role">You</div>
      <div>
        <p>${escapeHTML(displayMessage || "启动一个 OpenClaw PR 任务。")}</p>
        <span>brief received</span>
      </div>
    </article>
    <article class="agent-message assistant ${escapeHTML(status)}">
      <div class="agent-message-role">Agent</div>
      <div>
        ${
          assistantResponse
            ? `<p>${escapeHTML(assistantResponse)}</p><span>${escapeHTML(status)} · ${fmtNumber(events.length)} events</span>${renderOpenClawQuickActions(run)}`
            : `<div class="agent-main-live-card">${renderOpenClawLiveCard(run, events)}</div>`
        }
      </div>
    </article>
    <div class="agent-main-openclaw-space">
      ${renderOpenClawWorkspace(run, events)}
    </div>
  `;
  list.scrollTop = list.scrollHeight;
  return true;
}

function renderOpenClawExecutionPanel(run, events) {
  const steps = buildOpenClawSteps(run, events);
  const meta = $("#agentRunMeta");
  if (meta) {
    meta.textContent = `${run.status || "running"} · ${fmtNumber(steps.length)} steps · ${fmtNumber(events.length)} events`;
  }
  $("#agentApprovePlanBtn")?.classList.add("hidden");
  $("#agentCancelRunBtn")?.classList.toggle("hidden", !run.run_id || run.status !== "running");
  $("#agentCopyBriefBtn")?.classList.add("hidden");
  $("#agentApproveBtn")?.classList.add("hidden");
  $("#agentClarificationForm")?.classList.add("hidden");

  const stepList = $("#agentStepList");
  if (stepList) {
    stepList.innerHTML = steps.length
      ? steps
          .map(
            (step, index) => `
              <article class="agent-step-card ${escapeHTML(step.status || "pending")}">
                <div class="agent-step-rail">${String(index + 1).padStart(2, "0")}</div>
                <div class="agent-step-body">
                  <div class="agent-step-head">
                    <div>
                      <span>OpenClaw / Kolness MCP</span>
                      <strong>${escapeHTML(step.label || "任务步骤")}</strong>
                    </div>
                    <em>${escapeHTML(step.status || "pending")}</em>
                  </div>
                  <p>${escapeHTML(step.meta || "等待任务事件。")}</p>
                </div>
              </article>
            `
          )
          .join("")
      : emptyState("等待 OpenClaw 步骤", "任务启动后会显示 brief 解析、达人库读取、KOL 匹配和方案生成。");
  }

  const stream = $("#agentEventStream");
  if (stream) {
    stream.innerHTML = events.length
      ? events
          .map((event, index) => {
            const payload = event.payload || {};
            const status = openClawStepStatus(event, run);
            const label = openClawStepLabel(event);
            const summary = payload.content || payload.preview || payload.error || payload.tool_name || event.event_type || "";
            return `
              <article class="agent-event ${escapeHTML(status)}">
                <div class="agent-event-index">${String(event.sequence || index + 1).padStart(2, "0")}</div>
                <div>
                  <div class="agent-event-head">
                    <strong>${escapeHTML(label)}</strong>
                    <span>${escapeHTML(status)}</span>
                  </div>
                  <p>${escapeHTML(String(summary).slice(0, 240))}</p>
                  <div class="meta">${escapeHTML(event.event_type || "openclaw.event")}</div>
                </div>
              </article>
            `;
          })
          .join("")
      : emptyState("暂无 OpenClaw 事件", "OpenClaw Gateway 返回后会同步显示工具调用和产物事件。");
  }
}

function renderAgentFloatMessages() {
  const node = $("#agentFloatMessages");
  if (!node) return;
  node.classList.remove("agent-float-openclaw-space");
  const messages = state.activeAgentThread?.messages || [];
  const run = state.activeAgentRun?.run || {};
  const steps = state.activeAgentSteps || [];
  const artifacts = state.activeAgentArtifacts || [];
  const transcript = messages.slice(-8).map(
    (message) => `
      <article class="agent-float-message ${escapeHTML(message.role)}">
        <span>${escapeHTML(message.role === "user" ? "You" : "Agent")}</span>
        <p>${escapeHTML(message.content || "")}</p>
      </article>
    `
  );
  if (run.status || steps.length || artifacts.length) {
    transcript.push(renderAgentFloatRunCard(run, steps, artifacts));
  }
  node.innerHTML = transcript.length ? transcript.join("") : renderAgentFloatWelcome();
  node.scrollTop = node.scrollHeight;
}

function renderAgentFloatWelcome() {
  return `
    <article class="agent-float-welcome">
      <strong>把 brief 发给我。</strong>
      <p>我会拆需求、查达人标签、生成 KOL 推荐、风险提示和客户可读方案。需要看完整图谱时点「全屏」。</p>
      <div class="agent-float-suggestions">
        <button type="button" data-agent-prompt="帮我根据这个 brief 推荐 8 个小红书/抖音 KOL，并说明风险。">推荐 KOL</button>
        <button type="button" data-agent-prompt="把这个项目变成一份客户可看的 KOL 方案。">生成方案</button>
        <button type="button" data-agent-prompt="检查这个 brief 的投放风险和预算风险。">查风险</button>
      </div>
    </article>
  `;
}

function renderAgentFloatRunCard(run, steps, artifacts) {
  const latestSteps = steps.slice(-5);
  const latestArtifacts = artifacts.slice(-4);
  return `
    <article class="agent-float-run-card ${escapeHTML(run.status || "idle")}">
      <div class="agent-float-run-head">
        <span>${escapeHTML(run.status || "idle")}</span>
        <strong>${fmtNumber(steps.length)} steps · ${fmtNumber(artifacts.length)} assets</strong>
      </div>
      <div class="agent-float-step-stack">
        ${
          latestSteps.length
            ? latestSteps
                .map(
                  (step, index) => `
                    <div class="agent-float-step ${escapeHTML(step.status || "pending")}">
                      <em>${String(index + 1).padStart(2, "0")}</em>
                      <span>${escapeHTML(step.title || step.tool_name || "工具步骤")}</span>
                    </div>
                  `
                )
                .join("")
            : '<div class="meta">等待工具步骤生成。</div>'
        }
      </div>
      ${
        latestArtifacts.length
          ? `<div class="agent-float-asset-row">${latestArtifacts
              .map((artifact) => `<span>${escapeHTML(artifact.title || artifact.artifact_type || "asset")}</span>`)
              .join("")}</div>`
          : ""
      }
    </article>
  `;
}

async function runAgentFromPayload(payload) {
  let data;
  if (state.activeAgentThread?.thread?.thread_id && !state.activeAgentThread.thread.metadata?.legacy_task) {
    data = await api(`/api/agent/threads/${state.activeAgentThread.thread.thread_id}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.activeAgentThread = data;
  } else {
    const thread = await api("/api/agent/threads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.activeAgentThread = thread;
    renderAgentMessages();
    data = await api("/api/agent/chat/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...payload, task_id: thread.task?.task_id || thread.thread?.task_id || "" }),
    });
  }
  renderAgentRun(data);
  startAgentPolling(data.run?.run_id);
  await loadAgentTasks();
  await refreshWorkspaceHistoryIfVisible();
  renderAgentFloatDock();
  return data;
}

async function runOpenClawFromPayload(payload) {
  stopOpenClawPolling();
  ensureOpenClawSession();
  const displayMessage = String(payload.message || payload.brief || "").trim();
  state.activeOpenClawRun = optimisticOpenClawRun(payload);
  state.openClawConversation.push({
    runId: state.activeOpenClawRun.run.run_id,
    user: displayMessage,
    assistant: "",
    status: "running",
    eventCount: state.activeOpenClawRun.events.length,
    pending: true,
  });
  syncActiveOpenClawSession({ status: "running" });
  state.activeOpenClawCampaignTarget = null;
  renderAgentMessages();
  renderAgentFloatDock();
  renderAgentOpenClawStatus();
  const openClawPayload = enrichOpenClawPayload(payload);
  let data;
  try {
    data = await apiWithTimeout(
      "/api/openclaw/chat",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...openClawPayload, async: true }),
      },
      20000
    );
  } catch (error) {
    state.activeOpenClawRun = {
      ...state.activeOpenClawRun,
      run: {
        ...(state.activeOpenClawRun?.run || {}),
        status: "failed",
        error: error.message || "OpenClaw 请求失败",
        updated_at: new Date().toISOString(),
      },
    };
    upsertOpenClawConversation(state.activeOpenClawRun, displayMessage);
    syncActiveOpenClawSession({ status: "failed" });
    renderAgentMessages();
    renderAgentFloatDock();
    renderAgentOpenClawStatus();
    throw error;
  }
  data.displayMessage = displayMessage;
  state.activeOpenClawRun = data;
  upsertOpenClawConversation(data, displayMessage);
  syncActiveOpenClawSession({ status: data.run?.status || "running", openclawSessionId: data.run?.openclaw_session_id || "" });
  state.activeOpenClawCampaignTarget = null;
  renderAgentMessages();
  renderAgentFloatDock();
  renderAgentOpenClawStatus();
  if (data.run?.run_id && data.run?.status === "running") startOpenClawPolling(data.run.run_id);
  await refreshWorkspaceHistoryIfVisible();
  return data;
}

async function previewAgentCreatorImport(file, message = "") {
  const session = ensureOpenClawSession();
  const form = new FormData();
  form.append("file", file);
  const data = await api("/api/agent/import/preview", { method: "POST", body: form });
  state.activeAgentImportPreview = data;
  state.openClawConversation = [
    ...(state.openClawConversation || []),
    {
      runId: data.import_id,
      user: message ? `${message}\n\n附件：${file.name}` : `上传达人文件：${file.name}`,
      assistant: "已生成达人导入预览。请先检查字段识别和数量，再确认导入达人库。",
      status: "preview",
      pending: false,
    },
  ].slice(-20);
  session.importPreview = data;
  syncActiveOpenClawSession({ status: "preview" });
  renderAgentFloatDock();
  return data;
}

async function commitAgentCreatorImport(importId) {
  const review = state.activeAgentImportPreview;
  if (!review?.import_id || review.import_id !== importId) throw new Error("找不到当前导入预览，请重新上传文件");
  const mappings = {};
  (review.sheets || []).forEach((sheet) => {
    mappings[sheet.sheet] = { enabled: true, mapping: sheet.mapping || {} };
  });
  const data = await api(`/api/agent/import/${encodeURIComponent(importId)}/commit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mappings, replace: false }),
  });
  state.activeAgentImportPreview = {
    ...review,
    status: "committed",
    imported: data.imported || 0,
    quality_report: data.quality_report || null,
  };
  state.openClawConversation = [
    ...(state.openClawConversation || []),
    {
      runId: `${importId}:commit`,
      user: "",
      assistant: `已导入 ${fmtNumber(data.imported || 0)} 个达人，达人库已刷新。`,
      status: "committed",
      pending: false,
    },
  ].slice(-20);
  syncActiveOpenClawSession({ status: "committed" });
  await reloadAll();
  renderAgentFloatDock();
  return data;
}

async function saveActiveOpenClawRunToCampaign(formSelector = "#agentChatForm") {
  const runId = state.activeOpenClawRun?.run?.run_id;
  if (!runId) throw new Error("没有可保存的 OpenClaw run");
  const form = $(formSelector);
  const payload = form ? formToObject(form) : {};
  const data = await api(`/api/openclaw/runs/${encodeURIComponent(runId)}/save-to-campaign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  state.activeOpenClawCampaignTarget = data.target || null;
  await refreshWorkspaceHistoryIfVisible();
  renderAgentOpenClawStatus();
  renderAgentFloatDock();
  return data;
}

async function viewActiveOpenClawAssets() {
  setAgentFloatOpen(false);
  if (state.activeOpenClawCampaignTarget?.view === "platformOS") {
    await loadPlatformDashboard();
    setView("platformOS");
    await openCampaignRoom(state.activeOpenClawCampaignTarget.id);
    return;
  }
  await loadWorkspaceHistory();
  setView("history");
}

function openNativeOpenClawOrWorkspace() {
  const hasNativeUi = Boolean(state.openClawDiagnostics?.checks?.control_ui_url || state.openClaw?.status?.control_ui_url);
  if (hasNativeUi) {
    window.open("/openclaw", "_blank", "noopener,noreferrer");
    return;
  }
  setAgentFloatOpen(false);
  setView("agentWorkspace");
  toast("OpenClaw 原生前端未配置，已切到 Agent Workspace");
}

function activeReasoningGraphArtifact() {
  return state.activeAgentArtifacts.find((artifact) => artifact.artifact_type === "reasoning_graph");
}

function renderAgentReasoningGraph() {
  const panel = $("#agentReasoningPanel");
  const artifact = activeReasoningGraphArtifact();
  if (!panel) return;
  if (!artifact?.payload?.nodes?.length) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");
  const graph = artifact.payload;
  const meta = $("#agentReasoningMeta");
  if (meta) meta.textContent = `${fmtNumber(graph.summary?.node_count)} nodes / ${fmtNumber(graph.summary?.edge_count)} edges`;
  if (!state.activeAgentGraphNodeId || !(graph.nodes || []).some((node) => node.id === state.activeAgentGraphNodeId)) {
    state.activeAgentGraphNodeId = graph.nodes[0]?.id || "";
  }
  renderAgentGraphInto("#agentReasoningGraphCanvas", graph);
  renderAgentReasoningInspector();
}

function renderAgentGraphInto(selector, graph) {
  const canvas = $(selector);
  if (!canvas) return;
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  if (!nodes.length) {
    canvas.innerHTML = '<div class="meta">暂无 Agent 推理图谱。</div>';
    return;
  }
  const width = 1280;
  const height = Math.max(680, Math.ceil(nodes.length / 4) * 132);
  const positioned = layoutAgentGraphNodes(nodes, width, height);
  const nodeMap = Object.fromEntries(positioned.map((node) => [node.id, node]));
  const edgeSvg = edges
    .filter((edge) => nodeMap[edge.source] && nodeMap[edge.target])
    .map((edge) => {
      const source = nodeMap[edge.source];
      const target = nodeMap[edge.target];
      const stroke = agentEdgeColor(edge.type);
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;
      return `
        <path class="agent-graph-edge" d="M ${source.x} ${source.y} C ${source.x + 90} ${source.y}, ${target.x - 90} ${target.y}, ${target.x} ${target.y}" fill="none" stroke="${stroke}" stroke-width="1.8" />
        <text x="${midX}" y="${midY - 8}" class="graph-edge-label">${escapeHTML(edge.label || edge.type || "")}</text>
      `;
    })
    .join("");
  const nodeSvg = positioned
    .map((node) => {
      const selected = state.activeAgentGraphNodeId === node.id ? " selected" : "";
      const serialized = `${node.id} ${node.type || ""} ${node.stage || ""} ${JSON.stringify(node.payload || {})}`.toLowerCase();
      const live = state.activeAgentToolName && serialized.includes(String(state.activeAgentToolName).toLowerCase()) ? " live" : "";
      const score = node.score ? `<tspan x="${node.x}" dy="15">score ${escapeHTML(node.score)}</tspan>` : "";
      return `
        <g class="graph-node agent-reasoning-node ${escapeHTML(node.type || "node")}${selected}${live}" data-agent-node-id="${escapeHTML(node.id)}" tabindex="0" role="button" aria-label="${escapeHTML(node.label)}">
          <rect x="${node.x - 58}" y="${node.y - 30}" width="116" height="60" rx="6"></rect>
          <text x="${node.x}" y="${node.y - 4}" text-anchor="middle">${escapeHTML(shortLabel(node.label))}${score}</text>
        </g>
      `;
    })
    .join("");
  canvas.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Agent 推理图谱">${edgeSvg}${nodeSvg}</svg>`;
}

function layoutAgentGraphNodes(nodes, width, height) {
  const lanes = {
    input: 0.07,
    analysis: 0.18,
    plan: 0.3,
    evidence: 0.43,
    ontology: 0.53,
    kol_match: 0.62,
    risk: 0.74,
    trace: 0.82,
    proposal: 0.9,
    memory: 0.96,
  };
  const grouped = nodes.reduce((acc, node) => {
    const lane = lanes[node.stage || "analysis"] === undefined ? 0.5 : lanes[node.stage || "analysis"];
    acc[lane] = acc[lane] || [];
    acc[lane].push(node);
    return acc;
  }, {});
  return nodes.map((node) => {
    const lane = lanes[node.stage || "analysis"] === undefined ? 0.5 : lanes[node.stage || "analysis"];
    const group = grouped[lane];
    const index = group.indexOf(node);
    const gap = height / (group.length + 1);
    return { ...node, x: Math.round(width * lane), y: Math.round(gap * (index + 1)) };
  });
}

function agentEdgeColor(type) {
  if (type === "risk") return "#ff3b30";
  if (type === "match") return "#7c3aed";
  if (type === "evidence") return "#2563eb";
  if (type === "memory") return "#0f766e";
  if (type === "trace") return "#111827";
  return "#64748b";
}

function renderAgentReasoningInspector() {
  const target = $("#agentReasoningInspector");
  const graph = activeReasoningGraphArtifact()?.payload || {};
  if (!target) return;
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const node = nodes.find((item) => item.id === state.activeAgentGraphNodeId) || nodes[0];
  if (!node) {
    target.innerHTML = '<div class="meta">点击节点查看推理依据。</div>';
    return;
  }
  state.activeAgentGraphNodeId = node.id;
  const related = edges.filter((edge) => edge.source === node.id || edge.target === node.id).slice(0, 8);
  target.innerHTML = `
    <div class="card-kicker">${escapeHTML(node.stage || "reasoning")} · ${escapeHTML(node.type || "node")}</div>
    <h3>${escapeHTML(node.label || node.id)}</h3>
    ${node.score ? `<div class="node-score">${fmtNumber(node.score)}</div>` : ""}
    <p>${escapeHTML(node.detail || "暂无详细说明。")}</p>
    ${renderInspectorPayload(node.payload || {})}
    <div class="inspector-links">
      <strong>关系</strong>
      ${related.map((edge) => `<span>${escapeHTML(edge.source === node.id ? "→" : "←")} ${escapeHTML(edge.label || edge.type || "relation")}</span>`).join("") || '<span>暂无关联边</span>'}
    </div>
  `;
}

function renderAgentArtifact(artifact) {
  const payload = artifact.payload || {};
  let detail = "";
  if (artifact.artifact_type === "plan") {
    detail = `
      <div class="agent-plan">
        <div class="status-pill ${payload.status === "ready" ? "ok" : "warn"}">${escapeHTML(payload.status || "planned")}</div>
        ${(payload.steps || [])
          .map(
            (step, index) => `
              <div class="agent-plan-step ${escapeHTML(step.status || "pending")}">
                <span>${String(index + 1).padStart(2, "0")}</span>
                <div>
                  <strong>${escapeHTML(step.label || step.id)}</strong>
                  <p>${escapeHTML(step.reason || "")}</p>
                </div>
              </div>
            `
          )
          .join("")}
      </div>
    `;
  } else if (artifact.artifact_type === "clarification") {
    detail = `
      <div class="agent-clarification">
        ${(payload.questions || []).map((question) => `<div class="feedback-item"><strong>需要补充</strong><p>${escapeHTML(question)}</p></div>`).join("")}
        <div class="meta">${escapeHTML(payload.suggested_reply_format || "")}</div>
      </div>
    `;
  } else if (artifact.artifact_type === "knowledge") {
    detail = (payload.items || [])
      .slice(0, 4)
      .map((item) => `<li>${escapeHTML(item.title)} <span>${escapeHTML(item.source)}</span></li>`)
      .join("");
    detail = `<ul class="agent-mini-list">${detail}</ul>`;
  } else if (artifact.artifact_type === "memory_recall") {
    const sources = payload.source_counts || {};
    detail = `
      <div class="agent-artifact-metrics">
        <span>召回 ${fmtNumber(payload.count)}</span>
        <span>来源 ${fmtNumber(Object.keys(sources).length)}</span>
      </div>
      <ul class="agent-mini-list">
        ${(payload.items || [])
          .slice(0, 5)
          .map((item) => `<li>${escapeHTML(item.title || item.document_id || "memory")} <span>${escapeHTML(item.source_type || item.source || "knowledge")}</span></li>`)
          .join("")}
      </ul>
    `;
  } else if (artifact.artifact_type === "agent_handoffs") {
    detail = `
      <div class="agent-handoff-list">
        ${(payload.agents || [])
          .map(
            (item) => `
              <article>
                <strong>${escapeHTML(item.role || item.name || "Agent")}</strong>
                <p>${escapeHTML(item.responsibility || item.summary || "")}</p>
                <span>${escapeHTML(item.status || "completed")}</span>
              </article>
            `
          )
          .join("")}
      </div>
    `;
  } else if (artifact.artifact_type === "tool_trace") {
    detail = `
      <div class="agent-trace-list">
        ${(payload.items || [])
          .map(
            (item) => `
              <div class="agent-trace-item ${escapeHTML(item.status || "completed")}">
                <strong>${escapeHTML(item.tool_name)}</strong>
                <span>${fmtNumber(item.elapsed_ms)}ms</span>
                <p>${escapeHTML(item.output_summary || item.error || "")}</p>
              </div>
            `
          )
          .join("")}
      </div>
    `;
  } else if (artifact.artifact_type === "project_run") {
    const summary = payload.summary || {};
    detail = `
      <div class="agent-artifact-metrics">
        <span>KOL ${fmtNumber(summary.matches)}</span>
        <span>叙事 ${fmtNumber(summary.narratives)}</span>
        <span>步骤 ${fmtNumber(summary.steps)}</span>
      </div>
    `;
  } else if (artifact.artifact_type === "deliverables") {
    const summary = payload.summary || {};
    const client = payload.client_card || {};
    const topics = payload.topic_cards || [];
    detail = `
      <div class="agent-artifact-metrics">
        <span>${escapeHTML(summary.business_type || "业务类型")}</span>
        <span>选题 ${fmtNumber(summary.topic_count || topics.length)}</span>
        <span>${escapeHTML(summary.package_name || "报价骨架")}</span>
      </div>
      <div class="meta">客户：${escapeHTML(client.client_name || "待补充")} · 预算 ${escapeHTML(client.budget_range || "待定")}</div>
      <ul class="agent-mini-list">
        ${topics
          .slice(0, 4)
          .map((topic, index) => `<li>${index + 1}. ${escapeHTML(topic.topic_title || "选题")} <span>${escapeHTML(topic.content_format || "")}</span></li>`)
          .join("")}
      </ul>
      <button class="secondary agent-deliverables-to-filter-btn" data-artifact-id="${escapeHTML(artifact.artifact_id)}" type="button">带入筛选达人</button>
    `;
  } else if (artifact.artifact_type === "proposal") {
    const summary = payload.summary || {};
    detail = `
      <div class="agent-artifact-metrics">
        <span>候选 ${fmtNumber(summary.candidate_count)}</span>
        <span>预算 ${fmtNumber(summary.budget_total)}</span>
      </div>
      <div class="meta">${escapeHTML(payload.proposal?.share_url || "")}</div>
    `;
  } else if (artifact.artifact_type === "memory_suggestions") {
    detail = `
      <div class="agent-memory-list">
        ${(payload.suggestions || [])
          .map((item, index) => {
            const committed = payload.committed?.[String(index)];
            return `
              <article class="agent-memory-item ${committed ? "committed" : ""}">
                <div class="card-kicker">${escapeHTML(item.source_type || "case")}</div>
                <strong>${escapeHTML(item.title || "记忆建议")}</strong>
                <textarea class="memory-edit-title" data-artifact-id="${escapeHTML(artifact.artifact_id)}" data-suggestion-index="${index}">${escapeHTML(item.title || "")}</textarea>
                <textarea class="memory-edit-content" data-artifact-id="${escapeHTML(artifact.artifact_id)}" data-suggestion-index="${index}">${escapeHTML(item.content || "")}</textarea>
                <input class="memory-edit-tags" data-artifact-id="${escapeHTML(artifact.artifact_id)}" data-suggestion-index="${index}" value="${escapeHTML((item.tags || []).join("，"))}" placeholder="标签，逗号分隔" />
                <div class="tag-list">${(item.tags || []).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
                ${
                  committed
                    ? `<div class="meta">已入库：${escapeHTML(committed.document_id || "")}</div>`
                    : `<button class="primary commit-memory-btn" data-artifact-id="${escapeHTML(artifact.artifact_id)}" data-suggestion-index="${index}" type="button">确认入库</button>`
                }
              </article>
            `;
          })
          .join("")}
      </div>
    `;
  } else if (artifact.artifact_type === "reasoning_graph") {
    const summary = payload.summary || {};
    detail = `
      <div class="agent-artifact-metrics">
        <span>节点 ${fmtNumber(summary.node_count)}</span>
        <span>关系 ${fmtNumber(summary.edge_count)}</span>
        <span>KOL ${fmtNumber(summary.kol_count)}</span>
        <span>风险 ${fmtNumber(summary.risk_count)}</span>
      </div>
    `;
  }
  return `
    <article class="agent-artifact-card">
      <div class="card-kicker">${escapeHTML(artifact.artifact_type)}</div>
      <div class="agent-artifact-head">
        <strong>${escapeHTML(artifact.title)}</strong>
        <button class="secondary open-artifact-detail-btn" data-artifact-id="${escapeHTML(artifact.artifact_id)}" type="button">详情</button>
      </div>
      <p>${escapeHTML(artifact.summary || "")}</p>
      ${detail}
    </article>
  `;
}

function openArtifactModal(artifactId) {
  const artifact = state.activeAgentArtifacts.find((item) => item.artifact_id === artifactId);
  if (!artifact) return;
  state.activeArtifactDetail = artifact;
  $("#artifactModalTitle").textContent = artifact.title || artifact.artifact_type;
  $("#artifactModalMeta").textContent = `${artifact.artifact_type} · ${artifact.artifact_id}`;
  $("#artifactModalBody").textContent = JSON.stringify(artifact.payload || {}, null, 2);
  $("#artifactModal").classList.remove("hidden");
}

function closeArtifactModal() {
  $("#artifactModal")?.classList.add("hidden");
  state.activeArtifactDetail = null;
}

function renderKnowledge() {
  renderKnowledgeStats();
  renderKnowledgeDocuments();
  renderKnowledgeSearchResults();
}

function renderKnowledgeStats() {
  const node = $("#knowledgeStats");
  if (!node) return;
  const stats = state.knowledgeStats || {};
  const bySource = stats.source_counts || {};
  node.innerHTML = `
    <div>
      <span>文档</span>
      <strong>${fmtNumber(stats.documents)}</strong>
    </div>
    <div>
      <span>Chunks</span>
      <strong>${fmtNumber(stats.chunks)}</strong>
    </div>
    <div>
      <span>来源类型</span>
      <strong>${fmtNumber(Object.keys(bySource).length)}</strong>
    </div>
  `;
}

function renderKnowledgeDocuments() {
  const list = $("#knowledgeDocumentList");
  if (!list) return;
  if (!state.knowledgeDocuments.length) {
    list.innerHTML = emptyState("暂无知识文档", "先写入客户偏好、行业案例、风险规则或方案模板。");
    return;
  }
  list.innerHTML = state.knowledgeDocuments
    .map((doc) => {
      const tags = (doc.tags || []).slice(0, 6).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("");
      return `
        <article class="knowledge-card">
          <div class="card-kicker">${escapeHTML(doc.source_type || "manual")} · ${escapeHTML(doc.industry || "通用")}</div>
          <div class="creator-card-head">
            <h3>${escapeHTML(doc.title || "未命名知识")}</h3>
            <button class="secondary open-knowledge-doc-btn" data-document-id="${escapeHTML(doc.document_id)}" type="button">详情</button>
          </div>
          <p>${escapeHTML(doc.summary || "已切分为可检索知识片段，点击详情查看 chunk 内容。").slice(0, 160)}</p>
          <div class="tag-list">${tags || '<span class="meta">暂无标签</span>'}</div>
          <div class="meta">${escapeHTML(doc.client_id || "无客户绑定")} · ${fmtNumber(doc.chunk_count || 0)} chunks · ${escapeHTML(doc.updated_at || "")}</div>
        </article>
      `;
    })
    .join("");
}

function renderKnowledgeSearchResults() {
  const node = $("#knowledgeSearchResults");
  if (!node) return;
  if (!state.knowledgeSearchResults.length) {
    node.innerHTML = emptyState("暂无检索结果", "输入问题后会按关键词和本地向量相似度混合排序。");
    return;
  }
  node.innerHTML = state.knowledgeSearchResults
    .map((item, index) => {
      const tags = (item.tags || []).slice(0, 5).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("");
      return `
        <article class="knowledge-result">
          <div class="knowledge-rank">${String(index + 1).padStart(2, "0")}</div>
          <div>
            <div class="card-kicker">${escapeHTML(item.source_type || item.source || "knowledge")} · score ${Math.round(Number(item.score || 0) * 100)}</div>
            <strong>${escapeHTML(item.title || "知识片段")}</strong>
            <p>${escapeHTML(item.content || item.summary || "")}</p>
            <div class="tag-list">${tags}</div>
            <div class="meta">${escapeHTML(item.industry || "通用")} · ${escapeHTML(item.document_id || item.ref_id || "")}</div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderKnowledgeDetail(data) {
  const doc = data.document || {};
  const chunks = data.chunks || [];
  state.knowledgeSearchResults = chunks.map((chunk) => ({
    ...chunk,
    title: doc.title || chunk.title,
    source_type: doc.source_type,
    industry: doc.industry,
    tags: doc.tags,
    score: chunk.score || 1,
  }));
  renderKnowledgeSearchResults();
  toast(`已加载知识详情：${doc.title || doc.document_id}`);
}

function stopAgentPolling() {
  if (state.agentEventSource) {
    state.agentEventSource.close();
    state.agentEventSource = null;
  }
  if (state.agentPollTimer) {
    clearInterval(state.agentPollTimer);
    state.agentPollTimer = null;
  }
}

function stopOpenClawPolling() {
  if (state.openClawEventSource) {
    state.openClawEventSource.close();
    state.openClawEventSource = null;
  }
  if (state.openClawPollTimer) {
    clearInterval(state.openClawPollTimer);
    state.openClawPollTimer = null;
  }
}

async function loadAgentThread(threadId) {
  if (!threadId) return null;
  const data = await api(`/api/agent/threads/${threadId}`);
  state.activeAgentThread = data;
  state.activeAgentArtifacts = data.artifacts || [];
  renderAgentTasks();
  renderAgentMessages();
  renderAgentArtifacts();
  renderAgentReasoningGraph();
  renderAgentFloatDock();
  return data;
}

function startAgentPolling(runId) {
  stopAgentPolling();
  if (!runId) return;
  if (window.EventSource) {
    const tenant = encodeURIComponent(state.tenant || "default");
    const source = new EventSource(`/api/agent/runs/${encodeURIComponent(runId)}/stream?tenant=${tenant}`);
    state.agentEventSource = source;
    source.addEventListener("agent_run", async (event) => {
      const data = JSON.parse(event.data || "{}");
      renderAgentRun(data);
      const status = data.run?.status || "";
      if (status && status !== "running") {
        stopAgentPolling();
        const threadId = state.activeAgentThread?.thread?.thread_id;
        if (threadId) await loadAgentThread(threadId);
        await loadAgentTasks();
        await refreshWorkspaceHistoryIfVisible();
      }
    });
    source.addEventListener("agent_error", (event) => {
      stopAgentPolling();
      toast(JSON.parse(event.data || "{}").detail || "Agent stream error", true);
    });
    source.onerror = () => {
      if (!state.agentEventSource) return;
      source.close();
      state.agentEventSource = null;
      startAgentPollFallback(runId);
    };
    return;
  }
  startAgentPollFallback(runId);
}

function startAgentPollFallback(runId) {
  if (!runId) return;
  const tick = async () => {
    try {
      const data = await api(`/api/agent/runs/${runId}`);
      renderAgentRun(data);
      const status = data.run?.status || "";
      if (!["running"].includes(status)) {
        stopAgentPolling();
        const threadId = state.activeAgentThread?.thread?.thread_id;
        if (threadId) await loadAgentThread(threadId);
        await loadAgentTasks();
        await refreshWorkspaceHistoryIfVisible();
      }
    } catch (error) {
      stopAgentPolling();
      toast(error.message, true);
    }
  };
  tick();
  state.agentPollTimer = setInterval(tick, 1000);
}

function startOpenClawPolling(runId) {
  stopOpenClawPolling();
  if (!runId) return;
  if (window.EventSource) {
    const tenant = encodeURIComponent(state.tenant || "default");
    const source = new EventSource(`/api/openclaw/runs/${encodeURIComponent(runId)}/stream?tenant=${tenant}`);
    state.openClawEventSource = source;
    source.addEventListener("openclaw_run", async (event) => {
      const data = JSON.parse(event.data || "{}");
      state.activeOpenClawRun = data;
      upsertOpenClawConversation(data);
      syncActiveOpenClawSession({ status: data.run?.status || "running", openclawSessionId: data.run?.openclaw_session_id || "" });
      renderAgentMessages();
      renderAgentFloatDock();
      renderAgentOpenClawStatus();
      const status = data.run?.status || "";
      if (status && status !== "running") {
        stopOpenClawPolling();
        await refreshOpenClawRun(runId);
        await refreshWorkspaceHistoryIfVisible();
      }
    });
    source.addEventListener("agent_error", (event) => {
      stopOpenClawPolling();
      toast(JSON.parse(event.data || "{}").detail || "OpenClaw stream error", true);
    });
    source.onerror = () => {
      if (!state.openClawEventSource) return;
      source.close();
      state.openClawEventSource = null;
      startOpenClawPollFallback(runId);
    };
    return;
  }
  startOpenClawPollFallback(runId);
}

function startOpenClawPollFallback(runId) {
  if (!runId) return;
  const tick = async () => {
    try {
      const data = await api(`/api/openclaw/runs/${encodeURIComponent(runId)}/events`);
      state.activeOpenClawRun = data;
      upsertOpenClawConversation(data);
      syncActiveOpenClawSession({ status: data.run?.status || "running", openclawSessionId: data.run?.openclaw_session_id || "" });
      renderAgentMessages();
      renderAgentFloatDock();
      renderAgentOpenClawStatus();
      const status = data.run?.status || "";
      if (status && status !== "running") {
        stopOpenClawPolling();
        await refreshOpenClawRun(runId);
        await refreshWorkspaceHistoryIfVisible();
      }
    } catch (error) {
      stopOpenClawPolling();
      toast(error.message || "OpenClaw 轮询失败", true);
    }
  };
  tick();
  state.openClawPollTimer = setInterval(tick, 1200);
}

async function refreshOpenClawRun(runId) {
  if (!runId) return null;
  await new Promise((resolve) => setTimeout(resolve, 250));
  const data = await api(`/api/openclaw/runs/${encodeURIComponent(runId)}/events`);
  state.activeOpenClawRun = data;
  upsertOpenClawConversation(data);
  syncActiveOpenClawSession({ status: data.run?.status || "running", openclawSessionId: data.run?.openclaw_session_id || "" });
  renderAgentMessages();
  renderAgentFloatDock();
  renderAgentOpenClawStatus();
  return data;
}

function formToObject(form) {
  const formData = new FormData(form);
  const obj = {};
  for (const [key, value] of formData.entries()) {
    obj[key] = value;
  }
  ["follower_count", "listed_price"].forEach((key) => {
    if (obj[key]) obj[key] = Number(obj[key]);
  });
  return obj;
}

async function reloadCore() {
  await loadCreators();
  await loadCases();
}

async function reloadSecondary() {
  await Promise.all([
    loadImportTemplates(),
    loadGovernance(),
    loadSymbolicEngines(),
    loadAgentTasks(),
    loadAgentRuntime(),
    loadKnowledge(),
    loadCollaboration(),
    loadOrganization(),
    loadCommercial(),
    loadDistribution(),
    loadPlatformDashboard(),
    loadDataSources(),
    loadSymbolicOS(),
    loadKolIntelligence(),
  ]);
}

async function reloadAll({ backgroundSecondary = false } = {}) {
  await refreshStatus();
  const auth = await loadAuthMe();
  const needsLogin = state.authRequired && !auth.authenticated && !state.accessKey;
  if (needsLogin) {
    showAccessGate("请用内部或甲方账号登录后继续使用。");
    renderCreatorListAuthRequired();
    return;
  }
  if (state.currentIdentity?.user?.user_type === "client") {
    await loadClientPortalProjects();
    setView("clientPortal");
    return;
  }
  state.creatorsFetchAttempted = false;
  try {
    await reloadCore();
  } catch (error) {
    console.error("reload core failed", error);
  }
  if (backgroundSecondary) {
    reloadSecondary().catch((error) => {
      console.error("background reload failed", error);
    });
    return;
  }
  await reloadSecondary();
}

function renderResults(data) {
  $("#briefParsed").textContent = JSON.stringify(data.brief, null, 2);
  const tbody = $("#resultTable tbody");
  tbody.innerHTML = data.results
    .map(
      (row) => `
        <tr>
          <td>${row["达人"]}</td>
          <td>${row["平台"]}</td>
          <td><strong>${row["匹配分"]}</strong></td>
          <td>${row["等级"]}</td>
          <td>${row["推荐角色"]}</td>
          <td>${fmtNumber(row["建议预算"])}</td>
          <td>${row["报价判断"]}</td>
          <td>${row["数据可信度"]}</td>
          <td>${row["推荐理由"]}</td>
        </tr>
      `
    )
    .join("");
  state.lastProposal = data.proposal;
  $("#proposalOutput").value = data.proposal;
}

function renderSymbolicResults(data) {
  state.lastBrand = data.brand;
  state.lastSymbolicResults = data.results || [];
  state.lastNarratives = data.narratives || [];
  const tbody = $("#symbolicResultTable tbody");
  tbody.innerHTML = state.lastSymbolicResults
    .map(
      (row) => `
        <tr>
          <td>${row.creator_name}</td>
          <td><strong>${row.symbolic_score}</strong></td>
          <td>${row.recommendation_level}</td>
          <td>${(row.matched_brand_tags || []).join("、")}</td>
          <td>${row.metaphor_relation}</td>
          <td>${row.metonymy_relation}</td>
          <td>${row.match_reason}</td>
          <td>${(row.risk_points || []).join("；")}</td>
        </tr>
      `
    )
    .join("");
  $("#narrativeOutput").textContent = JSON.stringify(state.lastNarratives, null, 2);
  renderSymbolicGraphFromState();
}

function renderBrandCalibration(calibration) {
  const node = $("#brandCalibrationSummary");
  if (!node) return;
  node.classList.remove("hidden");
  if (!calibration?.applied) {
    node.innerHTML = `<div class="meta">${escapeHTML(calibration?.message || "暂无社会校准结果")}</div>`;
    return;
  }
  node.innerHTML = `
    <div class="card-kicker">social calibration</div>
    <strong>${escapeHTML(calibration.message || "已完成社会校准")}</strong>
    <div class="tag-list">${(calibration.added_target_tags || []).slice(0, 5).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
    <div class="tag-list">${(calibration.added_danger_tags || []).slice(0, 4).map((tag) => `<span class="tag danger">${escapeHTML(tag)}</span>`).join("")}</div>
  `;
}

function renderSymbolicEditor(kind, profile) {
  const container = kind === "creator" ? $("#creatorSymbolicEditor") : $("#brandSymbolicEditor");
  const fields = SYMBOLIC_EDITOR_FIELDS[kind];
  container.classList.remove("hidden");
  container.innerHTML = fields
    .map(([field, label, type]) => {
      const value = profile?.[field] ?? (type === "tags" ? [] : "");
      if (type === "tags") {
        return `
          <label class="symbolic-field">
            <span>${label}</span>
            <input data-symbolic-kind="${kind}" data-symbolic-field="${field}" data-symbolic-type="tags" value="${escapeHTML((value || []).join("，"))}" placeholder="用逗号分隔" />
            <div class="chip-preview">${renderChips(value || [])}</div>
          </label>
        `;
      }
      if (type === "textarea") {
        return `
          <label class="symbolic-field wide">
            <span>${label}</span>
            <textarea data-symbolic-kind="${kind}" data-symbolic-field="${field}" data-symbolic-type="textarea">${escapeHTML(value || "")}</textarea>
          </label>
        `;
      }
      return `
        <label class="symbolic-field">
          <span>${label}</span>
          <input data-symbolic-kind="${kind}" data-symbolic-field="${field}" data-symbolic-type="text" value="${escapeHTML(value || "")}" />
        </label>
      `;
    })
    .join("");
}

function renderChips(items) {
  const list = Array.isArray(items) ? items : splitInputList(items);
  return list.map((item) => `<span class="tag">${escapeHTML(item)}</span>`).join("") || '<span class="meta">暂无</span>';
}

function splitInputList(value) {
  return String(value || "")
    .replaceAll("，", ",")
    .replaceAll("、", ",")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function collectSymbolicEditor(kind, baseProfile) {
  const profile = { ...(baseProfile || {}) };
  $$(`[data-symbolic-kind="${kind}"]`).forEach((field) => {
    const key = field.dataset.symbolicField;
    if (field.dataset.symbolicType === "tags") {
      profile[key] = splitInputList(field.value);
    } else {
      profile[key] = field.value;
    }
  });
  return profile;
}

function syncSymbolicJson(kind) {
  if (kind === "creator" && state.lastCreatorSymbolic) {
    state.lastCreatorSymbolic = collectSymbolicEditor("creator", state.lastCreatorSymbolic);
    $("#creatorSymbolicOutput").value = JSON.stringify(state.lastCreatorSymbolic, null, 2);
  }
  if (kind === "brand" && state.lastBrand) {
    state.lastBrand = collectSymbolicEditor("brand", state.lastBrand);
    $("#brandSymbolicOutput").value = JSON.stringify(state.lastBrand, null, 2);
  }
}

async function refreshSymbolicMatch() {
  const payload = state.lastBrand || formToObject($("#brandSymbolicForm"));
  payload.use_social_context = Boolean(state.symbolicOS?.latest_report);
  const data = await api("/api/symbolic/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (data.calibration?.applied) renderBrandCalibration(data.calibration);
  renderSymbolicResults(data);
  return data;
}

async function renderSymbolicGraphFromState() {
  if (!state.lastBrand || !state.lastSymbolicResults.length) return;
  const graph = await api("/api/symbolic/graph", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      brand: state.lastBrand,
      matches: state.lastSymbolicResults,
      narratives: state.lastNarratives,
      social_context: state.symbolicOS?.latest_report || null,
      product_context: state.symbolicOS?.products?.[0] || null,
    }),
  });
  state.lastSymbolicGraph = graph;
  renderSymbolicGraph(graph);
}

function renderSymbolicGraph(graph) {
  renderSymbolicGraphInto("#symbolicGraphCanvas", graph);
}

function clampNumber(value, min, max) {
  return Math.min(max, Math.max(min, Number(value || 0)));
}

function projectRunGraphFitScale(width, height) {
  const canvas = $("#projectRunGraphCanvas");
  if (!canvas) return 1;
  const availableWidth = Math.max(320, canvas.clientWidth - 28);
  const availableHeight = Math.max(360, canvas.clientHeight - 28);
  return clampNumber(Math.min(availableWidth / width, availableHeight / height, 1), 0.42, 1.35);
}

function updateProjectRunZoomLabel() {
  const label = $("#projectRunGraphZoomLabel");
  if (!label) return;
  label.textContent = `${Math.round((state.projectRunGraphScale || 1) * 100)}%${state.projectRunGraphAutoFit ? " auto" : ""}`;
  label.title = "在画布内滚动鼠标或触控板即可缩放";
}

function zoomProjectRunGraph(nextScale, anchor = null) {
  if (!state.projectRun?.graph) return;
  const canvas = $("#projectRunGraphCanvas");
  const previousScale = clampNumber(state.projectRunGraphScale || 1, 0.42, 2.2);
  state.projectRunGraphAutoFit = false;
  state.projectRunGraphScale = clampNumber(nextScale, 0.42, 2.2);
  const ratio = state.projectRunGraphScale / previousScale;
  const before = anchor && canvas ? { left: canvas.scrollLeft, top: canvas.scrollTop, x: anchor.x, y: anchor.y } : null;
  renderSymbolicGraphInto("#projectRunGraphCanvas", state.projectRun.graph);
  if (before && canvas && Number.isFinite(ratio)) {
    canvas.scrollLeft = (before.left + before.x) * ratio - before.x;
    canvas.scrollTop = (before.top + before.y) * ratio - before.y;
  }
}

function renderSymbolicGraphInto(selector, graph) {
  const canvas = $(selector);
  if (!canvas) return;
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  if (!nodes.length) {
    canvas.innerHTML = '<div class="meta">暂无图谱数据。</div>';
    return;
  }
  const width = 1180;
  const height = Math.max(620, Math.ceil(nodes.length / 5) * 150);
  if (selector === "#projectRunGraphCanvas" && state.projectRunGraphAutoFit) {
    state.projectRunGraphScale = projectRunGraphFitScale(width, height);
  }
  const scale = selector === "#projectRunGraphCanvas" ? clampNumber(state.projectRunGraphScale || 1, 0.42, 2.2) : 1;
  const positioned = layoutGraphNodes(nodes, width, height);
  const nodeMap = Object.fromEntries(positioned.map((node) => [node.id, node]));
  const edgeSvg = edges
    .filter((edge) => nodeMap[edge.source] && nodeMap[edge.target])
    .map((edge) => {
      const source = nodeMap[edge.source];
      const target = nodeMap[edge.target];
      const stroke = edge.type === "risk" ? "#b42318" : edge.type === "match" ? "#0f766e" : "#94a3b8";
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;
      const dimmed =
        selector === "#projectRunGraphCanvas" &&
        state.projectRunStageFilter &&
        source.stage !== state.projectRunStageFilter &&
        target.stage !== state.projectRunStageFilter;
      return `
        <line class="graph-edge${dimmed ? " dimmed" : ""}" x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}" stroke="${stroke}" stroke-width="1.5" />
        <text x="${midX}" y="${midY - 5}" class="graph-edge-label${dimmed ? " dimmed" : ""}">${escapeHTML(edge.label)}</text>
      `;
    })
    .join("");
  const nodeSvg = positioned
    .map((node) => {
      const cls = `graph-node ${node.type}`;
      const score = node.score ? `<tspan x="${node.x}" dy="16">score ${node.score}</tspan>` : "";
      const selected = selector === "#projectRunGraphCanvas" && state.projectRunSelectedNodeId === node.id ? " selected" : "";
      const dimmed = selector === "#projectRunGraphCanvas" && state.projectRunStageFilter && node.stage !== state.projectRunStageFilter ? " dimmed" : "";
      return `
        <g class="${cls}${selected}${dimmed}" data-node-id="${escapeHTML(node.id)}" tabindex="0" role="button" aria-label="${escapeHTML(node.label)}">
          <circle cx="${node.x}" cy="${node.y}" r="${nodeRadius(node)}"></circle>
          <text x="${node.x}" y="${node.y - 4}" text-anchor="middle">${escapeHTML(shortLabel(node.label))}${score}</text>
        </g>
      `;
    })
    .join("");
  canvas.innerHTML = `<svg width="${Math.round(width * scale)}" height="${Math.round(height * scale)}" viewBox="0 0 ${width} ${height}" role="img" aria-label="符号关系图谱">${edgeSvg}${nodeSvg}</svg>`;
  if (selector === "#projectRunGraphCanvas") updateProjectRunZoomLabel();
}

function renderSymbolicEngines(data) {
  const status = $("#engineStatus");
  if (!status) return;
  const glmText = data.glm?.configured ? `GLM 已配置：${data.glm.model}` : "GLM 未配置，符号生成使用规则 fallback";
  const engines = data.stress_engines || [];
  const mirofish = engines.find((engine) => engine.id === "mirofish");
  const mirofishText = mirofish?.available ? "MiroFish CLI 可用" : "MiroFish CLI 未安装，压力测试会自动使用 fallback";
  status.innerHTML = `
    <span class="status-pill ${data.glm?.configured ? "ok" : "warn"}">${escapeHTML(glmText)}</span>
    <span class="status-pill ${mirofish?.available ? "ok" : "warn"}">${escapeHTML(mirofishText)}</span>
  `;
  const select = $("#stressEngine");
  if (select && mirofish) {
    Array.from(select.options).forEach((option) => {
      if (option.value === "mirofish") option.disabled = !mirofish.available;
    });
    if (select.value === "mirofish" && !mirofish.available) select.value = "llm_fallback";
  }
}

function renderSimulationReport(report) {
  state.lastSimulationReport = report;
  const badge = $("#simulationEngineBadge");
  if (badge) {
    const isFallback = String(report.engine || "").includes("fallback");
    badge.className = `status-pill ${isFallback ? "warn" : "ok"}`;
    badge.textContent = `${report.engine || "simulation"} · ${report.engine_status || "ready"}`;
  }
  $("#simulationSummary").innerHTML = `
    <strong>${escapeHTML(report.summary || "暂无结论")}</strong>
    <p>${escapeHTML(report.final_recommendation || "推演结果仅作为投放前压力测试参考。")}</p>
  `;
  renderList("#simulationPositiveList", report.positive_reactions || []);
  renderList("#simulationNegativeList", report.negative_reactions || []);
  renderSimulationGraph(report);
  renderSimulationTimeline(report.timeline || []);
  renderAgentReactions(report.agent_reactions || []);
  renderRiskAndSuggestions(report);
  $("#stressOutput").textContent = JSON.stringify(report, null, 2);
}

function renderList(selector, items) {
  const node = $(selector);
  if (!node) return;
  node.innerHTML = items.length ? items.map((item) => `<li>${escapeHTML(item)}</li>`).join("") : "<li>暂无</li>";
}

function renderSimulationGraph(report) {
  const canvas = $("#simulationGraphCanvas");
  if (!canvas) return;
  const nodes = report.nodes || [];
  const edges = report.edges || [];
  if (!nodes.length) {
    canvas.innerHTML = '<div class="meta">暂无推演图谱数据。</div>';
    return;
  }
  const width = 1120;
  const height = Math.max(560, Math.ceil(nodes.length / 4) * 150);
  const positioned = layoutSimulationNodes(nodes, width, height);
  const nodeMap = Object.fromEntries(positioned.map((node) => [node.node_id || node.id, node]));
  const edgeSvg = edges
    .filter((edge) => nodeMap[edge.source] && nodeMap[edge.target])
    .map((edge) => {
      const source = nodeMap[edge.source];
      const target = nodeMap[edge.target];
      const stroke = simulationEdgeColor(edge.edge_type || edge.type);
      const width = Math.max(1.5, Math.min(5, Number(edge.intensity || edge.weight || 50) / 22));
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;
      return `
        <path d="M ${source.x} ${source.y} C ${source.x + 80} ${source.y}, ${target.x - 80} ${target.y}, ${target.x} ${target.y}" fill="none" stroke="${stroke}" stroke-width="${width}" />
        <text x="${midX}" y="${midY - 8}" class="graph-edge-label">${escapeHTML(edge.label)}</text>
      `;
    })
    .join("");
  const nodeSvg = positioned
    .map((node) => {
      const id = node.node_id || node.id;
      const cls = `simulation-node ${escapeHTML(node.node_type || node.type || "agent")} ${escapeHTML(node.stance || "neutral")}`;
      const score = node.score ? `<tspan x="${node.x}" dy="16">${escapeHTML(node.risk_level || "medium")} · ${node.score}</tspan>` : "";
      return `
        <g class="${cls}" data-node-id="${escapeHTML(id)}">
          <rect x="${node.x - 62}" y="${node.y - 32}" width="124" height="64" rx="4"></rect>
          <text x="${node.x}" y="${node.y - 4}" text-anchor="middle">${escapeHTML(shortLabel(node.label))}${score}</text>
        </g>
      `;
    })
    .join("");
  canvas.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="传播推演图谱">${edgeSvg}${nodeSvg}</svg>`;
}

function layoutSimulationNodes(nodes, width, height) {
  const lanes = {
    brand: 0.08,
    product: 0.22,
    creator: 0.38,
    narrative: 0.52,
    target_tag: 0.52,
    audience: 0.68,
    comment: 0.82,
    risk_tag: 0.9,
    guardrail: 0.96,
  };
  const grouped = nodes.reduce((acc, node) => {
    const lane = lanes[node.node_type || node.type] === undefined ? 0.5 : lanes[node.node_type || node.type];
    acc[lane] = acc[lane] || [];
    acc[lane].push(node);
    return acc;
  }, {});
  return nodes.map((node) => {
    const lane = lanes[node.node_type || node.type] === undefined ? 0.5 : lanes[node.node_type || node.type];
    const group = grouped[lane];
    const index = group.indexOf(node);
    const gap = height / (group.length + 1);
    return { ...node, x: Math.round(width * lane), y: Math.round(gap * (index + 1)) };
  });
}

function simulationEdgeColor(type) {
  if (type === "risk") return "#ff3b30";
  if (type === "positive") return "#00a676";
  if (type === "feedback") return "#3858ff";
  return "#17120d";
}

function renderSimulationTimeline(events) {
  const node = $("#simulationTimeline");
  if (!node) return;
  if (!events.length) {
    node.innerHTML = '<div class="meta">暂无推演事件。</div>';
    return;
  }
  node.innerHTML = events
    .sort((a, b) => Number(a.step || 0) - Number(b.step || 0))
    .map(
      (event) => `
        <article class="timeline-card ${escapeHTML(event.sentiment || "neutral")}">
          <span>${escapeHTML(event.step || "")}</span>
          <div>
            <strong>${escapeHTML(event.title || event.event_type)}</strong>
            <div class="meta">${escapeHTML(event.actor)} · ${escapeHTML(event.event_type)} · ${escapeHTML(event.risk_level)}</div>
            <p>${escapeHTML(event.detail)}</p>
          </div>
        </article>
      `
    )
    .join("");
}

function renderAgentReactions(reactions) {
  const node = $("#agentReactionGrid");
  if (!node) return;
  if (!reactions.length) {
    node.innerHTML = '<div class="meta">暂无角色反馈。</div>';
    return;
  }
  node.innerHTML = reactions
    .map(
      (item) => `
        <article class="agent-reaction-card ${escapeHTML(item.stance || "neutral")}">
          <span class="card-kicker">${escapeHTML(item.role)}</span>
          <strong>${escapeHTML(item.agent_name)}</strong>
          <p>${escapeHTML(item.quote)}</p>
          <div class="tag-list">${(item.risk_flags || []).map((risk) => `<span class="tag danger">${escapeHTML(risk)}</span>`).join("")}</div>
        </article>
      `
    )
    .join("");
}

function renderRiskAndSuggestions(report) {
  const risks = $("#simulationRiskList");
  const suggestions = $("#simulationSuggestions");
  if (risks) {
    const items = [...(report.risk_points || []), ...(report.misreading_points || [])];
    risks.innerHTML = items.length
      ? `<h3>风险点</h3>${items.map((item) => `<div class="risk-item">${escapeHTML(item)}</div>`).join("")}`
      : '<div class="meta">暂无风险点。</div>';
  }
  if (suggestions) {
    suggestions.innerHTML = (report.optimization_suggestions || []).length
      ? `<h3>优化动作</h3>${(report.optimization_suggestions || []).map((item) => `<div class="suggestion-item">${escapeHTML(item)}</div>`).join("")}`
      : '<div class="meta">暂无优化建议。</div>';
  }
}

function demoSimulationPayload(engine = "llm_fallback") {
  return {
    engine,
    brand: {
      brand_name: "年轻新能源品牌",
      product: "智能 SUV",
      target_tags: ["城市自由", "科技感", "年轻家庭"],
      danger_tags: ["硬广感", "价格争议", "参数堆砌"],
    },
    matches: [
      {
        creator_name: "城市通勤研究所",
        risk_points: ["参数堆砌"],
        symbolic_score: 82,
        recommended_role: "真实试用主叙事",
      },
      {
        creator_name: "周末生活方式",
        risk_points: ["场景过散"],
        symbolic_score: 74,
        recommended_role: "生活方式补充触达",
      },
      {
        creator_name: "科技产品笔记",
        risk_points: ["专业表达太重"],
        symbolic_score: 69,
        recommended_role: "智能体验解释节点",
      },
    ],
    narratives: [{ narrative_path: "城市通勤痛点 -> 真实试用 -> 智能体验 -> 年轻家庭决策" }],
  };
}

async function runSimulation(payload) {
  const data = await api("/api/symbolic/stress-test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  renderSimulationReport(data.report);
  return data.report;
}

function renderCollaborationList() {
  const list = $("#collabProposalList");
  if (!list) return;
  if (!state.collabProposals.length) {
    list.innerHTML = emptyState("暂无协作方案", "先创建一个客户协作方案，再把链接发给甲方。");
    return;
  }
  list.innerHTML = state.collabProposals
    .map(
      (proposal) => `
        <div class="template-item">
          <div>
            <span class="card-kicker">Client room</span>
            <strong>${escapeHTML(proposal.project_name)}</strong>
            <div class="meta">${escapeHTML(proposal.client_name)} · ${escapeHTML(proposal.status)} · ${proposal.feedback_count || 0} 条反馈</div>
            <div class="meta">token: ${escapeHTML(proposal.share_token)}</div>
          </div>
          <button class="secondary open-proposal-btn" data-proposal-id="${escapeHTML(proposal.proposal_id)}" type="button">查看</button>
        </div>
      `
    )
    .join("");
}

function renderCommercial() {
  const invitationList = $("#commercialInvitationList");
  if (invitationList) {
    invitationList.innerHTML = state.commercialInvitations.length
      ? state.commercialInvitations
          .map(
            (item) => `
              <div class="template-item">
                <div>
                  <span class="card-kicker">Invite link</span>
                  <strong>${escapeHTML(item.creator_name || item.creator_id)}</strong>
                  <div class="meta">${escapeHTML(item.status)} · token: ${escapeHTML(item.token)}</div>
                </div>
                <button class="secondary copy-token-btn" data-target="#creatorInviteTokenInput" data-token="${escapeHTML(item.token)}" type="button">填入</button>
              </div>
            `
          )
          .join("")
      : emptyState("暂无邀请", "选择一个高频合作博主，生成商业档案邀请。");
  }
  const submissionList = $("#commercialSubmissionList");
  if (!submissionList) return;
  submissionList.innerHTML = state.commercialSubmissions.length
    ? state.commercialSubmissions
        .map(
          (item) => `
            <div class="feedback-item">
              <strong>${escapeHTML(item.creator_id)} · ${escapeHTML(item.status)}</strong>
              <div class="meta">案例 ${item.cases?.length || 0} 个 · ${escapeHTML(item.created_at || "")}</div>
              <div>${escapeHTML(item.ai_profile?.commercial_positioning || "待生成商业画像")}</div>
              <div class="decision-actions">
                <button class="primary review-commercial-btn" data-submission-id="${escapeHTML(item.submission_id)}" data-decision="approved" type="button">审核通过</button>
                <button class="secondary review-commercial-btn" data-submission-id="${escapeHTML(item.submission_id)}" data-decision="rejected" type="button">驳回</button>
                <button class="secondary open-commercial-profile-btn" data-creator-id="${escapeHTML(item.creator_id)}" type="button">看商业主页</button>
              </div>
            </div>
          `
        )
        .join("")
    : emptyState("暂无博主提交", "博主打开邀请链接后，提交内容会出现在这里。");
}

function renderDistributionList() {
  const list = $("#distributionBriefList");
  if (!list) return;
  list.innerHTML = state.distributionBriefs.length
    ? state.distributionBriefs
        .map(
          (item) => `
            <div class="template-item">
              <div>
                <span class="card-kicker">Brief push</span>
                <strong>${escapeHTML(item.project_name)}</strong>
                <div class="meta">${escapeHTML(item.client_name)} · ${escapeHTML(item.status)} · ${item.recipient_count || 0} 人 · 响应 ${item.response_count || 0}</div>
              </div>
              <button class="secondary open-distribution-btn" data-brief-id="${escapeHTML(item.brief_id)}" type="button">查看</button>
            </div>
          `
        )
        .join("")
    : emptyState("暂无 Brief 分发", "创建标准 Brief 后，系统会生成可推送名单。");
}

function renderDistributionDetail(data) {
  const panel = $("#distributionDetailPanel");
  if (!panel) return;
  state.activeDistribution = data;
  const brief = data.brief;
  panel.classList.remove("hidden");
  $("#distributionDetailTitle").textContent = brief.project_name;
  $("#distributionDetailMeta").textContent = `${brief.client_name} · ${brief.status} · ${brief.recipients.length} 个博主`;
  $("#distributionRecipientList").innerHTML = brief.recipients
    .map(
      (item) => `
        <div class="template-item">
          <div>
            <span class="card-kicker">Recipient</span>
            <strong>${escapeHTML(item.creator_name)}</strong>
            <div class="meta">${escapeHTML(item.platform)} · ${escapeHTML(item.status)} · token: ${escapeHTML(item.token)}</div>
            <div class="meta">匹配 ${item.match_score || "-"} · 建议预算 ${fmtNumber(item.suggested_budget)}</div>
          </div>
          <button class="secondary copy-token-btn" data-target="#creatorBriefTokenInput" data-token="${escapeHTML(item.token)}" type="button">填入</button>
        </div>
      `
    )
    .join("");
  $("#distributionSummaryOutput").textContent = JSON.stringify(data.summary || {}, null, 2);
}

function renderPlatformDashboard(data) {
  const metrics = data.metrics || {};
  const metricPanel = $("#platformMetrics");
  if (!metricPanel) return;
  metricPanel.innerHTML = [
    ["达人库", metrics.creators],
    ["商业档案", metrics.commercial_profiles],
    ["客户方案", metrics.client_proposals],
    ["Brief 分发", metrics.distribution_briefs],
    ["博主响应", metrics.creator_responses],
    ["最终方案", metrics.finalized_proposals],
  ]
    .map((item) => `<div class="metric"><span>${item[0]}</span><strong>${fmtNumber(item[1])}</strong></div>`)
    .join("");
  $("#platformLifecycle").innerHTML = (data.lifecycle || [])
    .map((item) => `<div class="timeline-item ${escapeHTML(item.status)}"><strong>${escapeHTML(item.label)}</strong><span>${fmtNumber(item.count)} · ${escapeHTML(item.status)}</span></div>`)
    .join("");
  $("#platformNextActions").innerHTML = (data.next_actions || [])
    .map((item) => `<div class="feedback-item">${escapeHTML(item)}</div>`)
    .join("") || '<div class="meta">暂无动作。</div>';
  $("#platformRecentOutput").textContent = JSON.stringify(data.recent || {}, null, 2);
  renderPlatformCampaignList();
}

function renderDataSources() {
  const grid = $("#dataSourceGrid");
  if (!grid) return;
  grid.innerHTML = state.dataSources.length
    ? state.dataSources
        .map((source) => {
          const ok = source.available || source.configured;
          const env = source.env
            ? Object.entries(source.env)
                .map(([key, value]) => `<div class="meta">${escapeHTML(key)}: ${escapeHTML(value || "-")}</div>`)
                .join("")
            : "";
          const platforms = source.platforms?.length
            ? `<div class="tag-list">${source.platforms.map((item) => `<span class="tag">${escapeHTML(item)}</span>`).join("")}</div>`
            : "";
          return `
            <article class="data-source-card ${ok ? "ok" : "warn"}">
              <div class="card-kicker">${escapeHTML(source.type)} · ${escapeHTML(source.status)}</div>
              <div class="creator-card-head">
                <h3>${escapeHTML(source.label)}</h3>
                <strong>${ok ? "ON" : "OFF"}</strong>
              </div>
              <p>${escapeHTML(source.detail || "")}</p>
              ${env}
              ${platforms}
              <button class="secondary data-source-test-btn" data-source-id="${escapeHTML(source.id)}" type="button">快速测试</button>
            </article>
          `;
        })
        .join("")
    : emptyState("暂无数据源状态", "点击刷新状态。");
}

function renderPlatformCampaignList() {
  const list = $("#platformCampaignList");
  if (!list) return;
  list.innerHTML = state.platformCampaigns.length
    ? state.platformCampaigns
        .map(
          (item) => `
            <div class="template-item">
              <div>
                <strong>${escapeHTML(item.campaign.project_name)}</strong>
                <div class="meta">${escapeHTML(item.campaign.client_name)} · ${escapeHTML(item.campaign.status)} · ${item.plans?.length || 0} 套方案 · 复盘 ${item.reviews?.length || 0}</div>
              </div>
              <button class="secondary open-platform-campaign-btn" data-campaign-id="${escapeHTML(item.campaign.campaign_id)}" type="button">查看</button>
            </div>
          `
        )
        .join("")
    : emptyState("暂无 Campaign 项目", "输入品牌 brief，一键生成 3 套传播方案。");
}

function renderPlatformCampaign(projectOrRoom) {
  const room = projectOrRoom.project && projectOrRoom.decision_summary ? projectOrRoom : null;
  const project = room ? room.project : projectOrRoom;
  $("#platformCampaignDetail").classList.remove("hidden");
  state.activePlatformCampaign = project;
  state.activeCampaignRoom = room;
  $("#platformCampaignTitle").textContent = project.campaign.project_name;
  $("#platformCampaignMeta").textContent = `${project.campaign.client_name} · ${project.campaign.status} · 预算 ${fmtNumber(project.campaign.budget)}`;
  $("#postReviewForm").elements.campaign_id.value = project.campaign.campaign_id;
  renderCampaignRoomSummary(room, project);
  renderCampaignRoomSidebars(room, project);
  const plans = room?.plans || project.plans || [];
  $("#platformPlanList").innerHTML = plans
    .map((plan) => {
      const simulation = plan.simulation || (project.simulations || []).find((item) => item.plan_id === plan.plan_id);
      const deepReport = simulation?.simulation_report || {};
      return `
        <article class="creator-card campaign-plan-card ${escapeHTML(plan.room_status || "ready")}">
          <div class="card-kicker">Campaign plan · ${escapeHTML(plan.room_status || "ready")}</div>
          <div class="creator-card-head">
            <h3>${escapeHTML(plan.plan_name)}${plan.is_recommended ? " · 推荐" : ""}</h3>
            <strong>${plan.execution_score}</strong>
          </div>
          <div class="meta">${escapeHTML(plan.risk_level)} risk · ${plan.creator_names?.length || 0} 个达人</div>
          <p>${escapeHTML(plan.strategy_summary)}</p>
          <div class="tag-list">${(plan.content_directions || []).map((item) => `<span class="tag">${escapeHTML(item)}</span>`).join("")}</div>
          <div class="meta">预算：${escapeHTML(JSON.stringify(plan.budget_allocation || {}))}</div>
          <div class="meta">推演：${escapeHTML(simulation?.summary || "")}</div>
          ${
            deepReport.nodes
              ? `<div class="meta">深度推演：${deepReport.nodes.length || 0} 节点 · ${deepReport.timeline?.length || 0} 事件 · ${deepReport.agent_reactions?.length || 0} agents</div>`
              : ""
          }
          <div class="tag-list">${(simulation?.risk_points || []).slice(0, 4).map((item) => `<span class="tag danger">${escapeHTML(item)}</span>`).join("")}</div>
          <div class="decision-actions">
            <button class="secondary campaign-simulate-btn" data-plan-id="${escapeHTML(plan.plan_id)}" type="button">深度推演</button>
            <button class="primary campaign-distribute-btn" data-plan-id="${escapeHTML(plan.plan_id)}" type="button">生成 Brief 分发</button>
          </div>
        </article>
      `;
    })
    .join("");
  renderCampaignRoomCreators(room);
  renderCampaignRoomDistribution(room);
  renderCampaignRoomReviews(room || { reviews: project.reviews || [] });
  $("#platformCampaignOutput").textContent = JSON.stringify(room || project, null, 2);
}

function renderCampaignRoomSummary(room, project) {
  const target = $("#campaignRoomSummary");
  if (!target) return;
  const summary = room?.decision_summary || {};
  target.innerHTML = `
    <div class="room-signal">
      <span>推荐方案</span>
      <strong>${escapeHTML(summary.recommended_plan || "待生成")}</strong>
    </div>
    <div class="room-signal">
      <span>执行分</span>
      <strong>${fmtNumber(summary.recommended_score || 0)}</strong>
    </div>
    <div class="room-signal">
      <span>Brief 分发</span>
      <strong>${fmtNumber(summary.distribution_count || 0)}</strong>
    </div>
    <div class="room-signal">
      <span>投后复盘</span>
      <strong>${fmtNumber(summary.review_count || 0)}</strong>
    </div>
    <div class="room-signal wide">
      <span>风险观察</span>
      <div class="tag-list">${(summary.risk_watch || project.simulations?.[0]?.risk_points || []).slice(0, 4).map((item) => `<span class="tag danger">${escapeHTML(item)}</span>`).join("") || '<span class="meta">暂无</span>'}</div>
    </div>
  `;
}

function renderCampaignRoomSidebars(room, project) {
  const actions = $("#campaignRoomActions");
  if (actions) {
    actions.innerHTML = (room?.next_actions || [])
      .map((item) => `<div class="feedback-item">${escapeHTML(item)}</div>`)
      .join("") || '<div class="meta">暂无动作。</div>';
  }
  const timeline = $("#campaignRoomTimeline");
  if (timeline) {
    timeline.innerHTML = (project.timeline || [])
      .map((item) => `<div class="timeline-item active"><strong>${escapeHTML(item.title)}</strong><span>${escapeHTML(item.type)} · ${escapeHTML(item.created_at || "")}</span></div>`)
      .join("") || '<div class="meta">暂无时间线。</div>';
  }
}

function renderCampaignRoomCreators(room) {
  const list = $("#campaignRoomCreatorList");
  if (!list) return;
  const creators = room?.creators || [];
  list.innerHTML = creators.length
    ? creators
        .map(
          (creator) => `
            <article class="creator-card room-creator-card">
              <div class="card-kicker">${escapeHTML(creator.platform)} · ${escapeHTML(creator.commercial_status)}</div>
              <div class="creator-card-head">
                <h3>${escapeHTML(creator.name)}</h3>
                <strong>${fmtNumber(creator.listed_price)}</strong>
              </div>
              <div class="meta">粉丝 ${fmtNumber(creator.follower_count)} · 履约 ${creator.delivery_rating || "-"}</div>
              <div class="tag-list">${(creator.tags || []).map((item) => `<span class="tag">${escapeHTML(item)}</span>`).join("")}</div>
              ${creator.latest_review ? `<p>${escapeHTML(creator.latest_review.brand_feedback || creator.latest_review.comment_feedback || "已有投后复盘")}</p>` : ""}
            </article>
          `
        )
        .join("")
    : emptyState("暂无达人资产", "先生成 Campaign 方案。");
}

function renderCampaignRoomDistribution(room) {
  const list = $("#campaignRoomDistributionList");
  if (!list) return;
  const briefs = room?.distribution_briefs || [];
  list.innerHTML = briefs.length
    ? briefs
        .map(
          (brief) => `
            <div class="template-item">
              <div>
                <strong>${escapeHTML(brief.project_name)}</strong>
                <div class="meta">${escapeHTML(brief.status)} · ${brief.recipients?.length || 0} 个博主 · token ${escapeHTML(brief.brief_id)}</div>
              </div>
              <button class="secondary open-distribution-btn" data-brief-id="${escapeHTML(brief.brief_id)}" type="button">查看</button>
            </div>
          `
        )
        .join("")
    : emptyState("暂无 Brief 分发", "从推荐方案生成 Brief 分发。");
}

function renderCampaignRoomReviews(room) {
  const list = $("#campaignRoomReviewList");
  if (!list) return;
  const reviews = room?.reviews || [];
  list.innerHTML = reviews.length
    ? reviews
        .map(
          (review) => `
            <div class="feedback-item">
              <strong>${escapeHTML(review.creator_id)} · 评分 ${review.delivery_rating || "-"}</strong>
              <div class="meta">曝光 ${fmtNumber(review.views)} · 互动 ${fmtNumber((review.likes || 0) + (review.comments || 0))} · ${escapeHTML(review.case_status)}</div>
              <div>${escapeHTML(review.brand_feedback || review.comment_feedback || "暂无反馈")}</div>
            </div>
          `
        )
        .join("")
    : '<div class="meta">暂无投后复盘。</div>';
}

async function openCampaignRoom(campaignId) {
  const data = await api(`/api/platform/campaigns/${campaignId}/room`);
  renderPlatformCampaign(data.room);
  return data.room;
}

async function openHistoryItem(type, id) {
  if (!id) return;
  if (type === "campaign") {
    await openCampaignRoom(id);
    setView("platformOS");
    return;
  }
  if (type === "agent_thread") {
    const threadData = await loadAgentThread(id);
    const runId = threadData?.thread?.current_run_id || threadData?.runs?.[0]?.run_id;
    if (runId) {
      const data = await api(`/api/agent/runs/${runId}`);
      renderAgentRun(data);
      if (data.run?.status === "running") startAgentPolling(runId);
    }
    setView("agentWorkspace");
    return;
  }
  if (type === "proposal") {
    await openCollaborationProposal(id);
    setView("collaboration");
    return;
  }
  if (type === "distribution") {
    await openDistribution(id);
    setView("briefDistribution");
    return;
  }
  toast("暂不支持打开该历史类型", true);
}

async function openDistribution(briefId) {
  const data = await api(`/api/distribution/briefs/${briefId}`);
  renderDistributionDetail(data);
}

async function loadCreatorInvite(token) {
  const data = await api(`/api/creator/invite/${token}`);
  state.activeCreatorInvite = data;
  $("#creatorInviteTokenInput").value = token;
  const form = $("#creatorSubmissionForm");
  form.classList.remove("hidden");
  form.elements.token.value = token;
  $("#creatorInviteOutput").textContent = JSON.stringify(data, null, 2);
}

async function loadCreatorBrief(token) {
  const data = await api(`/api/creator/brief/${token}`);
  state.activeCreatorBrief = data;
  $("#creatorBriefTokenInput").value = token;
  const form = $("#creatorBriefResponseForm");
  form.classList.remove("hidden");
  form.elements.token.value = token;
  $("#creatorBriefOutput").textContent = JSON.stringify(data, null, 2);
}

async function openCollaborationProposal(proposalId) {
  const data = await api(`/api/collaboration/proposals/${proposalId}`);
  state.activeProposal = data;
  renderCollaborationDetail(data);
}

function renderCollaborationDetail(data) {
  const panel = $("#collabDetailPanel");
  const proposal = data.proposal;
  const current = data.current;
  panel.classList.remove("hidden");
  $("#collabDetailTitle").textContent = proposal.project_name;
  $("#collabDetailMeta").textContent = `${proposal.client_name} · ${proposal.status} · v${proposal.current_version}`;
  $("#collabShareBox").innerHTML = `
    <div><strong>分享链接</strong> <code>${escapeHTML(proposal.share_url)}</code></div>
    <div><strong>分享 token</strong> <code>${escapeHTML(proposal.share_token)}</code></div>
    <div class="meta">默认隐藏联系方式、内部备注和底价来源。访问次数：${proposal.access_count || 0}</div>
    <div class="share-field-grid">
      <label class="checkline"><input id="shareEnabledInput" type="checkbox" ${proposal.share_enabled ? "checked" : ""} /> 启用分享链接</label>
      <label class="checkline"><input id="allowCommentsInput" type="checkbox" ${proposal.allow_comments ? "checked" : ""} /> 允许评论</label>
      <label class="checkline"><input id="allowDownloadInput" type="checkbox" ${proposal.allow_download ? "checked" : ""} /> 允许下载</label>
      <label class="symbolic-field"><span>有效期天数</span><input id="expiresDaysInput" type="number" min="1" max="90" value="14" /></label>
      ${renderShareField("contact", "联系方式", proposal.visible_fields?.contact)}
      ${renderShareField("manual_notes", "内部备注", proposal.visible_fields?.manual_notes)}
      ${renderShareField("price_source", "价格来源", proposal.visible_fields?.price_source)}
      ${renderShareField("cooperation_brands", "历史案例", proposal.visible_fields?.cooperation_brands)}
      ${renderShareField("risk_points", "风险提示", proposal.visible_fields?.risk_points)}
      ${renderShareField("suggested_budget", "建议预算", proposal.visible_fields?.suggested_budget)}
    </div>
    <div class="meta">版本：${(data.versions || []).map((item) => `v${item.version_number}${item.is_final ? " final" : ""}`).join(" / ")}</div>
    <div class="decision-actions">${(data.versions || []).map((item) => `<button class="secondary restore-version-btn" data-version-number="${item.version_number}" type="button">恢复 v${item.version_number}</button>`).join("")}</div>
  `;
  const candidates = current?.candidates || [];
  $("#collabCandidateTable tbody").innerHTML = candidates
    .map(
      (item) => `
        <tr>
          <td>${escapeHTML(item.creator_name)}</td>
          <td>${escapeHTML(item.platform)}</td>
          <td><strong>${item.match_score}</strong></td>
          <td>${escapeHTML(item.recommended_role || "-")}</td>
          <td>${fmtNumber(item.suggested_budget || item.listed_price)}</td>
          <td>${decisionLabel(item.client_decision)}</td>
        </tr>
      `
    )
    .join("");
  renderCollaborationFeedback(data.feedback || []);
  $("#clientPreferenceOutput").textContent = JSON.stringify(data.preference || {}, null, 2);
}

function renderShareField(key, label, checked) {
  return `<label class="checkline"><input class="share-field-input" data-field="${key}" type="checkbox" ${checked ? "checked" : ""} /> ${label}</label>`;
}

function renderCollaborationFeedback(feedback) {
  const list = $("#collabFeedbackList");
  if (!feedback.length) {
    list.innerHTML = '<div class="meta">暂无甲方反馈。</div>';
    return;
  }
  list.innerHTML = feedback
    .map(
      (item) => `
        <div class="feedback-item">
          <strong>${escapeHTML(item.target_type)} · ${escapeHTML(item.decision || "comment")}</strong>
          <div>${escapeHTML(item.comment || item.reason || "-")}</div>
          <div class="meta">${escapeHTML(item.status)} · ${escapeHTML(item.created_at)}</div>
          <div class="decision-actions">
            <button class="secondary feedback-status-btn" data-feedback-id="${escapeHTML(item.feedback_id)}" data-status="replied" type="button">已回复</button>
            <button class="secondary feedback-status-btn" data-feedback-id="${escapeHTML(item.feedback_id)}" data-status="adjusted" type="button">已调整</button>
            <button class="secondary feedback-status-btn" data-feedback-id="${escapeHTML(item.feedback_id)}" data-status="closed" type="button">关闭</button>
          </div>
        </div>
      `
    )
    .join("");
}

async function loadClientShare(token) {
  const data = await api(`/api/client/share/${token}`);
  state.activeClientShare = data;
  $("#clientShareTokenInput").value = token;
  renderClientProposal(data);
  setView("clientPortal");
}

async function loadClientPortalProjects() {
  const list = $("#clientPortalProjectList");
  if (!list || state.currentIdentity?.user?.user_type !== "client") return;
  const data = await api("/api/client/portal/projects");
  state.clientPortalProjects = data.items || [];
  list.innerHTML = state.clientPortalProjects.length
    ? state.clientPortalProjects
        .map(
          (proposal) => `
            <div class="template-item">
              <div>
                <strong>${escapeHTML(proposal.project_name)}</strong>
                <div class="meta">${escapeHTML(proposal.client_name)} · ${escapeHTML(proposal.status)} · v${proposal.current_version}</div>
              </div>
              <button class="primary client-portal-open-project-btn" data-proposal-id="${escapeHTML(proposal.proposal_id)}" type="button">打开项目</button>
            </div>
          `
        )
        .join("")
    : emptyState("暂无可访问项目", "请联系项目负责人为你开通项目权限。");
}

async function loadClientPortalProposal(proposalId) {
  const data = await api(`/api/client/portal/proposals/${proposalId}`);
  state.activeClientShare = data;
  $("#clientShareTokenInput").value = data.proposal?.share_token || "";
  renderClientProposal(data);
  setView("clientPortal");
}

function renderClientProposal(data) {
  const proposal = data.proposal;
  const candidates = data.candidates || [];
  const budget = data.budget || {};
  $("#clientProposalView").innerHTML = `
    <div class="client-hero">
      <div>
        <div class="card-kicker">Client approval arena</div>
        <h2>${escapeHTML(proposal.project_name)}</h2>
        <p>${escapeHTML(proposal.client_name)} · 当前版本 v${proposal.current_version}</p>
      </div>
      <div class="client-budget">
        <strong>${fmtNumber(budget.total)}</strong>
        <span>建议总预算</span>
      </div>
    </div>
    <div class="panel-subsection">
      <h2>Brief 摘要</h2>
      <p>${escapeHTML(proposal.brief_summary || proposal.brief_text || "")}</p>
    </div>
    <div class="client-candidate-grid">
      ${candidates.map(renderClientCandidate).join("")}
    </div>
    <div class="panel-subsection">
      <h2>整体反馈</h2>
      <textarea id="clientOverallComment" placeholder="对整体方案、预算或平台策略的意见"></textarea>
      <button class="primary client-overall-feedback-btn" type="button">提交整体反馈</button>
    </div>
  `;
}

function renderClientCandidate(item) {
  const reasons = (item.reasons || []).slice(0, 3).map((reason) => `<li>${escapeHTML(reason)}</li>`).join("");
  const risks = (item.risk_points || []).slice(0, 3).map((risk) => `<span class="tag risk">${escapeHTML(risk)}</span>`).join("");
  return `
    <article class="client-candidate-card">
      <div class="card-kicker">Candidate card</div>
      <div class="creator-card-head">
        <h3>${escapeHTML(item.creator_name)}</h3>
        <span class="tag">${decisionLabel(item.client_decision || item.feedback?.decision || "pending")}</span>
      </div>
      <div class="meta">${escapeHTML(item.platform)} · 粉丝 ${fmtNumber(item.follower_count)} · 预算 ${fmtNumber(item.suggested_budget || item.listed_price)}</div>
      <div class="score-line"><strong>${item.match_score || "-"}</strong><span>${escapeHTML(item.recommendation_level || "")}</span></div>
      <div class="meta">${escapeHTML(item.recommended_role || "")}</div>
      <ul class="plain-list">${reasons}</ul>
      <div class="tag-list">${risks}</div>
      <textarea data-client-comment="${escapeHTML(item.creator_id)}" placeholder="给这个达人写评论或替换要求">${escapeHTML(item.feedback?.comment || item.client_comment || "")}</textarea>
      <div class="decision-actions">
        <button class="primary client-decision-btn" data-creator-id="${escapeHTML(item.creator_id)}" data-decision="approved" type="button">通过</button>
        <button class="secondary client-decision-btn" data-creator-id="${escapeHTML(item.creator_id)}" data-decision="maybe" type="button">待定</button>
        <button class="secondary client-decision-btn" data-creator-id="${escapeHTML(item.creator_id)}" data-decision="rejected" type="button">拒绝</button>
      </div>
    </article>
  `;
}

function decisionLabel(value) {
  const labels = {
    approved: "通过",
    maybe: "待定",
    rejected: "拒绝",
    pending: "未处理",
  };
  return labels[value] || value || "未处理";
}

function layoutGraphNodes(nodes, width, height) {
  const lanes = {
    brand: 0.08,
    product: 0.22,
    social_context: 0.2,
    social_issue: 0.32,
    target_tag: 0.38,
    creator: 0.58,
    narrative: 0.76,
    risk_tag: 0.92,
  };
  const grouped = nodes.reduce((acc, node) => {
    const lane = lanes[node.type] === undefined ? 0.5 : lanes[node.type];
    acc[lane] = acc[lane] || [];
    acc[lane].push(node);
    return acc;
  }, {});
  return nodes.map((node) => {
    const lane = lanes[node.type] === undefined ? 0.5 : lanes[node.type];
    const group = grouped[lane];
    const index = group.indexOf(node);
    const gap = height / (group.length + 1);
    return { ...node, x: Math.round(width * lane), y: Math.round(gap * (index + 1)) };
  });
}

function renderProjectRun(run) {
  state.projectRun = run;
  state.projectRunSelectedNodeId = run.graph?.nodes?.[0]?.id || "";
  state.projectRunStageFilter = "";
  $("#projectRunResult")?.classList.remove("hidden");
  $("#projectRunKolCount").textContent = fmtNumber((run.matches || []).length);
  $("#projectRunNodeCount").textContent = fmtNumber((run.graph?.nodes || []).length);
  $("#projectRunSimulationCount").textContent = fmtNumber((run.simulation_report?.nodes || []).length);
  renderProjectRunSaveNotice(run);
  renderProjectRunSteps(run.steps || []);
  renderProjectRunStageLegend(run.graph || {});
  renderSymbolicGraphInto("#projectRunGraphCanvas", run.graph || {});
  renderProjectRunNodeInspector();
  renderProjectRunKols(run.matches || []);
  renderProjectRunSimulation(run.simulation_report || {});
  renderProjectRunNarratives(run.narrative_assets?.length ? run.narrative_assets : run.narratives || []);
  state.lastBrand = run.brand || null;
  state.lastSymbolicResults = run.matches || [];
  state.lastNarratives = run.narratives || [];
  state.lastSymbolicGraph = run.graph || null;
}

function renderProjectRunSaveNotice(run) {
  const target = $("#projectRunSaveNotice");
  if (!target) return;
  const campaign = run.campaign?.campaign || {};
  const saved = Boolean(campaign.campaign_id);
  target.innerHTML = saved
    ? `
      <div>
        <span class="card-kicker">asset saved</span>
        <strong>已保存到 Campaign 资产库</strong>
        <p>${escapeHTML(campaign.client_name || run.brand?.name || "当前客户")} · ${escapeHTML(campaign.project_name || "PR 项目")} · ${escapeHTML(campaign.status || "active")}</p>
      </div>
      <div class="button-row">
        <button class="secondary project-run-to-filter-btn" type="button">带入筛选达人</button>
        <button class="secondary open-platform-campaign-btn" data-campaign-id="${escapeHTML(campaign.campaign_id)}" type="button">打开完整资产</button>
      </div>
    `
    : `
      <div>
        <span class="card-kicker">local result</span>
        <strong>当前结果已生成</strong>
        <p>未拿到 Campaign ID，刷新资产库后可确认是否已保存。</p>
      </div>
      <button class="secondary project-run-to-filter-btn" type="button">带入筛选达人</button>
    `;
}

const GRAPH_STAGE_LABELS = {
  brief_parse: ["Brief 解析", "brief"],
  social_context: ["社会语境", "social"],
  brand_calibration: ["品牌校准", "brand"],
  product_profile: ["产品档案", "product"],
  kol_match: ["KOL 匹配", "creator"],
  narrative_asset: ["叙事资产", "narrative"],
  risk_test: ["风险推演", "risk"],
  analysis: ["分析节点", "analysis"],
};

const PROJECT_RUN_PROGRESS_STEPS = [
  {
    id: "brief_parse",
    label: "解析 PR Brief",
    detail: "拆解客户、项目、预算、目标人群、平台和风险要求。",
    node: { id: "progress_brief", label: "PR Brief", type: "brand", stage: "brief_parse", detail: "正在把输入需求拆成可计算字段。", payload: { status: "running" } },
  },
  {
    id: "social_context",
    label: "生成社会符号语境",
    detail: "识别行业语境、目标人群幻想和可借势议题。",
    node: { id: "progress_social", label: "社会语境", type: "social_context", stage: "social_context", detail: "正在生成可传播的社会符号网络。", payload: { status: "running" } },
  },
  {
    id: "brand_calibration",
    label: "生成并校准品牌符号档案",
    detail: "校准品牌想获得和想避开的传播符号。",
    node: { id: "progress_brand", label: "品牌符号档案", type: "target_tag", stage: "brand_calibration", detail: "正在校准品牌标签和危险标签。", payload: { status: "running" } },
  },
  {
    id: "product_profile",
    label: "生成产品符号档案",
    detail: "把产品卖点转成内容可表达的隐喻和场景。",
    node: { id: "progress_product", label: "产品符号档案", type: "product", stage: "product_profile", detail: "正在提取产品卖点、场景和内容角度。", payload: { status: "running" } },
  },
  {
    id: "kol_match",
    label: "补齐达人符号档案",
    detail: "扫描私有达人库，按标签、风险和预算生成候选池。",
    node: { id: "progress_kol", label: "KOL 候选池", type: "creator", stage: "kol_match", detail: "正在召回达人并计算匹配关系。", payload: { status: "running" } },
  },
  {
    id: "narrative_asset",
    label: "生成内容叙事资产",
    detail: "为首选达人生成内容路径、标题方向和避雷点。",
    node: { id: "progress_narrative", label: "内容叙事资产", type: "narrative", stage: "narrative_asset", detail: "正在组合达人角色和内容路径。", payload: { status: "running" } },
  },
  {
    id: "risk_test",
    label: "完成投放前风险推演",
    detail: "模拟评论区、竞品反应、履约和品牌安全风险。",
    node: { id: "progress_risk", label: "风险推演", type: "risk_tag", stage: "risk_test", detail: "正在压力测试候选组合。", payload: { status: "running" } },
  },
];

function stopProjectRunProgress() {
  if (state.projectRunProgressTimer) {
    clearInterval(state.projectRunProgressTimer);
    state.projectRunProgressTimer = null;
  }
}

function fillProjectRunForm(values) {
  const form = $("#projectRunForm");
  if (!form) return;
  Object.entries(values || {}).forEach(([name, value]) => {
    const field = form.elements[name];
    if (field) field.value = value;
  });
}

function randomProjectRunBrief() {
  return PROJECT_RUN_RANDOM_BRIEFS[Math.floor(Math.random() * PROJECT_RUN_RANDOM_BRIEFS.length)] || PROJECT_RUN_DEMO_VALUES;
}

function resetProjectRunWorkspace({ demo = false, values = null } = {}) {
  stopProjectRunProgress();
  state.projectRun = null;
  state.projectRunSelectedNodeId = "";
  state.projectRunStageFilter = "";
  state.projectRunGraphScale = 1;
  state.projectRunGraphAutoFit = true;
  state.projectRunGraphDrag = null;
  const nextValues =
    values ||
    (demo
      ? PROJECT_RUN_DEMO_VALUES
      : {
          client_name: "",
          project_name: "",
          brief: "",
          top_n: "8",
        });
  fillProjectRunForm(nextValues);
  $("#projectRunResult")?.classList.add("hidden");
  const steps = $("#projectRunSteps");
  if (steps) steps.innerHTML = '<div class="meta">等待输入 PR 需求。</div>';
  const legend = $("#projectRunStageLegend");
  if (legend) legend.innerHTML = "";
  const graph = $("#projectRunGraphCanvas");
  if (graph) graph.innerHTML = "";
  const inspector = $("#projectRunNodeInspector");
  if (inspector) inspector.innerHTML = '<div class="meta">点击图谱节点查看分析依据。</div>';
  const kolCount = $("#projectRunKolCount");
  if (kolCount) kolCount.textContent = "0";
  const nodeCount = $("#projectRunNodeCount");
  if (nodeCount) nodeCount.textContent = "0";
  const simulationCount = $("#projectRunSimulationCount");
  if (simulationCount) simulationCount.textContent = "0";
  updateProjectRunZoomLabel();
}

function buildProjectRunProgressGraph(stepIndex) {
  const visible = PROJECT_RUN_PROGRESS_STEPS.slice(0, Math.max(1, stepIndex + 1));
  return {
    nodes: visible.map((item, index) => ({
      ...item.node,
      score: index === stepIndex ? 66 : 100,
      detail: index === stepIndex ? item.node.detail : item.detail,
      payload: { ...item.node.payload, phase: item.label, progress: index === stepIndex ? "running" : "done" },
    })),
    edges: visible.slice(1).map((item, index) => ({
      source: visible[index].node.id,
      target: item.node.id,
      label: "feeds",
      type: "progress",
    })),
  };
}

function startProjectRunProgress(payload) {
  stopProjectRunProgress();
  const engineMode = projectRunEngineMode(payload.simulation_engine);
  state.projectRunEngineMode = engineMode;
  state.projectRun = { graph: buildProjectRunProgressGraph(0), matches: [], simulation_report: {}, narratives: [] };
  state.projectRunSelectedNodeId = "progress_brief";
  state.projectRunStageFilter = "";
  state.projectRunGraphAutoFit = true;
  state.projectRunGraphScale = 1;
  $("#projectRunResult")?.classList.remove("hidden");
  $("#projectRunKolCount").textContent = "-";
  $("#projectRunNodeCount").textContent = "1";
  $("#projectRunSimulationCount").textContent = "-";
  const saveNotice = $("#projectRunSaveNotice");
  if (saveNotice) {
    saveNotice.innerHTML = `
      <div>
        <span class="card-kicker">live reasoning</span>
        <strong>${escapeHTML(engineMode.runningTitle)}</strong>
        <p>${escapeHTML(payload.client_name || "当前客户")} · ${escapeHTML(payload.project_name || "PR 项目")} · ${escapeHTML(engineMode.runningDetail)}</p>
      </div>
      <span class="project-run-live-badge">RUNNING</span>
    `;
  }
  $("#projectRunGraphMeta").textContent = "推理节点会按 brief、语境、品牌、产品、KOL、叙事、风险逐步出现。";
  renderProjectRunProgressFrame(0, engineMode);
  let index = 0;
  state.projectRunProgressTimer = setInterval(() => {
    index = Math.min(index + 1, PROJECT_RUN_PROGRESS_STEPS.length - 1);
    renderProjectRunProgressFrame(index, engineMode);
    if (index >= PROJECT_RUN_PROGRESS_STEPS.length - 1) stopProjectRunProgress();
  }, 900);
}

function renderProjectRunProgressFrame(index, engineMode = state.projectRunEngineMode || projectRunEngineMode("llm_fallback")) {
  const graph = buildProjectRunProgressGraph(index);
  state.projectRun = { ...(state.projectRun || {}), graph };
  const activeNode = graph.nodes[index] || graph.nodes[0];
  state.projectRunSelectedNodeId = activeNode?.id || "";
  $("#projectRunNodeCount").textContent = fmtNumber(graph.nodes.length);
  renderProjectRunSteps(
    PROJECT_RUN_PROGRESS_STEPS.map((step, stepIndex) => ({
      id: step.id,
      label: step.label,
      detail: step.detail,
      status: stepIndex < index ? "done" : stepIndex === index ? "active" : "pending",
      count: stepIndex < index ? 1 : stepIndex === index ? 0 : 0,
    }))
  );
  renderProjectRunStageLegend(graph);
  renderSymbolicGraphInto("#projectRunGraphCanvas", graph);
  renderProjectRunNodeInspector();
  const kolList = $("#projectRunKolList");
  if (kolList) {
    kolList.innerHTML = `
      <div class="project-run-placeholder">
        <span>scanning creator memory</span>
        <strong>正在召回 KOL 候选池</strong>
        <p>系统会根据品牌、产品、平台、预算和风险标签，筛选可进入推荐名单的达人。</p>
      </div>
    `;
  }
  renderProjectRunSimulation({ summary: engineMode.simulationSummary, final_recommendation: engineMode.simulationDetail });
  const narratives = $("#projectRunNarratives");
  if (narratives) {
    narratives.innerHTML = `
      <div class="project-run-placeholder">
        <span>drafting narrative assets</span>
        <strong>正在生成达人内容路径</strong>
        <p>首选 KOL 确认后，这里会沉淀标题方向、内容角度、避雷词和客户可读方案素材。</p>
      </div>
    `;
  }
}

function projectRunEngineMode(value) {
  const engine = String(value || "llm_fallback");
  if (engine === "mirofish") {
    return {
      mode: "deep",
      label: "深度 MiroFish 推演",
      buttonText: "深度推演中...",
      noticeTitle: "当前是深度推演",
      noticeText: "会启动 MiroFish 多智能体推演，通常需要 3-8 分钟。适合正式方案、投前压力测试和沉淀客户可读证据。",
      runningTitle: "正在执行 MiroFish 深度推演",
      runningDetail: "这一步会比较久，完成后会保存图谱、报告和风险推演资产。",
      simulationSummary: "MiroFish 深度推演正在运行。",
      simulationDetail: "系统会先生成 KOL 推荐预演画布，后端完成后替换为真实 MiroFish 图谱和报告。",
    };
  }
  if (engine === "auto") {
    return {
      mode: "auto",
      label: "Auto 推演",
      buttonText: "Auto 推演中...",
      noticeTitle: "当前是 Auto 推演",
      noticeText: "会优先尝试 MiroFish；如果耗时过长或运行失败，会自动切回快推演，保证方案先产出。",
      runningTitle: "正在执行 Auto 推演",
      runningDetail: "系统会优先尝试深度推演，超时后自动保底生成 Campaign 资产。",
      simulationSummary: "Auto 推演正在运行。",
      simulationDetail: "如 MiroFish 超时，系统会自动使用 OS fallback，避免整个项目卡死。",
    };
  }
  return {
    mode: "fast",
    label: "快推演",
    buttonText: "生成中...",
    noticeTitle: "当前是快推演",
    noticeText: "会优先完成 brief 解析、KOL 匹配、风险提示和 Campaign 资产沉淀。",
    runningTitle: "正在生成 Campaign 快推演",
    runningDetail: "后端完成后会自动保存为历史任务。",
    simulationSummary: "正在等待风险推演结果。",
    simulationDetail: "真实候选、压力测试和内容资产会在后端完成后替换当前预演。",
  };
}

function updateProjectRunEngineNotice() {
  const select = $("#projectRunForm select[name='simulation_engine']");
  const notice = $("#projectRunEngineNotice");
  if (!select || !notice) return;
  const mode = projectRunEngineMode(select.value);
  notice.dataset.mode = mode.mode;
  notice.innerHTML = `<strong>${escapeHTML(mode.noticeTitle)}</strong><span>${escapeHTML(mode.noticeText)}</span>`;
}

function renderProjectRunStageLegend(graph) {
  const target = $("#projectRunStageLegend");
  if (!target) return;
  const counts = (graph.nodes || []).reduce((acc, node) => {
    const stage = node.stage || "analysis";
    acc[stage] = (acc[stage] || 0) + 1;
    return acc;
  }, {});
  const stages = Object.keys(GRAPH_STAGE_LABELS).filter((stage) => counts[stage]);
  target.innerHTML = stages.length
    ? stages
        .map((stage) => {
          const [label, cls] = GRAPH_STAGE_LABELS[stage];
          const active = state.projectRunStageFilter === stage ? " active" : "";
          return `
            <button
              class="stage-pill ${escapeHTML(cls)}${active}"
              data-stage="${escapeHTML(stage)}"
              type="button"
              title="${escapeHTML(label)} · ${fmtNumber(counts[stage])} 个图谱节点"
            >
              <span>${escapeHTML(label)}</span>
              <strong>${fmtNumber(counts[stage])}<small>节点</small></strong>
            </button>
          `;
        })
        .join("")
    : '<div class="meta">暂无阶段数据。</div>';
}

function renderProjectRunNodeInspector() {
  const target = $("#projectRunNodeInspector");
  const graph = state.projectRun?.graph || {};
  if (!target) return;
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const node = nodes.find((item) => item.id === state.projectRunSelectedNodeId) || nodes[0];
  if (!node) {
    target.innerHTML = '<div class="meta">点击图谱节点查看分析依据。</div>';
    return;
  }
  state.projectRunSelectedNodeId = node.id;
  const inbound = edges.filter((edge) => edge.target === node.id);
  const outbound = edges.filter((edge) => edge.source === node.id);
  const stageLabel = GRAPH_STAGE_LABELS[node.stage || "analysis"]?.[0] || "分析节点";
  target.innerHTML = `
    <div class="card-kicker">${escapeHTML(stageLabel)} · ${escapeHTML(node.type || "node")}</div>
    <h3>${escapeHTML(node.label || node.id)}</h3>
    ${node.score ? `<div class="node-score">${fmtNumber(node.score)}</div>` : ""}
    <p>${escapeHTML(node.detail || "暂无详细说明。")}</p>
    ${renderInspectorPayload(node.payload || {})}
    <div class="inspector-links">
      <strong>关联关系</strong>
      ${[...inbound.slice(0, 4), ...outbound.slice(0, 4)]
        .map((edge) => `<span>${escapeHTML(edge.source === node.id ? "→" : "←")} ${escapeHTML(edge.label || edge.type || "relation")}</span>`)
        .join("") || '<span>暂无关联边</span>'}
    </div>
  `;
}

function renderInspectorPayload(payload) {
  const entries = Object.entries(payload || {}).filter(([, value]) => value !== undefined && value !== null && value !== "" && !(Array.isArray(value) && !value.length));
  if (!entries.length) return "";
  return `
    <div class="inspector-payload">
      ${entries
        .slice(0, 8)
        .map(([key, value]) => {
          const text = Array.isArray(value) ? value.slice(0, 6).join("、") : typeof value === "object" ? JSON.stringify(value) : String(value);
          return `
            <div>
              <span>${escapeHTML(key)}</span>
              <strong>${escapeHTML(text)}</strong>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderProjectRunSteps(steps) {
  const target = $("#projectRunSteps");
  if (!target) return;
  target.innerHTML = steps.length
    ? steps
        .map(
          (step, index) => `
            <div class="project-step ${escapeHTML(step.status || "done")}">
              <span>${String(index + 1).padStart(2, "0")}</span>
              <div>
                <strong>${escapeHTML(step.label || step.id)}</strong>
                <p>${escapeHTML(step.detail || "")}</p>
              </div>
              <em>${fmtNumber(step.count || 0)}</em>
            </div>
          `
        )
        .join("")
    : '<div class="meta">等待输入 PR 需求。</div>';
}

function renderProjectRunKols(matches) {
  const target = $("#projectRunKolList");
  if (!target) return;
  target.innerHTML = matches.length
    ? matches
        .slice(0, 8)
        .map(
          (item) => `
            <article class="creator-card project-kol-card">
              <div class="card-kicker">KOL pick · ${escapeHTML(item.recommendation_level || "")}</div>
              <div class="creator-card-head">
                <h3>${escapeHTML(item.creator_name || "未命名达人")}</h3>
                <strong>${fmtNumber(item.symbolic_score || 0)}</strong>
              </div>
              <p>${escapeHTML(item.match_reason || item.suggested_content_direction || "")}</p>
              <div class="tag-list">${(item.matched_brand_tags || []).slice(0, 5).map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
              <div class="tag-list">${(item.risk_points || []).slice(0, 3).map((risk) => `<span class="tag danger">${escapeHTML(risk)}</span>`).join("")}</div>
            </article>
          `
        )
        .join("")
    : emptyState("暂无推荐 KOL", "请先导入达人库，再运行 PR 项目。");
}

function renderProjectRunSimulation(report) {
  const target = $("#projectRunSimulation");
  if (!target) return;
  const risks = report.risk_points || [];
  const suggestions = report.optimization_suggestions || [];
  const engine = report.engine || "simulation";
  const engineStatus = report.engine_status || "ready";
  const isMiroFish = engine.includes("mirofish") && !engine.includes("fallback");
  const engineLabel = isMiroFish
    ? "MiroFish CLI"
    : engine.includes("after_mirofish")
      ? "OS fallback · MiroFish 未接入"
      : "OS fallback";
  target.innerHTML = `
    <div class="feedback-item simulation-engine-card ${isMiroFish ? "ok" : "warn"}">
      <strong>推演引擎：${escapeHTML(engineLabel)}</strong>
      <p>${escapeHTML(engine)} · ${escapeHTML(engineStatus)}</p>
    </div>
    <div class="feedback-item">
      <strong>${escapeHTML(report.summary || "等待压力测试。")}</strong>
      <p>${escapeHTML(report.final_recommendation || "")}</p>
    </div>
    ${risks
      .slice(0, 4)
      .map((risk) => `<div class="feedback-item danger"><strong>风险</strong><p>${escapeHTML(risk)}</p></div>`)
      .join("")}
    ${suggestions
      .slice(0, 3)
      .map((item) => `<div class="feedback-item"><strong>优化</strong><p>${escapeHTML(item)}</p></div>`)
      .join("")}
  `;
}

function renderProjectRunNarratives(items) {
  const target = $("#projectRunNarratives");
  if (!target) return;
  target.innerHTML = items.length
    ? items
        .slice(0, 6)
        .map(
          (item) => `
            <article class="creator-card narrative-card">
              <div class="card-kicker">${escapeHTML(item.creator_name || "narrative")}</div>
              <h3>${escapeHTML(item.target_tag || item.project || "内容路径")}</h3>
              <p>${escapeHTML(item.narrative_path || item.content_brief || "")}</p>
              <div class="tag-list">${(item.title_directions || []).slice(0, 2).map((title) => `<span class="tag">${escapeHTML(title)}</span>`).join("")}</div>
              <div class="tag-list">${(item.must_avoid || item.risk_words || []).slice(0, 3).map((risk) => `<span class="tag danger">${escapeHTML(risk)}</span>`).join("")}</div>
            </article>
          `
        )
        .join("")
    : emptyState("暂无叙事资产", "运行后会为首选达人生成内容路径。");
}

function nodeRadius(node) {
  if (node.type === "brand") return 34;
  if (node.type === "creator") return 28;
  if (node.type === "narrative") return 25;
  return 22;
}

function shortLabel(label) {
  const text = String(label || "");
  return text.length > 14 ? `${text.slice(0, 13)}…` : text;
}

function parseJsonEditor(selector) {
  try {
    return JSON.parse($(selector).value || "{}");
  } catch (error) {
    throw new Error("JSON 格式不正确，无法保存");
  }
}

function renderImportReview(data) {
  state.importReview = data;
  const panel = $("#importReviewPanel");
  const list = $("#importReviewList");
  panel.classList.remove("hidden");
  const totalDetected = (data.sheets || []).reduce((sum, sheet) => sum + Number(sheet.detected_profiles || 0), 0);
  const templateText = data.matched_template ? ` · 已套用模板：${data.matched_template.name}` : " · 未套用模板";
  $("#importReviewMeta").textContent = `${data.filename || "上传文件"} · ${data.sheets.length} 个 Sheet · 预估 ${totalDetected} 个达人${templateText}`;
  $("#templateNameInput").value = data.matched_template?.name || `${(data.filename || "导入文件").replace(/\.[^.]+$/, "")} 模板`;
  $("#qualityReport").classList.add("hidden");
  $("#qualityReport").innerHTML = "";

  list.innerHTML = (data.sheets || [])
    .map((sheet, sheetIndex) => {
      const flags = (sheet.quality_flags || []).length ? sheet.quality_flags.join("；") : "字段识别正常";
      const fieldControls = (data.fields || [])
        .map((field) => {
          const selected = sheet.mapping?.[field.key] || "";
          const options = [`<option value="">不导入</option>`]
            .concat(
              (sheet.columns || []).map((column) => {
                const isSelected = String(column) === String(selected) ? "selected" : "";
                return `<option value="${escapeHTML(column)}" ${isSelected}>${escapeHTML(column)}</option>`;
              })
            )
            .join("");
          return `
            <label class="mapping-field">
              <span>${escapeHTML(field.label)}${field.required ? " *" : ""}</span>
              <select data-sheet="${sheetIndex}" data-field="${escapeHTML(field.key)}">${options}</select>
            </label>
          `;
        })
        .join("");
      const headers = (sheet.columns || []).slice(0, 10);
      const rows = (sheet.preview || [])
        .map(
          (row) => `
            <tr>
              ${headers.map((header) => `<td>${escapeHTML(row[header])}</td>`).join("")}
            </tr>
          `
        )
        .join("");
      return `
        <article class="review-sheet" data-sheet-index="${sheetIndex}">
          <div class="review-sheet-head">
            <label class="checkline">
              <input type="checkbox" class="sheet-enabled" data-sheet="${sheetIndex}" ${sheet.detected_profiles ? "checked" : ""} />
              <strong><span class="card-kicker">Sheet</span>${escapeHTML(sheet.sheet)}</strong>
            </label>
            <span class="meta">${sheet.rows} 行 · 预估 ${sheet.detected_profiles} 个达人 · ${escapeHTML(flags)}</span>
          </div>
          <div class="mapping-grid">${fieldControls}</div>
          <div class="table-wrap compact">
            <table>
              <thead>
                <tr>${headers.map((header) => `<th>${escapeHTML(header)}</th>`).join("")}</tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderImportTemplates() {
  const select = $("#importTemplateSelect");
  const list = $("#templateList");
  if (select) {
    select.innerHTML = '<option value="">自动匹配导入模板</option>' + state.importTemplates
      .map((template) => `<option value="${escapeHTML(template.id)}">${escapeHTML(template.name)}</option>`)
      .join("");
  }
  if (!list) return;
  if (!state.importTemplates.length) {
    list.innerHTML = '<div class="meta">暂无模板。确认导入时勾选“保存为模板”即可创建。</div>';
    return;
  }
  list.innerHTML = state.importTemplates
    .map((template) => {
      const sheetCount = Object.keys(template.sheets || {}).length;
      return `
        <div class="template-item">
          <div>
            <strong>${escapeHTML(template.name)}</strong>
            <div class="meta">${sheetCount} 个 Sheet 规则 · ${escapeHTML(template.updated_at || template.created_at || "")}</div>
          </div>
          <button class="secondary delete-template-btn" data-template-id="${escapeHTML(template.id)}" type="button">删除</button>
        </div>
      `;
    })
    .join("");
}

function renderQualityReport(report) {
  const panel = $("#qualityReport");
  if (!report) return;
  panel.classList.remove("hidden");
  const missing = report.missing || {};
  const rates = report.completion_rate || {};
  panel.innerHTML = `
    <h3>导入质量报告</h3>
    <div class="quality-grid">
      <div><span>成功导入</span><strong>${fmtNumber(report.total_profiles)}</strong></div>
      <div><span>缺粉丝数</span><strong>${fmtNumber(missing.follower_count)}</strong><em>${Math.round((rates.follower_count || 0) * 100)}% 完整</em></div>
      <div><span>缺报价</span><strong>${fmtNumber(missing.listed_price)}</strong><em>${Math.round((rates.listed_price || 0) * 100)}% 完整</em></div>
      <div><span>缺主页链接</span><strong>${fmtNumber(missing.homepage_url)}</strong><em>${Math.round((rates.homepage_url || 0) * 100)}% 完整</em></div>
      <div><span>缺简介</span><strong>${fmtNumber(missing.bio)}</strong><em>${Math.round((rates.bio || 0) * 100)}% 完整</em></div>
      <div><span>自动合并</span><strong>${fmtNumber(report.dedupe?.auto_merged || 0)}</strong></div>
    </div>
  `;
}

function renderGovernance(summary) {
  $("#duplicateCount").textContent = fmtNumber(summary.duplicate_candidates);
  $("#qualityIssueCount").textContent = fmtNumber(summary.quality_issues);
  $("#missingPriceCount").textContent = fmtNumber(summary.missing_listed_price);

  const duplicateBody = $("#duplicateTable tbody");
  duplicateBody.innerHTML = state.duplicateCandidates.length
    ? state.duplicateCandidates
        .map((item, index) => {
          const left = item.left || {};
          const right = item.right || {};
          const samePlatform = String(left.platform || "") === String(right.platform || "");
          return `
            <tr>
              <td><strong>${item.confidence}</strong></td>
              <td>${escapeHTML(item.reason)}</td>
              <td>${renderGovernanceProfile(left)}</td>
              <td>${renderGovernanceProfile(right)}</td>
              <td>${
                samePlatform
                  ? `<button class="secondary merge-duplicate-btn" data-index="${index}" type="button">合并到 A</button>`
                  : '<span class="meta">跨平台待建主档</span>'
              }</td>
            </tr>
          `;
        })
        .join("")
    : '<tr><td colspan="5" class="meta">暂无疑似重复。</td></tr>';

  const qualityBody = $("#qualityTable tbody");
  qualityBody.innerHTML = state.qualityIssues.length
    ? state.qualityIssues
        .map(
          (item) => `
            <tr>
              <td><button class="text-btn open-creator-btn" data-creator-id="${escapeHTML(item.creator_id)}" type="button">${escapeHTML(item.name)}</button></td>
              <td>${escapeHTML(item.platform)}</td>
              <td>${(item.missing || []).map((tag) => `<span class="tag risk">${escapeHTML(tag)}</span>`).join("") || "-"}</td>
              <td>${(item.warnings || []).join("；") || "-"}</td>
              <td>${escapeHTML(item.source || "-")}</td>
            </tr>
          `
        )
        .join("")
    : '<tr><td colspan="5" class="meta">暂无质量问题。</td></tr>';
}

function renderGovernanceProfile(profile) {
  return `
    <button class="text-btn open-creator-btn" data-creator-id="${escapeHTML(profile.creator_id)}" type="button">${escapeHTML(profile.name)}</button>
    <div class="meta">${escapeHTML(profile.platform)} · 粉丝 ${fmtNumber(profile.follower_count)} · 报价 ${fmtNumber(profile.listed_price)}</div>
    <div class="meta">${escapeHTML((profile.data_sources || []).slice(0, 2).join("、"))}</div>
  `;
}

async function openCreatorModal(creatorId) {
  if (!creatorId) {
    toast("缺少达人 ID", true);
    return;
  }
  showCreatorModalLoading(creatorId);
  $("#creatorModal")?.classList.remove("hidden");
  try {
    const data = await api(`/api/creators/${encodeURIComponent(creatorId)}`);
    if (!data?.creator) {
      closeCreatorModal();
      toast("达人不存在", true);
      return;
    }
    state.activeCreator = data.creator;
    state.activeCreatorEvidenceTags = data.evidence_tags || [];
    try {
      renderCreatorModal(data.creator);
    } catch (error) {
      const summary = $("#creatorProfileSummary");
      if (summary) {
        summary.textContent = `详情渲染部分失败：${error.message || "未知错误"}。可刷新后重试，或联系管理员。`;
      }
      toast(error.message || "达人详情部分渲染失败", true);
      console.error("renderCreatorModal failed", error);
    }
    $("#creatorModal")?.classList.remove("hidden");
  } catch (error) {
    closeCreatorModal();
    const message = error.message || "打不开达人详情";
    if (message.includes("登录") || message.includes("login")) {
      showAccessGate("登录已失效，请重新登录后查看达人详情。");
    }
    toast(message, true);
  }
}

function closeCreatorModal() {
  $("#creatorModal")?.classList.add("hidden");
  state.activeCreator = null;
  state.activeCreatorEvidenceTags = [];
  state.activeCreatorImageSuggestion = null;
}

async function deleteActiveCreator() {
  const creator = state.activeCreator;
  if (!creator?.creator_id) return toast("没有正在打开的达人", true);
  const confirmed = window.confirm(`确认删除「${creator.name || "这个达人"}」吗？删除后会从本地达人库移除。`);
  if (!confirmed) return;
  const button = $("#deleteCreatorBtn");
  if (button) {
    button.disabled = true;
    button.textContent = "删除中...";
  }
  try {
    await api(`/api/creators/${encodeURIComponent(creator.creator_id)}`, { method: "DELETE" });
    closeCreatorModal();
    await reloadAll();
    toast(`已删除：${creator.name || creator.creator_id}`);
  } catch (error) {
    toast(error.message || "删除达人失败", true);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "删除这个达人";
    }
  }
}

function openQuickCreatorModal() {
  const modal = $("#quickCreatorModal");
  const form = $("#quickCreatorForm");
  if (!modal || !form) return;
  form.reset();
  resetQuickCreatorAvatar(form);
  state.quickCreatorEvidenceTags = [];
  state.quickCreatorImageSuggestion = null;
  state.quickCreatorPendingAssets = [];
  state.quickCreatorAiPreview = null;
  resetQuickCreatorAuxSections();
  initPlatformSelects();
  renderQuickCreatorRateFields(form);
  initQuickCreatorTagEditors(form);
  bindCommercialCasesEditor(form);
  renderCommercialCasesEditor(form, []);
  syncCreatorDataCardPanel(form);
  modal.classList.remove("hidden");
  form.elements.name?.focus();
}

function resetQuickCreatorAuxSections() {
  renderCreatorImageAnalysis(null, {
    boxId: "#quickCreatorImageAnalysis",
    applyBtnId: "#quickCreatorImageApplyBtn",
    stateKey: "quickCreatorImageSuggestion",
  });
  const summary = $("#quickCreatorAiSummary");
  if (summary) {
    summary.textContent = "填写字段后点击「运行 AI 判断」，系统会生成摘要并自动补充标签。";
  }
  renderCreatorEvidenceTags([], { containerId: "#quickCreatorEvidenceTags", reviewable: false });
  renderQuickCreatorMediaAssets();
  const kitOutput = $("#quickCreatorCommercialKitOutput");
  if (kitOutput) {
    kitOutput.innerHTML = '<div class="commercial-card-empty">填写信息后点击生成，会在这里出现卡片式商业名片刊例预览。</div>';
    kitOutput.dataset.copyText = "";
  }
  const tags = $("#quickCreatorTags");
  if (tags) tags.innerHTML = '<span class="meta">暂无标签</span>';
}

function getPlatformRateFields(platform) {
  return PLATFORM_RATE_FIELDS[normalizePlatformValue(platform)] || DEFAULT_PLATFORM_RATE_FIELDS;
}

function renderCreatorRateFields(form, container, preserved = {}) {
  if (!container || !form) return;
  const platform = normalizePlatformValue(form.elements.platform?.value);
  const fields = getPlatformRateFields(platform);
  container.innerHTML = `
    <div class="platform-rate-head">
      <span class="card-kicker">刊例报价</span>
      <strong>${escapeHTML(platform)} 合作方式</strong>
    </div>
    <div class="platform-rate-row">
      ${fields
        .map(
          (item) => `
            <label class="platform-rate-field">
              <span>${escapeHTML(item.label)}</span>
              <input
                name="${escapeHTML(item.key)}"
                type="number"
                min="0"
                step="1"
                placeholder="元"
                value="${escapeHTML(preserved[item.key] || "")}"
              />
            </label>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderQuickCreatorRateFields(form, preserved = {}) {
  renderCreatorRateFields(form, $("#quickCreatorRateFields"), preserved);
}

function readCreatorRateValues(form) {
  const fields = getPlatformRateFields(form.elements.platform?.value);
  const values = {};
  fields.forEach((item) => {
    values[item.key] = Number(form.elements[item.key]?.value || 0);
  });
  return { fields, values };
}

function readQuickCreatorRateValues(form) {
  return readCreatorRateValues(form);
}

function rateValuesFromNotes(notes, platform) {
  const values = {};
  getPlatformRateFields(platform).forEach((item) => {
    const amount = extractRateFromNotes(notes, item.label);
    if (amount) values[item.key] = amount;
  });
  return values;
}

function remarkTagsFromNotes(notes) {
  return normalizeQuickTagValue(notes).filter((tag) => !isRateNoteTag(tag));
}

function rateLabelToFormat(label) {
  return String(label || "").replace(/报价$/, "").trim();
}

function isRateNoteTag(tag) {
  return /报价[：:]\s*\d/.test(String(tag || ""));
}

function rememberQuickCreatorTags(fieldName, tags) {
  if (!fieldName || !tags.length) return;
  try {
    const store = JSON.parse(localStorage.getItem(QUICK_CREATOR_RECENT_TAGS_KEY) || "{}");
    const recent = Array.isArray(store[fieldName]) ? store[fieldName] : [];
    const merged = [...tags, ...recent].filter((tag, index, list) => list.indexOf(tag) === index).slice(0, 12);
    store[fieldName] = merged;
    localStorage.setItem(QUICK_CREATOR_RECENT_TAGS_KEY, JSON.stringify(store));
  } catch {
    /* ignore local storage errors */
  }
}

function loadRecentQuickCreatorTags(fieldName) {
  try {
    const store = JSON.parse(localStorage.getItem(QUICK_CREATOR_RECENT_TAGS_KEY) || "{}");
    return Array.isArray(store[fieldName]) ? store[fieldName] : [];
  } catch {
    return [];
  }
}

function rememberPersonalTags(tags) {
  if (!tags.length) return;
  try {
    const recent = loadPersonalTagsRecent();
    const merged = [...tags, ...recent].filter((tag, index, list) => list.indexOf(tag) === index).slice(0, 24);
    localStorage.setItem(PERSONAL_TAG_RECENT_KEY, JSON.stringify(merged));
  } catch {
    /* ignore */
  }
}

function loadPersonalTagsRecent() {
  try {
    const recent = JSON.parse(localStorage.getItem(PERSONAL_TAG_RECENT_KEY) || "[]");
    return Array.isArray(recent) ? recent : [];
  } catch {
    return [];
  }
}

function getPersonalTagsFromHub(form) {
  const hidden = form.elements.personal_tags;
  return normalizeQuickTagValue(hidden?.value || "");
}

function setPersonalTagsOnHub(form, tags) {
  if (form.elements.personal_tags) form.elements.personal_tags.value = tags.join("，");
  renderPersonalTagHub(form);
}

function renderPersonalTagHub(form) {
  const hub = form.querySelector("[data-creator-tag-hub]");
  if (!hub) return;
  const list = hub.querySelector("[data-personal-tag-list]");
  const wrap = hub.querySelector("[data-personal-tag-suggestion-wrap]");
  if (!list) return;
  const tags = getPersonalTagsFromHub(form);
  const selected = new Set(tags);
  list.innerHTML = tags.length
    ? tags
        .map(
          (tag) => `
        <button class="tag-chip" data-personal-tag-remove="${escapeHTML(tag)}" type="button">
          <span>${escapeHTML(tag)}</span><strong>×</strong>
        </button>
      `,
        )
        .join("")
    : '<span class="meta">还没有标签，输入后回车添加</span>';
  if (wrap) {
    const suggestions = [...loadPersonalTagsRecent(), ...PERSONAL_TAG_PRESETS]
      .filter((tag, index, items) => items.indexOf(tag) === index)
      .filter((tag) => !selected.has(tag))
      .slice(0, 16)
      .map((tag) => `<button class="tag-suggestion" data-personal-tag-add="${escapeHTML(tag)}" type="button">${escapeHTML(tag)}</button>`)
      .join("");
    wrap.innerHTML = suggestions || '<span class="meta">暂无建议</span>';
  }
}

function addPersonalTagToHub(form, value) {
  const incoming = normalizeQuickTagValue(value);
  if (!incoming.length) return;
  const tags = getPersonalTagsFromHub(form);
  incoming.forEach((tag) => {
    if (!tags.includes(tag)) tags.push(tag);
  });
  setPersonalTagsOnHub(form, tags);
  rememberPersonalTags(incoming);
  form.dataset.tagClassifyDirty = "true";
  scheduleCreatorTagClassify(form);
}

function removePersonalTagFromHub(form, value) {
  const tags = getPersonalTagsFromHub(form).filter((tag) => tag !== value);
  setPersonalTagsOnHub(form, tags);
  form.dataset.tagClassifyDirty = "true";
  scheduleCreatorTagClassify(form);
}

function collectStructuredTagsFromForm(form) {
  const read = (name) => normalizeQuickTagValue(form.elements[name]?.value || "");
  return {
    industry_fit_tags: read("industry_fit_tags"),
    identity_tags: read("identity_tags"),
    content_capability_tags: read("content_capability_tags"),
    delivery_tags: read("delivery_tags"),
    risk_tags: read("risk_tags"),
    suitable_goals: read("suitable_goals"),
    cooperation_formats: read("cooperation_formats"),
    budget_fit_tags: read("budget_fit_tags"),
    cooperation_brands: read("cooperation_brands"),
    narrative_position: String(form.elements.narrative_position?.value || form.elements.narrative_position_display?.value || "").trim(),
  };
}

function applyTagClassificationToForm(form, classification = {}) {
  const assign = (name, values) => {
    const field = form.elements[name];
    if (!field || !Array.isArray(values)) return;
    field.value = values.join("，");
  };
  assign("industry_fit_tags", classification.industry_fit_tags);
  assign("identity_tags", classification.identity_tags);
  assign("content_capability_tags", classification.content_capability_tags);
  assign("delivery_tags", classification.delivery_tags);
  assign("risk_tags", classification.risk_tags);
  assign("suitable_goals", classification.suitable_goals);
  assign("cooperation_formats", classification.cooperation_formats);
  assign("budget_fit_tags", classification.budget_fit_tags);
  assign("cooperation_brands", classification.cooperation_brands);
  if (Array.isArray(classification.personal_tags) && classification.personal_tags.length) {
    assign("personal_tags", classification.personal_tags);
  }
  const narrative = String(classification.narrative_position || "").trim();
  if (narrative) {
    if (form.elements.narrative_position) form.elements.narrative_position.value = narrative;
    if (form.elements.narrative_position_display) form.elements.narrative_position_display.value = narrative;
    form.dataset.narrativeAuto = "true";
  }
  if (classification.platform_hint && form.elements.platform) {
    const current = normalizePlatformValue(form.elements.platform.value);
    const hinted = normalizePlatformValue(classification.platform_hint);
    if (!current || current === PLATFORM_OPTIONS[0]) {
      form.elements.platform.value = hinted;
      renderPlatformSelectOptions(form.elements.platform, hinted);
      syncCreatorDataCardPanel(form);
    }
  }
  const brands = classification.cooperation_brands || [];
  if (brands.length && form.elements.cooperation_brands) {
    const existing = normalizeQuickTagValue(form.elements.cooperation_brands.value);
    form.elements.cooperation_brands.value = [...new Set([...existing, ...brands])].join("，");
    const brandsEditor = form.querySelector('[data-tag-field="cooperation_brands"]');
    if (brandsEditor) renderCreatorTagEditor(brandsEditor);
  }
  renderPersonalTagHub(form);
  renderTagFramework(form);
  renderCreatorTagSummaryFromForm(form);
  form.dataset.tagClassifyDirty = "false";
}

function getFrameworkTags(form, field) {
  return normalizeQuickTagValue(form.elements[field]?.value || "");
}

function setFrameworkTags(form, field, tags) {
  if (!form.elements[field]) return;
  form.elements[field].value = tags.join("，");
}

function getFrameworkPresets(field) {
  return QUICK_CREATOR_TAG_PRESETS[field] || [];
}

function buildClientNarrativePosition(structured) {
  const parts = [];
  if (structured.identity_tags?.length) parts.push(structured.identity_tags[0]);
  if (structured.industry_fit_tags?.length) parts.push(`聚焦${structured.industry_fit_tags.slice(0, 2).join("/")}`);
  if (structured.content_capability_tags?.length) parts.push(`擅长${structured.content_capability_tags[0]}`);
  if (structured.suitable_goals?.length) parts.push(`适合担任${structured.suitable_goals[0]}`);
  else if (structured.identity_tags?.length && structured.industry_fit_tags?.length) {
    parts.push("适合担任圈层扩散或专业背书角色");
  }
  let narrative = parts.join("，");
  if (structured.delivery_tags?.length) narrative += `；履约侧：${structured.delivery_tags.slice(0, 2).join("/")}`;
  if (structured.risk_tags?.length) narrative += `；注意${structured.risk_tags.slice(0, 2).join("/")}`;
  return narrative.trim("；");
}

function updateNarrativeFromFramework(form) {
  const structured = collectStructuredTagsFromForm(form);
  const current = String(form.elements.narrative_position_display?.value || "").trim();
  const autoFlag = form.dataset.narrativeAuto === "true";
  if (current && !autoFlag) return;
  const narrative = buildClientNarrativePosition(structured);
  if (!narrative) return;
  if (form.elements.narrative_position) form.elements.narrative_position.value = narrative;
  if (form.elements.narrative_position_display) form.elements.narrative_position_display.value = narrative;
  form.dataset.narrativeAuto = "true";
}

function renderTagCompleteness(form) {
  const badge = form.querySelector("[data-tag-completeness]");
  const hint = form.querySelector("[data-tag-completeness-hint]");
  const essential = TAG_FRAMEWORK_ROWS.filter((row) => row.essential);
  const filledEssential = essential.filter((row) => getFrameworkTags(form, row.field).length > 0).length;
  const allRows = [...TAG_FRAMEWORK_ROWS, TAG_NARRATIVE_FRAMEWORK_ROW];
  const filledAll = allRows.filter((row) => getFrameworkTags(form, row.field).length > 0).length;
  if (badge) {
    badge.textContent = `核心完整度 ${filledEssential}/${essential.length}`;
    badge.classList.toggle("warn", filledEssential < essential.length);
    badge.classList.toggle("ok", filledEssential >= essential.length);
  }
  if (hint) {
    if (filledEssential < essential.length) {
      hint.textContent = "建议至少补全领域、身份、内容能力，Brief 匹配和筛选会更准（不挡保存）。";
    } else if (filledAll < 5) {
      hint.textContent = "核心已齐，可再补履约、风险与叙事角色，方便出方案和内部交接。";
    } else {
      hint.textContent = "标签较完整，保存后可直接用于 Brief 匹配与筛选达人工具。";
    }
  }
  allRows.forEach((row) => {
    const rowNode = form.querySelector(`[data-framework-field="${row.field}"]`);
    if (!rowNode) return;
    rowNode.classList.toggle("filled", getFrameworkTags(form, row.field).length > 0);
    rowNode.classList.toggle("missing-essential", row.essential && !getFrameworkTags(form, row.field).length);
  });
}

function renderTagFrameworkRow(form, row) {
  const tags = getFrameworkTags(form, row.field);
  const selected = new Set(tags);
  const chips = tags.length
    ? tags
        .map(
          (tag) => `
        <button class="tag-chip small" data-framework-tag-remove="${escapeHTML(row.field)}" data-framework-tag-value="${escapeHTML(tag)}" type="button">
          <span>${escapeHTML(tag)}</span><strong>×</strong>
        </button>
      `,
        )
        .join("")
    : `<span class="meta framework-empty">还未填写，可点选下方或输入</span>`;
  const suggestions = [...loadRecentQuickCreatorTags(row.field), ...getFrameworkPresets(row.field)]
    .filter((tag, index, list) => list.indexOf(tag) === index)
    .filter((tag) => !selected.has(tag))
    .slice(0, 10)
    .map(
      (tag) =>
        `<button class="tag-suggestion" data-framework-tag-add="${escapeHTML(row.field)}" data-framework-tag-suggestion="${escapeHTML(tag)}" type="button">${escapeHTML(tag)}</button>`,
    )
    .join("");
  const essentialMark = row.essential ? '<em class="framework-required">核心</em>' : "";
  return `
    <div class="creator-tag-framework-row" data-framework-field="${escapeHTML(row.field)}">
      <div class="creator-tag-framework-row-head">
        <div>
          <span class="framework-label">${escapeHTML(row.label)}</span>
          ${essentialMark}
        </div>
        <span class="framework-hint">${escapeHTML(row.hint)}</span>
      </div>
      <div class="tag-chip-list compact" data-framework-tag-list="${escapeHTML(row.field)}">${chips}</div>
      <div class="creator-tag-framework-entry">
        <input data-framework-tag-entry="${escapeHTML(row.field)}" type="text" placeholder="输入后回车，或点选常用词" />
      </div>
      <div class="tag-suggestion-wrap framework-suggestions" data-framework-suggestions="${escapeHTML(row.field)}">${suggestions}</div>
    </div>
  `;
}

function renderTagFramework(form) {
  const grid = form.querySelector("[data-tag-framework-grid]");
  if (!grid) return;
  grid.innerHTML = [...TAG_FRAMEWORK_ROWS, TAG_NARRATIVE_FRAMEWORK_ROW].map((row) => renderTagFrameworkRow(form, row)).join("");
  renderTagCompleteness(form);
}

function addFrameworkTag(form, field, value) {
  const incoming = normalizeQuickTagValue(value);
  if (!incoming.length || !form.elements[field]) return;
  const tags = getFrameworkTags(form, field);
  incoming.forEach((tag) => {
    if (!tags.includes(tag)) tags.push(tag);
  });
  setFrameworkTags(form, field, tags);
  rememberQuickCreatorTags(field, incoming);
  renderTagFramework(form);
  renderCreatorTagSummaryFromForm(form);
  updateNarrativeFromFramework(form);
}

function removeFrameworkTag(form, field, value) {
  setFrameworkTags(
    form,
    field,
    getFrameworkTags(form, field).filter((tag) => tag !== value),
  );
  renderTagFramework(form);
  renderCreatorTagSummaryFromForm(form);
  updateNarrativeFromFramework(form);
}

function renderCreatorTagSummaryFromForm(form) {
  const containerId = form.id === "quickCreatorForm" ? "#quickCreatorTags" : "#creatorTags";
  const structured = collectStructuredTagsFromForm(form);
  renderCreatorTagSummary(
    {
      personal_tags: getPersonalTagsFromHub(form),
      industry_fit_tags: structured.industry_fit_tags,
      identity_tags: structured.identity_tags,
      content_capability_tags: structured.content_capability_tags,
      delivery_tags: structured.delivery_tags,
      risk_tags: structured.risk_tags,
      suitable_goals: structured.suitable_goals,
      budget_fit_tags: structured.budget_fit_tags,
      narrative_position: structured.narrative_position,
    },
    containerId,
  );
}

let creatorTagClassifyTimer = null;

function scheduleCreatorTagClassify(form) {
  if (!form) return;
  clearTimeout(creatorTagClassifyTimer);
  creatorTagClassifyTimer = setTimeout(() => {
    classifyCreatorTagsFromForm(form, { silent: true }).catch(() => {});
  }, 450);
}

async function classifyCreatorTagsFromForm(form, { silent = false } = {}) {
  if (!form?.querySelector("[data-creator-tag-hub]")) return null;
  const tags = getPersonalTagsFromHub(form);
  const structured = collectStructuredTagsFromForm(form);
  const payload = {
    tags,
    platform: form.elements.platform?.value || "",
    ...structured,
  };
  try {
    const data = await api("/api/creators/tags/classify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    applyTagClassificationToForm(form, data.classification || {});
    if (!silent) toast("标签已分发到分类");
    return data.classification;
  } catch (error) {
    if (!silent) toast(error.message || "标签整理失败", true);
    throw error;
  }
}

async function ensureCreatorTagsClassified(form) {
  if (!form?.querySelector("[data-creator-tag-hub]")) return;
  if (form.dataset.tagClassifyDirty === "true" || getPersonalTagsFromHub(form).length) {
    await classifyCreatorTagsFromForm(form, { silent: true });
  }
  const narrativeDisplay = form.elements.narrative_position_display?.value?.trim();
  if (narrativeDisplay && form.elements.narrative_position) {
    form.elements.narrative_position.value = narrativeDisplay;
  }
}

function hydrateCreatorTagHubFromCreator(form, creator = {}) {
  if (!form?.querySelector("[data-creator-tag-hub]")) return;
  const personal = [
    ...asTagList(creator.personal_tags),
    ...asTagList(creator.industry_fit_tags),
    ...asTagList(creator.identity_tags),
    ...asTagList(creator.content_capability_tags),
    ...asTagList(creator.delivery_tags),
    ...asTagList(creator.risk_tags),
    ...asTagList(creator.suitable_goals),
  ].filter((tag, index, list) => list.indexOf(tag) === index);
  if (form.elements.personal_tags) {
    const savedPersonal = asTagList(creator.personal_tags);
    form.elements.personal_tags.value = (savedPersonal.length ? savedPersonal : personal).join("，");
  }
  const assignList = (name, values = []) => {
    if (form.elements[name]) form.elements[name].value = asTagList(values).join("，");
  };
  assignList("industry_fit_tags", creator.industry_fit_tags);
  assignList("identity_tags", creator.identity_tags);
  assignList("content_capability_tags", creator.content_capability_tags);
  assignList("delivery_tags", creator.delivery_tags);
  assignList("risk_tags", creator.risk_tags);
  assignList("suitable_goals", creator.suitable_goals);
  assignList("budget_fit_tags", creator.budget_fit_tags);
  const narrative = creator.narrative_position || "";
  if (form.elements.narrative_position) form.elements.narrative_position.value = narrative;
  if (form.elements.narrative_position_display) form.elements.narrative_position_display.value = narrative;
  form.dataset.narrativeAuto = narrative ? "true" : "false";
  renderPersonalTagHub(form);
  renderTagFramework(form);
  renderCreatorTagSummaryFromForm(form);
  form.dataset.tagClassifyDirty = "false";
}

function bindCreatorTagHubEvents(root) {
  if (!root || root.dataset.tagHubBound === "true") return;
  root.dataset.tagHubBound = "true";
  root.addEventListener("click", (event) => {
    const form = event.target.closest("form");
    if (!form) return;
    const addButton = event.target.closest("[data-personal-tag-add]");
    if (addButton) {
      addPersonalTagToHub(form, addButton.dataset.personalTagAdd);
      return;
    }
    const removeButton = event.target.closest("[data-personal-tag-remove]");
    if (removeButton) {
      removePersonalTagFromHub(form, removeButton.dataset.personalTagRemove);
      return;
    }
    const classifyButton = event.target.closest("[data-classify-tags-btn]");
    if (classifyButton) {
      classifyCreatorTagsFromForm(form).catch(() => {});
      return;
    }
    const frameworkAdd = event.target.closest("[data-framework-tag-add]");
    if (frameworkAdd) {
      addFrameworkTag(form, frameworkAdd.dataset.frameworkTagAdd, frameworkAdd.dataset.frameworkTagSuggestion);
      return;
    }
    const frameworkRemove = event.target.closest("[data-framework-tag-remove]");
    if (frameworkRemove) {
      removeFrameworkTag(form, frameworkRemove.dataset.frameworkTagRemove, frameworkRemove.dataset.frameworkTagValue);
    }
  });
  root.addEventListener("keydown", (event) => {
    const frameworkEntry = event.target.closest("[data-framework-tag-entry]");
    if (frameworkEntry) {
      const form = frameworkEntry.closest("form");
      if (!form) return;
      if (event.key === "Enter" || event.key === "," || event.key === "，") {
        event.preventDefault();
        addFrameworkTag(form, frameworkEntry.dataset.frameworkTagEntry, frameworkEntry.value);
        frameworkEntry.value = "";
      }
      return;
    }
    const entry = event.target.closest("[data-personal-tag-entry]");
    if (!entry) return;
    const form = entry.closest("form");
    if (!form) return;
    if (event.key === "Enter" || event.key === "," || event.key === "，") {
      event.preventDefault();
      addPersonalTagToHub(form, entry.value);
      entry.value = "";
    }
  });
  root.addEventListener(
    "blur",
    (event) => {
      const frameworkEntry = event.target.closest("[data-framework-tag-entry]");
      if (frameworkEntry?.value.trim()) {
        const form = frameworkEntry.closest("form");
        if (form) {
          addFrameworkTag(form, frameworkEntry.dataset.frameworkTagEntry, frameworkEntry.value);
          frameworkEntry.value = "";
        }
        return;
      }
      const entry = event.target.closest("[data-personal-tag-entry]");
      if (!entry?.value.trim()) return;
      const form = entry.closest("form");
      if (!form) return;
      addPersonalTagToHub(form, entry.value);
      entry.value = "";
    },
    true,
  );
  root.addEventListener("input", (event) => {
    const field = event.target.closest("[name='narrative_position_display']");
    if (!field) return;
    const form = field.closest("form");
    if (form) {
      form.dataset.narrativeAuto = "false";
      if (form.elements.narrative_position) form.elements.narrative_position.value = field.value;
    }
  });
}

function initCreatorTagHub(form) {
  if (!form?.querySelector("[data-creator-tag-hub]")) return;
  renderPersonalTagHub(form);
  renderTagFramework(form);
  renderCreatorTagSummaryFromForm(form);
}

function closeQuickCreatorModal() {
  $("#quickCreatorModal")?.classList.add("hidden");
}

function normalizeQuickTagValue(value) {
  return String(value || "")
    .replaceAll("，", ",")
    .replaceAll("、", ",")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function asTagList(value) {
  if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean);
  if (value == null || value === "") return [];
  return normalizeQuickTagValue(value);
}

function initCreatorTagEditors(form) {
  if (!form) return;
  form.querySelectorAll(".tag-editor").forEach((editor) => {
    const fieldName = editor.dataset.tagField;
    const hidden = form.elements[fieldName];
    if (!hidden) return;
    hidden.value = normalizeQuickTagValue(hidden.value).join("，");
    renderCreatorTagEditor(editor);
  });
  initCreatorTagHub(form);
}

function initQuickCreatorTagEditors(form) {
  initCreatorTagEditors(form);
}

function renderCreatorTagEditor(editor) {
  const form = editor.closest("form");
  const fieldName = editor.dataset.tagField;
  const hidden = form?.elements[fieldName];
  const list = editor.querySelector("[data-tag-list]");
  if (!hidden || !list) return;
  const tags = normalizeQuickTagValue(hidden.value);
  const selected = new Set(tags);
  const chips = tags
    .map(
      (tag) => `
        <button class="tag-chip" data-tag-remove="${escapeHTML(tag)}" type="button">
          <span>${escapeHTML(tag)}</span><strong>×</strong>
        </button>
      `,
    )
    .join("");
  const suggestions = [...loadRecentQuickCreatorTags(fieldName), ...(QUICK_CREATOR_TAG_PRESETS[fieldName] || [])]
    .filter((tag, index, list) => list.indexOf(tag) === index)
    .filter((tag) => !selected.has(tag))
    .slice(0, 12)
    .map((tag) => `<button class="tag-suggestion" data-tag-add="${escapeHTML(tag)}" type="button">${escapeHTML(tag)}</button>`)
    .join("");
  list.innerHTML = chips || '<span class="meta">还没有标签，输入后回车添加</span>';
  let suggestionsNode = editor.querySelector("[data-tag-suggestions]");
  if (!suggestionsNode) {
    suggestionsNode = document.createElement("div");
    suggestionsNode.className = "tag-suggestion-list";
    suggestionsNode.dataset.tagSuggestions = "true";
    const label = document.createElement("div");
    label.className = "tag-suggestion-label";
    label.textContent = "最近使用 / 常用标签";
    suggestionsNode.appendChild(label);
    const wrap = document.createElement("div");
    wrap.className = "tag-suggestion-wrap";
    wrap.dataset.tagSuggestionWrap = "true";
    suggestionsNode.appendChild(wrap);
    editor.appendChild(suggestionsNode);
  }
  const wrap = suggestionsNode.querySelector("[data-tag-suggestion-wrap]");
  if (wrap) wrap.innerHTML = suggestions;
}

function addCreatorTag(editor, value) {
  const form = editor.closest("form");
  const fieldName = editor.dataset.tagField;
  const hidden = form?.elements[fieldName];
  if (!hidden) return;
  const incoming = normalizeQuickTagValue(value);
  if (!incoming.length) return;
  const tags = normalizeQuickTagValue(hidden.value);
  incoming.forEach((tag) => {
    if (!tags.includes(tag)) tags.push(tag);
  });
  hidden.value = tags.join("，");
  rememberQuickCreatorTags(fieldName, incoming);
  const entry = editor.querySelector("[data-tag-entry]");
  if (entry) entry.value = "";
  renderCreatorTagEditor(editor);
}

function addQuickCreatorTag(editor, value) {
  addCreatorTag(editor, value);
}

function removeCreatorTag(editor, value) {
  const form = editor.closest("form");
  const fieldName = editor.dataset.tagField;
  const hidden = form?.elements[fieldName];
  if (!hidden) return;
  hidden.value = normalizeQuickTagValue(hidden.value)
    .filter((tag) => tag !== value)
    .join("，");
  renderCreatorTagEditor(editor);
}

function removeQuickCreatorTag(editor, value) {
  removeCreatorTag(editor, value);
}

function bindCreatorTagEditorEvents(root) {
  if (!root || root.dataset.tagEditorsBound === "true") return;
  root.dataset.tagEditorsBound = "true";
  root.addEventListener("click", (event) => {
    const addButton = event.target.closest("[data-tag-add]");
    if (addButton) {
      addCreatorTag(addButton.closest(".tag-editor"), addButton.dataset.tagAdd);
      return;
    }
    const removeButton = event.target.closest("[data-tag-remove]");
    if (removeButton) {
      removeCreatorTag(removeButton.closest(".tag-editor"), removeButton.dataset.tagRemove);
    }
  });
  root.addEventListener("keydown", (event) => {
    const entry = event.target.closest("[data-tag-entry]");
    if (!entry) return;
    if (event.key === "Enter" || event.key === "," || event.key === "，") {
      event.preventDefault();
      addCreatorTag(entry.closest(".tag-editor"), entry.value);
    }
  });
  root.addEventListener(
    "blur",
    (event) => {
      const entry = event.target.closest("[data-tag-entry]");
      if (entry?.value.trim()) addCreatorTag(entry.closest(".tag-editor"), entry.value);
    },
    true,
  );
}

function resetQuickCreatorAvatar(form) {
  if (form.elements.avatar_url) form.elements.avatar_url.value = "";
  if (form.elements.avatar_url_display) form.elements.avatar_url_display.value = "";
  syncCreatorAvatarPreview(form, "", "quickCreatorAvatarPreview");
}

async function setCreatorFormAvatar(file, form, previewId) {
  if (!file || !form?.elements.avatar_url) return;
  const dataUrl = await imageFileToDataUrl(file, 360);
  form.elements.avatar_url.value = dataUrl;
  const preview = document.getElementById(previewId) || $("#quickCreatorAvatarPreview");
  if (preview) {
    preview.textContent = "";
    preview.style.backgroundImage = `url("${dataUrl}")`;
    preview.classList.add("has-image");
  }
  const display = form.elements.avatar_url_display;
  if (display) display.value = dataUrl;
}

async function setQuickCreatorAvatar(file, form) {
  await setCreatorFormAvatar(file, form, "quickCreatorAvatarPreview");
}

function syncCreatorAvatarPreview(form, avatarUrl, previewId = "creatorEditAvatarPreview") {
  const preview = document.getElementById(previewId);
  if (!preview) return;
  if (avatarUrl) {
    preview.textContent = "";
    preview.style.backgroundImage = `url("${avatarUrl}")`;
    preview.classList.add("has-image");
  } else {
    preview.textContent = "头像";
    preview.style.backgroundImage = "";
    preview.classList.remove("has-image");
  }
  const display = form.elements.avatar_url_display;
  if (display) display.value = avatarUrl || "";
}

function imageFileToDataUrl(file, maxSize = 360) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("头像读取失败"));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error("头像图片无法解析"));
      img.onload = () => {
        const scale = Math.min(1, maxSize / Math.max(img.width, img.height));
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(img.width * scale));
        canvas.height = Math.max(1, Math.round(img.height * scale));
        const context = canvas.getContext("2d");
        context.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL("image/jpeg", 0.82));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

function prepareCreatorFormPayload(form) {
  initCreatorTagEditors(form);
  const narrativeDisplay = form.elements.narrative_position_display?.value?.trim();
  if (narrativeDisplay && form.elements.narrative_position) {
    form.elements.narrative_position.value = narrativeDisplay;
  }
  syncCreatorDataCardPanel(form);
  const rateContainer = form.id === "quickCreatorForm" ? $("#quickCreatorRateFields") : $("#creatorEditRateFields");
  if (rateContainer && !rateContainer.querySelector(".platform-rate-row") && form.elements.platform) {
    renderCreatorRateFields(form, rateContainer, rateValuesFromNotes(form.elements.manual_notes?.value || "", form.elements.platform.value));
  }
  const { fields, values } = readCreatorRateValues(form);
  const notesEditor = form.querySelector('[data-tag-field="manual_notes"]');
  const formatsEditor = form.querySelector('[data-tag-field="cooperation_formats"]');
  const noteTags = normalizeQuickTagValue(form.elements.manual_notes?.value).filter((tag) => !isRateNoteTag(tag));
  const formatTags = normalizeQuickTagValue(form.elements.cooperation_formats?.value);
  const rateTags = [];
  const cooperationFormats = new Set(formatTags);
  let primaryPrice = 0;

  fields.forEach((item) => {
    const amount = Number(values[item.key] || 0);
    if (!amount) return;
    rateTags.push(`${item.label}：${amount}`);
    const formatName = rateLabelToFormat(item.label);
    if (formatName) cooperationFormats.add(formatName);
    if (item.primary) primaryPrice = amount;
  });
  if (!primaryPrice) {
    primaryPrice = Object.values(values).find((value) => Number(value) > 0) || 0;
  }
  if (form.elements.listed_price) form.elements.listed_price.value = String(primaryPrice || "");
  if (form.elements.manual_notes) form.elements.manual_notes.value = [...noteTags, ...rateTags].join("，");
  if (form.elements.cooperation_formats) form.elements.cooperation_formats.value = [...cooperationFormats].join("，");
  if (notesEditor) renderCreatorTagEditor(notesEditor);
  if (formatsEditor) renderCreatorTagEditor(formatsEditor);
}

function prepareQuickCreatorPayload(form) {
  prepareCreatorFormPayload(form);
}

async function saveManualCreator(form, { openDetail = false } = {}) {
  await ensureCreatorTagsClassified(form);
  const payload = creatorFormPayload(form);
  const commercialCases = collectCommercialCasesFromForm(form);
  if (commercialCases.length) payload.commercial_cases = commercialCases;
  const data = await api("/api/import/manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const creatorId = data.creator?.creator_id;
  if (creatorId && state.quickCreatorPendingAssets?.length) {
    for (const item of state.quickCreatorPendingAssets) {
      if (!item.file) continue;
      try {
        const body = new FormData();
        body.append("file", item.file);
        await api(`/api/creators/${encodeURIComponent(creatorId)}/media/analyze`, { method: "POST", body });
      } catch {
        /* non-fatal: core profile already saved */
      }
    }
  }
  if (creatorId) {
    try {
      await api("/api/kol-intelligence/analyze-tags", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ creator_id: creatorId, limit: 1 }),
      });
    } catch {
      /* non-fatal */
    }
  }
  state.quickCreatorPendingAssets = [];
  state.quickCreatorEvidenceTags = [];
  state.quickCreatorAiPreview = null;
  form.reset();
  await reloadAll();
  toast(`已保存：${data.creator.name}`);
  if (openDetail && creatorId) {
    setView("creators");
    await openCreatorModal(creatorId);
  }
  return data;
}

function setCreatorFormField(form, name, value) {
  const field = form?.elements?.[name];
  if (!field) return;
  field.value = value == null ? "" : value;
}

function renderCreatorModal(creator) {
  const form = $("#creatorEditForm");
  if (!form || !creator) {
    throw new Error("达人详情表单未就绪");
  }
  $("#creatorModalTitle").textContent = creator.name || "未命名达人";
  $("#creatorModalMeta").textContent = `${creator.platform || "未知平台"} · ${creator.creator_id || ""}`;
  renderCreatorProfileHeader(creator);
  setCreatorFormField(form, "creator_id", creator.creator_id || "");
  setCreatorFormField(form, "name", creator.name || "");
  setCreatorFormField(form, "platform", normalizePlatformValue(creator.platform || PLATFORM_OPTIONS[0]));
  renderPlatformSelectOptions(form.elements.platform, normalizePlatformValue(creator.platform || PLATFORM_OPTIONS[0]));
  setCreatorFormField(form, "platform_user_id", creator.platform_user_id || "");
  setCreatorFormField(form, "homepage_url", creator.homepage_url || "");
  setCreatorFormField(form, "avatar_url", creator.avatar_url || "");
  syncCreatorAvatarPreview(form, creator.avatar_url || "");
  setCreatorFormField(form, "follower_count", creator.follower_count || "");
  setCreatorFormField(form, "listed_price", creator.listed_price || "");
  setCreatorFormField(form, "total_likes", creator.total_likes || "");
  setCreatorFormField(form, "engagement_rate", creator.engagement_rate || "");
  setCreatorFormField(form, "like_fan_ratio", creator.like_fan_ratio || "");
  setCreatorFormField(form, "avg_likes", creator.avg_likes || "");
  setCreatorFormField(form, "avg_comments", creator.avg_comments || "");
  setCreatorFormField(form, "avg_shares", creator.avg_shares || "");
  setCreatorFormField(form, "region", creator.region || "");
  setCreatorFormField(form, "contact", creator.contact || "");
  setCreatorFormField(form, "cooperation_brands", asTagList(creator.cooperation_brands).join("，"));
  setCreatorFormField(form, "cooperation_formats", asTagList(creator.cooperation_formats).join("，"));
  hydrateCreatorTagHubFromCreator(form, creator);
  setCreatorFormField(form, "bio", creator.bio || "");
  setCreatorFormField(form, "manual_notes", remarkTagsFromNotes(creator.manual_notes || "").join("，"));
  renderCreatorRateFields(form, $("#creatorEditRateFields"), rateValuesFromNotes(creator.manual_notes || "", creator.platform));
  initCreatorTagEditors(form);
  bindCommercialCasesEditor(form);
  loadCommercialCasesForCreator(creator.creator_id, form);
  const kitOutput = $("#creatorCommercialKitOutput");
  if (kitOutput) {
    kitOutput.innerHTML = '<div class="commercial-card-empty">点击生成后，会在这里出现卡片式商业名片刊例。</div>';
    kitOutput.dataset.copyText = "";
  }
  renderCreatorMediaAssets(creator);
  renderCreatorImageAnalysis(null);
  const dataSourcesNode = $("#creatorDataSources");
  if (dataSourcesNode) {
    const sources = asTagList(creator.data_sources);
    dataSourcesNode.innerHTML = sources.length
      ? sources.map((source) => `<span class="tag">${escapeHTML(source)}</span>`).join("")
      : '<span class="meta">暂无来源</span>';
  }
  renderCreatorEvidenceTags(state.activeCreatorEvidenceTags);
  syncCreatorDataCardPanel(form);
}

function renderCreatorTagSummary(creator, containerId = "#creatorTags") {
  const node = $(containerId);
  if (!node) return;
  const tags = [
    ...asTagList(creator.personal_tags),
    ...asTagList(creator.industry_fit_tags),
    ...asTagList(creator.identity_tags),
    ...asTagList(creator.content_capability_tags),
    ...asTagList(creator.delivery_tags),
    ...asTagList(creator.suitable_goals),
    ...asTagList(creator.suitable_stages),
    ...asTagList(creator.budget_fit_tags),
    ...asTagList(creator.risk_tags),
  ];
  const narrative = creator.narrative_position ? `<span class="tag narrative">${escapeHTML(creator.narrative_position)}</span>` : "";
  const tagHtml = tags.map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("");
  node.innerHTML = narrative || tagHtml ? `${narrative}${tagHtml}` : '<span class="meta">暂无标签</span>';
}

function renderCreatorEvidenceTags(tags = state.activeCreatorEvidenceTags, options = {}) {
  const node = $(options.containerId || "#creatorEvidenceTags");
  if (!node) return;
  const reviewable = options.reviewable !== false && Boolean(state.activeCreator?.creator_id);
  const items = tags || [];
  if (!items.length) {
    node.innerHTML = emptyState(
      "暂无证据标签",
      reviewable ? "点击「运行 AI 判断」后会生成。" : "点击「运行 AI 判断」后会在此预览，保存后写入证据库。",
    );
    return;
  }
  node.innerHTML = items
    .slice(0, 40)
    .map(
      (tag) => `
        <article class="creator-evidence-tag ${escapeHTML(tag.status || "suggested")}">
          <div>
            <span class="status-pill ${phase8StatusTone(tag.status)}">${escapeHTML(tag.status || "suggested")}</span>
            <strong>${escapeHTML(tag.tag)}</strong>
            <span class="meta">${escapeHTML(tag.category)} · confidence ${Math.round((tag.confidence || 0) * 100)}%</span>
          </div>
          <small>${escapeHTML((tag.evidence || []).slice(0, 2).join("；"))}</small>
          ${
            reviewable
              ? `<div class="button-row">
            <button class="secondary creator-evidence-review-btn" data-status="confirmed" data-tag-id="${escapeHTML(tag.tag_id)}" type="button">确认</button>
            <button class="secondary creator-evidence-review-btn danger" data-status="rejected" data-tag-id="${escapeHTML(tag.tag_id)}" type="button">拒绝</button>
          </div>`
              : ""
          }
        </article>
      `,
    )
    .join("");
}

function renderCreatorMediaAssets(creator) {
  const node = $("#creatorMediaAssets");
  if (!node) return;
  const assets = Array.isArray(creator.media_assets) ? creator.media_assets.slice(-6).reverse() : [];
  node.innerHTML = assets.length
    ? assets
        .map((asset) => {
          const label = asset.image_type || "image";
          const key = asset.key || asset.url || "uploaded image";
          const href = asset.url || "";
          return `
            <article class="media-asset-item">
              <span class="tag">${escapeHTML(label)}</span>
              <div>
                <strong>${escapeHTML(key.split("/").pop() || key)}</strong>
                <div class="meta">${escapeHTML(asset.provider || "")} · ${fmtNumber(asset.size)} bytes · ${escapeHTML(asset.uploaded_at || "")}</div>
              </div>
              ${href ? `<a class="text-btn" href="${escapeHTML(href)}" target="_blank" rel="noreferrer">打开</a>` : ""}
            </article>
          `;
        })
        .join("")
    : '<span class="meta">暂无图片资产</span>';
}

function renderCreatorImageAnalysis(result, options = {}) {
  const box = $(options.boxId || "#creatorImageAnalysis");
  const applyBtn = $(options.applyBtnId || "#creatorImageApplyBtn");
  const stateKey = options.stateKey || "activeCreatorImageSuggestion";
  if (!box || !applyBtn) return;
  if (!result) {
    box.classList.add("hidden");
    box.innerHTML = "";
    applyBtn.classList.add("hidden");
    state[stateKey] = null;
    return;
  }
  const analysis = result.analysis || {};
  const patch = result.suggested_patch || {};
  state[stateKey] = patch;
  const fieldRows = Object.entries(patch)
    .map(([key, value]) => `<li><strong>${escapeHTML(key)}</strong><span>${escapeHTML(Array.isArray(value) ? value.join("，") : value)}</span></li>`)
    .join("");
  const warnings = (analysis.warnings || []).map((item) => `<span class="tag risk">${escapeHTML(item)}</span>`).join("");
  const evidence = (analysis.evidence || []).map((item) => `<li>${escapeHTML(item)}</li>`).join("");
  box.classList.remove("hidden");
  box.innerHTML = `
    <div class="analysis-head">
      <span class="tag">${escapeHTML(analysis.image_type || "unknown")}</span>
      <span class="tag">${escapeHTML(analysis.confidence || "low")}</span>
      <span class="tag">${escapeHTML(analysis.provider || "vision")}</span>
    </div>
    ${fieldRows ? `<ul class="analysis-fields">${fieldRows}</ul>` : '<div class="meta">没有识别到可直接填入的字段。</div>'}
    ${evidence ? `<div class="analysis-block"><strong>识别依据</strong><ul>${evidence}</ul></div>` : ""}
    ${warnings ? `<div class="tag-list">${warnings}</div>` : ""}
  `;
  applyBtn.classList.toggle("hidden", !Object.keys(patch).length);
}

function applyCreatorImageSuggestion(form = $("#creatorEditForm"), options = {}) {
  const stateKey = options.stateKey || (form?.id === "quickCreatorForm" ? "quickCreatorImageSuggestion" : "activeCreatorImageSuggestion");
  const patch = state[stateKey] || {};
  if (!form || !Object.keys(patch).length) return;
  applyCreatorIntakePatch(form, patch);
  toast("已填入识别结果，确认后点击保存");
}

function applyCreatorIntakePatch(form, patch) {
  const listFields = new Set([
    "cooperation_brands",
    "cooperation_formats",
    "industry_fit_tags",
    "identity_tags",
    "content_capability_tags",
    "suitable_goals",
    "suitable_stages",
    "budget_fit_tags",
    "risk_tags",
    "delivery_tags",
    "personal_tags",
    "manual_notes",
  ]);
  Object.entries(patch).forEach(([key, value]) => {
    if (key === "ai_summary") return;
    const field = form.elements[key];
    if (!field) return;
    if (key === "narrative_position") {
      const text = String(value || "").trim();
      field.value = text;
      if (form.elements.narrative_position_display) form.elements.narrative_position_display.value = text;
      return;
    }
    if (listFields.has(key)) {
      const existing = normalizeQuickTagValue(field.value);
      const incoming = Array.isArray(value) ? value.map((item) => String(item).trim()).filter(Boolean) : normalizeQuickTagValue(value);
      field.value = [...new Set([...existing, ...incoming])].join("，");
      return;
    }
    if (!String(field.value || "").trim()) {
      field.value = Array.isArray(value) ? value.join("，") : value;
    }
  });
  const previewId = form.id === "quickCreatorForm" ? "quickCreatorAvatarPreview" : "creatorEditAvatarPreview";
  if (form.elements.avatar_url?.value) syncCreatorAvatarPreview(form, form.elements.avatar_url.value, previewId);
  const rateContainer = form.id === "quickCreatorForm" ? $("#quickCreatorRateFields") : $("#creatorEditRateFields");
  renderCreatorRateFields(form, rateContainer, rateValuesFromNotes(form.elements.manual_notes?.value || "", form.elements.platform?.value));
  initCreatorTagEditors(form);
  if (form.querySelector("[data-creator-tag-hub]")) {
    scheduleCreatorTagClassify(form);
  }
  if (form.id === "quickCreatorForm") {
    renderCreatorTagSummary(getCreatorDraftFromForm(form), "#quickCreatorTags");
    refreshCreatorCommercialKitPreview(form);
  }
}

function creatorFormPayload(form) {
  prepareCreatorFormPayload(form);
  const fields = form.elements;
  const avatarUrl = fields.avatar_url_display?.value?.trim() || fields.avatar_url.value;
  return {
    name: fields.name.value,
    platform: fields.platform.value,
    platform_user_id: fields.platform_user_id.value,
    homepage_url: fields.homepage_url.value,
    avatar_url: avatarUrl,
    follower_count: Number(fields.follower_count.value || 0),
    listed_price: Number(fields.listed_price.value || 0),
    total_likes: Number(fields.total_likes.value || 0),
    engagement_rate: Number(fields.engagement_rate.value || 0),
    like_fan_ratio: Number(fields.like_fan_ratio?.value || computeLikeFanRatio(fields.follower_count.value, fields.total_likes.value) || 0),
    avg_likes: Number(fields.avg_likes.value || 0),
    avg_comments: Number(fields.avg_comments.value || 0),
    avg_shares: Number(fields.avg_shares.value || 0),
    region: fields.region.value,
    contact: fields.contact.value,
    cooperation_brands: fields.cooperation_brands.value,
    cooperation_formats: fields.cooperation_formats.value,
    industry_fit_tags: fields.industry_fit_tags.value,
    identity_tags: fields.identity_tags.value,
    content_capability_tags: fields.content_capability_tags.value,
    suitable_goals: fields.suitable_goals.value,
    risk_tags: fields.risk_tags.value,
    personal_tags: fields.personal_tags?.value || "",
    delivery_tags: fields.delivery_tags?.value || "",
    budget_fit_tags: fields.budget_fit_tags?.value || "",
    narrative_position: fields.narrative_position?.value || fields.narrative_position_display?.value || "",
    bio: fields.bio.value,
    manual_notes: fields.manual_notes.value,
  };
}

function getCreatorDraftFromForm(form) {
  if (!form) return null;
  const payload = creatorFormPayload(form);
  const base = form.id === "quickCreatorForm" ? state.quickCreatorAiPreview || {} : state.activeCreator || {};
  return {
    ...base,
    ...payload,
    ai_summary:
      (form.id === "quickCreatorForm" ? state.quickCreatorAiPreview?.ai_summary : state.activeCreator?.ai_summary) || "",
    cooperation_brands: splitInputList(payload.cooperation_brands),
    cooperation_formats: splitInputList(payload.cooperation_formats),
    industry_fit_tags: splitInputList(payload.industry_fit_tags),
    identity_tags: splitInputList(payload.identity_tags),
    content_capability_tags: splitInputList(payload.content_capability_tags),
    suitable_goals: splitInputList(payload.suitable_goals),
    risk_tags: splitInputList(payload.risk_tags),
    delivery_tags: splitInputList(payload.delivery_tags),
    personal_tags: splitInputList(payload.personal_tags),
    budget_fit_tags: splitInputList(payload.budget_fit_tags),
    narrative_position: payload.narrative_position || "",
  };
}

function creatorDraftFromCurrentForm() {
  return getCreatorDraftFromForm($("#creatorEditForm"));
}

function compactTextList(items, fallback = "待补充") {
  const list = Array.isArray(items) ? items.filter(Boolean) : splitInputList(items);
  return list.length ? list.join("、") : fallback;
}

function cleanList(items) {
  return Array.isArray(items) ? items.filter(Boolean) : splitInputList(items);
}

function hasValue(value) {
  if (Array.isArray(value)) return value.filter(Boolean).length > 0;
  return String(value || "").trim() !== "" && String(value || "").trim() !== "0";
}

function extractRateFromNotes(notes, label) {
  const match = String(notes || "").match(new RegExp(`${label}[：:]\\s*([0-9]+)`));
  return match ? Number(match[1]) : 0;
}

function extractPlatformRates(creator) {
  const fields = getPlatformRateFields(creator.platform);
  const notes = creator.manual_notes || "";
  const rates = fields
    .map((item) => {
      const amount = extractRateFromNotes(notes, item.label);
      return amount ? [item.label.replace(/报价$/, ""), `${fmtNumber(amount)} 元`] : null;
    })
    .filter(Boolean);
  const fallback = Number(creator.listed_price || 0);
  if (!rates.length && fallback) rates.push(["报价", `${fmtNumber(fallback)} 元`]);
  return rates;
}

function creatorRateLines(creator) {
  const lines = [];
  const rates = extractPlatformRates(creator);
  if (rates.length) {
    rates.forEach(([label, value]) => lines.push(`- ${label}：${value}`));
  } else {
    lines.push("- 基础报价：待报价");
  }
  const formats = creator.cooperation_formats || [];
  if (formats.length) lines.push(`- 可合作形式：${compactTextList(formats)}`);
  lines.push("- 价格说明：以上为内部刊例/线索价，最终以档期、主题、交付要求和确认报价为准。");
  return lines.join("\n");
}

function creatorCommercialKitData(creator) {
  return {
    name: creator.name || "",
    platform: creator.platform || "",
    avatar: creator.avatar_url || "",
    homepage: creator.homepage_url || "",
    contact: creator.contact || "",
    followers: Number(creator.follower_count || 0),
    bio: creator.bio || creator.ai_summary || "",
    brands: cleanList(creator.cooperation_brands),
    industries: cleanList(creator.industry_fit_tags),
    identities: cleanList(creator.identity_tags),
    capabilities: cleanList(creator.content_capability_tags),
    formats: cleanList(creator.cooperation_formats),
    narratives: cleanList(creator.suitable_goals),
    risks: cleanList(creator.risk_tags),
    notes: cleanList(creator.manual_notes).filter((item) => !isRateNoteTag(item)),
    rates: extractPlatformRates(creator),
  };
}

function renderCommercialChips(items, tone = "") {
  return cleanList(items).map((item) => `<span class="commercial-chip ${tone}">${escapeHTML(item)}</span>`).join("");
}

function renderCommercialSection(title, content) {
  if (!hasValue(content)) return "";
  return `<section class="commercial-card-section"><h4>${escapeHTML(title)}</h4>${content}</section>`;
}

function renderCommercialTagSection(title, items, tone = "") {
  const list = cleanList(items);
  if (!list.length) return "";
  return renderCommercialSection(title, `<div class="commercial-chip-row">${renderCommercialChips(list, tone)}</div>`);
}

function renderCommercialCasesSection(cases = []) {
  const items = (Array.isArray(cases) ? cases : []).filter((item) => {
    const visibility = item.visibility || "public";
    return item.featured_on_kit !== false && visibility !== "internal";
  });
  if (!items.length) return "";
  const cards = items
    .map((item) => {
      const title = caseDisplayTitle(item);
      const summary = caseDisplaySummary(item);
      const link = item.content_url || "";
      const publicPath = item.case_id && (item.visibility || "public") !== "internal" ? `/cases/${encodeURIComponent(item.case_id)}` : "";
      return `
        <article class="commercial-case-card">
          <div class="commercial-case-card-brand">${escapeHTML(item.brand_name || "")}</div>
          <h5>${escapeHTML(title)}</h5>
          ${summary ? `<p>${escapeHTML(summary)}</p>` : ""}
          <div class="commercial-case-card-links">
            ${link ? `<a href="${escapeHTML(link)}" target="_blank" rel="noreferrer">原内容</a>` : ""}
            ${publicPath ? `<a href="${escapeHTML(publicPath)}" target="_blank" rel="noreferrer">案例页</a>` : ""}
          </div>
        </article>
      `;
    })
    .join("");
  return renderCommercialSection("精选合作案例", `<div class="commercial-case-grid">${cards}</div>`);
}

function buildCreatorCommercialKitHtml(creator, featuredCases = []) {
  const data = creatorCommercialKitData(creator);
  const avatar = data.avatar
    ? `<img src="${escapeHTML(data.avatar)}" alt="${escapeHTML(data.name)}头像" />`
    : `<span>${escapeHTML((data.name || "KOL").slice(0, 2).toUpperCase())}</span>`;
  const meta = [
    data.platform ? `<span>${escapeHTML(data.platform)}</span>` : "",
    data.followers ? `<span>${fmtNumber(data.followers)} 粉丝</span>` : "",
    data.homepage ? `<a href="${escapeHTML(data.homepage)}" target="_blank" rel="noreferrer">主页</a>` : "",
    data.contact ? `<span>${escapeHTML(data.contact)}</span>` : "",
  ].filter(Boolean).join("");
  const rateCards = data.rates.map(([label, value]) => `<div class="rate-card"><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong></div>`).join("");
  return `
    <article class="creator-commercial-card">
      <header class="commercial-card-header">
        <div class="commercial-card-avatar">${avatar}</div>
        <div>
          <div class="card-kicker">business rate card</div>
          <h3>${escapeHTML(data.name || "未命名达人")}</h3>
          ${meta ? `<div class="commercial-card-meta">${meta}</div>` : ""}
        </div>
      </header>
      ${data.bio ? `<p class="commercial-card-bio">${escapeHTML(data.bio)}</p>` : ""}
      ${rateCards ? `<section class="commercial-card-section"><h4>刊例报价</h4><div class="rate-card-grid">${rateCards}</div></section>` : ""}
      ${renderCommercialTagSection("服务品牌", data.brands)}
      ${renderCommercialTagSection("领域", data.industries)}
      ${renderCommercialTagSection("身份", data.identities)}
      ${renderCommercialTagSection("内容能力", data.capabilities)}
      ${renderCommercialTagSection("合作形式", data.formats)}
      ${renderCommercialTagSection("叙事角色", data.narratives)}
      ${renderCommercialTagSection("履约备注", data.notes)}
      ${renderCommercialTagSection("风险提示", data.risks, "risk")}
      ${renderCommercialCasesSection(featuredCases)}
    </article>
  `;
}

function buildCreatorCommercialKitText(creator) {
  const data = creatorCommercialKitData(creator);
  const lines = [
    `${data.name || "未命名达人"}｜${data.platform || "平台未填"}商业名片刊例`,
    data.followers ? `粉丝：${fmtNumber(data.followers)}` : "",
    data.homepage ? `主页：${data.homepage}` : "",
    data.contact ? `联系方式：${data.contact}` : "",
    data.rates.length ? `报价：${data.rates.map(([label, value]) => `${label}${value}`).join("；")}` : "",
    data.brands.length ? `服务品牌：${data.brands.join("、")}` : "",
    data.industries.length ? `领域：${data.industries.join("、")}` : "",
    data.identities.length ? `身份：${data.identities.join("、")}` : "",
    data.capabilities.length ? `内容能力：${data.capabilities.join("、")}` : "",
    data.formats.length ? `合作形式：${data.formats.join("、")}` : "",
    data.narratives.length ? `叙事角色：${data.narratives.join("、")}` : "",
    data.notes.length ? `履约备注：${data.notes.join("、")}` : "",
    data.risks.length ? `风险提示：${data.risks.join("、")}` : "",
  ];
  return lines.filter(Boolean).join("\n");
}

function openCreatorCommercialKitWeb(creatorId = "") {
  const form = $("#creatorEditForm");
  const outputId = form?.id === "quickCreatorForm" ? "#quickCreatorCommercialKitOutput" : "#creatorCommercialKitOutput";
  let card = $(outputId)?.querySelector(".creator-commercial-card");
  if (!card) {
    generateCreatorCommercialKit(form);
    card = $(outputId)?.querySelector(".creator-commercial-card");
  }
  if (!card) {
    toast("请先生成名片刊例", true);
    return;
  }
  const creator = getCreatorDraftFromForm(form) || state.activeCreator || {};
  const id = String(creatorId || creator.creator_id || state.activeCreator?.creator_id || "").trim();
  openCreatorKitPreviewBlob(card, creator, id ? creatorKitShareUrl(id) : "");
}

function generateCreatorCommercialKit(form = null) {
  const targetForm = form || $("#creatorEditForm");
  const creator = getCreatorDraftFromForm(targetForm);
  if (!creator?.name) {
    toast("请先填写达人名称", true);
    return "";
  }
  const outputId = targetForm?.id === "quickCreatorForm" ? "#quickCreatorCommercialKitOutput" : "#creatorCommercialKitOutput";
  const output = $(outputId);
  const cases = collectCommercialCasesFromForm(targetForm);
  const html = buildCreatorCommercialKitHtml(creator, cases);
  const text = buildCreatorCommercialKitText(creator);
  if (output) {
    output.innerHTML = html;
    output.dataset.copyText = text;
  }
  toast("商业名片刊例已生成");
  return text;
}

function refreshCommercialKitPreview(form) {
  if (!form) return;
  const outputId = form.id === "quickCreatorForm" ? "#quickCreatorCommercialKitOutput" : "#creatorCommercialKitOutput";
  const output = $(outputId);
  if (!output) return;
  if (form.id !== "quickCreatorForm" && !output.querySelector(".creator-commercial-card")) return;
  const creator = getCreatorDraftFromForm(form);
  if (!creator?.name) return;
  const cases = collectCommercialCasesFromForm(form);
  const html = buildCreatorCommercialKitHtml(creator, cases);
  const text = buildCreatorCommercialKitText(creator);
  output.innerHTML = html;
  output.dataset.copyText = text;
}

function refreshCreatorCommercialKitPreview(form = $("#quickCreatorForm")) {
  refreshCommercialKitPreview(form);
}

function creatorKitFilename(form = null, ext = "pdf") {
  const targetForm = form || $("#creatorEditForm");
  const creator = getCreatorDraftFromForm(targetForm);
  const name = (creator?.name || state.activeCreator?.name || "达人").replace(/[\\/:*?"<>|\\s]+/g, "_");
  return `${name}_商业名片刊例.${ext}`;
}

async function downloadCreatorCommercialKit(form = null) {
  const targetForm = form || $("#creatorEditForm");
  const outputId = targetForm?.id === "quickCreatorForm" ? "#quickCreatorCommercialKitOutput" : "#creatorCommercialKitOutput";
  const output = $(outputId);
  if (!output?.querySelector(".creator-commercial-card")) generateCreatorCommercialKit(targetForm);
  const card = output?.querySelector(".creator-commercial-card");
  if (!card) return;
  try {
    const html2pdf = await loadHtml2PdfLib();
    await html2pdf()
      .set({
        margin: [10, 10, 10, 10],
        filename: creatorKitFilename(targetForm, "pdf"),
        image: { type: "jpeg", quality: 0.95 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
      })
      .from(card)
      .save();
    toast("PDF 已下载");
  } catch (error) {
    toast(error.message || "PDF 生成失败", true);
  }
}

async function runCreatorFormAiJudgment(form) {
  if (!form) return;
  const isQuick = form.id === "quickCreatorForm";
  const button = isQuick ? $("#runQuickCreatorAiBtn") : $("#runCreatorAiBtn");
  const summaryNode = isQuick ? $("#quickCreatorAiSummary") : $("#creatorAiSummary");
  prepareCreatorFormPayload(form);
  const payload = creatorFormPayload(form);
  if (!payload.name) return toast("请先填写达人名称", true);
  if (button) {
    button.disabled = true;
    button.textContent = "判断中...";
  }
  try {
    if (isQuick) {
      const data = await api("/api/creators/intake/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      state.quickCreatorAiPreview = data.creator;
      state.quickCreatorEvidenceTags = data.evidence_tags || [];
      applyCreatorIntakePatch(form, data.suggested_patch || {});
      if (summaryNode) summaryNode.textContent = data.creator?.ai_summary || "暂无 AI 摘要。";
      renderCreatorEvidenceTags(state.quickCreatorEvidenceTags, { containerId: "#quickCreatorEvidenceTags", reviewable: false });
      renderCreatorTagSummary(getCreatorDraftFromForm(form), "#quickCreatorTags");
      refreshCreatorCommercialKitPreview(form);
      toast("AI 判断已更新，标签已自动填入");
      return;
    }
    const creatorId = form.elements.creator_id?.value;
    if (!creatorId) return toast("未找到达人 ID", true);
    await api(`/api/creators/${encodeURIComponent(creatorId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await api("/api/kol-intelligence/analyze-tags", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ creator_id: creatorId, limit: 1 }),
    });
    const detail = await api(`/api/creators/${encodeURIComponent(creatorId)}`);
    state.activeCreator = detail.creator;
    state.activeCreatorEvidenceTags = detail.evidence_tags || [];
    renderCreatorModal(detail.creator);
    toast("AI 判断已更新");
  } catch (error) {
    toast(error.message || "AI 判断失败", true);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "运行 AI 判断";
    }
  }
}

function renderQuickCreatorMediaAssets() {
  const node = $("#quickCreatorMediaAssets");
  if (!node) return;
  const assets = state.quickCreatorPendingAssets || [];
  node.innerHTML = assets.length
    ? assets
        .map((item, index) => {
          const analysis = item.analysis || {};
          const label = analysis.image_type || "image";
          const key = item.stored_object?.key || item.file?.name || `upload-${index + 1}`;
          return `
            <article class="media-asset-item">
              <span class="tag">${escapeHTML(label)}</span>
              <div>
                <strong>${escapeHTML(String(key).split("/").pop() || key)}</strong>
                <div class="meta">${escapeHTML(analysis.confidence || "pending")} · 待保存入库</div>
              </div>
            </article>
          `;
        })
        .join("")
    : '<span class="meta">暂无图片资产</span>';
}

async function analyzeQuickCreatorImage() {
  const form = $("#quickCreatorForm");
  const fileInput = $("#quickCreatorImageInput");
  const file = fileInput?.files?.[0];
  if (!form || !file) return toast("请先选择一张图片", true);
  const button = $("#quickCreatorImageAnalyzeBtn");
  prepareCreatorFormPayload(form);
  const context = creatorFormPayload(form);
  const body = new FormData();
  body.append("file", file);
  body.append("context", JSON.stringify(context));
  if (button) {
    button.disabled = true;
    button.textContent = "识别中...";
  }
  try {
    const data = await api("/api/creators/intake/media/analyze", { method: "POST", body });
    state.quickCreatorPendingAssets.push({ file, analysis: data.analysis, stored_object: data.stored_object });
    renderQuickCreatorMediaAssets();
    renderCreatorImageAnalysis(data, {
      boxId: "#quickCreatorImageAnalysis",
      applyBtnId: "#quickCreatorImageApplyBtn",
      stateKey: "quickCreatorImageSuggestion",
    });
    toast("图片识别完成，可填入识别结果");
  } catch (error) {
    toast(error.message || "图片识别失败", true);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "识别图片";
    }
  }
}

function collectImportMappings() {
  const mappings = {};
  if (!state.importReview) return mappings;
  (state.importReview.sheets || []).forEach((sheet, index) => {
    const enabled = $(`.sheet-enabled[data-sheet="${index}"]`)?.checked ?? true;
    const mapping = {};
    $$(`select[data-sheet="${index}"]`).forEach((select) => {
      if (select.value) mapping[select.dataset.field] = select.value;
    });
    mappings[sheet.sheet] = { enabled, mapping };
  });
  return mappings;
}

function downloadProposal() {
  if (!state.lastProposal) {
    toast("请先生成方案", true);
    return;
  }
  const blob = new Blob([state.lastProposal], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "pr_ai_os_proposal.md";
  a.click();
  URL.revokeObjectURL(url);
}

async function copyText(value) {
  const text = String(value || "");
  if (!text) {
    toast("没有可复制的内容", true);
    return;
  }
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

function bindCreatorCardClicks(root) {
  root?.addEventListener("click", (event) => {
    handleCreatorOpenClick(event);
  });
}

function bindEvents() {
  document.addEventListener("click", handleCreatorOpenClick, true);
  initPlatformSelects();
  initCreatorListShell();
  renderTenantStatus();
  $("#sidebarToggleBtn")?.addEventListener("click", () => {
    state.sidebarCollapsed = !state.sidebarCollapsed;
    localStorage.setItem("pr_ai_os_sidebar_collapsed", state.sidebarCollapsed ? "1" : "0");
    applySidebarState();
  });
  $$(".nav-item").forEach((button) =>
    button.addEventListener("click", async () => {
      setView(button.dataset.view);
      if (button.dataset.view === "organization") {
        try {
          await loadOrganization();
        } catch (error) {
          toast(error.message, true);
        }
      }
      if (button.dataset.view === "agentWorkspace") {
        try {
          await loadAgentTasks();
        } catch (error) {
          toast(error.message, true);
        }
      }
      if (button.dataset.view === "knowledge") {
        try {
          await loadKnowledge();
        } catch (error) {
          toast(error.message, true);
        }
      }
      if (button.dataset.view === "kolIntelligence") {
        try {
          await loadKolIntelligence();
        } catch (error) {
          toast(error.message, true);
        }
      }
      if (button.dataset.view === "creatorFilter" || button.dataset.view === "creators") {
        try {
          await ensureCreatorsLoaded();
          if (button.dataset.view === "creatorFilter") {
            renderCreatorFilterTagFramework();
            renderCreatorFilterStepper();
            renderCreatorFilterFunnel();
            renderCreatorFilterResults();
          }
        } catch (error) {
          toast(error.message, true);
        }
      }
      if (button.dataset.view === "caseLibrary") {
        try {
          await ensureCreatorsLoaded().catch(() => {});
          if (!state.cases.length) await loadCases();
          else renderCases();
        } catch (error) {
          toast(error.message, true);
        }
      }
    })
  );
  $$(".nav-group").forEach((group) => {
    group.addEventListener("toggle", () => {
      if (!group.open) return;
      $$(".nav-group").forEach((other) => {
        if (other !== group) other.open = false;
      });
    });
  });
  $("#tenantApplyBtn").addEventListener("click", async () => {
    stopAgentPolling();
    const nextTenant = normalizeTenant($("#tenantInput").value);
    state.tenant = nextTenant;
    localStorage.setItem("pr_ai_os_tenant", nextTenant);
    renderTenantStatus(nextTenant);
    state.activePlatformCampaign = null;
    state.activeCampaignRoom = null;
    $("#platformCampaignDetail")?.classList.add("hidden");
    await reloadAll();
    toast(`已切换 workspace：${nextTenant}`);
  });
  $("#tenantInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") $("#tenantApplyBtn").click();
  });
  $("#accessKeyApplyBtn")?.addEventListener("click", async () => {
    state.accessKey = $("#accessKeyInput").value.trim();
    localStorage.setItem("pr_ai_os_access_key", state.accessKey);
    await reloadAll();
    toast(state.accessKey ? "访问凭证已保存" : "访问凭证已清空");
  });
  $("#accessKeyInput")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") $("#accessKeyApplyBtn").click();
  });
  $("#accessGateCloseBtn")?.addEventListener("click", hideAccessGate);
  $("#accessGate")?.addEventListener("click", (event) => {
    if (event.target?.id === "accessGate") hideAccessGate();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") hideAccessGate();
  });
  $("#loginForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const data = await api("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    persistAuthSession(data.session);
    hideAccessGate();
    await reloadAll();
    toast("已登录");
  });
  $("#bootstrapAdminForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    if (state.accessKey) payload.access_key = state.accessKey;
    const data = await api("/api/auth/bootstrap-admin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    persistAuthSession(data.session);
    hideAccessGate();
    await reloadAll();
    toast("Admin 已创建并登录");
  });
  $("#gateAccessKeyBtn")?.addEventListener("click", async () => {
    state.accessKey = $("#gateAccessKeyInput").value.trim();
    localStorage.setItem("pr_ai_os_access_key", state.accessKey);
    renderTenantStatus();
    hideAccessGate();
    try {
      await reloadAll();
      toast("已进入工作台");
    } catch (error) {
      showAccessGate();
      toast(error.message, true);
    }
  });
  $("#gateAccessClearBtn")?.addEventListener("click", () => {
    state.accessKey = "";
    localStorage.removeItem("pr_ai_os_access_key");
    renderTenantStatus();
    showAccessGate();
  });
  $("#gateAccessKeyInput")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") $("#gateAccessKeyBtn").click();
  });
  document.addEventListener("click", async (event) => {
    if (event.target.closest("#authOpenLoginBtn")) {
      window.location.href = "/login";
      return;
    }
    if (event.target.closest("#authLogoutBtn")) {
      stopAgentPolling();
      await api("/api/auth/logout", { method: "POST" });
      state.currentIdentity = null;
      state.accessKey = "";
      clearAuthSession();
      localStorage.removeItem("pr_ai_os_access_key");
      renderAuthUser();
      await reloadAll();
      toast("已退出登录");
      return;
    }
    const projectBtn = event.target.closest(".client-portal-open-project-btn");
    if (projectBtn) {
      await loadClientPortalProposal(projectBtn.dataset.proposalId);
    }
    const agentTaskBtn = event.target.closest(".agent-task-item");
    if (agentTaskBtn) {
      const threadId = agentTaskBtn.dataset.threadId;
      if (threadId) {
        const threadData = await loadAgentThread(threadId);
        const runId = threadData?.thread?.current_run_id || agentTaskBtn.dataset.runId;
        if (runId) {
          const data = await api(`/api/agent/runs/${runId}`);
          renderAgentRun(data);
          if (data.run?.status === "running") startAgentPolling(runId);
        }
        return;
      }
      const runId = agentTaskBtn.dataset.runId;
      if (runId) {
        const data = await api(`/api/agent/runs/${runId}`);
        renderAgentRun(data);
        if (data.run?.status === "running") startAgentPolling(runId);
      }
    }
  });
  $("#refreshBtn").addEventListener("click", () => reloadAll().then(() => toast("已刷新")));
  $("#refreshGovernanceBtn").addEventListener("click", () => loadGovernance().then(() => toast("治理队列已刷新")));
  $("#refreshCollabBtn").addEventListener("click", () => loadCollaboration().then(() => toast("协作方案已刷新")));
  $("#refreshCommercialBtn").addEventListener("click", () => loadCommercial().then(() => toast("商业档案队列已刷新")));
  $("#refreshDataSourcesBtn").addEventListener("click", () => loadDataSources().then(() => toast("数据源状态已刷新")));
  $("#refreshOrganizationBtn")?.addEventListener("click", () => loadOrganization().then(() => toast("组织数据已刷新")));
  $("#refreshAgentTasksBtn")?.addEventListener("click", () => loadAgentTasks().then(() => toast("Agent 任务已刷新")));
  $("#refreshHistoryBtn")?.addEventListener("click", () => loadWorkspaceHistory().then(() => toast("历史资产已刷新")));
  document.addEventListener("click", (event) => {
    const filter = event.target.closest(".history-filter");
    if (!filter) return;
    state.historyFilter = filter.dataset.historyType || "all";
    renderWorkspaceHistory();
  });
  $("#agentNewThreadBtn")?.addEventListener("click", () => {
    stopAgentPolling();
    stopOpenClawPolling();
    state.activeAgentThread = null;
    state.activeAgentRun = null;
    state.activeAgentArtifacts = [];
    state.agentRuntimeComparison = null;
    state.activeOpenClawRun = null;
    state.activeOpenClawSessionId = "";
    state.openClawConversation = [];
    state.activeOpenClawCampaignTarget = null;
    ensureOpenClawSession();
    renderAgentTasks();
    renderAgentRun({ events: [], artifacts: [], run: {}, task: {} });
    renderAgentRuntimeComparison();
    renderAgentOpenClawStatus();
    renderAgentFloatDock();
    toast("已准备新 Agent 会话");
  });
  $("#refreshKnowledgeBtn")?.addEventListener("click", () => loadKnowledge().then(() => toast("知识库已刷新")));
  $("#knowledgeForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formToObject(form);
    if (!payload.title || !payload.content) {
      toast("请填写标题和正文", true);
      return;
    }
    try {
      await api("/api/knowledge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      form.reset();
      await loadKnowledge();
      toast("知识已写入");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#knowledgeSearchForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    payload.top_k = Number(payload.top_k || 5);
    try {
      const data = await api("/api/knowledge/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      state.knowledgeSearchResults = data.items || [];
      renderKnowledgeSearchResults();
      toast(`检索到 ${state.knowledgeSearchResults.length} 条知识`);
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#reloadOpenClawConfigBtn")?.addEventListener("click", async () => {
    try {
      state.openClaw = await api("/api/openclaw/config");
      state.openClawDiagnostics = await api("/api/openclaw/diagnostics");
      renderOpenClawAdmin();
      toast("OpenClaw 配置已重新加载");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#saveOpenClawConfigBtn")?.addEventListener("click", async () => {
    const form = $("#openClawConfigForm");
    if (!form) return;
    const payload = formToObject(form);
    payload.enabled = Boolean(form.elements.enabled.checked);
    try {
      const data = await api("/api/openclaw/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      state.openClaw = { ...(state.openClaw || {}), ...data };
      state.openClaw = await api("/api/openclaw/config");
      state.openClawDiagnostics = await api("/api/openclaw/diagnostics");
      renderOpenClawAdmin();
      renderAgentRuntimeControls();
      toast("OpenClaw 配置已保存");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#openClawBindingForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    try {
      await api("/api/openclaw/bindings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      state.openClaw = await api("/api/openclaw/config");
      state.openClawDiagnostics = await api("/api/openclaw/diagnostics");
      renderOpenClawAdmin();
      toast("员工 OpenClaw Agent 已绑定");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#agentChatForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const button = $("#agentRunBtn");
    try {
      if (button) {
        button.disabled = true;
        button.textContent = "执行中...";
      }
      if (payload.runtime === "openclaw") {
        await runOpenClawFromPayload(payload);
      } else {
        await runAgentFromPayload(payload);
      }
      toast("Agent 已启动，执行过程会实时刷新");
    } catch (error) {
      toast(error.message, true);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "启动 Agent";
      }
    }
  });
  $("#agentFloatToggle")?.addEventListener("click", (event) => {
    if (event.currentTarget.dataset.suppressClick === "1") {
      delete event.currentTarget.dataset.suppressClick;
      return;
    }
    setAgentFloatOpen(!state.agentFloatOpen);
  });
  $("#agentFloatCloseBtn")?.addEventListener("click", () => setAgentFloatOpen(false));
  $("#openAgentFloatFromWorkspaceBtn")?.addEventListener("click", () => setAgentFloatOpen(true));
  initAgentFloatFrameControls();
  $("#agentFloatNewTaskBtn")?.addEventListener("click", async () => {
    try {
      stopOpenClawPolling();
      state.activeOpenClawRun = null;
      state.activeOpenClawSessionId = "";
      state.openClawConversation = [];
      state.activeOpenClawCampaignTarget = null;
      state.activeAgentImportPreview = null;
      const session = ensureOpenClawSession();
      if (activeFloatRuntime() === "openclaw") {
        const data = await api("/api/openclaw/sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        if (data.session) {
          const serverSession = normalizeOpenClawSession(data.session);
          if (serverSession) {
            state.activeOpenClawSessionId = serverSession.id;
            state.openClawSessions = [serverSession, ...state.openClawSessions.filter((item) => item.id !== session.id && item.id !== serverSession.id)].slice(0, 20);
          }
        }
        session.openclawSessionId = data.session?.openclaw_session_id || session.openclawSessionId || "";
        syncActiveOpenClawSession({ status: "ready", openclawSessionId: session.openclawSessionId });
      }
      renderAgentFloatDock();
      toast("已准备新的 OpenClaw 任务");
    } catch (error) {
      toast(error.message || "创建 OpenClaw 会话失败", true);
    }
  });
  $("#agentFloatSaveCampaignBtn")?.addEventListener("click", async () => {
    try {
      await saveActiveOpenClawRunToCampaign("#agentFloatForm");
      toast("OpenClaw 任务已保存到 Campaign");
    } catch (error) {
      toast(error.message || "保存 Campaign 失败", true);
    }
  });
  $("#agentFloatViewAssetsBtn")?.addEventListener("click", async () => {
    await viewActiveOpenClawAssets();
  });
  document.addEventListener("click", async (event) => {
    const saveBtn = event.target.closest("#agentSaveOpenClawCampaignBtn");
    if (saveBtn) {
      try {
        saveBtn.disabled = true;
        await saveActiveOpenClawRunToCampaign("#agentChatForm");
        toast("OpenClaw 任务已保存到 Campaign");
      } catch (error) {
        toast(error.message || "保存 Campaign 失败", true);
      } finally {
        saveBtn.disabled = false;
      }
      return;
    }
    const viewBtn = event.target.closest("#agentViewOpenClawAssetsBtn");
    if (viewBtn) {
      await viewActiveOpenClawAssets();
    }
  });
  $("#agentFloatOpenFullBtn")?.addEventListener("click", () => {
    setAgentFloatOpen(false);
    setView("agentWorkspace");
  });
  $("#agentFloatOpenNativeBtn")?.addEventListener("click", () => {
    openNativeOpenClawOrWorkspace();
  });
  $("#openNativeOpenClawFromWorkspaceBtn")?.addEventListener("click", () => {
    openNativeOpenClawOrWorkspace();
  });
  $("#agentFloatForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formToObject(form);
    const fileInput = form.elements.file;
    const file = fileInput?.files?.[0] || null;
    delete payload.file;
    const button = $("#agentFloatRunBtn");
    try {
      if (!String(payload.message || "").trim() && !file) {
        toast("请输入消息或上传 KOL 表格", true);
        return;
      }
      if (button) {
        button.disabled = true;
        button.textContent = file ? "解析中..." : "发送中...";
      }
      if (file) {
        await previewAgentCreatorImport(file, String(payload.message || "").trim());
        if (fileInput) fileInput.value = "";
        const fileNameNode = $("#agentFloatFileName");
        if (fileNameNode) fileNameNode.textContent = "未选择文件";
      } else if (payload.runtime === "openclaw") {
        await runOpenClawFromPayload(payload);
      } else {
        await runAgentFromPayload(payload);
      }
      renderAgentFloatDock();
      toast(file ? "已生成导入预览" : "Agent 已在浮窗启动");
    } catch (error) {
      toast(error.message, true);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "发送";
      }
    }
  });
  $("#agentFloatFileInput")?.addEventListener("change", (event) => {
    const file = event.currentTarget.files?.[0];
    const fileNameNode = $("#agentFloatFileName");
    if (fileNameNode) fileNameNode.textContent = file ? file.name : "未选择文件";
  });
  $("#agentFloatRuntimeSelect")?.addEventListener("change", () => renderAgentFloatContent());
  $("#agentFloatPanel")?.addEventListener("click", async (event) => {
    const sessionBtn = event.target.closest("[data-openclaw-session]");
    if (sessionBtn) {
      activateOpenClawSession(sessionBtn.dataset.openclawSession || "").catch((error) => toast(error.message || "加载 OpenClaw session 失败", true));
      return;
    }
    const commitBtn = event.target.closest("[data-agent-import-commit]");
    if (commitBtn) {
      commitBtn.disabled = true;
      commitBtn.textContent = "导入中...";
      commitAgentCreatorImport(commitBtn.dataset.agentImportCommit || "").then(
        (data) => toast(`已导入 ${fmtNumber(data.imported || 0)} 个达人`),
        (error) => toast(error.message || "导入失败", true)
      );
      return;
    }
    const openClawAction = event.target.closest("[data-agent-openclaw-action]");
    if (openClawAction) {
      const action = openClawAction.dataset.agentOpenclawAction || "";
      try {
        openClawAction.disabled = true;
        if (action === "save-campaign") {
          await saveActiveOpenClawRunToCampaign("#agentFloatForm");
          toast("OpenClaw 任务已保存到 Campaign");
        } else if (action === "view-assets") {
          await viewActiveOpenClawAssets();
        }
      } catch (error) {
        toast(error.message || "操作失败", true);
      } finally {
        openClawAction.disabled = false;
      }
      return;
    }
    const prompt = event.target.closest("[data-agent-prompt]");
    if (!prompt) return;
    const textarea = $("#agentFloatForm textarea[name='message']");
    if (textarea) {
      textarea.value = prompt.dataset.agentPrompt || "";
      textarea.focus();
    }
  });
  $("#agentCompareRuntimeBtn")?.addEventListener("click", async (event) => {
    const form = $("#agentChatForm");
    if (!form) return;
    const payload = formToObject(form);
    const button = event.currentTarget;
    try {
      button.disabled = true;
      button.textContent = "对比中...";
      const data = await api("/api/agent/chat/compare-runtimes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, runtime_a: "custom", runtime_b: "openai_agents", require_plan_approval: false }),
      });
      state.agentRuntimeComparison = data;
      state.activeAgentRun = data.runtime_b;
      state.activeAgentArtifacts = data.runtime_b?.artifacts || [];
      renderAgentRun(data.runtime_b);
      renderAgentRuntimeComparison();
      await loadAgentTasks();
      toast("Runtime A/B 对比已完成");
    } catch (error) {
      toast(error.message, true);
    } finally {
      button.disabled = false;
      button.textContent = "A/B 对比";
    }
  });
  $("#agentApproveBtn")?.addEventListener("click", async (event) => {
    const runId = event.currentTarget.dataset.runId;
    if (!runId) return;
    const data = await api(`/api/agent/runs/${runId}/approve`, { method: "POST" });
    renderAgentRun(data);
    await loadAgentTasks();
    toast("已确认 Agent 产物");
  });
  $("#agentApprovePlanBtn")?.addEventListener("click", async (event) => {
    const runId = event.currentTarget.dataset.runId;
    if (!runId) return;
    const topN = Number($("#agentChatForm")?.elements?.top_n?.value || 8);
    const runtime = $("#agentRuntimeSelect")?.value || "auto";
    const data = await api(`/api/agent/runs/${runId}/approve-plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ top_n: topN, runtime }),
    });
    renderAgentRun(data);
    await loadAgentTasks();
    toast("计划已确认，Agent 已继续执行");
  });
  $("#agentCancelRunBtn")?.addEventListener("click", async (event) => {
    const runId = event.currentTarget.dataset.runId;
    if (!runId) return;
    const data = await api(`/api/agent/runs/${runId}/cancel`, { method: "POST" });
    renderAgentRun(data);
    await loadAgentTasks();
    toast("Run 已取消");
  });
  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".agent-step-action");
    if (!button) return;
    const stepId = button.dataset.stepId;
    const action = button.dataset.action;
    if (!stepId || !action) return;
    const payload = {};
    if (action === "edit") {
      const input = window.prompt("编辑这一步的输入摘要", "");
      if (input === null) return;
      payload.input_summary = input;
    }
    try {
      button.disabled = true;
      const data = await api(`/api/agent/steps/${encodeURIComponent(stepId)}/${encodeURIComponent(action)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      renderAgentRun(data);
      await loadAgentTasks();
      toast(action === "retry" ? "Step 已重试" : action === "skip" ? "Step 已跳过" : "Step 输入已更新");
    } catch (error) {
      toast(error.message, true);
    } finally {
      button.disabled = false;
    }
  });
  $("#agentCopyBriefBtn")?.addEventListener("click", (event) => {
    const brief = event.currentTarget.dataset.brief || "";
    const form = $("#agentChatForm");
    if (form?.elements?.message) form.elements.message.value = brief;
    toast("Brief 已复制到输入框");
  });
  $("#agentClarificationForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const runId = form.dataset.runId;
    if (!runId) return;
    const payload = formToObject(form);
    const runtime = $("#agentRuntimeSelect")?.value || "auto";
    const data = await api(`/api/agent/runs/${runId}/clarification`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ supplement: payload.supplement, top_n: Number(payload.top_n || 8), runtime }),
    });
    form.reset();
    renderAgentRun(data);
    await loadAgentTasks();
    toast("已补充信息并继续执行");
  });
  $("#internalUserForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    payload.user_type = "internal";
    try {
      await api("/api/auth/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      event.currentTarget.reset();
      await loadOrganization();
      toast("内部账号已创建");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#clientAccountForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    try {
      await api("/api/auth/clients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      event.currentTarget.reset();
      await loadOrganization();
      toast("客户已创建");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#clientUserForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const clientId = payload.client_id;
    delete payload.client_id;
    if (!clientId) {
      toast("请先选择客户", true);
      return;
    }
    try {
      await api(`/api/auth/clients/${clientId}/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      event.currentTarget.reset();
      await loadOrganization();
      toast("甲方账号已创建");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#projectAccessForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formToObject(form);
    payload.permissions = [];
    if (form.elements.permission_view?.checked) payload.permissions.push("view");
    if (form.elements.permission_comment?.checked) payload.permissions.push("comment");
    delete payload.permission_view;
    delete payload.permission_comment;
    if (!payload.permissions.length) payload.permissions = ["view"];
    try {
      await api("/api/auth/project-access", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      await loadOrganization();
      toast("项目授权已保存");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#reloadRuleConfigBtn")?.addEventListener("click", async () => {
    try {
      await loadRuleConfig();
      toast("规则配置已重新加载");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#saveRuleConfigBtn")?.addEventListener("click", async () => {
    const editor = $("#ruleConfigEditor");
    if (!editor) return;
    let payload;
    try {
      payload = JSON.parse(editor.value || "{}");
    } catch (error) {
      toast("规则 JSON 格式不正确", true);
      return;
    }
    try {
      const data = await api("/api/rules/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      state.ruleConfig = data.config || null;
      renderRuleConfig();
      toast("规则已保存，新的 Agent 运行会读取这版配置");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#resetRuleConfigBtn")?.addEventListener("click", async () => {
    if (!window.confirm("确认恢复默认规则？当前编辑内容会被覆盖。")) return;
    try {
      const data = await api("/api/rules/config/reset", { method: "POST" });
      state.ruleConfig = data.config || null;
      renderRuleConfig();
      toast("规则已恢复默认");
    } catch (error) {
      toast(error.message, true);
    }
  });
  $("#organization")?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-auth-action]");
    if (!button) return;
    const action = button.dataset.authAction;
    const userId = button.dataset.userId;
    if (!action || !userId) return;
    try {
      button.disabled = true;
      if (action === "toggle-user") {
        const nextStatus = button.dataset.nextStatus || "disabled";
        await api(`/api/auth/users/${encodeURIComponent(userId)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: nextStatus }),
        });
        await loadOrganization();
        toast(nextStatus === "active" ? "账号已启用" : "账号已禁用");
      }
      if (action === "reset-password") {
        const password = window.prompt("输入新密码，至少 8 位");
        if (password === null) return;
        if (password.length < 8) {
          toast("密码至少 8 位", true);
          return;
        }
        await api(`/api/auth/users/${encodeURIComponent(userId)}/reset-password`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password }),
        });
        toast("密码已重置");
      }
    } catch (error) {
      toast(error.message, true);
    } finally {
      button.disabled = false;
    }
  });
  $("#generateSocialReportBtn").addEventListener("click", async () => {
    const payload = formToObject($("#socialReportForm"));
    const data = await api("/api/symbolic-os/social-reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.symbolicOS = data.snapshot;
    renderSymbolicOS(data.snapshot);
    toast("社会符号网络报告已生成");
  });
  $("#addSignifierTagBtn").addEventListener("click", async () => {
    const payload = formToObject($("#signifierTagForm"));
    if (!payload.name) {
      toast("请先填写标签名称", true);
      return;
    }
    const data = await api("/api/symbolic-os/signifier-tags", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.symbolicOS = data.snapshot;
    renderSymbolicOS(data.snapshot);
    $("#signifierTagForm").reset();
    toast("能指标签已保存");
  });
  $("#generateProductSymbolicBtn").addEventListener("click", async () => {
    const payload = formToObject($("#productSymbolicForm"));
    if (state.lastBrand) {
      payload.brand_id = state.lastBrand.brand_id;
      payload.brand_name = payload.brand_name || state.lastBrand.brand_name;
    }
    const data = await api("/api/symbolic-os/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.symbolicOS = data.snapshot;
    renderSymbolicOS(data.snapshot);
    if (state.lastBrand && state.lastSymbolicResults.length) await renderSymbolicGraphFromState();
    toast("产品符号档案已生成");
  });
  $("#creatorSearch").addEventListener("input", renderCreators);
  bindCreatorCardClicks($("#creatorList"));
  bindCreatorCardClicks($("#creatorFilterList"));
  renderCreatorFilterTagFramework();
  renderCreatorFilterPresetSelect();
  renderCreatorFilterStepper();
  setCreatorFilterStep(1);
  $("#creatorFilterForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    setCreatorFilterStep(3);
    renderCreatorFilterResults();
  });
  $("#creatorFilterForm")?.addEventListener("input", renderCreatorFilterResults);
  $("#creatorFilterForm")?.addEventListener("click", (event) => {
    const nextBtn = event.target.closest(".creator-filter-next-btn");
    if (nextBtn) {
      event.preventDefault();
      setCreatorFilterStep(nextBtn.dataset.filterStep);
      renderCreatorFilterResults();
      return;
    }
    const prevBtn = event.target.closest(".creator-filter-prev-btn");
    if (prevBtn) {
      event.preventDefault();
      setCreatorFilterStep(prevBtn.dataset.filterStep);
      return;
    }
    const tab = event.target.closest(".creator-filter-step-tab, .creator-filter-funnel-node");
    if (tab?.dataset.filterStep) {
      event.preventDefault();
      const step = Number(tab.dataset.filterStep);
      if (step >= 1 && step <= 3) setCreatorFilterStep(step);
    }
  });
  $("#creatorFilterTagFramework")?.addEventListener("click", (event) => {
    const chip = event.target.closest(".creator-filter-tag-chip");
    if (!chip) return;
    event.preventDefault();
    toggleCreatorFilterTag(chip.dataset.filterGroup, chip.dataset.filterTag);
  });
  $("#creatorFilterTagFrameworkExtra")?.addEventListener("click", (event) => {
    const chip = event.target.closest(".creator-filter-tag-chip");
    if (!chip) return;
    event.preventDefault();
    toggleCreatorFilterTag(chip.dataset.filterGroup, chip.dataset.filterTag);
  });
  $("#creatorFilterNarrativeAnalyzeBtn")?.addEventListener("click", () => runCreatorFilterNarrativeAnalyze());
  $("#creatorFilterBriefFile")?.addEventListener("change", async (event) => {
    const text = await readCreatorFilterUploadFile(event.currentTarget);
    if (!text) return;
    const node = $("#creatorFilterNarrativeBrief");
    if (node) node.value = text;
    toast("Brief 文件已载入");
  });
  $("#creatorFilterTagsFile")?.addEventListener("change", async (event) => {
    const text = await readCreatorFilterUploadFile(event.currentTarget);
    if (!text) return;
    const node = $("#creatorFilterTextTags");
    if (node) node.value = text;
    toast("标签文件已载入");
  });
  $("#creatorFilterList")?.addEventListener("change", (event) => {
    const checkbox = event.target.closest(".creator-filter-select");
    if (!checkbox) return;
    event.stopPropagation();
    setCreatorFilterSelected(checkbox.dataset.creatorId, checkbox.checked);
  });
  $("#creatorFilterList")?.addEventListener("click", (event) => {
    if (event.target.closest(".creator-filter-select-wrap, .creator-filter-select")) {
      event.stopPropagation();
    }
  });
  $("#creatorFilterSelectAll")?.addEventListener("change", (event) => {
    const criteria = getCreatorFilterCriteria();
    const items = state.creators.filter((creator) => creatorMatchesFilter(creator, criteria));
    items.forEach((creator) => setCreatorFilterSelected(creator.creator_id, event.currentTarget.checked));
    renderCreatorFilterResults();
  });
  $("#creatorFilterExportBtn")?.addEventListener("click", exportSelectedCreatorFilterList);
  $("#creatorFilterSettlementBtn")?.addEventListener("click", () => openSettlementWizard());
  $("#creatorFilterDeliverablesBtn")?.addEventListener("click", async () => {
    const brief = getCreatorFilterNarrativeBriefText() || $("#creatorFilterBriefInput")?.value || "";
    if (!state.creatorFilterDeliverables?.markdown && brief) {
      await loadCreatorFilterDeliverables(brief);
    }
    downloadDeliverablesMarkdown();
  });
  $("#creatorFilterTwoStagePresetBtn")?.addEventListener("click", applyTwoStagePropagationPreset);
  $("#creatorFilterResetBtn")?.addEventListener("click", () => {
    $("#creatorFilterForm")?.reset();
    clearCreatorFilterTags();
    $("#creatorFilterBriefInput") && ($("#creatorFilterBriefInput").value = "");
    $("#creatorFilterNarrativeBrief") && ($("#creatorFilterNarrativeBrief").value = "");
    $("#creatorFilterTextTags") && ($("#creatorFilterTextTags").value = "");
    $("#creatorFilterBriefHints")?.classList.add("hidden");
    renderCreatorFilterNarrativeAnalysis(null);
    state.creatorFilterNarrativeAnalysis = null;
    state.creatorFilterBusinessType = null;
    renderCreatorFilterBusinessType(null);
    state.creatorFilterDeliverables = null;
    renderCreatorFilterDeliverables(null);
    state.creatorFilterSelected = {};
    state.creatorFilterRecommendations = {};
    setCreatorFilterStep(1);
    renderCreatorFilterResults();
  });
  $("#creatorFilterBriefApplyBtn")?.addEventListener("click", async () => {
    const text = $("#creatorFilterBriefInput")?.value || "";
    await applyCreatorFilterFromBriefText(text);
  });
  $("#creatorFilterPresetSaveBtn")?.addEventListener("click", saveCreatorFilterPreset);
  $("#creatorFilterPresetLoadBtn")?.addEventListener("click", loadSelectedCreatorFilterPreset);
  $("#creatorFilterPresetDeleteBtn")?.addEventListener("click", deleteSelectedCreatorFilterPreset);
  $("#caseSearch")?.addEventListener("input", renderCases);
  $("#openCaseModalBtn")?.addEventListener("click", () => openCaseModal());
  $("#openSettlementWizardBtn")?.addEventListener("click", async () => {
    await ensureCreatorsLoaded().catch(() => {});
    openSettlementWizard();
  });
  $("#closeSettlementWizardBtn")?.addEventListener("click", closeSettlementWizard);
  $("#settlementWizardForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector("button[type='submit']");
    if (button) button.disabled = true;
    try {
      await submitSettlementWizard(event.currentTarget);
    } catch (error) {
      toast(error.message || "结算回写失败", true);
    } finally {
      if (button) button.disabled = false;
    }
  });
  bindModalDismiss($("#settlementWizardModal"), "[data-close-settlement-wizard]", closeSettlementWizard);
  $("#closeCaseModalBtn")?.addEventListener("click", closeCaseModal);
  $("#deleteCaseBtn")?.addEventListener("click", deleteActiveCase);
  $("#caseForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector("button[type='submit']");
    if (button) button.disabled = true;
    try {
      await saveCaseForm(event.currentTarget);
    } catch (error) {
      toast(error.message || "保存案例失败", true);
    } finally {
      if (button) button.disabled = false;
    }
  });
  $("#caseList")?.addEventListener("click", async (event) => {
    const caseButton = event.target.closest(".open-case-btn");
    if (caseButton) {
      const caseItem = state.cases.find((item) => item.case_id === caseButton.dataset.caseId);
      if (caseItem) openCaseModal(caseItem);
      return;
    }
    const creatorButton = event.target.closest(".open-creator-from-case-btn");
    if (creatorButton) {
      await openCreatorModal(creatorButton.dataset.creatorId);
      setView("creators");
    }
  });
  $("#downloadProposalBtn").addEventListener("click", downloadProposal);
  $("#closeCreatorModalBtn").addEventListener("click", closeCreatorModal);
  $("#deleteCreatorBtn")?.addEventListener("click", deleteActiveCreator);
  $("#generateCreatorKitBtn")?.addEventListener("click", () => generateCreatorCommercialKit($("#creatorEditForm")));
  $("#openCreatorKitWebBtn")?.addEventListener("click", () => openCreatorCommercialKitWeb(state.activeCreator?.creator_id));
  $("#copyCreatorKitBtn")?.addEventListener("click", async () => {
    const output = $("#creatorCommercialKitOutput");
    const text = output?.dataset.copyText || generateCreatorCommercialKit($("#creatorEditForm"));
    if (!text) return;
    await copyText(text);
    toast("商业名片刊例已复制");
  });
  $("#downloadCreatorKitBtn")?.addEventListener("click", () => downloadCreatorCommercialKit($("#creatorEditForm")));
  $("#generateQuickCreatorKitBtn")?.addEventListener("click", () => generateCreatorCommercialKit($("#quickCreatorForm")));
  $("#copyQuickCreatorKitBtn")?.addEventListener("click", async () => {
    const output = $("#quickCreatorCommercialKitOutput");
    const text = output?.dataset.copyText || generateCreatorCommercialKit($("#quickCreatorForm"));
    if (!text) return;
    await copyText(text);
    toast("商业名片刊例已复制");
  });
  $("#downloadQuickCreatorKitBtn")?.addEventListener("click", () => downloadCreatorCommercialKit($("#quickCreatorForm")));
  $("#runQuickCreatorAiBtn")?.addEventListener("click", () => runCreatorFormAiJudgment($("#quickCreatorForm")));
  $("#runCreatorAiBtn")?.addEventListener("click", () => runCreatorFormAiJudgment($("#creatorEditForm")));
  $("#quickCreatorImageAnalyzeBtn")?.addEventListener("click", analyzeQuickCreatorImage);
  $("#quickCreatorImageApplyBtn")?.addEventListener("click", () =>
    applyCreatorImageSuggestion($("#quickCreatorForm"), { stateKey: "quickCreatorImageSuggestion" }),
  );
  $("#openQuickCreatorBtn")?.addEventListener("click", openQuickCreatorModal);
  $("#closeQuickCreatorBtn")?.addEventListener("click", closeQuickCreatorModal);
  $("#closeArtifactModalBtn")?.addEventListener("click", closeArtifactModal);
  bindModalDismiss($("#creatorModal"), "[data-close-modal]", closeCreatorModal);
  bindCreatorTagEditorEvents($("#quickCreatorModal"));
  bindCreatorTagEditorEvents($("#creatorModal"));
  bindCreatorTagHubEvents(document);
  bindCreatorDataCardEvents($("#creatorEditForm"));
  bindCreatorDataCardEvents($("#quickCreatorForm"));
  bindCommercialCasesEditor($("#creatorEditForm"));
  bindCommercialCasesEditor($("#quickCreatorForm"));
  bindModalDismiss($("#quickCreatorModal"), "[data-close-quick-creator]", closeQuickCreatorModal);
  bindModalDismiss($("#caseModal"), "[data-close-case-modal]", closeCaseModal);
  bindModalDismiss($("#artifactModal"), "[data-close-artifact-modal]", closeArtifactModal);
  bindModalEscape([
    ["#creatorModal", closeCreatorModal],
    ["#quickCreatorModal", closeQuickCreatorModal],
    ["#caseModal", closeCaseModal],
    ["#artifactModal", closeArtifactModal],
  ]);
  $("#quickCreatorAvatarInput")?.addEventListener("change", async (event) => {
    const file = event.currentTarget.files?.[0];
    if (!file) return;
    try {
      await setQuickCreatorAvatar(file, $("#quickCreatorForm"));
      toast("头像已载入，保存后进入达人档案");
    } catch (error) {
      toast(error.message || "头像上传失败", true);
    }
  });
  $("#creatorEditAvatarInput")?.addEventListener("change", async (event) => {
    const file = event.currentTarget.files?.[0];
    if (!file) return;
    try {
      await setCreatorFormAvatar(file, $("#creatorEditForm"), "creatorEditAvatarPreview");
      toast("头像已更新，保存后生效");
    } catch (error) {
      toast(error.message || "头像上传失败", true);
    }
  });
  $("#creatorEditForm")?.addEventListener("change", (event) => {
    const form = event.currentTarget;
    if (event.target.name === "platform") {
      const preserved = readCreatorRateValues(form).values;
      renderCreatorRateFields(form, $("#creatorEditRateFields"), preserved);
      syncCreatorDataCardPanel(form);
      return;
    }
    if (["follower_count", "total_likes"].includes(event.target.name)) {
      syncCreatorDataCardPanel(form);
    }
    if (event.target.name === "avatar_url_display") {
      const url = String(event.target.value || "").trim();
      form.elements.avatar_url.value = url;
      syncCreatorAvatarPreview(form, url);
    }
  });
  $("#quickCreatorForm")?.addEventListener("input", (event) => {
    const form = event.currentTarget;
    if (["follower_count", "total_likes"].includes(event.target.name)) {
      syncCreatorDataCardPanel(form);
    }
    if (form.id !== "quickCreatorForm") return;
    if (["name", "platform", "bio", "follower_count", "listed_price"].includes(event.target.name)) {
      refreshCreatorCommercialKitPreview(form);
    }
  });
  $("#quickCreatorForm")?.addEventListener("change", (event) => {
    const form = event.currentTarget;
    if (event.target.name === "platform") {
      const preserved = readCreatorRateValues(form).values;
      renderCreatorRateFields(form, $("#quickCreatorRateFields"), preserved);
      syncCreatorDataCardPanel(form);
      refreshCreatorCommercialKitPreview(form);
      return;
    }
    if (["follower_count", "total_likes"].includes(event.target.name)) {
      syncCreatorDataCardPanel(form);
    }
    if (event.target.name === "avatar_url_display") {
      const url = String(event.target.value || "").trim();
      form.elements.avatar_url.value = url;
      syncCreatorAvatarPreview(form, url, "quickCreatorAvatarPreview");
    }
  });
  $("#quickCreatorForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector("button[type='submit']");
    if (button) {
      button.disabled = true;
      button.textContent = "保存中...";
    }
    try {
      await saveManualCreator(event.currentTarget, { openDetail: true });
      closeQuickCreatorModal();
    } catch (error) {
      toast(error.message || "保存达人失败", true);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "保存并打开档案";
      }
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".data-source-test-btn");
    if (!button) return;
    const data = await api("/api/settings/data-sources/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_id: button.dataset.sourceId }),
    });
    $("#dataSourceTestOutput").textContent = JSON.stringify(data, null, 2);
    toast(data.ok ? "连接测试通过" : "连接测试未通过", !data.ok);
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".open-proposal-btn");
    if (!button) return;
    await openCollaborationProposal(button.dataset.proposalId);
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".copy-token-btn");
    if (!button) return;
    const input = $(button.dataset.target);
    if (input) input.value = button.dataset.token || "";
    toast("token 已填入");
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".open-distribution-btn");
    if (!button) return;
    await openDistribution(button.dataset.briefId);
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".open-platform-campaign-btn");
    if (!button) return;
    await openCampaignRoom(button.dataset.campaignId);
    setView("platformOS");
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".open-history-item-btn");
    if (!button) return;
    await openHistoryItem(button.dataset.historyType, button.dataset.historyId);
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".open-knowledge-doc-btn");
    if (!button) return;
    const data = await api(`/api/knowledge/${button.dataset.documentId}`);
    renderKnowledgeDetail(data);
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".commit-memory-btn");
    if (!button) return;
    const artifactId = button.dataset.artifactId;
    const suggestionIndex = Number(button.dataset.suggestionIndex || 0);
    const title = $(`.memory-edit-title[data-artifact-id="${artifactId}"][data-suggestion-index="${suggestionIndex}"]`)?.value || "";
    const content = $(`.memory-edit-content[data-artifact-id="${artifactId}"][data-suggestion-index="${suggestionIndex}"]`)?.value || "";
    const tags = $(`.memory-edit-tags[data-artifact-id="${artifactId}"][data-suggestion-index="${suggestionIndex}"]`)?.value || "";
    try {
      await api(`/api/agent/artifacts/${artifactId}/knowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          suggestion_index: suggestionIndex,
          override: { title, content, tags },
        }),
      });
      if (state.activeAgentRun?.run?.run_id) {
        const data = await api(`/api/agent/runs/${state.activeAgentRun.run.run_id}`);
        renderAgentRun(data);
      }
      await loadKnowledge();
      toast("记忆已写入知识库");
    } catch (error) {
      toast(error.message, true);
    }
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".open-artifact-detail-btn");
    if (!button) return;
    openArtifactModal(button.dataset.artifactId);
  });

  document.addEventListener("click", (event) => {
    const node = event.target.closest("#agentReasoningGraphCanvas [data-agent-node-id]");
    if (!node) return;
    state.activeAgentGraphNodeId = node.dataset.agentNodeId || "";
    renderAgentReasoningGraph();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const node = event.target.closest?.("#agentReasoningGraphCanvas [data-agent-node-id]");
    if (!node) return;
    event.preventDefault();
    state.activeAgentGraphNodeId = node.dataset.agentNodeId || "";
    renderAgentReasoningGraph();
  });

  document.addEventListener("click", (event) => {
    const node = event.target.closest("#projectRunGraphCanvas .graph-node");
    if (!node || !state.projectRun?.graph) return;
    if (state.projectRunGraphDrag?.moved) {
      state.projectRunGraphDrag = null;
      return;
    }
    state.projectRunSelectedNodeId = node.dataset.nodeId || "";
    state.projectRunStageFilter = "";
    renderSymbolicGraphInto("#projectRunGraphCanvas", state.projectRun.graph);
    renderProjectRunStageLegend(state.projectRun.graph);
    renderProjectRunNodeInspector();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const node = event.target.closest?.("#projectRunGraphCanvas .graph-node");
    if (!node || !state.projectRun?.graph) return;
    event.preventDefault();
    state.projectRunSelectedNodeId = node.dataset.nodeId || "";
    state.projectRunStageFilter = "";
    renderSymbolicGraphInto("#projectRunGraphCanvas", state.projectRun.graph);
    renderProjectRunStageLegend(state.projectRun.graph);
    renderProjectRunNodeInspector();
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("#projectRunStageLegend .stage-pill");
    if (!button || !state.projectRun?.graph) return;
    const stage = button.dataset.stage || "";
    state.projectRunStageFilter = state.projectRunStageFilter === stage ? "" : stage;
    const firstNode = (state.projectRun.graph.nodes || []).find((node) => node.stage === state.projectRunStageFilter);
    if (firstNode) state.projectRunSelectedNodeId = firstNode.id;
    renderProjectRunStageLegend(state.projectRun.graph);
    renderSymbolicGraphInto("#projectRunGraphCanvas", state.projectRun.graph);
    renderProjectRunNodeInspector();
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-project-graph-zoom]");
    if (!button || !state.projectRun?.graph) return;
    const action = button.dataset.projectGraphZoom;
    if (action === "fit") {
      state.projectRunGraphAutoFit = true;
      renderSymbolicGraphInto("#projectRunGraphCanvas", state.projectRun.graph);
      return;
    } else {
      const delta = action === "in" ? 0.12 : -0.12;
      zoomProjectRunGraph((state.projectRunGraphScale || 1) + delta);
    }
  });

  $("#projectRunGraphCanvas")?.addEventListener(
    "wheel",
    (event) => {
      if (!state.projectRun?.graph) return;
      event.preventDefault();
      const canvas = event.currentTarget;
      const rect = canvas.getBoundingClientRect();
      const anchor = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      const direction = event.deltaY > 0 ? -1 : 1;
      const speed = event.ctrlKey || event.metaKey ? 0.16 : 0.1;
      const nextScale = (state.projectRunGraphScale || 1) * (1 + direction * speed);
      zoomProjectRunGraph(nextScale, anchor);
    },
    { passive: false }
  );

  $("#projectRunGraphCanvas")?.addEventListener("dblclick", () => {
    if (!state.projectRun?.graph) return;
    state.projectRunGraphAutoFit = true;
    renderSymbolicGraphInto("#projectRunGraphCanvas", state.projectRun.graph);
  });

  $("#projectRunGraphCanvas")?.addEventListener("pointerdown", (event) => {
    if (!state.projectRun?.graph) return;
    if (event.button !== 0) return;
    const canvas = event.currentTarget;
    state.projectRunGraphDrag = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      scrollLeft: canvas.scrollLeft,
      scrollTop: canvas.scrollTop,
      moved: false,
    };
    canvas.classList.add("dragging");
    canvas.setPointerCapture?.(event.pointerId);
  });

  $("#projectRunGraphCanvas")?.addEventListener("pointermove", (event) => {
    const drag = state.projectRunGraphDrag;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const canvas = event.currentTarget;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
    canvas.scrollLeft = drag.scrollLeft - dx;
    canvas.scrollTop = drag.scrollTop - dy;
  });

  const endProjectGraphDrag = (event) => {
    const drag = state.projectRunGraphDrag;
    const canvas = $("#projectRunGraphCanvas");
    if (!drag) return;
    if (event?.pointerId && drag.pointerId !== event.pointerId) return;
    canvas?.classList.remove("dragging");
    canvas?.releasePointerCapture?.(drag.pointerId);
    if (!drag.moved) state.projectRunGraphDrag = null;
  };

  $("#projectRunGraphCanvas")?.addEventListener("pointerup", endProjectGraphDrag);
  $("#projectRunGraphCanvas")?.addEventListener("pointercancel", endProjectGraphDrag);
  $("#projectRunGraphCanvas")?.addEventListener("pointerleave", endProjectGraphDrag);

  window.addEventListener("resize", () => {
    if (!state.projectRun?.graph || !state.projectRunGraphAutoFit) return;
    renderSymbolicGraphInto("#projectRunGraphCanvas", state.projectRun.graph);
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".campaign-distribute-btn");
    if (!button || !state.activePlatformCampaign?.campaign?.campaign_id) return;
    const data = await api(`/api/platform/campaigns/${state.activePlatformCampaign.campaign.campaign_id}/distribution`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan_id: button.dataset.planId }),
    });
    await loadDistribution();
    await loadPlatformDashboard();
    renderPlatformCampaign(data.project);
    await openCampaignRoom(data.project.campaign.campaign_id);
    setView("briefDistribution");
    await openDistribution(data.distribution.brief_id);
    toast("已从 Campaign Plan 生成 Brief 分发");
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".campaign-simulate-btn");
    if (!button || !state.activePlatformCampaign?.campaign?.campaign_id) return;
    const data = await api(`/api/platform/campaigns/${state.activePlatformCampaign.campaign.campaign_id}/simulations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan_id: button.dataset.planId }),
    });
    await loadPlatformDashboard();
    await openCampaignRoom(data.project.campaign.campaign_id);
    toast("Campaign 深度推演已保存");
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".review-commercial-btn");
    if (!button) return;
    const data = await api(`/api/creator-commercial/submissions/${button.dataset.submissionId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision: button.dataset.decision }),
    });
    await loadCommercial();
    await loadCreators();
    await loadPlatformDashboard();
    $("#commercialProfileOutput").textContent = JSON.stringify(data.commercial_profile || data.submission, null, 2);
    toast(button.dataset.decision === "approved" ? "商业档案已审核通过" : "提交已驳回");
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".open-commercial-profile-btn");
    if (!button) return;
    const data = await api(`/api/creator-commercial/profile/${button.dataset.creatorId}`);
    $("#commercialProfileOutput").textContent = JSON.stringify(data, null, 2);
  });

  document.addEventListener("input", (event) => {
    const field = event.target.closest("[data-symbolic-kind]");
    if (!field) return;
    const wrapper = field.closest(".symbolic-field");
    if (field.dataset.symbolicType === "tags" && wrapper) {
      const preview = wrapper.querySelector(".chip-preview");
      if (preview) preview.innerHTML = renderChips(splitInputList(field.value));
    }
    syncSymbolicJson(field.dataset.symbolicKind);
  });

  $("#loadSampleBtn").addEventListener("click", async () => {
    await api("/api/import/sample", { method: "POST" });
    await reloadAll();
    toast("示例数据已导入");
  });

  $("#creatorImportSampleBtn")?.addEventListener("click", async () => {
    try {
      await api("/api/import/sample", { method: "POST" });
      state.creatorsFetchAttempted = false;
      await loadCreators();
      toast("示例达人已导入");
    } catch (error) {
      toast(error.message, true);
    }
  });

  $("#homeBriefForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    payload.top_n = Number(payload.top_n || 5);
    const button = $("#homeBriefSubmitBtn");
    if (button) {
      button.disabled = true;
      button.textContent = "推演中...";
    }
    try {
      const data = await api("/api/kol-intelligence/conversation/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      renderHomeBriefResult(data);
      renderPhase82Conversation(data);
      if (data.prediction) renderPhase8Prediction(data.prediction);
      toast("Brief 图谱和 KOL 推荐已生成");
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "跑图推荐";
      }
    }
  });

  $("#homeBriefResult")?.addEventListener("click", async (event) => {
    const copyButton = event.target.closest(".home-proposal-copy-btn");
    if (copyButton) {
      await copyText(state.lastProposal);
      toast("方案已复制");
      return;
    }
    if (event.target.closest(".home-proposal-download-btn")) {
      downloadProposal();
      return;
    }
    if (event.target.closest(".home-proposal-share-btn")) {
      const conversation = state.homeBriefConversation;
      if (!conversation?.brief) return toast("请先生成 Brief 推荐", true);
      const data = await api("/api/collaboration/proposals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_name: conversation.client_name || "未命名客户",
          project_name: conversation.project_name || "KOL 推荐方案",
          brief: conversation.brief,
          top_n: Math.max(1, Math.min(12, (conversation.recommendations || []).length || 8)),
          created_by: "home_brief_chat",
        }),
      });
      renderHomeProposalShare(data);
      await loadCollaboration();
      toast("甲方分享链接已生成");
      return;
    }
    const shareCopyButton = event.target.closest(".home-share-copy-btn");
    if (shareCopyButton) {
      const shareUrl = state.homeBriefShare?.proposal?.share_url
        ? new URL(state.homeBriefShare.proposal.share_url, window.location.origin).toString()
        : "";
      await copyText(shareUrl);
      toast("甲方链接已复制");
      return;
    }
    if (event.target.closest(".home-proposal-open-btn")) {
      setView("proposal");
      $("#proposalOutput").value = state.lastProposal || "";
      toast("已打开方案页");
      return;
    }
    if (event.target.closest(".home-brief-to-filter-btn")) {
      const conversation = state.homeBriefConversation;
      const form = $("#homeBriefForm");
      const text = String(form?.elements?.message?.value || conversation?.brief?.raw_text || "").trim();
      const parsedBrief = conversation?.brief && typeof conversation.brief === "object" ? conversation.brief : null;
      const clientName = String(form?.elements?.client_name?.value || conversation?.client_name || "").trim();
      await openCreatorFilterWithBrief(text, { parsedBrief, clientName });
      return;
    }
  });

  $("#projectRunResult")?.addEventListener("click", async (event) => {
    if (!event.target.closest(".project-run-to-filter-btn")) return;
    const form = $("#projectRunForm");
    const text = String(form?.elements?.brief?.value || "").trim();
    const clientName = String(form?.elements?.client_name?.value || "").trim();
    await openCreatorFilterWithBrief(text, { clientName });
  });

  $("#agentArtifactList")?.addEventListener("click", async (event) => {
    const button = event.target.closest(".agent-deliverables-to-filter-btn");
    if (!button) return;
    const artifactId = button.dataset.artifactId || "";
    const artifact = state.activeAgentArtifacts.find((item) => item.artifact_id === artifactId);
    const payload = artifact?.payload || {};
    const taskBrief = state.activeAgentRun?.task?.brief || state.activeAgentThread?.task?.brief || "";
    const briefText = String(payload.brief?.raw_text || taskBrief || "").trim();
    const clientName = String(payload.client_card?.client_name || state.activeAgentRun?.task?.client_name || "").trim();
    if (!briefText) return toast("未找到可带入的 Brief", true);
    state.creatorFilterDeliverables = normalizeDeliverablesPayload(payload);
    await openCreatorFilterWithBrief(briefText, { clientName });
  });

  $("#kolIntakeForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const body = new FormData(form);
    const button = $("#kolIntakeSubmitBtn");
    if (button) {
      button.disabled = true;
      button.textContent = "识别中...";
    }
    try {
      const data = await api("/api/kol-intake", { method: "POST", body });
      renderKolIntakeResult(data);
      await reloadAll();
      toast(`已建档 ${data.imported} 个 KOL，并生成证据标签`);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "识别并打标签";
      }
    }
  });

  $("#kolIntakeResult")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-view-jump]");
    if (!button) return;
    setView(button.dataset.viewJump);
  });

  $("#fileForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = $("#fileInput").files[0];
    if (!file) return toast("请选择文件", true);
    state.importFile = file;
    const form = new FormData();
    form.append("file", file);
    const templateId = $("#importTemplateSelect").value;
    if (templateId) form.append("template_id", templateId);
    const data = await api("/api/import/file/preview", { method: "POST", body: form });
    renderImportReview(data);
    toast("解析完成，请确认字段映射");
  });

  $("#confirmImportBtn").addEventListener("click", async () => {
    if (!state.importFile || !state.importReview) return toast("请先解析文件", true);
    const form = new FormData();
    form.append("file", state.importFile);
    form.append("replace", $("#replaceInput").checked ? "true" : "false");
    form.append("mappings", JSON.stringify(collectImportMappings()));
    form.append("save_template", $("#saveTemplateInput").checked ? "true" : "false");
    form.append("template_name", $("#templateNameInput").value);
    if (state.importReview.matched_template?.id) form.append("template_id", state.importReview.matched_template.id);
    const data = await api("/api/import/file/commit", { method: "POST", body: form });
    await reloadAll();
    renderQualityReport(data.quality_report);
    toast(`已导入 ${data.imported} 个达人`);
  });

  $("#templateList").addEventListener("click", async (event) => {
    const button = event.target.closest(".delete-template-btn");
    if (!button) return;
    await api(`/api/import/templates/${button.dataset.templateId}`, { method: "DELETE" });
    await loadImportTemplates();
    toast("模板已删除");
  });

  $("#duplicateTable").addEventListener("click", async (event) => {
    const button = event.target.closest(".merge-duplicate-btn");
    if (!button) return;
    const candidate = state.duplicateCandidates[Number(button.dataset.index)];
    if (!candidate?.left?.creator_id || !candidate?.right?.creator_id) return;
    await api("/api/governance/merge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ primary_id: candidate.left.creator_id, duplicate_ids: [candidate.right.creator_id] }),
    });
    await reloadAll();
    toast("重复达人已合并");
  });

  $("#creatorEditForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button[type='submit']");
    const buttonLabel = button?.textContent || "保存并重新画像";
    if (button) {
      button.disabled = true;
      button.textContent = "保存中…";
    }
    try {
      const creatorId = form.elements.creator_id.value;
      await ensureCreatorTagsClassified(form);
      const payload = creatorFormPayload(form);
      payload.commercial_cases = collectCommercialCasesFromForm(form);
      const data = await api(`/api/creators/${creatorId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      renderCreatorModal(data.creator);
      await reloadCore();
      loadKolIntelligence().catch(() => {});
      toast("达人已保存并重新画像");
    } catch (error) {
      toast(error.message || "保存达人失败", true);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = buttonLabel;
      }
    }
  });

  $("#creatorImageAnalyzeBtn")?.addEventListener("click", async () => {
    const form = $("#creatorEditForm");
    const creatorId = form?.elements.creator_id.value;
    const fileInput = $("#creatorImageInput");
    const file = fileInput?.files?.[0];
    if (!creatorId || !file) {
      toast("请先选择一张图片", true);
      return;
    }
    const body = new FormData();
    body.append("file", file);
    $("#creatorImageAnalyzeBtn").disabled = true;
    $("#creatorImageAnalyzeBtn").textContent = "识别中...";
    try {
      const data = await api(`/api/creators/${creatorId}/media/analyze`, {
        method: "POST",
        body,
      });
      state.activeCreator = data.creator;
      renderCreatorMediaAssets(data.creator);
      renderCreatorImageAnalysis(data);
      await loadCreators();
      toast("图片已保存并完成识别");
    } finally {
      $("#creatorImageAnalyzeBtn").disabled = false;
      $("#creatorImageAnalyzeBtn").textContent = "识别图片";
    }
  });

  $("#creatorImageApplyBtn")?.addEventListener("click", () =>
    applyCreatorImageSuggestion($("#creatorEditForm"), { stateKey: "activeCreatorImageSuggestion" }),
  );

  $("#creatorModal")?.addEventListener("click", async (event) => {
    const button = event.target.closest(".creator-evidence-review-btn");
    if (!button) return;
    await api(`/api/kol-intelligence/tags/${encodeURIComponent(button.dataset.tagId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: button.dataset.status }),
    });
    if (state.activeCreator?.creator_id) {
      const data = await api(`/api/creators/${state.activeCreator.creator_id}`);
      state.activeCreator = data.creator;
      state.activeCreatorEvidenceTags = data.evidence_tags || [];
      renderCreatorModal(data.creator);
    }
    await loadKolIntelligence();
    toast(`标签已更新为 ${button.dataset.status}`);
  });

  $("#manualForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveManualCreator(event.currentTarget);
  });

  $("#linksForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = await api("/api/import/links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ links: $("#linksInput").value }),
    });
    await reloadAll();
    toast(`已解析 ${data.imported} 条链接`);
  });

  $("#apiForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const data = await api("/api/import/api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await reloadAll();
    toast(`已通过 ${data.provider} 接入：${data.creator.name}`);
  });

  $("#recommendBtn").addEventListener("click", async () => {
    const payload = {
      brief: $("#briefInput").value,
      budget: $("#budgetInput").value ? Number($("#budgetInput").value) : undefined,
      top_n: 20,
    };
    const data = await api("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderResults(data);
    setView("brief");
    toast("推荐已生成");
  });

  $("#collabCreateForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    payload.top_n = Number(payload.top_n || 12);
    const data = await api("/api/collaboration/proposals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await loadCollaboration();
    await openCollaborationProposal(data.proposal.proposal_id);
    toast("协作方案已生成");
  });

  $("#creatorInviteForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    payload.expires_days = Number(payload.expires_days || 14);
    const data = await api("/api/creator-commercial/invitations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await loadCommercial();
    $("#creatorInviteTokenInput").value = data.invitation.token;
    toast("博主邀请已生成");
  });

  $("#loadCreatorInviteBtn").addEventListener("click", async () => {
    const token = $("#creatorInviteTokenInput").value.trim();
    if (!token) return toast("请输入邀请 token", true);
    await loadCreatorInvite(token);
  });

  $("#creatorSubmissionForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const fields = formToObject(event.currentTarget);
    const token = fields.token;
    const payload = {
      profile_fields: {
        price_range: fields.price_range,
        availability: fields.availability,
        industry_fit_tags: fields.industry_fit_tags,
        content_capability_tags: fields.content_capability_tags,
        suitable_goals: fields.suitable_goals,
        commercial_positioning: fields.commercial_positioning,
      },
      cases: fields.case_brand_name
        ? [
            {
              brand_name: fields.case_brand_name,
              industry: fields.case_industry,
              content_format: fields.case_format,
              views: fields.case_views,
              visibility: "client_summary",
            },
          ]
        : [],
    };
    const data = await api(`/api/creator/invite/${token}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("#creatorInviteOutput").textContent = JSON.stringify(data, null, 2);
    await loadCommercial();
    await loadPlatformDashboard();
    toast("博主信息已提交，等待媒介审核");
  });

  $("#distributionCreateForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    payload.top_n = Number(payload.top_n || 8);
    const data = await api("/api/distribution/briefs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await loadDistribution();
    await openDistribution(data.brief.brief_id);
    await loadPlatformDashboard();
    await refreshWorkspaceHistoryIfVisible();
    toast("Brief 分发名单已生成");
  });

  $("#platformCampaignForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const data = await api("/api/platform/campaigns", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await loadPlatformDashboard();
    await refreshWorkspaceHistoryIfVisible();
    await openCampaignRoom(data.project.campaign.campaign_id);
    toast("Campaign 项目和 3 套方案已生成");
  });

  $("#projectRunNewBtn")?.addEventListener("click", () => {
    resetProjectRunWorkspace();
    $("#projectRunForm input[name='client_name']")?.focus();
    toast("已开启新 PR 需求");
  });

  $("#projectRunRandomBtn")?.addEventListener("click", () => {
    const brief = randomProjectRunBrief();
    resetProjectRunWorkspace({ values: brief });
    $("#projectRunForm textarea[name='brief']")?.focus();
    toast(`已生成随机 Brief：${brief.project_name}`);
  });

  $("#projectRunDemoBtn")?.addEventListener("click", () => {
    resetProjectRunWorkspace({ demo: true });
    $("#projectRunForm textarea[name='brief']")?.focus();
    toast("已恢复示例需求");
  });

  $("#projectRunForm select[name='simulation_engine']")?.addEventListener("change", updateProjectRunEngineNotice);
  updateProjectRunEngineNotice();

  $("#projectRunForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = $("#projectRunSubmitBtn");
    const payload = formToObject(form);
    payload.top_n = Number(payload.top_n || 8);
    const engineMode = projectRunEngineMode(payload.simulation_engine);
    startProjectRunProgress(payload);
    $("#projectRunResult")?.scrollIntoView({ behavior: "smooth", block: "start" });
    if (button) {
      button.disabled = true;
      button.textContent = engineMode.buttonText;
    }
    try {
      const data = await api("/api/project-run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      stopProjectRunProgress();
      renderProjectRun(data.run);
      await Promise.all([loadPlatformDashboard(), refreshWorkspaceHistoryIfVisible(), loadSymbolicOS(), loadCreators()]);
      toast("完整 PR 项目链路已生成");
    } catch (error) {
      stopProjectRunProgress();
      renderProjectRunSteps([{ id: "failed", label: "生成失败", status: "failed", detail: error.message || "请稍后重试。", count: 0 }]);
      toast(error.message || "完整 PR 项目链路生成失败", true);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "一键生成完整方案";
      }
    }
  });

  $("#projectRunOpenRoomBtn")?.addEventListener("click", async () => {
    const campaignId = state.projectRun?.campaign?.campaign?.campaign_id;
    if (!campaignId) return toast("请先生成 PR 项目", true);
    await openCampaignRoom(campaignId);
    setView("platformOS");
  });

  $("#phase8AnalyzeBtn")?.addEventListener("click", async () => {
    const button = $("#phase8AnalyzeBtn");
    if (button) {
      button.disabled = true;
      button.textContent = "分析中...";
    }
    try {
      const data = await api("/api/kol-intelligence/analyze-tags", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: 300 }),
      });
      state.kolIntelligence = data.snapshot;
      renderKolIntelligence(data.snapshot);
      await loadPhase8ReviewQueue();
      toast(`已生成 ${fmtNumber((data.items || []).length)} 个证据标签`);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "分析达人标签";
      }
    }
  });

  $("#phase8GraphBtn")?.addEventListener("click", async () => {
    const brief = $("#phase8BriefInput")?.value || "";
    const graph = await api("/api/kol-intelligence/graph", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ brief, limit: 80 }),
    });
    renderSymbolicGraphInto("#phase8GraphCanvas", graph);
    renderPhase8Evolution(graph.evolution || []);
    await loadKolIntelligence();
    toast("KOL 知识图谱已生成");
  });

  $("#phase8PredictBtn")?.addEventListener("click", async () => {
    const brief = ($("#phase8BriefInput")?.value || "").trim();
    if (!brief) return toast("请输入甲方 brief", true);
    const button = $("#phase8PredictBtn");
    if (button) {
      button.disabled = true;
      button.textContent = "预测中...";
    }
    try {
      const prediction = await api("/api/kol-intelligence/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brief, top_n: 8 }),
      });
      renderPhase8Prediction(prediction);
      await loadKolIntelligence();
      toast("预测推荐已完成");
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "预测推荐";
      }
    }
  });

  $("#phase82Form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formToObject(form);
    payload.top_n = Number(payload.top_n || 8);
    payload.history = state.phase82Messages || [];
    const button = $("#phase82RunBtn");
    if (button) {
      button.disabled = true;
      button.textContent = "推演中...";
    }
    try {
      state.phase82Messages = [...(state.phase82Messages || []), { role: "user", content: payload.message, status: "completed" }];
      renderPhase82Messages();
      const data = await api("/api/kol-intelligence/conversation/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      renderPhase82Conversation(data);
      if (data.prediction) renderPhase8Prediction(data.prediction);
      toast("对话图谱已完成");
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "运行对话图谱";
      }
    }
  });

  $("#phase82ResetBtn")?.addEventListener("click", () => {
    if (state.phase82FrameTimer) clearInterval(state.phase82FrameTimer);
    state.phase82Conversation = null;
    state.phase82Messages = [];
    state.phase82ActiveFrame = 0;
    renderPhase82Messages();
    renderPhase82Recommendations();
    renderPhase82Frame();
  });

  $("#phase82PrevFrameBtn")?.addEventListener("click", () => movePhase82Frame(-1));
  $("#phase82NextFrameBtn")?.addEventListener("click", () => movePhase82Frame(1));
  $("#phase82Steps")?.addEventListener("click", (event) => {
    const button = event.target.closest(".phase82-step");
    if (!button) return;
    if (state.phase82FrameTimer) {
      clearInterval(state.phase82FrameTimer);
      state.phase82FrameTimer = null;
    }
    state.phase82ActiveFrame = Number(button.dataset.frameIndex || 0);
    renderPhase82Frame();
  });

  $("#phase8RefreshReviewBtn")?.addEventListener("click", async () => {
    state.phase8SelectedTagIds.clear();
    await loadPhase8ReviewQueue();
    toast("审核队列已刷新");
  });

  $("#phase8ReviewStatus")?.addEventListener("change", loadPhase8ReviewQueue);
  $("#phase8ReviewCreator")?.addEventListener("change", loadPhase8ReviewQueue);

  $("#phase8ReviewQueue")?.addEventListener("change", (event) => {
    const input = event.target.closest(".phase8-tag-check");
    if (!input) return;
    if (input.checked) state.phase8SelectedTagIds.add(input.dataset.tagId);
    else state.phase8SelectedTagIds.delete(input.dataset.tagId);
  });

  $("#phase8ReviewQueue")?.addEventListener("click", async (event) => {
    const button = event.target.closest(".phase8-review-btn");
    if (!button) return;
    await reviewPhase8Tags([button.dataset.tagId], button.dataset.status);
  });

  $("#phase8BulkConfirmBtn")?.addEventListener("click", async () => {
    const ids = Array.from(state.phase8SelectedTagIds);
    if (!ids.length) return toast("请先选择标签", true);
    await reviewPhase8Tags(ids, "confirmed");
  });

  $("#dataSourceTestForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const data = await api("/api/settings/data-sources/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("#dataSourceTestOutput").textContent = JSON.stringify(data, null, 2);
    toast(data.ok ? "连接测试通过" : "连接测试未通过", !data.ok);
  });

  $("#postReviewForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const campaignId = payload.campaign_id || state.activePlatformCampaign?.campaign?.campaign_id;
    if (!campaignId) return toast("请先选择 Campaign", true);
    ["actual_price", "views", "likes", "comments"].forEach((key) => {
      payload[key] = Number(payload[key] || 0);
    });
    payload.delivery_rating = Number(payload.delivery_rating || 0);
    const data = await api(`/api/platform/campaigns/${campaignId}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await loadCreators();
    await loadPlatformDashboard();
    await openCampaignRoom(data.project.campaign.campaign_id);
    toast("投后复盘已回流到达人画像");
  });

  $("#platformArchiveBtn").addEventListener("click", async () => {
    if (!state.activePlatformCampaign?.campaign?.campaign_id) return toast("请先选择 Campaign", true);
    const data = await api(`/api/platform/campaigns/${state.activePlatformCampaign.campaign.campaign_id}/archive`, { method: "POST" });
    await loadPlatformDashboard();
    await openCampaignRoom(data.project.campaign.campaign_id);
    toast("Campaign 已归档");
  });

  $("#refreshCampaignRoomBtn").addEventListener("click", async () => {
    if (!state.activePlatformCampaign?.campaign?.campaign_id) return toast("请先选择 Campaign", true);
    await openCampaignRoom(state.activePlatformCampaign.campaign.campaign_id);
    toast("作战室已刷新");
  });

  $("#campaignRoomBackListBtn")?.addEventListener("click", () => {
    $("#platformCampaignDetail")?.classList.add("hidden");
    $("#platformCampaignList")?.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  $("#campaignRoomBackProjectRunBtn")?.addEventListener("click", () => {
    setView("projectRun");
    $("#projectRunResult")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  $("#pushDistributionBtn").addEventListener("click", async () => {
    if (!state.activeDistribution?.brief?.brief_id) return toast("请先选择 Brief", true);
    const data = await api(`/api/distribution/briefs/${state.activeDistribution.brief.brief_id}/push`, { method: "POST" });
    await loadDistribution();
    await openDistribution(data.brief.brief_id);
    await loadPlatformDashboard();
    toast("Brief 已推送给博主");
  });

  $("#loadCreatorBriefBtn").addEventListener("click", async () => {
    const token = $("#creatorBriefTokenInput").value.trim();
    if (!token) return toast("请输入 Brief token", true);
    await loadCreatorBrief(token);
  });

  $("#creatorBriefResponseForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const token = payload.token;
    payload.quote = Number(payload.quote || 0);
    const data = await api(`/api/creator/brief/${token}/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("#creatorBriefOutput").textContent = JSON.stringify(data, null, 2);
    if (state.activeDistribution?.brief?.brief_id) await openDistribution(state.activeDistribution.brief.brief_id);
    await loadDistribution();
    await loadPlatformDashboard();
    toast("博主响应已提交");
  });

  $("#openClientPreviewBtn").addEventListener("click", async () => {
    if (!state.activeProposal?.proposal?.share_token) return toast("请先选择方案", true);
    await loadClientShare(state.activeProposal.proposal.share_token);
  });

  $("#finalizeProposalBtn").addEventListener("click", async () => {
    if (!state.activeProposal?.proposal?.proposal_id) return toast("请先选择方案", true);
    const data = await api(`/api/collaboration/proposals/${state.activeProposal.proposal.proposal_id}/finalize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirmed_by: "client_user" }),
    });
    await loadCollaboration();
    await openCollaborationProposal(data.proposal.proposal_id);
    toast("方案已标记最终确认");
  });

  $("#saveShareSettingsBtn").addEventListener("click", async () => {
    if (!state.activeProposal?.proposal?.proposal_id) return toast("请先选择方案", true);
    const visibleFields = {};
    $$(".share-field-input").forEach((input) => {
      visibleFields[input.dataset.field] = input.checked;
    });
    const data = await api(`/api/collaboration/proposals/${state.activeProposal.proposal.proposal_id}/share`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visible_fields: visibleFields,
        share_enabled: $("#shareEnabledInput").checked,
        allow_comments: $("#allowCommentsInput").checked,
        allow_download: $("#allowDownloadInput").checked,
        expires_days: Number($("#expiresDaysInput").value || 14),
      }),
    });
    await openCollaborationProposal(data.proposal.proposal_id);
    toast("分享设置已保存");
  });

  $("#exportProposalBtn").addEventListener("click", async () => {
    if (!state.activeProposal?.proposal?.proposal_id) return toast("请先选择方案", true);
    const data = await api(`/api/collaboration/proposals/${state.activeProposal.proposal.proposal_id}/export`);
    state.lastProposal = data.markdown;
    $("#proposalOutput").value = data.markdown;
    setView("proposal");
    toast("最终方案已生成到方案导出页");
  });

  $("#loadClientShareBtn").addEventListener("click", async () => {
    const token = $("#clientShareTokenInput").value.trim();
    if (!token) return toast("请输入分享 token", true);
    await loadClientShare(token);
  });

  $("#clientProposalView").addEventListener("click", async (event) => {
    const decisionBtn = event.target.closest(".client-decision-btn");
    if (decisionBtn) {
      const token = $("#clientShareTokenInput").value.trim();
      const creatorId = decisionBtn.dataset.creatorId;
      const comment = $(`[data-client-comment="${creatorId}"]`)?.value || "";
      const proposalId = state.activeClientShare?.proposal?.proposal_id;
      const feedbackUrl =
        state.currentIdentity?.user?.user_type === "client" && proposalId
          ? `/api/client/portal/proposals/${proposalId}/feedback`
          : `/api/client/share/${token}/feedback`;
      const data = await api(feedbackUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_type: "creator",
          target_id: creatorId,
          decision: decisionBtn.dataset.decision,
          reason: decisionBtn.dataset.decision === "rejected" ? comment : "",
          comment,
        }),
      });
      state.activeClientShare = data.proposal;
      renderClientProposal(data.proposal);
      await loadCollaboration();
      toast("达人反馈已提交");
      return;
    }
    const overallBtn = event.target.closest(".client-overall-feedback-btn");
    if (overallBtn) {
      const token = $("#clientShareTokenInput").value.trim();
      const comment = $("#clientOverallComment").value;
      const proposalId = state.activeClientShare?.proposal?.proposal_id;
      const feedbackUrl =
        state.currentIdentity?.user?.user_type === "client" && proposalId
          ? `/api/client/portal/proposals/${proposalId}/feedback`
          : `/api/client/share/${token}/feedback`;
      const data = await api(feedbackUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_type: "proposal", comment }),
      });
      state.activeClientShare = data.proposal;
      renderClientProposal(data.proposal);
      await loadCollaboration();
      toast("整体反馈已提交");
    }
  });

  $("#collabFeedbackList").addEventListener("click", async (event) => {
    const button = event.target.closest(".feedback-status-btn");
    if (!button) return;
    await api(`/api/collaboration/feedback/${button.dataset.feedbackId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: button.dataset.status }),
    });
    if (state.activeProposal?.proposal?.proposal_id) {
      await openCollaborationProposal(state.activeProposal.proposal.proposal_id);
    }
    toast("反馈状态已更新");
  });

  $("#collabShareBox").addEventListener("click", async (event) => {
    const button = event.target.closest(".restore-version-btn");
    if (!button || !state.activeProposal?.proposal?.proposal_id) return;
    const data = await api(`/api/collaboration/proposals/${state.activeProposal.proposal.proposal_id}/versions/${button.dataset.versionNumber}/restore`, {
      method: "POST",
    });
    state.activeProposal = data;
    renderCollaborationDetail(data);
    await loadCollaboration();
    toast(`已恢复 v${button.dataset.versionNumber}`);
  });

  $("#creatorSymbolicForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const data = await api("/api/symbolic/creator-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.lastCreatorSymbolic = data.profile;
    renderSymbolicEditor("creator", data.profile);
    $("#creatorSymbolicOutput").value = JSON.stringify(data.profile, null, 2);
    toast("博主符号档案已生成");
  });

  $("#saveCreatorSymbolicBtn").addEventListener("click", async () => {
    syncSymbolicJson("creator");
    const profile = state.lastCreatorSymbolic || parseJsonEditor("#creatorSymbolicOutput");
    if (!profile.creator_id) return toast("缺少 creator_id，无法保存", true);
    const data = await api(`/api/symbolic/creator-profile/${profile.creator_id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    state.lastCreatorSymbolic = data.profile;
    renderSymbolicEditor("creator", data.profile);
    $("#creatorSymbolicOutput").value = JSON.stringify(data.profile, null, 2);
    if (state.lastBrand && state.lastSymbolicResults.length) {
      await refreshSymbolicMatch();
    }
    toast("博主符号档案已保存");
  });

  $("#brandSymbolicForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const data = await api("/api/symbolic/brand-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.lastBrand = data.profile;
    renderSymbolicEditor("brand", data.profile);
    $("#brandSymbolicOutput").value = JSON.stringify(data.profile, null, 2);
    $("#brandCalibrationSummary")?.classList.add("hidden");
    toast("品牌符号档案已生成");
  });

  $("#calibrateBrandSymbolicBtn").addEventListener("click", async () => {
    syncSymbolicJson("brand");
    let profile = state.lastBrand || parseJsonEditor("#brandSymbolicOutput");
    if (!profile.brand_id) return toast("请先生成品牌符号档案", true);
    if (!state.symbolicOS?.latest_report) {
      toast("请先在符号 OS 页面生成社会符号网络报告", true);
      setView("symbolicOS");
      return;
    }
    await api(`/api/symbolic/brand-profile/${profile.brand_id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    const data = await api(`/api/symbolic/brand-profile/${profile.brand_id}/calibrate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ report_id: state.symbolicOS.latest_report.report_id }),
    });
    state.lastBrand = data.profile;
    renderSymbolicEditor("brand", data.profile);
    $("#brandSymbolicOutput").value = JSON.stringify(data.profile, null, 2);
    renderBrandCalibration(data.calibration);
    if (state.lastSymbolicResults.length) await refreshSymbolicMatch();
    toast(data.calibration?.applied ? "品牌已完成社会校准" : "没有可用社会报告");
  });

  $("#saveBrandSymbolicBtn").addEventListener("click", async () => {
    syncSymbolicJson("brand");
    const profile = state.lastBrand || parseJsonEditor("#brandSymbolicOutput");
    if (!profile.brand_id) return toast("缺少 brand_id，无法保存", true);
    const data = await api(`/api/symbolic/brand-profile/${profile.brand_id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    state.lastBrand = data.profile;
    renderSymbolicEditor("brand", data.profile);
    $("#brandSymbolicOutput").value = JSON.stringify(data.profile, null, 2);
    if (state.lastSymbolicResults.length) await refreshSymbolicMatch();
    toast("品牌符号档案已保存");
  });

  $("#symbolicMatchBtn").addEventListener("click", async () => {
    await refreshSymbolicMatch();
    toast("符号匹配已生成");
  });

  $("#saveMatchAssetsBtn").addEventListener("click", async () => {
    if (!state.lastBrand || !state.lastSymbolicResults.length) {
      toast("请先生成符号匹配", true);
      return;
    }
    const data = await api("/api/symbolic-os/matches", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brand: state.lastBrand,
        product: state.symbolicOS?.products?.[0] || {},
        results: state.lastSymbolicResults,
      }),
    });
    state.symbolicOS = data.snapshot;
    renderSymbolicOS(data.snapshot);
    toast(`已保存 ${data.items.length} 条匹配资产`);
  });

  $("#saveNarrativeAssetsBtn").addEventListener("click", async () => {
    if (!state.lastBrand || !state.lastNarratives.length) {
      toast("请先生成符号匹配和叙事路径", true);
      return;
    }
    const data = await api("/api/symbolic-os/narratives", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brand: state.lastBrand,
        product: state.symbolicOS?.products?.[0] || {},
        narratives: state.lastNarratives,
      }),
    });
    state.symbolicOS = data.snapshot;
    renderSymbolicOS(data.snapshot);
    toast(`已保存 ${data.items.length} 条叙事路径`);
  });

  $("#refreshSymbolicGraphBtn").addEventListener("click", async () => {
    if (!state.lastBrand || !state.lastSymbolicResults.length) {
      toast("请先生成品牌符号档案和符号匹配", true);
      return;
    }
    await renderSymbolicGraphFromState();
    setView("symbolicGraph");
    toast("符号图谱已刷新");
  });

  $("#stressTestBtn").addEventListener("click", async () => {
    const payload = {
      engine: $("#stressEngine").value,
      brand: state.lastBrand,
      matches: state.lastSymbolicResults.slice(0, 5),
      narratives: state.lastNarratives,
    };
    if (!payload.brand || !payload.matches.length) {
      toast("请先生成品牌符号档案和符号匹配", true);
      return;
    }
    await runSimulation(payload);
    toast("推演完成");
  });

  $("#demoStressTestBtn").addEventListener("click", async () => {
    await runSimulation(demoSimulationPayload($("#stressEngine").value));
    toast("示例推演完成");
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  hydrateAuthSessionFromLocation();
  syncAppBuildVersionInUrl();
  applySidebarState();
  decorateViews();
  bindEvents();
  try {
    await reloadAll({ backgroundSecondary: true });
    const share = new URLSearchParams(window.location.search).get("share");
    if (share) await loadClientShare(share);
    const inviteMatch = window.location.pathname.match(/^\/creator\/invite\/([^/]+)$/);
    if (inviteMatch) {
      setView("creatorCommercial");
      await loadCreatorInvite(inviteMatch[1]);
    }
    const briefMatch = window.location.pathname.match(/^\/creator\/brief\/([^/]+)$/);
    if (briefMatch) {
      setView("briefDistribution");
      await loadCreatorBrief(briefMatch[1]);
    }
  } catch (error) {
    $("#serverStatus").textContent = error.message === "需要 Access Key" ? "需要登录" : "连接失败";
    if (error.message === "需要 Access Key") showAccessGate("请登录后继续使用。");
    toast(error.message, true);
  }
});
