"""Investor / developer profile: mandate, capital and cost of capital.
It (1) sets finance and return assumptions, (2) scores every site for mandate fit, (3) narrows searches."""
from __future__ import annotations

import re

# Postcode area -> English region (or "Outside England")
_REGIONS = {
    "London": "E EC N NW SE SW W WC BR CR DA EN HA IG KT RM SM TW UB WD",
    "South East": "BN CT GU HP ME MK OX PO RG RH SL SO TN",
    "South West": "BA BH BS DT EX GL PL SN SP TA TQ TR",
    "East of England": "AL CB CM CO IP LU NR PE SG SS",
    "East Midlands": "DE LE LN NG NN",
    "West Midlands": "B CV DY HR ST TF WR WS WV",
    "North West": "BB BL CA CH CW FY L LA M OL PR SK WA WN",
    "Yorkshire and the Humber": "BD DN HD HG HU HX LS S WF YO",
    "North East": "DH DL NE SR TS",
    "Outside England": "CF LD LL NP SA SY AB DD DG EH FK G HS IV KA KW KY ML PA PH TD ZE BT",
}
AREA2REGION = {a: r for r, areas in _REGIONS.items() for a in areas.split()}
REGIONS = [r for r in _REGIONS if r != "Outside England"]
PC_AREA = re.compile(r"\b([A-Z]{1,2})\d[A-Z\d]?\b")

TOLERANCE = ["Consented", "Allocated", "Pre-app", "Speculative"]
_TOL_RANK = {"Consented": 0, "Allocated": 1, "Pre-app": 2, "Refused": 3, "Unknown": 3, "None": 3}
EXCLUDABLE = {"green_belt": "Green Belt", "flood_zone_3": "Flood Zone 3", "listed": "Listed building", "contamination": "Contamination",
              "access_issue": "Access or ransom issue", "conservation_area": "Conservation area"}

DEFAULT_INVESTOR = {
    "name": "", "firm": "", "active": False,
    "fund_size": 0.0, "equity_available": 0.0, "max_deal_pct_fund": 20.0,
    "min_ticket": 0.0, "max_ticket": 0.0, "min_deal": 0.0, "max_deal": 0.0, "min_units": 0, "max_units": 0,
    "strategies": ["develop_sell", "btr", "value_add"], "regions": [], "planning_tolerance": "Speculative",
    "target_irr": 18.0, "target_em": 1.6, "target_profit_gdv": 20.0, "target_profit_cost": 15.0, "cost_of_equity": 12.0,
    "senior_rate": 8.5, "senior_ltc": 60.0, "mezz_rate": 13.0, "mezz_ltc": 0.0, "debt_fee_pct": 1.0, "max_hold_months": 48,
    "exclusions": [], "notes": "", "filter_searches": True,
}


def region_of(site: dict) -> str | None:
    text = f"{site.get('postcode') or ''} {site.get('address') or ''} {site.get('name') or ''}".upper()
    for m in PC_AREA.finditer(text):
        r = AREA2REGION.get(m.group(1))
        if r:
            return r
    return site.get("region")


def derived_assumptions(p: dict) -> dict:
    """Map an investor profile to engine assumptions (percentages become fractions)."""
    return {
        "finance_rate": p["senior_rate"] / 100, "ltc": p["senior_ltc"] / 100, "mezz_rate": p["mezz_rate"] / 100, "mezz_ltc": p["mezz_ltc"] / 100,
        "debt_fee_pct": p["debt_fee_pct"] / 100, "cost_of_equity": p["cost_of_equity"] / 100,
        "target_profit_gdv": p["target_profit_gdv"] / 100, "target_profit_cost_btr": p["target_profit_cost"] / 100,
        "target_profit_cost_va": p["target_profit_cost"] / 100,
    }


def mandate_fit(site: dict, ev: dict, p: dict) -> dict:
    """Checklist of mandate tests. ok True/False, None when the data needed is missing."""
    checks = []
    ap = ev.get("appraisal") if ev else None
    complete = bool(ap and not ap.get("incomplete"))

    def add(name, ok, detail, hard=False):
        checks.append({"name": name, "ok": ok, "detail": detail, "hard": hard})

    if not p.get("active"):
        return {"active": False, "score": None, "label": "No profile", "checks": []}
    strat = ev.get("strategy") if ev else site.get("strategy")
    from .config import STRATEGIES
    sl = STRATEGIES.get(strat, strat)
    add("Strategy", strat in p["strategies"], f"{sl} {'is' if strat in p['strategies'] else 'is not'} in your mandate", True)
    region = region_of(site)
    if p["regions"]:
        add("Region", None if not region else region in p["regions"], f"{region or 'Region unknown'}; mandate: {', '.join(p['regions'])}", bool(region))
    if complete:
        cost = ap["total_cost"] / 1e6
        if p["min_deal"] or p["max_deal"]:
            ok = (not p["min_deal"] or cost >= p["min_deal"]) and (not p["max_deal"] or cost <= p["max_deal"])
            add("Deal size", ok, f"Total cost £{cost:.1f}m vs £{p['min_deal']:.0f}m to £{p['max_deal'] or float('inf'):.0f}m", True)
        eq = ap["peak_equity"] / 1e6
        cap = p["fund_size"] * p["max_deal_pct_fund"] / 100 if p["fund_size"] else None
        lim = [x for x in (p["max_ticket"] or None, cap, p["equity_available"] or None) if x]
        if lim or p["min_ticket"]:
            mx = min(lim) if lim else None
            ok = (mx is None or eq <= mx) and eq >= p["min_ticket"]
            add("Equity ticket", ok, f"Peak equity £{eq:.1f}m" + (f" vs limit £{mx:.1f}m" if mx else "") + (f", minimum £{p['min_ticket']:.1f}m" if p["min_ticket"] else ""))
        if p["min_units"] or p["max_units"]:
            u = ap["units"]
            add("Scale", (not p["min_units"] or u >= p["min_units"]) and (not p["max_units"] or u <= p["max_units"]), f"{u} units")
        irr = ap.get("irr_levered")
        add("Levered IRR", None if irr is None else irr * 100 >= p["target_irr"], f"{'n/a' if irr is None else f'{irr*100:.1f}%'} vs target {p['target_irr']:.1f}%")
        add("Equity multiple", ap["equity_multiple"] >= p["target_em"], f"{ap['equity_multiple']:.2f}x vs target {p['target_em']:.2f}x")
        npv = ap.get("npv_equity")
        if npv is not None:
            add("NPV at cost of equity", npv >= 0, f"£{npv/1e6:.2f}m at {p['cost_of_equity']:.1f}%")
        add("Hold period", ap["months_land"] <= p["max_hold_months"], f"{ap['months_land']:.0f} months vs {p['max_hold_months']} max")
    ps = site.get("planning_status", "Unknown")
    tol = _TOL_RANK.get(p["planning_tolerance"], 3)
    add("Planning risk", _TOL_RANK.get(ps, 3) <= tol or (p["planning_tolerance"] == "Speculative" and ps != "Refused"), f"Status {ps}; you accept up to {p['planning_tolerance']}", ps == "Refused" and p["planning_tolerance"] != "Speculative")
    hit = []
    for k in p["exclusions"]:
        if k == "flood_zone_3":
            if str(site.get("flood_zone", "1")) == "3":
                hit.append(EXCLUDABLE[k])
        elif site.get(k):
            hit.append(EXCLUDABLE[k])
    if p["exclusions"]:
        add("Exclusions", not hit, ("Hits: " + ", ".join(hit)) if hit else "No excluded constraints", True)
    ev_c = [c for c in checks if c["ok"] is not None]
    score = round(100 * sum(1 for c in ev_c if c["ok"]) / len(ev_c)) if ev_c else None
    hard_fail = any(c["ok"] is False and c["hard"] for c in checks)
    label = "Outside mandate" if hard_fail else "Strong fit" if score is not None and score >= 85 else "Partial fit" if score is not None and score >= 55 else "Weak fit"
    if not complete and not hard_fail:
        label = "Provisional"  # only strategy, region, planning and exclusions could be tested
        score = min(score, 60) if score is not None else None
    return {"active": True, "score": score, "label": label, "hard_fail": hard_fail, "checks": checks, "region": region}


def search_filter(p: dict, site: dict) -> bool:
    """Used by the scrapers: keep a listing only if it could plausibly sit in the mandate.
    The asking price is only the land cost, so it can rule a site out at the top end only (land alone above the maximum total deal size)."""
    if not p.get("active") or not p.get("filter_searches", True):
        return True
    price = site.get("asking_price")
    if price and p["max_deal"] and price > p["max_deal"] * 1e6:
        return False
    if p["strategies"] and site.get("strategy") and site["strategy"] not in p["strategies"]:
        return False
    r = region_of(site)
    if p["regions"] and r and r not in p["regions"]:
        return False
    return True
