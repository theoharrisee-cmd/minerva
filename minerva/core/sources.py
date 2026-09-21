"""Open data and manual import helpers (standard library only)."""
from __future__ import annotations

import csv
import io
import math
import re
import uuid

from . import net
from .scrapers import FULLPC, classify, geocode_text, parse_price

PDG = "https://www.planning.data.gov.uk"

CONSTRAINT_DATASETS = {
    "green-belt": ("green_belt", "Green Belt"),
    "flood-risk-zone": ("flood_zone", "Flood risk zone"),
    "conservation-area": ("conservation_area", "Conservation area"),
    "listed-building-outline": ("listed", "Listed building"),
    "tree-preservation-zone": ("trees", "Tree preservation zone"),
    "article-4-direction-area": ("article4", "Article 4 direction"),
    "brownfield-land": ("brownfield", "Brownfield land register"),
}


def check_constraints(lat: float, lon: float) -> dict:
    out: dict = {"hits": {}, "errors": []}
    for ds, (key, label) in CONSTRAINT_DATASETS.items():
        try:
            d = net.get_json(f"{PDG}/entity.json?dataset={ds}&longitude={lon}&latitude={lat}&geometry_relation=intersects&limit=5", timeout=12)
            ents = d.get("entities", [])
            if ents:
                out["hits"][key] = {"label": label, "entities": [{"name": e.get("name") or e.get("reference"), "reference": e.get("reference"),
                                                                   "flood": e.get("flood-risk-level")} for e in ents]}
        except Exception as e:
            out["errors"].append(f"{label}: {e}")
    return out


def constraints_to_flags(result: dict) -> dict:
    flags = {}
    for key, info in result["hits"].items():
        if key == "flood_zone":
            lv = [str(e.get("flood")) for e in info["entities"] if e.get("flood")]
            flags["flood_zone"] = max(lv) if lv else "2"
        elif key != "article4":
            flags[key] = True
    return flags


def fetch_brownfield(lat: float, lon: float, radius_km: float = 10, limit: int = 100) -> list[dict]:
    d = net.get_json(f"{PDG}/entity.json?dataset=brownfield-land&longitude={lon}&latitude={lat}&geometry_relation=intersects&limit={limit}", timeout=20)
    sites = []
    for e in d.get("entities", []):
        m = re.search(r"POINT\s*\(([-\d.]+)\s+([-\d.]+)\)", e.get("point") or "")
        if not m:
            continue
        x, y = float(m.group(1)), float(m.group(2))
        if math.hypot((y - lat) * 111, (x - lon) * 111 * math.cos(math.radians(lat))) > radius_km:
            continue
        sites.append(dict(id=f"bf-{e.get('entity')}", name=e.get("name") or f"Brownfield {e.get('reference')}", address=e.get("address-text") or "",
                          lat=y, lon=x, source="Brownfield register", site_ha=float(e.get("site-area") or e.get("hectares") or 0) or None,
                          units=int(float(e.get("maximum-net-dwellings") or 0)) or None, brownfield=True, planning_status="Allocated",
                          stage="Sourced", strategy="develop_sell"))
    return sites


RM = re.compile(r"rightmove\.co\.uk/(?:properties|property-for-sale/property)[-/](\d+)", re.I)
ZP = re.compile(r"zoopla\.co\.uk/(?:for-sale|to-rent)/details/(\d+)", re.I)


def parse_alert_text(text: str) -> list[dict]:
    """Optional: parse pasted saved-search alert emails you have received."""
    text = re.sub(r"(?s)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"<a [^>]*href=[\"']([^\"']+)[\"'][^>]*>", r"\n\1\n", text)
    text = re.sub(r"<[^>]+>", "\n", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out, seen = [], set()
    for i, line in enumerate(lines):
        m = RM.search(line) or ZP.search(line)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        blob = " | ".join(lines[max(0, i - 6): i + 3])
        src = "Rightmove alert" if RM.search(line) else "Zoopla alert"
        addr = next((w for w in lines[max(0, i - 6): i + 3] if re.search(r"\d|road|street|lane|close|avenue|way", w, re.I) and "£" not in w and "http" not in w), "")
        site = dict(id=f"alert-{m.group(1)}", name=addr[:80] or f"{src} {m.group(1)}", address=addr, asking_price=parse_price(blob), url=line if line.startswith("http") else "",
                    source=src, listing=True, stage="Sourced", **classify(blob))
        pc = FULLPC.search(blob.upper())
        if pc:
            site["postcode"] = f"{pc.group(1)} {pc.group(2)}"
        g = geocode_text(blob)
        if g:
            site["lat"], site["lon"], site["geo_precision"] = g
        out.append(site)
    return out


def parse_csv(text: str) -> list[dict]:
    out = []
    for r in csv.DictReader(io.StringIO(text.lstrip("﻿"))):
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        price = re.sub(r"[^\d.]", "", r.get("price") or r.get("asking_price") or "")
        s = dict(id=r.get("id") or f"csv-{uuid.uuid4().hex[:6]}", name=r.get("name") or r.get("address", ""), address=r.get("address", ""),
                 asking_price=float(price) if price else None, url=r.get("url", ""), source=r.get("source") or "CSV import", stage="Sourced",
                 strategy=r.get("strategy") or "develop_sell", listing=True)
        for k, tgt in (("site_ha", "site_ha"), ("sqft", "existing_sqft"), ("units", "units"), ("lat", "lat"), ("lon", "lon")):
            if r.get(k):
                try:
                    s[tgt] = float(r[k])
                except ValueError:
                    pass
        if s.get("lat") is None:
            g = geocode_text(r.get("postcode", "") + " " + s["address"])
            if g:
                s["lat"], s["lon"], s["geo_precision"] = g
        out.append(s)
    return out


def geocode_query(q: str):
    return geocode_text(q)
