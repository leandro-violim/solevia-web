/* Sole Via Entertainment — site interactions
   1. Bubble-wrap sheet (hero)       — real Zen Bubbles sprites + pop sounds
   2. Screenshot carousels (games)   — tabs, autoplay in view, swipe, arrow keys
   3. "Try a flick" mini pitch       — Cap Kickers flick physics on <canvas>
   4. Language switch                — remembers the visitor's choice
   5. Small things                   — header border on scroll, footer year
*/
(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Resolve assets from this script's own URL so /pt/ and /es/ pages load them correctly.
  const SCRIPT = document.currentScript || document.querySelector('script[src*="assets/js/site.js"]');
  const BASE = new URL("../../", SCRIPT ? SCRIPT.src : location.href).href;
  const asset = (path) => BASE + path;

  // Localized UI strings, rendered into the page by tools/build.py (English fallback).
  const T = Object.assign({
    pop_bubble: "Pop bubble", popped_bubble: "Popped bubble",
    m1: "There it is.", m5: "Oddly satisfying, right?", m15: "Halfway through the sheet.",
    m45: "You would like Zen Bubbles.", m100: "Okay, you really like Zen Bubbles.",
    cleared: "Sheet cleared — here’s a fresh one.", sound_on: "Sound on", sound_off: "Sound off",
    flick_nice: "Nice. Now beat the keeper — he never stops moving.", goal: "GOAL!",
  }, (() => {
    try { return JSON.parse(document.getElementById("sv-strings").textContent); } catch (_) { return {}; }
  })());
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ------------------------------------------------------------------ */
  /* Audio: tiny Web Audio sampler, unlocked on first user gesture       */
  /* ------------------------------------------------------------------ */
  const Sound = (() => {
    const files = ["assets/audio/pop-1.mp3", "assets/audio/pop-2.mp3", "assets/audio/pop-3.mp3"].map(asset);
    let ctx = null;
    let buffers = [];
    let loading = null;
    let enabled = true;

    function load() {
      if (loading) return loading;
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return Promise.resolve();
      ctx = new AC();
      loading = Promise.all(
        files.map((f) =>
          fetch(f)
            .then((r) => r.arrayBuffer())
            .then((b) => new Promise((res, rej) => ctx.decodeAudioData(b, res, rej)))
            .catch(() => null)
        )
      ).then((list) => { buffers = list.filter(Boolean); });
      return loading;
    }

    function pop() {
      if (!enabled) return;
      load().then(() => {
        if (!ctx || !buffers.length) return;
        if (ctx.state === "suspended") ctx.resume();
        const src = ctx.createBufferSource();
        src.buffer = buffers[(Math.random() * buffers.length) | 0];
        src.playbackRate.value = 0.9 + Math.random() * 0.25;
        const gain = ctx.createGain();
        gain.gain.value = 0.85;
        src.connect(gain).connect(ctx.destination);
        src.start();
      });
    }

    return {
      prime: load,
      pop,
      get enabled() { return enabled; },
      set enabled(v) { enabled = v; },
    };
  })();

  function haptic(ms = 8) {
    if (navigator.vibrate) { try { navigator.vibrate(ms); } catch (_) { /* ignore */ } }
  }

  /* ------------------------------------------------------------------ */
  /* 1. Bubble-wrap sheet                                                */
  /* ------------------------------------------------------------------ */
  function initSheet() {
    const sheet = $("#wrap-sheet");
    if (!sheet) return;
    const countEl = $("#pop-count");
    const msgEl = $("#pop-msg");
    const soundBtn = $("#sound-toggle");
    const COLS = 6, ROWS = 5, N = COLS * ROWS;
    const FULL = asset("assets/img/fx/bubble.webp");
    const POPPED = asset("assets/img/fx/bubble-popped.webp");

    // Preload the popped sprite so the swap is instant.
    new Image().src = POPPED;

    let total = 0;
    let left = N;
    let dragging = false;

    const messages = { 1: T.m1, 5: T.m5, 15: T.m15, 45: T.m45, 100: T.m100 };

    function build(animate) {
      sheet.innerHTML = "";
      const frag = document.createDocumentFragment();
      for (let i = 0; i < N; i++) {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "bubble" + (animate ? " is-fresh" : "");
        if (animate) b.style.setProperty("--d", ((i % COLS) + Math.floor(i / COLS)) * 28 + "ms");
        b.setAttribute("aria-label", T.pop_bubble);
        const img = document.createElement("img");
        img.src = FULL; img.alt = ""; img.width = 96; img.height = 96; img.decoding = "async";
        b.appendChild(img);
        frag.appendChild(b);
      }
      sheet.appendChild(frag);
      left = N;
    }

    function pop(b) {
      if (!b || b.classList.contains("is-popped")) return;
      b.classList.add("is-popped", "is-popping");
      b.querySelector("img").src = POPPED;
      b.setAttribute("aria-label", T.popped_bubble);
      b.disabled = true;
      b.addEventListener("animationend", () => b.classList.remove("is-popping"), { once: true });
      Sound.pop();
      haptic();
      total++; left--;
      countEl.textContent = total;
      if (messages[total]) msgEl.textContent = messages[total];
      if (left === 0) {
        msgEl.textContent = T.cleared;
        setTimeout(() => build(true), 900);
      }
    }

    sheet.addEventListener("pointerdown", (e) => {
      Sound.prime();
      const b = e.target.closest(".bubble");
      if (b) { e.preventDefault(); pop(b); }
      if (e.pointerType === "mouse") dragging = true;
    });
    // Mouse users can drag across the sheet to pop a row, like the real thing.
    sheet.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const el = document.elementFromPoint(e.clientX, e.clientY);
      const b = el && el.closest && el.closest(".bubble");
      if (b && sheet.contains(b)) pop(b);
    });
    window.addEventListener("pointerup", () => { dragging = false; });
    // Keyboard: Enter/Space triggers click with detail 0.
    sheet.addEventListener("click", (e) => {
      if (e.detail !== 0) return;
      pop(e.target.closest(".bubble"));
    });

    soundBtn.addEventListener("click", () => {
      Sound.enabled = !Sound.enabled;
      soundBtn.setAttribute("aria-pressed", String(Sound.enabled));
      soundBtn.textContent = Sound.enabled ? T.sound_on : T.sound_off;
    });

    build(false);
  }

  /* ------------------------------------------------------------------ */
  /* 2. Screenshot carousels                                             */
  /* ------------------------------------------------------------------ */
  function initCarousels() {
    $$("[data-carousel]").forEach((root) => {
      const shots = $$(".shot", root);
      const tabs = $$('[role="tab"]', root);
      const screen = $(".phone-screen", root);
      const interval = parseInt(root.dataset.interval, 10) || 4000;
      root.style.setProperty("--interval", interval + "ms");
      let index = 0, timer = null, inView = false, hovered = false;

      function show(i, fromUser) {
        index = (i + shots.length) % shots.length;
        shots.forEach((s, k) => s.classList.toggle("is-active", k === index));
        tabs.forEach((t, k) => {
          t.setAttribute("aria-selected", String(k === index));
          t.tabIndex = k === index ? 0 : -1;
        });
        // Warm the next image so the crossfade never waits on the network.
        const next = shots[(index + 1) % shots.length];
        if (next && next.loading === "lazy") next.loading = "eager";
        if (fromUser) restart();
      }

      function stop() { clearInterval(timer); timer = null; root.classList.remove("is-playing"); }
      function start() {
        if (reduceMotion || timer || !inView || hovered || document.hidden) return;
        root.classList.add("is-playing");
        timer = setInterval(() => show(index + 1), interval);
      }
      function restart() {
        stop();
        // Re-trigger the progress bar animation on the selected tab.
        void root.offsetWidth;
        start();
      }

      tabs.forEach((t, k) => {
        t.addEventListener("click", () => show(k, true));
        t.addEventListener("keydown", (e) => {
          if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
            e.preventDefault();
            show(index + (e.key === "ArrowRight" ? 1 : -1), true);
            tabs[index].focus();
          }
        });
      });

      // Swipe on the phone screen.
      let sx = null, sy = null;
      screen.addEventListener("pointerdown", (e) => { sx = e.clientX; sy = e.clientY; });
      screen.addEventListener("pointerup", (e) => {
        if (sx === null) return;
        const dx = e.clientX - sx, dy = e.clientY - sy;
        if (Math.abs(dx) > 36 && Math.abs(dx) > Math.abs(dy)) show(index + (dx < 0 ? 1 : -1), true);
        else if (Math.abs(dx) < 6 && Math.abs(dy) < 6) show(index + 1, true); // tap = next
        sx = sy = null;
      });

      root.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") { hovered = true; stop(); } });
      root.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") { hovered = false; start(); } });
      document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));

      if ("IntersectionObserver" in window) {
        new IntersectionObserver((entries) => {
          inView = entries[0].isIntersecting;
          inView ? start() : stop();
        }, { threshold: 0.35 }).observe(root);
      } else { inView = true; start(); }

      show(0);
    });
  }

  /* ------------------------------------------------------------------ */
  /* 3. "Try a flick" — a tiny Cap Kickers pitch                         */
  /* ------------------------------------------------------------------ */
  function initFlick() {
    const canvas = $("#flick-canvas");
    if (!canvas || !canvas.getContext) return;
    const ctx = canvas.getContext("2d");
    const goalsEl = $("#flick-goals");
    const shotsEl = $("#flick-shots");
    const hintEl = $("#flick-hint");

    const capImg = new Image(); capImg.src = asset("assets/img/fx/cap-soda-blue.webp");
    const keeperImg = new Image(); keeperImg.src = asset("assets/img/fx/cap-keeper.webp");

    const M = 14;               // pitch margin
    let W = 0, H = 0, dpr = 1;
    let r = 18;                 // cap radius
    let goalX = 0, goalDepth = 28, mouth = 110;
    const cap = { x: 0, y: 0, vx: 0, vy: 0, spin: 0, resting: true };
    const keeper = { x: 0, y: 0, r: 18 };
    let goals = 0, shots = 0;
    let goalFlash = 0;          // seconds remaining for GOAL! banner
    let resetTimer = 0;         // seconds until the cap returns
    let t = 0, last = 0, running = false, visible = false;
    let drag = null;            // { id, samples: [{x,y,t}] }
    let hinted = false;

    function layout() {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = rect.width; H = rect.height;
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      r = Math.max(13, Math.min(22, H * 0.075));
      keeper.r = r * 1.05;
      goalDepth = Math.max(20, r * 1.4);
      goalX = W - M - goalDepth;
      mouth = Math.min(H * 0.46, 132);
      keeper.x = goalX - r * 1.7;
      keeper.y = H / 2;
      resetCap();
    }

    function resetCap() {
      cap.x = Math.max(M + r * 2, W * 0.2); cap.y = H / 2;
      cap.vx = cap.vy = 0; cap.resting = true; resetTimer = 0;
    }

    /* ---- input ---- */
    function toLocal(e) {
      const rect = canvas.getBoundingClientRect();
      return { x: e.clientX - rect.left, y: e.clientY - rect.top, t: performance.now() };
    }
    canvas.addEventListener("pointerdown", (e) => {
      if (!cap.resting) return;
      const p = toLocal(e);
      if (Math.hypot(p.x - cap.x, p.y - cap.y) > r * 3.2) return;
      drag = { id: e.pointerId, samples: [p] };
      canvas.setPointerCapture(e.pointerId);
      canvas.classList.add("is-dragging");
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const p = toLocal(e);
      drag.samples.push(p);
      while (drag.samples.length > 2 && p.t - drag.samples[0].t > 90) drag.samples.shift();
    });
    function release(e) {
      if (!drag || e.pointerId !== drag.id) return;
      const p = toLocal(e);
      drag.samples.push(p);
      const a = drag.samples[0];
      const dt = Math.max(16, p.t - a.t) / 1000;
      let vx = (p.x - a.x) / dt, vy = (p.y - a.y) / dt;
      const speed = Math.hypot(vx, vy);
      const max = Math.max(900, W * 2.1);
      if (speed > max) { vx *= max / speed; vy *= max / speed; }
      drag = null;
      canvas.classList.remove("is-dragging");
      if (speed < 70) return; // a nudge, not a flick
      cap.vx = vx; cap.vy = vy; cap.resting = false;
      shots++; shotsEl.textContent = shots;
      if (!hinted) { hinted = true; hintEl.textContent = T.flick_nice; }
      haptic(6);
    }
    canvas.addEventListener("pointerup", release);
    canvas.addEventListener("pointercancel", release);

    /* ---- physics ---- */
    function step(dt) {
      t += dt;
      const top = H / 2 - mouth / 2, bot = H / 2 + mouth / 2;
      const swing = mouth / 2 - keeper.r * 0.55;
      keeper.y = H / 2 + Math.sin(t * (reduceMotion ? 0.8 : 1.7)) * swing;

      if (goalFlash > 0) goalFlash -= dt;
      if (resetTimer > 0) { resetTimer -= dt; if (resetTimer <= 0) resetCap(); }
      if (cap.resting) return;

      cap.x += cap.vx * dt; cap.y += cap.vy * dt;
      const decay = Math.exp(-1.35 * dt);
      cap.vx *= decay; cap.vy *= decay;
      cap.spin += Math.hypot(cap.vx, cap.vy) * dt / r;

      const inGoal = cap.x > goalX;
      // top / bottom walls (inside the goal they are the net's side panels)
      const yMin = inGoal ? top + r : M + r, yMax = inGoal ? bot - r : H - M - r;
      if (cap.y < yMin) { cap.y = yMin; cap.vy = Math.abs(cap.vy) * 0.7; }
      if (cap.y > yMax) { cap.y = yMax; cap.vy = -Math.abs(cap.vy) * 0.7; }
      if (cap.x < M + r) { cap.x = M + r; cap.vx = Math.abs(cap.vx) * 0.7; }
      // goal line: open only between the posts
      if (!inGoal && cap.x > goalX - r) {
        const between = cap.y > top + r * 0.35 && cap.y < bot - r * 0.35;
        if (!between) { cap.x = goalX - r; cap.vx = -Math.abs(cap.vx) * 0.6; }
      }
      if (cap.x > W - M - r) { cap.x = W - M - r; cap.vx = -Math.abs(cap.vx) * 0.25; }

      // keeper (kinematic circle)
      const dx = cap.x - keeper.x, dy = cap.y - keeper.y, d = Math.hypot(dx, dy), minD = r + keeper.r;
      if (d < minD && d > 0) {
        const nx = dx / d, ny = dy / d;
        cap.x = keeper.x + nx * minD; cap.y = keeper.y + ny * minD;
        const vn = cap.vx * nx + cap.vy * ny;
        if (vn < 0) { cap.vx -= 1.8 * vn * nx; cap.vy -= 1.8 * vn * ny; }
      }

      // scored?
      if (cap.x - r * 0.2 > goalX && resetTimer <= 0 && goalFlash <= 0) {
        goals++; goalsEl.textContent = goals;
        goalFlash = 1.2; resetTimer = 1.25;
        haptic(20);
      }
      // stopped?
      if (Math.hypot(cap.vx, cap.vy) < 9) {
        cap.vx = cap.vy = 0;
        if (resetTimer <= 0) resetTimer = 0.6;
      }
    }

    /* ---- drawing ---- */
    function drawPitch() {
      const stripes = 10, sw = W / stripes;
      for (let i = 0; i < stripes; i++) {
        ctx.fillStyle = i % 2 ? "#2F8A4B" : "#2A7F45";
        ctx.fillRect(i * sw, 0, sw + 1, H);
      }
      ctx.strokeStyle = "rgba(255,255,255,0.78)";
      ctx.lineWidth = 2;
      ctx.strokeRect(M, M, goalX - M, H - M * 2);
      // halfway line + centre circle
      const cx = Math.max(M + 40, W * 0.34);
      ctx.beginPath(); ctx.moveTo(cx, M); ctx.lineTo(cx, H - M); ctx.stroke();
      ctx.beginPath(); ctx.arc(cx, H / 2, Math.min(H * 0.2, 56), 0, Math.PI * 2); ctx.stroke();
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.beginPath(); ctx.arc(cx, H / 2, 3, 0, Math.PI * 2); ctx.fill();
      // penalty + goal boxes
      const bh = Math.min(H * 0.74, mouth * 2.3), bw = Math.min(W * 0.18, bh * 0.55);
      ctx.strokeRect(goalX - bw, H / 2 - bh / 2, bw, bh);
      const sh = mouth * 1.35, swd = bw * 0.4;
      ctx.strokeRect(goalX - swd, H / 2 - sh / 2, swd, sh);
      ctx.beginPath(); ctx.arc(goalX - bw * 0.72, H / 2, 2.5, 0, Math.PI * 2); ctx.fill();
      // net
      const top = H / 2 - mouth / 2;
      ctx.fillStyle = "rgba(255,255,255,0.13)";
      ctx.fillRect(goalX, top, goalDepth, mouth);
      ctx.save();
      ctx.beginPath(); ctx.rect(goalX, top, goalDepth, mouth); ctx.clip();
      ctx.strokeStyle = "rgba(255,255,255,0.35)"; ctx.lineWidth = 1;
      for (let k = -mouth; k < goalDepth + mouth; k += 7) {
        ctx.beginPath(); ctx.moveTo(goalX + k, top); ctx.lineTo(goalX + k - mouth, top + mouth); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(goalX + k - mouth, top); ctx.lineTo(goalX + k, top + mouth); ctx.stroke();
      }
      ctx.restore();
      ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 3.5;
      ctx.beginPath();
      ctx.moveTo(goalX, top); ctx.lineTo(goalX + goalDepth, top); ctx.lineTo(goalX + goalDepth, top + mouth); ctx.lineTo(goalX, top + mouth);
      ctx.stroke();
    }

    function drawDisc(img, x, y, rad, rot) {
      ctx.fillStyle = "rgba(0,0,0,0.28)";
      ctx.beginPath(); ctx.ellipse(x + rad * 0.18, y + rad * 0.32, rad * 1.02, rad * 0.9, 0, 0, Math.PI * 2); ctx.fill();
      if (img.complete && img.naturalWidth) {
        ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
        ctx.drawImage(img, -rad * 1.12, -rad * 1.12, rad * 2.24, rad * 2.24);
        ctx.restore();
      } else {
        ctx.fillStyle = "#1E4FD8"; ctx.beginPath(); ctx.arc(x, y, rad, 0, Math.PI * 2); ctx.fill();
      }
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);
      drawPitch();
      drawDisc(keeperImg, keeper.x, keeper.y, keeper.r, 0);
      // resting cue: soft pulsing ring
      if (cap.resting && !drag) {
        const pr = r * (1.5 + 0.25 * Math.sin(t * 4));
        ctx.strokeStyle = "rgba(255,210,63,0.9)"; ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.arc(cap.x, cap.y, pr, 0, Math.PI * 2); ctx.stroke();
      }
      drawDisc(capImg, cap.x, cap.y, r, cap.spin);
      if (goalFlash > 0) {
        const k = Math.min(1, (1.2 - goalFlash) * 6);
        ctx.save();
        ctx.globalAlpha = Math.min(1, goalFlash * 3);
        ctx.translate(W * 0.55, H / 2); ctx.scale(0.8 + 0.2 * k, 0.8 + 0.2 * k);
        ctx.font = `400 ${Math.round(Math.min(64, H * 0.24))}px "Young Serif", Georgia, serif`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillStyle = "rgba(0,0,0,0.35)"; ctx.fillText(T.goal, 3, 4);
        ctx.fillStyle = "#FFD23F"; ctx.fillText(T.goal, 0, 0);
        ctx.restore();
      }
    }

    function frame(now) {
      if (!running) return;
      const dt = Math.min(0.033, (now - last) / 1000 || 0.016);
      last = now;
      step(dt); draw();
      requestAnimationFrame(frame);
    }
    function play() { if (running) return; running = true; last = performance.now(); requestAnimationFrame(frame); }
    function pause() { running = false; }

    layout(); draw();
    if ("ResizeObserver" in window) new ResizeObserver(() => { layout(); draw(); }).observe(canvas);
    else window.addEventListener("resize", () => { layout(); draw(); });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver((en) => { visible = en[0].isIntersecting; visible && !document.hidden ? play() : pause(); }).observe(canvas);
    } else play();
    document.addEventListener("visibilitychange", () => (document.hidden ? pause() : visible && play()));
    capImg.onload = keeperImg.onload = draw;
  }

  /* ------------------------------------------------------------------ */
  /* 4. Language switch — remember the visitor's explicit choice         */
  /* ------------------------------------------------------------------ */
  function initLangSwitch() {
    $$(".lang-switch [data-lang]").forEach((a) => {
      a.addEventListener("click", () => {
        try { localStorage.setItem("sv-lang", a.dataset.lang); } catch (_) { /* private mode */ }
        // Keep the reader in the same section when switching language.
        if (location.hash && !a.href.includes("#")) a.href = a.href + location.hash;
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* 5. Small things                                                     */
  /* ------------------------------------------------------------------ */
  function initChrome() {
    const header = $(".site-header");
    const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    const y = $("#year");
    if (y) y.textContent = new Date().getFullYear();
  }

  initSheet();
  initCarousels();
  initFlick();
  initLangSwitch();
  initChrome();
})();
