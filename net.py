"""Polite HTTP: robots.txt aware, rate limited, disk cached. Standard library only."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

from . import store

DEFAULT_UA = "Mozilla/5.0 (compatible; MinervaResearch/0.2; personal property research)"
_last_hit: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}


class Blocked(Exception):
    pass


def _cache_path(url: str) -> Path:
    d = store.DATA / "cache"
    d.mkdir(exist_ok=True)
    return d / (hashlib.sha1(url.encode()).hexdigest() + ".json")


def robots_allowed(url: str, ua: str = DEFAULT_UA) -> bool:
    p = urllib.parse.urlparse(url)
    host = f"{p.scheme}://{p.netloc}"
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            req = urllib.request.Request(host + "/robots.txt", headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=10) as r:
                rp.parse(r.read().decode("utf-8", "ignore").splitlines())
            _robots[host] = rp
        except urllib.error.HTTPError as e:
            # 4xx means no robots file: everything allowed. 5xx: be cautious.
            _robots[host] = None if 400 <= e.code < 500 else False  # type: ignore
        except Exception:
            _robots[host] = None
    rp = _robots[host]
    if rp is False:
        return False
    return True if rp is None else rp.can_fetch("*", url)


def fetch(url: str, *, ua: str = DEFAULT_UA, delay: float = 1.5, ttl: int = 6 * 3600,
          respect_robots: bool = True, timeout: int = 20, use_cache: bool = True) -> str:
    """Return page text. Raises Blocked(reason) or urllib errors with a readable message."""
    cp = _cache_path(url)
    if use_cache and cp.exists() and time.time() - cp.stat().st_mtime < ttl:
        return json.loads(cp.read_text())["body"]
    if respect_robots and not robots_allowed(url, ua):
        raise Blocked("robots.txt disallows this page")
    host = urllib.parse.urlparse(url).netloc
    wait = delay - (time.time() - _last_hit.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/json",
                                               "Accept-Language": "en-GB,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode(r.headers.get_content_charset() or "utf-8", "ignore")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429, 503):
            raise Blocked(f"blocked by the site (HTTP {e.code})")
        if e.code == 404:
            raise Blocked("page not found (HTTP 404): check the search URL in Settings")
        raise
    low = body[:4000].lower()
    if any(x in low for x in ("captcha", "access denied", "are you a robot", "verify you are human", "cf-chl")):
        raise Blocked("bot protection challenge")
    cp.write_text(json.dumps({"url": url, "body": body}))
    return body


def get_json(url: str, timeout: int = 10):
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def post_json(url: str, payload: dict, headers: dict, timeout: int = 180):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:300]}")


def post_form(url: str, fields: dict, timeout: int = 30):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try:
            return json.loads(body)  # OAuth errors (authorization_pending etc.) arrive as JSON
        except Exception:
            raise RuntimeError(f"HTTP {e.code}: {body[:300]}")


def api_get(url: str, headers: dict | None = None, timeout: int = 30, cache_ttl: int = 0):
    """Authenticated GET returning parsed JSON (Graph, EPC, SPARQL). Optional disk cache."""
    cp = _cache_path(url)
    if cache_ttl and cp.exists() and time.time() - cp.stat().st_mtime < cache_ttl:
        return json.loads(cp.read_text())["body"]
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA, "Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}")
    if cache_ttl:
        cp.write_text(json.dumps({"url": url, "body": data}))
    return data
