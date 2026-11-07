const characterPlayer = (() => {
  const allowedDirections = new Set(["down", "left", "right", "up"]);
  let manifest = null;
  let ready = false;
  let failed = false;
  let direction = "down";
  let previousDirection = "down";
  let previousMoving = false;
  let action = "idle";
  let frame = 0;
  let elapsed = 0;
  let sequenceFinished = true;
  let element = null;
  let fallback = null;

  function asset(actionName, directionName) {
    return manifest.directions[directionName][actionName];
  }

  function applyFrame() {
    if (!ready || !manifest || !element) return;
    const current = asset(action, direction);
    element.style.backgroundImage = `url("/${current.path}")`;
    element.style.backgroundSize =
      `${current.frames * manifest.runtime_display.width}px `
      + `${manifest.runtime_display.height}px`;
    element.style.backgroundPosition =
      `-${frame * manifest.runtime_display.width}px 0`;
    element.dataset.direction = direction;
    element.dataset.action = action;
    element.dataset.frame = String(frame);
  }

  function begin(actionName, directionName, { once = false } = {}) {
    action = actionName;
    direction = directionName;
    frame = 0;
    elapsed = 0;
    sequenceFinished = !once;
    applyFrame();
  }

  function transition(desiredAction, desiredDirection) {
    if (
      !previousMoving
      && previousDirection !== desiredDirection
      && sequenceFinished
    ) {
      begin("turn", desiredDirection, { once: true });
      return;
    }
    if (previousMoving && !desiredAction.includes("walk")) {
      begin("stop", desiredDirection, { once: true });
      return;
    }
    if (action !== desiredAction || direction !== desiredDirection) {
      begin(desiredAction, desiredDirection);
    }
  }

  async function initialize() {
    element = document.querySelector("#map-player-sprite");
    fallback = document.querySelector("#map-player-fallback");
    if (!element) return;
    try {
      const response = await fetch(
        "/assets/characters/whale-girl/whale-girl-manifest.json",
        { headers: { Accept: "application/json" } },
      );
      if (!response.ok) throw new Error("character manifest unavailable");
      manifest = await response.json();
      const paths = new Set();
      Object.values(manifest.directions).forEach((byAction) => {
        Object.values(byAction).forEach((item) => paths.add(item.path));
      });
      await Promise.all(
        [...paths].map(
          (source) =>
            new Promise((resolve, reject) => {
              const image = new Image();
              image.onload = resolve;
              image.onerror = reject;
              image.src = `/${source}`;
            }),
        ),
      );
      ready = true;
      element.hidden = false;
      if (fallback) fallback.hidden = true;
      document.body.dataset.characterPlayer = "ready";
      begin("idle", "down");
      window.dispatchEvent(new CustomEvent("qinghe:character-ready"));
    } catch (error) {
      failed = true;
      element.hidden = true;
      if (fallback) fallback.hidden = false;
      document.body.dataset.characterPlayer = "fallback";
      console.error("角色精灵加载失败", error);
    }
  }

  function update(deltaMs, presence, reducedMotion = false) {
    if (!ready || !manifest || !presence) return;
    const desiredDirection = allowedDirections.has(presence.facing)
      ? presence.facing
      : "down";
    let desiredAction = "idle";
    if (presence.moving && presence.animation === "walk") {
      desiredAction = "walk";
    } else if (["study", "sit"].includes(presence.animation)) {
      desiredAction = "study";
    }
    if (reducedMotion) {
      if (action !== "idle" || direction !== desiredDirection) {
        begin("idle", desiredDirection);
      }
      previousDirection = desiredDirection;
      previousMoving = Boolean(presence.moving);
      return;
    }
    if (sequenceFinished) {
      transition(desiredAction, desiredDirection);
    }
    const current = asset(action, direction);
    elapsed += Math.max(0, deltaMs);
    const frameDuration = 1000 / current.fps;
    while (elapsed >= frameDuration) {
      elapsed -= frameDuration;
      frame += 1;
      if (frame >= current.frames) {
        if (current.loop) {
          frame = 0;
        } else {
          frame = 0;
          action = "idle";
          sequenceFinished = true;
          applyFrame();
        }
      }
      applyFrame();
    }
    previousDirection = desiredDirection;
    previousMoving = Boolean(presence.moving);
  }

  return {
    initialize,
    update,
    isReady: () => ready,
    isFailed: () => failed,
    getState: () => ({
      ready,
      failed,
      action,
      direction,
      frame,
      sequenceFinished,
    }),
  };
})();

window.qingheCharacterPlayer = characterPlayer;
