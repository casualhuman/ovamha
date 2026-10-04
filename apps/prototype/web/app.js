/* Ovamha web app: plain JS, no build step, no external assets. Works offline against the local server. */
"use strict";

// ---------------------------------------------------------------- icons (drawn inline, no downloads)
const P = {
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2.5"/>',
  play: '<path d="M7 5v14l11-7z"/>',
  replay: '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/>',
  speaker: '<path d="M4 9v6h4l5 4V5L8 9z"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M14 6l4 4"/>',
  home: '<path d="M4 11l8-7 8 7v9a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  logout: '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l-5-5 5-5M5 12h11"/>',
  alert: '<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17.5v.01"/>',
  send: '<path d="M4 12l16-8-6 16-2.5-6.5z"/>',
  right: '<path d="M9 5l7 7-7 7"/>',
  left: '<path d="M15 5l-7 7 7 7"/>',
  heart: '<path d="M3 12h4l2-4 4 9 2-5h6"/>',
  drop: '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
  temp: '<path d="M10 4a2 2 0 1 1 4 0v10a4 4 0 1 1-4 0z"/><path d="M12 9v7"/>',
  baby: '<circle cx="12" cy="7" r="3.5"/><path d="M6 21c0-4 2.7-7 6-7s6 3 6 7"/><path d="M10.5 6.5h.01M13.5 6.5h.01"/>',
  calendar: '<rect x="4" y="5" width="16" height="16" rx="3"/><path d="M4 10h16M9 3v4M15 3v4"/>',
  flask: '<path d="M9 3h6M10 3v6L5 19a1.5 1.5 0 0 0 1.3 2h11.4a1.5 1.5 0 0 0 1.3-2L14 9V3"/><path d="M7.5 15h9"/>',
  wifioff: '<path d="M3 3l18 18M8.5 16.5a5 5 0 0 1 7 0M5 12.5a10 10 0 0 1 5-2.5M14 10a10 10 0 0 1 5 2.5M12 20h.01"/>',
  shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
  file: '<path d="M6 3h8l5 5v13H6z"/><path d="M14 3v5h5M9 13h7M9 17h7"/>',
  sms: '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 10h8"/>',
  keyboard: '<rect x="3" y="6" width="18" height="12" rx="2.5"/><path d="M7 10h.01M11 10h.01M15 10h.01M7 14h10"/>',
  back: '<path d="M7 4L3 8l4 4"/><path d="M3 8h11a5 5 0 0 1 0 10h-3"/>',
  idcard: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="9" cy="11" r="2.2"/><path d="M5.8 16a3.4 3.4 0 0 1 6.4 0M14 10h4M14 13.5h3"/>',
  cloud: '<path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.1 11 3.5 3.5 0 0 0 7 18z"/>',
  device: '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
};
const icon = (n, cls = "i") => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${P[n] || ""}</svg>`;
const FIELD_ICON = {
  vaginal_bleeding: "drop", bleeding_amount: "drop", fainting: "alert", dizziness: "alert", headache: "alert",
  visual_disturbance: "alert", convulsions: "alert", fever: "temp", abdominal_pain: "alert", breathing_difficulty: "alert",
  unconscious: "alert", vomiting: "alert", reduced_fetal_movement: "baby", waters_broken: "drop", swelling: "alert",
};
const LANGS = [["kri", "Krio"], ["yo", "Yoruba"], ["en", "English"]];

// ---------------------------------------------------------------- state + helpers
const S = {
  screen: "welcome", slide: 0, token: null, worker: null, username: "", pin: "", err: "",
  lang: "en", st: null, result: null, rec: null, audioBlob: null, audioUrl: null, recSecs: 0,
  typing: false, transcript: "", counts: { checks: 0, referrals: 0 }, numbers: {}, numRec: null,
};
const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k) { try { return JSON.parse(sessionStorage.getItem(k)); } catch { return null; } },
  set(k, v) { try { sessionStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode: fine */ } },
  del(k) { try { sessionStorage.removeItem(k); } catch { /* ignore */ } },
};

function toast(msg, ms = 2600) {
  document.querySelectorAll(".toast").forEach((t) => t.remove());
  const t = document.createElement("div");
  t.className = "toast"; t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), ms);
}
function busy(msg) {
  const b = document.createElement("div");
  b.className = "busy"; b.innerHTML = `<div class="box"><div class="spinner"></div>${esc(msg)}</div>`;
  document.body.appendChild(b);
  return () => b.remove();
}

async function api(path, { method = "POST", body, form, raw } = {}) {
  const headers = {};
  if (S.token) headers.Authorization = `Bearer ${S.token}`;
  let payload;
  if (form) payload = form;
  else if (body !== undefined) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }
  const res = await fetch(path, { method, headers, body: payload });
  if (raw) {
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Request failed");
    return res;
  }
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && S.token) { signOut(true); throw new Error("Please sign in again."); }
  if (!res.ok) throw Object.assign(new Error(data.detail || data.message || "Something went wrong"), { data });
  return data;
}

// ---------------------------------------------------------------- audio
let ctx = null;
let current = null;
async function playBlob(blob) {
  try {
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === "suspended") await ctx.resume();
    const buf = await ctx.decodeAudioData(await blob.arrayBuffer());
    if (current) { try { current.stop(); } catch { /* already ended */ } }
    current = ctx.createBufferSource();
    current.buffer = buf;
    current.connect(ctx.destination);
    current.start();
  } catch {
    // Fallback: a fresh <audio> element each time (some browsers cannot decode every format).
    const a = new Audio(URL.createObjectURL(blob));
    a.play().catch(() => toast("Could not play the audio on this device"));
  }
}
async function speakItem(field, value) {
  try {
    const res = await api("/api/speak", { body: { field, value, lang: S.lang }, raw: true });
    const voiceLang = res.headers.get("X-Ovamha-Lang");
    if (voiceLang && voiceLang !== S.lang) toast("Read in English: this wording is not translated yet");
    playBlob(await res.blob());
  } catch (e) { toast(e.message); }
}
async function speakPrompt(prompt) {
  try {
    const res = await api("/api/speak", { body: { prompt, lang: S.lang }, raw: true });
    if (res.headers.get("X-Ovamha-Lang") !== S.lang) toast("Read in English: this wording is not translated yet");
    playBlob(await res.blob());
  } catch (e) { toast(e.message); }
}
async function speakText(text, lang = S.lang) {
  try {
    const res = await api("/api/speak", { body: { text, lang }, raw: true });
    playBlob(await res.blob());
  } catch (e) { toast(e.message); }
}

function pickMime() {
  const opts = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
  return opts.find((m) => window.MediaRecorder && MediaRecorder.isTypeSupported(m)) || "";
}
async function startRecorder(onStop) {
  if (!navigator.mediaDevices?.getUserMedia) {
    toast("Microphone needs HTTPS on a phone. Start the server with --https, or type instead.", 4500);
    return null;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 16000, noiseSuppression: false, echoCancellation: false } });
  const mime = pickMime();
  const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
  const chunks = [];
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  rec.onstop = () => { stream.getTracks().forEach((t) => t.stop()); onStop(new Blob(chunks, { type: rec.mimeType || "audio/webm" })); };
  rec.start();
  return rec;
}
const extFor = (blob) => (blob.type.includes("mp4") ? "m4a" : blob.type.includes("ogg") ? "ogg" : "webm");

// ---------------------------------------------------------------- navigation
function go(screen) { S.enter = screen !== S.screen; S.screen = screen; render(); window.scrollTo(0, 0); }
function render() {
  const app = $("#app");
  app.classList.toggle("enter", !!S.enter);  // fade in only when arriving on a new screen, not on every tap
  S.enter = false;
  const view = { welcome, login, home, woman, describe, confirm, history, measure, advice, referral, result, profile }[S.screen] || home;
  app.innerHTML = view() + (S.hosted && ["welcome", "login", "home", "profile"].includes(S.screen)
    ? `<div class="hosted-note">${icon("wifioff")}Hosted demo for judges. In the field, Ovamha runs fully offline on a local hub.</div>` : "");
  bind[S.screen]?.();
}
function nav(active) {
  const b = (id, ic, label) => `<button data-nav="${id}" class="${active === id ? "on" : ""}">${icon(ic)}<span>${label}</span></button>`;
  return `<nav class="nav">${b("home", "home", "Home")}${b("describe", "plus", "New check")}${b("profile", "user", "Profile")}</nav>`;
}
document.addEventListener("click", (e) => {
  const n = e.target.closest("[data-nav]");
  if (n) {
    const to = n.dataset.nav;
    if (to === "describe") startCheck(); else go(to);
  }
});
function steps(n) { return `<div class="steps">${[1, 2, 3, 4, 5].map((i) => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}</div>`; }
function topbar(title, back) {
  const card = S.screen !== "woman" && S.st?.woman ? `<span class="badge" title="Her card number">${icon("file")}${esc(S.st.woman.card_code)}</span>` : "";
  return `<div class="top">${back ? `<button class="icon-btn" data-back="${back}" aria-label="Back">${icon("left")}</button>` : ""}<h1>${esc(title)}</h1>
    ${card || `<span class="badge green" title="Everything runs on this device">${icon("wifioff")}Offline</span>`}</div>`;
}
document.addEventListener("click", (e) => { const b = e.target.closest("[data-back]"); if (b) go(b.dataset.back); });

// ---------------------------------------------------------------- 1. welcome (onboarding)
const SLIDES = [
  { t: "Offline voice guidance<br>for safer maternal care", p: "Ovamha helps nurses, midwives and community health workers spot danger signs early and refer fast, with no internet." },
  { t: "Speak in Krio,<br>Yoruba or English", p: "Describe the woman's situation in your own words. Ovamha writes it down and reads the key facts back to you." },
  { t: "You confirm.<br>Then refer.", p: "Nothing counts until you confirm it. WHO danger-sign checks run on the confirmed facts and the referral SMS is ready in seconds." },
];
function welcome() {
  const s = SLIDES[S.slide];
  return `<div class="welcome">
    <div class="art">${slideArt(S.slide)}</div>
    <div class="welcome-text">
      <h2>${s.t}</h2><p>${s.p}</p>
      <div class="dots">${SLIDES.map((_, i) => `<i class="${i === S.slide ? "on" : ""}"></i>`).join("")}</div>
      <div class="row"><button class="btn outline" id="skip">Skip</button><button class="btn primary" id="next">${S.slide < 2 ? "Next" : "Sign in"}</button></div>
    </div>
  </div>`;
}
const bind = {};
bind.welcome = () => {
  $("#skip").onclick = () => go("login");
  $("#next").onclick = () => { if (S.slide < 2) { S.slide++; render(); } else go("login"); };
};

// ---------------------------------------------------------------- 2. login (offline PIN)
const LOGO = `<svg viewBox="0 0 64 64" width="64" height="64" aria-hidden="true"><rect width="64" height="64" rx="18" fill="#0072C6"/>
  <circle cx="27" cy="20" r="6.5" fill="#fff"/><path d="M15 50c0-11 5.5-19 12-19 4.6 0 8 3 9.8 7.5" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round"/>
  <circle cx="40.5" cy="44" r="7.5" fill="#fff"/><path d="M45 17v12M39 23h12" stroke="#7CC0EE" stroke-width="4.5" stroke-linecap="round"/></svg>`;
const initials = (n) => n.replace(/^(Nurse|CHW|Midwife)\s+/i, "").slice(0, 2).toUpperCase();
function login() {
  const keys = [1, 2, 3, 4, 5, 6, 7, 8, 9].map((k) => `<button data-k="${k}">${k}</button>`).join("");
  return `<div class="screen" style="padding-bottom:28px">
    <div style="text-align:center;margin:8px 0 22px">${LOGO}
      <div style="font-weight:800;color:var(--blue);font-size:1.5rem;margin-top:10px">Ovamha</div></div>
    <h1 style="margin:0 0 4px;font-size:1.35rem">Sign in</h1>
    <p class="muted small" style="margin:0 0 14px">Checked on this device: no internet needed.</p>
    <label class="small muted" for="user" style="font-weight:650">Username</label>
    <input class="input" id="user" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false"
      placeholder="e.g. fati" value="${esc(S.username || "")}" style="margin:6px 0 4px">
    <div class="small muted" style="margin-top:14px;font-weight:650">PIN</div>
    <div class="pin-dots">${[0, 1, 2, 3, 4, 5].map((i) => `<i class="${i < S.pin.length ? "on" : ""}"></i>`).join("")}</div>
    <div class="err" id="err">${esc(S.err)}</div>
    <div class="pinpad">${keys}<button class="fn" data-k="clear">Clear</button><button data-k="0">0</button><button class="fn" data-k="del" aria-label="Delete">${icon("back")}</button></div>
  </div>`;
}
bind.login = () => {
  const u = $("#user");
  u.oninput = () => { S.username = u.value; };
  if (!S.username) u.focus();
  document.querySelectorAll("[data-k]").forEach((b) => b.onclick = () => pinKey(b.dataset.k));
};
document.addEventListener("keydown", (e) => {
  if (S.screen !== "login" || document.activeElement?.id === "user") return;
  if (/^\d$/.test(e.key)) pinKey(e.key); else if (e.key === "Backspace") pinKey("del");
});
async function pinKey(k) {
  if (k === "clear") S.pin = ""; else if (k === "del") S.pin = S.pin.slice(0, -1); else if (S.pin.length < 6) S.pin += k;
  S.err = "";
  if (S.pin.length === 6 && !(S.username || "").trim()) { S.err = "Enter your username first."; S.pin = ""; }
  render();
  if (S.pin.length === 6) {
    try {
      const r = await api("/api/login", { body: { username: S.username, pin: S.pin } });
      S.token = r.token; S.worker = r.worker; S.lang = r.worker.languages?.[0] || "en";
      store.set("ovamha", { token: S.token, worker: S.worker, lang: S.lang });
      S.pin = ""; S.username = ""; go("home");
    } catch (e) { S.err = e.message; S.pin = ""; render(); }
  }
}
function signOut(silent) {
  if (!silent) api("/api/logout").catch(() => {});
  S.token = null; S.worker = null; S.username = ""; store.del("ovamha");
  go("login");
}

// ---------------------------------------------------------------- 3. home
function home() {
  const w = S.worker;
  return `<div class="screen">
    <div class="hello"><span class="avatar">${esc(initials(w.display_name))}</span>
      <div class="who"><small>Hello,</small><b>${esc(w.display_name)}</b></div>
      <span class="badge green"><span class="offline-dot"></span>Works offline</span></div>
    <div class="hero">
      <svg class="plus" width="150" height="150" viewBox="0 0 24 24"><path d="M12 4v16M4 12h16" stroke="#fff" stroke-width="5" stroke-linecap="round"/></svg>
      <h2>New pregnancy check</h2>
      <p>Describe the woman's situation. Ovamha checks for danger signs and prepares the referral.</p>
      <button class="btn" id="start">${icon("mic")}Guide me</button>
    </div>
    <div class="section-title">Language for this check</div>
    <div class="chips">${LANGS.map(([c, n]) => `<button class="chip ${S.lang === c ? "on" : ""}" data-lang="${c}">${n}</button>`).join("")}</div>
    <div class="section-title">Today</div>
    <div class="tiles">
      <div class="tile"><div class="k">Checks ${icon("heart")}</div><div class="v">${S.counts.checks}</div></div>
      <div class="tile"><div class="k">Referrals ${icon("send")}</div><div class="v">${S.counts.referrals}</div></div>
    </div>
    <div class="card" style="margin-top:14px;display:flex;gap:12px;align-items:flex-start">
      <span class="icon-btn soft" style="flex:none">${icon("shield")}</span>
      <div><b>You stay in charge</b><div class="small muted">Nothing is used until you confirm it. Danger-sign checks follow WHO antenatal guidance. The AI can add a warning for you to check, never remove one.</div></div>
    </div>
    <p class="tiny" style="text-align:center;margin-top:16px">${esc(w.facility)} · Prototype with demo rules and simulated SMS</p>
  </div>${nav("home")}`;
}
bind.home = () => {
  $("#start").onclick = startCheck;
  document.querySelectorAll("[data-lang]").forEach((b) => b.onclick = () => { S.lang = b.dataset.lang; store.set("ovamha", { token: S.token, worker: S.worker, lang: S.lang }); render(); });
};
async function startCheck() {
  try {
    S.st = await api("/api/encounter/new", { body: { lang: S.lang } });
    S.result = null; S.audioBlob = null; S.audioUrl = null; S.transcript = ""; S.typing = false; S.numbers = {};
    S.cardMode = null; S.cardErr = ""; S.reg = null;
    go("woman");
  } catch (e) { toast(e.message); }
}

// ---------------------------------------------------------------- 3b. who is this check for (card number)
// Option card with its own read-aloud button (for workers who do not read English well).
function choice(attr, value, title, sub, ic, prompt, on) {
  return `<div class="opt ${on ? "on" : ""}">
    <button class="opt-main" ${attr}="${esc(value)}"><span class="icon-btn ${on ? "blue" : "soft"}" style="flex:none">${icon(on ? "check" : ic)}</span>
      <span style="flex:1;text-align:left"><b>${title}</b>${sub ? `<br><span class="small muted">${sub}</span>` : ""}</span></button>
    <button class="icon-btn soft opt-say" data-prompt="${prompt}" aria-label="Read aloud">${icon("speaker")}</button></div>`;
}
function qhead(text, prompt) {
  return `<div class="qhead"><h3>${text}</h3><button class="icon-btn soft" data-prompt="${prompt}" aria-label="Read aloud">${icon("speaker")}</button></div>`;
}
function stepper(key, value, allowUnknown = true) {
  const unknown = value === "unknown";
  return `<div class="stepper">
    <button class="icon-btn soft" data-step="${key}" data-d="-1" aria-label="One less" ${unknown ? "disabled" : ""}>−</button>
    <span class="num-big">${unknown ? "?" : value ?? 0}</span>
    <button class="icon-btn soft" data-step="${key}" data-d="1" aria-label="One more" ${unknown ? "disabled" : ""}>+</button>
    ${allowUnknown ? `<button class="chip ${unknown ? "on" : ""}" data-unknown="${key}">Don't know</button>` : ""}</div>`;
}
// ---------------------------------------------------------------- DAK question sets (content/questions/*.json)
async function qset(name) {
  S.qsets = S.qsets || {};
  if (!S.qsets[name]) S.qsets[name] = await api(`/api/questions/${name}`, { method: "GET" });
  return S.qsets[name];
}
function qVisible(q, ans) {
  return Object.entries(q.show_if || {}).every(([k, rule]) => {
    const v = ans[k];
    if (rule === "any") return v !== undefined && v !== "" && !(Array.isArray(v) && !v.length);
    if (typeof rule === "string" && rule.startsWith("gt")) return typeof v === "number" && v > Number(rule.slice(2));
    if (Array.isArray(rule)) return rule.includes(v);
    return v === rule;
  });
}
function speakQ(set, question, option) {
  api("/api/speak", { body: { questionnaire: set, question, option, lang: S.lang }, raw: true }).then(async (res) => {
    if (res.headers.get("X-Ovamha-Lang") !== S.lang) toast("Read in English: this wording is not translated yet");
    playBlob(await res.blob());
  }).catch((e) => toast(e.message));
}
function renderQ(set, q, ans) {
  const v = ans[q.id];
  const sayQ = `<button class="icon-btn soft" data-sq="${set}|${q.id}" aria-label="Read the question aloud">${icon("speaker")}</button>`;
  const head = `<div class="qhead"><h3>${esc(q.label)}${q.optional ? ' <span class="tiny">optional</span>' : ""}</h3>${sayQ}</div>`;
  let body = "";
  if (q.type === "single" || q.type === "multi") {
    body = q.options.map((o) => {
      const on = q.type === "single" ? v === o.value : Array.isArray(v) && v.includes(o.value);
      return `<div class="opt ${on ? "on" : ""}"><button class="opt-main" data-qa="${set}|${q.id}|${esc(o.value)}">
          <span class="tick ${q.type}">${on ? icon("check") : ""}</span><span style="flex:1;text-align:left"><b>${esc(o.label)}</b></span></button>
        <button class="icon-btn soft opt-say" data-sq="${set}|${q.id}|${esc(o.value)}" aria-label="Read aloud">${icon("speaker")}</button></div>`;
    }).join("");
    if (q.type === "multi") body = `<div class="tiny" style="margin:-2px 0 8px">Choose all that apply</div>` + body;
  } else if (q.type === "count") {
    const unknown = v === "unknown";
    const shown = unknown ? "?" : (v ?? "–");
    body = `<div class="stepper"><button class="icon-btn soft" data-qc="${set}|${q.id}|-1" ${unknown ? "disabled" : ""} aria-label="One less">−</button>
      <span class="num-big">${shown}</span><button class="icon-btn soft" data-qc="${set}|${q.id}|1" ${unknown ? "disabled" : ""} aria-label="One more">+</button>
      ${q.dont_know ? `<button class="chip ${unknown ? "on" : ""}" data-qu="${set}|${q.id}">Don't know</button>` : ""}</div>`;
  } else if (q.type === "date") {
    body = `<input class="input" type="date" data-qi="${set}|${q.id}" value="${esc(v || "")}">`;
  } else {
    body = `<input class="input" ${q.type === "phone" ? 'type="tel" inputmode="tel" placeholder="+232 …"' : 'type="text"'} data-qi="${set}|${q.id}" value="${esc(v || "")}" autocomplete="off">`;
  }
  return `<div class="q">${head}${body}</div>`;
}
function renderSet(set, def, ans, sectionIds) {
  return def.sections.filter((sec) => !sectionIds || sectionIds.includes(sec.id)).map((sec) => {
    const qs = sec.questions.filter((q) => qVisible(q, ans));
    return qs.length ? `<div class="card qcard"><div class="section-kicker">${esc(sec.title)}</div>${qs.map((q) => renderQ(set, q, ans)).join("")}</div>` : "";
  }).join("");
}
function bindSet(answersOf, rerender) {
  const find = (set, id) => S.qsets[set].sections.flatMap((s) => s.questions).find((q) => q.id === id);
  document.querySelectorAll("[data-sq]").forEach((b) => b.onclick = (e) => { e.preventDefault(); const [set, id, opt] = b.dataset.sq.split("|"); speakQ(set, id, opt); });
  document.querySelectorAll("[data-qa]").forEach((b) => b.onclick = () => {
    const [set, id, val] = b.dataset.qa.split("|"); const q = find(set, id); const ans = answersOf(set);
    if (q.type === "single") ans[id] = ans[id] === val ? undefined : val;
    else {
      const opt = q.options.find((o) => o.value === val);
      let cur = Array.isArray(ans[id]) ? ans[id] : [];
      if (cur.includes(val)) cur = cur.filter((x) => x !== val);
      else cur = opt.exclusive ? [val] : [...cur.filter((x) => !q.options.find((o) => o.value === x)?.exclusive), val];
      ans[id] = cur;
    }
    rerender();
  });
  document.querySelectorAll("[data-qc]").forEach((b) => b.onclick = () => {
    const [set, id, d] = b.dataset.qc.split("|"); const q = find(set, id); const ans = answersOf(set);
    const cur = typeof ans[id] === "number" ? ans[id] : (q.start ?? q.min ?? 0) - Number(d);
    ans[id] = Math.max(q.min ?? 0, Math.min(q.max ?? 99, cur + Number(d)));
    rerender();
  });
  document.querySelectorAll("[data-qu]").forEach((b) => b.onclick = () => {
    const [set, id] = b.dataset.qu.split("|"); const ans = answersOf(set);
    ans[id] = ans[id] === "unknown" ? undefined : "unknown"; rerender();
  });
  document.querySelectorAll("[data-qi]").forEach((el) => {
    const [set, id] = el.dataset.qi.split("|");
    el.oninput = () => { answersOf(set)[id] = el.value; };
    el.onchange = () => { answersOf(set)[id] = el.value; rerender(); };  // e.g. a phone number reveals "Wants SMS reminders?"
  });
}
function keepScroll(fn) { const y = window.scrollY; fn(); window.scrollTo(0, y); }

function registration() {
  const r = S.reg;
  return `
    <div class="card">${qhead("Does she have a national ID card?", "id_question")}
      <p class="small muted" style="margin:0 0 10px">Asked first. Her care is the same either way.</p>
      ${choice("data-nid", "nin", "National NIN", "She has a national ID card", "idcard", "id_nin", r.national_id === "nin")}
      ${choice("data-nid", "none", "No ID", "She has no national ID card", "x", "id_none", r.national_id === "none")}
      ${r.national_id === "nin" ? `<label class="consent"><input type="checkbox" id="consent" ${r.consent ? "checked" : ""}>
        <span>She agrees to link her Ovamha record to her national ID.</span>
        <button class="icon-btn soft" data-prompt="id_consent" aria-label="Read aloud" type="button">${icon("speaker")}</button></label>
        <p class="tiny" style="margin:6px 0 0">Do not write down the number. Ovamha records only that the card was shown; it is linked later through the national ID service.</p>` : ""}
    </div>
    <div class="card">${qhead("When was she born?", "dob_question")}
      ${choice("data-dob", "exact", "Exact date", "She knows her date of birth", "calendar", "dob_exact", r.dobMode === "exact")}
      ${choice("data-dob", "estimate", "Estimate her age", "She does not know her date of birth", "user", "dob_estimate", r.dobMode === "estimate")}
      ${r.dobMode === "exact" ? `<input class="input" type="date" id="dob" value="${esc(r.birth_date || "")}" style="margin-top:10px">` : ""}
      ${r.dobMode === "estimate" ? `<div class="small muted" style="margin:12px 0 4px">About how old is she?</div>${stepper("age", r.age, false)}<div class="tiny">years, your best estimate · saved as an estimated birth year</div>` : ""}
    </div>
    ${S.qsets?.["anc-registration"] ? renderSet("anc-registration", S.qsets["anc-registration"], r.details) : ""}
    <div class="err">${esc(S.cardErr)}</div>
    <button class="btn primary" id="createCard" style="margin-top:6px">${icon("plus")}Create her card number</button>`;
}
function woman() {
  const w = S.st?.woman;
  let body;
  if (w) {
    const idLine = w.id_check ? `${icon("idcard")} National ID shown, with consent` : `${icon("x")} No national ID`;
    const dob = w.birth_date ? (w.birth_date_estimated ? `Born about ${w.birth_date} (estimated)` : `Born ${w.birth_date}`) : "";
    const who = w.name ? `<div style="font-weight:700;font-size:1.15rem;margin-top:4px">${esc(w.name)}</div>` : "";
    body = `<div class="card" style="text-align:center">
      <div class="badge green" style="margin-bottom:10px">${icon("check")}${w.new ? "New card number created" : "Card found"}</div>
      ${who}<div class="small muted">${w.new ? "Write this on her antenatal card" : "Her card number"}</div>
      <div class="card-code">${esc(w.card_code)}</div>
      <button class="btn soft" id="sayCard">${icon("speaker")}Read aloud</button>
      <div class="small muted" style="margin-top:12px;display:flex;flex-direction:column;gap:4px;align-items:center">
        <span style="display:inline-flex;gap:6px;align-items:center">${idLine}</span>${dob ? `<span>${esc(dob)}</span>` : ""}
        ${w.new ? "" : `<span>${w.visits} previous ${w.visits === 1 ? "check" : "checks"} on this device</span>`}</div>
    </div>
    <div style="margin-top:16px"><button class="btn primary" id="toDescribe">Continue${icon("right")}</button></div>`;
  } else if (S.cardMode === "new") {
    body = registration();
  } else if (S.cardMode === "find") {
    body = `<div class="card"><h3>Her card number</h3><p class="small muted" style="margin:2px 0 12px">6 characters, as written on her antenatal card.</p>
      <input class="input card-input" id="card" autocapitalize="characters" autocorrect="off" spellcheck="false" maxlength="7" placeholder="K7P-3QZ">
      <div class="err">${esc(S.cardErr)}</div>
      <div class="row" style="margin-top:6px"><button class="btn soft" id="cardBack">Back</button><button class="btn primary" id="findCard">Find</button></div></div>`;
  } else {
    body = choice("data-mode", "new", "First visit", "Register her and create a card number", "plus", "visit_first", false)
      + choice("data-mode", "find", "Returning", "Enter the number on her card", "file", "visit_returning", false);
  }
  const title = S.cardMode === "new" && !w ? "First visit" : "Who is this check for?";
  return `<div class="screen">${topbar(title, "home")}${body}</div>${nav("describe")}`;
}
bind.woman = () => {
  const set = (st) => { S.st = st; S.cardErr = ""; render(); window.scrollTo(0, 0); };
  document.querySelectorAll("[data-prompt]").forEach((b) => b.onclick = (e) => { e.preventDefault(); speakPrompt(b.dataset.prompt); });
  document.querySelectorAll("[data-mode]").forEach((b) => b.onclick = () => {
    S.cardMode = b.dataset.mode; S.cardErr = "";
    if (S.cardMode === "new") S.reg = { national_id: null, consent: false, dobMode: null, birth_date: "", age: 25, details: {} };
    const show = () => { render(); window.scrollTo(0, 0); };
    if (S.cardMode === "new") qset("anc-registration").then(show).catch((e) => toast(e.message)); else show();
    if (S.cardMode === "find") $("#card").focus();
  });
  document.querySelectorAll("[data-nid]").forEach((b) => b.onclick = () => { S.reg.national_id = b.dataset.nid; render(); });
  document.querySelectorAll("[data-dob]").forEach((b) => b.onclick = () => { S.reg.dobMode = b.dataset.dob; render(); });
  $("#consent") && ($("#consent").onchange = (e) => { S.reg.consent = e.target.checked; });
  $("#dob") && ($("#dob").onchange = (e) => { S.reg.birth_date = e.target.value; });
  if (S.reg) bindSet(() => S.reg.details, () => keepScroll(render));
  const keyOf = { age: "age" };
  document.querySelectorAll("[data-step]").forEach((b) => b.onclick = () => {
    const k = keyOf[b.dataset.step], lo = k === "age" ? 10 : 0, hi = k === "age" ? 60 : 20;
    S.reg[k] = Math.max(lo, Math.min(hi, (Number(S.reg[k]) || 0) + Number(b.dataset.d)));
    render();
  });
  document.querySelectorAll("[data-unknown]").forEach((b) => b.onclick = () => {
    const k = keyOf[b.dataset.unknown];
    S.reg[k] = S.reg[k] === "unknown" ? 0 : "unknown";
    render();
  });
  $("#createCard") && ($("#createCard").onclick = () => {
    const r = S.reg;
    if (!r.national_id) { S.cardErr = "Answer the national ID question first."; render(); return; }
    if (r.national_id === "nin" && !r.consent) { S.cardErr = "Ask for her consent, or choose No ID."; render(); return; }
    if (!r.dobMode) { S.cardErr = "Answer when she was born: exact date or estimate."; render(); return; }
    const body = { national_id: r.national_id, consent: r.consent, details: Object.fromEntries(Object.entries(r.details).filter(([, v]) => v !== undefined && v !== "")) };
    if (r.dobMode === "exact") body.birth_date = r.birth_date || null; else body.age_years = r.age;
    api("/api/woman/new", { body }).then(set).catch((e) => { S.cardErr = e.message; render(); });
  });
  $("#cardBack") && ($("#cardBack").onclick = () => { S.cardMode = null; S.cardErr = ""; render(); });
  const find = () => api("/api/woman/find", { body: { card_code: $("#card").value } }).then(set).catch((e) => { S.cardErr = e.message; render(); });
  $("#findCard") && ($("#findCard").onclick = find);
  $("#card") && ($("#card").onkeydown = (e) => { if (e.key === "Enter") find(); });
  $("#sayCard") && ($("#sayCard").onclick = () => speakText(`Card number: ${S.st.woman.card_code.replace("-", "").split("").join(", ")}`, "en"));
  $("#toDescribe") && ($("#toDescribe").onclick = () => go("describe"));
};

// ---------------------------------------------------------------- 4. describe (record -> replay / next)
let recTimer = null;
function describe() {
  const langName = Object.fromEntries(LANGS)[S.lang];
  const live = !!S.rec;
  let body;
  if (S.typing) {
    body = `<div class="card"><h3>Type what was said</h3>
      <textarea class="input" id="tx" placeholder="e.g. She is 28 weeks and bleeding heavily since morning…">${esc(S.transcript)}</textarea>
      <div style="margin-top:12px" class="row"><button class="btn soft" id="toVoice">${icon("mic")}Use voice</button><button class="btn primary" id="nextTyped">Next${icon("right")}</button></div></div>`;
  } else if (S.audioBlob && !live) {
    body = `<div class="card rec">
      <div class="badge green" style="margin-bottom:10px">${icon("check")}Recorded ${S.recSecs}s</div>
      <h3 style="font-size:1.2rem">Check the recording</h3>
      <p class="muted small" style="margin:4px 0 18px">Listen to what you said, or go on to the read-back.</p>
      <audio id="myRecording" src="${S.audioUrl}" preload="auto" hidden></audio>
      <div class="stack">
        <button class="btn outline" id="replay">${icon("replay")}Replay guidance</button>
        <button class="btn primary" id="next">Next${icon("right")}</button>
        <button class="link" id="again">Record again</button>
      </div></div>`;
  } else {
    body = `<div class="card rec">
      <h3 style="font-size:1.2rem">${live ? "Listening…" : "Tap and describe the woman's situation"}</h3>
      <p class="muted small" style="margin:4px 0 0">${live ? "Tap again when you have finished." : `Speak in ${langName}. Symptoms and history. Numbers come next, on the keypad.`}</p>
      <button class="mic ${live ? "live" : ""}" id="mic" aria-label="${live ? "Stop recording" : "Start recording"}">${icon(live ? "stop" : "mic")}</button>
      <div class="wave ${live ? "live-wave" : ""}">${"<i></i>".repeat(9)}</div>
      <div class="timer" id="timer">${live ? fmtSecs(S.recSecs) : ""}</div>
      ${live ? "" : `<div class="row" style="margin-top:4px"><button class="btn soft" id="guide">${icon("speaker")}Hear guidance</button></div>
        <button class="link" id="type">${icon("keyboard")} Type instead</button>`}
    </div>`;
  }
  return `<div class="screen">${topbar("Describe", "woman")}${steps(1)}
    <div class="chips" style="margin-bottom:14px">${LANGS.map(([c, n]) => `<button class="chip ${S.lang === c ? "on" : ""}" data-lang="${c}">${n}</button>`).join("")}</div>
    ${body}
    <p class="tiny" style="text-align:center;margin-top:16px">Speech is turned into text on this device. Nothing is sent to the internet.</p>
  </div>${nav("describe")}`;
}
const fmtSecs = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
bind.describe = () => {
  document.querySelectorAll("[data-lang]").forEach((b) => b.onclick = () => { S.lang = b.dataset.lang; render(); });
  $("#mic") && ($("#mic").onclick = toggleRecord);
  $("#type") && ($("#type").onclick = () => { S.typing = true; render(); });
  $("#toVoice") && ($("#toVoice").onclick = () => { S.transcript = $("#tx").value; S.typing = false; render(); });
  // Replay guidance = play back the worker's own recording (the native player decodes webm/mp4 reliably).
  $("#replay") && ($("#replay").onclick = () => {
    const a = $("#myRecording");
    if (!a) return;
    a.currentTime = 0;
    a.play().catch(() => playBlob(S.audioBlob));
  });
  $("#guide") && ($("#guide").onclick = () => speakPrompt("guide_describe"));
  $("#again") && ($("#again").onclick = () => { S.audioBlob = null; S.audioUrl = null; render(); });
  $("#next") && ($("#next").onclick = transcribeAndRead);
  $("#nextTyped") && ($("#nextTyped").onclick = () => readBack($("#tx").value));
};
async function toggleRecord() {
  if (S.rec) { S.rec.stop(); return; }
  try {
    S.recSecs = 0;
    S.rec = await startRecorder((blob) => {
      clearInterval(recTimer); S.rec = null;
      if (S.audioUrl) URL.revokeObjectURL(S.audioUrl);
      S.audioBlob = blob; S.audioUrl = URL.createObjectURL(blob);
      render();
    });
    if (!S.rec) return;
    render();
    recTimer = setInterval(() => { S.recSecs++; const t = $("#timer"); if (t) t.textContent = fmtSecs(S.recSecs); }, 1000);
  } catch (e) { toast("Microphone not available: " + e.message, 4000); }
}
async function transcribeAndRead() {
  const done = busy("Turning speech into text, offline…");
  try {
    const fd = new FormData();
    fd.append("audio", S.audioBlob, `description.${extFor(S.audioBlob)}`);
    fd.append("lang", S.lang);
    const r = await api("/api/transcribe", { form: fd });
    done();
    if (r.note) toast(r.note, 4000);
    await readBack(r.text);
  } catch (e) { done(); toast(e.data?.message || e.message, 4500); }
}
async function readBack(text) {
  if (!text || !text.trim()) { toast("Nothing to read back yet."); return; }
  try {
    S.transcript = text;
    S.st = await api("/api/extract", { body: { transcript: text, lang: S.lang } });
    go("confirm");
  } catch (e) { toast(e.message); }
}

// ---------------------------------------------------------------- 5. confirm (read-back)
// Compact list rows: tinted icon, title + one-line subtitle, quiet actions.
function itemCard(it) {
  const warn = it.source === "ai-safety-net", ok = it.confirmed;
  const value = ok ? it.confirmed_value : it.display;
  const sub = warn ? "AI noticed this. Please check." : `Heard: “${it.evidence || ""}”`;
  let acts = "";
  if (ok) {
    acts = `<button class="row-link" data-undo="${it.field}">Change</button>`;
  } else if (it.kind === "severity" && it.value === true) {
    acts = `<div class="row-acts"><span class="row-q">How bad?</span>
      <button class="pill" data-set="${it.field}" data-v="severe">Severe</button>
      <button class="pill" data-set="${it.field}" data-v="mild">Mild</button>
      <button class="pill ghost" data-no="${it.field}">Not true</button></div>`;
  } else {
    acts = `<div class="row-acts"><button class="pill primary" data-ok="${it.field}">${icon("check")}Correct</button>
      <button class="pill ghost" data-no="${it.field}">Not true</button></div>`;
  }
  return `<div class="row-item ${ok ? "on" : ""} ${warn && !ok ? "warn" : ""}">
    <div class="row-main">
      <span class="row-ico">${icon(ok ? "check" : FIELD_ICON[it.field] || "file")}</span>
      <div class="row-text"><div class="row-title">${esc(it.label)} <span class="row-val">· ${esc(value)}</span></div>
        <div class="row-sub">${esc(sub)}</div></div>
      <button class="row-say" data-say="${it.field}" aria-label="Read aloud">${icon("speaker")}</button>
    </div>${acts}</div>`;
}
function confirm() {
  const items = (S.st?.items || []).filter((i) => !["gestational_age_weeks", "systolic", "diastolic", "systolic_repeat", "diastolic_repeat", "pulse", "temperature", "fetal_heart_rate", "urine_protein", "severe_pe_symptoms"].includes(i.field));
  const pending = items.filter((i) => !i.confirmed).length;
  return `<div class="screen">${topbar("What we understood", "describe")}${steps(2)}
    <div class="said"><div style="flex:1"><div class="row-sub" style="margin:0 0 2px">What was said</div>${esc(S.st?.transcript || "")}</div>
      <button class="row-say" id="sayAll" aria-label="Read aloud">${icon("speaker")}</button></div>
    ${(S.st?.notes || []).map((n) => `<div class="note-line">${icon("calendar")}${esc(n)}</div>`).join("")}
    <div class="list-head">${pending ? `${pending} to confirm` : "All checked"}<span>Only confirmed items count</span></div>
    <div class="row-list">${items.length ? items.map(itemCard).join("") : `<div class="row-sub" style="padding:14px">Nothing was picked up. Go on to measurements, or describe again.</div>`}</div>
  </div>
  <div class="sticky">${statusBanner()}<button class="btn primary" id="toMeasure">Next: measurements${icon("right")}</button></div>`;
}
// Information only: the guideline advice and the worker's decision come at the end.
function statusBanner() {
  const p = S.st?.preview;
  if (!p) return `<div class="status-line">${icon("shield")}Confirm what is correct. Advice comes at the end.</div>`;
  if (p.danger || p.referral) return `<div class="status-line warn">${icon("alert")}Danger sign confirmed. You will see the guideline advice and decide at the end.</div>`;
  if (p.ask_next.length) return `<div class="status-line">${icon("alert")}Still needed: ${esc(p.ask_next.slice(0, 3).map((a) => a.label).join(", "))}${p.ask_next.length > 3 ? "…" : ""}</div>`;
  return `<div class="status-line ok">${icon("check")}No danger sign on confirmed items</div>`;
}
bind.confirm = () => {
  const act = (path, body) => api(path, { body }).then((st) => { S.st = st; render(); }).catch((e) => toast(e.message));
  document.querySelectorAll("[data-ok]").forEach((b) => b.onclick = () => act("/api/confirm", { field: b.dataset.ok }));
  document.querySelectorAll("[data-set]").forEach((b) => b.onclick = () => act("/api/confirm", { field: b.dataset.set, value: b.dataset.v }));
  document.querySelectorAll("[data-no]").forEach((b) => b.onclick = () => act("/api/reject", { field: b.dataset.no }));
  document.querySelectorAll("[data-undo]").forEach((b) => b.onclick = () => act("/api/unconfirm", { field: b.dataset.undo }));
  document.querySelectorAll("[data-say]").forEach((b) => b.onclick = () => speakItem(b.dataset.say));
  $("#sayAll").onclick = () => speakText(S.st?.transcript || "", S.lang === "en" ? "en" : S.lang);
  $("#toMeasure").onclick = () => {
    if (S.st?.needs_profile && !S.st?.preview?.danger) {
      S.ans = S.ans || {}; S.ans["anc-profile"] = S.ans["anc-profile"] || {};
      qset("anc-profile").then(() => go("history")).catch((e) => toast(e.message));
    } else go("measure");
  };
};

// ---------------------------------------------------------------- 5b. history and profile (ANC.B6, first contact only)
function history() {
  const def = S.qsets["anc-profile"], ans = S.ans["anc-profile"];
  const ga = ans.ga_source === "lmp" && ans.lmp ? lmpInfo(ans.lmp) : "";
  return `<div class="screen">${topbar("Her history", "confirm")}${steps(3)}
    <div class="banner blue">${icon("file")}First contact: WHO antenatal care asks these once (ANC.B6). Use Don't know when she is not sure.</div>
    ${renderSet("anc-profile", def, ans)}
    ${ga ? `<div class="banner green">${icon("calendar")}${ga}</div>` : ""}
    <div class="err">${esc(S.histErr || "")}</div>
  </div>
  <div class="sticky"><button class="btn primary" id="saveHistory">${icon("check")}Save history and continue</button></div>`;
}
function lmpInfo(lmp) {
  // Same arithmetic as the server (UTC calendar days): GA = (today - LMP) / 7, EDD = LMP + 280 days.
  const d = new Date(lmp + "T00:00:00Z"), now = new Date(), today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.round((today - d) / 864e5);
  if (isNaN(days) || days < 0) return "";
  const edd = new Date(d.getTime() + 280 * 864e5);
  return `About ${(days / 7).toFixed(1)} weeks pregnant · due around ${edd.toLocaleDateString([], { dateStyle: "medium", timeZone: "UTC" })}`;
}
bind.history = () => {
  bindSet((set) => S.ans[set], () => keepScroll(render));
  $("#saveHistory").onclick = () => {
    const answers = Object.fromEntries(Object.entries(S.ans["anc-profile"]).filter(([, v]) => v !== undefined && v !== "" && !(Array.isArray(v) && !v.length)));
    api("/api/profile", { body: { answers } }).then((st) => { S.st = st; S.histErr = ""; go("measure"); })
      .catch((e) => { S.histErr = e.message; keepScroll(render); const el = $(".err"); el && el.scrollIntoView({ block: "center" }); });
  };
};

// ---------------------------------------------------------------- 6. measurements (keypad default, voice optional)
const MEASURES = [
  { id: "ga", prompt: "ask_ga", title: "Gestational age", icon: "calendar", fields: [["gestational_age_weeks", "weeks"]] },
  { id: "bp", prompt: "ask_bp", title: "Blood pressure", icon: "heart", fields: [["systolic", "systolic"], ["diastolic", "diastolic"]], unit: "mmHg · say “90 over 60”" },
  { id: "bp2", prompt: "ask_bp_repeat", title: "Repeat blood pressure", icon: "heart", fields: [["systolic_repeat", "systolic"], ["diastolic_repeat", "diastolic"]], unit: "mmHg · only if the first was high", optional: true },
  { id: "pulse", prompt: "ask_pulse", title: "Pulse", icon: "heart", fields: [["pulse", "/min"]], optional: true },
  { id: "temp", prompt: "ask_temp", title: "Temperature", icon: "temp", fields: [["temperature", "°C"]], optional: true },
  { id: "fhr", prompt: "ask_fhr", title: "Fetal heart rate", icon: "baby", fields: [["fetal_heart_rate", "/min"]], optional: true },
];
const item = (f) => (S.st?.items || []).find((i) => i.field === f);
function measureCard(m) {
  const allOk = m.fields.every(([f]) => item(f)?.confirmed);
  const inputs = m.fields.map(([f, u], k) => `${k ? '<span class="sep">/</span>' : ""}<input class="num" inputmode="decimal" id="n-${f}" placeholder="${esc(u)}" value="${esc(item(f)?.value ?? S.numbers[f] ?? "")}" ${allOk ? "disabled" : ""}>`).join("");
  const live = S.numRec === m.id;
  return `<div class="card measure">
    <div style="display:flex;align-items:center;gap:10px"><span class="icon-btn soft" style="width:40px;height:40px">${icon(m.icon)}</span>
      <h3 style="flex:1;margin:0">${m.title}${m.optional ? ' <span class="tiny">optional</span>' : ""}</h3>
      <button class="icon-btn soft" data-prompt="${m.prompt}" aria-label="Read the question aloud">${icon("speaker")}</button></div>
    <div class="num-row">${inputs}${allOk ? "" : `<button class="mic-sm ${live ? "live" : ""}" data-mrec="${m.id}" aria-label="Say the number">${icon(live ? "stop" : "mic")}</button>`}</div>
    ${m.unit ? `<div class="unit">${esc(m.unit)}</div>` : ""}
    ${allOk ? `<div class="done-line">${icon("check")}Confirmed <button class="link small" data-msay="${m.id}">Read back</button><button class="link small" data-mundo="${m.id}">Change</button></div>`
      : `<div class="row" style="margin-top:12px"><button class="btn soft" data-msay="${m.id}">${icon("speaker")}Read back</button><button class="btn primary" data-mok="${m.id}">${icon("check")}Confirm</button></div>`}
  </div>`;
}
const choiceKey = (v) => (v === true ? "yes" : v === false ? "no" : String(v));
function choiceCard(field, title, opts, ic, prompt) {
  const it = item(field);
  return `<div class="card measure"><div style="display:flex;align-items:center;gap:10px"><span class="icon-btn soft" style="width:40px;height:40px">${icon(ic)}</span><h3 style="flex:1;margin:0">${title} <span class="tiny">optional</span></h3>
    <button class="icon-btn soft" data-prompt="${prompt}" aria-label="Read the question aloud">${icon("speaker")}</button></div>
    <div class="seg">${opts.map(([v, l]) => `<button data-choice="${field}" data-v="${esc(v)}" class="${it?.confirmed && choiceKey(it.value) === v ? "on" : ""}">${l}</button>`).join("")}</div>
    ${it?.confirmed ? `<div class="done-line">${icon("check")}Confirmed: ${esc(it.confirmed_value)} <button class="link small" data-csay="${field}">Read back</button></div>` : ""}</div>`;
}
function measure() {
  const danger = S.st?.preview?.danger;
  return `<div class="screen">${topbar("Measurements", "confirm")}${steps(4)}
    ${danger && S.st?.needs_profile ? `<div class="note-line">${icon("file")}Her full history can wait because of the danger sign. Complete it at her next contact.</div>` : ""}
    ${danger ? `<div class="note-line warn">${icon("alert")}Danger sign confirmed. Measurements are optional; you decide at the end.</div>` : `<p class="muted small" style="margin-top:0">Type the numbers, or tap the microphone and say them. Each one is read back for you to confirm.</p>`}
    ${MEASURES.map(measureCard).join("")}
    ${choiceCard("urine_protein", "Urine protein", [["negative", "Negative"], ["trace", "Trace"], ["+", "+"], ["++", "++"], ["+++", "+++"], ["unknown", "Not done"]], "flask", "ask_protein")}
    ${choiceCard("severe_pe_symptoms", "Severe pre-eclampsia symptoms", [["yes", "Yes"], ["no", "No"], ["unknown", "Don't know"]], "alert", "ask_severe_pe")}
  </div>
  <div class="sticky">${statusBanner()}<button class="btn primary" id="finish">${icon("shield")}Check the guidelines</button></div>`;
}
bind.measure = () => {
  const refresh = (st) => { S.st = st; render(); };
  const readInputs = (m) => m.fields.map(([f]) => [f, $(`#n-${f}`).value.trim()]);
  document.querySelectorAll("input.num").forEach((el) => el.oninput = () => { S.numbers[el.id.slice(2)] = el.value; });
  document.querySelectorAll("[data-mok]").forEach((b) => b.onclick = async () => {
    const m = MEASURES.find((x) => x.id === b.dataset.mok);
    const vals = readInputs(m);
    if (vals.some(([, v]) => v === "")) { toast("Enter every number first"); return; }
    try {
      let st;
      for (const [f, v] of vals) { await api("/api/measure", { body: { field: f, value: v } }); st = await api("/api/confirm", { body: { field: f } }); }
      refresh(st);
    } catch (e) { toast(e.message, 4000); }
  });
  document.querySelectorAll("[data-msay]").forEach((b) => b.onclick = async () => {
    const m = MEASURES.find((x) => x.id === b.dataset.msay);
    const vals = readInputs(m);
    if (vals.some(([, v]) => v === "")) { toast("Enter the number first"); return; }
    const words = vals.map(([f, v]) => v).join(" over ");
    speakText(`${m.title}: ${words}`, "en");
  });
  document.querySelectorAll("[data-mundo]").forEach((b) => b.onclick = async () => {
    const m = MEASURES.find((x) => x.id === b.dataset.mundo);
    let st;
    for (const [f] of m.fields) st = await api("/api/reject", { body: { field: f } });
    refresh(st);
  });
  document.querySelectorAll("[data-mrec]").forEach((b) => b.onclick = () => recordNumber(MEASURES.find((x) => x.id === b.dataset.mrec)));
  document.querySelectorAll("[data-choice]").forEach((b) => b.onclick = async () => {
    try {
      await api("/api/measure", { body: { field: b.dataset.choice, value: b.dataset.v } });
      refresh(await api("/api/confirm", { body: { field: b.dataset.choice } }));
    } catch (e) { toast(e.message); }
  });
  document.querySelectorAll("[data-csay]").forEach((b) => b.onclick = () => speakItem(b.dataset.csay));
  document.querySelectorAll("[data-prompt]").forEach((b) => b.onclick = () => speakPrompt(b.dataset.prompt));
  $("#finish").onclick = finish;
};
let numRecorder = null;
async function recordNumber(m) {
  if (numRecorder) { numRecorder.stop(); return; }
  try {
    numRecorder = await startRecorder(async (blob) => {
      numRecorder = null; S.numRec = null; render();
      const done = busy("Listening for the number…");
      try {
        const fd = new FormData();
        fd.append("audio", blob, `number.${extFor(blob)}`);
        fd.append("field", m.fields[0][0]);
        fd.append("lang", S.lang);
        const r = await api("/api/number-voice", { form: fd });
        done();
        Object.assign(S.numbers, r.values);
        render();
        const words = m.fields.map(([f]) => r.values[f]).filter((v) => v !== undefined).join(" over ");
        toast(`Heard: ${r.heard}. Check it, then tap Confirm.`, 4000);
        speakText(`${m.title}: ${words}`, "en");
      } catch (e) { done(); toast(e.data?.message || e.message, 4500); }
    });
    if (numRecorder) { S.numRec = m.id; render(); }
  } catch (e) { toast("Microphone not available: " + e.message, 4000); }
}
async function finish() {
  const done = busy("Checking the guidelines…");
  try {
    S.assess = await api("/api/finish");
    S.decision = { choice: null, reason: "" };
    S.counts.checks++;
    done(); go("advice");
  } catch (e) { done(); toast(e.message); }
}

// ---------------------------------------------------------------- 7. guideline advice -> the worker's decision
const KIND_STYLE = { urgent_referral: "red", refer_cemonc: "red", refer_assessment: "amber", plan_cemonc_delivery: "amber", check_now: "amber" };
const SUGGEST_TEXT = {
  urgent_referral: "The guidelines suggest urgent referral.",
  refer_cemonc: "The guidelines suggest referral to a CEmONC facility.",
  refer_assessment: "The guidelines suggest referral to CEmONC for assessment.",
  plan_cemonc_delivery: "High-risk pregnancy: the guidelines suggest planning delivery at a CEmONC facility.",
  none: "No referral suggested on the confirmed information.",
};
// Advice as clean list rows: the reasons are the title; tap to see the full suggestion and its source.
function adviceRow(x, idx) {
  const style = KIND_STYLE[x.kind] || "amber";
  return `<details class="row-item adv ${style}">
    <summary class="row-main">
      <span class="row-ico">${icon(x.kind === "plan_cemonc_delivery" ? "calendar" : "alert")}</span>
      <div class="row-text"><div class="row-title">${esc(x.reasons.join(", "))}</div>
        <div class="row-sub">${esc(x.kindTitle)} · ${esc(x.who)}</div></div>
      <button class="row-say" data-say-adv="${idx}" aria-label="Read aloud">${icon("speaker")}</button>
    </summary>
    <div class="row-more"><div><span class="muted">Guideline suggests:</span> ${esc(x.rec)}</div>
      ${(x.assumptions || []).map((a) => `<div class="tiny" style="margin-top:6px">Assumption: ${esc(a)}</div>`).join("")}
      <div class="tiny" style="margin-top:8px">${esc(x.cite)}</div></div>
  </details>`;
}
function adviceItems() {
  const a = S.assess, items = [];
  a.rules.filter((r) => r.status === "fired").forEach((r) => items.push({ who: "WHO antenatal care", kind: "urgent_referral", kindTitle: "Danger signs requiring referral",
    reasons: r.reasons, rec: r.actions.join(". ") + ".", cite: `${r.source}. ${r.label}.`, assumptions: [] }));
  a.advice.forEach((x) => items.push({ who: "Sierra Leone guideline", kind: x.kind, kindTitle: x.kind_title, reasons: x.reasons,
    rec: x.recommendation, cite: `${x.source}: ${x.cite}`, assumptions: x.assumptions }));
  return items;
}
function decRow(v, title, sub, ic) {
  const on = S.decision.choice === v;
  return `<button class="row-item choice ${on ? "on" : ""}" data-choice-dec="${v}"><div class="row-main">
    <span class="row-ico">${icon(on ? "check" : ic)}</span>
    <div class="row-text"><div class="row-title">${title}</div><div class="row-sub">${sub}</div></div></div></button>`;
}
function advice() {
  const a = S.assess, items = adviceItems(), sug = a.suggestion, d = S.decision;
  const needsReason = (sug !== "none" && d.choice === "none") || (sug === "urgent_referral" && d.choice === "planned");
  const recording = S.reasonRec;
  return `<div class="screen">${topbar("Guideline advice", "measure")}${steps(5)}
    <div class="status-line ${sug === "none" ? "ok" : "warn"}" style="margin:0">${icon(sug === "none" ? "check" : "alert")}${esc(SUGGEST_TEXT[sug])} You decide.</div>
    <div class="list-head">What the guidelines say<span>Tap a row for details</span></div>
    <div class="row-list">${items.length ? items.map(adviceRow).join("") : `<div class="row-sub" style="padding:8px 2px">Nothing to suggest on the confirmed information.</div>`}</div>
    ${a.ask_next?.length && !a.danger ? `<div class="note-line warn">${icon("alert")}Not checked (missing): ${esc(a.ask_next.map((q) => q.label).join(", "))}</div>` : ""}
    ${a.next_contact?.text ? `<div class="note-line">${icon("calendar")}Next contact: ${esc(a.next_contact.text)}</div>` : ""}
    <div class="list-head">Your decision</div>
    <div class="row-list">
      ${decRow("urgent", "Refer urgently", "Emergency: consent, stabilise, call the ambulance", "alert")}
      ${decRow("planned", "Plan a referral", "Assessment or delivery at a CEmONC facility", "calendar")}
      ${decRow("none", "No referral now", "Continue care here", "home")}
    </div>
    ${needsReason ? `<div class="list-head">Your reason<span>Needed when you differ from the suggestion</span></div>
      <div class="reason-box"><textarea id="decReason" placeholder="Say or type your reason">${esc(d.reason)}</textarea>
        <button class="mic-sm ${recording ? "live" : ""}" id="reasonMic" aria-label="${recording ? "Stop" : "Say your reason"}">${icon(recording ? "stop" : "mic")}</button></div>` : ""}
    <div class="err">${esc(S.decErr || "")}</div>
  </div>
  <div class="sticky"><button class="btn primary" id="confirmDecision" ${d.choice ? "" : "disabled"}>${icon("check")}Confirm my decision</button></div>`;
}
let reasonRecorder = null;
bind.advice = () => {
  const items = adviceItems();
  document.querySelectorAll("[data-say-adv]").forEach((b) => b.onclick = (e) => {
    e.preventDefault(); e.stopPropagation();
    const x = items[Number(b.dataset.sayAdv)];
    speakText(`${x.reasons.join(", ")}. Guideline suggests: ${x.rec}`, "en");
  });
  document.querySelectorAll("[data-choice-dec]").forEach((b) => b.onclick = () => { S.decision.choice = b.dataset.choiceDec; S.decErr = ""; keepScroll(render); });
  $("#decReason") && ($("#decReason").oninput = (e) => { S.decision.reason = e.target.value; });
  $("#reasonMic") && ($("#reasonMic").onclick = async () => {
    if (reasonRecorder) { reasonRecorder.stop(); return; }
    try {
      reasonRecorder = await startRecorder(async (blob) => {
        reasonRecorder = null; S.reasonRec = false; keepScroll(render);
        const done = busy("Writing down your reason…");
        try {
          const fd = new FormData();
          fd.append("audio", blob, `reason.${extFor(blob)}`); fd.append("lang", S.lang);
          const r = await api("/api/transcribe", { form: fd });
          done();
          S.decision.reason = [S.decision.reason, r.text].filter(Boolean).join(" ");
          keepScroll(render);
        } catch (e) { done(); toast(e.data?.message || e.message, 4000); }
      });
      if (reasonRecorder) { S.reasonRec = true; keepScroll(render); }
    } catch (e) { toast("Microphone not available: " + e.message, 4000); }
  });
  $("#confirmDecision").onclick = async () => {
    try {
      const r = await api("/api/decision", { body: { choice: S.decision.choice, reason: S.decision.reason || null } });
      if (r.next === "referral") { S.isbar = r.isbar; S.ref = { consent: null, checklist: [], call_time: "", ambulance_time: "" }; go("referral"); }
      else { S.result = r; if (r.referral) S.counts.referrals++; go("result"); }
    } catch (e) { S.decErr = e.message; keepScroll(render); }
  };
};

// ---------------------------------------------------------------- 7b. urgent referral pathway (national guideline)
const nowHM = () => new Date().toTimeString().slice(0, 5);
const ISBAR = [["I", "Identification"], ["S", "Situation"], ["B", "Background"], ["A", "Assessment"], ["R", "Recommendation"]];
function referral() {
  const p = S.assess.pathway, r = S.ref, sb = S.isbar;
  const no = r.consent === false;
  const consentRow = (v, title, sub, ic) => `<button class="row-item choice ${r.consent === v ? "on" : ""}" data-consent="${v ? "yes" : "no"}"><div class="row-main">
      <span class="row-ico">${icon(r.consent === v ? "check" : ic)}</span><div class="row-text"><div class="row-title">${title}</div><div class="row-sub">${sub}</div></div></div></button>`;
  return `<div class="screen">${topbar("Urgent referral", "advice")}
    <div class="status-line warn" style="margin:0">${icon("alert")}You decided on urgent referral. Follow the national referral pathway.</div>
    <div class="list-head">1 · Consent<button class="row-say" data-say-text="consent" aria-label="Read aloud">${icon("speaker")}</button></div>
    <div class="row-sub" style="white-space:normal;margin:-4px 2px 10px">${esc(p.consent)}</div>
    <div class="row-list">${consentRow(true, "She agrees", "Continue the referral", "check")}${consentRow(false, "She refuses", "Record her refusal and keep caring for her", "x")}</div>
    ${no ? "" : `<div class="list-head">2 · Before she leaves<span>Do what your level allows</span></div>
      <div class="row-list">${p.emergency_checklist.map((t, i) => {
        const on = r.checklist.includes(i);
        return `<label class="row-item check ${on ? "on" : ""}"><div class="row-main"><input type="checkbox" data-check="${i}" ${on ? "checked" : ""}>
          <span class="row-title" style="font-weight:600">${esc(t)}</span></div></label>`;
      }).join("")}</div>
      <div class="list-head">3 · Call the call centre<button class="row-say" data-say-text="isbar" aria-label="Read iSBAR aloud">${icon("speaker")}</button></div>
      <div class="isbar-list">${ISBAR.map(([k, n]) => `<div class="isbar-row"><span class="isbar-k">${k}</span>
        <div><div class="row-sub" style="white-space:normal;margin:0">${n}</div><div>${esc(sb[k])}</div></div></div>`).join("")}</div>
      <div class="row" style="margin-top:12px">
        <label class="time-box"><span class="row-sub">Called at</span><input type="time" id="callTime" value="${esc(r.call_time)}"></label>
        <label class="time-box"><span class="row-sub">Ambulance arrived</span><input type="time" id="ambTime" value="${esc(r.ambulance_time)}"></label></div>
      <button class="row-link" style="margin-left:2px" id="calledNow">I called just now</button>`}
    <div class="err">${esc(S.refErr || "")}</div>
  </div>
  <div class="sticky"><button class="btn ${no ? "soft" : "danger"}" id="completeRef" ${r.consent === null ? "disabled" : ""}>${icon(no ? "file" : "send")}${no ? "Record refusal" : "Refer digitally and prepare the letter"}</button></div>`;
}
bind.referral = () => {
  const r = S.ref;
  document.querySelectorAll("[data-consent]").forEach((b) => b.onclick = () => { r.consent = b.dataset.consent === "yes"; keepScroll(render); });
  document.querySelectorAll("[data-check]").forEach((el) => el.onchange = () => {
    const i = Number(el.dataset.check);
    r.checklist = el.checked ? [...new Set([...r.checklist, i])] : r.checklist.filter((x) => x !== i);
    keepScroll(render);
  });
  $("#callTime") && ($("#callTime").onchange = (e) => { r.call_time = e.target.value; });
  $("#ambTime") && ($("#ambTime").onchange = (e) => { r.ambulance_time = e.target.value; });
  $("#calledNow") && ($("#calledNow").onclick = () => { r.call_time = nowHM(); keepScroll(render); });
  document.querySelectorAll("[data-say-text]").forEach((b) => b.onclick = () => {
    if (b.dataset.sayText === "consent") speakText(S.assess.pathway.consent, "en");
    else speakText(ISBAR.map(([k]) => S.isbar[k]).join(" "), "en");
  });
  $("#completeRef").onclick = async () => {
    try {
      S.result = await api("/api/referral/complete", { body: { consent: r.consent, checklist: r.checklist, call_time: r.call_time || null, ambulance_time: r.ambulance_time || null } });
      if (S.result.referral) S.counts.referrals++;
      go("result");
    } catch (e) { S.refErr = e.message; keepScroll(render); }
  };
};

// ---------------------------------------------------------------- referral letter (printable, two logo slots)
// Slot 1: facility / Ministry logo, supplied by the team as web/branding/logo-left.png (with permission).
// Slot 2: Ovamha. Elements follow the guideline's referral form: findings, treatment before referral,
// specific reasons, and a feedback slip for the receiving facility (two-way referral).
function letterHtml(L, leftLogo) {
  const li = (xs) => xs && xs.length ? `<ul>${xs.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : `<div class="small">None recorded</div>`;
  const when = new Date(L.date);
  const row = (k, v) => v ? `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>` : "";
  return `<div class="letter">
    <div class="lh">
      <div class="logo">${leftLogo ? `<img src="${leftLogo}" alt="Facility logo">` : `<div class="ph">Facility / MoHS logo</div>`}</div>
      <div class="mid"><b>${esc(L.from.facility)}</b><span class="small">${esc(L.from.level)} · Antenatal care</span></div>
      <div class="logo">${LOGO}</div>
    </div>
    <h1>REFERRAL LETTER</h1>
    ${L.urgent ? `<div class="urgent">URGENT · EMERGENCY REFERRAL</div>` : `<div class="small" style="text-align:center">${esc(L.type)}</div>`}
    <div class="meta">
      <div><b>Date:</b> ${esc(when.toLocaleDateString([], { dateStyle: "long" }))}, ${esc(when.toLocaleTimeString([], { timeStyle: "short" }))}</div>
      <div><b>Referral no.:</b> ${esc(L.ref)}</div>
      <div><b>To:</b> The Medical Officer / Midwife in charge, ${esc(L.to.facility)} (${esc(L.to.level)})</div>
      <div><b>From:</b> ${esc(L.from.worker)}, ${esc(L.from.role)}, ${esc(L.from.facility)}</div>
    </div>
    <p>Dear Colleague,</p>
    <p>Re: <b>${esc(L.patient.name)}</b>, ${esc(L.patient.age)}, card ${esc(L.patient.card)}${L.patient.community ? `, ${esc(L.patient.community)}` : ""}.</p>
    <p>I am referring this woman, ${esc(L.patient.ga.toLowerCase())} pregnant, for the reasons below. ${esc(L.request)}</p>
    <h2>Reason for referral</h2>${li(L.reasons)}
    <h2>Clinical findings</h2>
    <table>${row("Presenting complaints", L.complaints.join("; "))}${row("Examination / measurements", L.findings.join("; "))}
      ${row("Gestational age", L.patient.ga + (L.patient.edd ? `, EDD ${L.patient.edd}` : ""))}${row("Obstetric history", L.patient.obstetric)}
      ${row("Relevant history", L.history.join("; "))}</table>
    <h2>Treatment and actions before referral</h2>${li(L.treatment)}
    <table>${row("Woman's consent to referral", L.consent)}${row("Ambulance called", L.call.called)}${row("Ambulance arrived", L.call.arrived)}
      ${row("Referring worker's note", L.worker_reason)}</table>
    <h2>Guideline basis</h2><div class="small">${L.basis.map(esc).join("<br>")}</div>
    <p style="margin-top:12px">Thank you for receiving her. Please send your feedback using the slip below.</p>
    <div class="sign">
      <div><div class="line"></div><div class="small">Signature</div></div>
      <div><div class="line"></div><div class="small">${esc(L.from.worker)} · ${esc(L.from.role)}</div></div>
    </div>
    <div class="slip">
      <b>FEEDBACK FROM THE RECEIVING FACILITY</b> <span class="small">(return to ${esc(L.from.facility)}, referral no. ${esc(L.ref)})</span>
      <table style="margin-top:6px">
        <tr><td>Date and time received</td><td><div class="line"></div></td></tr>
        <tr><td>Diagnosis</td><td><div class="line"></div></td></tr>
        <tr><td>Treatment given</td><td><div class="line"></div></td></tr>
        <tr><td>Outcome / plan</td><td><div class="line"></div></td></tr>
        <tr><td>Follow-up at referring facility</td><td><div class="line"></div></td></tr>
        <tr><td>Name, role and signature</td><td><div class="line"></div></td></tr>
      </table>
    </div>
    <div class="small" style="margin-top:10px">Prepared with Ovamha (prototype). Use alongside the national standardized referral form.</div>
  </div>`;
}
async function leftLogoUrl() {
  try { const r = await fetch("/branding/logo-left.png", { method: "HEAD" }); return r.ok ? "/branding/logo-left.png" : null; } catch { return null; }
}
async function printLetter() {
  $("#printArea").innerHTML = letterHtml(S.result.letter, await leftLogoUrl());
  const imgs = [...document.querySelectorAll("#printArea img")];
  await Promise.all(imgs.map((i) => (i.complete ? null : new Promise((r) => { i.onload = i.onerror = r; }))));
  window.print();
}

// ---------------------------------------------------------------- 8. result (after the worker's decision)
function syncLine(st, valid) {
  if (valid && !valid.ok) return `<div class="banner red" style="margin:0">${icon("alert")}Record failed validation and was not queued. Tell your supervisor.</div>`;
  if (!st) return "";
  if (st.synced) return `<div style="display:flex;gap:12px;align-items:center"><span class="icon-btn soft" style="flex:none;color:var(--green);background:var(--green-50)">${icon("cloud")}</span>
    <div><b>Synced to the facility hub</b><div class="small muted">Saved on this device and on the hub. Nothing for you to do.</div></div></div>`;
  return `<div style="display:flex;gap:12px;align-items:center"><span class="icon-btn soft" style="flex:none">${icon("device")}</span>
    <div style="flex:1"><b>Saved on this device</b><div class="small muted">It will upload by itself when the hub is reachable. Nothing for you to do.</div></div></div>
    <button class="link small" id="syncNow">Try now</button>`;
}
let syncTimer = null;
function result() {
  const r = S.result, choice = r.decision?.choice;
  const pillCls = { requested: "wait", accepted: "ok", rejected: "no" }[r.status] || "wait";
  const pillTxt = { requested: "Waiting for the hospital to reply", accepted: "Hospital accepted the referral", rejected: "Hospital is full: refer elsewhere" }[r.status];
  const head = r.urgent ? `<div class="alert">${icon("send")}<h2>Urgent referral sent</h2><div>Your decision, recorded with the guideline advice.</div></div>`
    : choice === "urgent" ? `<div class="alert" style="background:linear-gradient(135deg,#B45F06,#E08A2B)">${icon("alert")}<h2>Referral refused</h2><div>She did not consent. Her refusal is recorded. Keep caring for her.</div></div>`
    : choice === "planned" ? `<div class="alert" style="background:linear-gradient(135deg,#B45F06,#E08A2B)">${icon("calendar")}<h2>Planned referral</h2><div>Recorded. Counsel her and prepare her for assessment or delivery at CEmONC.</div></div>`
    : `<div class="alert ok">${icon("check")}<h2>No referral now</h2><div>${r.decision?.reason ? "Your reason is recorded." : "Continue routine care."}</div></div>`;
  return `<div class="screen">${topbar("Result", null)}${steps(5)}
    ${head}
    ${r.letter ? `<div class="list-head">Referral<span>Digital and paper</span></div>
      <div class="row-list">
        <div class="row-item on"><div class="row-main"><span class="row-ico">${icon("send")}</span>
          <div class="row-text"><div class="row-title">Referred digitally</div><div class="row-sub">${esc(r.letter.to.facility)} · ${r.sms ? "SMS notice sent" : "record shared"} · record syncs to the hub</div></div></div></div>
        <button class="row-item" id="printLetter"><div class="row-main"><span class="row-ico">${icon("file")}</span>
          <div class="row-text"><div class="row-title">Print referral letter</div><div class="row-sub">Letter with both logos and a feedback slip</div></div>
          <span class="row-say">${icon("right")}</span></div></button>
        <button class="row-item" id="viewLetter"><div class="row-main"><span class="row-ico">${icon("file")}</span>
          <div class="row-text"><div class="row-title">Preview the letter</div><div class="row-sub">See it before printing</div></div>
          <span class="row-say">${icon("right")}</span></div></button>
      </div>
      <div id="letterPreview"></div>` : ""}
    ${r.next_contact?.text ? `<div class="note-line">${icon("calendar")}Next contact: ${esc(r.next_contact.text)}</div>` : ""}
    ${r.sms ? `<div class="section-title">Referral SMS <span class="badge ${r.sms.channel === "SIMULATED" ? "amber" : "green"}">${r.sms.channel === "SIMULATED" ? "Simulated" : "Sent by GSM"}</span></div>
      <div class="card"><div class="small muted">To the referral hospital · ${esc(new Date(r.sms.at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }))}</div><div class="sms">${esc(r.sms.text)}</div>
        <div style="margin-top:14px"><span class="status-pill ${pillCls}">${icon(pillCls === "ok" ? "check" : pillCls === "no" ? "x" : "sms")}${pillTxt}</span></div>
        ${r.status === "requested" ? `<div class="small muted" style="margin:14px 0 8px">Demo: simulate the hospital's reply</div>
        <div class="row"><button class="btn soft" data-reply="ACK ${esc(r.code)}">ACK ${esc(r.code)}</button><button class="btn soft" data-reply="FULL ${esc(r.code)}">FULL ${esc(r.code)}</button></div>` : ""}
      </div>` : ""}
    <div class="section-title">${r.referral ? "Referral form (iSBAR)" : "Contact record"}</div>
    <details class="card" open><summary>For the receiving team <button class="icon-btn soft" id="sayHandover" aria-label="Read aloud">${icon("speaker")}</button></summary><pre class="mono">${esc(r.handover)}</pre></details>
    <div class="section-title">Record</div>
    <div class="card" id="syncCard">${syncLine(r.sync, r.valid)}</div>
    <details class="card"><summary>Technical record (FHIR, for supervisors) ${r.valid.ok ? `<span class="badge green">${icon("check")}Valid</span>` : `<span class="badge red">Error</span>`}</summary>
      <p class="small muted">${esc(r.valid.message)}</p>
      <pre class="mono">${esc(JSON.stringify(r.bundle, null, 2))}</pre></details>
    <div style="margin-top:18px"><button class="btn primary" id="newCheck">${icon("plus")}New check</button></div>
  </div>${nav("")}`;
}
bind.result = () => {
  document.querySelectorAll("[data-reply]").forEach((b) => b.onclick = async () => {
    try {
      const out = await api("/api/sms/reply", { body: { text: b.dataset.reply } });
      S.result.status = out.status;
      if (out.sync) S.result.sync = out.sync;
      render();
    } catch (e) { toast(e.message); }
  });
  $("#sayHandover").onclick = (e) => { e.preventDefault(); speakText(["I", "S", "B", "A", "R"].map((k) => S.result.isbar[k]).join(" "), "en"); };
  const refreshSync = (st) => { S.result.sync = st; const c = $("#syncCard"); if (c) { c.innerHTML = syncLine(st, S.result.valid); bindSyncNow(); } };
  const bindSyncNow = () => { const b = $("#syncNow"); if (b) b.onclick = () => api("/api/sync/now").then(refreshSync).catch((e) => toast(e.message)); };
  bindSyncNow();
  clearInterval(syncTimer);
  syncTimer = setInterval(() => {
    if (S.screen !== "result" || S.result?.sync?.synced) { clearInterval(syncTimer); return; }
    api("/api/sync", { method: "GET" }).then(refreshSync).catch(() => {});
  }, 5000);
  $("#newCheck").onclick = startCheck;
  $("#printLetter") && ($("#printLetter").onclick = printLetter);
  $("#viewLetter") && ($("#viewLetter").onclick = async () => {
    const box = $("#letterPreview");
    box.innerHTML = box.innerHTML ? "" : `<div class="letter-preview">${letterHtml(S.result.letter, await leftLogoUrl())}</div>`;
  });
};

// ---------------------------------------------------------------- profile
function profile() {
  const w = S.worker;
  return `<div class="screen">${topbar("Profile", "home")}
    <div class="card" style="text-align:center"><span class="avatar" style="width:72px;height:72px;margin:0 auto 10px;font-size:1.4rem">${esc(initials(w.display_name))}</span>
      <h3 style="font-size:1.3rem">${esc(w.display_name)}</h3><div class="muted">${esc(w.role)}</div><div class="small muted">${esc(w.facility)}</div></div>
    <div class="card"><b>About this prototype</b><div class="small muted" style="margin-top:6px">Speech recognition, read-aloud and danger-sign checks run on this device. Danger-sign rules are demo rules from the WHO antenatal care guidance, pending full extraction. SMS is simulated unless a GSM modem is attached.</div></div>
    <div style="margin-top:16px"><button class="btn outline" id="signout">${icon("logout")}Sign out</button></div>
  </div>${nav("profile")}`;
}
bind.profile = () => { $("#signout").onclick = () => signOut(false); };

// ---------------------------------------------------------------- boot
(async function boot() {
  try { S.hosted = (await (await fetch("/api/config")).json()).hosted; } catch { S.hosted = false; }
  const saved = store.get("ovamha");
  if (saved?.token) {
    S.token = saved.token; S.worker = saved.worker; S.lang = saved.lang || "en";
    try { await api("/api/state", { method: "GET" }); S.screen = "home"; } catch { S.token = null; S.screen = "login"; }
  }
  render();
})();
