# Minerva 0.3

A native Mac app for finding, screening and appraising UK development and investment sites, built around how a developer-investor thinks.

## Running it

**Web version.** See `DEPLOY.md` to host Minerva behind a password on Render with no Terminal needed.

**1. The DMG (recommended).** Build it once on a Mac, then drag Minerva into Applications.

    ./packaging/build_dmg.sh          # produces dist/Minerva.dmg

No Mac to hand? Push this folder to GitHub and run the "Build Minerva DMG" workflow (Actions tab). It produces Apple Silicon and Intel DMGs as downloadable artefacts.

The app is not notarised. The first time, right-click Minerva in Applications and choose Open. If macOS says it is damaged, run `xattr -dr com.apple.quarantine /Applications/Minerva.app`.

**2. Double-click.** `Minerva.command` runs from source using the Python 3 already on your Mac and opens in your browser. Excel export needs `pip3 install openpyxl`; PDF text reading needs `pypdf`.

**3. Terminal.** `python3 run.py` (native window if `pywebview` is installed, otherwise the browser).

Your data lives in `~/Library/Application Support/Minerva`.

## What is new in 0.3

| Feature | Where | What it does |
|---|---|---|
| My mandate | left rail | Fund size, equity available, ticket and deal size, strategies, regions, planning appetite, exclusions, return targets, cost of equity, senior and mezzanine terms. Scores every site for fit, writes your cost of capital into every appraisal and filters listing refreshes. |
| Agent contact card | site > Overview | Named agent, phone and email where published, otherwise the firm's team or contact page, plus a one-click enquiry draft that opens in your email app. |
| Planning | site > Planning | Council register links, rule-based risk read-out, permission expiry, timeline, application register and consultee matrix (all editable), and a document analysis whose findings link back to the source document. |
| Documents | site > Documents | Per-deal vault. Drop PDFs, brochures, emails. Read in-app, auto-categorised, searchable by the analysis and Q&A. |
| Add deal | top right | Paste an agent's email or brochure, or drop PDFs and `.eml` files. Minerva reads the facts, creates the site and builds the model. |
| Financial model | site > Model | Editable unit mix and cost inputs, live appraisal, and a formula-driven Excel workbook (Inputs, Appraisal, Cash Flow, Summary, Sensitivity, Deal Info) that recalculates. |
| Market evidence | site > Market | HM Land Registry sold prices for the postcode sector, with EPC floor areas (free key) converted to £ per sq ft and one click to apply to the appraisal. |
| Inbox | left rail | Outlook through Microsoft Graph (read-only) with a likely-deal filter and one-click model build. A labelled demo mailbox is included. |
| Illustrative deals | Sites | Four fully fictional deals with 23 planning documents to show every feature. Remove or restore them in Settings. |

### Connecting Outlook

Microsoft requires each app to have an identity, so there is a three-minute one-off step. In Microsoft Entra (portal.azure.com) register an app, turn on **Allow public client flows**, add the delegated permissions **Mail.Read** and **User.Read**, then paste the Application (client) ID into Inbox and press Connect. You sign in on a Microsoft page with a short code. No secret is stored and Minerva never sends, moves or deletes mail. Tokens are saved in your Minerva data folder. Work accounts may need administrator consent. Not tested against a live tenant (see below).

## Existing views

Overview (KPIs, clustered map, ranking, funnel), Sites (sortable table, mandate filter), Pipeline (drag and drop), Sourcing (10 national agents and 2 aggregators, brownfield search, CSV and alert import), Settings (every assumption, scorecard weights, Claude API key, EPC key).

## Listings: how sourcing works

Rightmove and Zoopla are not used. Minerva reads public search pages from Jackson-Stops, Hamptons, Foxtons, Chestertons, Strutt & Parker, Savills, Knight Frank, Carter Jonas, Winkworth and Fine & Country, plus LandSale and OnTheMarket (land). Each source is polite (robots.txt, rate limit, 6 hour cache) and reports an honest status. When a source fails, a bundled snapshot of real listings (21 Sep 2026) is shown and labelled. Refreshes drop sites outside your mandate if you have one.

Contact details: only Hamptons publishes a firm number and land team email that we could confirm. For the rest Minerva links to the firm's contact page and extracts the named agent from each listing page where it is published.

## What has and has not been verified

* Verified by tests: appraisal engine, mandate logic, intake parsing (paste and `.eml`), document vault, planning register, Land Registry response parsing, the Outlook flow against a mocked Microsoft Graph, and every Excel workbook (recalculated in LibreOffice and matched to the engine to four significant figures).
* Not verified: live scraping, the Land Registry endpoint and EPC API (parsers are tested on fixtures, but the build environment blocks these hosts), a live Outlook sign-in, and the DMG build itself (it needs a Mac).

## Tests

    python3 tests/test_core.py
    python3 tests/test_scrapers.py
    python3 tests/test_v03.py
    python3 run.py --selftest
