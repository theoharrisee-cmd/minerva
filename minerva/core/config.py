"""Default assumptions, strategies and scoring weights. Everything here is
editable from the Settings tab and can be saved/loaded as a JSON profile."""

STRATEGIES = {
    "develop_sell": "Ground-up development (sell)",
    "btr": "Build-to-rent / multifamily",
    "value_add": "Value-add acquisition",
}

STAGES = ["Sourced", "Screened", "Appraised", "Offer", "Acquired", "Rejected"]

# Each assumption: (default, label, group, step)
ASSUMPTION_SPEC = {
    # Scheme
    "density_dph": (45.0, "Density if units unknown (units/ha)", "Scheme", 1.0),
    "unit_nsa_sqft": (750.0, "Average unit size (sq ft NSA)", "Scheme", 10.0),
    "efficiency": (0.80, "Net to gross efficiency", "Scheme", 0.01),
    "affordable_pct": (0.25, "Affordable housing share", "Scheme", 0.01),
    "affordable_disc": (0.45, "Affordable discount to market value", "Scheme", 0.01),
    # Revenue
    "sales_psf": (450.0, "Sales value (£/sq ft NSA)", "Revenue", 5.0),
    "rent_psf": (24.0, "Rent (£/sq ft NSA pa)", "Revenue", 0.5),
    "void_pct": (0.05, "Void and bad debt", "Revenue", 0.005),
    "opex_pct": (0.25, "Operating costs (% of gross rent)", "Revenue", 0.01),
    "exit_yield": (0.0475, "Exit yield (net initial)", "Revenue", 0.0025),
    "purchaser_costs": (0.068, "Purchaser costs on exit", "Revenue", 0.001),
    "uplift_pct": (0.20, "Value-add: value uplift on refurb", "Revenue", 0.01),
    # Costs
    "build_psf": (170.0, "Build cost (£/sq ft GIA)", "Costs", 5.0),
    "refurb_psf": (90.0, "Refurbishment (£/sq ft GIA)", "Costs", 5.0),
    "external_pct": (0.10, "Externals and abnormals (% of build)", "Costs", 0.01),
    "contingency_pct": (0.05, "Contingency (% of build)", "Costs", 0.005),
    "fees_pct": (0.08, "Professional fees (% of build)", "Costs", 0.005),
    "s106_per_unit": (8000.0, "S106 per unit (£)", "Costs", 500.0),
    "cil_psf": (0.0, "CIL (£/sq ft GIA)", "Costs", 1.0),
    "marketing_pct": (0.03, "Marketing and sales agents (% of GDV)", "Costs", 0.005),
    "sales_legal_pct": (0.005, "Sales legal (% of GDV)", "Costs", 0.0005),
    "acq_costs_pct": (0.068, "Land acquisition costs (SDLT, agent, legal)", "Costs", 0.001),
    # Finance and programme
    "finance_rate": (0.085, "Finance rate (pa)", "Finance and programme", 0.005),
    "ltc": (0.60, "Senior loan to cost", "Finance and programme", 0.05),
    "mezz_ltc": (0.0, "Mezzanine loan to cost (additional)", "Finance and programme", 0.05),
    "mezz_rate": (0.13, "Mezzanine rate (pa)", "Finance and programme", 0.005),
    "debt_fee_pct": (0.01, "Debt arrangement fee (% of facilities)", "Finance and programme", 0.0025),
    "cost_of_equity": (0.12, "Cost of equity / hurdle rate (pa)", "Return targets", 0.005),
    "planning_months": (0.0, "Months to secure planning (0 if consented)", "Finance and programme", 1.0),
    "build_months": (18.0, "Build period (months)", "Finance and programme", 1.0),
    "sales_months": (12.0, "Sales / lease-up period (months)", "Finance and programme", 1.0),
    # Return targets
    "target_profit_gdv": (0.20, "Target profit on GDV (sell)", "Return targets", 0.01),
    "target_profit_cost_btr": (0.15, "Target profit on cost (BTR)", "Return targets", 0.01),
    "target_profit_cost_va": (0.20, "Target profit on cost (value-add)", "Return targets", 0.01),
    "offer_discount": (0.10, "Opening offer below max bid", "Return targets", 0.01),
}

DEFAULT_ASSUMPTIONS = {k: v[0] for k, v in ASSUMPTION_SPEC.items()}

DEFAULT_WEIGHTS = {
    "planning": 0.20,
    "constraints": 0.15,
    "viability": 0.25,
    "scale": 0.10,
    "market": 0.15,
    "mandate": 0.15,
}

DEFAULT_MODEL = "claude-sonnet-4-5"
