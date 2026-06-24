const $ = (selector) => document.querySelector(selector);
const SESSION_KEY = "pr_ai_os_session_token";

function persistAuthSession(session) {
  const token = String(session?.session_id || "").trim();
  if (!token) return;
  localStorage.setItem(SESSION_KEY, token);
}

function clearLocalAuthHints() {
  localStorage.removeItem("pr_ai_os_access_key");
  localStorage.removeItem(SESSION_KEY);
}

function setFeedback(message, tone = "neutral") {
  const node = $("#loginFeedback");
  if (!node) return;
  node.textContent = message || "";
  node.dataset.tone = tone;
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("X-Tenant-ID", localStorage.getItem("pr_ai_os_tenant") || "default");
  const sessionToken = localStorage.getItem(SESSION_KEY) || "";
  if (sessionToken) headers.set("X-Session-Token", sessionToken);
  const response = await fetch(path, {
    credentials: "include",
    cache: "no-store",
    ...options,
    headers,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.detail || data.message || "请求失败");
  }
  return data;
}

function redirectToApp(session = null) {
  const token = String(session?.session_id || localStorage.getItem(SESSION_KEY) || "").trim();
  const hash = token ? `#session=${encodeURIComponent(token)}` : "";
  const version = window.prOsBuildVersion();
  window.location.href = `/app?v=${encodeURIComponent(version)}${hash}`;
}

async function checkExistingSession() {
  setFeedback("正在检查登录状态...", "neutral");
  try {
    const data = await api("/api/auth/me");
    if (data.authenticated && data.identity) {
      if (data.session?.session_id) persistAuthSession(data.session);
      setFeedback("已登录，正在进入工作台...", "success");
      window.setTimeout(() => redirectToApp(data.session), 120);
      return;
    }
    clearLocalAuthHints();
    setFeedback("");
  } catch {
    clearLocalAuthHints();
    setFeedback("");
  }
}

function bindLoginForm() {
  $("#loginForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setFeedback("正在登录...", "neutral");
    try {
      const data = await api("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
        }),
      });
      persistAuthSession(data.session);
      const label = data.user?.user_type === "client" ? "甲方客户 Portal" : "内部工作台";
      setFeedback(`登录成功，正在进入${label}。`, "success");
      window.setTimeout(() => redirectToApp(data.session), 250);
    } catch (error) {
      setFeedback(error.message || "登录失败", "danger");
    }
  });
}

bindLoginForm();
checkExistingSession();
