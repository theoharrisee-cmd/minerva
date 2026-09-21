import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core.appraisal import appraise, irr, sensitivity
from core.sample import SAMPLE_SITES
from core.scoring import red_flags, score_site
from core.sources import parse_alert_text, parse_csv
from core.planning import analyse_offline


def test_rlv_hits_target_profit():
    site = {"site_ha": 1.0, "sales_psf": 600, "asking_price": 1}
    for strat, key in (("develop_sell", "profit_on_gdv"), ("btr", "profit_on_cost")):
        site["rent_psf"] = 40
        r = appraise(site, strategy=strat)
        assert r["rlv_raw"] > 0
        r2 = appraise(site, strategy=strat, land_price=r["rlv"])
        assert abs(r2[key] - r["target_profit"]) < 1e-6, (strat, r2[key])


def test_value_add_and_sensitivity_direction():
    site = {"existing_sqft": 10000, "asking_price": 1_000_000, "sales_psf": 350, "rent_psf": 20}
    r = appraise(site, strategy="value_add")
    assert r["gdv"] > 0 and r["max_bid"] >= 0
    s = sensitivity({"site_ha": 1, "sales_psf": 500, "asking_price": 1_000_000}, {}, "build_psf", [-0.1, 0.1], "sales_psf", [-0.1, 0.1])
    assert s["z"][0][0] > s["z"][0][1]  # cheaper build, more profit
    assert s["z"][1][0] > s["z"][0][0]  # higher sales, more profit


def test_irr():
    assert abs(irr([-100] + [0] * 11 + [110]) - 0.10) < 1e-3


def test_sample_sites_run():
    for s in SAMPLE_SITES:
        ap = appraise(s)
        fl = red_flags(s)
        sc = score_site(s, ap, fl)
        assert 0 <= sc["score"] <= 100


def test_alert_and_csv_parsing():
    txt = "Development plot\n12 Mill Road, Leeds LS1 4AB\n£450,000\nhttps://www.rightmove.co.uk/properties/123456789#/?channel=RES_BUY\n"
    r = parse_alert_text(txt)
    assert r and r[0]["asking_price"] == 450000 and r[0]["postcode"] == "LS1 4AB"
    c = parse_csv("name,price,postcode\nA,100000,M1 1AA\n")
    assert c


def test_offline_planning():
    r = analyse_offline("The site lies in the Green Belt and Flood Zone 3. Application refused.", {})
    assert r["site_flags"]["green_belt"] and r["planning_position"] == "Refused"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
