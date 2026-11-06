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
  personaPanel: document.querySelector("#persona-panel"),
  personaSummary: document.querySelector("#persona-summary"),
  personaStatus: document.querySelector("#persona-status"),
  personaRevision: document.querySelector("#persona-revision"),
  personaActions: document.querySelector("#persona-actions"),
  defaultPersona: document.querySelector("#default-persona-button"),
  customPersona: document.querySelector("#custom-persona-button"),
  replacePersona: document.querySelector("#replace-persona-button"),
  personaForm: document.querySelector("#persona-form"),
  personaFormStatus: document.querySelector("#persona-form-status"),
  cancelPersona: document.querySelector("#cancel-persona-button"),
  helpButton: document.querySelector("#help-button"),
  helpDialog: document.querySelector("#help-dialog"),
  helpClose: document.querySelector("#help-close"),
};

const personaInputs = {
  name: document.querySelector("#persona-name"),
  pronouns: document.querySelector("#persona-pronouns"),
  age: document.querySelector("#persona-age"),
  appearance: document.querySelector("#persona-appearance"),
  identity: document.querySelector("#persona-identity"),
  speech_style: document.querySelector("#persona-speech"),
  traits: document.querySelector("#persona-traits"),
  values: document.querySelector("#persona-values"),
  interests: document.querySelector("#persona-interests"),
  initial_goals: document.querySelector("#persona-goals"),
  boundaries: document.querySelector("#persona-boundaries"),
  relationship_to_player: document.querySelector("#persona-relationship"),
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
  setup_acl_failed: "无法保护 Key 文件，请检查服务账户权限。",
  persona_not_configured: "请先选择或保存角色人设。",
  invalid_persona: "人设字段不符合要求，请检查长度和年龄。",
  persona_prompt_injection: "人设包含试图改写系统规则的表达，请修改。",
};

let setupState = null;
let personaState = null;

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

function setPersonaStatus(message, kind = "") {
  elements.personaFormStatus.textContent = message;
  elements.personaFormStatus.classList.toggle("is-error", kind === "error");
  elements.personaFormStatus.classList.toggle("is-success", kind === "success");
}

function setBusy(busy) {
  document.querySelectorAll("button").forEach((button) => {
    button.disabled = busy;
  });
}

function clearKeyInput() {
  elements.key.value = "";
}

function renderStatus(status, persona) {
  setupState = status;
  personaState = persona;
  const configured = status.configured;
  const personaConfigured = status.persona_configured;
  const hasPersonaId = persona.is_default
    ? "默认人设"
    : `自定义人设 ${persona.name || ""}`.trim();

  elements.form.hidden = configured;
  elements.configuredPanel.hidden = !configured;
  elements.personaPanel.hidden = !configured;
  elements.personaForm.hidden = true;
  elements.defaultPersona.hidden = personaConfigured;
  elements.customPersona.hidden = personaConfigured;
  elements.replacePersona.hidden = !personaConfigured;
  elements.personaActions.hidden = false;
  elements.continueButton.hidden = !status.world_ready;

  if (!configured) {
    setStatus("尚未配置 DeepSeek Key。");
    return;
  }
  elements.configuredCopy.textContent =
    `已配置 ${status.provider} · ${status.key_hint || "sk-..."}`;
  elements.personaRevision.textContent =
    personaConfigured ? `REVISION ${persona.revision}` : "";
  if (personaConfigured) {
    elements.personaSummary.hidden = false;
    elements.personaSummary.replaceChildren();
    const title = document.createElement("strong");
    title.textContent = persona.name || "角色";
    elements.personaSummary.append(
      title,
      document.createTextNode(
        ` · ${hasPersonaId} · revision ${persona.revision}`,
      ),
    );
    elements.personaStatus.textContent =
      "人设已保存。替换基础人设会保留当前世界、关系、记忆和位置。";
  } else {
    elements.personaSummary.hidden = true;
    elements.personaStatus.textContent =
      "请选择默认人设，或创建一个原创角色。";
  }
  setStatus(
    status.world_ready
      ? "设置完成，可以进入青禾镇。"
      : personaConfigured
        ? "人设已保存，请完成设置。"
        : "Key 已保存，请选择角色人设。",
    "success",
  );
}

async function loadStatus() {
  try {
    const [status, persona] = await Promise.all([
      fetchJSON("/api/setup/status"),
      fetchJSON("/api/persona/status"),
    ]);
    renderStatus(status, persona);
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
    await requestWithKey("/api/setup/deepseek/save", key);
    setStatus("Key 已安全保存。请选择角色人设。", "success");
    await loadStatus();
    elements.defaultPersona.focus();
  } catch (error) {
    setStatus(errorCopy[error.code] || "保存失败，请重试。", "error");
  } finally {
    clearKeyInput();
    setBusy(false);
  }
}

async function completeAndEnter() {
  const status = await fetchJSON("/api/setup/complete", {
    method: "POST",
    body: JSON.stringify({}),
  });
  renderStatus(status, personaState);
  window.location.assign("/");
}

async function useDefaultPersona() {
  setBusy(true);
  setStatus("正在保存默认人设…");
  try {
    const persona = await fetchJSON("/api/persona/default", {
      method: "POST",
      body: JSON.stringify({}),
    });
    personaState = {
      configured: true,
      revision: persona.baseline_revision,
      name: persona.baseline.name,
      is_default: true,
    };
    await completeAndEnter();
  } catch (error) {
    setStatus(errorCopy[error.code] || "保存默认人设失败。", "error");
  } finally {
    setBusy(false);
  }
}

function splitList(value) {
  return value
    .split(/[,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function personaPayload() {
  return {
    name: personaInputs.name.value.trim(),
    pronouns: personaInputs.pronouns.value.trim(),
    age: Number(personaInputs.age.value),
    appearance: personaInputs.appearance.value.trim(),
    identity: personaInputs.identity.value.trim(),
    speech_style: personaInputs.speech_style.value.trim(),
    traits: splitList(personaInputs.traits.value),
    values: splitList(personaInputs.values.value),
    interests: splitList(personaInputs.interests.value),
    initial_goals: splitList(personaInputs.initial_goals.value),
    boundaries: splitList(personaInputs.boundaries.value),
    relationship_to_player:
      personaInputs.relationship_to_player.value.trim(),
  };
}

function showPersonaForm() {
  elements.personaForm.hidden = false;
  elements.personaActions.hidden = true;
  setPersonaStatus("");
  personaInputs.name.focus();
}

async function saveCustomPersona(event) {
  event.preventDefault();
  setBusy(true);
  setPersonaStatus("正在保存自定义人设…");
  try {
    const persona = await fetchJSON("/api/persona/baseline", {
      method: "PUT",
      body: JSON.stringify(personaPayload()),
    });
    personaState = {
      configured: true,
      revision: persona.baseline_revision,
      name: persona.baseline.name,
      is_default: persona.baseline.is_default,
    };
    await completeAndEnter();
  } catch (error) {
    setPersonaStatus(
      errorCopy[error.code] || "人设保存失败，请检查字段后重试。",
      "error",
    );
  } finally {
    setBusy(false);
  }
}

async function completeSetup() {
  setBusy(true);
  try {
    await completeAndEnter();
  } catch (error) {
    setStatus(errorCopy[error.code] || "无法完成设置，请稍后重试。", "error");
  } finally {
    setBusy(false);
  }
}

async function clearKey() {
  if (!window.confirm("清除 DeepSeek Key？世界、人设和角色数据不会因此清空。")) {
    return;
  }
  setBusy(true);
  try {
    await fetchJSON("/api/setup/deepseek/clear", {
      method: "POST",
      body: JSON.stringify({}),
    });
    await loadStatus();
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
elements.defaultPersona.addEventListener("click", useDefaultPersona);
elements.customPersona.addEventListener("click", showPersonaForm);
elements.replacePersona.addEventListener("click", showPersonaForm);
elements.cancelPersona.addEventListener("click", () => {
  elements.personaForm.hidden = true;
  elements.personaActions.hidden = false;
});
elements.personaForm.addEventListener("submit", saveCustomPersona);
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
