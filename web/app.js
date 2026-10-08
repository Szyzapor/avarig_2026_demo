// Online MUSHRA test (ITU-R BS.1534-3 style), two sessions:
//   ?session=1 (default): information/consent -> questionnaire -> headphone check
//     -> instructions -> 2 practice pages -> 12 trials (overall quality, random
//     order) -> 2 repeated trials in a separate block -> comment -> send.
//   ?session=2: same frame, 1 practice page, then 4 attribute blocks of 6 trials
//     in a Latin-square order chosen from the participant code, plus 1 repeat.
// Participant code: ?pid=... (per-person links) or generated and written into
// the URL, so a reload resumes the same session. Every condition starts
// unrated; "Next" unlocks only when every condition has been heard and every
// slider moved. Results go to a Google Apps Script endpoint (config.js) one
// page at a time; a JSON download is always offered at the end as a backup.
"use strict";

const CFG = window.TEST_CONFIG;
const STORE_PREFIX = "avarig_mushra_v1";
const SCREENS = ["intro", "survey", "excluded", "check", "instr", "page", "end", "thanks"];
const ATTRIBUTES = ["tone_colour", "localisation", "externalisation", "artefacts"];
// Balanced Latin square for 4 blocks (each attribute in each position once and
// each attribute following every other once across the 4 rows).
const LATIN4 = [[0, 1, 3, 2], [1, 2, 0, 3], [2, 3, 1, 0], [3, 0, 2, 1]];
const EXCLUDED_DEVICES = ["dev_bluetooth", "dev_speakers"];

const SURVEY_FULL = [
  { key: "age", q: "q_age", opts: ["age_18", "age_25", "age_35", "age_45", "age_55", "prefer_not"] },
  { key: "hearing_impairment", q: "q_hearing", opts: ["no", "yes", "not_sure"] },
  { key: "device", q: "q_device",
    opts: ["dev_over_open", "dev_over_closed", "dev_on_ear", "dev_in_ear", "dev_bluetooth", "dev_speakers"] },
  { key: "headphone_model", q: "q_model", text: true, ph: "q_model_ph" },
  { key: "environment", q: "q_env", opts: ["env_quiet", "env_some", "env_noisy"] },
  { key: "music_experience", q: "q_music", opts: ["mus_none", "mus_hobby", "mus_edu", "mus_pro"] },
  { key: "audio_experience", q: "q_audio", opts: ["aud_none", "aud_hobby", "aud_student", "aud_pro"] },
  { key: "spatial_audio_experience", q: "q_spatial", opts: ["sp_none", "sp_some", "sp_reg"] },
  { key: "listening_tests", q: "q_tests", opts: ["tests_0", "tests_1", "tests_4"] },
];
const SURVEY_SHORT = SURVEY_FULL.filter((f) => ["device", "headphone_model", "environment"].includes(f.key));

// ------------------------------------------------------------------ helpers
const $ = (id) => document.getElementById(id);
const nowIso = () => new Date().toISOString();
const uid = () => (crypto.randomUUID ? crypto.randomUUID()
  : Date.now().toString(36) + Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2));
const round1 = (x) => Math.round(x * 10) / 10;

function shuffle(a) {
  a = a.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function hash(s) {
  let h = 0;
  for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return h;
}

function t(key, vars) {
  const d = window.I18N[state.lang] || window.I18N.en;
  let s = d[key] ?? window.I18N.en[key] ?? key;
  if (vars) for (const k in vars) s = s.replace("{" + k + "}", vars[k]);
  return s;
}

// ------------------------------------------------------------------ URL / identity
const params = new URLSearchParams(location.search);
const SESSION = params.get("session") === "2" ? 2 : 1;
const DEBUG = params.get("debug") === "1";
let PID = (params.get("pid") || "").replace(/[^A-Za-z0-9_-]/g, "").slice(0, 32);
if (!PID) {
  PID = uid().replace(/-/g, "").slice(0, 8);
  params.set("pid", PID);
  params.set("session", String(SESSION));
  history.replaceState(null, "", location.pathname + "?" + params.toString());
}
const STORE_KEY = `${STORE_PREFIX}_${PID}_s${SESSION}`;

// ------------------------------------------------------------------ state
let state = null;
let manifest = null;
let player = null;

function freshState() {
  const urlLang = params.get("lang");
  return {
    pid: PID, session: SESSION, session_uuid: uid(),
    lang: urlLang === "pl" || urlLang === "en" ? urlLang
      : ((navigator.language || "en").toLowerCase().startsWith("pl") ? "pl" : "en"),
    screen: "intro", started_at: nowIso(),
    survey: {}, check: { lr_attempts: 0, lr_correct: 0, lr_total: 0, lr_passed: false },
    plan: [], pos: 0, results: [], comment: "",
    pending: [], send_failed: false, profile_sent: false, finished: false, excluded_sent: false,
  };
}

function save() { try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* private mode */ } }
function load() {
  try { const s = JSON.parse(localStorage.getItem(STORE_KEY) || "null"); if (s && s.pid === PID) return s; }
  catch (e) { /* ignore */ }
  return null;
}

// ------------------------------------------------------------------ plan
function trialById(id) { return manifest.trials.find((x) => x.id === id); }

function makePage(kind, block, criterion, trial) {
  const conds = shuffle(manifest.conditions);
  const labels = {};
  conds.forEach((c, i) => { labels[String(i + 1)] = c; });
  return { kind, block, criterion, trial_id: trial.id, dataset: trial.dataset, clip: trial.clip,
           labels, page_id: `${criterion}_${trial.id}${kind === "repeat" ? "_repeat" : ""}` };
}

function planSession() {
  const training = manifest.trials.filter((x) => x.role === "training");
  const tests = manifest.trials.filter((x) => x.role === "test");
  const pages = [];
  if (SESSION === 1) {
    training.forEach((tr) => pages.push(makePage("training", 0, "overall", tr)));
    shuffle(tests).forEach((tr) => pages.push(makePage("test", 1, "overall", tr)));
    shuffle(CFG.session1Repeats).forEach((id) => pages.push(makePage("repeat", 2, "overall", trialById(id))));
  } else {
    const order = LATIN4[hash(PID) % 4].map((i) => ATTRIBUTES[i]);
    pages.push(makePage("training", 0, order[0], training.find((x) => x.dataset === "zhu") || training[0]));
    const trials = CFG.session2Trials.map(trialById);
    order.forEach((crit, b) => shuffle(trials).forEach((tr) => pages.push(makePage("test", b + 1, crit, tr))));
    // one repeat of a block-1 page, at the end of block 3 (a different block)
    const first = pages.filter((p) => p.block === 1)[Math.floor(Math.random() * trials.length)];
    const rep = makePage("repeat", 3, first.criterion, trialById(first.trial_id));
    const lastOf3 = pages.map((p) => p.block).lastIndexOf(3);
    pages.splice(lastOf3 + 1, 0, rep);
    state.attribute_order = order;
  }
  return pages;
}

// ------------------------------------------------------------------ sending
async function post(ev) {
  if (!CFG.endpoint) throw new Error("no endpoint");
  // text/plain + no-cors: no CORS preflight (Apps Script does not answer one).
  await fetch(CFG.endpoint, { method: "POST", mode: "no-cors", keepalive: true,
    headers: { "Content-Type": "text/plain;charset=utf-8" }, body: JSON.stringify(ev) });
}

async function send(type, data) {
  state.pending.push(Object.assign({ type, event_id: uid(), pid: PID, session: SESSION,
    session_uuid: state.session_uuid, client_time: nowIso() }, data));
  save();
  await flush();
}

async function flush() {
  if (!CFG.endpoint) { state.send_failed = true; save(); return; }
  for (const ev of state.pending.slice()) {
    try {
      await post(ev);
      state.pending = state.pending.filter((p) => p.event_id !== ev.event_id);
      state.send_failed = false;
    } catch (e) { state.send_failed = true; break; }
  }
  save();
}

// ------------------------------------------------------------------ i18n + screens
function applyI18n() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === state.lang));
  document.title = t("title");
  $("session-name").textContent = t(SESSION === 1 ? "s1_name" : "s2_name");
  $("intro-session").textContent = t(SESSION === 1 ? "intro_s1" : "intro_s2");
  $("survey-title").textContent = t(SESSION === 1 ? "survey_h" : "survey_h2");
  $("instr-s2").hidden = SESSION !== 2;
  $("instr-s2-list").innerHTML = ATTRIBUTES.map((a) => `<li><b>${t("crit_" + a)}</b>: ${t("crit_" + a + "_d")}</li>`).join("");
  if (state.screen === "page") renderPageText();
  if (state.screen === "check") renderLrProgress();
  if (state.screen === "thanks") renderThanks();
}

function show(name) {
  state.screen = name;
  save();
  SCREENS.forEach((s) => { $("s-" + s).hidden = s !== name; });
  const n = state.plan.length || 1;
  const frac = name === "page" ? 0.2 + 0.75 * state.pos / n : { intro: 0, survey: 0.05, excluded: 0.05,
    check: 0.1, instr: 0.15, end: 0.97, thanks: 1 }[name];
  $("progress-bar").style.width = Math.round(frac * 100) + "%";
  window.scrollTo(0, 0);
  if (name === "page") startPage();
  if (name === "thanks") renderThanks();
  applyI18n();
}

// ------------------------------------------------------------------ intro
function initIntro() {
  $("pid-intro").textContent = PID;
  $("consent").addEventListener("change", (e) => { $("btn-start").disabled = !e.target.checked; });
  $("btn-start").addEventListener("click", () => show("survey"));
  if (CFG.contactEmail) {
    $("contact").hidden = false;
    $("contact-link").href = "mailto:" + CFG.contactEmail;
    $("contact-link").textContent = CFG.contactEmail;
  }
}

// ------------------------------------------------------------------ questionnaire
function initSurvey() {
  const fields = SESSION === 1 ? SURVEY_FULL : SURVEY_SHORT;
  const form = $("survey-form");
  fields.forEach((f) => {
    const fs = document.createElement("fieldset");
    fs.className = "q";
    fs.dataset.key = f.key;
    const lg = document.createElement("legend");
    lg.dataset.i18n = f.q;
    fs.appendChild(lg);
    if (f.text) {
      const inp = document.createElement("input");
      inp.type = "text"; inp.name = f.key; inp.maxLength = 120; inp.dataset.i18nPh = f.ph;
      inp.value = state.survey[f.key] || "";
      fs.appendChild(inp);
    } else {
      const wrap = document.createElement("div");
      wrap.className = "opts";
      f.opts.forEach((o) => {
        const lab = document.createElement("label");
        const r = document.createElement("input");
        r.type = "radio"; r.name = f.key; r.value = o;
        if (state.survey[f.key] === o) r.checked = true;
        const sp = document.createElement("span");
        sp.dataset.i18n = o;
        lab.append(r, sp);
        wrap.appendChild(lab);
      });
      fs.appendChild(wrap);
    }
    form.appendChild(fs);
  });
  form.addEventListener("change", () => { $("survey-error").hidden = true; });
  $("btn-survey").addEventListener("click", (e) => {
    e.preventDefault();
    const data = new FormData(form);
    let ok = true;
    fields.forEach((f) => {
      const v = (data.get(f.key) || "").toString().trim();
      state.survey[f.key] = v;
      const missing = !v;
      form.querySelector(`[data-key="${f.key}"]`).classList.toggle("missing", missing);
      if (missing) ok = false;
    });
    save();
    if (!ok) {
      $("survey-error").hidden = false;
      form.querySelector(".missing").scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    if (EXCLUDED_DEVICES.includes(state.survey.device)) {
      if (!state.excluded_sent) {
        state.excluded_sent = true;
        send("participant", participantData({ excluded: state.survey.device }));
      }
      show("excluded");
      return;
    }
    show("check");
  });
  $("btn-excluded-back").addEventListener("click", () => show("survey"));
}

// ------------------------------------------------------------------ headphone check
let volAudio = null, lr = null, toneCtx = null;
const LR_N = 4;

function renderLrProgress() {
  $("lr-progress").textContent = lr ? t("lr_progress", { i: Math.min(lr.i + 1, LR_N), n: LR_N }) : "";
}

function newLrRound() {
  lr = { seq: shuffle(["L", "L", "R", "R"]), i: 0, correct: 0, played: false };
  $("btn-lr-play").disabled = false;
  $("btn-lr-left").disabled = $("btn-lr-right").disabled = true;
  $("lr-result").hidden = true; $("btn-lr-retry").hidden = true;
  renderLrProgress();
}

function playTone(side) {
  toneCtx = toneCtx || new (window.AudioContext || window.webkitAudioContext)();
  if (toneCtx.state === "suspended") toneCtx.resume();
  const osc = toneCtx.createOscillator();
  osc.frequency.value = 1000;
  const g = toneCtx.createGain();
  const merger = toneCtx.createChannelMerger(2);
  const t0 = toneCtx.currentTime;
  g.gain.setValueAtTime(0, t0);
  g.gain.linearRampToValueAtTime(0.12, t0 + 0.03);
  g.gain.setValueAtTime(0.12, t0 + 0.6);
  g.gain.linearRampToValueAtTime(0, t0 + 0.65);
  osc.connect(g);
  g.connect(merger, 0, side === "L" ? 0 : 1);
  merger.connect(toneCtx.destination);
  osc.start(t0); osc.stop(t0 + 0.7);
}

function lrAnswer(side) {
  if (!lr || !lr.played) return;
  if (side === lr.seq[lr.i]) lr.correct++;
  lr.i++; lr.played = false;
  $("btn-lr-left").disabled = $("btn-lr-right").disabled = true;
  if (lr.i < LR_N) { $("btn-lr-play").disabled = false; renderLrProgress(); return; }
  const c = state.check;
  c.lr_attempts++; c.lr_correct = lr.correct; c.lr_total = LR_N; c.lr_passed = lr.correct === LR_N;
  save();
  $("btn-lr-play").disabled = true;
  const res = $("lr-result");
  res.hidden = false;
  res.className = c.lr_passed ? "ok" : "error";
  res.textContent = t(c.lr_passed ? "lr_ok" : "lr_bad");
  $("btn-lr-retry").hidden = c.lr_passed;
  // Continue after a passed round, or after two failed rounds (recorded for screening).
  $("btn-check").disabled = !(c.lr_passed || c.lr_attempts >= 2);
}

function initCheck() {
  $("btn-vol").addEventListener("click", () => {
    if (volAudio && !volAudio.paused) {
      volAudio.pause(); $("btn-vol").dataset.i18n = "vol_play";
    } else {
      if (!volAudio) {
        volAudio = new Audio(manifest.trials.find((x) => x.role === "training").files.reference);
        volAudio.loop = true;
      }
      volAudio.play().catch(() => {});
      $("btn-vol").dataset.i18n = "vol_stop";
    }
    applyI18n();
  });
  $("btn-lr-play").addEventListener("click", () => {
    if (!lr) newLrRound();
    playTone(lr.seq[lr.i]);
    lr.played = true;
    $("btn-lr-play").disabled = true;
    setTimeout(() => { $("btn-lr-left").disabled = $("btn-lr-right").disabled = false; }, 650);
  });
  $("btn-lr-left").addEventListener("click", () => lrAnswer("L"));
  $("btn-lr-right").addEventListener("click", () => lrAnswer("R"));
  $("btn-lr-retry").addEventListener("click", newLrRound);
  $("btn-check").addEventListener("click", () => {
    if (volAudio) { volAudio.pause(); volAudio = null; }
    if (!state.profile_sent) {
      state.profile_sent = true;
      send("participant", participantData({}));
    }
    show("instr");
  });
  newLrRound();
  const c = state.check;
  $("btn-check").disabled = !(c.lr_passed || c.lr_attempts >= 2);
}

function participantData(extra) {
  const ctx = player.ensureCtx();
  return Object.assign({
    lang: state.lang, started_at: state.started_at, user_agent: navigator.userAgent,
    screen: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
    audio_sample_rate: ctx.sampleRate, audio_base_latency: ctx.baseLatency || null,
    stimulus_sample_rate: manifest.sample_rate,
    survey: state.survey, check: state.check, attribute_order: state.attribute_order || null,
    n_pages: state.plan.length, package: manifest.package,
  }, extra);
}

// ------------------------------------------------------------------ instructions
function initInstr() {
  $("btn-instr").addEventListener("click", () => show("page"));
}

// ------------------------------------------------------------------ MUSHRA page
let pageStart = 0;
let ratings = {};          // label -> score (null = unset)

function pageCounts() {
  const scored = state.plan.filter((p) => p.kind !== "training");
  const training = state.plan.filter((p) => p.kind === "training");
  return { scored, training };
}

function renderPageText() {
  const p = state.plan[state.pos];
  if (!p) return;
  const { scored, training } = pageCounts();
  let title;
  if (p.kind === "training") {
    title = t("page_training", { i: training.indexOf(p) + 1, n: training.length });
  } else {
    title = `${t("crit_" + p.criterion)} · ${t("page_progress", { i: scored.indexOf(p) + 1, n: scored.length })}`;
  }
  $("page-title").textContent = title + (DEBUG ? `  [${p.page_id}]` : "");
  const prev = state.plan[state.pos - 1];
  const nBlocks = Math.max(...state.plan.map((x) => x.block));
  let note = "";
  if (p.kind === "training") note = t("training_note");
  else if (prev && prev.block !== p.block && prev.kind !== "training") {
    note = t("block_break", { i: prev.block, n: nBlocks });
  }
  $("page-note").hidden = !note;
  $("page-note").innerHTML = note;
  $("page-crit").innerHTML = `<b>${t("crit_" + p.criterion)}</b>: ${t("crit_" + p.criterion + "_d")}`;
  player.relabel({ ref: t("ref") });
  updateMissing();
}

function buildSliders(p) {
  const box = $("sliders");
  box.innerHTML = '<div class="scol refcol"></div>';
  ratings = {};
  Object.keys(p.labels).forEach((label) => {
    ratings[label] = null;
    const col = document.createElement("div");
    col.className = "scol locked unset";
    col.dataset.label = label;
    col.innerHTML = `<span class="val">${t("unset")}</span>` +
      `<input type="range" min="0" max="100" step="1" value="0" disabled aria-label="${label}">` +
      `<small>${label}</small><span class="lockmsg">${t("play_first")}</span>`;
    const inp = col.querySelector("input");
    const set = () => {
      ratings[label] = parseInt(inp.value, 10);
      col.classList.remove("unset");
      col.querySelector(".val").textContent = inp.value;
      updateMissing();
    };
    // Starts at 0 with the thumb hidden (unrated). Any interaction sets it,
    // including a click on the current position (no "input" event then).
    inp.addEventListener("input", set);
    inp.addEventListener("change", set);
    inp.addEventListener("pointerup", () => { if (!inp.disabled) set(); });
    box.appendChild(col);
  });
}

function unlock(label) {
  const col = document.querySelector(`.scol[data-label="${label}"]`);
  if (!col || !col.classList.contains("locked")) return;
  col.classList.remove("locked");
  col.querySelector("input").disabled = false;
  updateMissing();
}

function updateMissing() {
  const unheard = Object.keys(ratings).filter((l) => (player.listened[l] || 0) < CFG.minListenSeconds);
  const unset = Object.keys(ratings).filter((l) => ratings[l] === null);
  const msg = [];
  if (unheard.length) msg.push(t("missing_listen", { list: unheard.join(", ") }));
  else if (unset.length) msg.push(t("missing_rate", { list: unset.join(", ") }));
  $("page-missing").textContent = msg.join(" ");
  $("btn-next").disabled = unheard.length > 0 || unset.length > 0;
}

async function startPage() {
  if (state.pos >= state.plan.length) { show("end"); return; }
  const p = state.plan[state.pos];
  const trial = trialById(p.trial_id);
  buildSliders(p);
  const sources = [{ id: "ref", key: "0", label: t("ref"), color: "#6b7280", url: trial.files.reference }]
    .concat(Object.entries(p.labels).map(([label, cond]) => ({
      id: label, key: label, label, color: "#3b82f6", url: trial.files[cond] })));
  renderPageText();
  pageStart = performance.now();
  const ok = await player.load(sources, { loading: t("loading"), error: t("load_err") });
  if (!ok) return;
  updateMissing();
  const next = state.plan[state.pos + 1];
  if (next) player.prefetch(Object.values(trialById(next.trial_id).files));
}

function finishPage() {
  const p = state.plan[state.pos];
  player.stop();
  const heard = player.listened;
  const record = {
    page_index: state.pos + 1, n_pages: state.plan.length, kind: p.kind, block: p.block,
    page_id: p.page_id, trial_id: p.trial_id, dataset: p.dataset, clip: p.clip, criterion: p.criterion,
    page_seconds: round1((performance.now() - pageStart) / 1000),
    reference_listen_s: round1(heard.ref || 0),
    ratings: Object.entries(p.labels).map(([label, cond]) => ({
      condition: cond, label, score: ratings[label], listen_s: round1(heard[label] || 0) })),
  };
  state.results.push(record);
  state.pos++;
  save();
  send("page", record);
  show(state.pos < state.plan.length ? "page" : "end");
}

function initPage() {
  player = new GaplessPlayer(
    { play: $("pl-play"), seek: $("pl-seek"), time: $("pl-time"), sources: $("pl-sources"), status: $("pl-status") },
    { onListen: (id, secs) => {
        if (secs >= CFG.minListenSeconds && id !== "ref") unlock(id);
        if (state.screen === "page") updateMissing();
      } },
  );
  $("btn-next").addEventListener("click", () => { if (!$("btn-next").disabled) finishPage(); });
}

// ------------------------------------------------------------------ end + thanks
function exportBlob() {
  const data = {
    pid: PID, session: SESSION, session_uuid: state.session_uuid, lang: state.lang,
    started_at: state.started_at, finished_at: state.finished_at, user_agent: navigator.userAgent,
    survey: state.survey, check: state.check, attribute_order: state.attribute_order || null,
    results: state.results, comment: state.comment, package: manifest && manifest.package,
  };
  return new Blob([JSON.stringify(data, null, 1)], { type: "application/json" });
}

function session2Url() {
  const u = new URL(location.href);
  u.search = "";
  u.searchParams.set("session", "2");
  u.searchParams.set("pid", PID);
  u.searchParams.set("lang", state.lang);
  return u.toString();
}

function renderThanks() {
  $("thanks-text").textContent = t(state.send_failed || state.pending.length ? "thanks_offline" : "thanks_ok");
  $("pid-thanks").textContent = PID;
  $("thanks-s2").hidden = SESSION !== 1;
  $("s2-link").href = $("s2-link").textContent = session2Url();
  $("paper-link").href = CFG.paperUrl;
}

function initEnd() {
  $("btn-submit").addEventListener("click", async () => {
    const b = $("btn-submit");
    b.disabled = true;
    b.textContent = t("sending");
    state.comment = $("final-comment").value.trim();
    state.finished_at = nowIso();
    await send("finish", { comment: state.comment, n_pages: state.results.length,
      total_seconds: Math.round((Date.parse(state.finished_at) - Date.parse(state.started_at)) / 1000) });
    state.finished = true;
    save();
    show("thanks");
  });
  $("btn-download").addEventListener("click", () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(exportBlob());
    a.download = `mushra_${PID}_session${SESSION}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  });
}

// ------------------------------------------------------------------ boot
async function boot() {
  state = load() || freshState();
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
    state.lang = b.dataset.lang; save(); applyI18n();
  }));
  try {
    manifest = await (await fetch("manifest.json", { cache: "no-cache" })).json();
  } catch (e) {
    document.querySelector("main").textContent = "Could not load manifest.json: " + e;
    return;
  }
  if (!state.plan.length) { state.plan = planSession(); save(); }
  initIntro(); initSurvey(); initPage(); initCheck(); initInstr(); initEnd();
  if (state.pending.length) flush();
  show(state.screen);
}

boot();
