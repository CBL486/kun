const elements = {
  form: document.querySelector("#key-form"),
  key: document.querySelector("#deepseek-key"),
  validate: document.querySelector("#validate-button"),
  save: document.querySelector("#save-button"),
  status: document.querySelector("#setup-status"),
  configuredPanel: document.querySelector("#configured-panel"),
  configuredCopy: document.querySelector("#configured-copy"),
  continueButton: document.querySelector("#continue-button"),
  replaceButton: document.querySelector("#replace-button"),
  clearButton: document.querySelector("#clear-button"),
  helpButton: document.querySelector("#help-button"),
  helpDialog: document.querySelector("#help-dialog"),
  helpClose: document.querySelector("#help-close"),
};

const errorCopy = {
  invalid_deepseek_key: "Key 格式不正确，请检查后重试。",
  deepseek_auth_failed: "Key 无效或没有 API 权限。",
  deepseek_quota_unavailable: "账户额度不足或请求过于频繁。",
  deepseek_timeout: "校验超时，请检查网络后重试。",
  deepseek_network_error: "无法连接 DeepSeek，请检查网络。",
  deepseek_unavailable: "DeepSeek 当前不可用，请稍后重试。",
  deepseek_invalid_response: "DeepSeek 返回异常，请稍后重试。",
  setup_lock_busy: "另一个设置进程正在写入，请稍后重试。",
};

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(body?.error?.message || "request_failed");
    error.code = body?.error?.code || "request_failed";
    throw error;
  }
  return body;
}

function setStatus(message, kind = "") {
  elements.status.textContent = message;
  elements.status.classList.toggle("is-error", kind === "error");
  elements.status.classList.toggle("is-success", kind === "success");
}

function setBusy(busy) {
  elements.validate.disabled = busy;
  elements.save.disabled = busy;
  elements.clearButton.disabled = busy;
  elements.continueButton.disabled = busy;
}

function clearKeyInput() {
  elements.key.value = "";
}

function renderStatus(status) {
  const configured = status.configured;
  elements.form.hidden = configured;
  elements.configuredPanel.hidden = !configured;
  if (!configured) {
    setStatus("尚未配置 DeepSeek Key。");
    return;
  }
  elements.configuredCopy.textContent =
    `已配置 ${status.provider} · ${status.key_hint || "sk-..."}`
    + (status.persona_configured ? " · 默认人设已就绪" : "");
  setStatus(
    status.world_ready ? "设置完成，可以进入青禾镇。" : "Key 已保存，请继续完成设置。",
    "success",
  );
}

async function loadStatus() {
  try {
    renderStatus(await fetchJSON("/api/setup/status"));
  } catch (error) {
    setStatus("无法读取设置状态，请确认本地 API 已启动。", "error");
  }
}

function keyFromInput() {
  const key = elements.key.value.trim();
  if (!key) {
    setStatus("请先输入 DeepSeek Key。", "error");
    return null;
  }
  return key;
}

async function requestWithKey(path, key) {
  return fetchJSON(path, {
    method: "POST",
    body: JSON.stringify({ api_key: key }),
  });
}

async function validateKey() {
  const key = keyFromInput();
  if (!key) return;
  setBusy(true);
  setStatus("正在让 DeepSeek 校验 Key…");
  try {
    await requestWithKey("/api/setup/deepseek/validate", key);
    setStatus("校验通过。现在可以保存。", "success");
  } catch (error) {
    setStatus(errorCopy[error.code] || "Key 校验失败，请重试。", "error");
  } finally {
    clearKeyInput();
    setBusy(false);
  }
}

async function saveKey() {
  const key = keyFromInput();
  if (!key) return;
  setBusy(true);
  setStatus("正在校验并保存 Key…");
  try {
    const status = await requestWithKey("/api/setup/deepseek/save", key);
    const complete = await fetchJSON("/api/setup/complete", {
      method: "POST",
      body: JSON.stringify({ use_default_persona: true }),
    });
    renderStatus({ ...status, ...complete });
    setStatus("Key 已安全保存。正在进入青禾镇…", "success");
    window.setTimeout(() => {
      window.location.assign("/");
    }, 500);
  } catch (error) {
    setStatus(errorCopy[error.code] || "保存失败，请重试。", "error");
  } finally {
    clearKeyInput();
    setBusy(false);
  }
}

async function completeSetup() {
  setBusy(true);
  try {
    const status = await fetchJSON("/api/setup/complete", {
      method: "POST",
      body: JSON.stringify({ use_default_persona: true }),
    });
    renderStatus(status);
    window.location.assign("/");
  } catch (error) {
    setStatus("无法完成设置，请稍后重试。", "error");
  } finally {
    setBusy(false);
  }
}

async function clearKey() {
  if (!window.confirm("清除 DeepSeek Key？世界和角色数据不会因此清空。")) return;
  setBusy(true);
  try {
    renderStatus(await fetchJSON("/api/setup/deepseek/clear", {
      method: "POST",
      body: JSON.stringify({}),
    }));
    setStatus("Key 已清除。", "success");
  } catch (error) {
    setStatus("无法清除 Key，请稍后重试。", "error");
  } finally {
    setBusy(false);
  }
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  saveKey();
});
elements.validate.addEventListener("click", validateKey);
elements.continueButton.addEventListener("click", completeSetup);
elements.clearButton.addEventListener("click", clearKey);
elements.replaceButton.addEventListener("click", () => {
  elements.configuredPanel.hidden = true;
  elements.form.hidden = false;
  elements.key.focus();
});
elements.helpButton.addEventListener("click", () => {
  elements.helpDialog.showModal();
});
elements.helpClose.addEventListener("click", () => {
  elements.helpDialog.close();
});
elements.helpDialog.addEventListener("click", (event) => {
  if (event.target === elements.helpDialog) elements.helpDialog.close();
});

loadStatus();
