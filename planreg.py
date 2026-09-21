"""Planning register helpers: local authority links, timeline, and a register-based risk read-out."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from urllib.parse import quote

from . import net

STANCE_WEIGHT = {"Object": 3, "Holding objection": 3, "Conditions": 1, "No objection": 0, "Support": -1}
STATUSES = ["Pre-app", "Submitted", "Validated", "Granted", "Refused", "Appeal allowed", "Appeal dismissed", "Withdrawn", "Lapsed"]


def lookup_lpa(site: dict) -> str | None:
    if site.get("la"):
        return site["la"]
    pc = (site.get("postcode") or "").strip()
    if not pc:
        return None
    try:
        js = net.get_json(f"https://api.postcodes.io/postcodes/{quote(pc)}", timeout=8)
        la = (js.get("result") or {}).get("admin_district")
        if la:
            site["la"] = la
        return la
    except Exception:
        return None


def links(site: dict) -> list[dict]:
    """Deep links to official registers. These open the public sites: Minerva does not scrape council portals."""
    la = site.get("la") or ""
    pc = site.get("postcode") or ""
    out = []
    if la:
        out.append({"label": f"{la}: planning applications search", "url": f"https://www.google.com/search?q={quote(la + ' council search planning applications')}", "note": "Opens a search for the council's own register"})
    if site.get("lat") is not None:
        out.append({"label": "Planning data map (national dataset)", "url": f"https://www.planning.data.gov.uk/map/?lat={site['lat']}&lng={site['lon']}&zoom=16", "note": "Conservation areas, listed buildings, Green Belt, tree preservation orders and more"})
    out += [{"label": "Planning Portal: find applications", "url": "https://www.planningportal.co.uk/planning/planning-applications/find-a-planning-application", "note": "National starting point"},
            {"label": "Flood risk for this postcode", "url": f"https://check-long-term-flood-risk.service.gov.uk/postcode?postcode={quote(pc)}" if pc else "https://check-long-term-flood-risk.service.gov.uk/", "note": "Environment Agency"},
            {"label": "MAGIC map (designations)", "url": "https://magic.defra.gov.uk/MagicMap.aspx", "note": "SPA, SSSI, ancient woodland, Green Belt"}]
    return out


def _d(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def timeline(site: dict) -> list[dict]:
    ev = []
    for h in site.get("planning_history", []):
        if _d(h.get("submitted")):
            ev.append({"date": h["submitted"], "event": f"{h['ref']} submitted: {h['description']}", "kind": "app", "docs": []})
        if _d(h.get("decided")):
            ev.append({"date": h["decided"], "event": f"{h['ref']}: {h['status']}", "kind": "decision", "docs": h.get("docs", [])})
    for c in site.get("consultees", []):
        if _d(c.get("date")):
            ev.append({"date": c["date"], "event": f"{c['body']}: {c['stance']}. {c['summary']}", "kind": "consultee", "docs": [c["doc"]] if c.get("doc") else []})
    for k in site.get("key_dates", []):
        if _d(k.get("date")):
            ev.append({"date": k["date"], "event": k["event"], "kind": "key", "docs": []})
    return sorted(ev, key=lambda e: e["date"])


GRANTED = ("Granted", "Approved", "Appeal allowed")


def read_out(site: dict) -> dict:
    """A transparent, rule-based reading of the register (not a prediction). Every point comes from the register entries."""
    apps = site.get("planning_history", [])
    cons = site.get("consultees", [])
    grants = [h for h in apps if h.get("status") in GRANTED and _d(h.get("decided"))]
    grant = max(grants, key=lambda h: _d(h["decided"]), default=None)
    consented = bool(grant) or site.get("planning_status") == "Consented"
    pts, risk, conds = [], (0 if consented else 2), 0
    for c in cons:
        w = STANCE_WEIGHT.get(c.get("stance"), 0)
        if w >= 3:
            if consented:
                pts.append({"level": "Low", "text": f"{c['body']} objected (overcome by the grant): {c['summary']}", "doc": c.get("doc")})
            else:
                pts.append({"level": "High", "text": f"{c['body']} objects: {c['summary']}", "doc": c.get("doc")})
                risk += w
        elif w == 1 or c.get("stance") == "Mixed":
            pts.append({"level": "Medium", "text": f"{c['body']} conditions: {c['summary']}" if not consented else f"Condition to discharge, {c['body']}: {c['summary']}", "doc": c.get("doc")})
            conds += 1
            risk += 0 if consented else 1
    for h in apps:
        if h["status"] in ("Refused", "Appeal dismissed") and not (grant and _d(h.get("decided")) and _d(h["decided"]) < _d(grant["decided"])):
            pts.append({"level": "High", "text": f"{h['ref']} was {h['status'].lower()}: " + "; ".join(h.get("key_points", [])[:2]), "doc": (h.get("docs") or [None])[0]})
            risk += 3
    status = "Consented" if consented else site.get("planning_status", "Unknown")
    expiry = None
    if grant:
        d = _d(grant["decided"])
        expiry = (d.replace(year=d.year + 3) - timedelta(days=1)).isoformat() if not (d.month == 2 and d.day == 29) else (d.replace(year=d.year + 3, day=28) - timedelta(days=1)).isoformat()
    days_left = (_d(expiry) - date.today()).days if expiry else None
    if consented:
        level = "High" if (days_left is not None and days_left < 180) else "Medium" if conds >= 3 or risk >= 3 else "Low"
    else:
        level = "Low" if risk <= 2 else "Medium" if risk <= 5 else "High"
    return {"status": status, "risk": level, "risk_points": risk, "points": sorted(pts, key=lambda p: {"High": 0, "Medium": 1}.get(p["level"], 2)),
            "latest": grant, "permission_expiry": expiry, "expiry_days": days_left, "open_objections": sum(1 for c in cons if STANCE_WEIGHT.get(c.get("stance"), 0) >= 3 and not consented),
            "note": "Rule-based read-out of the register entries. It is a prompt for diligence, not a forecast."}
