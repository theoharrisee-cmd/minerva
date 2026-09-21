"""Illustrative showcase deals with rich detail. EVERYTHING here is fictional: names, references,
people, telephone numbers (Ofcom drama range 020 7946 xxxx) and documents. It exists only to
demonstrate the product's features. Run `python -m core.demo_deals` to (re)generate the PDFs."""
from __future__ import annotations

from pathlib import Path

DIR = Path(__file__).with_name("demo_docs")
BANNER = "ILLUSTRATIVE DOCUMENT. Fictional content created to demonstrate Minerva. Not a real planning record."

AGENT_HV = dict(firm="Harcourt & Vane LLP (fictional)", role="Head of Land and Development", phone="020 7946 0142", email="land@harcourtvane.example.com",
                branch="Leeds and London", url="https://harcourtvane.example.com/land", verified=False, note="Fictional agent for demonstration")

# ------------------------------------------------------------------ documents
# key -> (deal, filename, category, date, title, paragraphs)
DOCS = {
 "kf-report": ("kingsfield", "Officer_delegated_report_25-03418-FU.pdf", "Officer report", "2026-08-11", "Delegated Officer Report: 25/03418/FU",
  ["Proposal: demolition of existing haulage buildings and erection of a 132 unit Build to Rent residential scheme in three blocks of 5 to 9 storeys, with 38 parking spaces, 210 cycle spaces and ground floor amenity space. Site area 1.1 hectares. Previously developed land.",
   "Principle: the site is within the Hunslet regeneration area and is identified as suitable for residential-led mixed use (Core Strategy policy SP1, Site Allocations Plan HG2-114). Loss of employment land is accepted because the site has been vacant for 26 months and marketing evidence was provided (para 4.6).",
   "Design: following the refusal of 24/01102/FU on height, Block C has been reduced from 12 to 9 storeys and set back 6m from the canal towpath. The Design Panel supported the revised massing (para 6.2). Materials are conditioned.",
   "Affordable housing: 20% Affordable Private Rent at 80% of market rent, secured for the lifetime of the scheme via S106. Viability was reviewed independently and the offer is policy compliant (para 7.4).",
   "Recommendation: APPROVE subject to conditions and completion of a Section 106 agreement. Delegated authority exercised on 11 August 2026."]),
 "kf-decision": ("kingsfield", "Decision_notice_25-03418-FU.pdf", "Decision notice", "2026-08-14", "Decision Notice: Planning Permission Granted",
  ["Application 25/03418/FU. Permission GRANTED on 14 August 2026 subject to 31 conditions. Time limit: three years from the date of decision (expires 13 August 2029).",
   "Pre-commencement conditions include: Construction Management Plan (4), contamination remediation strategy and verification (9 to 12), surface water drainage scheme with 30% betterment on greenfield rate (14), flood resilience measures with finished floor levels no lower than 32.10m AOD (15), Biodiversity Net Gain plan securing 10% (18).",
   "Pre-occupation conditions include: highway works on Hunslet Road (22), travel plan (23), noise mitigation to the railway boundary (25), and provision of the ground floor amenity space (27).",
   "The permission is subject to the S106 agreement dated 12 August 2026 (see heads of terms)."]),
 "kf-highways": ("kingsfield", "Consultee_Highways_response.pdf", "Consultee response", "2026-06-03", "Highways Authority Consultation Response",
  ["No objection subject to conditions. The reduced parking provision (38 spaces for 132 units, 0.29 per unit) is acceptable given the site's PTAL of 4 and the car club bay offered.",
   "Requests: Hunslet Road junction improvement (estimated £180,000 via S278), servicing management plan, a Travel Plan monitoring fee of £6,000, and a Stage 1 Road Safety Audit before commencement of highway works.",
   "The applicant's transport assessment shows 41 two-way vehicle trips in the AM peak, which the Authority considers acceptable."]),
 "kf-llfa": ("kingsfield", "Consultee_LLFA_drainage_response.pdf", "Consultee response", "2026-06-10", "Lead Local Flood Authority Response",
  ["No objection subject to a detailed drainage condition. The site is currently 96% impermeable. The proposal must limit discharge to 5 l/s/ha for the 1 in 100 year plus 40% climate change event, requiring approximately 410 cubic metres of attenuation.",
   "Green roofs on Blocks A and B are welcomed and may be counted towards attenuation."]),
 "kf-ea": ("kingsfield", "Consultee_Environment_Agency_response.pdf", "Consultee response", "2026-06-17", "Environment Agency Response",
  ["No objection on flood risk grounds provided the development is carried out in accordance with the Flood Risk Assessment. The site lies in Flood Zone 2 with a small area of Zone 3a along the canal edge. Residential accommodation must be raised above the 1 in 100 year plus climate change level (32.10m AOD).",
   "Groundwater: the site overlies a Secondary A aquifer. Piling must be risk assessed to avoid contaminant migration."]),
 "kf-eh": ("kingsfield", "Consultee_Environmental_Health_contamination.pdf", "Consultee response", "2026-06-20", "Environmental Health: Contaminated Land",
  ["The Phase 2 report identifies hydrocarbons (up to 3,400 mg/kg TPH) and elevated lead in made ground to 2.5m in the former fuel storage area. Remediation is required in the form of excavation and off-site disposal of approximately 1,900 cubic metres, and gas protection measures to Blocks B and C.",
   "Indicative remediation cost in the applicant's report: £640,000 to £820,000. Conditions 9 to 12 secure remediation, verification and a discovery strategy."]),
 "kf-s106": ("kingsfield", "S106_Heads_of_Terms.pdf", "S106 / obligations", "2026-07-28", "Section 106 Heads of Terms",
  ["Affordable housing: 26 units (20%) as Affordable Private Rent at 80% of open market rent, retained for the life of the scheme with a clawback mechanism.",
   "Financial contributions: Public transport £96,000; Greenspace £142,000 (£1,075 per dwelling); Travel plan monitoring £6,000; Local employment and skills £38,000. Total £282,000, index linked. No education contribution due to the BTR tenure.",
   "Viability review mechanism at 75% occupation. Monitoring fee 2.5% of contributions."]),
 "kf-brochure": ("kingsfield", "Sales_particulars_Kingsfield_Yard.pdf", "Brochure / particulars", "2026-08-25", "Sales Particulars: Kingsfield Yard, Hunslet",
  ["Freehold development opportunity with full planning permission for 132 Build to Rent apartments. Guide price £3,400,000 (subject to contract). Informal tender, bids by 12 noon on 16 October 2026.",
   "Site area 1.1 hectares. Vacant possession. Services available at the boundary. Phase 2 contamination report and Section 106 agreement available in the data room. VAT is not payable on the price."]),
 "mp-preapp": ("millpond", "LPA_pre-application_advice_letter.pdf", "Officer report", "2026-04-09", "Pre-Application Advice: Land at Mill Pond Meadows",
  ["Principle: the site is allocated for approximately 150 dwellings in the Local Plan Update (policy SS12). Development of the allocation is supported in principle subject to the requirements of the policy, including a Suitable Alternative Natural Greenspace (SANG) contribution and a primary school contribution.",
   "Housing mix: 40% affordable (70:30 social rent to shared ownership), a minimum of 10% as M4(3) wheelchair accessible. Density of 31 dph is acceptable; officers would accept up to 34 dph subject to landscape impact.",
   "Concerns: officers consider the proposed access from Mill Lane inadequate for 150 dwellings and advise that a second emergency access will be needed. The landscape officer is concerned about built form on the western ridge line.",
   "Timescale: an outline application is likely to be determined at committee in 13 to 16 months, given the scale and the need for a Section 106 agreement."]),
 "mp-highways": ("millpond", "Consultee_Highways_holding_objection.pdf", "Consultee response", "2026-07-22", "Highways Authority: Holding Objection",
  ["Holding objection. The Transport Assessment underestimates trip generation and does not model the Mill Lane / Reading Road junction, which operates at 96% capacity in the PM peak. A junction improvement scheme is likely to be required, estimated at £650,000 to £900,000.",
   "A second access for emergency vehicles is required. Pedestrian and cycle links to the station (1.4km) must be provided."]),
 "mp-ne": ("millpond", "Consultee_Natural_England_SANG.pdf", "Consultee response", "2026-07-30", "Natural England: Thames Basin Heaths SPA",
  ["The site lies within 5km of the Thames Basin Heaths Special Protection Area. Natural England advises that the development is acceptable only if mitigated through SANG provision and a SAMM tariff. Approximately £2,650 per dwelling is expected for the combined contribution.",
   "The Habitats Regulations Assessment must be completed before permission can be granted."]),
 "mp-tw": ("millpond", "Consultee_Thames_Water_capacity.pdf", "Consultee response", "2026-08-05", "Thames Water: Network Capacity",
  ["Foul water: the existing network has insufficient capacity for 150 dwellings. Network reinforcement is required and Thames Water will need up to 18 months from a firm order to deliver it. A Grampian condition is likely.",
   "Water supply: capacity available subject to a 200mm main extension at the developer's cost."]),
 "mp-lp": ("millpond", "Local_Plan_Update_policy_SS12_extract.pdf", "Local plan / policy", "2025-11-18", "Local Plan Update: Policy SS12 (Extract)",
  ["Land at Mill Pond Meadows is allocated for approximately 150 dwellings. Development will be permitted subject to: a masterplan agreed with the Council; 40% affordable housing; delivery of 1.6ha of SANG on site; a new primary school contribution; a link road connection to Reading Road; retention of the western hedgerow and ridge line planting.",
   "The Plan was submitted for examination in January 2026. Hearings are scheduled for November 2026. Policy SS12 has moderate weight."]),
 "mp-brochure": ("millpond", "Marketing_brochure_Mill_Pond_Meadows.pdf", "Brochure / particulars", "2026-06-15", "Marketing Brochure: Mill Pond Meadows",
  ["Greenfield allocated site of 4.8 hectares. Guide price £5,600,000 for the freehold. The vendor will consider offers conditional on an outline planning consent (with a longstop of 24 months) and will share planning costs.",
   "Existing use: arable and paddock. Boundary hedgerows and 14 category B trees. No known contamination. Vendor's planning consultant has submitted an outline application (ref O/2026/1774) which is pending."]),
 "hr-conservation": ("harbour", "Pre-app_Conservation_Officer_response.pdf", "Consultee response", "2026-05-19", "Conservation Officer: Pre-Application Response",
  ["The three warehouses are Grade II listed and form part of the Harbourside Conservation Area. The principle of residential conversion is supported as a viable use that secures the long-term future of the buildings.",
   "Concerns: the proposed rooftop extension on Warehouse 2 would harm the roofline and is not supported. Retention of the cast iron columns, timber floor structure and loading doors is expected. New window openings on the quay elevation will not be accepted.",
   "Listed Building Consent will be needed alongside the planning application. A Heritage Statement and a schedule of works are required."]),
 "hr-he": ("harbour", "Consultee_Historic_England_advice.pdf", "Consultee response", "2026-06-02", "Historic England: Pre-Application Advice",
  ["Historic England supports re-use of the warehouses. It advises that the scheme minimises intervention to the primary structure and recommends a structural strategy that retains the timber floor plates as an exposed feature.",
   "It recommends analysis of the cast iron column loading before any additional floors or plant are proposed."]),
 "hr-ea": ("harbour", "Consultee_Environment_Agency_tidal_flood.pdf", "Consultee response", "2026-06-11", "Environment Agency: Tidal Flood Risk",
  ["The site lies in Flood Zone 3a (tidal) and benefits from the Bristol Frome defences to a 1 in 200 standard. Residential use at ground floor level is not acceptable; sleeping accommodation must be at first floor or above. A flood warning and evacuation plan is required. The Sequential Test must be passed.",
   "Ground floor should be limited to commercial or parking uses, which lowers the achievable number of apartments."]),
 "hr-survey": ("harbour", "Structural_condition_survey_summary.pdf", "Survey / technical", "2026-04-30", "Structural Condition Survey: Summary",
  ["Warehouses 1 and 3 are in fair condition. Warehouse 2 has localised decay to timber joists at the northern gable and significant deflection to the second floor. Estimated structural repair budget £410,000. Roof coverings require replacement (£290,000). Asbestos survey identified ACM in the boiler room and ceiling boards.",
   "Cast iron columns show no evidence of cracking. Floor loading capacity is 5kN/sqm, suitable for residential."]),
 "hr-brochure": ("harbour", "Particulars_Harbour_Row_Warehouses.pdf", "Brochure / particulars", "2026-05-06", "Particulars: Harbour Row Warehouses",
  ["Three Grade II listed warehouses totalling approximately 21,400 sq ft (GIA) on 0.35 hectares, with quay frontage. Offers invited around £3,300,000. Pre-application discussions have been held for 22 apartments and ground floor commercial units.",
   "Freehold. Sold with the benefit of a heritage statement and structural survey. Sale by informal tender."]),
 "oi-appeal": ("infirmary", "Appeal_decision_APP-X2715-W-25-3341.pdf", "Appeal decision", "2026-06-12", "Appeal Decision: Appeal Allowed",
  ["The appeal is allowed and planning permission is granted for the change of use and extension of the former Old Infirmary to provide 40 retirement apartments (Class C3) with communal facilities, subject to conditions.",
   "Main issues: (1) the effect on the character of the Conservation Area; (2) the adequacy of parking. The Inspector found that the removal of the 1970s extension would enhance the Conservation Area and that the scheme would cause less than substantial harm, outweighed by the public benefits including the re-use of a vacant building and the delivery of specialist housing for older people (paras 14 to 19).",
   "Parking: the Inspector accepted a provision of 0.5 spaces per unit given the retirement occupancy restriction (para 24).",
   "Costs: an application for costs by the appellant was refused. Conditions include a restriction to occupants aged 60 or over (condition 5)."]),
 "oi-refusal": ("infirmary", "Refusal_notice_24-02271-FUL.pdf", "Decision notice", "2025-11-07", "Refusal Notice: 24/02271/FUL",
  ["Refused on 7 November 2025 for two reasons: (1) the proposed extension by reason of scale and design would fail to preserve or enhance the character and appearance of the Conservation Area; (2) insufficient on-site parking would lead to displaced parking on surrounding streets to the detriment of highway safety."]),
 "oi-report": ("infirmary", "Officer_report_24-02271-FUL.pdf", "Officer report", "2025-10-30", "Committee Report: 24/02271/FUL",
  ["Officers recommended refusal on the reasons set out above. Committee agreed with the recommendation and refused the application. The report notes that the applicant offered a S106 contribution of £120,000 for off-site affordable housing and £48,000 for open space.",
   "Consultees: Highways objects on parking; Conservation Officer objects to the third storey extension; Environmental Health no objection; Ecology requires a bat survey (submitted, roost of Common Pipistrelle in the north gable requiring a licence)."]),
 "oi-brochure": ("infirmary", "Sales_brochure_Old_Infirmary.pdf", "Brochure / particulars", "2026-07-06", "Sales Brochure: The Old Infirmary, Harrogate",
  ["Freehold former care home of 31,000 sq ft (GIA) on 0.9 hectares with mature gardens. Now benefits from planning permission on appeal for 40 retirement apartments. Guide price £2,400,000.",
   "The permission will expire three years from 12 June 2026. A bat licence is required before demolition works commence. Vacant possession."]),
}

DEALS = [
 dict(id="rich-kingsfield", name="Kingsfield Yard, Hunslet, Leeds", address="Hunslet Road, Leeds LS10 1JQ", postcode="LS10 1JQ", lat=53.7845, lon=-1.5320, la="Leeds",
      source="Harcourt & Vane LLP", listing=True, demo=True, demo_rich=True, strategy="btr", stage="Screened", planning_status="Consented", brownfield=True,
      contamination=True, flood_zone="2", asking_price=3_400_000, site_ha=1.1, units=132, sales_psf=330, rent_psf=20, property_type="Development land (consented)",
      tenure="Freehold", description="Former haulage depot with full planning permission (granted 14 August 2026) for 132 Build to Rent apartments in three blocks of 5 to 9 storeys beside the canal. Vacant possession, services at boundary, Phase 2 contamination report available.",
      vendor="Hunslet Haulage Holdings Ltd (fictional)", marketing="Informal tender, bids by 12 noon on 16 October 2026", bid_deadline="2026-10-16",
      utilities="All mains services at boundary; 800kVA substation upgrade to be confirmed by Northern Powergrid", access="From Hunslet Road; secondary access to canal towpath (Canal & River Trust licence needed)", existing_use="Vacant haulage yard (B8)",
      unit_mix=[dict(type="Studio", count=20, nsa_sqft=380, sale_value=135000, rent_pcm=1085), dict(type="1 bed", count=52, nsa_sqft=520, sale_value=172000, rent_pcm=1315),
                dict(type="2 bed", count=50, nsa_sqft=735, sale_value=235000, rent_pcm=1700), dict(type="3 bed", count=10, nsa_sqft=980, sale_value=300000, rent_pcm=2060)],
      build_cost_total=16_800_000, gia_sqft=99_000,
      ovr=dict(affordable_pct=0.20, affordable_disc=0.20, s106_per_unit=2136, exit_yield=0.0500, opex_pct=0.25, planning_months=0.0, build_months=22.0, cil_psf=0.0),
      agent={**AGENT_HV, "name": "Priya Raman", "role": "Associate Director, Land and Development", "phone": "020 7946 0142", "email": "priya.raman@harcourtvane.example.com", "address": "14 Whitehall Quay, Leeds LS1 4HR"},
      comps=[dict(kind="BTR sale", address="Canal Wharf, Leeds LS10", detail="184 units, sold to a PRS investor", metric="4.90% NIY", date="2026-03"),
             dict(kind="Rent", address="Tannery Square, Leeds LS11", detail="2 bed, 720 sq ft", metric="£1,625 pcm (£32.5 psf pa)", date="2026-07"),
             dict(kind="Rent", address="Kirkstall Point, Leeds LS5", detail="1 bed, 510 sq ft", metric="£1,250 pcm", date="2026-06"),
             dict(kind="Land", address="Crown Point Road, Leeds LS9", detail="0.8ha consented BTR site", metric="£26,000 per unit", date="2026-02")],
      key_dates=[dict(date="2026-08-14", event="Planning permission granted"), dict(date="2026-10-16", event="Tender deadline"), dict(date="2029-08-13", event="Permission expires")],
      notes="Strong consent, contamination is the main cost risk (£640k to £820k in the applicant's estimate). Check whether the seller will retain a contamination indemnity. Exit yield needs testing against the Canal Wharf sale.",
      docs=["kf-report", "kf-decision", "kf-highways", "kf-llfa", "kf-ea", "kf-eh", "kf-s106", "kf-brochure"],
      planning_history=[
          dict(ref="25/03418/FU", status="Approved", description="Demolition and erection of 132 BTR apartments in three blocks", submitted="2025-12-02", decided="2026-08-14", lpa="Leeds City Council", docs=["kf-report", "kf-decision", "kf-s106"],
               key_points=["Delegated approval, 31 conditions", "20% Affordable Private Rent at 80% of market", "Block C reduced from 12 to 9 storeys"]),
          dict(ref="24/01102/FU", status="Refused", description="Demolition and erection of 141 apartments, up to 12 storeys", submitted="2024-09-10", decided="2025-05-06", lpa="Leeds City Council", docs=[],
               key_points=["Refused on height and impact on canal setting", "Informed the redesign"]),
          dict(ref="23/00210/PREAPP", status="Pre-app", description="Pre-application advice for residential led redevelopment", submitted="2023-03-14", decided="2023-05-22", lpa="Leeds City Council", docs=[],
               key_points=["Principle of residential supported", "Height concern flagged"])],
      consultees=[
          dict(body="Highways", stance="Conditions", summary="No objection; S278 junction works c.£180k, travel plan fee £6k", doc="kf-highways", date="2026-06-03"),
          dict(body="Lead Local Flood Authority", stance="Conditions", summary="5 l/s/ha discharge, c.410m3 attenuation", doc="kf-llfa", date="2026-06-10"),
          dict(body="Environment Agency", stance="No objection", summary="Finished floor levels 32.10m AOD; piling risk assessment", doc="kf-ea", date="2026-06-17"),
          dict(body="Environmental Health", stance="Conditions", summary="Remediation £640k to £820k; gas protection to Blocks B and C", doc="kf-eh", date="2026-06-20"),
          dict(body="Ecology", stance="Conditions", summary="10% Biodiversity Net Gain, delivered off-site", doc=None, date="2026-06-12"),
          dict(body="Neighbour representations", stance="Mixed", summary="14 objections (height, parking), 6 in support", doc=None, date="2026-07-01")]),
 dict(id="rich-millpond", name="Mill Pond Meadows, Wokingham", address="Mill Lane, Wokingham RG40 3QT", postcode="RG40 3QT", lat=51.4053, lon=-0.8590, la="Wokingham",
      source="Harcourt & Vane LLP", listing=True, demo=True, demo_rich=True, strategy="develop_sell", stage="Sourced", planning_status="Allocated", flood_zone="1", trees=True,
      asking_price=5_600_000, site_ha=4.8, units=150, sales_psf=480, rent_psf=24, property_type="Greenfield allocation", tenure="Freehold",
      description="4.8 hectare greenfield site allocated for approximately 150 homes in the Local Plan Update (policy SS12). Outline application pending. Vendor will consider conditional offers with a 24 month longstop and will share planning costs.",
      vendor="Mill Pond Estates Trust (fictional)", marketing="Offers invited, conditional bids welcome", bid_deadline="2026-11-06", utilities="Water on site; foul network reinforcement needed (Thames Water up to 18 months)",
      access="Mill Lane (single carriageway); second emergency access required", existing_use="Arable and paddock",
      unit_mix=[dict(type="2 bed house", count=36, nsa_sqft=790, sale_value=439000), dict(type="3 bed house", count=58, nsa_sqft=1050, sale_value=576000),
                dict(type="4 bed house", count=38, nsa_sqft=1420, sale_value=775000), dict(type="1 bed flat", count=18, nsa_sqft=530, sale_value=279000)],
      ovr=dict(affordable_pct=0.40, affordable_disc=0.42, s106_per_unit=14500, cil_psf=18.0, planning_months=14.0, build_months=28.0, sales_months=6.0, build_psf=165.0, external_pct=0.14),
      agent={**AGENT_HV, "name": "Tom Ashworth", "role": "Partner, Land and Development", "phone": "020 7946 0177", "email": "tom.ashworth@harcourtvane.example.com", "address": "9 Cavendish Square, London W1G 0PH"},
      comps=[dict(kind="Land", address="Barkham Road, Wokingham RG41", detail="5.2ha allocated site, sold STP", metric="£1.9m per hectare", date="2026-01"),
             dict(kind="New build", address="Arborfield Green RG2", detail="3 bed house, 1,040 sq ft", metric="£510,000 (£490 psf)", date="2026-06"),
             dict(kind="New build", address="Finchampstead RG40", detail="4 bed house, 1,410 sq ft", metric="£690,000 (£489 psf)", date="2026-05")],
      key_dates=[dict(date="2026-07-22", event="Highways holding objection"), dict(date="2026-11-06", event="Offer deadline"), dict(date="2026-11-17", event="Local Plan Update hearings"), dict(date="2027-09-01", event="Committee (target)")],
      notes="Land value hinges on the Mill Lane junction (£650k to £900k) and SANG/SAMM costs (c.£2,650 per dwelling). Local Plan is at examination so SS12 carries moderate weight. Structure any offer as conditional on outline consent.",
      docs=["mp-preapp", "mp-highways", "mp-ne", "mp-tw", "mp-lp", "mp-brochure"],
      planning_history=[
          dict(ref="O/2026/1774", status="Pending", description="Outline application for up to 150 dwellings, access and SANG", submitted="2026-06-24", decided=None, lpa="Wokingham Borough Council", docs=["mp-highways", "mp-ne", "mp-tw"],
               key_points=["Highways holding objection (junction capacity)", "HRA needed for SPA", "Thames Water Grampian condition likely"]),
          dict(ref="PA/2026/0412", status="Pre-app", description="Pre-application advice for 150 dwellings", submitted="2026-02-11", decided="2026-04-09", lpa="Wokingham Borough Council", docs=["mp-preapp"],
               key_points=["Principle supported (allocation SS12)", "40% affordable, M4(3) 10%", "Second access and ridge line concerns"])],
      consultees=[
          dict(body="Highways", stance="Object", summary="Holding objection: junction at 96% capacity, second access needed", doc="mp-highways", date="2026-07-22"),
          dict(body="Natural England", stance="Conditions", summary="SANG and SAMM c.£2,650 per dwelling; HRA required", doc="mp-ne", date="2026-07-30"),
          dict(body="Thames Water", stance="Conditions", summary="Foul capacity insufficient; up to 18 months reinforcement", doc="mp-tw", date="2026-08-05"),
          dict(body="Landscape officer", stance="Object", summary="Built form on the western ridge line", doc="mp-preapp", date="2026-04-09"),
          dict(body="Education", stance="Conditions", summary="Primary school contribution expected under SS12", doc="mp-lp", date="2026-05-01")]),
 dict(id="rich-harbour", name="Harbour Row Warehouses, Bristol", address="Harbour Row, Bristol BS1 5TT", postcode="BS1 5TT", lat=51.4487, lon=-2.5985, la="Bristol",
      source="Harcourt & Vane LLP", listing=True, demo=True, demo_rich=True, strategy="value_add", stage="Appraised", planning_status="Pre-app", listed=True, conservation_area=True, flood_zone="3", brownfield=True,
      asking_price=3_300_000, existing_sqft=21_400, units=22, sales_psf=610, rent_psf=27, property_type="Listed warehouses (conversion)", tenure="Freehold",
      description="Three Grade II listed quayside warehouses in the Harbourside Conservation Area. Pre-application advice supports residential conversion but not the proposed roof extension. Ground floor residential is not acceptable due to tidal flood risk.",
      vendor="Harbour Row Trustees (fictional)", marketing="Informal tender", bid_deadline="2026-10-30", utilities="Mains services; boiler room contains ACM", access="Quay frontage and rear service yard from Harbour Lane", existing_use="Vacant storage (B8)",
      unit_mix=[dict(type="1 bed", count=8, nsa_sqft=560, sale_value=345000, rent_pcm=1650), dict(type="2 bed", count=10, nsa_sqft=790, sale_value=470000, rent_pcm=2150), dict(type="3 bed penthouse", count=4, nsa_sqft=1150, sale_value=720000, rent_pcm=3100)],
      ovr=dict(refurb_psf=185.0, contingency_pct=0.12, fees_pct=0.12, planning_months=10.0, build_months=16.0, uplift_pct=0.08, affordable_pct=0.0),
      agent={**AGENT_HV, "name": "Nadia Osei", "role": "Director, Heritage and Regeneration", "phone": "020 7946 0163", "email": "nadia.osei@harcourtvane.example.com", "address": "22 Queen Square, Bristol BS1 4ND"},
      comps=[dict(kind="Sale", address="Wapping Wharf, Bristol BS1", detail="2 bed conversion apartment, 800 sq ft", metric="£475,000 (£594 psf)", date="2026-06"),
             dict(kind="Sale", address="Redcliffe Wharf, Bristol BS1", detail="1 bed, 540 sq ft", metric="£330,000 (£611 psf)", date="2026-05"),
             dict(kind="Refurb cost", address="Grade II mill conversion, Bath", detail="Heritage residential", metric="£240 to £290 psf", date="2025-11")],
      key_dates=[dict(date="2026-05-19", event="Conservation Officer pre-app response"), dict(date="2026-06-11", event="EA flood response"), dict(date="2026-10-30", event="Tender deadline")],
      notes="Heritage premium on values but heavy abnormal costs: structural repair £410k, roof £290k, asbestos. Flood Zone 3a removes ground floor residential. Rooftop extension unlikely, so model 22 units without it.",
      docs=["hr-conservation", "hr-he", "hr-ea", "hr-survey", "hr-brochure"],
      planning_history=[
          dict(ref="PA/2026/0288", status="Pre-app", description="Pre-application: conversion to 22 apartments with ground floor commercial", submitted="2026-04-02", decided="2026-05-19", lpa="Bristol City Council", docs=["hr-conservation", "hr-he", "hr-ea"],
               key_points=["Rooftop extension on Warehouse 2 not supported", "LBC required", "No ground floor residential (Flood Zone 3a)"])],
      consultees=[
          dict(body="Conservation Officer", stance="Conditions", summary="Supports conversion; retain columns, timber floors and loading doors; no rooftop extension", doc="hr-conservation", date="2026-05-19"),
          dict(body="Historic England", stance="No objection", summary="Supports re-use; minimal intervention", doc="hr-he", date="2026-06-02"),
          dict(body="Environment Agency", stance="Conditions", summary="Zone 3a tidal; sleeping above first floor; evacuation plan", doc="hr-ea", date="2026-06-11")]),
 dict(id="rich-infirmary", name="The Old Infirmary, Harrogate", address="Victoria Avenue, Harrogate HG1 5QF", postcode="HG1 5QF", lat=53.9921, lon=-1.5418, la="Harrogate",
      source="Harcourt & Vane LLP", listing=True, demo=True, demo_rich=True, strategy="develop_sell", stage="Offer", planning_status="Consented", conservation_area=True, brownfield=True, trees=True, flood_zone="1",
      asking_price=2_400_000, site_ha=0.9, units=40, sales_psf=500, rent_psf=25, property_type="Care home (consented on appeal)", tenure="Freehold",
      description="Former care home of 31,000 sq ft on 0.9 hectares with mature gardens. Planning permission was granted on appeal on 12 June 2026 for 40 retirement apartments. A bat licence is required before demolition works.",
      vendor="Northern Care Estates plc (fictional)", marketing="Guide price, private treaty", bid_deadline="2026-10-09", utilities="All mains; gas supply to be reconfigured", access="Victoria Avenue; gated drive", existing_use="Vacant care home (C2)",
      unit_mix=[dict(type="1 bed retirement", count=16, nsa_sqft=560, sale_value=334000), dict(type="2 bed retirement", count=20, nsa_sqft=780, sale_value=454000), dict(type="2 bed plus", count=4, nsa_sqft=950, sale_value=552000)],
      build_cost_total=7_200_000, gia_sqft=44_000, ovr=dict(affordable_pct=0.0, s106_per_unit=4200, planning_months=0.0, build_months=20.0, sales_months=18.0, target_profit_gdv=0.18),
      agent={**AGENT_HV, "name": "Julian Frey", "role": "Partner", "phone": "020 7946 0190", "email": "julian.frey@harcourtvane.example.com", "address": "5 Parliament Street, Harrogate HG1 2QU", "branch": "Harrogate"},
      comps=[dict(kind="Sale", address="Cornwall Court, Harrogate HG1", detail="2 bed retirement, 760 sq ft", metric="£440,000 (£579 psf)", date="2026-04"),
             dict(kind="Sale", address="The Stray Residences, Harrogate HG2", detail="1 bed retirement, 550 sq ft", metric="£328,000 (£596 psf)", date="2026-02")],
      key_dates=[dict(date="2026-06-12", event="Appeal allowed"), dict(date="2026-10-09", event="Offers by"), dict(date="2029-06-11", event="Permission expires")],
      notes="Appeal win removes the main risk. Retirement sales pace is slower (allow 18 to 24 months). The permission is restricted to occupants aged 60 or over. Bat roost needs a licence: build 3 months into the programme.",
      docs=["oi-appeal", "oi-refusal", "oi-report", "oi-brochure"],
      planning_history=[
          dict(ref="APP/X2715/W/25/3341", status="Appeal allowed", description="Appeal against refusal of 24/02271/FUL: 40 retirement apartments", submitted="2026-01-14", decided="2026-06-12", lpa="Harrogate Borough Council (Planning Inspectorate)", docs=["oi-appeal"],
               key_points=["Less than substantial harm outweighed by public benefits", "Parking at 0.5 per unit accepted", "Age restriction 60+"]),
          dict(ref="24/02271/FUL", status="Refused", description="Change of use and extension to 40 retirement apartments", submitted="2024-11-19", decided="2025-11-07", lpa="Harrogate Borough Council", docs=["oi-refusal", "oi-report"],
               key_points=["Refused: extension design in Conservation Area", "Refused: insufficient parking"])],
      consultees=[
          dict(body="Highways", stance="Object", summary="Parking provision inadequate (overruled at appeal)", doc="oi-report", date="2025-08-22"),
          dict(body="Conservation Officer", stance="Object", summary="Third storey extension harmful (overruled at appeal)", doc="oi-report", date="2025-08-29"),
          dict(body="Ecology", stance="Conditions", summary="Common Pipistrelle roost in north gable: licence required", doc="oi-report", date="2025-09-05"),
          dict(body="Environmental Health", stance="No objection", summary="No contamination concerns", doc="oi-report", date="2025-09-01")]),
]


def write_pdfs():
    """Generate the demo PDFs and .txt sidecars (needs reportlab). Run once from a dev machine."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from reportlab.lib import colors
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10.5, leading=15, spaceAfter=8)
    ban = ParagraphStyle("ban", parent=ss["BodyText"], fontSize=8, textColor=colors.HexColor("#B3261E"), spaceAfter=10)
    for key, (deal, fn, cat, date, title, paras) in DOCS.items():
        out = DIR / deal
        out.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(out / fn), pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=20 * mm, bottomMargin=20 * mm, title=title)
        story = [Paragraph(BANNER, ban), Paragraph(title, ss["Title"]), Paragraph(f"{cat} · dated {date}", ss["Italic"]), Spacer(1, 8)]
        for i, p in enumerate(paras, 1):
            story.append(Paragraph(f"<b>{i}.</b> {p}", body))
        doc.build(story)
        (out / (fn + ".txt")).write_text(f"{title}\n{cat} {date}\n\n" + "\n\n".join(paras))
    print("wrote", len(DOCS), "documents to", DIR)


if __name__ == "__main__":
    write_pdfs()
