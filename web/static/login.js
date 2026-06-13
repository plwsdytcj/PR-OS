const $ = (selector) => document.querySelector(selector);

function clearLocalAuthHints() {
  localStorage.removeItem("pr_ai_os_access_key");
}

function setFeedback(message, tone = "neutral") {
  const node = $("#loginFeedback");
  if (!node) return;
  node.textContent = message || "";
  node.dataset.tone = tone;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    cache: "no-store",
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.detail || data.message || "请求失败");
  }
  return data;
}

function redirectToApp() {
  window.location.href = "/app?v=20260611-6";
}

async function checkExistingSession() {
  setFeedback("正在检查登录状态...", "neutral");
  try {
    const data = await api("/api/auth/me");
    if (data.authenticated && data.identity) {
      setFeedback("已登录，正在进入工作台...", "success");
      window.setTimeout(redirectToApp, 120);
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
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
        }),
      });
      const label = data.user?.user_type === "client" ? "甲方客户 Portal" : "内部工作台";
      setFeedback(`登录成功，正在进入${label}。`, "success");
      window.setTimeout(redirectToApp, 250);
    } catch (error) {
      setFeedback(error.message || "登录失败", "danger");
    }
  });
}

bindLoginForm();
checkExistingSession();
