/* Minerva front end: vanilla JS, no dependencies. */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = async (p, b) => {
  const r = await fetch(p, b === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || "Request failed");
  return j;
};
const I = {
  overview: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>',
  sites: '<svg viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg>',
  pipeline: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="5" height="16" rx="1.5"/><rect x="10" y="4" width="5" height="10" rx="1.5"/><rect x="17" y="4" width="4" height="13" rx="1.5"/></svg>',
  sourcing: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
  settings: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>',
  investor: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"/></svg>',
  inbox: '<svg viewBox="0 0 24 24"><path d="M3 13l3-8h12l3 8v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M3 13h5l1 3h6l1-3h5"/></svg>',
  sun: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  moon: '<svg viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
  x: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  link: '<svg viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
};
const NAV = [["overview", "Overview"], ["sites", "Sites"], ["pipeline", "Pipeline"], ["sourcing", "Sourcing"], ["inbox", "Inbox"], ["investor", "My mandate"], ["settings", "Settings"]];
const TITLES = {
  overview: ["Overview", "Where your opportunities are, and which ones stack up"], sites: ["Sites", "Every site and listing, scored and appraised"],
  pipeline: ["Pipeline", "Drag deals through your process"], sourcing: ["Sourcing", "Agents, aggregators and open data feeding the pipeline"], settings: ["Settings", "Assumptions, scoring and integrations"],
  inbox: ["Inbox", "Deals arriving by email, straight from Outlook"], investor: ["My mandate", "Your capital, cost of capital and appetite: used to filter and score everything"],
};
let D = null, view = "overview", sortKey = "score", sortDir = -1, drawer = null, pollT = null, mapInst = null;
const F = { q: "", stage: "active", src: "all", viable: false, strat: "all", fit: false };

/* Links, downloads and mail: the desktop app hands them to the operating system, the hosted app to the browser. */
function openUrl(url) {
  if (!D?.hosted) return api("/api/open", { url });
  if (url.startsWith("mailto:")) location.href = url; else window.open(url, "_blank", "noopener");
}
function download(url) { const a = document.createElement("a"); a.href = url; a.download = ""; document.body.append(a); a.click(); a.remove(); }

/* ---------- formatting ---------- */
const money = x => x == null || isNaN(x) ? "n/a" : Math.abs(x) >= 1e6 ? `£${(x / 1e6).toFixed(2)}m` : Math.abs(x) >= 1e3 ? `£${Math.round(x / 1e3).toLocaleString("en-GB")}k` : `£${Math.round(x)}`;
const pct = (x, d = 1) => x == null || isNaN(x) ? "n/a" : `${(x * 100).toFixed(d)}%`;
const grade = g => { const c = /^[ABCD]$/.test(g) ? g : "N"; return `<div class="grade g${c}">${c === "N" ? "?" : c}</div>`; };
const sevClass = s => ({ High: "hi", Medium: "med", Low: "lo" }[s] || "lo");
const gcol = g => getComputedStyle(document.documentElement).getPropertyValue(`--g${/^[ABCD]$/.test(g) ? g : "N"}`).trim() || "#888";
const when = iso => { if (!iso) return ""; const m = Math.round((Date.now() - new Date(iso)) / 60000); return m < 1 ? "just now" : m < 60 ? `${m}m ago` : m < 1440 ? `${Math.round(m / 60)}h ago` : `${Math.round(m / 1440)}d ago`; };
function toast(msg) { const t = document.createElement("div"); t.className = "toast"; t.textContent = msg; $("#toasts").append(t); setTimeout(() => t.remove(), 3600); }

/* ---------- theme ---------- */
function applyTheme() {
  const t = D?.theme || "auto";
  const dark = t === "dark" || (t === "auto" && matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  $("#themeBtn").innerHTML = dark ? I.sun : I.moon;
  if (mapInst) mapInst.setTheme(dark);
}
$("#themeBtn").onclick = async () => {
  const dark = document.documentElement.dataset.theme === "dark";
  D.theme = dark ? "light" : "dark"; applyTheme(); api("/api/settings", { theme: D.theme });
};

/* ---------- data helpers ---------- */
const sites = () => D.sites;
const ev = s => s._ev;
function filtered() {
  const q = F.q.trim().toLowerCase();
  return sites().filter(s => {
    if (F.stage === "active" && s.stage === "Rejected") return false;
    if (!["active", "all"].includes(F.stage) && s.stage !== F.stage) return false;
    if (F.src !== "all" && (s.source || "Other") !== F.src) return false;
    if (F.strat !== "all" && ev(s).strategy !== F.strat) return false;
    if (F.viable && !(ev(s).appraisal?.viable)) return false;
    if (F.fit && (ev(s).fit?.hard_fail || !ev(s).fit?.active)) return false;
    if (q && !`${s.name} ${s.address} ${s.source} ${s.postcode || ""} ${s.property_type || ""}`.toLowerCase().includes(q)) return false;
    return true;
  });
}
async function load(keepDrawer = true) {
  D = await api("/api/state");
  applyTheme(); render();
  if (keepDrawer && drawer) refreshDrawer();
}

/* ---------- shell ---------- */
function renderNav() {
  const live = sites().filter(s => s.listing).length;
  $("#nav").innerHTML = NAV.map(([k, l]) => `<button class="nav-i ${view === k ? "on" : ""}" data-act="nav" data-v="${k}">${I[k]}<span>${l}</span>${k === "sites" ? `<em class="n">${sites().length}</em>` : k === "sourcing" && live ? `<em class="n">${live}</em>` : ""}</button>`).join("");
}
function render() {
  renderNav();
  $(".ver").innerHTML = D.hosted ? 'v0.3 · <a href="/logout">Sign out</a>' : "v0.3 MVP";
  $("#title").textContent = TITLES[view][0]; $("#subtitle").textContent = TITLES[view][1];
  if (mapInst) { mapInst.destroy(); mapInst = null; }
  ({ overview: vOverview, sites: vSites, pipeline: vPipeline, sourcing: vSourcing, settings: vSettings, inbox: vInbox, investor: vInvestor })[view]();
  const running = D.job?.running;
  const b = $("#refreshBtn"); b.disabled = !!running;
  b.querySelector("span").textContent = running ? "Refreshing" : "Refresh listings";
  b.querySelector("svg").classList.toggle("spin", !!running);
  if (running) poll();
}

/* ---------- overview ---------- */
function vOverview() {
  const all = filtered();
  const live = all.filter(s => s.listing).length;
  const viable = all.filter(s => ev(s).appraisal?.viable).length;
  const top = [...all].sort((a, b) => ev(b).score.score - ev(a).score.score);
  const high = all.reduce((n, s) => n + ev(s).flags.filter(f => f.severity === "High").length, 0);
  const srcOk = Object.values(D.job?.sources || {}).filter(x => x.status === "ok" || x.fallback).length;
  const funnel = D.stages.map(st => [st, sites().filter(s => s.stage === st).length]);
  const fmax = Math.max(1, ...funnel.map(f => f[1]));
  $("#view").innerHTML = `
  <div class="grid kpis">
    ${kpi("Sites tracked", all.length, `${live} from listings`)}
    ${kpi("Viable at asking", viable, "meet your return target")}
    ${kpi("Top score", top[0] ? ev(top[0]).score.score : "n/a", top[0] ? esc(top[0].name.slice(0, 28)) : "")}
    ${kpi("High risk flags", high, "across visible sites")}
    ${D.investor?.active ? kpi("Inside your mandate", all.filter(s => ev(s).fit?.active && !ev(s).fit.hard_fail).length, `of ${all.length} visible`) : kpi("Sources responding", D.job?.started ? `${srcOk}/${D.sources.length}` : "n/a", D.job?.started ? "last refresh" : "not refreshed yet")}
  </div>
  <div class="grid dash">
    <div class="map" id="map"></div>
    <div class="grid" style="align-content:start">
      <div class="card"><div class="h"><h3>Top opportunities</h3><span class="m">by score</span></div><div class="list">
        ${top.slice(0, 7).map(s => `<div class="row" data-act="open" data-id="${esc(s.id)}">${grade(ev(s).score.grade)}<div class="grow"><div class="t">${esc(s.name)}</div><div class="m">${esc(s.source || "")} · ${money(s.asking_price)}${ev(s).appraisal?.incomplete ? " · needs data" : ""}</div></div>${fitChip(ev(s).fit)}<span class="chip ${ev(s).appraisal?.viable ? "ok" : ""}">${ev(s).score.score}</span></div>`).join("") || '<div class="empty">No sites match the filters</div>'}
      </div></div>
      <div class="card pad"><h3 style="margin-bottom:12px">Pipeline</h3>
        ${funnel.map(([st, n]) => `<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px"><span style="width:74px;color:var(--muted);font-size:12.5px">${st}</span><div class="bar" style="flex:1"><i style="width:${n / fmax * 100}%"></i></div><b style="width:22px;text-align:right">${n}</b></div>`).join("")}
      </div>
    </div>
  </div>`;
  const pins = all.filter(s => s.lat != null).map(s => ({ id: s.id, lat: s.lat, lon: s.lon, g: ev(s).score.grade, snap: !!s.snapshot, name: s.name, ask: s.asking_price, score: ev(s).score.score, src: s.source }));
  mapInst = new MiniMap($("#map"), pins, id => openSite(id));
  mapInst.setTheme(document.documentElement.dataset.theme === "dark");
}
const kpi = (l, v, s) => `<div class="card kpi"><div class="l">${l}</div><div class="v">${v}</div><div class="s">${s || "&nbsp;"}</div></div>`;

/* ---------- mini slippy map (Web Mercator, CARTO tiles) ---------- */
class MiniMap {
  constructor(el, pins, onOpen) {
    this.el = el; this.pins = pins; this.onOpen = onOpen; this.dark = false;
    el.innerHTML = '<div class="tiles"></div><div class="marks"></div><div class="zoom"><button data-z="1">+</button><button data-z="-1">−</button></div><div class="attr">© OpenStreetMap contributors © CARTO</div>';
    this.tiles = $(".tiles", el); this.marks = $(".marks", el);
    this.z = 6; this.c = { lat: 52.8, lon: -1.6 };
    if (pins.length) this.fit();
    else el.insertAdjacentHTML("beforeend", '<div class="map-empty">No mapped sites yet.<br>Refresh listings or add a site with a postcode.</div>');
    this.bind(); this.draw();
    this.ro = new ResizeObserver(() => this.draw()); this.ro.observe(el);
  }
  destroy() { this.ro?.disconnect(); }
  setTheme(d) { this.dark = d; this.draw(true); }
  px(lat, lon, z = this.z) { const s = 256 * 2 ** z, r = lat * Math.PI / 180; return { x: (lon + 180) / 360 * s, y: (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * s }; }
  ll(x, y, z = this.z) { const s = 256 * 2 ** z, n = Math.PI - 2 * Math.PI * y / s; return { lat: 180 / Math.PI * Math.atan(Math.sinh(n)), lon: x / s * 360 - 180 }; }
  fit() {
    const w = this.el.clientWidth || 800, h = this.el.clientHeight || 540;
    const lats = this.pins.map(p => p.lat), lons = this.pins.map(p => p.lon);
    const b = { n: Math.max(...lats), s: Math.min(...lats), e: Math.max(...lons), w: Math.min(...lons) };
    this.c = { lat: (b.n + b.s) / 2, lon: (b.e + b.w) / 2 };
    for (let z = 12; z >= 4; z--) { const a = this.px(b.n, b.w, z), c = this.px(b.s, b.e, z); if (c.x - a.x < w - 120 && c.y - a.y < h - 120) { this.z = z; return; } this.z = 4; }
  }
  bind() {
    let drag = null;
    this.el.addEventListener("pointerdown", e => { if (e.target.closest(".pin,.zoom")) return; drag = { x: e.clientX, y: e.clientY }; this.el.setPointerCapture(e.pointerId); });
    this.el.addEventListener("pointermove", e => {
      if (!drag) return;
      const p = this.px(this.c.lat, this.c.lon); p.x -= e.clientX - drag.x; p.y -= e.clientY - drag.y; drag = { x: e.clientX, y: e.clientY };
      this.c = this.ll(p.x, p.y); this.draw();
    });
    this.el.addEventListener("pointerup", () => drag = null);
    this.el.addEventListener("wheel", e => { e.preventDefault(); this.zoom(e.deltaY < 0 ? 1 : -1); }, { passive: false });
    $$(".zoom button", this.el).forEach(b => b.onclick = () => this.zoom(+b.dataset.z));
  }
  zoom(d) { this.z = Math.max(4, Math.min(16, this.z + d)); this.draw(); }
  draw(force) {
    const w = this.el.clientWidth, h = this.el.clientHeight; if (!w) return;
    const cp = this.px(this.c.lat, this.c.lon), z = this.z, n = 2 ** z;
    const x0 = Math.floor((cp.x - w / 2) / 256), x1 = Math.floor((cp.x + w / 2) / 256), y0 = Math.floor((cp.y - h / 2) / 256), y1 = Math.floor((cp.y + h / 2) / 256);
    const style = this.dark ? "dark_all" : "light_all", r = devicePixelRatio > 1 ? "@2x" : "";
    let html = "";
    for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) {
      if (y < 0 || y >= n) continue;
      const xx = ((x % n) + n) % n, sub = "abcd"[(x + y) & 3];
      html += `<img loading="lazy" style="left:${x * 256 - cp.x + w / 2}px;top:${y * 256 - cp.y + h / 2}px" src="https://${sub}.basemaps.cartocdn.com/${style}/${z}/${xx}/${y}${r}.png" onerror="this.remove()">`;
    }
    this.tiles.innerHTML = html;
    const cl = [];
    this.pins.forEach((p, i) => {
      const q = this.px(p.lat, p.lon), X = q.x - cp.x + w / 2, Y = q.y - cp.y + h / 2;
      if (X < -30 || Y < -30 || X > w + 30 || Y > h + 30) return;
      const c = cl.find(c => Math.hypot(c.X - X, c.Y - Y) < 30);
      if (c) { c.items.push(i); c.X = (c.X * (c.items.length - 1) + X) / c.items.length; c.Y = (c.Y * (c.items.length - 1) + Y) / c.items.length; }
      else cl.push({ X, Y, items: [i] });
    });
    this.marks.innerHTML = cl.map((c, k) => {
      if (c.items.length === 1) { const p = this.pins[c.items[0]]; return `<div class="pin ${p.snap ? "snap" : ""}" data-i="${c.items[0]}" style="left:${c.X}px;top:${c.Y}px;background:${gcol(p.g)}">${p.g === "N" || !p.g ? "?" : p.g}</div>`; }
      return `<div class="pin cl" data-k="${k}" style="left:${c.X}px;top:${c.Y}px;width:36px;height:36px;background:var(--ink);color:var(--bg)">${c.items.length}</div>`;
    }).join("");
    $$(".pin.cl", this.marks).forEach(el => el.onclick = () => { const c = cl[+el.dataset.k]; const pts = c.items.map(i => this.pins[i]); this.c = { lat: pts.reduce((a, p) => a + p.lat, 0) / pts.length, lon: pts.reduce((a, p) => a + p.lon, 0) / pts.length }; this.zoom(2); });
    $$(".pin:not(.cl)", this.marks).forEach(el => {
      const p = this.pins[+el.dataset.i];
      el.onclick = () => this.onOpen(p.id);
      el.onmouseenter = () => { const t = document.createElement("div"); t.className = "tip"; t.innerHTML = `<b>${esc(p.name)}</b><br>${money(p.ask)} · score ${p.score}<br><span style="opacity:.7">${esc(p.src || "")}</span>`; t.style.left = Math.min(el.offsetLeft + 18, w - 270) + "px"; t.style.top = Math.max(8, el.offsetTop - 66) + "px"; this.el.append(t); el._t = t; };
      el.onmouseleave = () => el._t?.remove();
    });
  }
}

/* ---------- sites table ---------- */
function vSites() {
  const srcs = ["all", ...new Set(sites().map(s => s.source || "Other"))];
  const rows = filtered();
  const val = { score: s => ev(s).score.score, name: s => s.name.toLowerCase(), ask: s => s.asking_price || 0, max: s => ev(s).appraisal?.max_bid ?? -1, head: s => ev(s).appraisal?.headroom_vs_asking ?? -9, flags: s => ev(s).flags.length, fit: s => ev(s).fit?.score ?? -1, stage: s => D.stages.indexOf(s.stage), src: s => s.source || "" }[sortKey] || (s => 0);
  rows.sort((a, b) => (val(a) > val(b) ? 1 : -1) * sortDir);
  const th = (k, l, cls = "") => `<th class="${cls}" data-act="sort" data-k="${k}">${l}${sortKey === k ? (sortDir > 0 ? " ↑" : " ↓") : ""}</th>`;
  $("#view").innerHTML = `
  <div class="toolbar">
    ${["active", "all", ...D.stages].map(s => `<button class="pill ${F.stage === s ? "on" : ""}" data-act="fstage" data-v="${s}">${s === "active" ? "Active" : s === "all" ? "All" : s}</button>`).join("")}
    <span style="flex:1"></span>
    <select id="fsrc" style="width:auto">${srcs.map(s => `<option value="${esc(s)}" ${F.src === s ? "selected" : ""}>${s === "all" ? "All sources" : esc(s)}</option>`).join("")}</select>
    <select id="fstrat" style="width:auto"><option value="all">All strategies</option>${Object.entries(D.strategies).map(([k, v]) => `<option value="${k}" ${F.strat === k ? "selected" : ""}>${v}</option>`).join("")}</select>
    <button class="pill ${F.viable ? "on" : ""}" data-act="fviable">Viable only</button>${D.investor?.active ? `<button class="pill ${F.fit ? "on" : ""}" data-act="ffit">Inside my mandate</button>` : ""}
  </div>
  <div class="card tablewrap"><table><thead><tr>${th("score", "Score")}${th("name", "Site")}${th("src", "Source")}${th("ask", "Asking", "num")}${th("max", "Max bid", "num")}${th("head", "Headroom", "num")}${th("flags", "Flags", "num")}${D.investor?.active ? th("fit", "Fit") : ""}${th("stage", "Stage")}</tr></thead><tbody>
  ${rows.map(s => { const e = ev(s), a = e.appraisal; return `<tr data-act="open" data-id="${esc(s.id)}">
    <td>${grade(e.score.grade)}</td>
    <td><div class="tname">${esc(s.name)}</div><div class="tsub">${esc(s.property_type || D.strategies[e.strategy])}${s.snapshot ? " · snapshot" : ""}${s.demo_rich ? " · illustrative" : s.demo ? " · demo" : ""}${s.deal ? " · deal" : ""}${s._ndocs ? ` · ${s._ndocs} docs` : ""}</div></td>
    <td>${esc(s.source || "")}</td><td class="num">${money(s.asking_price)}</td>
    <td class="num">${a && !a.incomplete ? money(a.max_bid) : '<span class="chip lo">needs data</span>'}</td>
    <td class="num ${a && !a.incomplete && a.headroom_vs_asking != null ? (a.headroom_vs_asking >= 0 ? "pos" : "neg") : ""}">${a && !a.incomplete && a.headroom_vs_asking != null ? pct(a.headroom_vs_asking, 0) : ""}</td>
    <td class="num">${e.flags.length ? `<span class="chip ${e.flags.some(f => f.severity === "High") ? "hi" : "med"}">${e.flags.length}</span>` : ""}</td>
    ${D.investor?.active ? `<td>${fitChip(e.fit)}</td>` : ""}<td><span class="chip">${esc(s.stage)}</span></td></tr>`; }).join("") || `<tr><td colspan="9"><div class="empty">Nothing matches. Try Refresh listings or clear the filters.</div></td></tr>`}
  </tbody></table></div>`;
  $("#fsrc").onchange = e => { F.src = e.target.value; render(); };
  $("#fstrat").onchange = e => { F.strat = e.target.value; render(); };
}

/* ---------- pipeline ---------- */
function vPipeline() {
  const rows = filtered();
  $("#view").innerHTML = `<div class="board">${D.stages.map(st => { const cs = rows.filter(s => s.stage === st).sort((a, b) => ev(b).score.score - ev(a).score.score); return `
  <div class="col" data-stage="${st}"><h4><span>${st}</span><span>${cs.length}</span></h4>
  ${cs.map(s => `<div class="kc" draggable="true" data-id="${esc(s.id)}" data-act="open"><div class="t">${esc(s.name)}</div><div class="m"><span>${money(s.asking_price)}</span><span style="display:flex;gap:6px;align-items:center">${esc(s.source || "")}${grade(ev(s).score.grade).replace('class="grade', 'style="width:22px;height:22px;font-size:11px;border-radius:7px" class="grade')}</span></div></div>`).join("")}</div>`; }).join("")}</div>`;
  $$(".kc").forEach(k => k.ondragstart = e => { e.dataTransfer.setData("id", k.dataset.id); });
  $$(".col").forEach(c => {
    c.ondragover = e => { e.preventDefault(); c.classList.add("over"); }; c.ondragleave = () => c.classList.remove("over");
    c.ondrop = async e => { e.preventDefault(); const id = e.dataTransfer.getData("id"); await api("/api/site", { site: { id, stage: c.dataset.stage } }); await load(); };
  });
}

/* ---------- sourcing ---------- */
const STATUS = { ok: ["ok", "Live"], blocked: ["hi", "Blocked"], robots: ["med", "Disallowed"], js: ["med", "Needs browser"], empty: ["med", "No results"], error: ["hi", "Error"], running: ["acc", "Running"], queued: ["", "Queued"] };
function vSourcing() {
  const job = D.job || {}, js = job.sources || {}, cfg = D.scrape;
  const done = Object.values(js).filter(x => !["queued", "running"].includes(x.status)).length, tot = Object.keys(js).length;
  const feed = sites().filter(s => s.listing).sort((a, b) => (b.last_seen || "").localeCompare(a.last_seen || "")).slice(0, 12);
  $("#view").innerHTML = `
  ${job.running ? `<div class="card pad" style="margin-bottom:16px"><div style="display:flex;justify-content:space-between;margin-bottom:8px"><b>Refreshing sources</b><span class="m">${done} of ${tot}</span></div><div class="bar"><i style="width:${tot ? done / tot * 100 : 0}%"></i></div></div>` : ""}
  <div class="src-grid">${D.sources.map(s => {
    const st = js[s.id], on = cfg.enabled.includes(s.id), c = STATUS[st?.status] || ["", s.verified ? "Ready" : "Unverified"];
    return `<div class="card src"><div class="top2"><div style="display:flex;gap:10px;align-items:center"><div class="rank">${s.rank}</div><div><div class="nm">${esc(s.name)}</div><div class="tsub">${s.kind === "agent" ? "Top 10 agent" : "Aggregator"}</div></div></div><button class="switch ${on ? "on" : ""}" data-act="togsrc" data-id="${s.id}" title="Include in refresh"></button></div>
    <div><span class="chip ${c[0]}"><i class="dot"></i>${c[1]}</span>${st?.count != null ? ` <span class="chip">${st.count} listings</span>` : ""}${st?.fallback ? ' <span class="chip lo">snapshot</span>' : ""}</div>
    <div class="msg">${esc(st?.message || s.note || (s.verified ? "Search page verified in testing." : "Search URL not yet verified."))}</div>
    <div style="display:flex;gap:6px"><button class="btn sm" data-act="runsrc" data-id="${s.id}" ${job.running ? "disabled" : ""}>Refresh</button><button class="btn sm" data-act="editsrc" data-id="${s.id}">Edit URL</button></div></div>`; }).join("")}</div>
  <div class="two" style="margin-top:18px">
    <div class="card pad"><h3 style="margin-bottom:6px">Scrape behaviour</h3><div class="tsub" style="margin-bottom:12px">Polite by design: robots.txt, rate limits and a cache.</div>
      <div class="three"><label class="field"><span>Pages per search</span><input type="number" min="1" max="10" id="sc_pages" value="${cfg.max_pages}"></label>
      <label class="field"><span>Opportunities only</span><select id="sc_opp"><option value="1" ${cfg.opportunities_only ? "selected" : ""}>Land, conversions, investment</option><option value="0" ${!cfg.opportunities_only ? "selected" : ""}>Everything</option></select></label>
      <label class="field"><span>Respect robots.txt</span><select id="sc_rob"><option value="1" ${cfg.respect_robots ? "selected" : ""}>Yes (recommended)</option><option value="0" ${!cfg.respect_robots ? "selected" : ""}>No</option></select></label></div>
      <div style="margin-top:12px"><label class="field"><span>Snapshot fallback</span><select id="sc_snap"><option value="1" ${cfg.use_snapshot ? "selected" : ""}>Use bundled snapshot (21 Sep 2026) when a source fails</option><option value="0" ${!cfg.use_snapshot ? "selected" : ""}>Never</option></select></label></div>
      <p class="tsub" style="margin-top:12px">Many portals restrict automated access in their terms. Use for personal research on public pages and check each site's terms before commercial use.</p></div>
    <div class="card pad"><h3 style="margin-bottom:6px">Open data and manual import</h3><div class="tsub" style="margin-bottom:12px">Brownfield land registers, CSV, or pasted alert emails.</div>
      <div style="display:flex;gap:8px;margin-bottom:12px"><input type="text" id="bf_pc" placeholder="Centre postcode, e.g. M5 3AA"><input type="number" id="bf_r" value="10" style="width:90px"><button class="btn" data-act="brownfield">Find brownfield</button></div>
      <textarea id="imp_text" placeholder="Paste CSV rows (name,address,postcode,price,site_ha,sqft,url) or a saved-search alert email"></textarea>
      <div style="display:flex;gap:8px;margin-top:8px"><button class="btn" data-act="imp" data-k="csv">Import CSV</button><button class="btn" data-act="imp" data-k="alert">Parse alert email</button></div></div>
  </div>
  <div class="sec"><h3>Latest listings</h3><span class="m">${feed.length ? "most recently seen" : ""}</span></div>
  <div class="card list">${feed.map(s => `<div class="row" data-act="open" data-id="${esc(s.id)}">${grade(ev(s).score.grade)}<div class="grow"><div class="t">${esc(s.name)}</div><div class="m">${esc(s.source)} · ${esc(s.property_type || "")} · ${money(s.asking_price)}${s.snapshot ? " · snapshot" : ""}</div></div><span class="m">${when(s.last_seen)}</span></div>`).join("") || '<div class="empty">No listings yet. Press Refresh listings.</div>'}</div>`;
  ["sc_pages", "sc_opp", "sc_rob", "sc_snap"].forEach(id => $("#" + id).onchange = saveScrape);
}
async function saveScrape() {
  await api("/api/settings", { scrape: { max_pages: +$("#sc_pages").value || 2, opportunities_only: $("#sc_opp").value === "1", respect_robots: $("#sc_rob").value === "1", use_snapshot: $("#sc_snap").value === "1" } });
  D.scrape = { ...D.scrape, max_pages: +$("#sc_pages").value || 2, opportunities_only: $("#sc_opp").value === "1", respect_robots: $("#sc_rob").value === "1", use_snapshot: $("#sc_snap").value === "1" };
}
async function startScrape(ids) {
  const r = await api("/api/scrape", ids ? { sources: ids } : {});
  if (!r.started) return toast("A refresh is already running");
  D.job = await api("/api/job"); render();
}
function poll() {
  clearInterval(pollT);
  pollT = setInterval(async () => {
    D.job = await api("/api/job");
    if (!D.job.running) {
      clearInterval(pollT); const j = D.job; await load();
      toast(`Refresh complete: ${j.added} new, ${j.updated} updated`);
    } else if (view === "sourcing") { const y = $("#view").scrollTop; render(); $("#view").scrollTop = y; }
  }, 1200);
}
$("#refreshBtn").onclick = () => startScrape();

/* ---------- settings ---------- */
function vSettings() {
  const groups = {}; for (const [k, v] of Object.entries(D.spec)) (groups[v.group] ||= []).push(k);
  $("#view").innerHTML = `
  <div class="grid" style="grid-template-columns:minmax(0,2fr) minmax(300px,1fr);align-items:start">
   <div class="grid">${Object.entries(groups).map(([g, ks]) => `<div class="card pad"><h3 style="margin-bottom:12px">${g}</h3><div class="three">${ks.map(k => `<label class="field"><span>${esc(D.spec[k].label)}</span><input type="number" step="${D.spec[k].step}" data-as="${k}" value="${D.assumptions[k]}"></label>`).join("")}</div></div>`).join("")}</div>
   <div class="grid">
    <div class="card pad"><h3 style="margin-bottom:12px">Scorecard weights</h3>${Object.entries(D.weights).map(([k, v]) => `<label class="field" style="margin-bottom:10px"><span style="display:flex;justify-content:space-between"><b style="text-transform:capitalize;color:var(--ink)">${k}</b><em style="font-style:normal">${Math.round(v * 100)}%</em></span><input type="range" min="0" max="1" step="0.05" value="${v}" data-w="${k}"></label>`).join("")}</div>
    <div class="card pad"><h3 style="margin-bottom:12px">Claude API</h3><label class="field"><span>Anthropic API key ${D.has_key ? '<span class="chip ok">saved</span>' : ""}</span><input type="password" id="apikey" placeholder="${D.has_key ? "Saved. Paste to replace" : "sk-ant-..."}"></label>
      <label class="field" style="margin-top:10px"><span>Model</span><input type="text" id="model" value="${esc(D.model)}"></label>
      <p class="tsub" style="margin-top:10px">Powers planning document analysis and Q&amp;A. The key is stored on this Mac only.</p></div>
    <div class="card pad"><h3 style="margin-bottom:12px">Sold price data (EPC)</h3><p class="tsub" style="margin-bottom:10px">Land Registry sales need no key. To turn sales into £ per sq ft, add a free key from epc.opendatacommunities.org.</p>
      <label class="field"><span>Registered email</span><input type="text" id="epc_email" value="${esc(D.epc?.email || "")}"></label>
      <label class="field" style="margin-top:10px"><span>EPC API key ${D.epc?.has_key ? '<span class="chip ok">saved</span>' : ""}</span><input type="password" id="epc_key" placeholder="${D.epc?.has_key ? "Saved. Paste to replace" : "Paste key"}"></label>
      <button class="btn sm" style="margin-top:10px" data-act="saveepc">Save</button></div>
    <div class="card pad"><h3 style="margin-bottom:12px">Data</h3><div style="display:flex;flex-direction:column;gap:8px">
      <button class="btn" data-act="restoredemo">Restore illustrative demo deals</button><button class="btn" data-act="cleardemo">Remove all demo sites</button><button class="btn" data-act="resetset">Reset assumptions to defaults</button></div></div>
   </div></div>`;
  $$("[data-as]").forEach(i => i.onchange = async () => { D.assumptions[i.dataset.as] = +i.value; await api("/api/settings", { assumptions: { [i.dataset.as]: +i.value } }); toast("Saved"); await load(); });
  $$("[data-w]").forEach(i => i.onchange = async () => { D.weights[i.dataset.w] = +i.value; await api("/api/settings", { weights: { [i.dataset.w]: +i.value } }); await load(); vSettings(); });
  $("#apikey").onchange = async e => { await api("/api/settings", { api_key: e.target.value.trim() }); toast("API key saved"); await load(); };
  $("#model").onchange = async e => { await api("/api/settings", { model: e.target.value.trim() }); toast("Model saved"); };
}

/* ---------- workbench drawer ---------- */
const AKEYS = ["sales_psf", "rent_psf", "build_psf", "exit_yield", "affordable_pct", "s106_per_unit", "planning_months", "build_months", "finance_rate", "target_profit_gdv"];
async function openSite(id, tab) {
  drawer = { id, tab: tab || (drawer && drawer.id === id ? drawer.tab : "overview"), ovr: {}, chat: [] };
  $("#drawer").classList.add("on"); $("#scrim").classList.add("on");
  await refreshDrawer();
}
function closeDrawer() { drawer = null; $("#drawer").classList.remove("on"); $("#scrim").classList.remove("on"); }
async function refreshDrawer(soft) {
  if (!drawer) return;
  const s = sites().find(x => x.id === drawer.id); if (!s) return closeDrawer();
  drawer.ev = await api("/api/appraise", { id: s.id, assumptions: drawer.ovr });
  drawer.site = s; paintDrawer(soft);
}
function effective(s, k) { return drawer.ovr[k] ?? (k === "sales_psf" || k === "rent_psf" ? (s[k] || D.assumptions[k]) : (s.ovr?.[k] ?? D.assumptions[k])); }
function paintDrawer(soft) {
  const s = drawer.site, e = drawer.ev, a = e.appraisal, sc = e.score;
  if (soft) { $("#dbody").innerHTML = tabBody(); bindTab(); return; }
  $("#drawer").innerHTML = `<div class="dh"><div class="r1"><div><h2>${esc(s.name)}</h2><div class="a">${[s.demo_rich ? "Illustrative" : "", s.address, s.source, s.snapshot ? "snapshot" : "", s.geo_precision === "outcodes" || s.geo_precision === "approx" ? "approximate location" : ""].filter(Boolean).map(esc).join(" · ")}</div></div>
    <div style="display:flex;gap:10px;align-items:center">${s.url ? `<button class="btn sm" data-act="ext" data-url="${esc(s.url)}">${I.link}Listing</button>` : ""}<div class="score"><div class="ring">${ring(sc.score, gcol(sc.grade))}<b>${sc.score}</b></div></div><button class="ghost" data-act="close">${I.x}</button></div></div>
    <div class="tabs">${[["overview", "Overview"], ["appraisal", "Appraisal"], ["model", "Model"], ["planning", "Planning"], ["documents", `Documents${s.docs?.length ? ` (${s.docs.length})` : ""}`], ["market", "Market"], ["details", "Details"]].map(([k, l]) => `<button class="tab ${drawer.tab === k ? "on" : ""}" data-act="tab" data-v="${k}">${l}</button>`).join("")}</div></div>
    <div class="db" id="dbody">${tabBody()}</div>`;
  bindTab();
}
const ring = (v, c) => `<svg viewBox="0 0 36 36" style="width:64px;height:64px;transform:rotate(-90deg)"><circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--line)" stroke-width="3"/><circle cx="18" cy="18" r="15.5" fill="none" stroke="${c}" stroke-width="3" stroke-linecap="round" stroke-dasharray="${v * .974} 100"/></svg>`;
function tabBody() { return { overview: tOverview, appraisal: tAppraisal, model: tModel, planning: tPlanning, documents: tDocuments, market: tMarket, details: tDetails }[drawer.tab](); }
function verdict(a, flags) {
  if (!a || a.incomplete) return ["Needs data", "var(--muted)", `Add ${(a?.missing || ["site details"]).join(" and ")} to appraise this site.`];
  const hi = flags.some(f => f.severity === "High");
  if (a.viable && !hi) return ["Pursue", "var(--ok)", "Meets your return target at the asking price with no high-severity flags."];
  if (a.viable) return ["Pursue with conditions", "var(--gB)", "Returns work, but high-severity flags need resolving before committing."];
  if (a.max_bid > 0) return ["Renegotiate", "var(--med)", `Returns fall short at asking. Your ceiling is ${money(a.max_bid)}.`];
  return ["Pass", "var(--hi)", "No positive land value at your target return."];
}
function tOverview() {
  const s = drawer.site, e = drawer.ev, a = e.appraisal, [v, col, why] = verdict(a, e.flags);
  const parts = e.score.parts;
  return `<div class="verdict"><div><div class="l" style="font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:600">Recommendation</div><div class="vt" style="color:${col}">${v}</div><div class="tsub">${why}</div></div>
    ${a && !a.incomplete ? `<div style="text-align:right"><div class="tsub">Opening offer</div><b style="font-size:20px">${money(a.opening_offer)}</b><div class="tsub">Walk away above ${money(a.walk_away)}</div></div>` : ""}</div>
  ${a && !a.incomplete ? `<div class="stat4">${kpi("GDV / exit value", money(a.gdv), `${a.units} units`)}${kpi("Residual land value", money(a.rlv), `asking ${money(a.asking)}`)}${kpi("Profit at asking", pct(a.profit_basis === "gdv" ? a.profit_on_gdv : a.profit_on_cost), `target ${pct(a.target_profit, 0)} on ${a.profit_basis}`)}${kpi("Levered IRR", pct(a.irr_levered, 0), `EM ${a.equity_multiple.toFixed(2)}x`)}</div>` : ""}
  <div class="two"><div class="card"><div class="h"><h3>Red flags</h3><span class="m">${e.flags.length}</span></div>${e.flags.map(f => `<div class="flag"><div class="fh"><span class="chip ${sevClass(f.severity)}">${f.severity}</span>${esc(f.flag)}</div><p>${esc(f.why)}</p><p style="margin-top:3px;color:var(--ink2)"><b>Mitigation:</b> ${esc(f.mitigation)}</p></div>`).join("") || '<div class="empty" style="padding:24px">No red flags from current data</div>'}</div>
  <div class="card pad"><h3 style="margin-bottom:14px">Scorecard</h3>${Object.entries(parts).map(([k, v]) => `<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:4px"><span style="text-transform:capitalize">${k}</span><b>${v}</b></div><div class="bar"><i style="width:${v}%"></i></div></div>`).join("")}
  <div class="tsub">Weights are set in Settings.</div></div></div>${tOverviewExtra()}`;
}
function tAppraisal() {
  const s = drawer.site;
  return `<div class="two" style="grid-template-columns:320px 1fr;align-items:start"><div class="card pad"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><h3>Assumptions</h3><span class="chip acc">live</span></div>
    <label class="field" style="margin-bottom:10px"><span>Strategy</span><select id="ap_strat">${Object.entries(D.strategies).map(([k, v]) => `<option value="${k}" ${drawer.ev.strategy === k ? "selected" : ""}>${v}</option>`).join("")}</select></label>
    <div style="display:grid;gap:10px">${AKEYS.map(k => `<label class="field"><span>${esc(D.spec[k].label)}</span><input type="number" step="${D.spec[k].step}" data-ap="${k}" value="${+(+effective(s, k)).toFixed(4)}"></label>`).join("")}</div>
    <div style="display:flex;gap:8px;margin-top:14px"><button class="btn sm primary" data-act="saveovr">Save to site</button><button class="btn sm" data-act="resetovr">Reset</button></div></div>
    <div id="apRes">${apResults()}</div></div>`;
}
function apResults() {
  const e = drawer.ev, a = e.appraisal, sens = e.sens;
  if (!a) return '<div class="empty">Could not appraise this site.</div>';
  const notice = a.incomplete ? `<div class="notice">Missing ${a.missing.join(", ")}. Figures below use placeholders until you add it in Site details.</div>` : "";
  const items = [["Land and costs", a.land_cost, "#0F766E"], ["Land finance", a.land_finance, "#5EA6A1"], ["Build / refurb", a.build, "#3B6BA5"], ["Contingency and fees", a.contingency + a.fees, "#7A8FB8"], ["S106 and CIL", a.s106 + a.cil, "#B89A5B"], ["Build finance", a.build_finance, "#A66A5B"], ["Sales costs", a.sales_costs, "#8B8F98"]];
  const tot = items.reduce((n, i) => n + i[1], 0), scale = Math.max(tot, a.gdv);
  return `${notice}<div class="stat4" style="grid-template-columns:repeat(3,1fr)">${kpi("Residual land value", money(a.rlv), `asking ${money(a.asking)}`)}${kpi("Profit at asking", pct(a.profit_basis === "gdv" ? a.profit_on_gdv : a.profit_on_cost), `target ${pct(a.target_profit, 0)}`)}${kpi("Yield on cost", pct(a.yield_on_cost, 2), `NOI ${money(a.noi)}`)}${kpi("IRR unlevered", pct(a.irr_unlevered, 1), "before debt")}${kpi("IRR levered", pct(a.irr_levered, 1), `EM ${a.equity_multiple.toFixed(2)}x`)}${kpi("Peak equity", money(a.peak_equity), "levered")}</div>
  <div class="card pad" style="margin-bottom:14px"><h3 style="margin-bottom:12px">Cost stack vs value</h3>
   <div style="display:flex;height:26px;border-radius:8px;overflow:hidden;background:var(--surface2)">${items.map(i => `<div title="${i[0]} ${money(i[1])}" style="width:${i[1] / scale * 100}%;background:${i[2]}"></div>`).join("")}</div>
   <div class="legend">${items.map(i => `<span><i style="background:${i[2]}"></i>${i[0]} ${money(i[1])}</span>`).join("")}</div>
   <div style="display:flex;justify-content:space-between;margin-top:12px"><span class="tsub">Total cost <b style="color:var(--ink)">${money(a.total_cost)}</b></span><span class="tsub">Exit value <b style="color:var(--ink)">${money(a.gdv)}</b></span><span class="tsub">Profit <b class="${a.profit >= 0 ? "pos" : "neg"}">${money(a.profit)}</b></span></div></div>
  <div class="card pad" style="margin-bottom:14px"><h3 style="margin-bottom:4px">Sensitivity</h3><div class="tsub" style="margin-bottom:10px">Profit on ${a.profit_basis === "gdv" ? "GDV" : "cost"} with the land price held at ${money(a.asking || a.rlv)}. Rows: ${esc(sens.ylabel)}. Columns: ${esc(sens.xlabel)}.</div>${heat(sens, a.target_profit)}</div>
  <div class="card pad"><h3 style="margin-bottom:10px">Cash flow</h3>${cfChart(a.cashflow)}</div>`;
}
function heat(sens, target) {
  const n = sens.x.length;
  const col = v => { const t = Math.max(-1, Math.min(1, (v - target) / 0.12)); return t >= 0 ? `hsl(${140 - (1 - t) * 60} 55% ${72 - t * 8}%)` : `hsl(${20 + (1 + t) * 40} 70% ${72 + t * 6}%)`; };
  return `<div class="hm" style="grid-template-columns:54px repeat(${n},1fr)"><div></div>${sens.x.map(x => `<div class="hml" style="background:none;color:var(--muted)">${x > 0 ? "+" : ""}${Math.round(x * 100)}%</div>`).join("")}
  ${sens.z.map((row, i) => `<div class="hml" style="background:none;padding:8px 6px 0 0;color:var(--muted);text-align:right">${sens.y[i] > 0 ? "+" : ""}${Math.round(sens.y[i] * 100)}%</div>${row.map((v, j) => `<div style="background:${col(v)};${i === 3 && j === 3 ? "outline:2px solid var(--ink);outline-offset:-2px" : ""}">${(v * 100).toFixed(0)}%</div>`).join("")}`).join("")}</div>`;
}
function cfChart(rows) {
  const W = 700, H = 200, p = 26, n = rows.length; const v = rows.map(r => r.unlevered); let cum = 0; const c = v.map(x => cum += x);
  const mn = Math.min(0, ...v, ...c), mx = Math.max(0, ...v, ...c), y = x => H - p - (x - mn) / (mx - mn || 1) * (H - 2 * p), bw = (W - 2 * p) / n;
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;stroke-width:1">
   <line x1="${p}" x2="${W - p}" y1="${y(0)}" y2="${y(0)}" stroke="var(--line)"/>
   ${v.map((x, i) => `<rect x="${p + i * bw + 1}" y="${Math.min(y(x), y(0))}" width="${Math.max(1, bw - 2)}" height="${Math.abs(y(x) - y(0))}" fill="var(--accent)" opacity=".75" rx="1.5"/>`).join("")}
   <polyline fill="none" stroke="var(--med)" stroke-width="2.2" points="${c.map((x, i) => `${p + i * bw + bw / 2},${y(x)}`).join(" ")}"/>
   <text x="${p}" y="${H - 6}" fill="var(--muted)" font-size="11">Month 0</text><text x="${W - p}" y="${H - 6}" fill="var(--muted)" font-size="11" text-anchor="end">Month ${n - 1}</text>
   <text x="${W - p}" y="14" fill="var(--muted)" font-size="11" text-anchor="end">Bars: monthly net. Line: cumulative (${money(mn)} to ${money(mx)})</text></svg>`;
}
function tDetails() {
  const s = drawer.site, v = (k, d = "") => esc(s[k] ?? d);
  const chk = [["green_belt", "Green Belt"], ["conservation_area", "Conservation area"], ["listed", "Listed"], ["contamination", "Contamination"], ["trees", "Trees / ecology"], ["access_issue", "Access issue"], ["brownfield", "Brownfield"]];
  return `<div class="card pad"><div class="three">
   <label class="field"><span>Name</span><input type="text" data-f="name" value="${v("name")}"></label><label class="field"><span>Address</span><input type="text" data-f="address" value="${v("address")}"></label><label class="field"><span>Postcode</span><input type="text" data-f="postcode" value="${v("postcode")}"></label>
   <label class="field"><span>Asking price (£)</span><input type="number" data-f="asking_price" data-n value="${v("asking_price")}"></label><label class="field"><span>Site area (ha)</span><input type="number" step="0.05" data-f="site_ha" data-n value="${v("site_ha")}"></label><label class="field"><span>Units (blank uses density)</span><input type="number" data-f="units" data-n value="${v("units")}"></label>
   <label class="field"><span>Existing floor area (sq ft)</span><input type="number" data-f="existing_sqft" data-n value="${v("existing_sqft")}"></label>
   <label class="field"><span>Strategy</span><select data-f="strategy">${Object.entries(D.strategies).map(([k, l]) => `<option value="${k}" ${s.strategy === k ? "selected" : ""}>${l}</option>`).join("")}</select></label>
   <label class="field"><span>Planning status</span><select data-f="planning_status">${["Unknown", "None", "Pre-app", "Allocated", "Consented", "Refused"].map(o => `<option ${s.planning_status === o ? "selected" : ""}>${o}</option>`).join("")}</select></label>
   <label class="field"><span>Stage</span><select data-f="stage">${D.stages.map(o => `<option ${s.stage === o ? "selected" : ""}>${o}</option>`).join("")}</select></label>
   <label class="field"><span>Flood zone</span><select data-f="flood_zone">${["1", "2", "3"].map(o => `<option ${String(s.flood_zone || "1") === o ? "selected" : ""}>${o}</option>`).join("")}</select></label>
   <label class="field"><span>Local sales £/sq ft</span><input type="number" data-f="sales_psf" data-n value="${v("sales_psf")}"></label><label class="field"><span>Local rent £/sq ft pa</span><input type="number" data-f="rent_psf" data-n value="${v("rent_psf")}"></label></div>
   <div style="display:flex;gap:16px;flex-wrap:wrap;margin:16px 0">${chk.map(([k, l]) => `<label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-c="${k}" ${s[k] ? "checked" : ""}>${l}</label>`).join("")}</div>
   <label class="field"><span>Notes</span><textarea data-f="notes" style="font-family:var(--font)">${v("notes")}</textarea></label>
   <div style="display:flex;gap:8px;margin-top:14px"><button class="btn primary" data-act="savesite">Save</button><button class="btn" data-act="constraints">Check open-data constraints</button><span style="flex:1"></span><button class="btn danger" data-act="delsite">Delete</button></div>
   <div id="cres" class="tsub" style="margin-top:12px"></div></div>`;
}
function bindTab() {
  const s = drawer.site;
  if (drawer.tab === "appraisal") {
    let t; $$("[data-ap]").forEach(i => i.oninput = () => { drawer.ovr[i.dataset.ap] = +i.value; clearTimeout(t); t = setTimeout(async () => { drawer.ev = await api("/api/appraise", { id: s.id, assumptions: drawer.ovr, strategy: $("#ap_strat").value }); $("#apRes").innerHTML = apResults(); }, 220); });
    $("#ap_strat").onchange = async e => { drawer.ev = await api("/api/appraise", { id: s.id, assumptions: drawer.ovr, strategy: e.target.value }); $("#apRes").innerHTML = apResults(); };
  }
  bindFeatureTab();
}
async function saveSite() {
  const s = { id: drawer.id };
  $$("[data-f]").forEach(i => { const v = i.value; s[i.dataset.f] = i.hasAttribute("data-n") ? (v === "" ? null : +v) : v; });
  $$("[data-c]").forEach(i => s[i.dataset.c] = i.checked);
  await api("/api/site", { site: s, regeocode: !!s.postcode && s.postcode !== drawer.site.postcode });
  toast("Saved"); await load();
}

/* ---------- modals ---------- */
function modal(html, onReady) { const m = $("#modal"); m.innerHTML = `<div class="modal">${html}</div>`; m.classList.add("on"); onReady?.(m); m.onclick = e => { if (e.target === m) closeModal(); }; }
function closeModal() { $("#modal").classList.remove("on"); }
function addSite() {
  modal(`<h3>Add a site</h3><div class="three"><label class="field"><span>Name</span><input type="text" id="ns_name"></label><label class="field"><span>Postcode</span><input type="text" id="ns_pc"></label><label class="field"><span>Asking price (£)</span><input type="number" id="ns_ask"></label>
  <label class="field"><span>Site area (ha)</span><input type="number" step="0.05" id="ns_ha"></label><label class="field"><span>Floor area (sq ft)</span><input type="number" id="ns_sq"></label><label class="field"><span>Strategy</span><select id="ns_st">${Object.entries(D.strategies).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}</select></label></div>
  <div class="mf"><button class="btn" data-act="closem">Cancel</button><button class="btn primary" data-act="createsite">Add site</button></div>`);
}
function editSrc(id) {
  const s = D.sources.find(x => x.id === id), cur = (D.scrape.overrides[id]?.urls || s.urls).join("\n");
  modal(`<h3>${esc(s.name)} search URLs</h3><p class="tsub">One URL per line. Use the agent's own search results page for land, development or investment stock.</p><textarea id="src_urls" style="min-height:110px">${esc(cur)}</textarea><div class="mf"><button class="btn" data-act="closem">Cancel</button><button class="btn primary" data-act="savesrc" data-id="${id}">Save</button></div>`);
}

/* ---------- events ---------- */
document.addEventListener("click", async e => {
  const t = e.target.closest("[data-act]"); if (!t) return;
  const act = t.dataset.act;
  try {
    if (act === "nav") { view = t.dataset.v; render(); }
    else if (act === "open") openSite(t.dataset.id);
    else if (act === "close") closeDrawer();
    else if (act === "tab") { drawer.tab = t.dataset.v; paintDrawer(); }
    else if (act === "sort") { const k = t.dataset.k; sortDir = sortKey === k ? -sortDir : -1; sortKey = k; render(); }
    else if (act === "fstage") { F.stage = t.dataset.v; render(); }
    else if (act === "fviable") { F.viable = !F.viable; render(); }
    else if (act === "togsrc") { const en = new Set(D.scrape.enabled); en.has(t.dataset.id) ? en.delete(t.dataset.id) : en.add(t.dataset.id); D.scrape.enabled = [...en]; await api("/api/settings", { scrape: { enabled: D.scrape.enabled } }); render(); }
    else if (act === "runsrc") startScrape([t.dataset.id]);
    else if (act === "editsrc") editSrc(t.dataset.id);
    else if (act === "savesrc") { const urls = $("#src_urls").value.split("\n").map(x => x.trim()).filter(Boolean); const o = { ...D.scrape.overrides, [t.dataset.id]: { urls } }; await api("/api/settings", { scrape: { overrides: o } }); closeModal(); await load(); toast("URLs saved"); }
    else if (act === "closem") closeModal();
    else if (act === "brownfield") { const r = await api("/api/brownfield", { postcode: $("#bf_pc").value, radius: $("#bf_r").value }); toast(`${r.added} new brownfield sites (${r.found} found)`); await load(); }
    else if (act === "imp") { const r = await api("/api/import", { kind: t.dataset.k, text: $("#imp_text").value }); toast(`${r.added} new sites (${r.found} found)`); await load(); }
    else if (act === "cleardemo") { await api("/api/clear-demo", {}); toast("Demo sites removed"); await load(); }
    else if (act === "resetset") { await api("/api/settings/reset", {}); toast("Defaults restored"); await load(); }
    else if (act === "ext") { e.preventDefault(); openUrl(t.dataset.url); }
    else if (act === "saveovr") {
      const site = { id: drawer.id, ovr: { ...(drawer.site.ovr || {}) } };
      for (const [k, v] of Object.entries(drawer.ovr)) { if (k === "sales_psf" || k === "rent_psf") site[k] = v; else if (Math.abs(v - D.assumptions[k]) > 1e-9) site.ovr[k] = v; else delete site.ovr[k]; }
      drawer.ovr = {}; await api("/api/site", { site }); toast("Saved to site"); await load();
    }
    else if (act === "resetovr") { drawer.ovr = {}; await refreshDrawer(true); }
    else if (act === "ffit") { F.fit = !F.fit; render(); }
    else if (act === "restoredemo") { const r = await api("/api/demo/restore", {}); toast(r.added ? `${r.added} illustrative deals restored` : "Already present"); await load(); }
    else if (act === "saveepc") { await api("/api/settings/epc", { email: $("#epc_email").value.trim(), key: $("#epc_key").value.trim() }); toast("Saved"); await load(); }
    else if (act === "savesite") saveSite();
    else if (act === "delsite") { if (confirm("Delete this site?")) { await api("/api/site/delete", { id: drawer.id }); closeDrawer(); await load(); } }
    else if (act === "constraints") { $("#cres").textContent = "Querying planning.data.gov.uk..."; const r = await api("/api/constraints", { id: drawer.id }); $("#cres").innerHTML = (Object.values(r.hits).map(h => `<div><b>${esc(h.label)}</b>: ${h.entities.map(x => esc(x.name)).join(", ")}</div>`).join("") || "No constraint datasets intersect this point.") + r.errors.map(x => `<div>Could not query ${esc(x)}</div>`).join(""); await load(); }
    else if (act === "createsite") {
      const site = { name: $("#ns_name").value || "New site", postcode: $("#ns_pc").value, address: $("#ns_pc").value, asking_price: +$("#ns_ask").value || null, site_ha: +$("#ns_ha").value || null, existing_sqft: +$("#ns_sq").value || null, strategy: $("#ns_st").value, source: "Manual" };
      const r = await api("/api/site", { site }); closeModal(); await load(); openSite(r.id, "details");
    }
  } catch (err) { toast(err.message); }
});
$("#scrim").onclick = closeDrawer;
document.addEventListener("keydown", e => { if (e.key === "Escape") { closeModal(); closeDrawer(); } if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); $("#q").focus(); } });
$("#q").oninput = e => { F.q = e.target.value; if (view === "settings" || view === "sourcing") { view = "sites"; } render(); };
$("#addBtn").onclick = () => addDeal();
matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", () => D?.theme === "auto" && applyTheme());
