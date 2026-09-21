"""Listing scrapers for the UK's top national estate agents plus bot-tolerant aggregators.

Design rules
* Polite: robots.txt respected, ~1.5s between hits per host, disk cache, identifying User-Agent.
* Honest: every source reports a status (ok / blocked / js / empty / error) and the reason.
* Resilient: one generic extractor (JSON-LD first, then link-anchored card parsing) driven by a
  small per-source config that can be edited in Settings, plus a bundled snapshot fallback.
* Terms: most portals restrict automated collection in their terms of use. This is an MVP for
  personal research on public pages; check each site's terms before commercial use.
"""
from __future__ import annotations

import html as htmllib
import json
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from . import net, store

# link: regex whose FIRST group is the listing id; verified: URL and structure observed on 21 Sep 2026.
SOURCES: list[dict] = [
    dict(id="jacksonstops", name="Jackson-Stops", kind="agent", rank=1, base="https://www.jackson-stops.co.uk",
         urls=["https://www.jackson-stops.co.uk/properties/for-sale?propertyType=land"], link=r"/properties/(\d+)/sales/", page="page", verified=True),
    dict(id="hamptons", name="Hamptons", kind="agent", rank=2, base="https://www.hamptons.co.uk",
         urls=["https://www.hamptons.co.uk/properties/sales/land"], link=r"/properties/(\d+)/sales/", page="page", verified=True),
    dict(id="foxtons", name="Foxtons", kind="agent", rank=3, base="https://www.foxtons.co.uk",
         urls=["https://www.foxtons.co.uk/properties-for-sale/london"], link=r"/properties-for-sale/[a-z0-9]{2,5}/([a-z]{2,5}\d+)", page="page", verified=True),
    dict(id="chestertons", name="Chestertons", kind="agent", rank=4, base="https://www.chestertons.co.uk",
         urls=["https://www.chestertons.co.uk/properties/sales"], link=r"/properties/(\d+)/sales/", page="page", verified=True),
    dict(id="struttandparker", name="Strutt & Parker", kind="agent", rank=5, base="https://www.struttandparker.com",
         urls=["https://www.struttandparker.com/properties"], link=r"/properties/([a-z0-9]+(?:-[a-z0-9]+)+)", page="page", verified=True),
    dict(id="savills", name="Savills", kind="agent", rank=6, base="https://search.savills.com",
         urls=["https://search.savills.com/gb/en/list/commercial/property-for-sale/development-land/uk"], link=r"/property-detail/([a-z0-9-]+)", page="page", verified=False,
         note="Returned HTTP 403 (bot protection) in testing"),
    dict(id="knightfrank", name="Knight Frank", kind="agent", rank=7, base="https://www.knightfrank.co.uk",
         urls=["https://www.knightfrank.co.uk/properties/for-sale/land-and-development/uk"], link=r"/properties/[a-z-]+/for-sale/[a-z0-9-]+/([a-z0-9-]+)", page="page", verified=False,
         note="Renders in the browser with JavaScript in testing"),
    dict(id="carterjonas", name="Carter Jonas", kind="agent", rank=8, base="https://www.carterjonas.co.uk",
         urls=["https://www.carterjonas.co.uk/property-search?searchtype=sales&propertytype=land"], link=r"/property-search/([a-z0-9-]+)", page="page", verified=False,
         note="Search results not present in static HTML in testing"),
    dict(id="winkworth", name="Winkworth", kind="agent", rank=9, base="https://www.winkworth.co.uk",
         urls=["https://www.winkworth.co.uk/property-for-sale"], link=r"/(?:property|properties)/(?:sales/)?(\d+)", page="page", verified=False,
         note="Search URL needs confirming"),
    dict(id="fineandcountry", name="Fine & Country", kind="agent", rank=10, base="https://www.fineandcountry.co.uk",
         urls=["https://www.fineandcountry.co.uk/property-for-sale"], link=r"/property/(\d+)", page="page", verified=False,
         note="Search URL needs confirming"),
    # Aggregators that served static, unprotected pages when tested
    dict(id="landsale", name="LandSale", kind="aggregator", rank=11, base="https://www.landsale.co.uk", land_only=True,
         urls=["https://www.landsale.co.uk/development/london", "https://www.landsale.co.uk/england"], link=r"/properties/(\d+)", page="page", verified=True),
    dict(id="onthemarket", name="OnTheMarket (land)", kind="aggregator", rank=12, base="https://www.onthemarket.com", land_only=True,
         urls=["https://www.onthemarket.com/for-sale/land/uk/"], link=r"/details/(\d+)/", page="page", verified=True,
         note="Terms of use restrict automated collection; robots.txt is respected"),
]

OPPORTUNITY = re.compile(r"\b(land|plot|plots|site|development|redevelopment|conversion|barn|acre|acres|hectare|paddock|"
                         r"planning|consent|permission|block of|investment|freehold|commercial|care home|hotel|warehouse|"
                         r"church|pub|school|garage|yard|depot|potential|refurbishment)\b", re.I)
PRICE = re.compile(r"£\s?([\d]{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(m\b|million)?", re.I)
RENT = re.compile(r"\b(pcm|pw|per (month|week)|p/?m\b|pcw)\b", re.I)
FULLPC = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})\b")
OUTCODE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?)\b")
SQFT = re.compile(r"([\d,]{3,7})\s*sq\.?\s*ft", re.I)
ACRES = re.compile(r"([\d.]+)\s*acres?", re.I)
HECT = re.compile(r"([\d.]+)\s*hectares?|([\d.]+)\s*ha\b", re.I)
BEDS = re.compile(r"(\d+)\s*bed", re.I)


# ------------------------------------------------------------------ parsing

def _text_lines(fragment: str) -> list[str]:
    fragment = re.sub(r"(?is)<(script|style|svg|noscript).*?</\1>", " ", fragment)
    fragment = re.sub(r"(?i)</?(div|p|li|br|h\d|span|a|section|article|ul|td|tr)[^>]*>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    out = []
    for ln in htmllib.unescape(fragment).splitlines():
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln:
            out.append(ln)
    return out


def parse_price(text: str) -> float | None:
    m = PRICE.search(text)
    if not m:
        return None
    raw = m.group(1).replace(",", "")
    v = float(raw)
    if m.group(2):
        v *= 1_000_000
    return v if v >= 1000 else None


def classify(text: str) -> dict:
    low = text.lower()
    out: dict = {}
    if re.search(r"\b(land|plot|plots|paddock|acre|acres|hectare|site)\b", low) and not re.search(r"\b(\d+ bed)", low):
        out["property_type"], out["strategy"] = "Land", "develop_sell"
    elif re.search(r"block of|investment|commercial|hotel|care home|warehouse|office|pub\b|church|school|garage|depot|yard|barn|conversion|freehold|refurb", low):
        out["property_type"], out["strategy"] = "Investment / conversion", "value_add"
    else:
        out["property_type"], out["strategy"] = "Residential", "value_add"
    if re.search(r"\bconsented\b|(full|outline|detailed) planning|planning (permission|consent) (has been )?(granted|approved|secured|obtained|for)|with planning|consent granted|approved for|benefit of planning", low):
        out["planning_status"] = "Consented"
    elif re.search(r"subject to planning|potential for|development potential|stpp|stp\b", low):
        out["planning_status"] = "None"
    else:
        out["planning_status"] = "Unknown"
    m = SQFT.search(text)
    if m:
        out["existing_sqft"] = float(m.group(1).replace(",", ""))
    m = ACRES.search(text)
    if m:
        out["site_ha"] = round(float(m.group(1)) * 0.4047, 2)
    else:
        m = HECT.search(text)
        if m:
            out["site_ha"] = float(m.group(1) or m.group(2))
    m = BEDS.search(text)
    if m:
        out["bedrooms"] = int(m.group(1))
    return out


def _jsonld(html: str) -> list[dict]:
    items = []
    for blk in re.findall(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html):
        try:
            data = json.loads(blk.strip())
        except Exception:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                if "itemListElement" in d:
                    stack.append(d["itemListElement"])
                if d.get("@type") in ("Product", "RealEstateListing", "House", "Apartment", "SingleFamilyResidence", "Residence", "Place", "ListItem", "Offer") or "offers" in d:
                    items.append(d)
                if "item" in d:
                    stack.append(d["item"])
    return items


def extract(html: str, src: dict) -> list[dict]:
    link_re = re.compile(src["link"], re.I)
    base = src["base"]
    listings: dict[str, dict] = {}

    # 1. JSON-LD (best quality when present)
    for it in _jsonld(html):
        url = it.get("url") or (it.get("item") or {}).get("url") or ""
        m = link_re.search(url)
        if not m:
            continue
        offers = it.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = None
        try:
            price = float(str(offers.get("price", "")).replace(",", "")) or None
        except Exception:
            pass
        addr = it.get("address") or {}
        astr = ", ".join(str(addr.get(k)) for k in ("streetAddress", "addressLocality", "postalCode") if isinstance(addr, dict) and addr.get(k)) if addr else ""
        geo = it.get("geo") or {}
        listings[m.group(1)] = dict(source_id=m.group(1), url=urljoin(base, url), name=it.get("name") or astr,
                                    address=astr or it.get("name", ""), asking_price=price,
                                    lat=_f(geo.get("latitude")), lon=_f(geo.get("longitude")), _text=json.dumps(it)[:1500])

    # 2. Link-anchored cards
    hits = []
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html):
        lm = link_re.search(m.group(1))
        if lm:
            hits.append((max(0, html.rfind("<", 0, m.start())), lm.group(1), m.group(1)))
    firsts: dict[str, tuple[int, str]] = {}
    for pos, lid, href in hits:
        firsts.setdefault(lid, (pos, href))
    order = sorted((pos, lid, href) for lid, (pos, href) in firsts.items())
    for i, (pos, lid, href) in enumerate(order):
        end = order[i + 1][0] if i + 1 < len(order) else pos + 2500
        chunk = html[pos:min(end, pos + 4500)]
        # stop at the next link to any other listing-like page (for example a lettings card)
        other = re.search(r'href=["\'][^"\']*/(?:properties|property|details)/[^"\']*["\']', chunk[60:])
        if other:
            chunk = chunk[:60 + other.start()]
        lines = _text_lines(chunk)
        text = " | ".join(lines)
        if not parse_price(text):
            pre = _text_lines(html[max(0, pos - 500):pos])
            text_pre = " | ".join(pre[-6:])
            if parse_price(text_pre):
                text = text_pre + " | " + text
        rec = listings.get(lid, dict(source_id=lid, lat=None, lon=None))
        rec.setdefault("url", urljoin(base, href))
        rec["_text"] = (rec.get("_text") or "") + " " + text
        pm = PRICE.search(text)
        rec["is_rent"] = bool(pm and RENT.search(text[pm.end():pm.end() + 30]))
        if not rec.get("asking_price"):
            rec["asking_price"] = parse_price(text)
        if not rec.get("name"):
            cands = [l for l in lines if 5 <= len(l) <= 110 and "£" not in l and not re.match(r"^(new|reduced|save|sold|let|featured|view|\d+ ?(bed|bath|sq))", l, re.I)]
            addr = next((l for l in cands if "," in l or FULLPC.search(l)), cands[0] if cands else "")
            rec["name"] = addr
            rec["address"] = addr
        listings[lid] = rec
    return list(listings.values())


def _f(x):
    try:
        return float(x)
    except Exception:
        return None


# --------------------------------------------------------------- geocoding

_GEO_FILE = store.DATA / "geo.json"
_geo: dict = {}
try:
    _geo = json.loads(_GEO_FILE.read_text())
except Exception:
    pass


def geocode_text(text: str) -> tuple[float, float, str] | None:
    """Full postcode, then outcode, via postcodes.io (cached). Returns lat, lon, precision."""
    m = FULLPC.search(text.upper())
    keys = []
    if m:
        keys.append(("postcodes", f"{m.group(1)}{m.group(2)}"))
        keys.append(("outcodes", m.group(1)))
    else:
        for o in OUTCODE.findall(text.upper()):
            if re.match(r"^[A-Z]{1,2}\d", o):
                keys.append(("outcodes", o))
                break
    for kind, k in keys:
        if k in _geo:
            v = _geo[k]
            if v:
                return v[0], v[1], kind
            continue
        try:
            r = net.get_json(f"https://api.postcodes.io/{kind}/{k}", timeout=6)["result"]
            _geo[k] = [r["latitude"], r["longitude"]]
            _GEO_FILE.write_text(json.dumps(_geo))
            return r["latitude"], r["longitude"], kind
        except Exception:
            _geo[k] = None
    return None


# ----------------------------------------------------------------- running

def _pagify(url: str, param: str, n: int) -> str:
    if n <= 1:
        return url
    return url + ("&" if "?" in url else "?") + f"{param}={n}"


def scrape_source(src: dict, *, max_pages: int = 2, opportunities_only: bool = True, ua: str | None = None,
                  respect_robots: bool = True, progress=None) -> dict:
    """Returns {status, message, listings}. Never raises."""
    found: dict[str, dict] = {}
    status, message = "ok", ""
    js_hint = False
    for base_url in src["urls"]:
        for n in range(1, max_pages + 1):
            try:
                html = net.fetch(_pagify(base_url, src.get("page", "page"), n), ua=ua or net.DEFAULT_UA, respect_robots=respect_robots)
            except net.Blocked as e:
                status, message = ("robots" if "robots" in str(e) else "blocked"), str(e)
                break
            except Exception as e:
                status = "error"
                message = ("Could not reach the site: check your internet connection" if "URLError" in type(e).__name__ or "Tunnel" in str(e) or "timed out" in str(e)
                           else f"{type(e).__name__}: {e}")
                break
            got = extract(html, src)
            if not got:
                if re.search(r"__NEXT_DATA__|<app-root|id=\"root\"|id=\"__nuxt\"", html):
                    js_hint = True
                break
            new = 0
            for rec in got:
                if rec["source_id"] not in found:
                    found[rec["source_id"]] = rec
                    new += 1
            if new == 0:
                break
        if status in ("blocked", "robots"):
            break
    if not found and status == "ok":
        status, message = ("js", "Results load with JavaScript, which this build does not run") if js_hint else ("empty", "No listings recognised on the page: the layout may have changed")
    listings = []
    for rec in found.values():
        text = (rec.get("_text") or "") + " " + (rec.get("name") or "")
        if rec.get("is_rent") or "/lettings/" in (rec.get("url") or ""):
            continue
        cls = classify(text)
        if opportunities_only and not src.get("land_only") and not OPPORTUNITY.search(text):
            continue
        site = dict(id=f"{src['id']}-{rec['source_id']}", name=(rec.get("name") or f"{src['name']} listing")[:90], address=rec.get("address") or rec.get("name") or "",
                    url=rec["url"], source=src["name"], source_id=src["id"], asking_price=rec.get("asking_price"), listing=True,
                    stage="Sourced", last_seen=datetime.now(timezone.utc).isoformat(timespec="minutes"), **cls)
        if src.get("land_only"):
            site["property_type"], site["strategy"] = "Land", "develop_sell"
        if rec.get("lat") is not None and rec.get("lon") is not None:
            site["lat"], site["lon"] = rec["lat"], rec["lon"]
        else:
            g = geocode_text(site["address"] + " " + text)
            if g:
                site["lat"], site["lon"], site["geo_precision"] = g
        m = FULLPC.search((site["address"] + " " + text).upper())
        if m:
            site["postcode"] = f"{m.group(1)} {m.group(2)}"
        listings.append(site)
    if status == "ok":
        message = f"{len(listings)} listings"
    return {"status": status, "message": message, "listings": listings}


def load_snapshot() -> list[dict]:
    p = Path(__file__).with_name("snapshot.json")
    try:
        rows = json.loads(p.read_text())
    except Exception:
        return []
    for r in rows:
        r.update(snapshot=True, listing=True, stage=r.get("stage", "Sourced"))
    return rows


# ------------------------------------------------------------ job manager

class ScrapeJob:
    def __init__(self):
        self.lock = threading.Lock()
        self.state = {"running": False, "started": None, "finished": None, "sources": {}, "added": 0, "updated": 0}

    def snapshot(self) -> dict:
        with self.lock:
            return json.loads(json.dumps(self.state))

    def start(self, source_ids: list[str], sites_ref: list[dict], persist, cfg: dict, keep=None) -> bool:
        with self.lock:
            if self.state["running"]:
                return False
            self.state = {"running": True, "started": time.time(), "finished": None, "added": 0, "updated": 0,
                          "sources": {sid: {"status": "queued", "message": ""} for sid in source_ids}}
        threading.Thread(target=self._run, args=(source_ids, sites_ref, persist, cfg, keep), daemon=True).start()
        return True

    def _run(self, ids, sites, persist, cfg, keep=None):
        srcs = {s["id"]: {**s, **(cfg.get("overrides", {}).get(s["id"], {}))} for s in SOURCES}
        snap = load_snapshot() if cfg.get("use_snapshot", True) else []
        for sid in ids:
            src = srcs.get(sid)
            if not src:
                continue
            with self.lock:
                self.state["sources"][sid] = {"status": "running", "message": ""}
            res = scrape_source(src, max_pages=cfg.get("max_pages", 2), opportunities_only=cfg.get("opportunities_only", True),
                                ua=cfg.get("ua") or None, respect_robots=cfg.get("respect_robots", True))
            rows = res["listings"]
            if not rows and snap:
                rows = [r for r in snap if r.get("source_id") == sid]
                if rows:
                    res["message"] += f" Showing {len(rows)} snapshot listings from 21 Sep 2026."
                    res["fallback"] = True
            added = updated = 0
            index = {s["id"]: s for s in sites}
            for r in rows:
                cur = index.get(r["id"])
                if cur:
                    for k, v in r.items():
                        if k in ("stage", "strategy", "ovr", "notes"):
                            continue
                        if v not in (None, ""):
                            cur[k] = v
                    updated += 1
                elif keep is None or keep(r):
                    sites.append(r)
                    added += 1
            persist()
            with self.lock:
                self.state["sources"][sid] = {"status": res["status"], "message": res["message"], "count": len(rows),
                                              "fallback": bool(res.get("fallback"))}
                self.state["added"] += added
                self.state["updated"] += updated
        with self.lock:
            self.state["running"] = False
            self.state["finished"] = time.time()
