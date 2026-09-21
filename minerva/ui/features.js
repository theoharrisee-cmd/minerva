/* Minerva v0.3 features: mandate, contacts, planning register, documents, model, market evidence, inbox, deal intake. */
const fileB64 = f => new Promise(res => { const r = new FileReader(); r.onload = () => res({ name: f.name, data: r.result.split(",")[1] }); r.readAsDataURL(f); });
const chipCls = { ok: "ok", "No objection": "ok", Support: "ok", Conditions: "med", Mixed: "med", Object: "hi", "Holding objection": "hi" };
const stCls = s => /Granted|Approved|allowed/i.test(s) ? "ok" : /Refused|dismissed/i.test(s) ? "hi" : /Pending|Submitted|Validated|Pre-app/i.test(s) ? "med" : "";
const fdate = d => { if (!d) return ""; const x = new Date(d); return isNaN(x) ? esc(d) : x.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }); };
const daysTo = d => { const x = new Date(d); return isNaN(x) ? null : Math.round((x - new Date()) / 864e5); };
const tick = ok => ok === true ? '<span class="pos" style="font-weight:700">&#10003;</span>' : ok === false ? '<span class="neg" style="font-weight:700">&#10007;</span>' : '<span class="tsub">&ndash;</span>';
const DOCI = '<svg viewBox="0 0 24 24" style="width:14px;height:14px"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg>';
const docOf = id => drawer?.site?.docs?.find(d => d.id === id);
const docChip = (id, label) => { const d = docOf(id); return d ? `<button class="docchip" data-act="viewdoc" data-doc="${esc(id)}" title="${esc(d.name)}">${DOCI}<span>${esc(label || d.title || d.name.replace(/\.[a-z]+$/i, "").replace(/_/g, " "))}</span></button>` : ""; };
const ext = url => `data-act="ext" data-url="${esc(url)}"`;

function fitChip(f) {
  if (!f || !f.active) return "";
  if (f.label === "Provisional") return '<span class="chip lo" title="Needs price, size and planning data before returns can be tested against your mandate">Provisional</span>';
  const c = f.hard_fail ? "hi" : f.score >= 85 ? "ok" : f.score >= 55 ? "med" : "lo";
  return `<span class="chip ${c}" title="${esc(f.label)}">${f.hard_fail ? "Outside" : f.score == null ? "n/a" : f.label.replace(" fit", "")}${f.score != null && !f.hard_fail ? " " + f.score : ""}</span>`;
}

/* ---------------- overview extras ---------------- */
function tOverviewExtra() {
  const s = drawer.site, e = drawer.ev, c = e.contact || {}, f = e.fit;
  const facts = [["Property type", s.property_type], ["Tenure", s.tenure], ["Existing use", s.existing_use], ["Site area", s.site_ha ? `${s.site_ha} ha` : ""], ["Existing floor area", s.existing_sqft ? `${Math.round(s.existing_sqft).toLocaleString("en-GB")} sq ft` : ""],
    ["Units", s.units], ["Planning", s.planning_status], ["Local authority", s.la], ["Vendor", s.vendor], ["Marketing", s.marketing], ["Bid deadline", s.bid_deadline ? `${fdate(s.bid_deadline)}${daysTo(s.bid_deadline) != null && daysTo(s.bid_deadline) >= 0 ? ` (${daysTo(s.bid_deadline)} days)` : ""}` : ""], ["Utilities", s.utilities], ["Access", s.access]].filter(x => x[1]);
  const phone = c.best_phone, mail = c.best_email;
  const who = c.name ? `${esc(c.name)}${c.role ? `<span class="tsub"> · ${esc(c.role)}</span>` : ""}` : `<span class="tsub">Named contact not published</span>`;
  const mix = s.unit_mix || [];
  return `
  ${f?.active ? `<div class="card" style="margin-top:14px"><div class="h"><h3>Fit with your mandate</h3><span>${fitChip(f)}</span></div>${f.checks.map(k => `<div class="flag" style="display:flex;gap:10px;align-items:baseline"><span style="width:16px">${tick(k.ok)}</span><div><b>${esc(k.name)}</b> ${k.hard ? '<span class="chip lo">hard limit</span>' : ""}<div class="tsub">${esc(k.detail)}</div></div></div>`).join("")}</div>` : ""}
  <div class="two" style="margin-top:14px;align-items:start">
   <div class="card pad"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><h3>Agent</h3>${s.demo_rich ? '<span class="chip lo">fictional contact</span>' : c.enriched ? '<span class="chip ok">from listing</span>' : ""}</div>
     <div style="font-size:15px;font-weight:620">${esc(c.firm || s.source || "Unknown agent")}</div><div style="margin:2px 0 10px">${who}</div>
     <div class="kv">${phone ? `<div>Phone</div><div><a href="tel:${esc(phone.replace(/\s/g, ""))}">${esc(phone)}</a>${!c.phone && c.team_phone ? ` <span class="tsub">(${esc(c.team || "team")})</span>` : !c.phone ? ' <span class="tsub">(firm switchboard)</span>' : ""}</div>` : ""}
      ${mail ? `<div>Email</div><div><a href="mailto:${esc(mail)}">${esc(mail)}</a></div>` : ""}
      ${c.address ? `<div>Office</div><div>${esc(c.address)}</div>` : ""}${c.branch && !c.address ? `<div>Branch</div><div>${esc(c.branch)}</div>` : ""}
      ${!phone && !mail ? `<div>Contact</div><div class="tsub">${esc(c.firm_note || "No number published on the listing. Use the firm's contact page.")}</div>` : ""}</div>
     <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px"><button class="btn sm primary" data-act="enquiry">Draft enquiry</button>
      ${c.firm_page ? `<button class="btn sm" ${ext(c.firm_page)}>${I.link}Contact page</button>` : ""}${s.url ? `<button class="btn sm" ${ext(s.url)}>${I.link}Listing</button>` : ""}
      ${s.url && !s.demo_rich && !c.enriched ? '<button class="btn sm" data-act="findcontact">Find details on listing</button>' : ""}</div></div>
   <div class="card pad"><h3 style="margin-bottom:8px">Property</h3>${facts.length ? `<div class="kv">${facts.map(([k, v]) => `<div>${k}</div><div>${esc(v)}</div>`).join("")}</div>` : '<div class="tsub">No further detail yet. Add it under Details, or add documents.</div>'}
    ${s.description ? `<p class="tsub" style="margin:12px 0 0;color:var(--ink2)">${esc(s.description)}</p>` : ""}${s.notes ? `<div class="notice" style="margin:12px 0 0"><b>Notes.</b> ${esc(s.notes)}</div>` : ""}</div></div>
  <div class="two" style="margin-top:14px;align-items:start">
   <div class="card"><div class="h"><h3>Key dates</h3></div>${(s.key_dates || []).slice().sort((a, b) => a.date.localeCompare(b.date)).map(k => { const d = daysTo(k.date); return `<div class="flag" style="display:flex;justify-content:space-between;gap:10px"><div><b>${esc(k.event)}</b></div><div class="tsub" style="white-space:nowrap">${fdate(k.date)}${d != null ? (d >= 0 ? ` · in ${d}d` : "") : ""}</div></div>`; }).join("") || '<div class="tsub" style="padding:8px 16px 16px">No dates recorded. Add them in the Planning tab.</div>'}</div>
   <div class="card">${mix.length ? `<div class="h"><h3>Unit mix</h3><span class="m">${mix.reduce((n, m) => n + m.count, 0)} units</span></div><table><thead><tr><th>Type</th><th class="num">No.</th><th class="num">Sq ft</th><th class="num">Value</th></tr></thead><tbody>${mix.map(m => `<tr style="cursor:default"><td>${esc(m.type)}</td><td class="num">${m.count}</td><td class="num">${m.nsa_sqft || ""}</td><td class="num">${m.sale_value ? money(m.sale_value) : m.rent_pcm ? "£" + m.rent_pcm + " pcm" : ""}</td></tr>`).join("")}</tbody></table>` : '<div class="h"><h3>Unit mix</h3></div><div class="tsub" style="padding:8px 16px 16px">Not provided. The model uses average unit sizes; add a mix in the Model tab.</div>'}</div></div>`;
}

/* ---------------- model tab ---------------- */
function tModel() {
  const s = drawer.site, e = drawer.ev, a = e.appraisal, mix = s.unit_mix || [];
  const miss = s.intake_missing?.length ? `<div class="notice"><b>To confirm from the source:</b> ${s.intake_missing.map(esc).join(", ")}. The model has used your default assumptions for these.</div>` : "";
  return `${miss}<div class="card pad" style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap"><div><h3>Financial model</h3><div class="tsub" style="max-width:560px">Built from the deal information, your unit mix and your mandate's cost of capital. The Excel file has live formulas: change any input and every number follows.</div></div>
    <div style="display:flex;gap:8px"><button class="btn primary" data-act="savemodel">Download Excel model</button></div></div>
    ${s.intake_engine ? `<div class="tsub" style="margin-top:8px">Deal facts read by: ${esc(s.intake_engine)}</div>` : ""}</div>
  <div class="card pad" style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><h3>Scheme inputs</h3><span class="tsub">Edit, then Save. Everything below recalculates.</span></div>
   <table id="mixT"><thead><tr><th>Unit type</th><th class="num">Count</th><th class="num">Size sq ft</th><th class="num">Sale value £</th><th class="num">Rent £ pcm</th><th></th></tr></thead><tbody>
   ${mix.map((m, i) => mixRow(m, i)).join("")}</tbody></table>
   <div style="display:flex;gap:8px;margin:10px 0 14px"><button class="btn sm" data-act="mixadd">Add unit type</button></div>
   <div class="three"><label class="field"><span>Total build cost £ (blank uses £/sq ft)</span><input type="number" id="m_build" value="${s.build_cost_total ?? ""}"></label>
    <label class="field"><span>GIA sq ft (blank derives from mix)</span><input type="number" id="m_gia" value="${s.gia_sqft ?? ""}"></label>
    <label class="field"><span>Asking price £</span><input type="number" id="m_ask" value="${s.asking_price ?? ""}"></label></div>
   <div style="margin-top:12px"><button class="btn primary sm" data-act="mixsave">Save inputs</button></div></div>
  <div id="apRes">${apResults()}</div>
  ${a && !a.incomplete ? `<div class="card pad" style="margin-top:14px"><h3 style="margin-bottom:10px">Funding</h3><div class="kv"><div>Peak equity</div><div>${money(a.peak_equity)}</div><div>Debt arrangement fee</div><div>${money(a.debt_fee)}</div><div>Senior / mezzanine</div><div>${pct(D.assumptions.ltc, 0)} at ${pct(D.assumptions.finance_rate)} / ${pct(D.assumptions.mezz_ltc, 0)} at ${pct(D.assumptions.mezz_rate)}</div><div>Cost of equity</div><div>${pct(D.assumptions.cost_of_equity)}</div><div>NPV of equity</div><div class="${a.npv_equity >= 0 ? "pos" : "neg"}">${money(a.npv_equity)}</div></div><div class="tsub" style="margin-top:8px">${D.investor?.active ? "Cost of capital comes from My mandate." : "Set your own cost of capital under My mandate."}</div></div>` : ""}`;
}
const mixRow = (m, i) => `<tr style="cursor:default" data-mi="${i}"><td><input type="text" data-mf="type" value="${esc(m.type || "")}"></td><td><input type="number" data-mf="count" value="${m.count ?? ""}"></td><td><input type="number" data-mf="nsa_sqft" value="${m.nsa_sqft ?? ""}"></td><td><input type="number" data-mf="sale_value" value="${m.sale_value ?? ""}"></td><td><input type="number" data-mf="rent_pcm" value="${m.rent_pcm ?? ""}"></td><td><button class="ghost" data-act="mixdel" data-i="${i}">${I.x}</button></td></tr>`;
function readMix() {
  return $$("#mixT tbody tr").map(tr => { const o = {}; $$("[data-mf]", tr).forEach(i => { const k = i.dataset.mf; o[k] = k === "type" ? i.value : (i.value === "" ? null : +i.value); }); return o; }).filter(m => m.type || m.count).map(m => { Object.keys(m).forEach(k => m[k] == null && delete m[k]); return m; });
}

/* ---------------- planning tab ---------------- */
function tPlanning() {
  const p = drawer.ev.planning || {}, ro = p.read_out || {}, s = drawer.site, an = p.analysis;
  const lvl = { High: "hi", Medium: "med", Low: "ok" }[ro.risk] || "";
  const apps = p.apps || [], cons = p.consultees || [];
  const exp = ro.permission_expiry ? `Permission expires ${fdate(ro.permission_expiry)}${ro.expiry_days != null ? ` (${Math.round(ro.expiry_days / 30)} months)` : ""}` : "";
  return `
  <div class="card pad"><div style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap"><div><div class="kl">Planning position</div><div style="display:flex;gap:8px;align-items:center;margin-top:4px"><span style="font-size:20px;font-weight:700">${esc(ro.status || s.planning_status || "Unknown")}</span><span class="chip ${lvl}">${esc(ro.risk || "n/a")} planning risk</span></div>
     ${exp ? `<div class="tsub" style="margin-top:4px">${exp}</div>` : ""}${p.la ? `<div class="tsub">${esc(p.la)}</div>` : ""}</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:flex-start;max-width:520px;justify-content:flex-end">${(p.links || []).map(l => `<button class="btn sm" title="${esc(l.note || "")}" ${ext(l.url)}>${I.link}${esc(l.label)}</button>`).join("")}</div></div>
   ${(ro.points || []).length ? `<div style="margin-top:14px">${ro.points.map(x => `<div class="flag" style="display:flex;gap:10px;align-items:flex-start"><span class="chip ${sevClass(x.level)}" style="margin-top:1px">${x.level}</span><div style="flex:1">${esc(x.text)}</div>${x.doc ? docChip(x.doc, "Source") : ""}</div>`).join("")}<div class="tsub" style="margin-top:8px">${esc(ro.note || "")}</div></div>` : ""}</div>

  <div class="sec"><h3>Application register</h3><button class="btn sm" data-act="appedit" data-i="-1">Add application</button></div>
  ${apps.map((h, i) => `<div class="card pad" style="margin-bottom:10px"><div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start"><div><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><b>${esc(h.ref)}</b><span class="chip ${stCls(h.status)}">${esc(h.status)}</span><span class="tsub">${h.submitted ? "Submitted " + fdate(h.submitted) : ""}${h.decided ? " · Decided " + fdate(h.decided) : ""}</span></div>
     <div style="margin-top:4px">${esc(h.description || "")}</div>${h.lpa ? `<div class="tsub">${esc(h.lpa)}</div>` : ""}</div><div style="display:flex;gap:2px"><button class="ghost" data-act="appedit" data-i="${i}" title="Edit">&#9998;</button><button class="ghost" data-act="appdel" data-i="${i}" title="Remove">${I.x}</button></div></div>
    ${(h.key_points || []).length ? `<ul class="kp">${h.key_points.map(k => `<li>${esc(k)}</li>`).join("")}</ul>` : ""}
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">${(h.docs || []).map(d => docChip(d)).join("") || '<span class="tsub">No documents linked. Add them in Documents.</span>'}</div></div>`).join("") || '<div class="empty card">No applications recorded yet.</div>'}

  <div class="sec"><h3>Consultee matrix</h3><button class="btn sm" data-act="conedit" data-i="-1">Add response</button></div>
  <div class="card tablewrap" style="max-height:none"><table><thead><tr><th>Consultee</th><th>Stance</th><th>Summary</th><th>Date</th><th>Document</th><th></th></tr></thead><tbody>
   ${cons.map((c, i) => `<tr style="cursor:default"><td style="white-space:nowrap"><b>${esc(c.body)}</b></td><td><span class="chip ${chipCls[c.stance] || ""}">${esc(c.stance)}</span></td><td>${esc(c.summary)}</td><td style="white-space:nowrap">${fdate(c.date)}</td><td>${c.doc ? docChip(c.doc, "Open response") : ""}</td><td style="white-space:nowrap"><button class="ghost" data-act="conedit" data-i="${i}">&#9998;</button><button class="ghost" data-act="condel" data-i="${i}">${I.x}</button></td></tr>`).join("") || `<tr style="cursor:default"><td colspan="6"><div class="empty">No consultee responses recorded.</div></td></tr>`}</tbody></table></div>

  <div class="sec"><h3>Timeline</h3><span class="m">${(p.timeline || []).length} events</span></div>
  <div class="card pad"><div class="tl">${(p.timeline || []).map(t => `<div class="tli ${t.kind}"><i></i><div class="tld">${fdate(t.date)}</div><div>${esc(t.event)}${(t.docs || []).map(d => " " + docChip(d, "Doc")).join("")}</div></div>`).join("") || '<div class="tsub">Nothing to show yet.</div>'}</div></div>

  <div class="sec"><h3>Document analysis</h3><span class="m">${an ? `${esc(an._engine)} · ${an.n_docs || ""} documents · ${when(an.analysed)}` : ""}</span></div>
  <div class="card pad" style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap"><div class="tsub" style="max-width:520px">Reads every document in the vault (${(s.docs || []).length}) and links each finding back to its source. ${D.has_key ? "" : "No Claude API key is set, so this is a keyword screen. Add a key in Settings for reasoning, cost signals and programme."}</div>
    <button class="btn primary" data-act="analyse" ${(s.docs || []).length ? "" : "disabled"}>${an ? "Re-analyse documents" : "Analyse documents"}</button></div><div id="pstatus"></div></div>
  ${an ? planResult(an) : ""}`;
}
function planResult(r) {
  const li = (arr, f) => (arr || []).map(f).join("") || '<div class="tsub" style="padding:6px 16px 14px">None identified</div>';
  const src = x => x.source_doc && docOf(x.source_doc) ? `<div style="margin-top:6px">${docChip(x.source_doc)}${x.source_ref && !/\.pdf|\[/.test(x.source_ref) ? ` <span class="tsub">${esc(x.source_ref)}</span>` : ""}</div>` : x.source_ref ? `<div class="tsub" style="margin-top:4px">${esc(x.source_ref)}</div>` : "";
  return `<div class="card pad" style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;gap:16px"><div><p style="margin:0">${esc(r.summary || "")}</p>${r.likelihood_rationale ? `<p class="tsub" style="margin-top:6px">${esc(r.likelihood_rationale)}</p>` : ""}</div>
   ${r.approval_likelihood != null ? `<div style="text-align:right;min-width:110px"><div class="tsub">Approval likelihood</div><div style="font-size:30px;font-weight:700">${r.approval_likelihood}%</div></div>` : ""}</div></div>
  <div class="two" style="align-items:start"><div class="card"><div class="h"><h3>Constraints</h3></div>${li(r.constraints, x => `<div class="flag"><div class="fh"><span class="chip ${sevClass(x.severity)}">${esc(x.severity)}</span>${esc(x.item)}</div><p>${esc(x.note || "")}</p>${src(x)}</div>`)}
   <div class="h"><h3>Policy context</h3></div>${li(r.policy_context, x => `<div class="flag"><div class="fh">${esc(x.policy)} <span class="chip">${esc(x.effect)}</span></div><p>${esc(x.note || "")}</p>${src(x)}</div>`)}</div>
   <div class="card"><div class="h"><h3>Opportunities</h3></div>${li(r.opportunities, x => `<div class="flag"><div class="fh">${esc(x.item)}</div><p>${esc(x.note || "")}</p>${src(x)}</div>`)}
   <div class="h"><h3>Precedent</h3></div>${li(r.precedent, x => `<div class="flag"><div class="fh">${esc(x.ref)}</div><p>${esc(x.outcome || "")}. ${esc(x.relevance || "")}</p>${src(x)}</div>`)}
   <div class="h"><h3>Next steps</h3></div>${li(r.next_steps, x => `<div class="flag"><p style="color:var(--ink)">${esc(x)}</p></div>`)}</div></div>
  <div style="margin:14px 0"><button class="btn primary" data-act="applyplan">Apply findings to site and appraisal</button></div>
  <div class="card pad"><h3>Ask the documents</h3><div class="chat">${drawer.chat.map(m => `<div class="${m.role === "user" ? "msg-u" : "msg-a"}">${m.role === "user" ? esc(m.content) : esc(m.content).replace(/\[doc:([0-9a-f]+)\]/g, (_, id) => docChip(id) || "")}</div>`).join("")}</div>
   <div style="display:flex;gap:8px"><input type="text" id="pq" placeholder="e.g. What did Highways object to, and is it curable?"><button class="btn" data-act="ask">Ask</button></div>${D.has_key ? "" : '<div class="tsub" style="margin-top:6px">Questions need a Claude API key (Settings).</div>'}</div>`;
}

/* ---------------- documents tab ---------------- */
function tDocuments() {
  const s = drawer.site, ds = s.docs || [];
  const by = {}; ds.forEach(d => (by[d.category] ||= []).push(d));
  const cats = D.doc_cats.filter(c => by[c]);
  return `<div class="drop" id="drop"><input type="file" id="pfiles" multiple hidden><b>Drop documents here</b><div class="tsub">Planning documents, brochures, surveys, emails. PDF, text, HTML or .eml. Text is read so they can be searched and analysed.</div></div>
  <div id="pstatus"></div>
  ${cats.map(c => `<div class="sec"><h3>${esc(c)}</h3><span class="m">${by[c].length}</span></div><div class="card list">${by[c].sort((a, b) => (b.date || "").localeCompare(a.date || "")).map(d => `<div class="row" data-act="viewdoc" data-doc="${d.id}">
    <div class="doci">${d.kind === "pdf" ? "PDF" : d.kind === "html" ? "HTML" : "TXT"}</div><div class="grow"><div class="t">${esc(d.title || d.name)}</div><div class="m">${esc(d.name)} · ${d.date ? fdate(d.date) + " · " : ""}${Math.max(1, Math.round(d.size / 1024))} KB · ${d.chars ? "text read" : "no text extracted"}</div></div>
    <select data-catof="${d.id}" style="width:auto" onclick="event.stopPropagation()">${D.doc_cats.map(k => `<option ${k === d.category ? "selected" : ""}>${k}</option>`).join("")}</select>
    <button class="ghost" data-act="deldoc" data-doc="${d.id}" title="Remove">${I.x}</button></div>`).join("")}</div>`).join("") || '<div class="empty">No documents yet.</div>'}`;
}
async function viewDoc(id) {
  const d = docOf(id); if (!d) return;
  const url = `/docs/${encodeURIComponent(drawer.id)}/${d.id}`;
  let body = "";
  if (d.kind === "pdf" || d.kind === "html") body = `<iframe src="${url}" style="width:100%;height:100%;border:0;background:#fff;border-radius:10px"></iframe>`;
  else { const t = await (await fetch(url)).text(); body = `<pre class="docpre">${esc(t)}</pre>`; }
  const wrap = $("#modal"); wrap.innerHTML = `<div class="modal wide"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:10px"><div><h3 style="margin:0">${esc(d.title || d.name)}</h3><div class="tsub">${esc(d.category)}${d.date ? " · " + fdate(d.date) : ""}${d.source === "demo" ? " · fictional document" : ""}</div></div><div style="display:flex;gap:6px"><button class="btn sm" data-act="savedoc" data-doc="${d.id}">Save to Downloads</button><button class="btn sm" data-act="closem">Close</button></div></div><div style="flex:1;min-height:0">${body}</div></div>`;
  wrap.classList.add("on"); wrap.onclick = e => { if (e.target === wrap) closeModal(); };
}

/* ---------------- market tab ---------------- */
let compsCache = {};
function tMarket() {
  const s = drawer.site, r = compsCache[s.id], ev0 = s.comps || [];
  const sm = r?.summary;
  return `<div class="card pad" style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap"><div><h3>Sold price evidence</h3><div class="tsub" style="max-width:560px">Recent sales in the postcode sector from HM Land Registry (Price Paid Data). ${D.epc?.has_key ? "Floor areas come from EPC records so sales convert to £ per sq ft." : "Add an EPC key in Settings to convert sales to £ per sq ft."}</div></div>
    <div style="display:flex;gap:8px;align-items:center"><select id="cmonths" style="width:auto"><option value="12">12 months</option><option value="24" selected>24 months</option><option value="36">36 months</option></select><button class="btn primary" data-act="pullcomps" ${s.postcode ? "" : "disabled"}>Pull sold prices</button></div></div>
   ${s.postcode ? "" : '<div class="notice" style="margin:12px 0 0">Add a postcode in Details first.</div>'}<div id="cstatus"></div></div>
  ${r && !r.error && !r.demo ? `<div class="stat4">${kpi("Sales found", sm.n, `sector ${esc(r.sector)}, ${r.months} months`)}${kpi("New build sales", sm.new_build_n, sm.new_build_median_price ? "median " + money(sm.new_build_median_price) : "")}${kpi("Median £ psf", sm.median_psf ? "£" + Math.round(sm.median_psf) : "n/a", r.epc_note)}${kpi("Flats £ psf", sm.median_psf_flats ? "£" + Math.round(sm.median_psf_flats) : "n/a", "median")}</div>
   <div class="card" style="margin-bottom:14px"><div class="h"><h3>By property type</h3>${sm.median_psf ? `<button class="btn sm primary" data-act="applypsf" data-psf="${Math.round(sm.median_psf_flats && /flat|btr/i.test(D.strategies[drawer.ev.strategy] + " " + (s.property_type || "")) ? sm.median_psf_flats : sm.median_psf)}">Use £${Math.round(sm.median_psf_flats && /flat|btr/i.test(D.strategies[drawer.ev.strategy] + " " + (s.property_type || "")) ? sm.median_psf_flats : sm.median_psf)} psf in appraisal</button>` : ""}</div>
   <table><thead><tr><th>Type</th><th class="num">Sales</th><th class="num">Median</th><th class="num">Range</th><th class="num">Median £ psf</th></tr></thead><tbody>${sm.by_type.map(t => `<tr style="cursor:default"><td>${esc(t.type)}</td><td class="num">${t.count}</td><td class="num">${money(t.median_price)}</td><td class="num">${money(t.min)} to ${money(t.max)}</td><td class="num">${t.median_psf ? "£" + Math.round(t.median_psf) : ""}</td></tr>`).join("")}</tbody></table></div>
   <div class="card tablewrap" style="max-height:420px"><table><thead><tr><th>Address</th><th>Type</th><th>Date</th><th class="num">Price</th><th class="num">Sq ft</th><th class="num">£ psf</th></tr></thead><tbody>${r.sales.slice(0, 200).map(x => `<tr style="cursor:default"><td>${esc([x.saon, x.paon, x.street].filter(Boolean).join(" "))}, ${esc(x.postcode)}${x.new_build ? ' <span class="chip acc">new build</span>' : ""}</td><td>${esc(x.type)}</td><td>${fdate(x.date)}</td><td class="num">${money(x.price)}</td><td class="num">${x.sqft || ""}</td><td class="num">${x.psf ? "£" + x.psf : ""}</td></tr>`).join("")}</tbody></table></div>
   <div class="tsub" style="margin-top:8px">${esc(r.source)}. <a href="#" ${ext(r.links.ppd)}>Open on Land Registry</a> · <a href="#" ${ext(r.links.epc)}>Search EPCs</a></div>` : r?.error ? `<div class="notice">${esc(r.error)}</div>` : s.land_registry ? `<div class="tsub">Last pulled ${fdate(s.land_registry.fetched)} for ${esc(s.land_registry.sector)}: ${s.land_registry.summary.n} sales. Pull again to see them.</div>` : ""}
  ${ev0.length ? `<div class="sec"><h3>Evidence on file</h3><span class="m">${s.demo_rich ? "fictional, for illustration" : "added to this deal"}</span></div><div class="card list">${ev0.map(c => `<div class="row" style="cursor:default"><span class="chip">${esc(c.kind)}</span><div class="grow"><div class="t">${esc(c.address)}</div><div class="m">${esc(c.detail)}</div></div><div style="text-align:right"><b>${esc(c.metric)}</b><div class="tsub">${esc(c.date)}</div></div></div>`).join("")}</div>` : ""}
  <div class="tsub" style="margin-top:12px">Current appraisal uses £${Math.round(s.sales_psf || D.assumptions.sales_psf)} per sq ft ${s.sales_psf ? "(set on this site)" : "(global assumption)"}.</div>`;
}

/* ---------------- tab bindings ---------------- */
function bindFeatureTab() {
  const s = drawer.site;
  if (drawer.tab === "documents" || drawer.tab === "planning") {
    const drop = $("#drop"), inp = $("#pfiles");
    if (drop && inp) {
      drop.onclick = () => inp.click(); inp.onchange = () => uploadDocs([...inp.files]);
      drop.ondragover = e => { e.preventDefault(); drop.classList.add("over"); }; drop.ondragleave = () => drop.classList.remove("over");
      drop.ondrop = e => { e.preventDefault(); drop.classList.remove("over"); uploadDocs([...e.dataTransfer.files]); };
    }
    $$("[data-catof]").forEach(sel => sel.onchange = async () => { await api("/api/docs/update", { id: s.id, doc: sel.dataset.catof, category: sel.value }); await load(); });
    $("#pq")?.addEventListener("keydown", e => e.key === "Enter" && ask());
  }
}
async function uploadDocs(files) {
  if (!files.length) return;
  $("#pstatus").innerHTML = '<div class="notice">Reading documents.</div>';
  try { await api("/api/docs/upload", { id: drawer.id, files: await Promise.all(files.map(fileB64)) }); toast(`${files.length} document${files.length > 1 ? "s" : ""} added`); await load(); } catch (e) { $("#pstatus").innerHTML = `<div class="notice">${esc(e.message)}</div>`; }
}
async function ask() {
  const q = $("#pq").value.trim(); if (!q) return;
  drawer.chat.push({ role: "user", content: q }); paintDrawer(true);
  try { const r = await api("/api/planning/ask", { id: drawer.id, q, history: drawer.chat.slice(0, -1) }); drawer.chat.push({ role: "assistant", content: r.answer }); } catch (e) { drawer.chat.push({ role: "assistant", content: e.message }); }
  paintDrawer(true);
}
async function refreshPlanning(b) { drawer.ev.planning = b; drawer.site = sites().find(x => x.id === drawer.id); await load(); }

function entryModal(kind, i) {
  const p = drawer.ev.planning, s = drawer.site, isApp = kind === "app";
  const cur = i >= 0 ? (isApp ? p.apps[i] : p.consultees[i]) : {};
  const docSel = id => `<select id="e_doc"><option value="">No document</option>${(s.docs || []).map(d => `<option value="${d.id}" ${d.id === id ? "selected" : ""}>${esc(d.title || d.name)}</option>`).join("")}</select>`;
  modal(isApp ? `<h3>${i >= 0 ? "Edit" : "Add"} application</h3><div class="three"><label class="field"><span>Reference</span><input type="text" id="e_ref" value="${esc(cur.ref || "")}"></label><label class="field"><span>Status</span><select id="e_status">${D.plan_statuses.concat(["Approved", "Pending"]).map(x => `<option ${x === cur.status ? "selected" : ""}>${x}</option>`).join("")}</select></label><label class="field"><span>Authority</span><input type="text" id="e_lpa" value="${esc(cur.lpa || p.la || "")}"></label>
    <label class="field"><span>Submitted</span><input type="text" id="e_sub" placeholder="YYYY-MM-DD" value="${esc(cur.submitted || "")}"></label><label class="field"><span>Decided</span><input type="text" id="e_dec" placeholder="YYYY-MM-DD" value="${esc(cur.decided || "")}"></label></div>
    <label class="field" style="margin-top:12px"><span>Description</span><input type="text" id="e_desc" value="${esc(cur.description || "")}"></label>
    <label class="field" style="margin-top:12px"><span>Key points (one per line)</span><textarea id="e_kp" style="font-family:var(--font);min-height:90px">${esc((cur.key_points || []).join("\n"))}</textarea></label>
    <label class="field" style="margin-top:12px"><span>Linked documents</span><select id="e_docs" multiple style="min-height:90px">${(s.docs || []).map(d => `<option value="${d.id}" ${(cur.docs || []).includes(d.id) ? "selected" : ""}>${esc(d.title || d.name)}</option>`).join("")}</select></label>`
  : `<h3>${i >= 0 ? "Edit" : "Add"} consultee response</h3><div class="three"><label class="field"><span>Consultee</span><input type="text" id="e_body" value="${esc(cur.body || "")}" placeholder="Highways"></label><label class="field"><span>Stance</span><select id="e_stance">${["No objection", "Conditions", "Object", "Holding objection", "Mixed", "Support"].map(x => `<option ${x === cur.stance ? "selected" : ""}>${x}</option>`).join("")}</select></label><label class="field"><span>Date</span><input type="text" id="e_date" placeholder="YYYY-MM-DD" value="${esc(cur.date || "")}"></label></div>
    <label class="field" style="margin-top:12px"><span>Summary</span><input type="text" id="e_sum" value="${esc(cur.summary || "")}"></label><label class="field" style="margin-top:12px"><span>Linked document</span>${docSel(cur.doc)}</label>`
  + `<div class="mf"><button class="btn" data-act="closem">Cancel</button><button class="btn primary" data-act="entrysave" data-kind="${kind}" data-i="${i}">Save</button></div>`);
}

/* ---------------- investor ---------------- */
const INV_GROUPS = [
  ["Capital", [["fund_size", "Fund size (£m)"], ["equity_available", "Equity available now (£m)"], ["max_deal_pct_fund", "Max share of fund in one deal (%)"], ["min_ticket", "Minimum equity ticket (£m)"], ["max_ticket", "Maximum equity ticket (£m)"]]],
  ["Deal profile", [["min_deal", "Minimum total deal cost (£m)"], ["max_deal", "Maximum total deal cost (£m)"], ["min_units", "Minimum units"], ["max_units", "Maximum units"], ["max_hold_months", "Longest hold (months)"]]],
  ["Return targets", [["target_irr", "Target levered IRR (%)"], ["target_em", "Target equity multiple (x)"], ["target_profit_gdv", "Target profit on GDV (%)"], ["target_profit_cost", "Target profit on cost (%)"]]],
  ["Cost of capital", [["cost_of_equity", "Cost of equity (%)"], ["senior_rate", "Senior debt rate (%)"], ["senior_ltc", "Senior loan to cost (%)"], ["mezz_rate", "Mezzanine rate (%)"], ["mezz_ltc", "Mezzanine loan to cost (%)"], ["debt_fee_pct", "Arrangement fee (%)"]]],
];
function vInvestor() {
  const p = D.investor, all = sites().filter(s => s.stage !== "Rejected"), inn = all.filter(s => ev(s).fit?.active && !ev(s).fit.hard_fail).length;
  $("#view").innerHTML = `<div class="grid" style="grid-template-columns:minmax(0,2fr) minmax(280px,1fr);align-items:start">
  <div class="grid">
   <div class="card pad"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px"><div><h3>Who is investing</h3><div class="tsub">Used on enquiry drafts and the model.</div></div>
     <label class="tog"><span>Use my mandate</span><button class="switch ${p.active ? "on" : ""}" id="i_active" type="button"></button></label></div>
    <div class="two" style="margin-top:12px"><label class="field"><span>Name</span><input type="text" id="i_name" value="${esc(p.name)}"></label><label class="field"><span>Firm or fund</span><input type="text" id="i_firm" value="${esc(p.firm)}"></label></div></div>
   ${INV_GROUPS.map(([g, fs]) => `<div class="card pad"><h3 style="margin-bottom:12px">${g}</h3><div class="three">${fs.map(([k, l]) => `<label class="field"><span>${l}</span><input type="number" step="any" data-iv="${k}" value="${p[k] ?? ""}"></label>`).join("")}</div></div>`).join("")}
   <div class="card pad"><h3 style="margin-bottom:12px">Appetite</h3>
    <div class="kl">Strategies</div><div class="checks">${Object.entries(D.strategies).map(([k, l]) => `<label><input type="checkbox" data-is="${k}" ${p.strategies.includes(k) ? "checked" : ""}>${esc(l)}</label>`).join("")}</div>
    <div class="kl" style="margin-top:14px">Regions (none selected means all of England)</div><div class="checks">${D.regions.map(r => `<label><input type="checkbox" data-ir="${esc(r)}" ${p.regions.includes(r) ? "checked" : ""}>${esc(r)}</label>`).join("")}</div>
    <div class="two" style="margin-top:14px"><label class="field"><span>Planning risk you will take</span><select id="i_tol">${D.tolerance.map(t => `<option ${p.planning_tolerance === t ? "selected" : ""} value="${t}">${t === "Speculative" ? "Speculative (no consent needed)" : t === "Pre-app" ? "Pre-application or better" : t === "Allocated" ? "Allocated or better" : "Consented only"}</option>`).join("")}</select></label></div>
    <div class="kl" style="margin-top:14px">Exclude sites with</div><div class="checks">${Object.entries(D.excludable).map(([k, l]) => `<label><input type="checkbox" data-ix="${k}" ${p.exclusions.includes(k) ? "checked" : ""}>${esc(l)}</label>`).join("")}</div>
    <label class="field" style="margin-top:14px"><span>Notes</span><textarea id="i_notes" style="font-family:var(--font);min-height:70px">${esc(p.notes)}</textarea></label></div>
  </div>
  <div class="grid" style="position:sticky;top:0">
   <div class="card pad"><h3 style="margin-bottom:8px">How this is used</h3>
    <div class="usage"><b>Scoring.</b> Every site gets a mandate fit score, weighted with planning, viability and the rest.</div>
    <div class="usage"><b>Appraisals.</b> Cost of equity, debt rates, loan to cost and target profit flow into every model.</div>
    <div class="usage"><b>Searches.</b> Refreshing listings drops sites outside your strategies, regions and maximum size.</div>
    <div class="usage"><b>Enquiries.</b> Drafts to agents state who you are and your ticket range.</div>
    <label class="tog" style="margin-top:12px"><span>Filter searches by mandate</span><button class="switch ${p.filter_searches !== false ? "on" : ""}" id="i_filter" type="button"></button></label>
    <label class="tog" style="margin-top:8px"><span>Write cost of capital into assumptions</span><button class="switch on" id="i_apply" type="button"></button></label></div>
   <div class="card pad"><div class="kl">Right now</div><div style="font-size:30px;font-weight:700;margin-top:4px">${p.active ? inn : "n/a"}</div><div class="tsub">${p.active ? `of ${all.length} active sites sit inside your mandate` : "Switch on Use my mandate and save"}</div>
    <button class="btn primary" style="margin-top:14px;width:100%;justify-content:center" data-act="saveinv">Save mandate</button></div>
  </div></div>`;
  $$(".switch[id^=i_]").forEach(b => b.onclick = () => b.classList.toggle("on"));
}
async function saveInvestor() {
  const p = { name: $("#i_name").value, firm: $("#i_firm").value, active: $("#i_active").classList.contains("on"), filter_searches: $("#i_filter").classList.contains("on"), planning_tolerance: $("#i_tol").value, notes: $("#i_notes").value };
  $$("[data-iv]").forEach(i => p[i.dataset.iv] = i.value === "" ? 0 : +i.value);
  p.strategies = $$("[data-is]").filter(i => i.checked).map(i => i.dataset.is); p.regions = $$("[data-ir]").filter(i => i.checked).map(i => i.dataset.ir); p.exclusions = $$("[data-ix]").filter(i => i.checked).map(i => i.dataset.ix);
  await api("/api/investor", { profile: p, apply_finance: $("#i_apply").classList.contains("on") });
  toast(p.active ? "Mandate saved and applied" : "Saved. Mandate is switched off"); await load();
}

/* ---------------- inbox (Outlook) ---------------- */
let INBOX = { msgs: null, demo: true, q: "", dealsOnly: true, err: "", loading: false }, olPoll = null;
async function loadInbox() {
  INBOX.loading = true; INBOX.err = "";
  try { const r = await api("/api/outlook/list", { q: INBOX.q }); INBOX.msgs = r.messages; INBOX.demo = r.demo; } catch (e) { INBOX.err = e.message; INBOX.msgs = INBOX.msgs || []; }
  INBOX.loading = false; if (view === "inbox") vInbox(true);
}
function vInbox(noload) {
  const o = D.outlook || {}, msgs = (INBOX.msgs || []).filter(m => !INBOX.dealsOnly || m.score >= 25);
  if (!noload && INBOX.msgs === null) loadInbox();
  $("#view").innerHTML = `<div class="grid" style="grid-template-columns:minmax(0,2fr) minmax(300px,1fr);align-items:start">
   <div>
    <div class="toolbar"><button class="pill ${INBOX.dealsOnly ? "on" : ""}" data-act="inboxdeals">Likely deals</button><button class="pill ${!INBOX.dealsOnly ? "on" : ""}" data-act="inboxall">All mail</button><span style="flex:1"></span><input type="text" id="inbox_q" placeholder="Search mail" style="width:220px" value="${esc(INBOX.q)}"><button class="btn sm" data-act="inboxrefresh">${INBOX.loading ? "Loading" : "Refresh"}</button></div>
    ${INBOX.demo ? `<div class="notice">You are looking at a <b>demo mailbox</b> of fictional emails. Connect Outlook on the right to read your own.</div>` : ""}${INBOX.err ? `<div class="notice">${esc(INBOX.err)}</div>` : ""}
    <div class="card list">${msgs.map(m => `<div class="row" style="align-items:flex-start;cursor:default"><div class="grow"><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><span class="t" style="white-space:normal">${esc(m.subject)}</span>${m.score >= 25 ? `<span class="chip ok">${m.score >= 60 ? "Likely deal" : "Possible deal"}</span>` : ""}${m.has_attachments ? '<span class="chip lo">attachment</span>' : ""}</div>
       <div class="m" style="white-space:normal;margin-top:2px">${esc(m.from)} · ${fdate(m.date)}</div><div class="m" style="white-space:normal;margin-top:4px;color:var(--ink2)">${esc(m.preview)}</div></div>
       <button class="btn sm primary" data-act="mailimport" data-mid="${esc(m.id)}" data-demo="${m.demo ? 1 : 0}">Build model</button></div>`).join("") || `<div class="empty">${INBOX.msgs === null || INBOX.loading ? "Loading mail" : "No matching mail in the last 30 days."}</div>`}</div>
   </div>
   <div class="grid">
    <div class="card pad"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><h3>Outlook</h3>${o.connected ? '<span class="chip ok">Connected</span>' : o.pending ? '<span class="chip med">Waiting for sign-in</span>' : '<span class="chip lo">Not connected</span>'}</div>
     ${o.connected ? `<div class="tsub" style="margin-bottom:10px">Signed in as ${esc(o.account || "your account")}. Minerva only reads mail. It never sends, moves or deletes.</div><button class="btn sm" data-act="olout">Disconnect</button>`
     : o.device ? `<div class="tsub">Open <a href="#" ${ext(o.device.verification_uri)}>${esc(o.device.verification_uri)}</a> and enter</div><div style="font:700 26px var(--mono);letter-spacing:.12em;margin:8px 0">${esc(o.device.user_code)}</div><div class="tsub">This page updates once you have signed in.</div>`
     : `<label class="field"><span>Application (client) ID</span><input type="text" id="ol_id" value="${esc(o.client_id || "")}" placeholder="00000000-0000-0000-0000-000000000000"></label>
        <label class="field" style="margin-top:8px"><span>Tenant</span><input type="text" id="ol_tenant" value="${esc(o.tenant || "common")}"></label>
        <button class="btn primary" style="margin-top:12px;width:100%;justify-content:center" data-act="olconnect">Connect Outlook</button>`}
     <div id="ol_msg" class="tsub" style="margin-top:8px"></div></div>
    <div class="card pad"><h3 style="margin-bottom:8px">One-off setup</h3><ol class="steps"><li>In Microsoft Entra (portal.azure.com) open <b>App registrations</b> and choose <b>New registration</b>.</li><li>Under <b>Authentication</b>, turn on <b>Allow public client flows</b>.</li><li>Under <b>API permissions</b> add the delegated permissions <b>Mail.Read</b> and <b>User.Read</b>.</li><li>Copy the <b>Application (client) ID</b> here and press Connect. No secret is needed.</li></ol>
     <div class="tsub" style="margin-top:8px">Work accounts may need an administrator to approve the app.</div></div>
    <div class="card pad"><h3 style="margin-bottom:8px">Other ways in</h3><div class="tsub" style="margin-bottom:10px">Use <b>Add deal</b> at the top to paste an email, drop a brochure, or drag an .eml file saved from Outlook.</div><button class="btn sm" data-act="adddeal">Add deal</button></div>
   </div></div>`;
  $("#inbox_q")?.addEventListener("keydown", e => { if (e.key === "Enter") { INBOX.q = e.target.value; loadInbox(); } });
  if (o.pending && !olPoll) olPoll = setInterval(pollOutlook, 4000);
}
async function pollOutlook() {
  try { const st = await api("/api/outlook/poll", {}); D.outlook = st; if (st.error) { clearInterval(olPoll); olPoll = null; toast(st.error); if (view === "inbox") vInbox(true); return; } if (st.connected) { clearInterval(olPoll); olPoll = null; INBOX.msgs = null; toast("Outlook connected"); await load(); } } catch (e) { clearInterval(olPoll); olPoll = null; toast(e.message); }
}

/* ---------------- add deal ---------------- */
let dealFiles = [];
function addDeal() {
  dealFiles = [];
  modal(`<h3>Add a deal</h3><p class="tsub" style="margin-top:-6px">Paste the agent's email, the brochure text or your own notes. Minerva reads the facts, sets up the site and builds the financial model. Anything it cannot find is flagged for you to confirm.</p>
   <textarea id="deal_text" style="min-height:170px;font-family:var(--font)" placeholder="e.g. Land at Ashby Road, Loughborough LE11 3TH. 2.9 ha with outline consent for 64 dwellings. Guide price £3.95m, offers by 23 October 2026..."></textarea>
   <div class="drop" id="deal_drop" style="margin-top:10px;padding:16px"><input type="file" id="deal_in" multiple hidden accept=".pdf,.txt,.html,.htm,.eml,.md"><b>Add brochures, PDFs or an .eml</b><div class="tsub">They are read for facts and kept in the deal's document vault.</div></div><div id="deal_files" class="tsub" style="margin-top:6px"></div>
   <div class="tsub" style="margin-top:8px">${D.has_key ? "Facts are read with Claude." : "No Claude key set, so facts are read with a simpler keyword reader. Add a key in Settings for better extraction."}</div>
   <div class="mf"><button class="btn" data-act="addsite">Add site manually</button><span style="flex:1"></span><button class="btn" data-act="closem">Cancel</button><button class="btn primary" data-act="dealgo">Build model</button></div>`, () => {
    const drop = $("#deal_drop"), inp = $("#deal_in");
    const add = fs => { dealFiles.push(...fs); $("#deal_files").textContent = dealFiles.map(f => f.name).join(", "); };
    drop.onclick = () => inp.click(); inp.onchange = () => add([...inp.files]);
    drop.ondragover = e => { e.preventDefault(); drop.classList.add("over"); }; drop.ondragleave = () => drop.classList.remove("over"); drop.ondrop = e => { e.preventDefault(); drop.classList.remove("over"); add([...e.dataTransfer.files]); };
  });
}
async function dealGo(btn) {
  const text = $("#deal_text").value; if (!text.trim() && !dealFiles.length) return toast("Paste some text or add a file");
  btn.disabled = true; btn.textContent = "Reading";
  try {
    const enc = await Promise.all(dealFiles.map(fileB64)); const eml = enc.find(f => /\.eml$/i.test(f.name));
    const r = await api("/api/deal/intake", { text, files: enc.filter(f => f !== eml), eml: eml?.data });
    closeModal(); await load(); await openSite(r.id, "model");
    toast(r.missing?.length ? `Model built. Please confirm: ${r.missing.join(", ")}` : "Model built");
  } catch (e) { toast(e.message); btn.disabled = false; btn.textContent = "Build model"; }
}

/* ---------------- enquiry ---------------- */
async function enquiry() {
  const d = await api("/api/site/enquiry", { id: drawer.id });
  modal(`<h3>Draft enquiry</h3><label class="field"><span>To</span><input type="text" id="q_to" value="${esc(d.to)}" placeholder="No email published. Use the contact page."></label><label class="field" style="margin-top:10px"><span>Subject</span><input type="text" id="q_sub" value="${esc(d.subject)}"></label>
   <label class="field" style="margin-top:10px"><span>Message</span><textarea id="q_body" style="font-family:var(--font);min-height:280px">${esc(d.body)}</textarea></label>
   ${D.investor?.active ? "" : '<div class="tsub" style="margin-top:6px">Add your details under My mandate to personalise this.</div>'}
   <div class="mf"><button class="btn" data-act="closem">Close</button><button class="btn" data-act="qcopy">Copy</button><button class="btn primary" data-act="qmail">Open in email app</button></div>`);
}

/* ---------------- events ---------------- */
document.addEventListener("click", async e => {
  const t = e.target.closest("[data-act]"); if (!t) return;
  const act = t.dataset.act, i = t.dataset.i != null ? +t.dataset.i : null;
  try {
    if (act === "savedoc" && D.hosted) { download(`/docs/${encodeURIComponent(drawer.id)}/${t.dataset.doc}?dl=1`); toast("Downloading"); }
    else if (act === "savedoc") { const r = await api("/api/docs/save", { id: drawer.id, doc: t.dataset.doc }); toast(`Saved to Downloads: ${r.name}`); }
    else if (act === "viewdoc") { e.stopPropagation(); await viewDoc(t.dataset.doc); }
    else if (act === "deldoc") { e.stopPropagation(); if (confirm("Remove this document from the vault?")) { await api("/api/docs/delete", { id: drawer.id, doc: t.dataset.doc }); await load(); } }
    else if (act === "analyse") { $("#pstatus").innerHTML = '<div class="notice" style="margin-top:12px">Reading documents and analysing. Large reports can take a minute.</div>'; t.disabled = true; await api("/api/planning/analyse", { id: drawer.id }); await load(); toast("Analysis complete"); }
    else if (act === "applyplan") { await api("/api/planning/apply", { id: drawer.id }); toast("Findings applied"); await load(); }
    else if (act === "ask") ask();
    else if (act === "appedit") entryModal("app", i);
    else if (act === "conedit") entryModal("consultee", i);
    else if (act === "appdel" || act === "condel") { if (confirm("Remove this entry?")) { await refreshPlanning(await api("/api/planning/entry", { id: drawer.id, kind: act === "appdel" ? "app" : "consultee", op: "delete", index: i })); } }
    else if (act === "entrysave") {
      const kind = t.dataset.kind; let entry;
      if (kind === "app") entry = { ref: $("#e_ref").value, status: $("#e_status").value, lpa: $("#e_lpa").value, submitted: $("#e_sub").value || null, decided: $("#e_dec").value || null, description: $("#e_desc").value, key_points: $("#e_kp").value, docs: [...$("#e_docs").selectedOptions].map(o => o.value) };
      else entry = { body: $("#e_body").value, stance: $("#e_stance").value, date: $("#e_date").value || null, summary: $("#e_sum").value, doc: $("#e_doc").value || null };
      closeModal(); await refreshPlanning(await api("/api/planning/entry", { id: drawer.id, kind, op: "save", index: i >= 0 ? i : null, entry }));
    }
    else if (act === "mixadd") { const tb = $("#mixT tbody"); tb.insertAdjacentHTML("beforeend", mixRow({ type: "New type", count: 1 }, tb.children.length)); }
    else if (act === "mixdel") { t.closest("tr").remove(); }
    else if (act === "mixsave") {
      const site = { id: drawer.id, unit_mix: readMix(), build_cost_total: $("#m_build").value === "" ? null : +$("#m_build").value, gia_sqft: $("#m_gia").value === "" ? null : +$("#m_gia").value, asking_price: $("#m_ask").value === "" ? null : +$("#m_ask").value };
      if (site.unit_mix.length) site.units = site.unit_mix.reduce((n, m) => n + (m.count || 0), 0);
      await api("/api/site", { site }); toast("Inputs saved"); await load();
    }
    else if (act === "savemodel" && D.hosted) { download(`/download/model/${encodeURIComponent(drawer.id)}.xlsx?strategy=${drawer.ev.strategy}`); toast("Downloading the Excel model"); }
    else if (act === "savemodel") { const r = await api("/api/model/save", { id: drawer.id, strategy: drawer.ev.strategy }); toast(r.path ? `Saved to Downloads: ${r.name}` : "Saved"); }
    else if (act === "pullcomps") {
      $("#cstatus").innerHTML = '<div class="notice" style="margin:12px 0 0">Querying HM Land Registry.</div>'; t.disabled = true;
      const r = await api("/api/comps", { id: drawer.id, months: +$("#cmonths").value }); compsCache[drawer.id] = r; if (r.error) toast("Could not pull sales"); await load();
    }
    else if (act === "applypsf") { await api("/api/comps/apply", { id: drawer.id, psf: +t.dataset.psf }); toast(`£${t.dataset.psf} per sq ft applied`); await load(); }
    else if (act === "enquiry") await enquiry();
    else if (act === "qcopy") { await navigator.clipboard?.writeText(`${$("#q_sub").value}\n\n${$("#q_body").value}`); toast("Copied"); }
    else if (act === "qmail") { const to = $("#q_to").value.trim(); openUrl(`mailto:${to}?subject=${encodeURIComponent($("#q_sub").value)}&body=${encodeURIComponent($("#q_body").value)}`); }
    else if (act === "findcontact") { t.disabled = true; t.textContent = "Looking"; await api("/api/site/contact", { id: drawer.id }); await load(); toast("Contact details updated from the listing where published"); }
    else if (act === "saveinv") await saveInvestor();
    else if (act === "adddeal") addDeal();
    else if (act === "addsite") { closeModal(); addSite(); }
    else if (act === "dealgo") await dealGo(t);
    else if (act === "inboxdeals") { INBOX.dealsOnly = true; vInbox(true); }
    else if (act === "inboxall") { INBOX.dealsOnly = false; vInbox(true); }
    else if (act === "inboxrefresh") { INBOX.q = $("#inbox_q")?.value || ""; loadInbox(); vInbox(true); }
    else if (act === "mailimport") { t.disabled = true; t.textContent = "Reading"; const r = await api("/api/outlook/import", { mid: t.dataset.mid, demo: t.dataset.demo === "1" }); await load(); await openSite(r.id, "model"); toast(r.missing?.length ? `Model built. Please confirm: ${r.missing.join(", ")}` : "Model built from email"); }
    else if (act === "olconnect") {
      $("#ol_msg").textContent = "Contacting Microsoft";
      await api("/api/outlook/configure", { client_id: $("#ol_id").value, tenant: $("#ol_tenant").value });
      D.outlook = await api("/api/outlook/connect", {}); vInbox(true);
    }
    else if (act === "olout") { D.outlook = await api("/api/outlook/disconnect", {}); INBOX.msgs = null; vInbox(); }
  } catch (err) { toast(err.message); if (t.disabled) t.disabled = false; }
});
document.addEventListener("dragover", e => { if ([...(e.dataTransfer?.types || [])].includes("Files") && !e.target.closest(".drop")) e.preventDefault(); });
load();
