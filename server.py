"""Minerva local server: JSON API + static UI. Standard library only."""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from core import comps as comps_mod
from core import contacts, docs, intake, investor as inv, outlook, planreg
from core import planning as plan
from core import scrapers, sources, store
from core.appraisal import appraise, sensitivity
from core.config import (ASSUMPTION_SPEC, DEFAULT_ASSUMPTIONS, DEFAULT_MODEL, DEFAULT_WEIGHTS, STAGES, STRATEGIES)
from core.scoring import red_flags, score_site

PASSWORD = os.environ.get("MINERVA_PASSWORD", "")          # set when hosted: everything sits behind this password
HOSTED = bool(PASSWORD) or bool(os.environ.get("MINERVA_HOSTED"))
SECRET = (os.environ.get("MINERVA_SECRET") or PASSWORD or "local").encode()
COOKIE = "minerva_session"
_fails: dict[str, list[float]] = {}

LOGIN_HTML = """<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Minerva</title>
<style>:root{color-scheme:light dark}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#F5F6F8;color:#0E1319;font:15px -apple-system,BlinkMacSystemFont,'Segoe UI',Inter,sans-serif}
@media(prefers-color-scheme:dark){body{background:#0A0E13;color:#EAF0F6}form{background:#11171E!important;border-color:#1E2731!important}input{background:#0A0E13!important;color:#EAF0F6!important;border-color:#1E2731!important}}
form{background:#fff;border:1px solid #E4E7EC;border-radius:18px;padding:32px;width:min(360px,90vw);box-shadow:0 8px 30px -12px rgba(16,24,40,.18)}
.logo{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#0F766E,#0B4F6C);color:#fff;display:grid;place-items:center;font-weight:700;margin-bottom:16px}
h1{font-size:20px;margin:0 0 4px}p{margin:0 0 18px;color:#6B7686;font-size:13.5px}input{width:100%;box-sizing:border-box;padding:11px 13px;border-radius:11px;border:1px solid #E4E7EC;font:inherit;margin-bottom:12px}
button{width:100%;padding:11px;border:0;border-radius:11px;background:#0F766E;color:#fff;font:inherit;font-weight:600;cursor:pointer}.e{color:#C23A31;font-size:13px;margin-bottom:10px}</style></head>
<body><form method="post" action="/login"><div class="logo">M</div><h1>Minerva</h1><p>Enter your password to continue.</p>__ERR__<input type="password" name="password" placeholder="Password" autofocus required><button>Sign in</button></form></body></html>"""


def _sign(exp: int) -> str:
    import hashlib
    import hmac
    return f"{exp}.{hmac.new(SECRET, str(exp).encode(), hashlib.sha256).hexdigest()}"


def _valid(tok: str) -> bool:
    import hmac
    import time
    try:
        exp, _ = tok.split(".", 1)
        return int(exp) > time.time() and hmac.compare_digest(tok, _sign(int(exp)))
    except Exception:
        return False


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
UI = ROOT / "ui"
LOCK = threading.RLock()

prof = store.load_profile()
STATE = {
    "sites": store.load_sites(),
    "assumptions": {**DEFAULT_ASSUMPTIONS, **prof.get("assumptions", {})},
    "weights": {**DEFAULT_WEIGHTS, **prof.get("weights", {})},
    "model": prof.get("model", DEFAULT_MODEL),
    "api_key": prof.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", ""),
    "scrape": {"max_pages": 2, "opportunities_only": True, "respect_robots": True, "use_snapshot": True, "ua": "",
               "enabled": [s["id"] for s in scrapers.SOURCES], "overrides": {}, **prof.get("scrape", {})},
    "theme": prof.get("theme", "auto"),
    "investor": {**inv.DEFAULT_INVESTOR, **prof.get("investor", {})},
    "epc": {"email": "", "key": "", **prof.get("epc", {})},
}
JOB = scrapers.ScrapeJob()
PLAN_TEXT: dict[str, str] = {}
PLAN_RES: dict[str, dict] = {}


def persist_sites():
    store.save_sites(STATE["sites"])


def persist_profile():
    store.save_profile({"assumptions": STATE["assumptions"], "weights": STATE["weights"], "model": STATE["model"],
                        "api_key": STATE["api_key"], "scrape": STATE["scrape"], "theme": STATE["theme"],
                        "investor": STATE["investor"], "epc": STATE["epc"]})


def site_by_id(sid):
    return next((s for s in STATE["sites"] if s["id"] == sid), None)


def assumptions_for(site, extra=None):
    return {**STATE["assumptions"], **(site.get("ovr") or {}), **(extra or {})}


def evaluate(site, strategy=None, extra=None, full=False):
    strat = strategy or site.get("strategy") or "develop_sell"
    try:
        ap = appraise(site, assumptions_for(site, extra), strat)
    except Exception:  # never let one bad record break the dashboard
        ap = None
    flags = red_flags(site)
    slim = None
    if ap:
        keys = ["units", "nsa", "gia", "gdv", "rlv", "rlv_raw", "asking", "profit", "profit_on_gdv", "profit_on_cost", "yield_on_cost",
                "irr_unlevered", "irr_levered", "equity_multiple", "peak_equity", "max_bid", "opening_offer", "walk_away",
                "headroom_vs_asking", "viable", "incomplete", "missing", "target_profit", "profit_basis", "months_land", "noi",
                "land_cost", "land_finance", "build", "contingency", "fees", "s106", "cil", "build_finance", "sales_costs", "total_cost", "net_value",
                "npv_equity", "equity_profit", "debt_fee"]
        slim = {k: ap.get(k) for k in keys}
        if full:
            slim["cashflow"] = ap["cashflow"]
    fit = inv.mandate_fit(site, {"appraisal": slim, "strategy": strat}, STATE["investor"])
    sc = score_site(site, ap, flags, STATE["weights"], fit)
    return {"appraisal": slim, "flags": flags, "score": sc, "strategy": strat, "fit": fit}


def contact_of(site):
    """Agent details merged with firm-level details, always populated with at least a route to the agent."""
    a = dict(site.get("agent") or {})
    fc = contacts.firm_contact(site)
    a.setdefault("firm", fc.get("firm") or site.get("source"))
    for k, dst in (("team_phone", "team_phone"), ("team_email", "team_email"), ("phone", "firm_phone"), ("email", "firm_email"), ("url", "firm_page"), ("team", "team"), ("note", "firm_note")):
        if fc.get(k) and not a.get(dst):
            a[dst] = fc[k]
    a["listing_url"] = site.get("url")
    a["best_phone"] = a.get("phone") or a.get("team_phone") or a.get("firm_phone")
    a["best_email"] = a.get("email") or a.get("team_email") or a.get("firm_email")
    return a


def public_state():
    rows = []
    for s in STATE["sites"]:
        ev = evaluate(s)
        rows.append({**s, "_ev": ev, "_contact": contact_of(s), "_region": inv.region_of(s), "_ndocs": len(s.get("docs", []))})
    return {
        "sites": rows, "stages": STAGES, "strategies": STRATEGIES,
        "assumptions": STATE["assumptions"], "spec": {k: {"default": v[0], "label": v[1], "group": v[2], "step": v[3]} for k, v in ASSUMPTION_SPEC.items()},
        "weights": STATE["weights"], "model": STATE["model"], "has_key": bool(STATE["api_key"]), "theme": STATE["theme"],
        "scrape": STATE["scrape"], "sources": scrapers.SOURCES, "job": JOB.snapshot(),
        "investor": STATE["investor"], "regions": inv.REGIONS, "excludable": inv.EXCLUDABLE, "tolerance": inv.TOLERANCE,
        "epc": {"email": STATE["epc"]["email"], "has_key": bool(STATE["epc"]["key"])}, "doc_cats": docs.CATS, "plan_statuses": planreg.STATUSES,
        "outlook": outlook.status(), "hosted": HOSTED,
    }


def planning_bundle(s):
    planreg.lookup_lpa(s) if s.get("postcode") and not s.get("la") and s.get("_lpa_tried") is None and not s.get("demo_rich") and s.update(_lpa_tried=True) is None else None
    return {"links": planreg.links(s), "timeline": planreg.timeline(s), "read_out": planreg.read_out(s), "apps": s.get("planning_history", []),
            "consultees": s.get("consultees", []), "analysis": s.get("planning_analysis"), "docs": s.get("docs", []), "la": s.get("la")}


def _decode_files(files):
    return [(f["name"], base64.b64decode(f["data"])) for f in (files or [])]


def create_from_intake(text, subject="", sender="", files=(), source="Deal intake", received=""):
    parts = [text]
    for name, data in files:
        t = docs.extract_text(name, data)
        if t:
            parts.append(f"\n===== ATTACHMENT: {name} =====\n{t}")
    d = intake.extract("\n".join(parts), STATE["api_key"] or None, STATE["model"], subject, sender)
    site = intake.to_site(d, source)
    site["region"] = inv.region_of(site)
    if received:
        site["received"] = received
    STATE["sites"].append(site)
    docs.add(site, f"Email {subject[:60] or 'enquiry'}.txt", f"From: {sender}\nSubject: {subject}\nDate: {received}\n\n{text}".encode(), category="Email", source="email", date=received[:10] or None)
    for name, data in files:
        docs.add(site, name, data, source="email attachment")
    persist_sites()
    return site


def model_bytes(s, strategy=None):
    import tempfile
    try:
        from core import xlmodel
    except ImportError:
        raise RuntimeError("Excel export needs the openpyxl package (pip3 install openpyxl). The DMG includes it.")
    strat = strategy or s.get("strategy") or "develop_sell"
    a = assumptions_for(s)
    ap = appraise(s, a, strat)
    ev = evaluate(s, strat)
    with tempfile.TemporaryDirectory() as td:
        p = str(Path(td) / "m.xlsx")
        xlmodel.build_model(s, a, strat, ap, STATE["investor"] if STATE["investor"].get("active") else None, ev["fit"] if ev["fit"].get("active") else None, p)
        return Path(p).read_bytes()


# ------------------------------------------------------------------ routes

def api(method: str, path: str, q: dict, body: dict):
    with LOCK:
        if method == "GET" and path == "/api/state":
            return public_state()
        if method == "GET" and path == "/api/job":
            return JOB.snapshot()
        if method == "POST" and path == "/api/appraise":
            s = site_by_id(body["id"])
            if not s:
                return {"error": "not found"}, 404
            extra = body.get("assumptions") or {}
            s = {**s, **{k: extra[k] for k in ("sales_psf", "rent_psf") if k in extra}}  # site-level values win in the engine
            strat = body.get("strategy")
            ev = evaluate(s, strat, extra, full=True)
            metric = "profit_on_gdv" if ev["strategy"] == "develop_sell" else "profit_on_cost"
            ykey = "sales_psf" if ev["strategy"] in ("develop_sell", "value_add") else "exit_yield"
            xkey = "build_psf" if ev["strategy"] != "value_add" else "refurb_psf"
            steps = [-0.15, -0.10, -0.05, 0, 0.05, 0.10, 0.15]
            sens = sensitivity(s, assumptions_for(s, extra), xkey, steps, ykey, steps, metric, ev["strategy"])
            ev["sens"] = {**sens, "xkey": xkey, "ykey": ykey, "xlabel": ASSUMPTION_SPEC[xkey][1], "ylabel": ASSUMPTION_SPEC[ykey][1]}
            ev["planning"] = planning_bundle(s)
            ev["contact"] = contact_of(s)
            return ev
        if method == "POST" and path == "/api/site":
            d = body["site"]
            s = site_by_id(d.get("id"))
            if s:
                s.update(d)
            else:
                d["id"] = d.get("id") or f"manual-{uuid.uuid4().hex[:6]}"
                d.setdefault("stage", "Sourced")
                d.setdefault("strategy", "develop_sell")
                if d.get("lat") is None and (d.get("postcode") or d.get("address")):
                    g = scrapers.geocode_text(f"{d.get('postcode','')} {d.get('address','')}")
                    if g:
                        d["lat"], d["lon"], d["geo_precision"] = g
                STATE["sites"].append(d)
                s = d
            if s.get("postcode") and (s.get("lat") is None or body.get("regeocode")):
                g = scrapers.geocode_text(s["postcode"])
                if g:
                    s["lat"], s["lon"], s["geo_precision"] = g
            persist_sites()
            return {"ok": True, "id": s["id"]}
        if method == "POST" and path == "/api/site/delete":
            STATE["sites"] = [s for s in STATE["sites"] if s["id"] != body["id"]]
            persist_sites()
            return {"ok": True}
        if method == "POST" and path == "/api/open":
            import webbrowser
            if str(body.get("url", "")).startswith(("http://", "https://", "mailto:")):
                webbrowser.open(body["url"])
            return {"ok": True}
        if method == "POST" and path == "/api/model/save":
            s = site_by_id(body["id"])
            data = model_bytes(s, body.get("strategy"))
            out = Path(os.environ.get("MINERVA_DOWNLOADS") or (Path.home() / "Downloads"))
            out.mkdir(parents=True, exist_ok=True)
            name = re.sub(r"[^A-Za-z0-9]+", "_", s.get("name", "deal")).strip("_")[:40] + "_model.xlsx"
            p = out / name
            n = 1
            while p.exists():
                p = out / f"{p.stem.rsplit('_v', 1)[0]}_v{n}.xlsx"
                n += 1
            p.write_bytes(data)
            if not os.environ.get("MINERVA_NO_OPEN"):
                import webbrowser
                webbrowser.open(p.as_uri())
            return {"path": str(p), "name": p.name}
        if method == "POST" and path == "/api/clear-demo":
            STATE["sites"] = [s for s in STATE["sites"] if not s.get("demo")]
            persist_sites()
            return {"ok": True}
        if method == "POST" and path == "/api/settings":
            for k in ("assumptions", "weights", "scrape"):
                if k in body:
                    STATE[k].update(body[k])
            for k in ("model", "theme"):
                if k in body:
                    STATE[k] = body[k]
            if "api_key" in body and body["api_key"] is not None:
                STATE["api_key"] = body["api_key"]
            persist_profile()
            return {"ok": True}
        if method == "POST" and path == "/api/settings/reset":
            STATE["assumptions"] = dict(DEFAULT_ASSUMPTIONS)
            STATE["weights"] = dict(DEFAULT_WEIGHTS)
            persist_profile()
            return {"ok": True}
        if method == "POST" and path == "/api/scrape":
            ids = body.get("sources") or STATE["scrape"]["enabled"]
            ok = JOB.start(ids, STATE["sites"], persist_sites, STATE["scrape"], keep=lambda r: inv.search_filter(STATE["investor"], r))
            return {"started": ok}
        if method == "POST" and path == "/api/import":
            try:
                rows = sources.parse_csv(body["text"]) if body["kind"] == "csv" else sources.parse_alert_text(body["text"])
            except Exception as e:
                return {"error": str(e)}, 400
            have = {s["id"] for s in STATE["sites"]}
            new = [r for r in rows if r["id"] not in have]
            STATE["sites"].extend(new)
            persist_sites()
            return {"added": len(new), "found": len(rows)}
        if method == "POST" and path == "/api/brownfield":
            g = scrapers.geocode_text(body["postcode"])
            if not g:
                return {"error": "Could not geocode that postcode"}, 400
            try:
                rows = sources.fetch_brownfield(g[0], g[1], float(body.get("radius", 10)))
            except Exception as e:
                return {"error": f"Open data request failed: {e}"}, 502
            have = {s["id"] for s in STATE["sites"]}
            new = [r for r in rows if r["id"] not in have]
            STATE["sites"].extend(new)
            persist_sites()
            return {"added": len(new), "found": len(rows)}
        if method == "POST" and path == "/api/constraints":
            s = site_by_id(body["id"])
            if not s or s.get("lat") is None:
                return {"error": "Site needs coordinates: add a postcode"}, 400
            res = sources.check_constraints(s["lat"], s["lon"])
            s.update(sources.constraints_to_flags(res))
            persist_sites()
            return res
        if method == "POST" and path == "/api/planning/analyse":
            s = site_by_id(body["id"])
            for name, data in _decode_files(body.get("files")):
                docs.add(s, name, data)
            if not s.get("docs"):
                return {"error": "Add documents to the vault first"}, 400
            text = docs.all_text(s, body.get("doc_ids") or None)
            res = plan.analyse(text, s, STATE["api_key"] or None, STATE["model"])
            res["analysed"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
            res["n_docs"] = len(body.get("doc_ids") or s["docs"])
            s["planning_analysis"] = res
            persist_sites()
            return res
        if method == "POST" and path == "/api/planning/get":
            s = site_by_id(body["id"])
            persist_sites()
            return planning_bundle(s)
        if method == "POST" and path == "/api/planning/apply":
            s = site_by_id(body["id"])
            res = s.get("planning_analysis")
            if not res:
                return {"error": "No analysis yet"}, 400
            plan.apply_to_site(s, res)
            ovr = dict(s.get("ovr") or {})
            cs = res.get("cost_signals") or {}
            if cs.get("affordable_pct"):
                v = float(cs["affordable_pct"])
                ovr["affordable_pct"] = v / 100 if v > 1 else v
            for k in ("s106_per_unit", "cil_psf"):
                if cs.get(k):
                    ovr[k] = float(cs[k])
            ps = res.get("programme_signals") or {}
            if ps.get("months_to_consent"):
                ovr["planning_months"] = float(ps["months_to_consent"])
            s["ovr"] = ovr
            persist_sites()
            return {"ok": True}
        if method == "POST" and path == "/api/planning/ask":
            if not STATE["api_key"]:
                return {"error": "Add an Anthropic API key in Settings to ask questions of the documents"}, 400
            s = site_by_id(body["id"])
            try:
                ans = plan.answer_question(docs.all_text(s), body["q"] + "\n\nCite documents as [doc:ID] using the id in each DOCUMENT header.", STATE["api_key"], STATE["model"], body.get("history"))
            except Exception as e:
                return {"error": str(e)}, 502
            return {"answer": ans}
        if method == "POST" and path == "/api/planning/entry":
            s = site_by_id(body["id"])
            lst = s.setdefault({"app": "planning_history", "consultee": "consultees", "key": "key_dates"}[body["kind"]], [])
            if body["op"] == "delete":
                if 0 <= body["index"] < len(lst):
                    lst.pop(body["index"])
            else:
                e = body["entry"]
                if body["kind"] == "app":
                    e["key_points"] = [x.strip() for x in str(e.get("key_points", "")).split("\n") if x.strip()] if isinstance(e.get("key_points"), str) else e.get("key_points", [])
                    e.setdefault("docs", [])
                if body.get("index") is None:
                    lst.append(e)
                else:
                    lst[body["index"]].update(e)
            persist_sites()
            return planning_bundle(s)
        if method == "POST" and path == "/api/docs/upload":
            s = site_by_id(body["id"])
            added = [docs.add(s, n, d, category=body.get("category") or None) for n, d in _decode_files(body.get("files"))]
            persist_sites()
            return {"added": added}
        if method == "POST" and path == "/api/docs/update":
            s = site_by_id(body["id"])
            for d in s.get("docs", []):
                if d["id"] == body["doc"]:
                    d.update({k: body[k] for k in ("category", "title", "date") if k in body})
            persist_sites()
            return {"ok": True}
        if method == "POST" and path == "/api/docs/save":
            s = site_by_id(body["id"])
            d = next(x for x in s["docs"] if x["id"] == body["doc"])
            out = Path(os.environ.get("MINERVA_DOWNLOADS") or (Path.home() / "Downloads"))
            out.mkdir(parents=True, exist_ok=True)
            p = out / d["name"]
            n = 1
            while p.exists():
                p = out / f"{Path(d['name']).stem}_{n}{Path(d['name']).suffix}"
                n += 1
            p.write_bytes(docs.path_of(s, d).read_bytes())
            if not os.environ.get("MINERVA_NO_OPEN"):
                import webbrowser
                webbrowser.open(p.as_uri())
            return {"path": str(p), "name": p.name}
        if method == "POST" and path == "/api/docs/delete":
            s = site_by_id(body["id"])
            docs.remove(s, body["doc"])
            persist_sites()
            return {"ok": True}
        if method == "POST" and path == "/api/investor":
            p = {**STATE["investor"], **body.get("profile", {})}
            for k, v in inv.DEFAULT_INVESTOR.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    try:
                        p[k] = type(v)(p[k]) if p[k] not in (None, "") else v
                    except (TypeError, ValueError):
                        p[k] = v
            STATE["investor"] = p
            if p.get("active") and body.get("apply_finance", True):
                STATE["assumptions"].update(inv.derived_assumptions(p))
            persist_profile()
            return {"ok": True, "derived": inv.derived_assumptions(p)}
        if method == "POST" and path == "/api/site/contact":
            s = site_by_id(body["id"])
            contacts.enrich(s)
            persist_sites()
            return contact_of(s)
        if method == "POST" and path == "/api/site/enquiry":
            s = site_by_id(body["id"])
            s2 = {**s, "agent": contact_of(s)}
            return contacts.enquiry_draft(s2, STATE["investor"])
        if method == "POST" and path == "/api/deal/intake":
            files = _decode_files(body.get("files"))
            text, subject, sender, received = body.get("text", ""), body.get("subject", ""), body.get("sender", ""), body.get("received", "")
            if body.get("eml"):
                m = intake.parse_eml(base64.b64decode(body["eml"]))
                text, subject, sender, received = m["text"], m["subject"], m["from"], m["date"]
                files = list(files) + m["attachments"]
            if not (text.strip() or files):
                return {"error": "Paste some text or add a file"}, 400
            site = create_from_intake(text, subject, sender, files, body.get("source") or "Deal intake", received)
            return {"id": site["id"], "missing": site.get("intake_missing", []), "engine": site.get("intake_engine")}
        if method == "POST" and path == "/api/comps":
            s = site_by_id(body["id"])
            if s.get("demo_rich"):
                return {"demo": True, "sales": [], "summary": None, "evidence": s.get("comps", []), "message": "Illustrative deal: the evidence below is fictional. Real deals pull HM Land Registry sales."}
            res = comps_mod.fetch(s, int(body.get("months", 24)), STATE["epc"]["email"], STATE["epc"]["key"])
            if "error" not in res:
                s["land_registry"] = {k: res[k] for k in ("sector", "summary", "fetched", "epc_note")}
                persist_sites()
            return res
        if method == "POST" and path == "/api/comps/apply":
            s = site_by_id(body["id"])
            s["sales_psf"] = float(body["psf"])
            persist_sites()
            return {"ok": True}
        if method == "POST" and path == "/api/settings/epc":
            STATE["epc"] = {"email": body.get("email", ""), "key": body.get("key") or STATE["epc"]["key"]}
            persist_profile()
            return {"ok": True}
        if method == "POST" and path == "/api/demo/restore":
            have = {x["id"] for x in STATE["sites"]}
            new = [d for d in store.rich_demo_deals() if d["id"] not in have]
            STATE["sites"] = new + STATE["sites"]
            persist_sites()
            return {"added": len(new)}
        # ---- Outlook
        if method == "POST" and path == "/api/outlook/configure":
            outlook.configure(body.get("client_id", ""), body.get("tenant", "common"))
            return outlook.status()
        if method == "POST" and path == "/api/outlook/connect":
            try:
                return outlook.start_device_flow()
            except Exception as e:
                return {"error": str(e)}, 400
        if method == "POST" and path == "/api/outlook/poll":
            try:
                return outlook.poll_device_flow()
            except Exception as e:
                return {"error": str(e)}, 502
        if method == "POST" and path == "/api/outlook/disconnect":
            outlook.disconnect()
            return outlook.status()
        if method == "POST" and path == "/api/outlook/list":
            st = outlook.status()
            if body.get("demo") or not st["connected"]:
                return {"demo": True, "messages": outlook.demo_list()}
            try:
                return {"demo": False, "messages": outlook.list_messages(int(body.get("days", 30)), 60, body.get("q", ""))}
            except Exception as e:
                return {"error": str(e)}, 502
        if method == "POST" and path == "/api/outlook/import":
            try:
                m = outlook.demo_get(body["mid"]) if body.get("demo") else outlook.get_message(body["mid"])
            except Exception as e:
                return {"error": str(e)}, 502
            site = create_from_intake(m["text"], m["subject"], m["from"], m["attachments"], "Outlook" if not body.get("demo") else "Outlook (demo mailbox)", m["date"])
            site["outlook_id"] = body["mid"]
            if body.get("demo"):
                site["demo"] = True
            persist_sites()
            return {"id": site["id"], "missing": site.get("intake_missing", [])}
    return {"error": "not found"}, 404


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, data: bytes, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _authed(self) -> bool:
        if not PASSWORD:
            return True
        from http.cookies import SimpleCookie
        c = SimpleCookie(self.headers.get("Cookie") or "")
        return COOKIE in c and _valid(c[COOKIE].value)

    def _login(self, u, method):
        import hmac
        import time
        from urllib.parse import parse_qs as pq
        ip = (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[0].strip()
        if method == "GET":
            return self._send(200, LOGIN_HTML.replace("__ERR__", "").encode(), "text/html; charset=utf-8")
        n = int(self.headers.get("Content-Length") or 0)
        pw = (pq(self.rfile.read(n).decode()).get("password") or [""])[0]
        recent = [t for t in _fails.get(ip, []) if t > time.time() - 600]
        if len(recent) >= 8:
            return self._send(429, LOGIN_HTML.replace("__ERR__", '<div class="e">Too many attempts. Try again in a few minutes.</div>').encode(), "text/html; charset=utf-8")
        if hmac.compare_digest(pw.encode(), PASSWORD.encode()):
            tok = _sign(int(time.time()) + 30 * 86400)
            secure = "; Secure" if self.headers.get("X-Forwarded-Proto") == "https" else ""
            self.send_response(303)
            self.send_header("Set-Cookie", f"{COOKIE}={tok}; Path=/; HttpOnly; SameSite=Lax; Max-Age={30 * 86400}{secure}")
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        _fails[ip] = recent + [time.time()]
        time.sleep(1)
        return self._send(401, LOGIN_HTML.replace("__ERR__", '<div class="e">Incorrect password.</div>').encode(), "text/html; charset=utf-8")

    def _handle(self, method):
        u = urlparse(self.path)
        if u.path == "/healthz":
            return self._send(200, b"ok", "text/plain")
        if u.path == "/login":
            return self._login(u, method)
        if u.path == "/logout":
            self.send_response(303)
            self.send_header("Set-Cookie", f"{COOKIE}=; Path=/; Max-Age=0")
            self.send_header("Location", "/login")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if not self._authed():
            if u.path.startswith("/api/"):
                return self._send(401, b'{"error":"Signed out. Reload the page to sign in."}')
            self.send_response(303)
            self.send_header("Location", "/login")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if u.path.startswith("/api/"):
            body = {}
            if method == "POST":
                n = int(self.headers.get("Content-Length") or 0)
                if n:
                    try:
                        body = json.loads(self.rfile.read(n))
                    except Exception:
                        return self._send(400, b'{"error":"bad json"}')
            try:
                res = api(method, u.path, parse_qs(u.query), body)
            except Exception as e:
                res = ({"error": f"{type(e).__name__}: {e}"}, 500)
            code = 200
            if isinstance(res, tuple):
                res, code = res
            return self._send(code, json.dumps(res, default=str).encode())
        if u.path.startswith("/docs/"):
            try:
                _, _, sid, did = u.path.split("/", 3)
                s = site_by_id(sid)
                d = next(x for x in s["docs"] if x["id"] == did.split("/")[0])
                p = docs.path_of(s, d)
                ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
                if p.suffix.lower() in (".eml", ".txt", ".md"):
                    ctype = "text/plain; charset=utf-8"
                self.send_response(200)
                data = p.read_bytes()
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f'{"attachment" if "dl=1" in u.query else "inline"}; filename="{p.name}"')
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                return self._send(404, b"Document not found", "text/plain")
        if u.path.startswith("/download/model/"):
            try:
                sid = u.path.rsplit("/", 1)[1].removesuffix(".xlsx")
                with LOCK:
                    s = site_by_id(sid)
                    data = model_bytes(s, (parse_qs(u.query).get("strategy") or [None])[0])
                fn = re.sub(r"[^A-Za-z0-9]+", "_", s.get("name", "deal"))[:40] + "_model.xlsx"
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f'attachment; filename="{fn}"')
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                return self._send(500, f"Could not build the model: {e}".encode(), "text/plain")
        rel = u.path.lstrip("/") or "index.html"
        f = (UI / rel).resolve()
        if not str(f).startswith(str(UI.resolve())) or not f.is_file():
            f = UI / "index.html"
        ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        self._send(200, f.read_bytes(), ctype + ("; charset=utf-8" if ctype.startswith("text") or "javascript" in ctype else ""))

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


def make_server(port: int = 0, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)
