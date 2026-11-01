const state = {
  world: null,
  agent: null,
  timeline: null,
  memory: null,
  memoryLimit: 20,
};

const BUILDING_ASSETS = {
  loc_dorm: "dorm",
  loc_classroom: "classroom",
  loc_library: "library",
  loc_canteen: "canteen",
  loc_shop: "shop",
  loc_river: "river",
};

const INTERIOR_ASSETS = {
  loc_dorm: "dorm",
  loc_classroom: "classroom",
  loc_library: "library",
  loc_canteen: "canteen",
  loc_shop: "shop",
  loc_river: "river",
};

const INTERIOR_NOTES = {
  loc_dorm: "木地板宿舍里，行李已经收好，书桌边留着今天的小纸条。",
  loc_classroom: "课桌整齐排开，黑板前还留着午后讨论的痕迹。",
  loc_library: "书院的书架层层排开，靠窗的位置最适合安静读完一章。",
  loc_canteen: "热食柜台、长桌和餐椅都准备好了，饭点前显得格外安静。",
  loc_shop: "便利店货架塞得满满的，收银台边放着刚补上的日用品。",
  loc_river: "石桥横过河面，步道边的树影和长椅把傍晚拉得很长。",
};

const SCENE_DIALOGUE = {
  loc_dorm: "宿舍的灯还亮着。晚风把窗边晾着的纸页轻轻翻了一页。",
  loc_classroom: "教学楼前的路灯亮起来了，走廊里还留着放学后的回声。",
  loc_library: "青禾书院很安静，只有靠窗的一盏灯照着尚未合上的书。",
  loc_canteen: "食堂刚结束收拾，空气里还留着一点热汤和米饭的味道。",
  loc_river: "河边传来很轻的水声，石桥上的影子被路灯拉得很长。",
  loc_shop: "便利店的灯箱映在路面上，门铃偶尔响一下，又归于安静。",
};

const MAP_WORLD = {
  width: 2400,
  height: 900,
  playerWidth: 36,
  playerHeight: 54,
  speed: 170,
};

const BUILDING_LAYOUT = {
  loc_dorm: { x: 42, y: 92, width: 360, height: 220 },
  loc_classroom: { x: 610, y: 16, width: 320, height: 315 },
  loc_library: { x: 1350, y: 44, width: 300, height: 280 },
  loc_canteen: { x: 294, y: 510, width: 220, height: 265 },
  loc_river: { x: 1018, y: 656, width: 96, height: 144 },
  loc_shop: { x: 2010, y: 504, width: 180, height: 268 },
};

const LOCATION_STARTS = {
  loc_dorm: { x: 430, y: 338 },
  loc_classroom: { x: 960, y: 338 },
  loc_library: { x: 1510, y: 338 },
  loc_canteen: { x: 530, y: 456 },
  loc_river: { x: 1120, y: 724 },
  loc_shop: { x: 2120, y: 456 },
};

const PORTRAITS = {
  char_lin_cheng: "lin_cheng",
  npc_chen: "chen_lan",
  npc_su: "su_wan",
  npc_gao: "gao_yuan",
  npc_gu: "gu_yan",
};

const elements = {
  loading: document.querySelector("#loading-state"),
  connectionBanner: document.querySelector("#connection-banner"),
  connectionMessage: document.querySelector("#connection-message"),
  retryButton: document.querySelector("#retry-button"),
  serviceStatus: document.querySelector("#service-status"),
  mapStage: document.querySelector(".world-map-stage"),
  worldPlane: document.querySelector("#world-plane"),
  mapPlayer: document.querySelector("#map-player"),
  mapViewLabel: document.querySelector("#map-view-label"),
  sceneDialogueLine: document.querySelector("#scene-dialogue-line"),
  currentLocation: document.querySelector("#current-location"),
  worldName: document.querySelector("#world-name"),
  worldClock: document.querySelector("#world-clock"),
  locations: document.querySelector("#map-locations"),
  mapBuildings: document.querySelector("#map-buildings"),
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
  locationDialog: document.querySelector("#location-dialog"),
  locationDialogClose: document.querySelector("#location-dialog-close"),
  locationDialogTitle: document.querySelector("#location-dialog-title"),
  locationDialogStatus: document.querySelector("#location-dialog-status"),
  locationDialogArt: document.querySelector("#location-dialog-art"),
  locationDialogDescription: document.querySelector("#location-dialog-description"),
  locationDialogPeople: document.querySelector("#location-dialog-people"),
};

const mapState = {
  initialized: false,
  active: new Set(),
  x: 278,
  y: 386,
  lastFrame: 0,
  nearestLocationId: null,
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
  elements.mapBuildings.replaceChildren();
  const mapImage = document.querySelector(".map-background-image");
  mapImage.addEventListener(
    "error",
    () => {
      mapImage.hidden = true;
    },
    { once: true },
  );

  locations.forEach((location, index) => {
    elements.mapBuildings.append(renderMapBuilding(location, world));
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
      createElement("span", "location-open-hint", "查看内部"),
    );
    makeLocationInteractive(card, location);
    elements.locations.append(card);
  });
  initializeMapPlayer(worldPayload);
}

function renderMapBuilding(location, world) {
  const assetName = BUILDING_ASSETS[location.location_id];
  const layout = BUILDING_LAYOUT[location.location_id];
  const card = createElement("article", "map-building");
  card.dataset.location = location.location_id;
  if (layout) {
    card.style.left = `${layout.x}px`;
    card.style.top = `${layout.y}px`;
    card.style.width = `${layout.width}px`;
  }
  if (location.location_id === world.current_location_id) {
    card.classList.add("is-current");
  }
  if (!assetName) {
    card.classList.add("is-missing");
  }

  const image = createElement("img", "map-building-art");
  image.src = assetName
    ? `/assets/buildings/${assetName}.webp`
    : "/assets/icons/brand.png";
  image.alt = `${location.name}像素建筑`;
  image.loading = "eager";
  image.decoding = "async";
  image.addEventListener(
    "error",
    () => {
      card.classList.add("is-missing");
      image.src = "/assets/icons/brand.png";
    },
    { once: true },
  );

  const label = createElement("div", "map-building-label");
  const title = createElement("strong", "", location.name);
  const stateText = createElement(
    "span",
    "",
    location.is_open ? "开放" : "已关闭",
  );
  const statusIcon = createElement("img", "building-status");
  statusIcon.src = location.is_open
    ? "/assets/icons/open.png"
    : "/assets/icons/closed.png";
  statusIcon.alt = "";
  title.textContent = location.name;
  label.append(statusIcon, title, stateText);
  const openHint = createElement("span", "map-building-open", "点击进入");
  card.append(image, label, openHint);
  makeLocationInteractive(card, location);
  return card;
}

function makeLocationInteractive(element, location) {
  element.tabIndex = 0;
  element.setAttribute("role", "button");
  element.setAttribute("aria-label", `查看${location.name}内部`);
  element.addEventListener("click", () => openLocationDialog(location));
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openLocationDialog(location);
    }
  });
}

function openLocationDialog(location) {
  const assetName = INTERIOR_ASSETS[location.location_id] || "dorm";
  elements.locationDialogTitle.textContent = location.name;
  elements.locationDialogStatus.textContent = location.is_open ? "开放中" : "已关闭";
  elements.locationDialogStatus.classList.toggle("is-closed", !location.is_open);
  elements.locationDialogDescription.textContent =
    INTERIOR_NOTES[location.location_id] || "这里保留着小镇今天的一页观察手账。";
  elements.locationDialogPeople.textContent = location.people.length
    ? `此刻在内：${location.people.join("、")}`
    : "此刻无人，只留下安静的场景。";
  elements.locationDialogArt.src = `/assets/interiors/${assetName}.webp`;
  elements.locationDialogArt.alt = `${location.name}内部像素场景`;
  elements.locationDialog.dataset.location = location.location_id;
  document.body.classList.add("has-open-location");
  if (typeof elements.locationDialog.showModal === "function") {
    elements.locationDialog.showModal();
  } else {
    elements.locationDialog.setAttribute("open", "");
  }
}

function closeLocationDialog() {
  if (typeof elements.locationDialog.close === "function") {
    elements.locationDialog.close();
  } else {
    elements.locationDialog.removeAttribute("open");
  }
  document.body.classList.remove("has-open-location");
}

function setMapPlayerPosition(x, y) {
  mapState.x = Math.max(0, Math.min(MAP_WORLD.width - MAP_WORLD.playerWidth, x));
  mapState.y = Math.max(0, Math.min(MAP_WORLD.height - MAP_WORLD.playerHeight, y));
  elements.mapPlayer.style.left = `${mapState.x}px`;
  elements.mapPlayer.style.top = `${mapState.y}px`;
}

function clampCamera(value, viewport, world) {
  return Math.max(0, Math.min(world - viewport, value));
}

function updateMapCamera() {
  if (!elements.mapStage || !elements.worldPlane) return;
  const viewportWidth = elements.mapStage.clientWidth;
  const viewportHeight = elements.mapStage.clientHeight;
  const cameraX = clampCamera(
    mapState.x - viewportWidth * 0.62,
    viewportWidth,
    MAP_WORLD.width,
  );
  const cameraY = clampCamera(
    mapState.y - viewportHeight * 0.72,
    viewportHeight,
    MAP_WORLD.height,
  );
  elements.worldPlane.style.transform =
    `translate3d(${-cameraX}px, ${-cameraY}px, 0)`;
}

function updateMapViewLabel(locations) {
  let nearest = null;
  let nearestDistance = Number.POSITIVE_INFINITY;
  locations.forEach((location) => {
    const layout = BUILDING_LAYOUT[location.location_id];
    if (!layout) return;
    const centerX = layout.x + layout.width / 2;
    const centerY = layout.y + layout.height / 2;
    const distance = Math.hypot(
      centerX - (mapState.x + MAP_WORLD.playerWidth / 2),
      centerY - (mapState.y + MAP_WORLD.playerHeight / 2),
    );
    if (distance < nearestDistance) {
      nearest = location;
      nearestDistance = distance;
    }
  });
  const nextId = nearestDistance < 260 ? nearest?.location_id : null;
  if (nextId === mapState.nearestLocationId) return;
  mapState.nearestLocationId = nextId;
  elements.mapViewLabel.textContent = nextId
    ? `视野 · ${nearest.name}`
    : "视野 · 小镇街口";
  elements.sceneDialogueLine.textContent = nextId
    ? SCENE_DIALOGUE[nextId]
    : "夜色落在小镇的屋檐上，远处只剩几盏还亮着的灯。";
}

function initializeMapPlayer(worldPayload) {
  const { world, locations } = worldPayload;
  if (!mapState.initialized) {
    const start =
      LOCATION_STARTS[world.current_location_id] || LOCATION_STARTS.loc_dorm;
    setMapPlayerPosition(start.x, start.y);
    mapState.initialized = true;
  }
  updateMapCamera();
  updateMapViewLabel(locations);
  document.body.dataset.mapReady = "true";
}

function blockedByBuilding(nextX, nextY) {
  return Object.values(BUILDING_LAYOUT).some(
    (building) =>
      nextX + MAP_WORLD.playerWidth > building.x + 4 &&
      nextX < building.x + building.width - 4 &&
      nextY + MAP_WORLD.playerHeight > building.y + 8 &&
      nextY < building.y + building.height,
  );
}

function mapAnimationFrame(timestamp) {
  if (!mapState.lastFrame) mapState.lastFrame = timestamp;
  const elapsed = Math.min((timestamp - mapState.lastFrame) / 1000, 0.05);
  mapState.lastFrame = timestamp;
  let horizontal = 0;
  let vertical = 0;
  if (mapState.active.has("left")) horizontal -= 1;
  if (mapState.active.has("right")) horizontal += 1;
  if (mapState.active.has("up")) vertical -= 1;
  if (mapState.active.has("down")) vertical += 1;

  if (horizontal || vertical) {
    const length = Math.hypot(horizontal, vertical);
    const step = MAP_WORLD.speed * elapsed;
    const deltaX = (horizontal / length) * step;
    const deltaY = (vertical / length) * step;
    const nextX = mapState.x + deltaX;
    const nextY = mapState.y + deltaY;
    if (!blockedByBuilding(nextX, mapState.y)) {
      mapState.x = nextX;
    }
    if (!blockedByBuilding(mapState.x, nextY)) {
      mapState.y = nextY;
    }
    setMapPlayerPosition(mapState.x, mapState.y);
    updateMapCamera();
    if (state.world) updateMapViewLabel(state.world.locations);
    if (horizontal) {
      window.qingheSpinePlayer?.setFacing(horizontal);
    }
  }
  elements.mapPlayer.classList.toggle(
    "is-moving",
    Boolean(horizontal || vertical),
  );
  window.qingheSpinePlayer?.setAnimation(
    horizontal || vertical ? "walk" : "idle",
  );
  requestAnimationFrame(mapAnimationFrame);
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
  avatar.src = portraitPath(agent.person_id);
  avatar.alt = `${agent.name}像素头像`;
  avatar.addEventListener(
    "error",
    () => {
      avatar.src = "/assets/icons/character.png";
    },
    { once: true },
  );
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
    const identity = createElement("div", "relationship-identity");
    const miniPortrait = createElement("img", "relationship-avatar");
    miniPortrait.src = portraitPath(relationship.person_id);
    miniPortrait.alt = "";
    miniPortrait.addEventListener(
      "error",
      () => {
        miniPortrait.src = "/assets/icons/character.png";
      },
      { once: true },
    );
    const copy = createElement("div");
    copy.append(
      createElement("strong", "", relationship.name),
      createElement("p", "", relationship.recent_context),
    );
    identity.append(miniPortrait, copy);
    row.append(identity, createElement("span", "", relationship.label));
    relationshipList.append(row);
  });
  side.append(relationshipList);
  elements.agentCard.replaceChildren(main, side);
}

function portraitPath(personId) {
  const name = PORTRAITS[personId] || "lin_cheng";
  return `/assets/portraits/${name}.webp`;
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

const MOVE_KEYS = {
  ArrowUp: "up",
  KeyW: "up",
  ArrowDown: "down",
  KeyS: "down",
  ArrowLeft: "left",
  KeyA: "left",
  ArrowRight: "right",
  KeyD: "right",
};

function canMoveMap() {
  return (
    !document.querySelector("#view-map").hidden
    && !elements.locationDialog.open
    && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)
  );
}

window.addEventListener("keydown", (event) => {
  const direction = MOVE_KEYS[event.code];
  if (!direction || !canMoveMap()) return;
  event.preventDefault();
  mapState.active.add(direction);
});

window.addEventListener("keyup", (event) => {
  const direction = MOVE_KEYS[event.code];
  if (direction) mapState.active.delete(direction);
});

window.addEventListener("blur", () => {
  mapState.active.clear();
});

document.querySelectorAll("[data-move]").forEach((button) => {
  const direction = button.dataset.move;
  const stop = () => {
    mapState.active.delete(direction);
    button.classList.remove("is-pressed");
  };
  button.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    mapState.active.add(direction);
    button.classList.add("is-pressed");
  });
  button.addEventListener("pointerup", stop);
  button.addEventListener("pointercancel", stop);
  button.addEventListener("lostpointercapture", stop);
});

window.addEventListener("resize", updateMapCamera);
window.qingheSpinePlayer?.initialize();
requestAnimationFrame(mapAnimationFrame);

elements.locationDialogClose.addEventListener("click", closeLocationDialog);
elements.locationDialog.addEventListener("close", () => {
  document.body.classList.remove("has-open-location");
});
elements.locationDialog.addEventListener("click", (event) => {
  if (event.target === elements.locationDialog) {
    closeLocationDialog();
  }
});
elements.locationDialogArt.addEventListener(
  "error",
  () => {
    elements.locationDialogArt.src = "/assets/icons/brand.png";
  },
  { once: true },
);

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
