const state = {
  tenant: localStorage.getItem("pr_ai_os_tenant") || "default",
  accessKey: localStorage.getItem("pr_ai_os_access_key") || "",
  authRequired: false,
  currentIdentity: null,
  authUsers: [],
  authClients: [],
  projectAccess: [],
  agentTasks: [],
  activeAgentRun: null,
  activeAgentArtifacts: [],
  activeArtifactDetail: null,
  activeAgentGraphNodeId: "",
  agentPollTimer: null,
  knowledgeDocuments: [],
  knowledgeStats: null,
  knowledgeSearchResults: [],
  clientPortalProjects: [],
  creators: [],
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
  projectRun: null,
  projectRunSelectedNodeId: "",
  projectRunStageFilter: "",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

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
  projectRun: ["新建 PR 项目", "输入一个需求，自动跑完 brief、符号图谱、KOL 选择和 Campaign Room。"],
  ingest: ["数据接入", "把 Excel、链接和 API 变成统一 KOL Profile。"],
  creators: ["达人库", "扫描、修正和调用你的私有 KOL 资产。"],
  governance: ["数据治理", "清理重复、补齐字段、提高推荐可信度。"],
  brief: ["Brief 推荐", "把甲方需求转成可解释的达人组合。"],
  proposal: ["方案导出", "把推荐结果打包成甲方可读方案。"],
  collaboration: ["客户协作", "让甲方在线查看、反馈和确认名单。"],
  clientPortal: ["甲方方案页", "模拟客户视角的方案确认体验。"],
  creatorCommercial: ["博主商业档案", "邀请博主补充报价、档期和案例。"],
  briefDistribution: ["Brief 分发", "把确认的需求推给博主并收集响应。"],
  platformOS: ["OS 总控台", "管理 Campaign、多方案、推演和投后回流。"],
  organization: ["组织管理", "管理内部账号、甲方客户、客户成员和项目授权。"],
  dataSources: ["数据源设置", "检查达人 API、LLM、推演引擎和导入能力。"],
  symbolicOS: ["符号 OS", "维护社会符号网络、能指标签库和投后修正。"],
  symbolicCreator: ["博主符号档案", "把内容风格、受众幻想和风险变成标签。"],
  symbolicBrand: ["品牌符号分析", "识别品牌想获得和想避开的传播符号。"],
  symbolicMatch: ["符号匹配", "用符号关系解释品牌和博主为什么适合。"],
  symbolicGraph: ["符号图谱", "把品牌、博主、内容路径和风险连成图。"],
  stressTest: ["压力测试", "投放前模拟评论区、竞品和品牌安全风险。"],
};

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
  $("#gateAccessKeyInput").value = state.accessKey || "";
  const title = gate.querySelector("p");
  if (title && message) title.textContent = message === "login required" ? "请用内部或甲方账号登录后继续使用。" : message;
}

function hideAccessGate() {
  $("#accessGate")?.classList.add("hidden");
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("X-Tenant-ID", state.tenant || "default");
  if (state.accessKey) headers.set("X-Access-Key", state.accessKey);
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      showAccessGate(data.detail || "login required");
      throw new Error(data.detail === "login required" ? "需要登录" : data.detail || "需要登录");
    }
    throw new Error(data.detail || `请求失败：${response.status}`);
  }
  return data;
}

function fmtNumber(value) {
  const n = Number(value || 0);
  return n ? n.toLocaleString("zh-CN") : "-";
}

function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setView(viewId) {
  $$(".view").forEach((node) => node.classList.toggle("active", node.id === viewId));
  $$(".nav-item").forEach((node) => node.classList.toggle("active", node.dataset.view === viewId));
  const activeNav = $(`.nav-item[data-view="${viewId}"]`);
  $$(".nav-group").forEach((group) => {
    group.open = Boolean(activeNav && group.contains(activeNav));
  });
}

function decorateViews() {
  $$(".view").forEach((view) => {
    if (view.querySelector(":scope > .view-poster")) return;
    const meta = VIEW_TITLES[view.id];
    if (!meta || view.id === "workspace") return;
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
  renderAuthUser();
  return data;
}

function renderAuthUser() {
  const box = $("#authUserBox");
  if (!box) return;
  const user = state.currentIdentity?.user;
  if (!user) {
    box.innerHTML = `
      <span>未登录</span>
      <button id="authOpenLoginBtn" class="secondary" type="button">登录</button>
    `;
    return;
  }
  box.innerHTML = `
    <span>${escapeHTML(user.name || user.email)} · ${escapeHTML(user.role)}</span>
    <button id="authLogoutBtn" class="secondary" type="button">退出</button>
  `;
}

async function loadCreators() {
  const data = await api("/api/creators");
  state.creators = data.items;
  renderCreators();
  renderCreatorOptions();
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
  state.authUsers = users.items || [];
  state.authClients = clients.items || [];
  state.collabProposals = proposals.items || [];
  state.projectAccess = access.items || [];
  renderOrganization();
}

async function loadAgentTasks() {
  if (state.currentIdentity?.user?.user_type === "client") return;
  const data = await api("/api/agent/tasks");
  state.agentTasks = data.items || [];
  renderAgentTasks();
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
}

function renderCreators() {
  const query = ($("#creatorSearch")?.value || "").toLowerCase();
  const list = $("#creatorList");
  if (!list) return;
  const items = state.creators.filter((creator) => {
    const text = [
      creator.name,
      creator.platform,
      creator.ai_summary,
      ...(creator.industry_fit_tags || []),
      ...(creator.content_capability_tags || []),
    ]
      .join(" ")
      .toLowerCase();
    return text.includes(query);
  });
  if (!items.length) {
    list.innerHTML = emptyState("暂无达人数据", "先导入 Excel / CSV 或使用示例数据启动达人雷达。");
    return;
  }
  list.innerHTML = items
    .map((creator) => {
      const tags = [...(creator.industry_fit_tags || []), ...(creator.content_capability_tags || [])]
        .slice(0, 6)
        .map((tag) => `<span class="tag">${tag}</span>`)
        .join("");
      const risks = (creator.risk_tags || [])
        .slice(0, 2)
        .map((tag) => `<span class="tag risk">${tag}</span>`)
        .join("");
      return `
        <article class="creator-card">
          <div class="card-kicker">${escapeHTML(creator.platform || "未知平台")}</div>
          <div class="creator-card-head">
            <h3>${creator.name}</h3>
            <button class="secondary open-creator-btn" data-creator-id="${creator.creator_id}" type="button">详情</button>
          </div>
          <div class="meta">${creator.platform} · 粉丝 ${fmtNumber(creator.follower_count)} · 报价 ${fmtNumber(creator.listed_price)}</div>
          <p>${creator.ai_summary || "待生成画像"}</p>
          <div class="tag-list">${tags}${risks}</div>
        </article>
      `;
    })
    .join("");
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
  renderOrgMetrics();
  renderInternalUsers();
  renderClientAccounts();
  renderOrgSelects();
  renderProjectAccessTable();
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
  list.innerHTML = state.authClients.length
    ? state.authClients
        .map((client) => {
          const members = (client.members || [])
            .map((member) => {
              const user = userById(member.user_id);
              return `
                <span class="mini-member">
                  ${escapeHTML(user?.name || user?.email || member.user_id)}
                  ${renderRolePill(member.role)}
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

function renderAgentTasks() {
  const list = $("#agentTaskList");
  if (!list) return;
  list.innerHTML = state.agentTasks.length
    ? state.agentTasks
        .map(({ task, runs, artifacts }) => {
          const latestRun = runs?.[0];
          return `
            <button class="agent-task-item" data-run-id="${escapeHTML(latestRun?.run_id || "")}" data-task-id="${escapeHTML(task.task_id)}" type="button">
              <strong>${escapeHTML(task.title)}</strong>
              <span>${escapeHTML(task.status)} · ${artifacts?.length || 0} 个产物</span>
            </button>
          `;
        })
        .join("")
    : emptyState("暂无 Agent 任务", "输入一个 PR 需求后会生成任务、执行和产物。");
}

function renderAgentRun(data) {
  state.activeAgentRun = data;
  state.activeAgentArtifacts = data.artifacts || [];
  const run = data.run || {};
  const task = data.task || {};
  const events = data.events || [];
  const meta = $("#agentRunMeta");
  if (meta) meta.textContent = task.title ? `${task.title} · ${run.status || "running"}` : "等待 Agent 执行。";
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
  renderAgentReasoningGraph();
}

function renderAgentArtifacts() {
  const list = $("#agentArtifactList");
  if (!list) return;
  list.innerHTML = state.activeAgentArtifacts.length
    ? state.activeAgentArtifacts.map((artifact) => renderAgentArtifact(artifact)).join("")
    : emptyState("暂无产物", "Agent 会在这里沉淀知识检索、PR 运行结果和甲方方案。");
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
      const score = node.score ? `<tspan x="${node.x}" dy="15">score ${escapeHTML(node.score)}</tspan>` : "";
      return `
        <g class="graph-node agent-reasoning-node ${escapeHTML(node.type || "node")}${selected}" data-agent-node-id="${escapeHTML(node.id)}" tabindex="0" role="button" aria-label="${escapeHTML(node.label)}">
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
  if (state.agentPollTimer) {
    clearInterval(state.agentPollTimer);
    state.agentPollTimer = null;
  }
}

function startAgentPolling(runId) {
  stopAgentPolling();
  if (!runId) return;
  const tick = async () => {
    try {
      const data = await api(`/api/agent/runs/${runId}`);
      renderAgentRun(data);
      const status = data.run?.status || "";
      if (!["running"].includes(status)) {
        stopAgentPolling();
        await loadAgentTasks();
      }
    } catch (error) {
      stopAgentPolling();
      toast(error.message, true);
    }
  };
  tick();
  state.agentPollTimer = setInterval(tick, 1000);
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

async function reloadAll() {
  await refreshStatus();
  const auth = await loadAuthMe();
  if (state.authRequired && !auth.authenticated && !state.accessKey) {
    showAccessGate("请用内部或甲方账号登录后继续使用。");
    return;
  }
  if (state.currentIdentity?.user?.user_type === "client") {
    await loadClientPortalProjects();
    setView("clientPortal");
    return;
  }
  await loadCreators();
  await loadImportTemplates();
  await loadGovernance();
  await loadSymbolicEngines();
  await loadAgentTasks();
  await loadKnowledge();
  await loadCollaboration();
  await loadOrganization();
  await loadCommercial();
  await loadDistribution();
  await loadPlatformDashboard();
  await loadDataSources();
  await loadSymbolicOS();
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
  canvas.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="符号关系图谱">${edgeSvg}${nodeSvg}</svg>`;
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
          return `<button class="stage-pill ${escapeHTML(cls)}${active}" data-stage="${escapeHTML(stage)}" type="button">${escapeHTML(label)} <strong>${fmtNumber(counts[stage])}</strong></button>`;
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
  target.innerHTML = `
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
  const data = await api(`/api/creators/${creatorId}`);
  state.activeCreator = data.creator;
  renderCreatorModal(data.creator);
  $("#creatorModal").classList.remove("hidden");
}

function closeCreatorModal() {
  $("#creatorModal").classList.add("hidden");
  state.activeCreator = null;
}

function renderCreatorModal(creator) {
  const form = $("#creatorEditForm");
  const fields = form.elements;
  $("#creatorModalTitle").textContent = creator.name;
  $("#creatorModalMeta").textContent = `${creator.platform} · ${creator.creator_id}`;
  fields.creator_id.value = creator.creator_id;
  fields.name.value = creator.name || "";
  fields.platform.value = creator.platform || "未知";
  fields.platform_user_id.value = creator.platform_user_id || "";
  fields.homepage_url.value = creator.homepage_url || "";
  fields.follower_count.value = creator.follower_count || "";
  fields.listed_price.value = creator.listed_price || "";
  fields.region.value = creator.region || "";
  fields.contact.value = creator.contact || "";
  fields.cooperation_brands.value = (creator.cooperation_brands || []).join("，");
  fields.cooperation_formats.value = (creator.cooperation_formats || []).join("，");
  fields.bio.value = creator.bio || "";
  fields.manual_notes.value = creator.manual_notes || "";
  $("#creatorDataSources").innerHTML = (creator.data_sources || [])
    .map((source) => `<span class="tag">${escapeHTML(source)}</span>`)
    .join("") || '<span class="meta">暂无来源</span>';
  const tags = [
    ...(creator.industry_fit_tags || []),
    ...(creator.content_capability_tags || []),
    ...(creator.suitable_goals || []),
    ...(creator.suitable_stages || []),
    ...(creator.budget_fit_tags || []),
    ...(creator.risk_tags || []),
  ];
  $("#creatorTags").innerHTML = tags.length
    ? tags.map((tag) => `<span class="tag">${escapeHTML(tag)}</span>`).join("")
    : '<span class="meta">暂无标签</span>';
}

function creatorFormPayload(form) {
  const fields = form.elements;
  return {
    name: fields.name.value,
    platform: fields.platform.value,
    platform_user_id: fields.platform_user_id.value,
    homepage_url: fields.homepage_url.value,
    follower_count: Number(fields.follower_count.value || 0),
    listed_price: Number(fields.listed_price.value || 0),
    region: fields.region.value,
    contact: fields.contact.value,
    cooperation_brands: fields.cooperation_brands.value,
    cooperation_formats: fields.cooperation_formats.value,
    bio: fields.bio.value,
    manual_notes: fields.manual_notes.value,
  };
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

function bindEvents() {
  renderTenantStatus();
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
  $("#accessKeyApplyBtn").addEventListener("click", async () => {
    state.accessKey = $("#accessKeyInput").value.trim();
    localStorage.setItem("pr_ai_os_access_key", state.accessKey);
    await reloadAll();
    toast(state.accessKey ? "Access key 已保存" : "Access key 已清空");
  });
  $("#accessKeyInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") $("#accessKeyApplyBtn").click();
  });
  $("#loginForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    await api("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    hideAccessGate();
    await reloadAll();
    toast("已登录");
  });
  $("#bootstrapAdminForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    if (state.accessKey) payload.access_key = state.accessKey;
    await api("/api/auth/bootstrap-admin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    hideAccessGate();
    await reloadAll();
    toast("Admin 已创建并登录");
  });
  $("#gateAccessKeyBtn").addEventListener("click", async () => {
    state.accessKey = $("#gateAccessKeyInput").value.trim();
    localStorage.setItem("pr_ai_os_access_key", state.accessKey);
    renderTenantStatus();
    hideAccessGate();
    try {
      await reloadAll();
      toast("Access Key 已验证");
    } catch (error) {
      showAccessGate();
      toast(error.message, true);
    }
  });
  $("#gateAccessClearBtn").addEventListener("click", () => {
    state.accessKey = "";
    localStorage.removeItem("pr_ai_os_access_key");
    renderTenantStatus();
    showAccessGate();
  });
  $("#gateAccessKeyInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") $("#gateAccessKeyBtn").click();
  });
  document.addEventListener("click", async (event) => {
    if (event.target.closest("#authOpenLoginBtn")) {
      showAccessGate("请登录后继续使用。");
      return;
    }
    if (event.target.closest("#authLogoutBtn")) {
      stopAgentPolling();
      await api("/api/auth/logout", { method: "POST" });
      state.currentIdentity = null;
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
  $("#agentChatForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const button = $("#agentRunBtn");
    try {
      if (button) {
        button.disabled = true;
        button.textContent = "执行中...";
      }
      const data = await api("/api/agent/chat/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      renderAgentRun(data);
      startAgentPolling(data.run?.run_id);
      await loadAgentTasks();
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
    const data = await api(`/api/agent/runs/${runId}/approve-plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ top_n: topN }),
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
    const data = await api(`/api/agent/runs/${runId}/clarification`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ supplement: payload.supplement, top_n: Number(payload.top_n || 8) }),
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
  $("#downloadProposalBtn").addEventListener("click", downloadProposal);
  $("#closeCreatorModalBtn").addEventListener("click", closeCreatorModal);
  $("#closeArtifactModalBtn")?.addEventListener("click", closeArtifactModal);
  $("#artifactModal")?.addEventListener("click", (event) => {
    if (event.target.dataset.closeArtifactModal) closeArtifactModal();
  });
  $("#creatorModal").addEventListener("click", (event) => {
    if (event.target.dataset.closeModal) closeCreatorModal();
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".open-creator-btn");
    if (!button) return;
    await openCreatorModal(button.dataset.creatorId);
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
    const creatorId = form.elements.creator_id.value;
    const data = await api(`/api/creators/${creatorId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(creatorFormPayload(form)),
    });
    renderCreatorModal(data.creator);
    await reloadAll();
    toast("达人已保存并重新画像");
  });

  $("#manualForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = formToObject(event.currentTarget);
    const data = await api("/api/import/manual", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    event.currentTarget.reset();
    await reloadAll();
    toast(`已保存：${data.creator.name}`);
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
    await openCampaignRoom(data.project.campaign.campaign_id);
    toast("Campaign 项目和 3 套方案已生成");
  });

  $("#projectRunForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = $("#projectRunSubmitBtn");
    const payload = formToObject(form);
    payload.top_n = Number(payload.top_n || 8);
    renderProjectRunSteps([{ id: "running", label: "系统正在跑完整链路", status: "active", detail: "解析 brief、生成符号图谱、选择 KOL、创建 Campaign Room。", count: 0 }]);
    if (button) {
      button.disabled = true;
      button.textContent = "生成中...";
    }
    try {
      const data = await api("/api/project-run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      renderProjectRun(data.run);
      await Promise.all([loadPlatformDashboard(), loadSymbolicOS(), loadCreators()]);
      toast("完整 PR 项目链路已生成");
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
  decorateViews();
  bindEvents();
  try {
    await reloadAll();
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
    $("#serverStatus").textContent = error.message === "需要 Access Key" ? "需要 Access Key" : "连接失败";
    if (error.message === "需要 Access Key") showAccessGate();
    toast(error.message, true);
  }
});
