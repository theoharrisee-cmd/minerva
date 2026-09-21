"""Development / investment appraisal engine.

One engine, three strategies. Every strategy is reduced to:
    V   net exit value (after sales/purchaser costs)
    C   non-land costs (build, externals, contingency, fees, S106/CIL, sales costs)
    T   months the land is financed
and the residual land value (RLV) is solved so the target profit is met.
"""
from __future__ import annotations

from copy import deepcopy

from .config import DEFAULT_ASSUMPTIONS


def _units(site: dict, a: dict) -> int:
    if site.get("units"):
        return int(site["units"])
    return max(1, int(round(float(site.get("site_ha") or 0) * a["density_dph"])))


def _scheme(site: dict, a: dict, strategy: str) -> dict:
    """Areas, values and non-land costs for the chosen strategy."""
    sales_psf = float(site.get("sales_psf") or a["sales_psf"])
    rent_psf = float(site.get("rent_psf") or a["rent_psf"])
    out = {"strategy": strategy, "sales_psf": sales_psf, "rent_psf": rent_psf}

    if strategy == "value_add":
        gia = float(site.get("existing_sqft") or 0)
        nsa = gia * a["efficiency"]
        units = int(site.get("units") or max(1, round(nsa / a["unit_nsa_sqft"])))
        build = gia * a["refurb_psf"]
        gdv = nsa * sales_psf * (1 + a["uplift_pct"])
        noi = nsa * rent_psf * (1 + a["uplift_pct"]) * (1 - a["void_pct"]) * (1 - a["opex_pct"])
        build_months = max(3.0, min(a["build_months"], 9.0))
        s106 = cil = 0.0
        sale_units = units
    else:
        mix = [m for m in (site.get("unit_mix") or []) if m.get("count")]
        if mix:
            units = int(sum(m["count"] for m in mix))
            nsa = sum(m["count"] * float(m.get("nsa_sqft") or a["unit_nsa_sqft"]) for m in mix)
            mkt_gdv = sum(m["count"] * float(m.get("sale_value") or float(m.get("nsa_sqft") or a["unit_nsa_sqft"]) * sales_psf) for m in mix)
            mkt_rent = sum(m["count"] * (float(m["rent_pcm"]) * 12 if m.get("rent_pcm") else float(m.get("nsa_sqft") or a["unit_nsa_sqft"]) * rent_psf) for m in mix)
        else:
            units = _units(site, a)
            nsa = units * a["unit_nsa_sqft"]
            mkt_gdv, mkt_rent = nsa * sales_psf, nsa * rent_psf
        gia = float(site.get("gia_sqft") or nsa / a["efficiency"])
        build = float(site["build_cost_total"]) if site.get("build_cost_total") else gia * a["build_psf"] * (1 + a["external_pct"])
        s106 = units * a["s106_per_unit"]
        cil = gia * a["cil_psf"]
        build_months = a["build_months"]
        aff = a["affordable_pct"]
        share = (1 - aff) + aff * (1 - a["affordable_disc"])
        gdv = mkt_gdv * share
        gross_rent = mkt_rent * share
        noi = gross_rent * (1 - a["void_pct"]) * (1 - a["opex_pct"])
        sale_units = units

    contingency = build * a["contingency_pct"]
    fees = build * a["fees_pct"]
    cost_ex_sales = build + contingency + fees + s106 + cil

    if strategy == "develop_sell":
        gross_value = gdv
        sales_costs = gdv * (a["marketing_pct"] + a["sales_legal_pct"])
        net_value = gdv - sales_costs
    else:
        # Capital value from income (BTR) or resale (value-add: higher of resale and income value)
        income_value = noi / a["exit_yield"] if a["exit_yield"] > 0 else 0
        gross_value = income_value if strategy == "btr" else max(income_value, gdv)
        sales_costs = gross_value * a["purchaser_costs"] / (1 + a["purchaser_costs"])
        net_value = gross_value - sales_costs

    out.update(
        units=units, nsa=nsa, gia=gia, build=build, contingency=contingency, fees=fees,
        s106=s106, cil=cil, cost_ex_land=cost_ex_sales + (sales_costs if strategy == "develop_sell" else 0),
        cost_ex_land_pre_sales=cost_ex_sales, gdv=gross_value, sales_costs=sales_costs,
        net_value=net_value, noi=noi, build_months=build_months,
    )
    return out


def _finance_factor(a: dict, months_land: float) -> float:
    return 1 + a["acq_costs_pct"] + a["finance_rate"] * months_land / 12


def _build_finance(a: dict, build_cost: float, build_months: float, tail_months: float) -> float:
    r = a["finance_rate"]
    return r * (build_cost * 0.55 * build_months / 12 + build_cost * tail_months / 2 / 12)


def _profit_basis(strategy: str) -> str:
    return "gdv" if strategy == "develop_sell" else "cost"


def _target(strategy: str, a: dict) -> float:
    return {"develop_sell": a["target_profit_gdv"], "btr": a["target_profit_cost_btr"],
            "value_add": a["target_profit_cost_va"]}[strategy]


def appraise(site: dict, assumptions: dict | None = None, strategy: str | None = None,
             land_price: float | None = None) -> dict:
    """Full appraisal. If land_price is None the site's asking price is tested
    (falling back to the residual land value when there is no asking price)."""
    a = {**DEFAULT_ASSUMPTIONS, **(assumptions or {})}
    strategy = strategy or site.get("strategy") or "develop_sell"
    s = _scheme(site, a, strategy)

    tail = a["sales_months"]
    months_land = a["planning_months"] + s["build_months"] + tail
    k = _finance_factor(a, months_land)
    bfin = _build_finance(a, s["cost_ex_land_pre_sales"], s["build_months"], tail)
    C = s["cost_ex_land"]
    p = _target(strategy, a)

    if _profit_basis(strategy) == "gdv":
        rlv = (s["net_value"] - (C - s["sales_costs"]) - bfin - p * s["gdv"]) / k
    else:
        # profit on cost: total cost * (1 + p) = net value
        rlv = (s["net_value"] / (1 + p) - C - bfin) / k
    rlv_raw = rlv
    rlv = max(rlv, 0.0)

    asking = float(site.get("asking_price") or 0)
    tested = land_price if land_price is not None else (asking if asking > 0 else rlv)
    land_cost = tested * (1 + a["acq_costs_pct"])
    land_fin = tested * a["finance_rate"] * months_land / 12
    total_cost = land_cost + land_fin + C + bfin
    # For develop_sell, C already contains sales costs, and net_value is GDV less those
    # costs, so add them back to avoid counting them twice.
    profit = s["net_value"] - total_cost
    if strategy == "develop_sell":
        profit = s["net_value"] - (total_cost - s["sales_costs"])

    profit_on_gdv = profit / s["gdv"] if s["gdv"] else 0.0
    profit_on_cost = profit / total_cost if total_cost else 0.0
    yoc = s["noi"] / total_cost if total_cost else 0.0

    max_bid = rlv
    headroom = (max_bid - asking) / asking if asking > 0 else None
    res = {
        **s, "strategy": strategy, "rlv": rlv, "rlv_raw": rlv_raw, "asking": asking, "tested_land_price": tested,
        "land_cost": land_cost, "land_finance": land_fin, "build_finance": bfin,
        "total_cost": total_cost, "profit": profit, "profit_on_gdv": profit_on_gdv,
        "profit_on_cost": profit_on_cost, "yield_on_cost": yoc,
        "months_land": months_land, "target_profit": p, "profit_basis": _profit_basis(strategy),
        "max_bid": max_bid, "opening_offer": max_bid * (1 - a["offer_discount"]),
        "walk_away": max_bid, "headroom_vs_asking": headroom,
        "viable": profit_on_gdv >= a["target_profit_gdv"] - 1e-9 if strategy == "develop_sell"
        else profit_on_cost >= p - 1e-9,
    }
    missing = []
    if strategy == "value_add" and not site.get("existing_sqft"):
        missing.append("existing floor area (sq ft)")
    elif strategy != "value_add" and not site.get("units") and not site.get("site_ha"):
        missing.append("site area (ha) or unit count")
    if not asking:
        missing.append("asking price")
    res["missing"] = missing
    res["incomplete"] = bool(missing)
    if missing:
        res["viable"] = False
    cf = cashflow(res, a)
    res.update(irr_unlevered=irr(cf["unlevered"]), irr_levered=irr(cf["levered"]),
               equity_multiple=cf["equity_multiple"], peak_equity=cf["peak_equity"], npv_equity=cf["npv_equity"],
               equity_profit=cf["equity_profit"], debt_fee=cf["debt_fee"],
               cashflow=cf["rows"])
    return res


# ---------------------------------------------------------------- cash flow

def _scurve(n: int) -> list[float]:
    """Monthly build spend weights: differences of the cubic S(x) = 3x^2 - 2x^3 (sums to exactly 1)."""
    if n <= 1:
        return [1.0]
    S = lambda x: 3 * x * x - 2 * x ** 3
    return [S((i + 1) / n) - S(i / n) for i in range(n)]


def cashflow(res: dict, a: dict) -> dict:
    pl = int(round(a["planning_months"]))
    bm = int(round(res["build_months"]))
    sm = max(1, int(round(a["sales_months"])))
    n = pl + bm + sm + 1
    flows = [0.0] * n
    build_total = res["cost_ex_land_pre_sales"]
    for i, w in enumerate(_scurve(bm)):
        flows[pl + 1 + i] -= build_total * w
    strat = res["strategy"]
    if strat == "develop_sell":
        for i in range(sm):
            flows[pl + bm + 1 + i] += res["net_value"] / sm
    else:
        flows[n - 1] += res["net_value"]
    flows[0] = -res["land_cost"]  # land price plus acquisition costs at t0
    unlev = flows[:]

    # levered: senior and mezzanine draw pro rata to outflows, interest rolls up, repaid from inflows (senior first)
    tranches = [{"ltc": a["ltc"], "r": a["finance_rate"] / 12, "bal": 0.0}, {"ltc": a.get("mezz_ltc", 0.0), "r": a.get("mezz_rate", 0.13) / 12, "bal": 0.0}]
    fee = a.get("debt_fee_pct", 0.0) * (a["ltc"] + a.get("mezz_ltc", 0.0)) * -sum(x for x in flows if x < 0)
    eq, cum_eq, peak = [], 0.0, 0.0
    for i, f in enumerate(flows):
        for t in tranches:
            t["bal"] *= 1 + t["r"]
        if i == 0:
            f -= fee
        if f < 0:
            e = f
            for t in tranches:
                draw = -f * t["ltc"]
                t["bal"] += draw
                e += draw
        else:
            e = f
            for t in tranches:
                rp = min(t["bal"], e)
                t["bal"] -= rp
                e -= rp
        eq.append(e)
        cum_eq += e
        peak = min(peak, cum_eq)
    rest = sum(t["bal"] for t in tranches)
    if rest > 1e-6:
        eq[-1] -= rest
    invested = -sum(x for x in eq if x < 0)
    returned = sum(x for x in eq if x > 0)
    mr = (1 + a.get("cost_of_equity", 0.12)) ** (1 / 12) - 1
    npv_eq = sum(x / (1 + mr) ** i for i, x in enumerate(eq))
    rows = [{"month": i, "unlevered": u, "levered": e} for i, (u, e) in enumerate(zip(unlev, eq))]
    return {"unlevered": unlev, "levered": eq, "rows": rows, "debt_fee": fee, "npv_equity": npv_eq, "equity_profit": sum(eq),
            "equity_multiple": (returned / invested) if invested else 0.0, "peak_equity": -peak}


def irr(flows: list[float]) -> float | None:
    if not any(f < 0 for f in flows) or not any(f > 0 for f in flows):
        return None

    def npv(r: float) -> float:
        return sum(f / (1 + r) ** i for i, f in enumerate(flows))

    lo, hi = -0.9, 1.0
    if npv(lo) * npv(hi) > 0:
        return None
    for _ in range(120):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    m = (lo + hi) / 2
    return (1 + m) ** 12 - 1


# -------------------------------------------------------------- sensitivity

def sensitivity(site: dict, assumptions: dict, x_key: str, x_steps: list[float],
                y_key: str, y_steps: list[float], metric: str = "profit_on_gdv",
                strategy: str | None = None) -> dict:
    """Two-way table. Steps are relative changes (e.g. -0.1 = 10% lower)."""
    a0 = {**DEFAULT_ASSUMPTIONS, **assumptions}
    # Hold the price paid for the land fixed at the base case, as a real bid would be
    fixed_land = appraise(site, a0, strategy)["tested_land_price"]
    grid = []
    for dy in y_steps:
        row = []
        for dx in x_steps:
            a, st = deepcopy(a0), dict(site)
            for key, d in ((x_key, dx), (y_key, dy)):
                if st.get(key):          # a site-level override wins over the global assumption
                    st[key] = st[key] * (1 + d)
                else:
                    a[key] = a0[key] * (1 + d)
            row.append(appraise(st, a, strategy, land_price=fixed_land)[metric])
        grid.append(row)
    return {"x": x_steps, "y": y_steps, "z": grid}
