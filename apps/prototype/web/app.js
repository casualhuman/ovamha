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
function go(screen) { S.screen = screen; render(); window.scrollTo(0, 0); }
function render() {
  const app = $("#app");
  const view = { welcome, login, home, woman, describe, confirm, measure, result, profile }[S.screen] || home;
  app.innerHTML = view();
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
function steps(n) { return `<div class="steps">${[1, 2, 3, 4].map((i) => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}</div>`; }
function topbar(title, back) {
  const card = S.screen !== "woman" && S.st?.woman ? `<span class="badge" title="Her card number">${icon("file")}${esc(S.st.woman.card_code)}</span>` : "";
  return `<div class="top">${back ? `<button class="icon-btn" data-back="${back}" aria-label="Back">${icon("left")}</button>` : ""}<h1>${esc(title)}</h1>
    ${card || `<span class="badge green" title="Everything runs on this device">${icon("wifioff")}Offline</span>`}</div>`;
}
document.addEventListener("click", (e) => { const b = e.target.closest("[data-back]"); if (b) go(b.dataset.back); });

// ---------------------------------------------------------------- 1. welcome (onboarding)
const SLIDES = [
  { t: "Safer pregnancies,<br>even offline", p: "Ovamha helps nurses, midwives and community health workers spot danger signs early and refer fast, with no internet." },
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
      <div style="font-weight:800;color:var(--blue);font-size:1.5rem;margin-top:10px">Ovamha</div>
      <div style="font-size:1.15rem;font-weight:650;margin-top:2px">Offline voice guidance<br>for safer maternal care</div></div>
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
    S.cardMode = null; S.cardErr = ""; S.idDoc = null;
    go("woman");
  } catch (e) { toast(e.message); }
}

// ---------------------------------------------------------------- 3b. who is this check for (card number)
const ID_DOCS = [["sl-nin", "Sierra Leone NIN"], ["ng-nin", "Nigeria NIN"], ["other", "Other ID"]];
function idCheckCard(w) {
  if (w.id_check) {
    return `<div class="card" style="margin-top:14px;display:flex;gap:12px;align-items:flex-start"><span class="icon-btn soft" style="flex:none">${icon("idcard")}</span>
      <div><b>ID check recorded</b><div class="small muted">${esc(w.id_check.document)} shown, with her consent. The number is not stored. It can be verified later through the national ID service.</div></div></div>`;
  }
  const picked = S.idDoc;
  return `<div class="card" style="margin-top:14px">
    <div style="display:flex;gap:10px;align-items:center"><span class="icon-btn soft" style="width:40px;height:40px">${icon("idcard")}</span>
      <h3 style="margin:0;flex:1">National ID <span class="tiny">optional</span></h3></div>
    <p class="small muted" style="margin:8px 0 10px">Does she have a national ID card? Care continues the same without one.</p>
    <div class="seg">${ID_DOCS.map(([v, l]) => `<button data-doc="${v}" class="${picked === v ? "on" : ""}">${l}</button>`).join("")}<button data-doc="none" class="${picked === "none" ? "on" : ""}">No ID</button></div>
    ${picked && picked !== "none" ? `<label style="display:flex;gap:12px;align-items:flex-start;margin-top:14px;font-weight:600">
        <input type="checkbox" id="idConsent" style="width:26px;height:26px;flex:none;margin-top:2px">
        <span>She agrees to link her Ovamha record to her national ID.</span></label>
      <p class="tiny" style="margin:8px 0 10px">Do not type the ID number. Ovamha records only that the card was shown.</p>
      <button class="btn soft" id="saveId">${icon("check")}Record ID check</button>` : ""}
  </div>`;
}
function woman() {
  const w = S.st?.woman;
  let body;
  if (w && w.new) {
    body = `<div class="card" style="text-align:center">
      <div class="badge green" style="margin-bottom:10px">${icon("check")}New card number created</div>
      <div class="small muted">Write this on her antenatal card</div>
      <div style="font-size:2.6rem;font-weight:800;letter-spacing:.12em;color:var(--blue-700);margin:10px 0 6px;font-family:ui-monospace,Menlo,monospace">${esc(w.card_code)}</div>
      <button class="btn soft" id="sayCard">${icon("speaker")}Read aloud</button>
      <p class="tiny" style="margin:12px 0 0">No name or phone number is stored. Ovamha keeps its own ID for her on this device.</p>
    </div>
    ${idCheckCard(w)}
    <div style="margin-top:16px"><button class="btn primary" id="toDescribe">Continue${icon("right")}</button></div>`;
  } else if (w) {
    body = `<div class="card" style="text-align:center">
      <div class="badge green" style="margin-bottom:10px">${icon("check")}Card found</div>
      <div style="font-size:2.2rem;font-weight:800;letter-spacing:.12em;color:var(--blue-700);margin:6px 0;font-family:ui-monospace,Menlo,monospace">${esc(w.card_code)}</div>
      <div class="small muted">${w.visits} previous ${w.visits === 1 ? "check" : "checks"} on this device</div>
    </div>
    <div style="margin-top:16px"><button class="btn primary" id="toDescribe">Continue${icon("right")}</button></div>`;
  } else if (S.cardMode === "find") {
    body = `<div class="card"><h3>Her card number</h3><p class="small muted" style="margin:2px 0 12px">6 characters, as written on her antenatal card.</p>
      <input class="input" id="card" autocapitalize="characters" autocorrect="off" spellcheck="false" maxlength="7" placeholder="K7P-3QZ"
        style="font-size:1.6rem;text-align:center;letter-spacing:.15em;font-weight:700;font-family:ui-monospace,Menlo,monospace">
      <div class="err">${esc(S.cardErr)}</div>
      <div class="row" style="margin-top:6px"><button class="btn soft" id="cardBack">Back</button><button class="btn primary" id="findCard">Find</button></div></div>`;
  } else {
    body = `<button class="card" id="newWoman" style="width:100%;text-align:left;display:flex;gap:14px;align-items:center;border:0">
        <span class="icon-btn blue" style="flex:none">${icon("plus")}</span>
        <span style="flex:1"><b style="font-size:1.1rem">First visit</b><br><span class="small muted">Create a new card number for her</span></span>${icon("right")}</button>
      <button class="card" id="oldWoman" style="width:100%;text-align:left;display:flex;gap:14px;align-items:center;border:0">
        <span class="icon-btn soft" style="flex:none">${icon("file")}</span>
        <span style="flex:1"><b style="font-size:1.1rem">Returning</b><br><span class="small muted">Enter the number on her card</span></span>${icon("right")}</button>`;
  }
  return `<div class="screen">${topbar("Who is this check for?", "home")}${body}</div>${nav("describe")}`;
}
bind.woman = () => {
  const set = (st) => { S.st = st; S.cardErr = ""; render(); };
  $("#newWoman") && ($("#newWoman").onclick = () => api("/api/woman/new").then(set).catch((e) => toast(e.message)));
  $("#oldWoman") && ($("#oldWoman").onclick = () => { S.cardMode = "find"; render(); $("#card").focus(); });
  $("#cardBack") && ($("#cardBack").onclick = () => { S.cardMode = null; S.cardErr = ""; render(); });
  const find = () => api("/api/woman/find", { body: { card_code: $("#card").value } }).then(set).catch((e) => { S.cardErr = e.message; render(); });
  $("#findCard") && ($("#findCard").onclick = find);
  $("#card") && ($("#card").onkeydown = (e) => { if (e.key === "Enter") find(); });
  $("#sayCard") && ($("#sayCard").onclick = () => speakText(`Card number: ${S.st.woman.card_code.replace("-", "").split("").join(", ")}`, "en"));
  $("#toDescribe") && ($("#toDescribe").onclick = () => go("describe"));
  document.querySelectorAll("[data-doc]").forEach((b) => b.onclick = () => { S.idDoc = b.dataset.doc; render(); });
  $("#saveId") && ($("#saveId").onclick = () => {
    if (!$("#idConsent").checked) { toast("Ask for her consent first, or choose No ID"); return; }
    api("/api/woman/id-check", { body: { document: S.idDoc, consent: true } }).then(set).catch((e) => toast(e.message));
  });
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
      <p class="muted small" style="margin:4px 0 12px">Listen to what you said, or go on to the read-back.</p>
      <audio controls src="${S.audioUrl}" style="width:100%;margin-bottom:14px"></audio>
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
  $("#replay") && ($("#replay").onclick = () => speakPrompt("guide_describe"));
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
function itemCard(it) {
  const warn = it.source === "ai-safety-net";
  const ok = it.confirmed;
  const tag = warn ? `<span class="badge amber">${icon("alert")}AI warning: please check</span>`
    : `<span class="badge">${icon("mic")}Heard</span>`;
  let acts;
  if (ok) {
    acts = `<div class="done-line">${icon("check")}Confirmed <button class="link small" data-undo="${it.field}">Change</button></div>`;
  } else if (it.kind === "severity" && it.value === true) {
    acts = `<div class="small muted" style="margin-top:12px">How bad is it?</div><div class="acts">
      <button class="btn danger" data-set="${it.field}" data-v="severe">Severe</button>
      <button class="btn soft" data-set="${it.field}" data-v="mild">Mild</button>
      <button class="btn soft" data-no="${it.field}">${icon("x")}Not true</button></div>`;
  } else {
    acts = `<div class="acts"><button class="btn primary" data-ok="${it.field}">${icon("check")}Correct</button>
      <button class="btn soft" data-no="${it.field}">${icon("x")}Not true</button></div>`;
  }
  return `<div class="item ${ok ? "ok" : warn ? "warn" : ""}">
    <div class="head"><span class="ico">${icon(ok ? "check" : FIELD_ICON[it.field] || "file")}</span>
      <div class="t"><b>${esc(it.label)}</b><span class="val">${esc(ok ? it.confirmed_value : it.display)}</span></div>
      <button class="icon-btn soft" data-say="${it.field}" aria-label="Read aloud">${icon("speaker")}</button></div>
    <div style="margin-top:8px">${tag}</div>
    ${it.evidence ? `<div class="quote">“${esc(it.evidence)}”</div>` : ""}
    ${acts}</div>`;
}
function confirm() {
  const items = (S.st?.items || []).filter((i) => !["gestational_age_weeks", "systolic", "diastolic", "systolic_repeat", "diastolic_repeat", "pulse", "temperature", "fetal_heart_rate", "urine_protein", "severe_pe_symptoms"].includes(i.field));
  const pending = items.filter((i) => !i.confirmed).length;
  return `<div class="screen">${topbar("Check what was heard", "describe")}${steps(2)}
    <div class="card" style="display:flex;gap:12px;align-items:flex-start">
      <div style="flex:1"><div class="small muted">What was said</div><div style="margin-top:4px">${esc(S.st?.transcript || "")}</div></div>
      <button class="icon-btn soft" id="sayAll" aria-label="Read all aloud">${icon("speaker")}</button>
    </div>
    ${(S.st?.notes || []).map((n) => `<div class="banner blue" style="margin-top:12px">${icon("calendar")}${esc(n)}</div>`).join("")}
    <div class="section-title">${pending ? `${pending} to confirm` : "All checked"}<span class="tiny">Only confirmed items count</span></div>
    ${items.length ? items.map(itemCard).join("") : `<div class="card muted">No symptoms were picked up. You can go on to measurements, or go back and describe again.</div>`}
    <div style="height:12px"></div>
  </div>
  <div class="sticky">${statusBanner()}<button class="btn primary" id="toMeasure">Next: measurements${icon("right")}</button></div>`;
}
function statusBanner() {
  const p = S.st?.preview;
  if (!p) return `<div class="banner blue">${icon("shield")}Confirm items to run the danger-sign check</div>`;
  if (p.danger) return `<div class="banner red">${icon("alert")}Danger sign confirmed: refer now</div>`;
  if (p.referral) return `<div class="banner red">${icon("alert")}Referral needed</div>`;
  if (p.ask_next.length) return `<div class="banner amber">${icon("alert")}Still needed: ${esc(p.ask_next.slice(0, 3).map((a) => a.label).join(", "))}${p.ask_next.length > 3 ? "…" : ""}</div>`;
  return `<div class="banner green">${icon("check")}No danger sign on confirmed items</div>`;
}
bind.confirm = () => {
  const act = (path, body) => api(path, { body }).then((st) => { S.st = st; render(); }).catch((e) => toast(e.message));
  document.querySelectorAll("[data-ok]").forEach((b) => b.onclick = () => act("/api/confirm", { field: b.dataset.ok }));
  document.querySelectorAll("[data-set]").forEach((b) => b.onclick = () => act("/api/confirm", { field: b.dataset.set, value: b.dataset.v }));
  document.querySelectorAll("[data-no]").forEach((b) => b.onclick = () => act("/api/reject", { field: b.dataset.no }));
  document.querySelectorAll("[data-undo]").forEach((b) => b.onclick = () => act("/api/unconfirm", { field: b.dataset.undo }));
  document.querySelectorAll("[data-say]").forEach((b) => b.onclick = () => speakItem(b.dataset.say));
  $("#sayAll").onclick = () => speakText(S.st?.transcript || "", S.lang === "en" ? "en" : S.lang);
  $("#toMeasure").onclick = () => go("measure");
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
  return `<div class="screen">${topbar("Measurements", "confirm")}${steps(3)}
    ${danger ? `<div class="banner red">${icon("alert")}Danger sign confirmed. Refer now: measurements are optional.</div>` : `<p class="muted small" style="margin-top:0">Type the numbers, or tap the microphone and say them. Each one is read back for you to confirm.</p>`}
    ${MEASURES.map(measureCard).join("")}
    ${choiceCard("urine_protein", "Urine protein", [["negative", "Negative"], ["trace", "Trace"], ["+", "+"], ["++", "++"], ["+++", "+++"], ["unknown", "Not done"]], "flask", "ask_protein")}
    ${choiceCard("severe_pe_symptoms", "Severe pre-eclampsia symptoms", [["yes", "Yes"], ["no", "No"], ["unknown", "Don't know"]], "alert", "ask_severe_pe")}
  </div>
  <div class="sticky">${statusBanner()}<button class="btn primary" id="finish">${icon("send")}Finish and see result</button></div>`;
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
  const done = busy("Checking danger signs…");
  try {
    S.result = await api("/api/finish");
    S.counts.checks++;
    if (S.result.referral) S.counts.referrals++;
    done(); go("result");
  } catch (e) { done(); toast(e.message); }
}

// ---------------------------------------------------------------- 7. result
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
  const r = S.result;
  const fired = r.rules.filter((x) => x.status === "fired");
  const pillCls = { requested: "wait", accepted: "ok", rejected: "no" }[r.status] || "wait";
  const pillTxt = { requested: "Waiting for the hospital to reply", accepted: "Hospital accepted the referral", rejected: "Hospital is full: refer elsewhere" }[r.status];
  const notes = r.rules.flatMap((x) => x.notes);
  return `<div class="screen">${topbar("Result", null)}${steps(4)}
    ${r.referral ? `<div class="alert">${icon("alert")}<h2>Urgent referral</h2>
        <div>${esc(fired.map((f) => f.reasons.join(", ")).join("; "))}</div>
        <ul>${[...new Set(fired.flatMap((f) => f.actions))].map((a) => `<li>${esc(a)}</li>`).join("")}</ul></div>`
      : `<div class="alert ok">${icon("check")}<h2>No danger sign found</h2><div>On the confirmed information. Continue routine care and follow national guidelines.</div></div>`}
    ${notes.map((n) => `<div class="banner amber" style="margin-top:12px">${icon("alert")}${esc(n)}</div>`).join("")}
    ${r.ask_next.length && !r.danger ? `<div class="banner amber" style="margin-top:12px">${icon("alert")}Not checked (missing): ${esc(r.ask_next.map((a) => a.label).join(", "))}</div>` : ""}
    ${r.sms ? `<div class="section-title">Referral SMS <span class="badge ${r.sms.channel === "SIMULATED" ? "amber" : "green"}">${r.sms.channel === "SIMULATED" ? "Simulated" : "Sent by GSM"}</span></div>
      <div class="card"><div class="small muted">To the referral hospital · ${esc(new Date(r.sms.at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }))}</div><div class="sms">${esc(r.sms.text)}</div>
        <div style="margin-top:14px"><span class="status-pill ${pillCls}">${icon(pillCls === "ok" ? "check" : pillCls === "no" ? "x" : "sms")}${pillTxt}</span></div>
        ${r.status === "requested" ? `<div class="small muted" style="margin:14px 0 8px">Demo: simulate the hospital's reply</div>
        <div class="row"><button class="btn soft" data-reply="ACK ${esc(r.code)}">ACK ${esc(r.code)}</button><button class="btn soft" data-reply="FULL ${esc(r.code)}">FULL ${esc(r.code)}</button></div>` : ""}
      </div>` : ""}
    <div class="section-title">Handover</div>
    <details class="card" open><summary>For the receiving nurse <button class="icon-btn soft" id="sayHandover" aria-label="Read aloud">${icon("speaker")}</button></summary><pre class="mono">${esc(r.handover)}</pre></details>
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
      render();
      if (out.sync) S.result.sync = out.sync;
    } catch (e) { toast(e.message); }
  });
  $("#sayHandover").onclick = (e) => { e.preventDefault(); speakText(S.result.handover.replace(/\[.*?\]/g, ""), "en"); };
  const refreshSync = (st) => { S.result.sync = st; const c = $("#syncCard"); if (c) { c.innerHTML = syncLine(st, S.result.valid); bindSyncNow(); } };
  const bindSyncNow = () => { const b = $("#syncNow"); if (b) b.onclick = () => api("/api/sync/now").then(refreshSync).catch((e) => toast(e.message)); };
  bindSyncNow();
  clearInterval(syncTimer);
  syncTimer = setInterval(() => {
    if (S.screen !== "result" || S.result?.sync?.synced) { clearInterval(syncTimer); return; }
    api("/api/sync", { method: "GET" }).then(refreshSync).catch(() => {});
  }, 5000);
  $("#newCheck").onclick = startCheck;
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
  const saved = store.get("ovamha");
  if (saved?.token) {
    S.token = saved.token; S.worker = saved.worker; S.lang = saved.lang || "en";
    try { await api("/api/state", { method: "GET" }); S.screen = "home"; } catch { S.token = null; S.screen = "login"; }
  }
  render();
})();
