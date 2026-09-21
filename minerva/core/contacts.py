"""Agent contact details: firm-level pages (verified where possible), listing-page extraction and enquiry drafts."""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin

from . import net

# Firm level. Only details actually seen on the firm's public site on 21 Sep 2026 are given as phone/email.
FIRM_CONTACTS = {
    "hamptons": dict(firm="Hamptons", phone="+44 (0)20 3930 8917", email="enquiries@hamptons.co.uk", team="Land and New Homes team",
                     team_phone="+44 (0)20 3582 0376", team_email="landandnewhomes@hamptons.co.uk", url="https://www.hamptons.co.uk/contact-us", verified=True),
    "jacksonstops": dict(firm="Jackson-Stops", url="https://www.jackson-stops.co.uk/contact-us", team="Land services", team_url="https://www.jackson-stops.co.uk/land-sales-acquisitions",
                         note="Contact form and branch finder; no central number published on the contact page", verified=True),
    "knightfrank": dict(firm="Knight Frank", url="https://www.knightfrank.co.uk/contact-us", note="Contact form; use the office finder for numbers", verified=True),
    "struttandparker": dict(firm="Strutt & Parker", url="https://www.struttandparker.com/contact-us", note="Contact form; see Our Offices for numbers", verified=True),
    "chestertons": dict(firm="Chestertons", url="https://www.chestertons.co.uk/contact-us", address="5th Floor West, The Lantern Building, 75 Hampstead Road, London NW1 2PL", verified=True),
    "landsale": dict(firm="LandSale", url="https://www.landsale.co.uk/contact", note="Enquire through the listing; support hours Mon to Fri 07:00 to 16:00", verified=True),
    "savills": dict(firm="Savills", url="https://www.savills.co.uk/contact-us.aspx", note="Site blocked automated checks; use the contact page", verified=False),
    "carterjonas": dict(firm="Carter Jonas", url="https://www.carterjonas.co.uk/contact-us", note="Confirm contact page", verified=False),
    "winkworth": dict(firm="Winkworth", url="https://www.winkworth.co.uk/", note="Confirm contact page", verified=False),
    "fineandcountry": dict(firm="Fine & Country", url="https://www.fineandcountry.co.uk/", note="Confirm contact page", verified=False),
    "onthemarket": dict(firm="OnTheMarket", url="https://www.onthemarket.com/", note="Enquiries go to the listing agent shown on the listing page", verified=False),
}

PHONE = re.compile(r"(?:\+44\s?\(0\)\s?|\+44\s?|\(?0)(?:\d[\s()-]?){9,10}\d")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def firm_contact(site: dict) -> dict:
    return FIRM_CONTACTS.get(site.get("source_id", ""), {})


def _clean_phone(p: str) -> str:
    return re.sub(r"\s+", " ", p).strip()


def extract_from_html(html: str, base: str = "") -> dict:
    out: dict = {}
    for blk in re.findall(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html):
        try:
            data = json.loads(blk.strip())
        except Exception:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                if d.get("@type") in ("RealEstateAgent", "LocalBusiness", "Organization", "Person") or "telephone" in d:
                    for k, tgt in (("name", "name"), ("telephone", "phone"), ("email", "email"), ("url", "url")):
                        if d.get(k) and tgt not in out and isinstance(d[k], str):
                            out[tgt] = d[k]
                stack.extend(v for v in d.values() if isinstance(v, (dict, list)))
    tel = re.findall(r'href=["\']tel:([^"\']+)["\']', html)
    if tel and "phone" not in out:
        out["phone"] = _clean_phone(tel[0].replace("%20", " "))
    mail = re.findall(r'href=["\']mailto:([^"\'?]+)', html)
    if mail and "email" not in out:
        out["email"] = mail[0]
    if "phone" not in out:
        m = PHONE.search(re.sub(r"<[^>]+>", " ", html))
        if m:
            out["phone"] = _clean_phone(m.group(0))
    m = re.search(r'(?is)(?:branch|office|negotiator|contact)[^<]{0,20}[:>]\s*([A-Z][A-Za-z&\' -]{3,50})', html)
    if m:
        out.setdefault("branch", m.group(1).strip())
    return out


def enrich(site: dict) -> dict:
    """Try to pull agent name, phone and email from the listing page; merge with firm-level details."""
    agent = dict(site.get("agent") or {})
    fc = firm_contact(site)
    agent.setdefault("firm", fc.get("firm") or site.get("source"))
    found = {}
    err = None
    if site.get("url") and site["url"].startswith("http") and not site.get("snapshot_only"):
        try:
            html = net.fetch(site["url"], ttl=24 * 3600)
            found = extract_from_html(html, site["url"])
        except Exception as e:
            err = str(e)
    for k, v in found.items():
        if v and not agent.get(k):
            agent[k] = v
    if fc:
        agent.setdefault("firm_page", fc.get("url"))
        for k_src, k_dst in (("team_phone", "team_phone"), ("team_email", "team_email"), ("phone", "firm_phone"), ("email", "firm_email"), ("team", "team")):
            if fc.get(k_src):
                agent.setdefault(k_dst, fc[k_src])
    agent["enriched"] = True
    agent["enrich_error"] = err
    site["agent"] = agent
    return agent


def enquiry_draft(site: dict, investor: dict | None = None) -> dict:
    a = site.get("agent") or {}
    inv = investor or {}
    who = a.get("name") or "the team"
    name = site.get("name", "the property")
    price = f" (guide £{site['asking_price']:,.0f})" if site.get("asking_price") else ""
    me = inv.get("name") or "[your name]"
    firm = f" of {inv['firm']}" if inv.get("firm") else ""
    body = (f"Dear {who.split()[0] if a.get('name') else 'all'},\n\n"
            f"I am writing about {name}{price}. {me}{firm} is an active buyer of sites of this type"
            + (f" with capital available for opportunities from £{inv['min_deal']:.0f}m to £{inv['max_deal']:.0f}m" if inv.get("max_deal") else "") + ".\n\n"
            "Could you please share, where available:\n"
            "1. The planning history and any pre-application correspondence, including consultee responses\n"
            "2. Technical reports (ground conditions, flood risk, ecology, transport)\n"
            "3. The vendor's timetable and preferred structure, including openness to conditional offers\n"
            "4. Details of the proposed unit mix and any viability assessment\n\n"
            "I would welcome a call this week.\n\nKind regards,\n" + me)
    fc = firm_contact(site)
    to = a.get("email") or a.get("team_email") or fc.get("team_email") or a.get("firm_email") or fc.get("email") or ""
    return {"to": to, "subject": f"Enquiry: {name}", "body": body}
