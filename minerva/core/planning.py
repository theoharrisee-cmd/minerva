"""Planning document analysis: read officer reports, decision notices, local plan
extracts and return a structured, developer-minded appraisal."""
from __future__ import annotations

import io
import json
import re

from .config import DEFAULT_MODEL

SYSTEM = """You are a senior UK land and planning director at a residential developer-investor.
You read planning documents (officer reports, decision notices, pre-app letters, local plan extracts,
committee minutes, S106 heads of terms) and assess a site for acquisition or development.

Think like the person writing the cheque:
- What must be true for a consent to be granted, and what could stop it?
- Which policies (NPPF, adopted or emerging local plan, design codes, Green Belt and grey belt tests,
  Biodiversity Net Gain, nutrient neutrality, Building Safety Act gateways) bite?
- What will it cost: S106, CIL, affordable housing, abnormals, remediation, off-site works?
- What does nearby precedent say about density, height, mix and tenure?
- How long will it take, and what is the route (delegated, committee, appeal)?
Only state what the documents support. Where a point is inferred, say so. Quote references
(paragraph, policy number, reference) when available. Do not invent facts."""

SCHEMA = """Return ONLY valid JSON with these keys:
{
 "summary": "3 to 5 sentence plain English summary",
 "planning_position": "Consented | Allocated | Pre-app | Refused | None | Unknown",
 "approval_likelihood": 0-100 integer,
 "likelihood_rationale": "why",
 "policy_context": [{"policy": "...", "effect": "supports|constrains|neutral", "note": "...", "source_doc": "document id"}],
 "constraints": [{"item": "...", "severity": "High|Medium|Low", "note": "...", "source_ref": "para or policy", "source_doc": "id from the DOCUMENT header, e.g. a1b2c3d4"}],
 "opportunities": [{"item": "...", "note": "...", "source_ref": "...", "source_doc": "document id"}],
 "precedent": [{"ref": "...", "outcome": "...", "relevance": "...", "source_doc": "document id"}],
 "cost_signals": {"affordable_pct": null, "s106_per_unit": null, "cil_psf": null, "other": "..."},
 "programme_signals": {"months_to_consent": null, "route": "..."},
 "site_flags": {"green_belt": false, "conservation_area": false, "listed": false, "flood_zone": null,
                "contamination": false, "trees": false, "access_issue": false},
 "suggested_units": null,
 "next_steps": ["..."]
}"""


def extract_text(files: list[tuple[str, bytes]]) -> str:
    """files: list of (filename, bytes). Handles PDF and plain text."""
    out = []
    for name, data in files:
        if name.lower().endswith(".pdf"):
            try:
                from pypdf import PdfReader
                r = PdfReader(io.BytesIO(data))
                text = "\n".join((p.extract_text() or "") for p in r.pages)
            except Exception as e:  # pragma: no cover
                text = f"[Could not read {name}: {e}]"
        else:
            text = data.decode("utf-8", errors="ignore")
        out.append(f"\n===== DOCUMENT: {name} =====\n{text}")
    return "\n".join(out)


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def _claude(api_key: str, model: str, system: str, messages: list, max_tokens: int) -> str:
    from . import net
    r = net.post_json("https://api.anthropic.com/v1/messages",
                      {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages},
                      {"x-api-key": api_key, "anthropic-version": "2023-06-01"})
    return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")


def analyse_with_claude(text: str, site: dict, api_key: str, model: str = DEFAULT_MODEL,
                        max_chars: int = 400_000) -> dict:
    ctx = {k: site.get(k) for k in ("name", "address", "la", "site_ha", "units", "asking_price", "strategy") if site.get(k)}
    body = text[:max_chars]
    raw = _claude(api_key, model, SYSTEM, [{"role": "user", "content": f"Site: {json.dumps(ctx)}\n\n{SCHEMA}\n\nDOCUMENTS:\n{body}"}], 4000)
    res = _parse_json(raw)
    res["_engine"] = f"claude:{model}"
    return res


def answer_question(text: str, question: str, api_key: str, model: str = DEFAULT_MODEL, history: list | None = None) -> str:
    msgs = [{"role": "user", "content": f"Planning documents for reference:\n{text[:400_000]}\n\nAnswer using only these documents and cite references."}]
    msgs.append({"role": "assistant", "content": "Understood. Ask your question."})
    for h in history or []:
        msgs.append(h)
    msgs.append({"role": "user", "content": question})
    return _claude(api_key, model, SYSTEM, msgs, 1500)


_KEYWORDS = [
    ("green belt", "High", "Green Belt policy engaged"),
    ("flood zone 3", "High", "Flood Zone 3"),
    ("flood zone 2", "Medium", "Flood Zone 2"),
    ("conservation area", "Medium", "Conservation area"),
    ("listed building", "Medium", "Listed building"),
    ("contaminat", "Medium", "Contamination"),
    ("nutrient neutrality", "High", "Nutrient neutrality"),
    ("biodiversity net gain", "Low", "Biodiversity Net Gain"),
    ("refus", "High", "Refusal referenced"),
    ("highway", "Medium", "Highways matters"),
    ("overlooking", "Medium", "Amenity / overlooking"),
    ("tree preservation", "Low", "Protected trees"),
    ("section 106", "Medium", "S106 obligations"),
    ("community infrastructure levy", "Medium", "CIL"),
    ("affordable housing", "Medium", "Affordable housing requirement"),
]


_BLOCK = re.compile(r"===== DOCUMENT (?:id=([0-9a-f]+): )?([^\n]*?) =====\n")


def analyse_offline(text: str, site: dict) -> dict:
    """Keyword screen used when no API key is set. Deliberately labelled as basic, but every hit links to its document."""
    parts = _BLOCK.split(text)
    docs = [("", "", parts[0])] if len(parts) == 1 else [(parts[i], parts[i + 1], parts[i + 2]) for i in range(1, len(parts) - 2, 3)]
    cons, seen = [], {}
    for did, dname, body in docs:
        low = body.lower()
        for kw, sev, label in _KEYWORDS:
            n = low.count(kw)
            if n and sum(1 for c in cons if c["item"] == label) < 2:
                i = low.index(kw)
                snippet = re.sub(r"\s+", " ", body[max(0, i - 80):i + 160]).strip()
                cons.append({"item": label, "severity": sev, "note": f"...{snippet}...", "source_ref": dname, "source_doc": did})
                seen[kw] = seen.get(kw, 0) + n
    low = text.lower()
    flags = {
        "green_belt": "green belt" in low, "conservation_area": "conservation area" in low,
        "listed": "listed building" in low or "grade ii" in low, "contamination": "contaminat" in low,
        "trees": "tree preservation" in low, "access_issue": "ransom" in low,
        "flood_zone": "3" if "flood zone 3" in low else "2" if "flood zone 2" in low else None,
    }
    pos = "Refused" if re.search(r"\brefus", low) and not re.search(r"granted|allowed", low) else "Consented" if re.search(r"permission (is )?granted|approved subject|appeal (is )?allowed", low) else "Unknown"
    order = {"High": 0, "Medium": 1, "Low": 2}
    cons.sort(key=lambda c: order[c["severity"]])
    return {"summary": "Keyword screen of the documents in the vault. Add an Anthropic API key in Settings for reasoning, cost signals and programme.",
            "planning_position": pos, "approval_likelihood": None, "likelihood_rationale": "", "policy_context": [], "constraints": cons[:24], "opportunities": [],
            "precedent": [], "cost_signals": {}, "programme_signals": {}, "site_flags": flags, "suggested_units": None,
            "next_steps": ["Provide an API key for full analysis"], "_engine": "offline-keywords"}


def analyse(text: str, site: dict, api_key: str | None, model: str = DEFAULT_MODEL) -> dict:
    if api_key:
        try:
            return analyse_with_claude(text, site, api_key, model)
        except Exception as e:
            r = analyse_offline(text, site)
            r["summary"] = f"Claude call failed ({e}). " + r["summary"]
            return r
    return analyse_offline(text, site)


def apply_to_site(site: dict, result: dict) -> dict:
    """Feed extracted signals back into the site record so scoring and red flags update."""
    f = result.get("site_flags") or {}
    for k in ("green_belt", "conservation_area", "listed", "contamination", "trees", "access_issue"):
        if f.get(k):
            site[k] = True
    if f.get("flood_zone") in ("2", "3", 2, 3):
        site["flood_zone"] = str(f["flood_zone"])
    if result.get("planning_position") in ("Consented", "Allocated", "Pre-app", "Refused"):
        site["planning_status"] = result["planning_position"]
    if result.get("suggested_units") and not site.get("units"):
        site["units"] = int(result["suggested_units"])
    return site
