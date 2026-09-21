"""Illustrative demo sites so the dashboard works on first launch.
These are NOT real listings: names, prices and attributes are invented."""

SAMPLE_SITES = [
    dict(id="demo-1", name="Former depot, Salford Quays", address="Salford, Greater Manchester", lat=53.4720, lon=-2.2900, la="Salford",
         source="Demo", asking_price=2_600_000, site_ha=1.4, planning_status="Allocated", brownfield=True, flood_zone="1",
         contamination=True, sales_psf=395, rent_psf=28, stage="Screened", strategy="btr"),
    dict(id="demo-2", name="Paddock off Mill Lane, Wokingham", address="Wokingham, Berkshire", lat=51.4112, lon=-0.8330, la="Wokingham",
         source="Demo", asking_price=6_500_000, site_ha=2.6, planning_status="None", green_belt=False, flood_zone="1", trees=True,
         sales_psf=500, rent_psf=24, stage="Sourced", strategy="develop_sell", ovr={"planning_months": 14.0}),
    dict(id="demo-3", name="Cinema and car park, Leeds", address="Leeds, West Yorkshire", lat=53.7997, lon=-1.5492, la="Leeds",
         source="Demo", asking_price=2_400_000, site_ha=0.55, units=120, planning_status="Consented", brownfield=True, flood_zone="2",
         sales_psf=380, rent_psf=29, stage="Appraised", strategy="btr"),
    dict(id="demo-4", name="Warehouse conversion, Bristol", address="Bristol, BS2", lat=51.4585, lon=-2.5810, la="Bristol",
         source="Demo", asking_price=3_400_000, existing_sqft=14_500, units=16, planning_status="Pre-app", conservation_area=True, brownfield=True,
         sales_psf=520, rent_psf=27, stage="Sourced", strategy="value_add"),
    dict(id="demo-5", name="Farmland, Green Belt edge, Guildford", address="Guildford, Surrey", lat=51.2362, lon=-0.5704, la="Guildford",
         source="Demo", asking_price=4_800_000, site_ha=3.1, planning_status="Refused", green_belt=True, flood_zone="1",
         sales_psf=560, rent_psf=26, stage="Rejected", strategy="develop_sell", ovr={"planning_months": 30.0}),
    dict(id="demo-6", name="Brownfield yard, Birmingham Digbeth", address="Birmingham, B5", lat=52.4740, lon=-1.8800, la="Birmingham",
         source="Demo", asking_price=2_950_000, site_ha=0.9, planning_status="Allocated", brownfield=True, contamination=True, flood_zone="1",
         sales_psf=470, rent_psf=23, stage="Screened", strategy="develop_sell"),
    dict(id="demo-7", name="Care home, Reading", address="Reading, Berkshire", lat=51.4543, lon=-0.9781, la="Reading",
         source="Demo", asking_price=4_200_000, existing_sqft=22_000, units=30, planning_status="Pre-app", brownfield=True, flood_zone="1",
         sales_psf=470, rent_psf=24, stage="Offer", strategy="value_add"),
    dict(id="demo-8", name="Riverside plot, Newcastle", address="Newcastle upon Tyne", lat=54.9690, lon=-1.6000, la="Newcastle",
         source="Demo", asking_price=1_100_000, site_ha=0.8, planning_status="Allocated", flood_zone="3", access_issue=True,
         sales_psf=330, rent_psf=19, stage="Sourced", strategy="develop_sell"),
]
