"""Persistence in the user's application-support folder (JSON files)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _home() -> Path:
    if os.environ.get("MINERVA_HOME"):
        return Path(os.environ["MINERVA_HOME"])
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Minerva"
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA", Path.home())) / "Minerva"
    return Path.home() / ".minerva"


DATA = _home()
DATA.mkdir(parents=True, exist_ok=True)
SITES = DATA / "sites.json"
PROFILE = DATA / "profile.json"


def _read(p: Path, default):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def load_sites() -> list[dict]:
    if SITES.exists():
        return _read(SITES, [])
    from .sample import SAMPLE_SITES
    from .scrapers import load_snapshot
    return rich_demo_deals() + [dict(s, demo=True) for s in SAMPLE_SITES] + load_snapshot()


def rich_demo_deals() -> list[dict]:
    """Fully populated fictional deals (with PDFs copied into the document vault)."""
    import copy
    from . import demo_deals, docs
    out = []
    for deal in demo_deals.DEALS:
        d = copy.deepcopy(deal)
        d["_doc_keys"] = d.pop("docs", [])
        docs.seed_demo(d)
        out.append(d)
    return out


def save_sites(sites: list[dict]) -> None:
    SITES.write_text(json.dumps(sites, indent=1, default=str))


def load_profile() -> dict:
    return _read(PROFILE, {})


def save_profile(profile: dict) -> None:
    PROFILE.write_text(json.dumps(profile, indent=1))
