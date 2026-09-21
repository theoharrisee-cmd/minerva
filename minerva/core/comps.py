"""Sold-price and floor-area evidence from open data.

* HM Land Registry Price Paid Data (SPARQL endpoint, no key needed): what nearby properties actually sold for.
* EPC Open Data Communities (free key, optional): floor area, so a sale can be turned into GBP per sq ft.

Everything degrades gracefully: with no network or no key the caller gets a clear message, never a crash."""
from __future__ import annotations

import base64
import re
import statistics
from datetime import date, timedelta
from urllib.parse import quote, urlencode

from . import net

SPARQL = "https://landregistry.data.gov.uk/landregistry/query"
EPC_API = "https://epc.opendatacommunities.org/api/v1/domestic/search"
TYPES = {"detached": "Detached", "semi-detached": "Semi-detached", "terraced": "Terraced", "flat-maisonette": "Flat / maisonette", "otherPropertyType": "Other"}
SQM_TO_SQFT = 10.7639


def sector(postcode: str) -> str | None:
    """'RG40 3QT' -> 'RG40 3' (postcode sector)."""
    m = re.match(r"\s*([A-Za-z]{1,2}\d[A-Za-z\d]?)\s*(\d)[A-Za-z]{2}\s*$", postcode or "")
    return f"{m.group(1).upper()} {m.group(2)}" if m else None


def query_for(sec: str, since: str, limit: int = 300) -> str:
    return f"""PREFIX lrppi: <http://landregistry.data.gov.uk/def/ppi/>
PREFIX lrcommon: <http://landregistry.data.gov.uk/def/common/>
SELECT ?paon ?saon ?street ?town ?postcode ?amount ?date ?type ?newbuild ?estate
WHERE {{
  ?t lrppi:pricePaid ?amount ; lrppi:transactionDate ?date ; lrppi:propertyAddress ?a ;
     lrppi:propertyType ?type ; lrppi:newBuild ?newbuild ; lrppi:estateType ?estate .
  ?a lrcommon:postcode ?postcode .
  OPTIONAL {{ ?a lrcommon:paon ?paon }} OPTIONAL {{ ?a lrcommon:saon ?saon }}
  OPTIONAL {{ ?a lrcommon:street ?street }} OPTIONAL {{ ?a lrcommon:town ?town }}
  FILTER (STRSTARTS(?postcode, "{sec}") && ?date >= "{since}"^^<http://www.w3.org/2001/XMLSchema#date>)
}} ORDER BY DESC(?date) LIMIT {limit}"""


def parse_sparql(js: dict) -> list[dict]:
    out = []
    for b in js.get("results", {}).get("bindings", []):
        g = lambda k: (b.get(k) or {}).get("value", "")
        typ = g("type").rsplit("/", 1)[-1]
        est = g("estate").rsplit("/", 1)[-1]
        out.append({"paon": g("paon"), "saon": g("saon"), "street": g("street").title(), "town": g("town").title(), "postcode": g("postcode"),
                    "price": float(g("amount") or 0), "date": g("date")[:10], "type": TYPES.get(typ, typ),
                    "new_build": g("newbuild").lower() == "true", "tenure": "Freehold" if est == "freehold" else "Leasehold" if est == "leasehold" else est})
    return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def epc_areas(postcode_sector_pcs: list[str], email: str, key: str) -> dict:
    """Map normalised 'number street postcode' -> floor area sq ft using the EPC API (Basic auth)."""
    tok = base64.b64encode(f"{email}:{key}".encode()).decode()
    out = {}
    for pc in postcode_sector_pcs[:12]:
        try:
            js = net.api_get(f"{EPC_API}?{urlencode({'postcode': pc, 'size': 200})}", {"Authorization": f"Basic {tok}"}, cache_ttl=7 * 86400)
        except Exception:
            continue
        for row in js.get("rows", []) if isinstance(js, dict) else []:
            try:
                area = float(row.get("total-floor-area") or 0) * SQM_TO_SQFT
            except ValueError:
                continue
            if area:
                out[_norm(f"{row.get('address1','')}{row.get('address2','')}{row.get('postcode','')}")] = area
                out[_norm(f"{row.get('address','')}{row.get('postcode','')}")] = area
    return out


def attach_areas(sales: list[dict], areas: dict) -> int:
    n = 0
    for s in sales:
        for cand in (f"{s['saon']} {s['paon']} {s['street']}", f"{s['paon']} {s['street']}", f"{s['saon']}, {s['paon']} {s['street']}"):
            a = areas.get(_norm(cand + s["postcode"]))
            if a:
                s["sqft"] = round(a)
                s["psf"] = round(s["price"] / a)
                n += 1
                break
    return n


def summarise(sales: list[dict]) -> dict:
    by = {}
    for s in sales:
        by.setdefault(s["type"], []).append(s)
    rows = []
    for t, xs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        prices = [x["price"] for x in xs]
        psf = [x["psf"] for x in xs if x.get("psf")]
        rows.append({"type": t, "count": len(xs), "median_price": statistics.median(prices), "min": min(prices), "max": max(prices),
                     "median_psf": statistics.median(psf) if psf else None, "psf_n": len(psf)})
    newb = [s for s in sales if s["new_build"]]
    allpsf = [s["psf"] for s in sales if s.get("psf")]
    flats_psf = [s["psf"] for s in sales if s.get("psf") and s["type"].startswith("Flat")]
    return {"by_type": rows, "n": len(sales), "new_build_n": len(newb),
            "median_psf": statistics.median(allpsf) if allpsf else None, "median_psf_flats": statistics.median(flats_psf) if flats_psf else None,
            "new_build_median_price": statistics.median([s["price"] for s in newb]) if newb else None}


def fetch(site: dict, months: int = 24, epc_email: str = "", epc_key: str = "") -> dict:
    sec = sector(site.get("postcode", ""))
    if not sec:
        return {"error": "Add a full postcode to this site to pull comparables"}
    since = (date.today() - timedelta(days=30 * months)).isoformat()
    url = f"{SPARQL}?{urlencode({'query': query_for(sec, since)})}"
    try:
        js = net.api_get(url, {"Accept": "application/sparql-results+json"}, timeout=45, cache_ttl=24 * 3600)
    except Exception as e:
        return {"error": f"Could not reach HM Land Registry open data ({str(e)[:120]}). Check your connection and try again.", "sector": sec}
    sales = parse_sparql(js)
    epc_note = "Add a free EPC Open Data key in Settings to convert sales to £ per sq ft."
    matched = 0
    if epc_email and epc_key and sales:
        areas = epc_areas(sorted({s["postcode"] for s in sales}), epc_email, epc_key)
        matched = attach_areas(sales, areas)
        epc_note = f"Floor area matched from EPC for {matched} of {len(sales)} sales."
    return {"sector": sec, "months": months, "sales": sales, "summary": summarise(sales), "epc_note": epc_note, "epc_matched": matched,
            "source": "HM Land Registry Price Paid Data (Open Government Licence)", "fetched": date.today().isoformat(),
            "links": {"ppd": f"https://landregistry.data.gov.uk/app/ppd?{urlencode({'postcode': site.get('postcode','')})}",
                      "epc": f"https://find-energy-certificate.service.gov.uk/find-a-certificate/search-by-postcode?postcode={quote(site.get('postcode',''))}"}}
