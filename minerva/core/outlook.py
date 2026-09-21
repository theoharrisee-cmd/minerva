"""Outlook / Microsoft 365 mailbox connection through Microsoft Graph (read-only).

Sign-in uses the OAuth device-code flow: no client secret and no redirect URI, so it suits a desktop app.
One-off setup (about 3 minutes): register an app in Microsoft Entra (portal.azure.com > App registrations),
set 'Allow public client flows' to Yes, add delegated permissions Mail.Read and User.Read, and paste the
Application (client) ID into Minerva. Scopes requested: Mail.Read offline_access User.Read.
Nothing is ever sent, moved or deleted. A labelled demo mailbox is included so the workflow can be seen without an account."""
from __future__ import annotations

import base64
import json
import re
import time
from datetime import datetime, timedelta, timezone

from . import net, store

SCOPES = "Mail.Read offline_access User.Read"
GRAPH = "https://graph.microsoft.com/v1.0"
TOKEN_FILE = store.DATA / "outlook.json"

DEAL_WORDS = ["guide price", "for sale", "offers", "tender", "site", "land", "development", "planning", "consent", "s106", "units", "apartments",
              "dwellings", "acres", "hectares", "off-market", "off market", "opportunity", "brochure", "particulars", "hectare", "sq ft", "conditional"]
NOISE_WORDS = ["unsubscribe", "newsletter", "webinar", "invoice", "receipt", "out of office", "password"]


def _now() -> float:
    return time.time()


def load() -> dict:
    try:
        return json.loads(TOKEN_FILE.read_text())
    except Exception:
        return {}


def save(d: dict) -> None:
    TOKEN_FILE.write_text(json.dumps(d))
    try:
        TOKEN_FILE.chmod(0o600)
    except Exception:
        pass


def status() -> dict:
    d = load()
    return {"client_id": d.get("client_id", ""), "tenant": d.get("tenant", "common"), "connected": bool(d.get("refresh_token")),
            "account": d.get("account"), "pending": bool(d.get("device") and d["device"].get("expires_at", 0) > _now()),
            "device": {k: d["device"][k] for k in ("user_code", "verification_uri", "expires_at")} if d.get("device") and d["device"].get("expires_at", 0) > _now() else None}


def configure(client_id: str, tenant: str = "common") -> None:
    d = load()
    d.update(client_id=client_id.strip(), tenant=(tenant or "common").strip())
    save(d)


def start_device_flow() -> dict:
    d = load()
    if not d.get("client_id"):
        raise ValueError("Enter your Azure application (client) ID first")
    r = net.post_form(f"https://login.microsoftonline.com/{d.get('tenant','common')}/oauth2/v2.0/devicecode", {"client_id": d["client_id"], "scope": SCOPES})
    if "device_code" not in r:
        raise RuntimeError(r.get("error_description") or r.get("error") or "Microsoft did not return a device code")
    d["device"] = {"device_code": r["device_code"], "user_code": r["user_code"], "verification_uri": r.get("verification_uri", "https://microsoft.com/devicelogin"),
                   "interval": r.get("interval", 5), "expires_at": _now() + int(r.get("expires_in", 900))}
    save(d)
    return status()


def poll_device_flow() -> dict:
    """Call repeatedly (the UI does so every few seconds) until connected."""
    d = load()
    dev = d.get("device")
    if not dev:
        return status()
    if dev["expires_at"] < _now():
        d.pop("device", None)
        save(d)
        return {**status(), "error": "The sign-in code expired. Start again."}
    r = net.post_form(f"https://login.microsoftonline.com/{d.get('tenant','common')}/oauth2/v2.0/token",
                      {"grant_type": "urn:ietf:params:oauth:grant-type:device_code", "client_id": d["client_id"], "device_code": dev["device_code"]})
    if "access_token" in r:
        d.pop("device", None)
        _store_tokens(d, r)
        try:
            me = _get(d["access_token"], "/me?$select=displayName,mail,userPrincipalName")
            d["account"] = me.get("mail") or me.get("userPrincipalName")
        except Exception:
            pass
        save(d)
        return status()
    err = r.get("error")
    if err in ("authorization_pending", "slow_down"):
        return status()
    d.pop("device", None)
    save(d)
    return {**status(), "error": r.get("error_description", err or "Sign-in failed")[:200]}


def _store_tokens(d: dict, r: dict) -> None:
    d["access_token"] = r["access_token"]
    d["expires_at"] = _now() + int(r.get("expires_in", 3600)) - 60
    if r.get("refresh_token"):
        d["refresh_token"] = r["refresh_token"]


def _token() -> str:
    d = load()
    if d.get("access_token") and d.get("expires_at", 0) > _now():
        return d["access_token"]
    if not d.get("refresh_token"):
        raise PermissionError("Not connected to Outlook")
    r = net.post_form(f"https://login.microsoftonline.com/{d.get('tenant','common')}/oauth2/v2.0/token",
                      {"grant_type": "refresh_token", "client_id": d["client_id"], "refresh_token": d["refresh_token"], "scope": SCOPES})
    if "access_token" not in r:
        raise PermissionError(r.get("error_description", "Outlook sign-in has expired. Connect again."))
    _store_tokens(d, r)
    save(d)
    return d["access_token"]


def disconnect() -> None:
    d = load()
    for k in ("access_token", "refresh_token", "expires_at", "account", "device"):
        d.pop(k, None)
    save(d)


def _get(tok: str, path: str, prefer_text: bool = False):
    h = {"Authorization": f"Bearer {tok}"}
    if prefer_text:
        h["Prefer"] = 'outlook.body-content-type="text"'
    return net.api_get(GRAPH + path, h)


def deal_score(subject: str, preview: str, has_att: bool = False) -> int:
    t = f"{subject} {preview}".lower()
    s = sum(8 for w in DEAL_WORDS if w in t) + (10 if has_att else 0) - sum(20 for w in NOISE_WORDS if w in t)
    if re.search(r"£\s?\d", t):
        s += 12
    if re.search(r"\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b", f"{subject} {preview}"):
        s += 8
    return max(0, min(100, s))


def list_messages(days: int = 30, top: int = 50, query: str = "") -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = (f"/me/mailFolders/inbox/messages?$top={min(top,100)}&$orderby=receivedDateTime desc&$filter=receivedDateTime ge {since}"
            "&$select=id,subject,from,receivedDateTime,bodyPreview,hasAttachments").replace(" ", "%20")
    js = _get(_token(), path)
    out = []
    for m in js.get("value", []):
        frm = (m.get("from") or {}).get("emailAddress") or {}
        row = {"id": m["id"], "subject": m.get("subject") or "(no subject)", "from": f"{frm.get('name','')} <{frm.get('address','')}>".strip(), "date": m.get("receivedDateTime"),
               "preview": m.get("bodyPreview", "")[:300], "has_attachments": bool(m.get("hasAttachments"))}
        row["score"] = deal_score(row["subject"], row["preview"], row["has_attachments"])
        if not query or query.lower() in f"{row['subject']} {row['preview']} {row['from']}".lower():
            out.append(row)
    return out


def get_message(mid: str) -> dict:
    tok = _token()
    m = _get(tok, f"/me/messages/{mid}?$select=subject,from,receivedDateTime,body", prefer_text=True)
    frm = (m.get("from") or {}).get("emailAddress") or {}
    atts = []
    try:
        for a in _get(tok, f"/me/messages/{mid}/attachments?$select=name,contentType,size,contentBytes").get("value", []):
            if a.get("contentBytes") and a.get("size", 0) < 25_000_000 and re.search(r"\.(pdf|txt|html?|eml)$", a.get("name", ""), re.I):
                atts.append((a["name"], base64.b64decode(a["contentBytes"])))
    except Exception:
        pass
    return {"subject": m.get("subject", ""), "from": f"{frm.get('name','')} <{frm.get('address','')}>", "date": m.get("receivedDateTime", ""),
            "text": (m.get("body") or {}).get("content", ""), "attachments": atts}


# ------------------------------------------------------------------ demo mailbox (entirely fictional)
DEMO_MAILBOX = [
    {"id": "demo-1", "subject": "Off-market: Land at Ashby Road, Loughborough. 64 plots, outline consent",
     "from": "Priya Nair <priya.nair@harcourtvane.example.com>", "date": "2026-09-18T09:42:00Z", "has_attachments": True,
     "text": ("Dear Harry,\n\nWe are instructed by Ashby Farms Ltd to bring to the market, on an off-market basis, land at Ashby Road, Loughborough LE11 3TH.\n\n"
              "The site extends to 2.9 hectares (7.2 acres) of arable land on the southern edge of Loughborough. Outline planning permission (ref P/25/1187/2) was granted on 3 July 2026 for up to 64 dwellings "
              "with all matters reserved except access. The Section 106 agreement is complete: 30% affordable housing (19 units), £4,300 per dwelling towards education and healthcare, and a bus stop contribution.\n\n"
              "Indicative mix: 12 x 2 bed houses (830 sq ft, c.£292,000), 34 x 3 bed houses (1,050 sq ft, c.£368,000), 18 x 4 bed houses (1,350 sq ft, c.£478,000).\n\n"
              "Guide price: £3,950,000 (subject to contract). Offers by 12 noon on Friday 23 October 2026. Vendor prefers unconditional or conditional on reserved matters only. "
              "The vendor's cost consultant has prepared a build cost budget of £9,800,000 for 86,000 sq ft GIA (houses, externals and abnormals included). There is a 20m wide gas main easement on the northern boundary; the ecology report records a small badger sett that will need a licence.\n\n"
              "Technical reports are in the attached brochure. Please call me on 020 7946 0155 to discuss.\n\nKind regards,\nPriya Nair\nAssociate Director, Land\nHarcourt & Vane LLP (fictional)"),
     "attachments": []},
    {"id": "demo-2", "subject": "Kingsfield Yard, Hunslet: informal tender deadline reminder", "from": "Anthony Marsh <anthony.marsh@harcourtvane.example.com>",
     "date": "2026-09-16T14:05:00Z", "has_attachments": False, "text": "Harry, a reminder that bids for Kingsfield Yard close at 12 noon on 16 October 2026. The S106 has now been signed and the data room has been updated with the Phase 2 report. Guide remains £3,400,000. Regards, Anthony", "attachments": []},
    {"id": "demo-3", "subject": "Quarterly newsletter: UK residential outlook", "from": "Research <research@bigagent.example.com>", "date": "2026-09-15T08:00:00Z", "has_attachments": False,
     "text": "Our latest newsletter is attached. To unsubscribe click here.", "attachments": []},
    {"id": "demo-4", "subject": "Site for sale: former depot, Nottingham NG7. 0.6 ha, PP for 38 flats", "from": "Owen Bright <owen@midlandsland.example.com>", "date": "2026-09-12T16:20:00Z",
     "has_attachments": False,
     "text": ("Hi Harry, quick one. Former council depot at Lenton Boulevard, Nottingham NG7 2BY, 0.6 hectares. Full planning permission for 38 apartments (23/00921/PFUL3) granted March 2026, no S106 beyond a £52,000 open space payment. "
              "Asking £1,900,000. Possible contamination from old fuel tanks, no Phase 2 yet. Bids by 30 October 2026. Call 020 7946 0177. Owen (fictional agent)"), "attachments": []},
    {"id": "demo-5", "subject": "Lunch on Thursday?", "from": "Sam <sam@friends.example.com>", "date": "2026-09-11T10:01:00Z", "has_attachments": False, "text": "Are we still on for Thursday?", "attachments": []},
]


def demo_list() -> list[dict]:
    out = []
    for m in DEMO_MAILBOX:
        r = {k: m[k] for k in ("id", "subject", "from", "date", "has_attachments")}
        r["preview"] = re.sub(r"\s+", " ", m["text"])[:300]
        r["score"] = deal_score(r["subject"], m["text"][:600], r["has_attachments"])
        r["demo"] = True
        out.append(r)
    return out


def demo_get(mid: str) -> dict:
    m = next((x for x in DEMO_MAILBOX if x["id"] == mid), None)
    if not m:
        raise KeyError(mid)
    return {k: m[k] for k in ("subject", "from", "date", "text", "attachments")}
