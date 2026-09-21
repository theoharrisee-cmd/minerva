import os, pathlib, sys, tempfile
os.environ["MINERVA_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import net, scrapers

LANDSALE = """<html><body>
<div class="card"><a href="/properties/155711"><img src="x.jpg"></a><h3><a href="/properties/155711">16-20 Morden Road, South Wimbledon SW19</a></h3><p>From £3,500,000</p><p>Development site with planning permission granted for 24 flats. 0.4 acres</p></div>
<div class="card"><a href="/properties/155678"><img src="y.jpg"></a><h3><a href="/properties/155678">188 Rye Lane, Peckham, SE15</a></h3><p>£1,950,000</p><p>Freehold block, subject to planning</p></div>
<div class="card"><a href="/properties/155187">Land to the East of 28 Groombridge Road E9 7DP</a><span>Offers in Excess of £750,000</span></div>
</body></html>"""
HAMPTONS = """<ul><li><a href="/properties/22134598/sales/A1NTV">Highfield Gardens, Aldershot, GU11</a> <b>£795,000</b> 3 bed house</li>
<li><a href="/properties/22134599/lettings/B2">Rental flat</a> £1,500 pcm</li></ul>"""
JSONLD = """<script type="application/ld+json">{"@type":"ItemList","itemListElement":[{"@type":"ListItem","item":{"@type":"Product","name":"Barn conversion, Devon","url":"/details/20025735/","offers":{"price":"1150000"},"geo":{"latitude":50.7,"longitude":-3.5}}}]}</script>"""


def run(src_id, html, **kw):
    src = next(s for s in scrapers.SOURCES if s["id"] == src_id)
    net.fetch = lambda url, **k: html if "page=" not in url else ""
    scrapers.geocode_text = lambda t: None
    return scrapers.scrape_source(src, max_pages=1, **kw)


def test_landsale():
    r = run("landsale", LANDSALE)
    assert r["status"] == "ok" and len(r["listings"]) == 3, r
    a = {x["id"]: x for x in r["listings"]}["landsale-155711"]
    assert a["asking_price"] == 3_500_000 and a["planning_status"] == "Consented" and a["property_type"] == "Land"
    assert a["site_ha"] == 0.16 or abs(a["site_ha"] - 0.16) < 0.01
    assert {x["asking_price"] for x in r["listings"]} == {3_500_000, 1_950_000, 750_000}


def test_hamptons_skips_lettings_and_filters():
    r = run("hamptons", HAMPTONS, opportunities_only=False)
    assert len(r["listings"]) == 1 and r["listings"][0]["bedrooms"] == 3
    r2 = run("hamptons", HAMPTONS, opportunities_only=True)  # ordinary house filtered out
    assert len(r2["listings"]) == 0


def test_jsonld():
    r = run("onthemarket", JSONLD)
    assert r["listings"] and r["listings"][0]["lat"] == 50.7 and r["listings"][0]["asking_price"] == 1_150_000


def test_blocked_and_js():
    src = next(s for s in scrapers.SOURCES if s["id"] == "savills")
    def boom(url, **k): raise net.Blocked("blocked by the site (HTTP 403)")
    net.fetch = boom
    r = scrapers.scrape_source(src)
    assert r["status"] == "blocked" and not r["listings"]
    net.fetch = lambda url, **k: '<html><script id="__NEXT_DATA__">{}</script></html>'
    r = scrapers.scrape_source(next(s for s in scrapers.SOURCES if s["id"] == "knightfrank"), max_pages=1)
    assert r["status"] == "js"


def test_snapshot_fallback_job():
    net.fetch = lambda url, **k: (_ for _ in ()).throw(net.Blocked("blocked by the site (HTTP 403)"))
    sites = []
    job = scrapers.ScrapeJob()
    job.start(["landsale", "jacksonstops"], sites, lambda: None, {"use_snapshot": True, "max_pages": 1})
    import time
    for _ in range(50):
        if not job.snapshot()["running"]: break
        time.sleep(0.1)
    s = job.snapshot()
    assert s["sources"]["landsale"]["fallback"] and len(sites) == 7, (s, len(sites))


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
