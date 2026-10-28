const state = {
  world: null,
  agent: null,
  timeline: null,
  memory: null,
  memoryLimit: 20,
};

const elements = {
  loading: document.querySelector("#loading-state"),
  connectionBanner: document.querySelector("#connection-banner"),
  connectionMessage: document.querySelector("#connection-message"),
  retryButton: document.querySelector("#retry-button"),
  serviceStatus: document.querySelector("#service-status"),
  currentLocation: document.querySelector("#current-location"),
  worldName: document.querySelector("#world-name"),
  worldClock: document.querySelector("#world-clock"),
  locations: document.querySelector("#map-locations"),
  previewIdentity: document.querySelector("#preview-identity"),
  previewMood: document.querySelector("#preview-mood"),
  previewGoal: document.querySelector("#preview-goal"),
  agentCard: document.querySelector("#agent-card"),
  timeline: document.querySelector("#timeline-list"),
  chatForm: document.querySelector("#chat-form"),
  chatMessage: document.querySelector("#chat-message"),
  chatCounter: document.querySelector("#chat-counter"),
  chatSubmit: document.querySelector("#chat-submit"),
  chatStatus: document.querySelector("#chat-status"),
  chatLog: document.querySelector("#chat-log"),
  diary: document.querySelector("#diary-list"),
  memory: document.querySelector("#memory-list"),
  memoryFilter: document.querySelector("#memory-filter"),
  memoryMore: document.querySelector("#memory-more"),
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
    const error = new Error(body?.error?.code || `HTTP_${response.status}`);
    error.code = body?.error?.code || "request_failed";
    throw error;
  }
  return body;
}

function showView(viewName, updateHash = true) {
  const target = document.querySelector(`[data-view-panel="${viewName}"]`);
  if (!target) return;
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    panel.hidden = panel !== target;
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    const active = button.dataset.view === viewName;
    button.classList.toggle("is-active", active);
    if (active) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  });
  if (updateHash) {
    history.replaceState(null, "", `#${viewName}`);
  }
  document.querySelector("#main-content").focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setLoading(loading) {
  elements.loading.hidden = !loading;
  elements.loading.setAttribute("aria-busy", String(loading));
}

function showConnectionError(error) {
  elements.connectionMessage.textContent =
    error.code === "database_unavailable"
      ? "数据库暂时不可用，请稍后重试。"
      : "暂时无法读取小镇数据，请确认本地 API 已启动。";
  elements.connectionBanner.hidden = false;
  elements.serviceStatus.textContent = "连接异常";
}

function clearConnectionError() {
  elements.connectionBanner.hidden = true;
  elements.serviceStatus.textContent = "已连接";
}

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function renderWorld(worldPayload) {
  state.world = worldPayload;
  const { world, locations } = worldPayload;
  elements.worldName.textContent = world.name;
  elements.currentLocation.textContent = `${world.current_location_name} · 当前`;
  elements.worldClock.textContent = `${formatDate(world.current_date)} ${world.current_time}`;
  elements.locations.replaceChildren();

  locations.forEach((location, index) => {
    const card = createElement("article", "location-card");
    if (location.location_id === world.current_location_id) {
      card.classList.add("is-current");
    }
    const topline = createElement("div", "location-topline");
    topline.append(
      createElement("span", "location-index", String(index + 1).padStart(2, "0")),
      createElement("span", "open-state", location.is_open ? "开放" : "已关闭"),
    );
    const people = location.people.length
      ? location.people.join("、")
      : "此刻无人";
    card.append(
      topline,
      createElement("h4", "", location.name),
      createElement("p", "", people),
    );
    elements.locations.append(card);
  });
}

function renderAgent(agentPayload) {
  state.agent = agentPayload;
  const { agent } = agentPayload;
  elements.previewIdentity.textContent = agent.identity;
  elements.previewMood.textContent = agent.mood_label;
  elements.previewGoal.textContent = agent.current_goal.title;

  const main = createElement("article", "character-main");
  const identity = createElement("div", "character-identity");
  const portrait = createElement("div", "portrait portrait-large");
  const avatar = createElement("img");
  avatar.src = "/static/assets/placeholders/avatar.svg";
  avatar.alt = `${agent.name}头像占位图`;
  portrait.append(avatar, createElement("span", "", agent.name.slice(0, 1)));
  const identityText = createElement("div");
  identityText.append(
    createElement("h3", "", agent.name),
    createElement(
      "p",
      "",
      `${agent.age} 岁 · ${agent.identity}`,
    ),
    createElement(
      "p",
      "muted",
      `${agent.location_name} · ${agent.mood_label}`,
    ),
  );
  identity.append(portrait, identityText);

  const goal = createElement("div", "goal-card");
  goal.append(
    createElement("p", "eyebrow", "CURRENT GOAL"),
    createElement("h3", "", agent.current_goal.title),
    createElement(
      "p",
      "",
      `${agent.current_goal.progress_label} · 截止 ${formatDate(agent.current_goal.due_date)}`,
    ),
  );
  main.append(identity, goal);

  const side = createElement("aside", "character-side");
  side.append(createElement("p", "eyebrow", "RELATIONSHIPS"));
  const relationshipList = createElement("div", "relationship-list");
  agent.relationships.forEach((relationship) => {
    const row = createElement("div", "relationship-row");
    const copy = createElement("div");
    copy.append(
      createElement("strong", "", relationship.name),
      createElement("p", "", relationship.recent_context),
    );
    row.append(copy, createElement("span", "", relationship.label));
    relationshipList.append(row);
  });
  side.append(relationshipList);
  elements.agentCard.replaceChildren(main, side);
}

function renderTimeline(timelinePayload) {
  state.timeline = timelinePayload;
  elements.timeline.replaceChildren();
  if (!timelinePayload.items.length) {
    elements.timeline.append(emptyState("时间线还是空的", "有公开事件后会出现在这里。"));
    return;
  }
  timelinePayload.items.forEach((item) => {
    const article = createElement(
      "article",
      `timeline-item${item.kind === "share" ? " is-share" : ""}`,
    );
    const body = createElement("div", "timeline-body");
    body.append(
      createElement("h3", "", item.title),
      createElement("p", "", item.summary),
    );
    const meta = createElement("div", "timeline-meta");
    if (item.location_name) meta.append(createElement("span", "", item.location_name));
    if (item.participants.length) {
      meta.append(createElement("span", "", item.participants.join("、")));
    }
    body.append(meta);
    article.append(
      createElement("time", "timeline-date", formatDateTime(item.occurred_at)),
      createElement("span", "timeline-dot"),
      body,
    );
    elements.timeline.append(article);
  });
}

function renderMemory(memoryPayload) {
  state.memory = memoryPayload;
  elements.memory.replaceChildren();
  if (!memoryPayload.items.length) {
    elements.memory.append(emptyState("还没有可展示的记忆", "安全摘要会逐步积累。"));
  } else {
    memoryPayload.items.forEach((item) => {
      const card = createElement("article", "memory-card");
      card.append(
        createElement("span", "memory-category", item.category),
        createElement("h3", "", formatDate(item.date)),
        createElement("p", "", item.summary),
      );
      elements.memory.append(card);
    });
  }
  elements.memoryMore.hidden = !memoryPayload.next_cursor;

  elements.diary.replaceChildren();
  if (!memoryPayload.diary_summaries.length) {
    elements.diary.append(emptyState("还没有日记摘要", "目前没有可公开的安全摘要。"));
  } else {
    memoryPayload.diary_summaries.forEach((diary) => {
      const card = createElement("article", "diary-card");
      card.append(
        createElement("time", "", formatDate(diary.date)),
        createElement("h3", "", "一周里的一段记录"),
        createElement("p", "", diary.summary),
      );
      elements.diary.append(card);
    });
  }
}

function emptyState(title, copy) {
  const card = createElement("div", "empty-card");
  card.append(createElement("h3", "", title), createElement("p", "", copy));
  return card;
}

function appendChatMessage(text, kind, note) {
  const empty = elements.chatLog.querySelector(".chat-empty");
  if (empty) empty.remove();
  const bubble = createElement(
    "div",
    `chat-message${kind === "observer" ? " is-observer" : ""}`,
  );
  bubble.append(createElement("p", "", text));
  if (note) bubble.append(createElement("small", "", note));
  elements.chatLog.append(bubble);
  elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
}

function formatDate(dateText) {
  const date = new Date(`${dateText}T00:00:00+08:00`);
  return new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    weekday: "short",
  }).format(date);
}

function formatDateTime(dateText) {
  const date = new Date(dateText);
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

async function loadDashboard() {
  setLoading(true);
  clearConnectionError();
  try {
    const [world, agent, timeline, memory] = await Promise.all([
      fetchJSON("/world"),
      fetchJSON("/agent"),
      fetchJSON("/timeline?limit=50"),
      fetchJSON("/memory?limit=20"),
    ]);
    renderWorld(world);
    renderAgent(agent);
    renderTimeline(timeline);
    renderMemory(memory);
    document.body.dataset.ready = "true";
  } catch (error) {
    showConnectionError(error);
  } finally {
    setLoading(false);
  }
}

elements.retryButton.addEventListener("click", loadDashboard);
document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => showView(button.dataset.view));
});

elements.chatMessage.addEventListener("input", () => {
  elements.chatCounter.textContent = `${elements.chatMessage.value.length} / 280`;
});

elements.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = elements.chatMessage.value.trim();
  if (!message) return;
  elements.chatSubmit.disabled = true;
  elements.chatSubmit.textContent = "审核中…";
  elements.chatStatus.classList.remove("is-error");
  elements.chatStatus.textContent = "正在提交并检查留言…";
  try {
    const response = await fetchJSON("/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    appendChatMessage(response.visible_message, "observer", "已排队");
    appendChatMessage(response.reply, "resident", "系统答复");
    elements.chatMessage.value = "";
    elements.chatCounter.textContent = "0 / 280";
    elements.chatStatus.textContent = "留言已排队，不会立即改变世界。";
  } catch (error) {
    elements.chatStatus.classList.add("is-error");
    elements.chatStatus.textContent =
      error.code === "content_policy_blocked"
        ? "留言未通过审核，请换一种表达。"
        : "留言发送失败，请检查连接后重试。";
  } finally {
    elements.chatSubmit.disabled = false;
    elements.chatSubmit.textContent = "发送留言";
  }
});

elements.memoryFilter.addEventListener("change", async () => {
  const kind = elements.memoryFilter.value;
  const query = new URLSearchParams({ limit: String(state.memoryLimit) });
  if (kind) query.set("kind", kind);
  try {
    renderMemory(await fetchJSON(`/memory?${query.toString()}`));
  } catch (error) {
    showConnectionError(error);
  }
});

elements.memoryMore.addEventListener("click", async () => {
  state.memoryLimit = Math.min(50, state.memoryLimit + 20);
  const kind = elements.memoryFilter.value;
  const query = new URLSearchParams({ limit: String(state.memoryLimit) });
  if (kind) query.set("kind", kind);
  try {
    renderMemory(await fetchJSON(`/memory?${query.toString()}`));
  } catch (error) {
    showConnectionError(error);
  }
});

document.querySelectorAll("img").forEach((image) => {
  image.addEventListener("error", () => {
    image.hidden = true;
  });
});

const initialView = location.hash.replace("#", "") || "map";
showView(initialView, false);
loadDashboard();
