"""
AqarSAS Authenticated Extractor
================================
aqarsas.sa uses HttpOnly session cookies (not JWT Bearer tokens).
Login requires a real browser to trigger Vue reactivity + get the cookie.

Authentication strategy — SESSION FILE (same as Paseetah):
    1. Run once to capture session:
         python extractors/aqarsas_extractor.py
       Playwright types the credentials, submits the form, and saves all
       cookies (including HttpOnly) to .aqarsas_session.json
    2. Extractor reads cookies from file on every run; refreshes when expired.

Session file location (override with env var):
    AQARSAS_SESSION_FILE=.aqarsas_session.json   # relative to project root

Credentials (set in .env):
    AQARSAS_EMAIL=your-account@example.invalid
    AQARSAS_PASSWORD=YOUR_PRIVATE_PASSWORD
"""

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

import httpx

from extractors.base import BaseExtractor, ExtractionResult
from extractors.normalizer import (
    extract_number,
    normalize_area,
    normalize_city,
    normalize_date,
)

AQARSAS_BASE    = "https://aqarsas.sa"
AQARSAS_API     = "https://api.aqarsas.sa"
LOGIN_URL       = f"{AQARSAS_BASE}/login"
EXTRACTOR_NAME  = "aqarsas_extractor"
EXTRACTOR_VERSION = "2.0.0"
SESSION_TTL     = 86400   # 24 h

_PROJECT_ROOT   = Path(__file__).parent.parent
_DEFAULT_SESSION = _PROJECT_ROOT / ".aqarsas_session.json"

_session_cache: dict = {"cookies": None, "saved_at": 0.0}


# ── Session helpers ───────────────────────────────────────────────────────────

def _session_file() -> Path:
    env = os.environ.get("AQARSAS_SESSION_FILE", "")
    if env:
        p = Path(env)
        return p if p.is_absolute() else _PROJECT_ROOT / p
    return _DEFAULT_SESSION


def _load_session() -> Optional[list]:
    """Load full cookie list from session file. Returns None if missing/expired."""
    path = _session_file()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        age  = datetime.now(timezone.utc).timestamp() - data.get("saved_at", 0)
        if age > SESSION_TTL:
            print("[aqarsas] Session expired — re-running login")
            return None
        return data.get("cookies")
    except Exception as e:
        print(f"[aqarsas] Could not read session file: {e}")
        return None


def _build_httpx_cookies(cookie_list) -> httpx.Cookies:
    """Build an httpx.Cookies jar from Playwright cookie list or plain dict."""
    jar = httpx.Cookies()
    if isinstance(cookie_list, dict):
        # Old format: {name: value} — set for both domains
        for name, value in cookie_list.items():
            for domain in ("aqarsas.sa", "api.aqarsas.sa", ".aqarsas.sa"):
                try:
                    jar.set(name, value, domain=domain)
                except Exception:
                    pass
    elif isinstance(cookie_list, list):
        # New format: [{name, value, domain, path, ...}]
        for c in cookie_list:
            name   = c.get("name", "")
            value  = c.get("value", "")
            domain = c.get("domain", "aqarsas.sa").lstrip(".")
            if not name:
                continue
            # Set for the original domain AND api subdomain
            for d in {domain, "api.aqarsas.sa", "aqarsas.sa"}:
                try:
                    jar.set(name, value, domain=d)
                except Exception:
                    pass
    return jar


def _save_session(cookies) -> None:
    """Save cookies — accepts list of full cookie dicts or plain name→value dict."""
    path = _session_file()
    path.write_text(json.dumps({
        "cookies":          cookies,   # list of {name, value, domain, path, ...}
        "saved_at":         datetime.now(timezone.utc).timestamp(),
        "saved_at_human":   datetime.now(timezone.utc).isoformat(),
    }, indent=2, ensure_ascii=False))
    count = len(cookies) if isinstance(cookies, list) else len(cookies)
    print(f"[aqarsas] Session saved → {path} ({count} cookies)")


async def _get_session() -> list:
    """Return cookie list, loading from file or running Playwright login."""
    now = datetime.now(timezone.utc).timestamp()
    if _session_cache["cookies"] and (now - _session_cache["saved_at"]) < SESSION_TTL:
        return _session_cache["cookies"]
    cookies = _load_session()
    if cookies:
        _session_cache.update(cookies=cookies, saved_at=now)
        return cookies
    # No valid session — run Playwright login automatically
    cookies = await _playwright_login()
    _save_session(cookies)
    _session_cache.update(cookies=cookies, saved_at=now)
    return cookies


# ── Playwright login ──────────────────────────────────────────────────────────

async def _playwright_login() -> dict:
    """Headless Chromium login for AqarSAS (no CAPTCHA — headless works fine)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "playwright not installed.\n"
            "  pip install playwright --break-system-packages\n"
            "  playwright install chromium"
        )

    email    = os.environ.get("AQARSAS_EMAIL", "")
    password = os.environ.get("AQARSAS_PASSWORD", "")
    if not email or not password:
        raise RuntimeError("AQARSAS_EMAIL / AQARSAS_PASSWORD must be set in .env")

    print(f"[aqarsas] Logging in as {email} ...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="ar-SA",
            viewport={"width": 1280, "height": 800},
        )
        page = await ctx.new_page()

        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=45000)

        # Wait for the login form to appear (Vue needs time to mount)
        try:
            await page.wait_for_selector('input[name="email"]', timeout=15000)
        except Exception:
            # Already logged in? Check URL
            if "/login" not in page.url:
                print(f"[aqarsas] Already on dashboard: {page.url}")
                raw   = await ctx.cookies()
                cdict = {c["name"]: c["value"] for c in raw
                         if "aqarsas" in c.get("domain", "")}
                await browser.close()
                return cdict
            raise

        await page.wait_for_timeout(800)

        # Type credentials — real keyboard events trigger Vue v-model
        await page.locator('input[name="email"]').click()
        await page.keyboard.type(email, delay=60)

        await page.locator('input[type="password"]').click()
        await page.keyboard.type(password, delay=60)

        await page.wait_for_timeout(400)

        # Click submit — try multiple selectors
        try:
            await page.locator('button[type="submit"]').click(timeout=8000)
        except Exception:
            # Fallback: press Enter in the password field
            await page.locator('input[type="password"]').press("Enter")

        # Wait for redirect away from /login
        try:
            await page.wait_for_url(
                lambda url: "/login" not in url,
                timeout=20000,
            )
            print(f"[aqarsas] Login successful → {page.url}")
        except Exception:
            # Check for error message
            try:
                err = await page.locator('[class*=error],[class*=alert]').first.inner_text(timeout=2000)
            except Exception:
                err = "unknown"
            await browser.close()
            raise RuntimeError(f"AqarSAS login failed. Page error: {err}")

        # Grab ALL cookies (including HttpOnly) — keep full objects for domain info
        raw    = await ctx.cookies()
        # Keep cookies for aqarsas domains; also grab all cookies as fallback
        clist  = [c for c in raw if "aqarsas" in c.get("domain", "")]
        if not clist:
            clist = raw   # keep everything if no domain filter match

        await browser.close()

        if not clist:
            raise RuntimeError("Login OK but no cookies found in session")
        return clist   # list of full cookie dicts


# ── Citation builder ──────────────────────────────────────────────────────────

def _citation(source_id: UUID, url: str, snippet: str, locator: str, conf: float) -> dict:
    return {
        "source_id":             str(source_id),
        "source_type":           "url",
        "source_url_or_name":    url,
        "retrieval_timestamp":   datetime.now(timezone.utc).isoformat(),
        "locator":               locator,
        "snippet":               (snippet or "")[:500],
        "extractor_name":        EXTRACTOR_NAME,
        "extractor_version":     EXTRACTOR_VERSION,
        "parse_confidence":      conf,
        "llm_confidence":        None,
        "crosscheck_confidence": None,
        "normalization_notes":   None,
    }


# ── Field mapper ──────────────────────────────────────────────────────────────

def _map_fields(data: dict, source_id: UUID, url: str) -> list[dict]:
    """
    Map AqarSAS landdetails API response to canonical field list.

    Actual API field names (confirmed from live response, March 2026):
      City        → city (Arabic, e.g. "الخرج")
      Hai         → district / neighborhood (Arabic, e.g. "مشرف")
      M566        → plan_number (mukhtatat number, e.g. "560")
      Qitah       → parcel_number (e.g. "165 / 2 / 2")
      Coord       → {lat, lng} coordinates
      Transactions_count → number of transactions
      DealsHistory → list of transactions, each with:
                      Price, Area, Meter_price, GDate, HDate, Degree, Kind
    """
    fields: list[dict] = []

    def add(name: str, raw, norm, conf: float, loc: str):
        if raw is None:
            return
        # Skip zero-value numbers (not meaningful)
        if isinstance(raw, (int, float)) and raw == 0:
            return
        fields.append({
            "field_name":       name,
            "raw_value":        str(raw),
            "normalized_value": str(norm) if norm is not None else str(raw),
            "confidence":       round(conf, 4),
            "citation":         _citation(source_id, url, str(raw), loc, conf),
        })

    # ── City ──────────────────────────────────────────────────────────────────
    # Confirmed field: "City" (Arabic name, e.g. "الخرج")
    for k in ("City", "city", "CityName", "city_name"):
        if k in data and data[k]:
            en, ar = normalize_city(str(data[k]))
            add("city_en", data[k], en,       0.90, f"json.{k}")
            add("city_ar", data[k], data[k],  0.90, f"json.{k}")
            break

    # ── District / Neighborhood ───────────────────────────────────────────────
    # Confirmed field: "Hai" (حي = neighborhood, e.g. "مشرف")
    # Also try legacy names in case other endpoints use them
    for k in ("Hai", "HaiName", "District", "Neighborhood", "district", "neighborhood"):
        if k in data and data[k]:
            add("district", data[k], str(data[k]), 0.88, f"json.{k}")
            break

    # ── Plan / Mukhtatat number ───────────────────────────────────────────────
    # Confirmed field: "M566" (mukhtatat number, the plan/subdivision number)
    for k in ("M566", "PlanNo", "MukhtatatNo", "plan_no", "PlanNumber"):
        if k in data and data[k]:
            add("plan_number", data[k], str(data[k]), 0.88, f"json.{k}")
            break

    # ── Parcel / Qitah number ─────────────────────────────────────────────────
    # Confirmed field: "Qitah" (e.g. "165 / 2 / 2")
    for k in ("Qitah", "QitahNo", "ParcelNo", "parcel_no", "LotNumber"):
        if k in data and data[k]:
            add("parcel_number", data[k], str(data[k]), 0.88, f"json.{k}")
            break

    # ── Coordinates ───────────────────────────────────────────────────────────
    # Confirmed structure: "Coord": {"lat": 0, "lng": 0}  (0 = not available)
    coord = data.get("Coord", {})
    if isinstance(coord, dict):
        lat = coord.get("lat") or coord.get("Lat")
        lng = coord.get("lng") or coord.get("Lng") or coord.get("lon")
        if lat and lat != 0:
            add("latitude",  lat, lat, 0.92, "json.Coord.lat")
        if lng and lng != 0:
            add("longitude", lng, lng, 0.92, "json.Coord.lng")
    # Also try flat lat/lng keys
    for k in ("Lat", "lat", "latitude"):
        if k in data and data[k] and data[k] != 0:
            add("latitude", data[k], data[k], 0.92, f"json.{k}")
            break
    for k in ("Lng", "Lon", "lng", "lon", "longitude"):
        if k in data and data[k] and data[k] != 0:
            add("longitude", data[k], data[k], 0.92, f"json.{k}")
            break

    # ── Transactions count ────────────────────────────────────────────────────
    tx_count = data.get("Transactions_count") or data.get("transactions_count")
    if tx_count:
        add("transactions_count", tx_count, str(tx_count), 0.95, "json.Transactions_count")

    # ── DealsHistory — extract most recent deal's price/area ─────────────────
    # Confirmed structure: list of dicts with Price, Area, Meter_price, GDate, HDate, Degree, Kind
    deals = data.get("DealsHistory") or data.get("deals_history") or data.get("Deals") or []
    if isinstance(deals, list) and deals:
        # Use the most recent deal (last in list) for primary price/area fields
        latest = deals[-1]

        # Area (consistent across deals for same parcel)
        for k in ("Area", "area", "LandArea"):
            if k in latest and latest[k]:
                n = extract_number(str(latest[k]))
                if n:
                    nv, _ = normalize_area(n, "sqm")
                    add("area_sqm",      latest[k], nv,  0.93, f"json.DealsHistory[-1].{k}")
                    add("primary_area_sqm", latest[k], nv, 0.93, f"json.DealsHistory[-1].{k}")
                break

        # Most recent transaction price
        for k in ("Price", "price", "SalePrice"):
            if k in latest and latest[k]:
                n = extract_number(str(latest[k]))
                add("transacted_price", latest[k], n,     0.95, f"json.DealsHistory[-1].{k}")
                add("currency",         "SAR",      "SAR", 0.99, "default.sar")
                break

        # Most recent price per sqm
        for k in ("Meter_price", "meter_price", "MeterPrice", "PricePerMeter"):
            if k in latest and latest[k]:
                n = extract_number(str(latest[k]))
                add("price_per_sqm", latest[k], n, 0.93, f"json.DealsHistory[-1].{k}")
                break

        # Most recent transaction date (Gregorian)
        for k in ("GDate", "gdate", "Date", "date", "TransactionDate"):
            if k in latest and latest[k]:
                norm = normalize_date(str(latest[k]))
                add("transaction_date", latest[k], norm or str(latest[k]), 0.92,
                    f"json.DealsHistory[-1].{k}")
                break

        # Most recent transaction date (Hijri)
        for k in ("HDate", "hdate", "HijriDate"):
            if k in latest and latest[k]:
                add("transaction_date_hijri", latest[k], str(latest[k]), 0.92,
                    f"json.DealsHistory[-1].{k}")
                break

        # Property type / classification from deal
        for k in ("Degree", "degree", "Classification", "classification"):
            if k in latest and latest[k]:
                add("property_classification", latest[k], str(latest[k]), 0.88,
                    f"json.DealsHistory[-1].{k}")
                break
        for k in ("Kind", "kind", "Type", "type", "PropertyType"):
            if k in latest and latest[k]:
                add("property_type", latest[k], str(latest[k]), 0.88,
                    f"json.DealsHistory[-1].{k}")
                break

        # Store all transactions as a JSON summary field
        import json as _json
        add("all_transactions_json",
            _json.dumps(deals, ensure_ascii=False),
            _json.dumps(deals, ensure_ascii=False),
            0.98, "json.DealsHistory")

    # ── Top-level Price/Area fallbacks (for dealdetails endpoint) ─────────────
    for k in ("Price", "SalePrice", "price", "transaction_price", "DealPrice"):
        if k in data and data[k]:
            n = extract_number(str(data[k]))
            if n:
                add("transacted_price", data[k], n,     0.90, f"json.{k}")
                add("currency",         "SAR",   "SAR", 0.99, "default.sar")
            break

    for k in ("Area", "LandArea", "area", "land_area", "Area_size"):
        if k in data and data[k]:
            n = extract_number(str(data[k]))
            if n:
                nv, _ = normalize_area(n, "sqm")
                add("area_sqm", data[k], nv, 0.90, f"json.{k}")
            break

    for k in ("Meter_price", "PricePerMeter", "MeterPrice", "meter_price"):
        if k in data and data[k]:
            n = extract_number(str(data[k]))
            if n:
                add("price_per_sqm", data[k], n, 0.88, f"json.{k}")
            break

    return fields


# ── URL helpers ───────────────────────────────────────────────────────────────

def _listing_id(url: str) -> Optional[str]:
    m = re.search(r"/(\d{4,})", url)
    return m.group(1) if m else None


def _api_endpoints(listing_id: Optional[str], url: str = "") -> list[str]:
    """
    Return API endpoints to try in order.
    Endpoints confirmed via browser network inspection on aqarsas.sa:
      - landdetails/?id={id}  → land/parcel detail page
      - dealssearch/           → search results
      - useractivity/          → authenticated recent activity
    """
    if not listing_id:
        return []

    # Detect URL type to pick the right primary endpoint
    is_deal = "/deals/" in url or "/transactions/" in url

    if is_deal:
        return [
            f"{AQARSAS_API}/dealdetails/?id={listing_id}&src=aqarsasteam",
            f"{AQARSAS_API}/landdetails/?id={listing_id}&src=aqarsasteam",
        ]

    # Default / land URL: landdetails is the confirmed primary endpoint
    return [
        f"{AQARSAS_API}/landdetails/?id={listing_id}&src=aqarsasteam",
        f"{AQARSAS_API}/dealdetails/?id={listing_id}&src=aqarsasteam",
        f"{AQARSAS_API}/nearbydeals/?id={listing_id}",
    ]


# ── Extractor class ───────────────────────────────────────────────────────────

class AqarSASExtractor(BaseExtractor):
    """
    Authenticated extractor for aqarsas.sa.

    Uses Playwright once to login and capture HttpOnly session cookies,
    then httpx with those cookies for all API calls.
    Session is cached for 24 h in .aqarsas_session.json.
    """

    name             = EXTRACTOR_NAME
    version          = EXTRACTOR_VERSION
    RELIABILITY_SCORE = 4   # Official Saudi real estate registry

    def can_handle(self, source_type: str) -> bool:
        return source_type in ("url", "aqarsas")

    async def extract(
        self,
        source_id: UUID,
        content: str = "",
        url: str     = "",
        **kwargs,
    ) -> ExtractionResult:

        lid       = _listing_id(url)
        raw_data  = None
        error_msg = None

        try:
            cookie_list = await _get_session()
            jar         = _build_httpx_cookies(cookie_list)

            headers = {
                "Accept":             "application/json",
                "Origin":             AQARSAS_BASE,
                "Referer":            AQARSAS_BASE + "/",
                "X-Requested-With":   "XMLHttpRequest",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            }

            async with httpx.AsyncClient(
                cookies=jar, headers=headers, follow_redirects=True
            ) as client:
                for endpoint in _api_endpoints(lid, url):
                    try:
                        r = await client.get(endpoint, timeout=15)
                        if r.status_code != 200:
                            continue
                        body = r.json()
                        rc   = body.get("ResponseCode")
                        # ResponseCode 0 = OK, 7 = not authorized, 8 = bad request
                        if rc == 7:
                            print(f"[aqarsas] ResponseCode=7 (not authorized) on {endpoint}")
                            continue
                        if rc == 8:
                            print(f"[aqarsas] ResponseCode=8 (malformed) on {endpoint}")
                            continue
                        # AqarSAS wraps data in Obj, List, data, etc.
                        candidate = (
                            body.get("Obj") or
                            body.get("obj") or
                            body.get("data") or
                            body.get("property") or
                            body.get("transaction") or
                            body.get("listing") or
                            (body if isinstance(body, dict) and rc == 0 else None)
                        )
                        if isinstance(candidate, dict) and candidate:
                            raw_data = candidate
                            print(f"[aqarsas] ✅ Got data from {endpoint.replace(AQARSAS_API,'')}")
                            break
                    except Exception as exc:
                        print(f"[aqarsas] Error on {endpoint}: {exc}")
                        continue

        except Exception as e:
            error_msg = f"AqarSAS extraction error: {e}"

        if raw_data:
            return ExtractionResult(
                source_id        = source_id,
                fields           = _map_fields(raw_data, source_id, url),
                extractor_name   = self.name,
                extractor_version= self.version,
                raw_content      = str(raw_data),
                error            = None,
            )

        return ExtractionResult(
            source_id        = source_id,
            fields           = [],
            extractor_name   = self.name,
            extractor_version= self.version,
            raw_content      = content or "",
            error            = error_msg or f"Could not fetch AqarSAS data for: {url}",
        )


# ── CLI: save session ─────────────────────────────────────────────────────────

async def save_session_interactively() -> None:
    """Force a fresh Playwright login and save the session."""
    import sys
    sys.path.insert(0, str(_PROJECT_ROOT))
    from dotenv import load_dotenv
    load_dotenv()
    cookies = await _playwright_login()
    _save_session(cookies)
    print("✅ AqarSAS session saved.")


if __name__ == "__main__":
    asyncio.run(save_session_interactively())
