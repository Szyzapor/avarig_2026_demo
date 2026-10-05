// Gapless A/B comparison player (ported from src/demo/player/index.html).
//
// Every version of one clip is decoded into a single AudioContext and driven
// from ONE transport: only one version is audible at a time, and switching
// cross-fades at the same playhead, so the comparison is sample-aligned and
// click-free. On top of the Streamlit original it tracks how long each
// version was actually heard, which the rating UI uses to require listening.
"use strict";

class GaplessPlayer {
  constructor(els, { onListen } = {}) {
    this.els = els;              // {play, seek, time, sources, status}
    this.onListen = onListen || (() => {});
    this.FADE = 0.012;
    this.ctx = null;
    this.master = null;
    this.sources = [];           // [{id, label, color}]
    this.buffers = {};
    this.duration = 0;
    this.currentId = null;
    this.playing = false;
    this.offset = 0;
    this.anchor = 0;
    this.active = null;
    this.scrubbing = false;
    this.loading = false;
    this.listened = {};          // id -> seconds heard
    this.lastTick = 0;
    this.cache = new Map();      // url -> Promise<ArrayBuffer>

    els.play.addEventListener("click", () => (this.playing ? this.pause() : this.play()));
    els.seek.addEventListener("input", () => {
      this.scrubbing = true;
      els.time.textContent = this.fmt((els.seek.value / 1000) * this.duration) + " / " + this.fmt(this.duration);
    });
    els.seek.addEventListener("change", () => {
      this.scrubbing = false;
      this.seekTo((els.seek.value / 1000) * this.duration);
    });
    window.addEventListener("keydown", (e) => {
      if (!this.enabled || this.loading) return;
      const el = e.target;
      if (el && (el.tagName === "TEXTAREA" || (el.tagName === "INPUT" && el.type === "text"))) return;
      if (e.code === "Space") { e.preventDefault(); this.playing ? this.pause() : this.play(); }
      else if (e.key >= "1" && e.key <= "9") {
        const i = parseInt(e.key, 10) - 1;
        if (i < this.sources.length) this.select(this.sources[i].id);
      }
    });
    this.enabled = false;
  }

  ensureCtx() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
    }
    return this.ctx;
  }

  fmt(t) {
    if (!isFinite(t) || t < 0) t = 0;
    return Math.floor(t / 60) + ":" + String(Math.floor(t % 60)).padStart(2, "0");
  }

  now() {
    if (!this.playing) return this.offset;
    return (this.offset + (this.ctx.currentTime - this.anchor)) % (this.duration || 1);
  }

  voice(id, at) {
    const ctx = this.ctx;
    const node = ctx.createBufferSource();
    node.buffer = this.buffers[id];
    node.loop = true;
    const g = ctx.createGain();
    node.connect(g); g.connect(this.master);
    const t = ctx.currentTime;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(1, t + this.FADE);
    node.start(t, Math.max(0, Math.min(at, node.buffer.duration - 0.001)));
    return { node, g };
  }

  kill(v) {
    if (!v) return;
    const t = this.ctx.currentTime;
    try {
      v.g.gain.cancelScheduledValues(t);
      v.g.gain.setValueAtTime(Math.max(0.0001, v.g.gain.value), t);
      v.g.gain.exponentialRampToValueAtTime(0.0001, t + this.FADE);
      v.node.stop(t + this.FADE + 0.01);
    } catch (e) { /* already stopped */ }
  }

  play() {
    if (this.loading || !this.currentId || this.playing) return;
    this.ensureCtx();
    if (this.ctx.state === "suspended") this.ctx.resume();
    this.active = this.voice(this.currentId, this.offset);
    this.anchor = this.ctx.currentTime;
    this.lastTick = performance.now();
    this.playing = true;
    this.els.play.textContent = "⏸";
    this.tick();
  }

  pause() {
    if (!this.playing) return;
    this.account();
    this.offset = this.now();
    this.playing = false;
    this.kill(this.active); this.active = null;
    this.els.play.textContent = "▶";
    this.render();
  }

  stop() {
    this.pause();
    this.enabled = false;
  }

  select(id) {
    if (id === this.currentId || !this.buffers[id]) return;
    if (this.playing) {
      this.account();
      const at = this.now();
      const old = this.active;
      this.active = this.voice(id, at);
      this.offset = at; this.anchor = this.ctx.currentTime;
      this.kill(old);
    }
    this.currentId = id;
    this.render();
  }

  seekTo(t) {
    t = Math.max(0, Math.min(this.duration, t));
    if (this.playing) {
      this.account();
      const old = this.active;
      this.active = this.voice(this.currentId, t);
      this.anchor = this.ctx.currentTime;
      this.kill(old);
    }
    this.offset = t;
    this.render();
  }

  // Credit wall-clock listening time to the version currently sounding.
  account() {
    const t = performance.now();
    if (this.playing && this.currentId) {
      const d = (t - this.lastTick) / 1000;
      this.listened[this.currentId] = (this.listened[this.currentId] || 0) + d;
      this.onListen(this.currentId, this.listened[this.currentId]);
    }
    this.lastTick = t;
  }

  tick() {
    if (!this.playing) return;
    this.account();
    this.render();
    requestAnimationFrame(() => this.tick());
  }

  render() {
    const t = this.now();
    if (!this.scrubbing) this.els.seek.value = this.duration ? Math.round((t / this.duration) * 1000) : 0;
    this.els.time.textContent = this.fmt(t) + " / " + this.fmt(this.duration);
    this.els.sources.querySelectorAll(".src").forEach((b) => {
      b.classList.toggle("active", b.dataset.id === this.currentId);
    });
  }

  buildButtons() {
    this.els.sources.innerHTML = "";
    this.sources.forEach((s, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "src";
      b.dataset.id = s.id;
      b.style.borderLeftColor = s.color;
      b.innerHTML = `<span></span><small>${i + 1}</small>`;
      b.firstChild.textContent = s.label;
      b.addEventListener("click", () => this.select(s.id));
      this.els.sources.appendChild(b);
    });
  }

  relabel(labels) {
    this.sources.forEach((s) => {
      if (labels[s.id]) s.label = labels[s.id];
      const b = this.els.sources.querySelector(`.src[data-id="${s.id}"] span`);
      if (b) b.textContent = s.label;
    });
  }

  fetchBuf(url) {
    if (!this.cache.has(url)) {
      const p = fetch(url).then((r) => {
        if (!r.ok) throw new Error(r.status + " " + url);
        return r.arrayBuffer();
      });
      p.catch(() => this.cache.delete(url));
      this.cache.set(url, p);
    }
    return this.cache.get(url);
  }

  // Start downloading a clip in the background (next trial).
  prefetch(urls) { urls.forEach((u) => this.fetchBuf(u).catch(() => {})); }

  async load(sources, msgs) {
    this.loading = true;
    this.enabled = true;
    if (this.playing) { this.kill(this.active); this.active = null; this.playing = false; }
    this.els.play.textContent = "▶";
    this.els.play.disabled = true; this.els.seek.disabled = true;
    this.els.status.textContent = msgs.loading;
    this.offset = 0; this.currentId = null; this.buffers = {}; this.duration = 0; this.listened = {};
    this.sources = sources.map((s) => ({ id: s.id, label: s.label, color: s.color }));
    this.buildButtons();
    this.ensureCtx();
    try {
      await Promise.all(sources.map(async (s) => {
        const ab = await this.fetchBuf(s.url);
        // decodeAudioData detaches its input; keep the cached copy intact.
        this.buffers[s.id] = await this.ctx.decodeAudioData(ab.slice(0));
      }));
    } catch (e) {
      this.els.status.textContent = msgs.error + " (" + e.message + ")";
      this.loading = false;
      return false;
    }
    sources.forEach((s) => this.cache.delete(s.url));   // free memory
    this.duration = Math.max(...sources.map((s) => this.buffers[s.id].duration));
    this.currentId = sources[0].id;
    this.els.play.disabled = false; this.els.seek.disabled = false;
    this.els.status.textContent = "";
    this.loading = false;
    this.render();
    return true;
  }
}

window.GaplessPlayer = GaplessPlayer;
