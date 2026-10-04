/* Onboarding illustrations: hand-drawn inline SVG (no external assets, works offline).
   A community health worker in a blue headwrap, beside a phone, on a soft cloud. */
"use strict";

const ART_C = {
  blue: "#0072C6", blue2: "#2E95E0", sky: "#7CC0EE", pale: "#D3E8F8", paler: "#EAF4FC",
  skin: "#7A4A2B", skinDark: "#5C3520", hair: "#1E1714", white: "#FFFFFF", line: "#BFDDF4",
  green: "#12805C", greenPale: "#E7F6F0", amber: "#F2A33A", ink: "#0E2235",
};

function artDefs(id) {
  const c = ART_C;
  return `<defs>
    <pattern id="${id}-dots" width="12" height="12" patternUnits="userSpaceOnUse">
      <rect width="12" height="12" fill="#E3F2FC"/><circle cx="3" cy="3" r="1.8" fill="${c.sky}"/><circle cx="9" cy="9" r="1.8" fill="${c.sky}"/></pattern>
    <linearGradient id="${id}-blob" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E4F2FC"/><stop offset="1" stop-color="#CFE6F8"/></linearGradient>
    <linearGradient id="${id}-screen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F7FBFE"/><stop offset="1" stop-color="#EAF4FC"/></linearGradient>
    <filter id="${id}-shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#0E3C6E" flood-opacity=".14"/></filter>
  </defs>`;
}

function plusSign(x, y, s, color, o = 1) {
  return `<path d="M${x} ${y - s}v${2 * s}M${x - s} ${y}h${2 * s}" stroke="${color}" stroke-width="${s * 0.7}" stroke-linecap="round" opacity="${o}"/>`;
}

function cloud(id) {
  return `<path d="M58 250c-34-6-46-52-18-74-10-38 30-66 62-48 14-40 76-48 100-14 34-16 76 6 74 48 34 10 38 60 6 76-6 26-40 34-62 22-26 22-74 20-96-2-26 10-58 6-66-8z" fill="url(#${id}-blob)"/>`;
}

function phone(x, y, w, h, id, inner) {
  return `<g filter="url(#${id}-shadow)"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="22" fill="${ART_C.white}" stroke="${ART_C.line}" stroke-width="3"/></g>
    <rect x="${x + 8}" y="${y + 18}" width="${w - 16}" height="${h - 30}" rx="14" fill="url(#${id}-screen)"/>
    <rect x="${x + w / 2 - 16}" y="${y + 7}" width="32" height="5" rx="2.5" fill="${ART_C.pale}"/>
    <g transform="translate(${x + 8} ${y + 18})">${inner}</g>`;
}

/* The health worker. (x, y) = top of her headwrap; pose: "point" | "hold" | "wave" */
function worker(x, y, id, pose = "point") {
  const c = ART_C;
  const arm = {
    point: `<path d="M${x - 18} ${y + 92}c-14 6-26 0-36-14" stroke="${c.skin}" stroke-width="13" fill="none" stroke-linecap="round"/>
            <circle cx="${x - 56}" cy="${y + 76}" r="8" fill="${c.skin}"/><path d="M${x - 58} ${y + 70}l-8-10" stroke="${c.skin}" stroke-width="5" stroke-linecap="round"/>`,
    hold: `<path d="M${x - 20} ${y + 96}c-16 2-26-6-30-20" stroke="${c.skin}" stroke-width="13" fill="none" stroke-linecap="round"/>
           <rect x="${x - 66}" y="${y + 52}" width="26" height="42" rx="6" fill="${c.ink}"/><rect x="${x - 63}" y="${y + 57}" width="20" height="30" rx="3" fill="${c.sky}"/>
           <circle cx="${x - 48}" cy="${y + 80}" r="7.5" fill="${c.skin}"/>`,
    wave: `<path d="M${x + 24} ${y + 92}c12-8 18-26 14-44" stroke="${c.skin}" stroke-width="13" fill="none" stroke-linecap="round"/>
           <circle cx="${x + 37}" cy="${y + 42}" r="8" fill="${c.skin}"/>`,
  }[pose];
  return `<g>
    <!-- body / uniform -->
    <path d="M${x - 42} ${y + 200}c0-56 14-104 42-116 28 12 42 60 42 116z" fill="url(#${id}-dots)"/>
    <path d="M${x - 42} ${y + 200}c0-56 14-104 42-116 28 12 42 60 42 116" fill="none" stroke="${c.line}" stroke-width="2"/>
    <path d="M${x - 12} ${y + 86}l12 18 12-18" fill="${c.white}" stroke="${c.line}" stroke-width="2" stroke-linejoin="round"/>
    <!-- neck and head -->
    <rect x="${x - 7}" y="${y + 60}" width="14" height="22" rx="6" fill="${c.skinDark}"/>
    <ellipse cx="${x}" cy="${y + 46}" rx="21" ry="24" fill="${c.skin}"/>
    <!-- headwrap -->
    <path d="M${x - 24} ${y + 42}c-4-28 12-44 26-44s32 12 26 42c-8-12-20-18-26-18s-18 6-26 20z" fill="${c.blue}"/>
    <path d="M${x + 14} ${y + 4}c14-10 30-4 30 8-8-4-18-2-24 4z" fill="${c.blue2}"/>
    <path d="M${x - 18} ${y + 22}c10-8 26-8 36 0" stroke="${c.blue2}" stroke-width="4" fill="none" stroke-linecap="round"/>
    <!-- face (simple) -->
    <path d="M${x - 9} ${y + 46}q3-3 6 0M${x + 4} ${y + 46}q3-3 6 0" stroke="${c.hair}" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <path d="M${x - 5} ${y + 56}q5 5 10 0" stroke="${c.hair}" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <circle cx="${x + 21}" cy="${y + 50}" r="3" fill="${c.amber}"/>
    ${arm}
  </g>`;
}

function slideArt(i, id = "a" + i) {
  const c = ART_C;
  const deco = plusSign(26, 70, 9, c.sky, .9) + plusSign(292, 236, 12, c.sky, .8) + plusSign(282, 52, 6, c.blue, .5) + plusSign(44, 262, 6, c.blue, .4);
  let scene = "";
  if (i === 0) {
    // Phone with a pregnancy card and a green check; worker points at it. Offline badge.
    const inner = `
      <rect x="10" y="12" width="90" height="56" rx="12" fill="${c.blue}"/>
      <circle cx="40" cy="36" r="9" fill="${c.white}"/><path d="M30 60c0-12 5-16 10-16 6 0 12 4 12 14" fill="${c.white}"/><circle cx="50" cy="52" r="7" fill="${c.white}"/>
      ${plusSign(78, 30, 7, c.white)}
      <rect x="10" y="80" width="90" height="9" rx="4.5" fill="${c.pale}"/><rect x="10" y="96" width="62" height="9" rx="4.5" fill="${c.pale}"/>
      <rect x="10" y="118" width="90" height="38" rx="12" fill="${c.greenPale}"/>
      <path d="M24 137l8 8 16-16" stroke="${c.green}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="56" y="132" width="34" height="8" rx="4" fill="#BFE6D6"/>`;
    scene = cloud(id) + phone(70, 40, 126, 200, id, inner) + worker(232, 70, id, "point") + `
      <g transform="translate(150 22)"><rect width="74" height="28" rx="14" fill="${c.white}" stroke="${c.line}" stroke-width="2"/>
        <circle cx="16" cy="14" r="5" fill="${c.green}"/><text x="27" y="19" font-family="system-ui,-apple-system,sans-serif" font-size="12" font-weight="700" fill="${c.green}">Offline</text></g>`;
  } else if (i === 1) {
    // Worker speaks; speech bubbles in three languages; sound wave on the phone.
    const bars = [10, 22, 36, 22, 30, 14, 26, 10].map((h, k) => `<rect x="${18 + k * 10}" y="${60 - h / 2}" width="6" height="${h}" rx="3" fill="${k % 2 ? c.sky : c.blue}"/>`).join("");
    const inner = `<circle cx="55" cy="112" r="26" fill="${c.blue}"/><rect x="49" y="98" width="12" height="22" rx="6" fill="${c.white}"/>
      <path d="M43 114a12 12 0 0 0 24 0M55 126v6" stroke="${c.white}" stroke-width="3.5" fill="none" stroke-linecap="round"/>${bars}`;
    const bubble = (bx, by, label, fill, tx, up = false) => `<g transform="translate(${bx} ${by})">
      <path d="${up ? "M14 2l-4-10 12 8z" : "M14 30l-4 10 12-8z"}" fill="${fill}" stroke="${fill === c.blue ? "none" : c.line}" stroke-width="2"/>
      <rect width="${label.length * 9 + 26}" height="32" rx="16" fill="${fill}" stroke="${fill === c.blue ? "none" : c.line}" stroke-width="2"/><text x="13" y="21" font-family="system-ui,-apple-system,sans-serif" font-size="14" font-weight="700" fill="${tx}">${label}</text></g>`;
    scene = cloud(id) + phone(60, 66, 126, 180, id, inner) + worker(236, 76, id, "hold")
      + bubble(196, 22, "Krio", c.blue, c.white) + bubble(22, 30, "Yorùbá", c.paler, c.blue) + bubble(14, 252, "English", c.paler, c.blue, true);
  } else {
    // Confirmed checklist, then the referral SMS flies to the hospital.
    const row = (y, w) => `<rect x="10" y="${y}" width="90" height="34" rx="10" fill="${c.white}" stroke="${c.line}" stroke-width="1.5"/>
      <circle cx="26" cy="${y + 17}" r="9" fill="${c.greenPale}"/><path d="M21 ${y + 17}l4 4 7-7" stroke="${c.green}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="42" y="${y + 13}" width="${w}" height="8" rx="4" fill="${c.pale}"/>`;
    const inner = row(12, 48) + row(54, 38) + row(96, 44) + `<rect x="10" y="140" width="90" height="26" rx="13" fill="${c.blue}"/>
      <text x="55" y="157" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-size="11" font-weight="700" fill="${c.white}">Refer</text>`;
    const hospital = `<g transform="translate(214 8) scale(.76)"><rect x="0" y="22" width="70" height="66" rx="6" fill="${c.white}" stroke="${c.line}" stroke-width="2.5"/>
      <rect x="20" y="0" width="30" height="30" rx="6" fill="${c.white}" stroke="${c.line}" stroke-width="2.5"/>${plusSign(35, 15, 7, "#C62828")}
      <rect x="10" y="38" width="12" height="12" rx="2" fill="${c.pale}"/><rect x="48" y="38" width="12" height="12" rx="2" fill="${c.pale}"/>
      <rect x="27" y="64" width="16" height="24" rx="3" fill="${c.sky}"/></g>`;
    const sms = `<g transform="translate(128 22) rotate(-10) scale(.85)"><rect width="62" height="34" rx="10" fill="${c.blue}"/><path d="M12 32l-2 10 10-8z" fill="${c.blue}"/>
      <rect x="10" y="10" width="40" height="5" rx="2.5" fill="${c.white}"/><rect x="10" y="20" width="26" height="5" rx="2.5" fill="${c.sky}"/></g>
      <path d="M184 38c10-4 18-8 26-10" stroke="${c.sky}" stroke-width="3" stroke-dasharray="4 7" fill="none" stroke-linecap="round"/>`;
    scene = cloud(id) + phone(36, 64, 126, 190, id, inner) + hospital + sms + worker(244, 110, id, "wave");
  }
  return `<svg viewBox="0 0 320 300" width="100%" style="max-width:340px" role="img" aria-hidden="true">${artDefs(id)}${deco}${scene}</svg>`;
}
