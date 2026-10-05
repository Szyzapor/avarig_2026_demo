// Online listening test: consent -> questionnaire -> headphone check ->
// instructions -> blind MOS trials -> final comment -> submit.
//
// Responses are POSTed as small JSON events to a Google Apps Script web app
// (config.js: endpoint), which appends them to a Google Sheet. Each event has
// a unique event_id so the script can drop duplicates from retries. Progress
// is kept in localStorage so a reload resumes the session instead of
// restarting it.
"use strict";

const CFG = window.TEST_CONFIG;
const SYSTEMS = ["crm", "zhu", "a2b"];
const LABEL_COLORS = { A: "#3b82f6", B: "#f59e0b", C: "#10b981" };
const STORE_KEY = "avarig_listening_test_v1";
const SCREENS = ["intro", "survey", "check", "instr", "trial", "end", "thanks"];

const SURVEY = [
  { key: "age", q: "q_age", req: true,
    opts: ["age_u24", "age_25", "age_35", "age_45", "age_55", "age_65", "prefer_not"] },
  { key: "gender", q: "q_gender", req: false, opts: ["g_f", "g_m", "g_o", "prefer_not"] },
  { key: "device", q: "q_device", req: true,
    opts: ["dev_over_closed", "dev_over_open", "dev_on_ear", "dev_iem", "dev_bt_buds",
           "dev_bt_head", "dev_speakers", "dev_unknown"] },
  { key: "headphone_model", q: "q_model", req: false, text: true, ph: "q_model_ph" },
  { key: "anc", q: "q_anc", req: false, opts: ["anc_on", "anc_off", "anc_na"] },
  { key: "environment", q: "q_env", req: true, opts: ["env_quiet", "env_some", "env_noisy"] },
  { key: "hearing_impairment", q: "q_hearing", req: true, opts: ["no", "yes", "not_sure", "prefer_not"] },
  { key: "music_experience", q: "q_music", req: true, opts: ["mus_none", "mus_hobby", "mus_edu", "mus_pro"] },
  { key: "audio_experience", q: "q_audio", req: true, opts: ["aud_none", "aud_hobby", "aud_student", "aud_pro"] },
  { key: "spatial_audio_experience", q: "q_spatial", req: true, opts: ["sp_none", "sp_some", "sp_reg"] },
  { key: "listening_tests", q: "q_tests", req: true, opts: ["tests_0", "tests_1", "tests_4"] },
];

// ------------------------------------------------------------------ helpers
const $ = (id) => document.getElementById(id);
const uid = () => (crypto.randomUUID ? crypto.randomUUID()
  : Date.now().toString(36) + Math.random().toString(36).slice(2));
const nowIso = () => new Date().toISOString();

function shuffle(a) {
  a = a.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function t(key, vars) {
  const dict = window.I18N[state.lang] || window.I18N.en;
  let s = dict[key] ?? window.I18N.en[key] ?? key;
  if (vars) for (const k in vars) s = s.replace("{" + k + "}", vars[k]);
  return s;
}

// ------------------------------------------------------------------ state
let state = null;
let manifest = null;
let player = null;

function freshState() {
  return {
    session_id: uid(),
    lang: (navigator.language || "en").toLowerCase().startsWith("pl") ? "pl" : "en",
    screen: "intro",
    started_at: nowIso(),
    survey: {},
    check: { lr_attempts: 0, lr_correct: 0, lr_total: 0, lr_passed: false },
    trials: [],          // planned: [{dataset, clip_id, files, mapping}]
    results: [],         // completed trial records
    trial_pos: 0,
    final_comment: "",
    pending: [],         // events not yet confirmed sent
    send_failed: false,
    finished: false,
  };
}

function save() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* private mode */ }
}

function load() {
  try {
    const s = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
    if (s && s.session_id && !s.finished) return s;
  } catch (e) { /* ignore */ }
  return null;
}

// ------------------------------------------------------------------ sending
async function post(ev) {
  if (!CFG.endpoint) throw new Error("no endpoint");
  // text/plain + no-cors avoids a CORS preflight, which Apps Script does not
  // answer. The response is opaque; only network failures are detectable.
  await fetch(CFG.endpoint, {
    method: "POST", mode: "no-cors", keepalive: true,
    headers: { "Content-Type": "text/plain;charset=utf-8" },
    body: JSON.stringify(ev),
  });
}

async function send(type, data) {
  const ev = Object.assign({ type, event_id: uid(), session_id: state.session_id,
                             client_time: nowIso() }, data);
  state.pending.push(ev);
  save();
  await flush();
}

async function flush() {
  if (!CFG.endpoint) { state.send_failed = true; save(); return; }
  const queue = state.pending.slice();
  for (const ev of queue) {
    try {
      await post(ev);
      state.pending = state.pending.filter((p) => p.event_id !== ev.event_id);
      state.send_failed = false;
    } catch (e) {
      state.send_failed = true;
      break;
    }
  }
  save();
}

// ------------------------------------------------------------------ i18n
function applyI18n() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === state.lang));
  document.title = t("title");
  if (state.screen === "trial") renderTrialText();
  if (state.screen === "check") renderLrProgress();
  if (state.screen === "thanks") renderThanks();
}

// ------------------------------------------------------------------ screens
function show(name) {
  state.screen = name;
  save();
  SCREENS.forEach((s) => { $("s-" + s).hidden = s !== name; });
  const idx = SCREENS.indexOf(name);
  let frac = idx / (SCREENS.length - 1);
  if (name === "trial" && state.trials.length) {
    frac = (4 + state.trial_pos / state.trials.length) / (SCREENS.length - 1);
  }
  $("progress-bar").style.width = Math.round(frac * 100) + "%";
  window.scrollTo(0, 0);
  if (name === "trial") startTrial();
  if (name === "thanks") renderThanks();
  applyI18n();
}

// ---- intro
function initIntro() {
  $("consent").addEventListener("change", (e) => { $("btn-start").disabled = !e.target.checked; });
  $("btn-start").addEventListener("click", () => show("survey"));
  if (CFG.contactEmail) {
    $("contact").hidden = false;
    $("contact-link").href = "mailto:" + CFG.contactEmail;
    $("contact-link").textContent = CFG.contactEmail;
  }
}

// ---- questionnaire
function initSurvey() {
  const form = $("survey-form");
  SURVEY.forEach((f) => {
    const fs = document.createElement("fieldset");
    fs.className = "q";
    fs.dataset.key = f.key;
    const lg = document.createElement("legend");
    lg.dataset.i18n = f.q;
    fs.appendChild(lg);
    if (f.text) {
      const inp = document.createElement("input");
      inp.type = "text"; inp.name = f.key; inp.maxLength = 120;
      inp.dataset.i18nPh = f.ph;
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
    SURVEY.forEach((f) => {
      const v = (data.get(f.key) || "").toString().trim();
      state.survey[f.key] = v;
      const missing = f.req && !v;
      form.querySelector(`[data-key="${f.key}"]`).classList.toggle("missing", missing);
      if (missing) ok = false;
    });
    save();
    if (!ok) {
      $("survey-error").hidden = false;
      form.querySelector(".missing").scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    show("check");
  });
}

// ---- headphone check
let volAudio = null;
const LR_N = 4;
let lr = null;     // {seq, i, answers}
let toneCtx = null;

function renderLrProgress() {
  if (!lr) { $("lr-progress").textContent = ""; return; }
  $("lr-progress").textContent = t("lr_progress", { i: Math.min(lr.i + 1, LR_N), n: LR_N });
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
  // round finished
  const c = state.check;
  c.lr_attempts++;
  c.lr_correct = lr.correct; c.lr_total = LR_N;
  c.lr_passed = lr.correct === LR_N;
  save();
  $("btn-lr-play").disabled = true;
  const res = $("lr-result");
  res.hidden = false;
  res.className = c.lr_passed ? "ok" : "error";
  res.textContent = t(c.lr_passed ? "lr_ok" : "lr_bad");
  $("btn-lr-retry").hidden = c.lr_passed;
  // Do not trap participants: after one completed round they may continue;
  // the check result is stored with their answers for later screening.
  $("btn-check").disabled = false;
}

function initCheck() {
  $("btn-vol").addEventListener("click", () => {
    if (volAudio && !volAudio.paused) {
      volAudio.pause();
      $("btn-vol").dataset.i18n = "vol_play";
    } else {
      if (!volAudio) {
        const first = state.trials[0] || planTrials()[0];
        volAudio = new Audio(first.files.reference);
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
    show("instr");
  });
  newLrRound();
  if (state.check.lr_attempts > 0) $("btn-check").disabled = false;
}

// ---- instructions
function initInstr() {
  const tb = $("scale-table");
  [5, 4, 3, 2, 1].forEach((m) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td class="n">${m}</td><td><b data-i18n="mos_${m}"></b></td><td class="muted" data-i18n="mos_${m}d"></td>`;
    tb.appendChild(tr);
  });
  $("btn-instr").addEventListener("click", async () => {
    // Send the profile once, just before the first trial.
    if (!state.profile_sent) {
      state.profile_sent = true;
      send("participant", {
        lang: state.lang,
        started_at: state.started_at,
        user_agent: navigator.userAgent,
        screen: `${screen.width}x${screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
        survey: state.survey,
        check: state.check,
        n_trials: state.trials.length,
      });
    }
    show("trial");
  });
}

// ---- trials
function planTrials() {
  const k = CFG.clipsPerDataset;
  let picked = [];
  manifest.datasets.forEach((ds) => {
    shuffle(ds.clips).slice(0, k).forEach((c) => picked.push({ dataset: ds.id, clip_id: c.id, files: c.files }));
  });
  picked = shuffle(picked);
  // Avoid two clips from the same dataset back to back where possible.
  for (let i = 1; i < picked.length; i++) {
    if (picked[i].dataset === picked[i - 1].dataset) {
      const j = picked.findIndex((p, m) => m > i && p.dataset !== picked[i - 1].dataset);
      if (j > 0) [picked[i], picked[j]] = [picked[j], picked[i]];
    }
  }
  picked.forEach((p) => {
    const sys = shuffle(SYSTEMS);
    p.mapping = { A: sys[0], B: sys[1], C: sys[2] };
  });
  return picked;
}

let trialStart = 0;
let trialRatings = {};

function trialSources(tr) {
  return [{ id: "ref", label: t("ref_label"), color: "#6b7280", url: tr.files.reference }]
    .concat(["A", "B", "C"].map((l) => ({
      id: l, label: t("sys_label", { l }), color: LABEL_COLORS[l], url: tr.files[tr.mapping[l]],
    })));
}

function renderTrialText() {
  const n = state.trials.length;
  $("trial-title").textContent = t("trial_h", { i: state.trial_pos + 1, n });
  $("btn-next").textContent = t(state.trial_pos + 1 < n ? "next" : "finish_trials");
  if (player) player.relabel({ ref: t("ref_label"), A: t("sys_label", { l: "A" }),
                               B: t("sys_label", { l: "B" }), C: t("sys_label", { l: "C" }) });
  document.querySelectorAll(".rcard h3").forEach((h) => { h.textContent = t("sys_label", { l: h.dataset.l }); });
}

function updateNext() {
  const done = ["A", "B", "C"].every((l) => trialRatings[l] && trialRatings[l].mos);
  $("btn-next").disabled = !done;
  if (done) $("trial-error").hidden = true;
}

function unlockCard(l) {
  const card = document.querySelector(`.rcard[data-l="${l}"]`);
  if (!card || !card.classList.contains("locked")) return;
  card.classList.remove("locked");
  card.querySelectorAll("input").forEach((i) => { i.disabled = false; });
}

function buildRatingCards() {
  const box = $("ratings");
  box.innerHTML = "";
  trialRatings = {};
  ["A", "B", "C"].forEach((l) => {
    trialRatings[l] = { mos: null, comment: "" };
    const card = document.createElement("div");
    card.className = "rcard" + (CFG.minListenSeconds > 0 ? " locked" : "");
    card.dataset.l = l;
    card.style.borderLeftColor = LABEL_COLORS[l];
    let html = `<h3 data-l="${l}"></h3><p class="lockmsg" data-i18n="play_first"></p><div class="mos">`;
    [1, 2, 3, 4, 5].forEach((m) => {
      html += `<label><input type="radio" name="mos_${l}" value="${m}"${CFG.minListenSeconds > 0 ? " disabled" : ""}>` +
              `<span class="num">${m}</span><span class="lbl" data-i18n="mos_${m}"></span></label>`;
    });
    html += `</div><input type="text" class="cmt" maxlength="500" data-i18n-ph="comment_ph"${CFG.minListenSeconds > 0 ? " disabled" : ""}>`;
    card.innerHTML = html;
    card.querySelectorAll(`input[name="mos_${l}"]`).forEach((r) => r.addEventListener("change", () => {
      trialRatings[l].mos = parseInt(r.value, 10);
      updateNext();
    }));
    card.querySelector(".cmt").addEventListener("input", (e) => { trialRatings[l].comment = e.target.value; });
    box.appendChild(card);
  });
  updateNext();
}

async function startTrial() {
  if (state.trial_pos >= state.trials.length) { show("end"); return; }
  const tr = state.trials[state.trial_pos];
  buildRatingCards();
  renderTrialText();
  trialStart = performance.now();
  const ok = await player.load(trialSources(tr), { loading: t("loading"), error: t("load_err") });
  if (!ok) return;
  const next = state.trials[state.trial_pos + 1];
  if (next) player.prefetch([next.files.reference].concat(SYSTEMS.map((s) => next.files[s])));
}

function finishTrial() {
  const tr = state.trials[state.trial_pos];
  player.stop();
  const listened = player.listened;
  const r = (x) => Math.round(x * 10) / 10;
  const record = {
    trial_index: state.trial_pos + 1,
    n_trials: state.trials.length,
    dataset: tr.dataset,
    clip_id: tr.clip_id,
    trial_seconds: r((performance.now() - trialStart) / 1000),
    reference_listen_s: r(listened.ref || 0),
    ratings: ["A", "B", "C"].map((l) => ({
      blind_label: l,
      system: tr.mapping[l],
      mos: trialRatings[l].mos,
      comment: trialRatings[l].comment.trim(),
      listen_s: r(listened[l] || 0),
    })),
  };
  state.results.push(record);
  state.trial_pos++;
  save();
  send("trial", record);
  show(state.trial_pos < state.trials.length ? "trial" : "end");
}

function initTrial() {
  player = new GaplessPlayer(
    { play: $("pl-play"), seek: $("pl-seek"), time: $("pl-time"),
      sources: $("pl-sources"), status: $("pl-status") },
    { onListen: (id, secs) => { if (secs >= CFG.minListenSeconds) unlockCard(id); } },
  );
  $("btn-next").addEventListener("click", () => {
    if ($("btn-next").disabled) { $("trial-error").hidden = false; return; }
    finishTrial();
  });
}

// ---- end + thanks
function exportBlob() {
  const data = {
    session_id: state.session_id, lang: state.lang, started_at: state.started_at,
    finished_at: state.finished_at, user_agent: navigator.userAgent,
    survey: state.survey, check: state.check, results: state.results,
    final_comment: state.final_comment,
  };
  return new Blob([JSON.stringify(data, null, 1)], { type: "application/json" });
}

function renderThanks() {
  $("thanks-text").textContent = t(state.send_failed || state.pending.length ? "thanks_offline" : "thanks_text");
  $("paper-link").href = CFG.paperUrl;
}

function initEnd() {
  $("btn-submit").addEventListener("click", async () => {
    const b = $("btn-submit");
    b.disabled = true;
    b.textContent = t("sending");
    state.final_comment = $("final-comment").value.trim();
    state.finished_at = nowIso();
    const secs = (Date.parse(state.finished_at) - Date.parse(state.started_at)) / 1000;
    await send("finish", { final_comment: state.final_comment, total_seconds: Math.round(secs),
                           n_completed: state.results.length });
    state.finished = true;
    save();
    show("thanks");
  });
  $("btn-download").addEventListener("click", () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(exportBlob());
    a.download = `listening_test_${state.session_id.slice(0, 8)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  });
}

// ------------------------------------------------------------------ boot
async function boot() {
  state = load() || freshState();
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
    state.lang = b.dataset.lang;
    save();
    applyI18n();
  }));
  try {
    manifest = await (await fetch("manifest.json", { cache: "no-cache" })).json();
  } catch (e) {
    document.querySelector("main").textContent = "Could not load manifest.json: " + e;
    return;
  }
  if (!state.trials.length) { state.trials = planTrials(); save(); }

  initIntro(); initSurvey(); initCheck(); initInstr(); initTrial(); initEnd();
  if (state.pending.length) flush();     // retry anything unsent from a previous visit
  show(state.screen === "thanks" ? "intro" : state.screen);
}

boot();
