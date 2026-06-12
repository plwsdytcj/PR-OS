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

function setSessionBox(identity) {
  const box = $("#sessionBox");
  const labelNode = $("#sessionLabel");
  if (!box || !labelNode) return;
  const user = identity?.user;
  if (!user) {
    box.classList.add("hidden");
    labelNode.textContent = "";
    return;
  }
  const label = user.user_type === "client" ? "甲方客户" : "内部团队";
  labelNode.textContent = `当前浏览器已保持登录：${user.email || user.name || "当前账号"}（${label}）。`;
  box.classList.remove("hidden");
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
  setFeedback("正在检查当前浏览器会话...", "neutral");
  try {
    const data = await api("/api/auth/me");
    if (data.authenticated && data.identity) {
      const user = data.identity.user || {};
      const label = user.user_type === "client" ? "甲方客户" : "内部团队";
      setSessionBox(data.identity);
      setFeedback(`已登录为 ${user.email || user.name || "当前账号"}（${label}），可以直接进入工作台。`, "success");
      return;
    }
    setSessionBox(null);
    clearLocalAuthHints();
    setFeedback("未检测到有效登录会话，请输入邮箱和密码。", "neutral");
  } catch {
    setSessionBox(null);
    clearLocalAuthHints();
    setFeedback("未检测到有效登录会话，请输入邮箱和密码。", "neutral");
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

function bindLogoutButton() {
  $("#logoutBtn")?.addEventListener("click", async () => {
    setFeedback("正在退出当前浏览器会话...", "neutral");
    try {
      await api("/api/auth/logout", { method: "POST" });
    } catch {
      // Even if the server session is already gone, clear browser-side hints.
    }
    clearLocalAuthHints();
    setSessionBox(null);
    $("#password").value = "";
    setFeedback("已退出。现在可以重新登录或切换账号。", "success");
  });
}

bindLoginForm();
bindLogoutButton();
checkExistingSession();
