"""Deal intake: turn pasted text, an email (.eml) or brochure into a structured deal."""
from __future__ import annotations

import email
from datetime import datetime
import json
import re
import uuid
from email import policy

from . import planning, scrapers
from .config import DEFAULT_MODEL

SCHEMA = """Return ONLY JSON:
{"name": "...", "address": "...", "postcode": "...", "asking_price": number|null, "site_ha": number|null, "existing_sqft": number|null,
 "units": number|null, "strategy": "develop_sell|btr|value_add", "planning_status": "Consented|Allocated|Pre-app|Refused|None|Unknown",
 "tenure": "...", "description": "2 sentence summary", "bid_deadline": "YYYY-MM-DD"|null, "vendor": "...", "marketing": "...",
 "unit_mix": [{"type":"2 bed","count":10,"nsa_sqft":700,"sale_value":350000,"rent_pcm":1500}],
 "build_cost_total": number|null, "gia_sqft": number|null,
 "agent": {"firm":"...","name":"...","role":"...","phone":"...","email":"..."},
 "flags": {"green_belt":false,"conservation_area":false,"listed":false,"contamination":false,"trees":false,"access_issue":false,"flood_zone":null},
 "key_dates": [{"date":"YYYY-MM-DD","event":"..."}], "notes": "risks or open questions worth flagging", "missing": ["what the sender did not say that a developer needs"]}
Use null where the text does not say. Do not invent figures."""
PHONE = re.compile(r"(?:\+44\s?\(0\)\s?|\+44\s?|\(?0)(?:\d[\s()-]?){9,10}\d")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def parse_eml(data: bytes) -> dict:
    msg = email.message_from_bytes(data, policy=policy.default)
    body = msg.get_body(preferencelist=("plain", "html"))
    text = body.get_content() if body else ""
    if body and body.get_content_type() == "text/html":
        text = re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", text))
    atts = []
    for part in msg.iter_attachments():
        fn = part.get_filename()
        if fn:
            atts.append((fn, part.get_payload(decode=True) or b""))
    return {"subject": str(msg["subject"] or ""), "from": str(msg["from"] or ""), "date": str(msg["date"] or ""), "text": text, "attachments": atts}


def heuristic(text: str, subject: str = "", sender: str = "") -> dict:
    full = f"{subject}\n{text}"
    cls = scrapers.classify(full)
    price = None
    m = re.search(r"(?:guide|asking|offers (?:in excess of|over)|price)[^£]{0,25}£\s?([\d,.]+)\s*(m|million)?", full, re.I) or scrapers.PRICE.search(full)
    if m:
        v = float(m.group(1).replace(",", ""))
        price = v * 1_000_000 if (len(m.groups()) > 1 and m.group(2)) else v
    pc = scrapers.FULLPC.search(full.upper())
    units = re.search(r"(\d{2,4})\s*(?:units|apartments|flats|homes|dwellings|houses)", full, re.I)
    ha = re.search(r"([\d.]+)\s*(?:ha\b|hectares?)", full, re.I)
    ac = re.search(r"([\d.]+)\s*acres?", full, re.I)
    sq = re.search(r"([\d,]{4,7})\s*sq\.?\s*ft", full, re.I)
    ph = PHONE.search(full)
    em = [e for e in EMAIL.findall(full) if "noreply" not in e.lower()]
    deadline = re.search(r"(?:bids?|offers?|tender|deadline)[^.\n]{0,60}?(\d{1,2})(?:st|nd|rd|th)? (January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})", full, re.I)
    bid_deadline = None
    if deadline:
        try:
            bid_deadline = datetime.strptime(f"{deadline.group(1)} {deadline.group(2).title()} {deadline.group(3)}", "%d %B %Y").date().isoformat()
        except ValueError:
            pass
    if ha or ac:
        pass
    first = (full.strip().splitlines() or ["New deal"])[0]
    name = subject.strip() or re.split(r"(?<=[a-z0-9])\.\s", first)[0][:70]
    name = re.sub(r"^(re|fwd?):\s*", "", name, flags=re.I)
    sname = re.match(r"\s*\"?([^<\"]+)\"?\s*<", sender or "")
    bc = re.search(r"(?:build|construction) (?:cost|budget)[^£]{0,60}£\s?([\d,.]+)\s*(m\b|million)?|cost plan[^£]{0,40}£\s?([\d,.]+)\s*(m\b|million)?", full, re.I)
    build_total = None
    if bc:
        raw = bc.group(1) or bc.group(3)
        mult = 1_000_000 if (bc.group(2) or bc.group(4)) else 1
        try:
            build_total = float(raw.replace(",", "")) * mult
        except ValueError:
            pass
    gia = re.search(r"([\d,]{4,7})\s*sq\.? ?ft\s*(?:\(?GIA|gross internal)|GIA (?:of )?([\d,]{4,7})", full, re.I)
    mix = [{"type": f"{b} bed", "count": int(n), "nsa_sqft": float(a.replace(",", "")), "sale_value": float(v.replace(",", ""))}
           for n, b, a, v in re.findall(r"(\d+)\s*x\s*(\d) bed[^(\n]{0,25}\((\d[\d,]*)\s*sq\.? ?ft,?\s*(?:c\.?\s*)?£\s?([\d,]+)\)", full, re.I)]
    return {"build_cost_total": build_total, "gia_sqft": float((gia.group(1) or gia.group(2)).replace(",", "")) if gia else None, "unit_mix": mix, "name": name, "address": "", "postcode": f"{pc.group(1)} {pc.group(2)}" if pc else "", "asking_price": price,
            "site_ha": float(ha.group(1)) if ha else round(float(ac.group(1)) * 0.4047, 2) if ac else None,
            "existing_sqft": None if (ha or ac) and units else float(sq.group(1).replace(",", "")) if sq else cls.get("existing_sqft"), "units": (sum(m["count"] for m in mix) if mix else int(units.group(1)) if units else None),
            "strategy": "develop_sell" if ((ha or ac) and (units or re.search(r"\bplots?\b|dwellings|\bland\b", full, re.I))) else cls["strategy"], "planning_status": cls["planning_status"], "description": full.strip()[:400],
            "bid_deadline": bid_deadline, "agent": {"name": sname.group(1).strip() if sname else "", "phone": ph.group(0).strip() if ph else "", "email": (re.search(r"<([^>]+@[^>]+)>", sender or "") or [None, None])[1] or (em[0] if em else "")},
            "flags": {"green_belt": bool(re.search(r"green belt", full, re.I)), "conservation_area": bool(re.search(r"conservation area", full, re.I)),
                      "listed": bool(re.search(r"listed", full, re.I)), "contamination": bool(re.search(r"contaminat", full, re.I)),
                      "flood_zone": "3" if re.search(r"flood zone 3", full, re.I) else "2" if re.search(r"flood zone 2", full, re.I) else None},
            "missing": [x for x, ok in (("asking price", price), ("site area or floor area", ha or ac or sq), ("unit count", units), ("postcode", pc)) if not ok],
            "_engine": "keyword"}


def extract(text: str, api_key: str | None, model: str = DEFAULT_MODEL, subject: str = "", sender: str = "") -> dict:
    if api_key:
        try:
            raw = planning._claude(api_key, model, "You are a UK property acquisitions analyst extracting deal facts from an agent's email or brochure. Be exact.",
                                   [{"role": "user", "content": f"{SCHEMA}\n\nSubject: {subject}\nFrom: {sender}\n\nTEXT:\n{text[:120000]}"}], 3000)
            d = planning._parse_json(raw)
            d["_engine"] = f"claude:{model}"
            return d
        except Exception as e:
            d = heuristic(text, subject, sender)
            d["_engine"] = f"keyword (Claude failed: {str(e)[:80]})"
            return d
    return heuristic(text, subject, sender)


def to_site(d: dict, source: str = "Deal intake") -> dict:
    site = {k: d.get(k) for k in ("name", "address", "postcode", "asking_price", "site_ha", "existing_sqft", "units", "strategy", "planning_status", "tenure",
                                  "description", "bid_deadline", "vendor", "marketing", "unit_mix", "build_cost_total", "gia_sqft", "key_dates", "notes") if d.get(k) not in (None, "", [])}
    site.update(id=f"deal-{uuid.uuid4().hex[:6]}", source=source, deal=True, stage="Screened", listing=False)
    site.setdefault("name", "New deal")
    site.setdefault("strategy", "develop_sell")
    for k, v in (d.get("flags") or {}).items():
        if v:
            site[k] = v
    a = {k: v for k, v in (d.get("agent") or {}).items() if v}
    if a:
        site["agent"] = a
    if d.get("missing"):
        site["intake_missing"] = d["missing"]
    site["intake_engine"] = d.get("_engine")
    g = scrapers.geocode_text(f"{site.get('postcode', '')} {site.get('address', '')} {site['name']}")
    if g:
        site["lat"], site["lon"], site["geo_precision"] = g
    return site
