const $ = (selector) => document.querySelector(selector);

function setFeedback(message, tone = "neutral") {
  const node = $("#loginFeedback");
  if (!node) return;
  node.textContent = message || "";
  node.dataset.tone = tone;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
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
  try {
    const data = await api("/api/auth/me");
    if (data.authenticated && data.identity) {
      const label = data.identity.user_type === "client" ? "甲方客户" : "内部团队";
      setFeedback(`已登录为 ${data.identity.email}（${label}），可以直接进入工作台。`, "success");
    }
  } catch {
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

function bindBootstrapForm() {
  $("#bootstrapForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setFeedback("正在创建 admin...", "neutral");
    try {
      await api("/api/auth/bootstrap-admin", {
        method: "POST",
        body: JSON.stringify({
          email: form.get("adminEmail"),
          password: form.get("adminPassword"),
        }),
      });
      setFeedback("Admin 已创建，正在进入工作台。", "success");
      window.setTimeout(redirectToApp, 250);
    } catch (error) {
      setFeedback(error.message || "创建失败", "danger");
    }
  });
}

bindLoginForm();
bindBootstrapForm();
checkExistingSession();
