"""Red flag engine and site scorecard: the 'developer's eye' on each site."""
from __future__ import annotations

from .config import DEFAULT_WEIGHTS

SEV_POINTS = {"High": 35, "Medium": 15, "Low": 5}


def red_flags(site: dict) -> list[dict]:
    f: list[dict] = []

    def add(sev, title, why, mitigation):
        f.append({"severity": sev, "flag": title, "why": why, "mitigation": mitigation})

    if site.get("green_belt"):
        add("High", "Green Belt", "Inappropriate development needs very special circumstances; NPPF grey belt and previously developed land tests may help.",
            "Check grey belt / PDL status, local plan review status, and promote through the plan rather than a speculative application.")
    z = str(site.get("flood_zone", "1"))
    if z == "3":
        add("High", "Flood Zone 3", "Sequential and exception tests apply; insurability and mortgageability are at risk.",
            "Commission an FRA; test raised levels, sustainable drainage and safe escape routes.")
    elif z == "2":
        add("Medium", "Flood Zone 2", "Sequential test likely required; may push up build cost and affect values.", "Commission an FRA early.")
    if site.get("conservation_area"):
        add("Medium", "Conservation area", "Design scrutiny and Article 4 style restrictions; slower determination.", "Pre-application with the conservation officer; heritage statement.")
    if site.get("listed"):
        add("Medium", "Listed building or setting", "Listed building consent needed; harm to significance must be justified.", "Heritage consultant; sensitive re-use options.")
    if site.get("contamination"):
        add("Medium", "Contamination risk", "Remediation cost can be large and uncertain; conditions will apply.", "Phase 1 and 2 surveys; price remediation into the bid or seek retention.")
    if site.get("trees"):
        add("Low", "Protected trees / ecology", "Reduces developable area; Biodiversity Net Gain (10%) applies.", "Arboricultural and ecology surveys; budget for off-site BNG units.")
    if site.get("access_issue"):
        add("High", "Access or ransom strip", "Site may be landlocked or reliant on third party land, giving a third party hold-up value.", "Legal title review; secure access rights before exchange.")
    ps = site.get("planning_status", "None")
    if ps == "Refused":
        add("High", "Previous refusal", "Reasons for refusal must be overcome; appeals add 9 to 18 months.", "Read the decision notice and officer report; assess whether reasons are curable.")
    elif ps in ("None", "Unknown"):
        add("Medium", "No planning position", "Value is speculative until a consent or allocation exists.", "Pre-application advice; consider a subject-to-planning option.")
    if float(site.get("s106_risk", 0) or 0) > 0.5:
        add("Medium", "Heavy S106 / CIL expectation", "Obligations could erode land value.", "Ask the council for indicative heads of terms; stress test in the appraisal.")
    return f


def score_site(site: dict, appraisal: dict | None, flags: list[dict], weights: dict | None = None, fit: dict | None = None) -> dict:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    tot_w = sum(w.values()) or 1

    plan_map = {"Consented": 95, "Allocated": 80, "Pre-app": 60, "Refused": 25, "None": 35, "Unknown": 35}
    planning = plan_map.get(site.get("planning_status", "Unknown"), 35)
    if site.get("brownfield"):
        planning = min(100, planning + 8)

    constraints = max(0, 100 - sum(SEV_POINTS[x["severity"]] for x in flags))

    viability = 40
    if appraisal and not appraisal.get("incomplete"):
        h = appraisal.get("headroom_vs_asking")
        if h is not None:
            viability = max(0, min(100, 50 + h * 100))
        else:
            viability = max(0, min(100, 50 + appraisal["profit_on_cost"] * 200))

    units = appraisal["units"] if appraisal else 0
    scale = 30 if units < 10 else 60 if units < 30 else 90 if units < 300 else 75

    psf = float(site.get("sales_psf") or 0)
    market = max(0, min(100, (psf - 250) / 4)) if psf else 50

    parts = {"planning": planning, "constraints": constraints, "viability": viability,
             "scale": scale, "market": market}
    if fit and fit.get("active") and fit.get("score") is not None:
        parts["mandate"] = fit["score"]
        if fit.get("hard_fail"):
            parts["mandate"] = min(parts["mandate"], 20)
    else:
        w = {k: v for k, v in w.items() if k != "mandate"}
        tot_w = sum(w.values()) or 1
    total = sum(parts[k] * w[k] for k in parts) / tot_w
    grade = "A" if total >= 75 else "B" if total >= 60 else "C" if total >= 45 else "D"
    if appraisal is None or appraisal.get("incomplete"):
        grade = "N"  # not enough data to grade
    return {"score": round(total), "grade": grade, "parts": {k: round(v) for k, v in parts.items()}}
