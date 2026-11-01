const spinePlayer = (() => {
  let appCanvas = null;
  let skeleton = null;
  let animationState = null;
  let currentAnimation = null;
  let facing = 1;
  let ready = false;
  let frames = 0;

  function setAnimation(name) {
    if (!animationState || currentAnimation === name) return;
    currentAnimation = name;
    animationState.setAnimation(0, name, true);
  }

  function setFacing(direction) {
    facing = direction < 0 ? -1 : 1;
    if (skeleton) {
      skeleton.scaleX = facing * 2;
    }
  }

  function initialize() {
    if (typeof spine === "undefined") {
      const fallback = document.querySelector("#map-player-fallback");
      fallback.hidden = false;
      return;
    }
    const canvas = document.querySelector("#map-player-canvas");
    const fallback = document.querySelector("#map-player-fallback");
    try {
      appCanvas = new spine.SpineCanvas(canvas, {
        pathPrefix: "/assets/spine/",
        webglConfig: {
          alpha: true,
          premultipliedAlpha: true,
          antialias: false,
        },
        app: {
          loadAssets(instance) {
            instance.assetManager.loadText("lin_cheng.json");
            instance.assetManager.loadTextureAtlas("lin_cheng.atlas");
          },
          initialize(instance) {
            const atlas = instance.assetManager.require("lin_cheng.atlas");
            const atlasLoader = new spine.AtlasAttachmentLoader(atlas);
            const skeletonJson = new spine.SkeletonJson(atlasLoader);
            const skeletonData = skeletonJson.readSkeletonData(
              instance.assetManager.require("lin_cheng.json"),
            );
            skeleton = new spine.Skeleton(skeletonData);
            skeleton.scaleX = 2;
            skeleton.scaleY = 2;
            skeleton.updateWorldTransform();

            const stateData = new spine.AnimationStateData(skeletonData);
            stateData.setMix("idle", "walk", 0.14);
            stateData.setMix("walk", "idle", 0.16);
            animationState = new spine.AnimationState(stateData);
            animationState.setAnimation(0, "idle", true);
            currentAnimation = "idle";

            instance.renderer.camera.position.x = 0;
            instance.renderer.camera.position.y = 66;
            instance.renderer.camera.setViewport(96, 140);
            instance.renderer.camera.update();
            ready = true;
            document.body.dataset.spineReady = "true";
            window.dispatchEvent(new CustomEvent("qinghe:spine-ready"));
          },
          update(instance, delta) {
            if (!skeleton || !animationState) return;
            animationState.update(delta);
            animationState.apply(skeleton);
            skeleton.updateWorldTransform();
            frames += 1;
            instance.htmlCanvas.dataset.animation = currentAnimation || "";
            instance.htmlCanvas.dataset.spineFrame = String(frames);
          },
          render(instance) {
            instance.clear(0, 0, 0, 0);
            if (!skeleton) return;
            instance.renderer.begin();
            instance.renderer.drawSkeleton(skeleton);
            instance.renderer.end();
          },
          error(instance, errors) {
            console.error("Spine 资源加载失败", errors);
            canvas.hidden = true;
            fallback.hidden = false;
          },
        },
      });
    } catch (error) {
      console.error("Spine 初始化失败", error);
      canvas.hidden = true;
      fallback.hidden = false;
      document.body.dataset.spineReady = "fallback";
    }
  }

  return {
    initialize,
    setAnimation,
    setFacing,
    isReady: () => ready,
    getState: () => {
      const root = skeleton?.bones?.find((bone) => bone.data.name === "root");
      const leftLeg = skeleton?.bones?.find(
        (bone) => bone.data.name === "leg_left",
      );
      const torso = skeleton?.bones?.find(
        (bone) => bone.data.name === "torso",
      );
      return {
        ready,
        animation: currentAnimation,
        facing,
        frames,
        rootY: root?.appliedPose?.y ?? root?.pose?.y ?? null,
        leftLegRotation:
          leftLeg?.rotation
          ?? leftLeg?.appliedPose?.rotation
          ?? leftLeg?.pose?.rotation
          ?? null,
        torsoRotation:
          torso?.rotation
          ?? torso?.appliedPose?.rotation
          ?? torso?.pose?.rotation
          ?? null,
      };
    },
  };
})();

window.qingheSpinePlayer = spinePlayer;
