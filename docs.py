"""Per-site document vault: store, classify, extract text, serve."""
from __future__ import annotations

import html as htmllib
import io
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import store

CATS = ["Officer report", "Decision notice", "Consultee response", "S106 / obligations", "Design & access", "Appeal decision",
        "Local plan / policy", "Brochure / particulars", "Survey / technical", "Email", "Other"]
_RULES = [
    ("Appeal decision", r"appeal decision|planning inspectorate|appeal ref|APP/[A-Z]\d{4}"),
    ("Decision notice", r"decision notice|notice of (decision|refusal)|permission granted|refusal notice|refused on"),
    ("Officer report", r"officer'?s? report|delegated report|committee report|pre-?application advice|case officer"),
    ("S106 / obligations", r"section 106|s106|heads of terms|unilateral undertaking|planning obligation"),
    ("Consultee response", r"consultee|consultation response|highways|lead local flood|environment agency|natural england|historic england|thames water|conservation officer|environmental health"),
    ("Design & access", r"design (and|&) access"),
    ("Local plan / policy", r"local plan|core strategy|neighbourhood plan|nppf|policy [a-z]{1,3}\d"),
    ("Survey / technical", r"survey|flood risk assessment|transport assessment|phase [12]|ecolog|arboricultur|structural|geotechnical"),
    ("Brochure / particulars", r"particulars|brochure|guide price|informal tender|for sale"),
]


def root(site_id: str) -> Path:
    d = store.DATA / "docs" / re.sub(r"[^A-Za-z0-9_.-]", "_", site_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def classify(name: str, text: str = "") -> str:
    hay = f"{name} {text[:2500]}".lower().replace("_", " ").replace("-", " ")
    for cat, rx in _RULES:
        if re.search(rx, hay, re.I):
            return cat
    return "Other"


def extract_text(name: str, data: bytes) -> str:
    low = name.lower()
    if low.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        except Exception:
            return ""
    if low.endswith((".html", ".htm")):
        t = re.sub(r"(?is)<(script|style).*?</\1>", " ", data.decode("utf-8", "ignore"))
        return htmllib.unescape(re.sub(r"<[^>]+>", " ", t))
    if low.endswith((".txt", ".md", ".csv", ".eml")):
        return data.decode("utf-8", "ignore")
    return ""


def add(site: dict, name: str, data: bytes, *, category: str | None = None, source: str = "upload", date: str | None = None, text: str | None = None) -> dict:
    name = re.sub(r"[^A-Za-z0-9 _.,()&'-]", "_", Path(name).name) or "document"
    d = root(site["id"])
    target = d / name
    n = 1
    while target.exists():
        target = d / f"{target.stem}_{n}{target.suffix}"
        n += 1
    target.write_bytes(data)
    text = text if text is not None else extract_text(target.name, data)
    (d / (target.name + ".txt")).write_text(text)
    rec = {"id": uuid.uuid4().hex[:8], "name": target.name, "category": category or classify(target.name, text), "size": len(data), "source": source,
           "added": datetime.now(timezone.utc).isoformat(timespec="minutes"), "date": date, "chars": len(text),
           "kind": "pdf" if target.suffix.lower() == ".pdf" else "html" if target.suffix.lower() in (".html", ".htm") else "text" if target.suffix.lower() in (".txt", ".md", ".eml") else "file"}
    site.setdefault("docs", []).append(rec)
    return rec


def path_of(site: dict, doc: dict) -> Path:
    return root(site["id"]) / doc["name"]


def text_of(site: dict, doc: dict) -> str:
    p = root(site["id"]) / (doc["name"] + ".txt")
    return p.read_text() if p.exists() else ""


def all_text(site: dict, only: list[str] | None = None) -> str:
    out = []
    for d in site.get("docs", []):
        if only and d["id"] not in only:
            continue
        out.append(f"\n===== DOCUMENT id={d['id']}: {d['name']} [{d['category']}] =====\n{text_of(site, d)}")
    return "\n".join(out)


def remove(site: dict, doc_id: str) -> None:
    for d in list(site.get("docs", [])):
        if d["id"] == doc_id:
            for p in (path_of(site, d), root(site["id"]) / (d["name"] + ".txt")):
                p.unlink(missing_ok=True)
            site["docs"].remove(d)


def seed_demo(site: dict) -> None:
    """Copy bundled demo PDFs into the vault and resolve doc keys used by planning_history and consultees."""
    from . import demo_deals as dd
    keymap = {}
    site["docs"] = []
    for key in site.pop("_doc_keys", []):
        deal, fn, cat, date, title, _ = dd.DOCS[key]
        src = dd.DIR / deal / fn
        if not src.exists():
            continue
        rec = add(site, fn, src.read_bytes(), category=cat, source="demo", date=date, text=(dd.DIR / deal / (fn + ".txt")).read_text())
        rec["title"] = title
        keymap[key] = rec["id"]
    for h in site.get("planning_history", []):
        h["docs"] = [keymap[k] for k in h.get("docs", []) if k in keymap]
    for c in site.get("consultees", []):
        c["doc"] = keymap.get(c.get("doc"))
