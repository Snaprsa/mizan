"""
Paseetah Authenticated Extractor
==================================
Paseetah (paseetah.com) uses Laravel Sanctum + reCAPTCHA v2 checkbox on login.
reCAPTCHA v2 requires a human tick — it cannot be automated headlessly.

Authentication strategy — SESSION FILE:
    1. User logs in once manually in their browser
    2. Run:  python extractors/paseetah_extractor.py --save-session
       (or call save_session_from_browser() after manual login)
    3. Session cookies are saved to PASEETAH_SESSION_FILE (default: .paseetah_session.json)
    4. Extractor reads the session file on every run; re-prompts when expired

Session file location (override with env var):
    PASEETAH_SESSION_FILE=.paseetah_session.json   # relative to project root

Usage:
    # Save session from Chrome cookies (run once after manual login):
    python -c "
    from extractors.paseetah_extractor import save_session_interactively
    import asyncio; asyncio.run(save_session_interactively())
    "

    # Use in extraction pipeline:
    extractor = PaseetahExtractor()
    result = await extractor.extract(source_id=..., url="https://paseetah.com/...")
"""

import asyncio
import json
import os
import re
import sys
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

PASEETAH_BASE = "https://paseetah.com"
PASEETAH_API  = "https://paseetah.com/api"   # confirmed from JS bundle (Mf constant)
EXTRACTOR_NAME = "paseetah_extractor"
EXTRACTOR_VERSION = "1.3.0"

# How many seconds before a cached session is considered stale
SESSION_TTL = 86400  # 24 hours

# Project root — session file lives here
_PROJECT_ROOT = Path(__file__).parent.parent
_DEFAULT_SESSION_FILE = _PROJECT_ROOT / ".paseetah_session.json"

# In-memory session cache
_session_cache: dict = {"cookies": None, "saved_at": 0.0}


def _session_file_path() -> Path:
    env_path = os.environ.get("PASEETAH_SESSION_FILE", "")
    if env_path:
        p = Path(env_path)
        return p if p.is_absolute() else _PROJECT_ROOT / p
    return _DEFAULT_SESSION_FILE


def load_session_from_file() -> Optional[dict]:
    """Load cookies from the session file. Returns None if missing or expired."""
    path = _session_file_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        saved_at = data.get("saved_at", 0)
        if (datetime.now(timezone.utc).timestamp() - saved_at) > SESSION_TTL:
            print("[paseetah] Session file expired — please re-run save_session_interactively()")
            return None
        return data.get("cookies")
    except Exception as e:
        print(f"[paseetah] Could not read session file: {e}")
        return None


def save_session_to_file(cookies: dict) -> None:
    """Persist cookies to the session file."""
    path = _session_file_path()
    data = {
        "cookies": cookies,
        "saved_at": datetime.now(timezone.utc).timestamp(),
        "saved_at_human": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[paseetah] Session saved to: {path}")


async def save_session_from_cookies(cookies: dict) -> None:
    """
    Accept a cookies dict (from browser) and persist it.
    Call this after the user has logged in manually.
    """
    save_session_to_file(cookies)
    _session_cache["cookies"] = cookies
    _session_cache["saved_at"] = datetime.now(timezone.utc).timestamp()
    print(f"[paseetah] ✅ Session saved. {len(cookies)} cookies stored.")


async def save_session_interactively() -> None:
    """
    Prompt the user to log in at paseetah.com in their browser, then
    extract and save the session cookies via browser automation.

    Requires playwright: pip install playwright && playwright install chromium
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("playwright not installed: pip install playwright && playwright install chromium")
        return

    print("\n" + "="*60)
    print("Paseetah Manual Login — Session Capture")
    print("="*60)
    print("A browser window will open. Please:")
    print("  1. Tick the reCAPTCHA checkbox ('أنا لست برنامج روبوت')")
    print("  2. Click 'تسجيل الدخول' (Login)")
    print("  3. Wait for the dashboard to load")
    print("  4. Come back here — session will be saved automatically")
    print("="*60)

    email = os.environ.get("PASEETAH_EMAIL", "")
    password = os.environ.get("PASEETAH_PASSWORD", "")

    async with async_playwright() as p:
        # Use non-headless (visible) browser so user can tick reCAPTCHA
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="ar-SA",
        )
        page = await context.new_page()
        await page.goto(f"{PASEETAH_BASE}/login", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1500)

        # Pre-fill credentials
        if email:
            try:
                await page.locator('input[type="email"]').fill(email)
            except Exception:
                pass
        if password:
            try:
                await page.locator('input[type="password"]').fill(password)
            except Exception:
                pass

        print("\n→ Browser window opened and credentials pre-filled.")
        print("→ Please tick the reCAPTCHA, then click Login.")
        print("→ Waiting for you to complete login...")

        # Wait up to 3 minutes for user to complete login
        try:
            await page.wait_for_url(
                lambda url: "/login" not in url and "/register" not in url,
                timeout=180000,
            )
            print("→ Login successful! Capturing session...")
        except Exception:
            print("→ Timed out waiting for login. Saving whatever cookies exist...")

        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies if c.get("domain", "").endswith("paseetah.com")}
        await browser.close()

        if cookie_dict:
            save_session_to_file(cookie_dict)
            print(f"✅ Session saved! {len(cookie_dict)} cookies: {list(cookie_dict.keys())}")
        else:
            print("❌ No Paseetah cookies found — login may not have completed.")


async def _get_session_cookies() -> dict:
    """Return session cookies, loading from file or cache."""
    # 1. Try in-memory cache
    now = datetime.now(timezone.utc).timestamp()
    if _session_cache["cookies"] and (now - _session_cache["saved_at"]) < SESSION_TTL:
        return _session_cache["cookies"]

    # 2. Try file
    cookies = load_session_from_file()
    if cookies:
        _session_cache["cookies"] = cookies
        _session_cache["saved_at"] = now
        return cookies

    # 3. No session available
    raise RuntimeError(
        "No Paseetah session found. Run once to authenticate:\n"
        "  python -c \"from extractors.paseetah_extractor import save_session_interactively; "
        "import asyncio; asyncio.run(save_session_interactively())\"\n"
        f"Session file location: {_session_file_path()}"
    )


def _build_citation(source_id: UUID, url: str, snippet: str, locator: str, confidence: float) -> dict:
    return {
        "source_id": str(source_id),
        "source_type": "url",
        "source_url_or_name": url,
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "locator": locator,
        "snippet": snippet[:500] if snippet else None,
        "extractor_name": EXTRACTOR_NAME,
        "extractor_version": EXTRACTOR_VERSION,
        "parse_confidence": confidence,
        "llm_confidence": None,
        "crosscheck_confidence": None,
        "normalization_notes": None,
    }


def _parse_listing_id(url: str) -> Optional[str]:
    m = re.search(r"/(\d{3,})", url)
    return m.group(1) if m else None


def _is_share_url(url: str) -> bool:
    """Return True if the URL is a Paseetah share link (e.g. /share/{token})."""
    return bool(re.search(r"/share/[A-Za-z0-9]+", url))


async def _resolve_share_url(
    url: str,
    cookie_jar: "httpx.Cookies",
) -> tuple[Optional[str], str, Optional[str], Optional[str]]:
    """
    Follow a /share/{token} redirect and extract the real parcel_id + type.

    The Paseetah server returns a Location header ONLY when the request is made
    with an HTML Accept header (not JSON).  We therefore use a dedicated
    short-lived client with Accept: text/html for this step.

    Returns (parcel_id, parcel_type, lat, lng).
    """
    import urllib.parse
    html_headers = {
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Referer": PASEETAH_BASE + "/",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }
    try:
        async with httpx.AsyncClient(
            cookies=cookie_jar, headers=html_headers,
            follow_redirects=False, timeout=12,
        ) as html_client:
            resp = await html_client.get(url)
            location = resp.headers.get("location", "")
            if not location:
                # Fallback: if follow_redirects somehow absorbed it, use final URL
                location = str(resp.url)
            parsed = urllib.parse.urlparse(location)
            qs = urllib.parse.parse_qs(parsed.query)
            parcel_id = (qs.get("parcel_id") or [None])[0]
            parcel_type = (qs.get("type") or ["new_parcel"])[0]
            lat = (qs.get("lat") or [None])[0]
            lng = (qs.get("lng") or [None])[0]
            return parcel_id, parcel_type, lat, lng
    except Exception as e:
        print(f"[paseetah] Could not resolve share URL {url}: {e}")
        return None, "new_parcel", None, None


import math as _math

def _compute_polygon_area_sqm(coordinates: list) -> Optional[float]:
    """
    Compute the area of a polygon in square metres using the Shoelace formula.
    coordinates is a list of [lng, lat] pairs (GeoJSON ring format).
    """
    if not coordinates or len(coordinates) < 3:
        return None
    ring = coordinates
    lat_avg = sum(p[1] for p in ring) / len(ring)
    cos_lat = _math.cos(_math.radians(lat_avg))
    deg_to_m = 111_000.0
    pts = [(p[0] * deg_to_m * cos_lat, p[1] * deg_to_m) for p in ring]
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    area_sqm = abs(area) / 2.0
    return area_sqm if area_sqm > 5 else None


def _map_new_parcel_fields(
    building_code_data: dict,
    dimensions_data: Optional[dict],
    source_id: "UUID",
    url: str,
    lat: Optional[str] = None,
    lng: Optional[str] = None,
) -> list[dict]:
    """
    Extract fields from get_building_code + get_new_parcel_dimensions responses.
    These are the two endpoints accessible on Paseetah's free tier for new parcels.
    """
    fields: list[dict] = []

    def add(field_name, raw_value, normalized_value, confidence, locator):
        if raw_value is None:
            return
        fields.append({
            "field_name": field_name,
            "raw_value": str(raw_value),
            "normalized_value": normalized_value if normalized_value is not None else str(raw_value),
            "confidence": round(confidence, 4),
            "citation": _build_citation(source_id, url, str(raw_value)[:500], locator, confidence),
        })

    parcel_info = building_code_data.get("parcel_info", {})
    building_code = building_code_data.get("building_code", {})

    # City (en + ar)
    city_en = parcel_info.get("city_en")
    city_ar = parcel_info.get("city_ar")
    if city_en:
        add("city", city_ar or city_en, city_en, 0.90, "json.parcel_info.city_en")
    if city_ar:
        add("city_ar", city_ar, city_ar, 0.90, "json.parcel_info.city_ar")

    # District / Neighborhood (en + ar)
    nb_en = parcel_info.get("neighborhood_en")
    nb_ar = parcel_info.get("neighborhood_ar")
    if nb_en:
        add("district", nb_ar or nb_en, nb_en, 0.88, "json.parcel_info.neighborhood_en")
    if nb_ar:
        add("district_ar", nb_ar, nb_ar, 0.88, "json.parcel_info.neighborhood_ar")

    # Region
    region_en = parcel_info.get("region_en")
    region_ar = parcel_info.get("region_ar")
    if region_en:
        add("region", region_ar or region_en, region_en, 0.88, "json.parcel_info.region_en")

    # Parcel reference numbers
    parcel_num = parcel_info.get("parcel_number")
    plan_num = parcel_info.get("plan_number")
    if parcel_num:
        add("parcel_number", parcel_num, parcel_num, 0.95, "json.parcel_info.parcel_number")
    if plan_num:
        add("plan_number", plan_num, plan_num, 0.95, "json.parcel_info.plan_number")

    # Property type / building usage
    usage_en = building_code.get("building_usage_en") or building_code.get("building_usage")
    if usage_en:
        usage_clean = str(usage_en).strip("{}").replace(",", "/")
        add("property_type", usage_en, usage_clean, 0.80, "json.building_code.building_usage_en")

    # Floor count
    floors = building_code.get("heights_floors_allowed")
    if floors:
        add("floors", floors, str(floors), 0.82, "json.building_code.heights_floors_allowed")

    # Area from polygon (Shoelace formula — most accurate)
    if dimensions_data:
        geo = dimensions_data.get("geoJson", {})
        coords_list = geo.get("geometry", {}).get("coordinates", [])
        if coords_list:
            ring = coords_list[0]  # outer ring
            area_sqm = _compute_polygon_area_sqm(ring)
            if area_sqm:
                add("area_sqm", f"{area_sqm:.1f}", f"{area_sqm:.1f}", 0.87,
                    "computed.shoelace_formula_from_geojson")
        # Fallback: estimate from side lengths
        if not any(f["field_name"] == "area_sqm" for f in fields):
            sides = dimensions_data.get("sidesLengths", [])
            if len(sides) >= 2:
                sides_sorted = sorted(sides)
                area_est = sides_sorted[-1] * sides_sorted[-2]
                add("area_sqm", f"{area_est:.1f}", f"{area_est:.1f}", 0.65,
                    "computed.sides_approximation")

    # Lat/lng from share redirect URL (reliable — these come from the map)
    if lat:
        add("latitude", lat, lat, 0.93, "url.query.lat")
    if lng:
        add("longitude", lng, lng, 0.93, "url.query.lng")

    return fields


def _map_fields(data: dict, source_id: UUID, url: str) -> list[dict]:
    fields = []

    def add(field_name, raw_value, normalized_value, confidence, locator):
        if raw_value is None:
            return
        fields.append({
            "field_name": field_name,
            "raw_value": str(raw_value),
            "normalized_value": normalized_value if normalized_value is not None else str(raw_value),
            "confidence": round(confidence, 4),
            "citation": _build_citation(source_id, url, str(raw_value)[:500], locator, confidence),
        })

    for key in ("price", "Price", "sale_price", "transaction_price", "amount"):
        if key in data:
            num = extract_number(str(data[key]))
            add("price", data[key], str(num) if num else str(data[key]), 0.90, f"json.{key}")
            add("currency", "SAR", "SAR", 0.99, "default.sar")
            break

    for key in ("area", "space", "size", "property_area", "area_size"):
        if key in data:
            num = extract_number(str(data[key]))
            unit = str(data.get("area_unit", data.get("unit", "sqm")))
            if num:
                norm_val, _ = normalize_area(num, unit)
                add("area_sqm", data[key], str(norm_val), 0.90, f"json.{key}")
            break

    for key in ("price_per_meter", "price_per_sqm", "price_per_m2"):
        if key in data:
            num = extract_number(str(data[key]))
            add("price_per_sqm", data[key], str(num) if num else str(data[key]), 0.88, f"json.{key}")
            break

    for key in ("city", "city_name", "City"):
        if key in data:
            en, ar = normalize_city(str(data[key]))
            add("city_en", data[key], en, 0.85, f"json.{key}")
            if ar:
                add("city_ar", data[key], ar, 0.85, f"json.{key}")
            break

    for key in ("district", "neighborhood", "area_name", "zone"):
        if key in data:
            add("district", data[key], str(data[key]), 0.80, f"json.{key}")
            break

    for key in ("address", "location", "full_address"):
        if key in data:
            add("address", data[key], str(data[key]), 0.75, f"json.{key}")
            break

    for key in ("lat", "latitude"):
        if key in data and data[key]:
            add("latitude", data[key], str(data[key]), 0.92, f"json.{key}")
            break

    for key in ("lng", "lon", "longitude"):
        if key in data and data[key]:
            add("longitude", data[key], str(data[key]), 0.92, f"json.{key}")
            break

    for key in ("property_type", "type", "category", "Type"):
        if key in data:
            add("property_type", data[key], str(data[key]), 0.85, f"json.{key}")
            break

    for key in ("deal_type", "transaction_type", "purpose"):
        if key in data:
            add("deal_type", data[key], str(data[key]), 0.85, f"json.{key}")
            break

    for key in ("date", "transaction_date", "created_at", "published_at"):
        if key in data and data[key]:
            norm = normalize_date(str(data[key]))
            add("transaction_date", data[key], norm or str(data[key]), 0.82, f"json.{key}")
            break

    for key in ("rooms", "bedrooms", "bedroom_count", "beds"):
        if key in data:
            num = extract_number(str(data[key]))
            add("bedrooms", data[key], str(int(num)) if num else str(data[key]), 0.85, f"json.{key}")
            break

    for key in ("bathrooms", "bathroom_count", "baths"):
        if key in data:
            num = extract_number(str(data[key]))
            add("bathrooms", data[key], str(int(num)) if num else str(data[key]), 0.80, f"json.{key}")
            break

    for key in ("title", "name", "Title"):
        if key in data and data[key]:
            add("title", data[key], str(data[key]), 0.75, f"json.{key}")
            break

    return fields


class PaseetahExtractor(BaseExtractor):
    """
    Authenticated extractor for paseetah.com.

    Uses a pre-saved session file for authentication.
    Session is obtained via save_session_interactively() which opens a visible
    browser window for the user to complete the reCAPTCHA v2 challenge once.
    """

    name = EXTRACTOR_NAME
    version = EXTRACTOR_VERSION
    RELIABILITY_SCORE = 3

    def can_handle(self, source_type: str) -> bool:
        return source_type in ("url", "paseetah")

    async def extract(
        self,
        source_id: UUID,
        content: str = "",
        url: str = "",
        **kwargs,
    ) -> ExtractionResult:
        raw_data: Optional[dict] = None
        error_msg: Optional[str] = None

        try:
            cookies = await _get_session_cookies()
            cookie_jar = httpx.Cookies()
            for name, value in cookies.items():
                cookie_jar.set(name, value, domain="paseetah.com")

            xsrf = cookies.get("XSRF-TOKEN", "")
            headers = {
                "Accept": "application/json, text/html, */*",
                "Content-Type": "application/json",
                "X-XSRF-TOKEN": xsrf,
                "Referer": PASEETAH_BASE + "/",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            }

            async with httpx.AsyncClient(
                cookies=cookie_jar, headers=headers, follow_redirects=True
            ) as client:
                # ── Step 1: Verify session is actually authenticated ──────────
                auth_check = await client.get(f"{PASEETAH_API}/user", timeout=8)
                if auth_check.status_code == 200:
                    auth_body = auth_check.json()
                    if not auth_body.get("is_logged_in", False):
                        raise RuntimeError(
                            "Paseetah session exists but is NOT authenticated "
                            "(is_logged_in=false). Re-run save_session_interactively()."
                        )

                # ── Step 2: Handle /share/{token} URLs ───────────────────────
                # Share URLs do a server-side redirect to:
                #   /map?lng=...&lat=...&zoom_level=...&type=new_parcel&parcel_id={id}
                # We follow the redirect to get the real parcel_id and type,
                # then call the new-parcel–specific endpoints that are available
                # on Paseetah's free tier.
                if _is_share_url(url):
                    parcel_id, parcel_type, lat, lng = await _resolve_share_url(url, cookie_jar)
                    if parcel_id and parcel_type == "new_parcel":
                        print(f"[paseetah] 🔗 Share link resolved → parcel_id={parcel_id} ({parcel_type})")

                        # a) Building code → city, district, region, usage, floors
                        building_code_data: Optional[dict] = None
                        bc_resp = await client.get(
                            f"{PASEETAH_API}/get_building_code?new_parcel_id={parcel_id}",
                            timeout=12,
                        )
                        if bc_resp.status_code == 200:
                            try:
                                bc_body = bc_resp.json()
                                if isinstance(bc_body, dict) and "parcel_info" in bc_body:
                                    building_code_data = bc_body
                                    print(f"[paseetah] ✅ Got building code data")
                            except Exception:
                                pass

                        # b) Parcel dimensions → polygon → compute area via Shoelace
                        dimensions_data: Optional[dict] = None
                        dim_resp = await client.get(
                            f"{PASEETAH_API}/get_new_parcel_dimensions/{parcel_id}",
                            timeout=12,
                        )
                        if dim_resp.status_code == 200:
                            try:
                                dim_body = dim_resp.json()
                                if isinstance(dim_body, dict) and "geoJson" in dim_body:
                                    dimensions_data = dim_body
                                    print(f"[paseetah] ✅ Got parcel dimensions")
                            except Exception:
                                pass

                        if building_code_data or dimensions_data:
                            fields = _map_new_parcel_fields(
                                building_code_data or {},
                                dimensions_data,
                                source_id,
                                url,
                                lat=lat,
                                lng=lng,
                            )
                            raw_combined = json.dumps(
                                {"building_code": building_code_data, "dimensions": dimensions_data},
                                ensure_ascii=False,
                            )[:5000]
                            return ExtractionResult(
                                source_id=source_id,
                                fields=fields,
                                extractor_name=self.name,
                                extractor_version=self.version,
                                raw_content=raw_combined,
                                error=None,
                            )
                    else:
                        print(f"[paseetah] ⚠️  Could not resolve share link parcel_id (type={parcel_type!r})")
                    # Fall through to generic path if share resolution failed
                    return ExtractionResult(
                        source_id=source_id,
                        fields=[],
                        extractor_name=self.name,
                        extractor_version=self.version,
                        raw_content=content or "",
                        error=f"Could not resolve Paseetah share link: {url}",
                    )

                # ── Step 3: Non-share URL → existing listing/parcel lookup ────
                listing_id = _parse_listing_id(url)
                endpoints_to_try = []
                if listing_id:
                    endpoints_to_try = [
                        # Parcel detail — primary source for property data
                        f"{PASEETAH_API}/get_parcel_data?parcel_id={listing_id}",
                        # Summary popup — used by map pin clicks
                        f"{PASEETAH_API}/get_summary_popup_data?parcel_id={listing_id}",
                        # Portfolio / saved properties
                        f"{PASEETAH_API}/portfolios/{listing_id}",
                        # Generic property/transaction lookup
                        f"{PASEETAH_API}/properties/{listing_id}",
                        f"{PASEETAH_API}/transactions/{listing_id}",
                    ]

                for endpoint in endpoints_to_try:
                    resp = await client.get(endpoint, timeout=15)
                    if resp.status_code == 200:
                        try:
                            body = resp.json()
                        except Exception:
                            continue
                        raw_data = (
                            body.get("data") or
                            body.get("parcel") or
                            body.get("property") or
                            body.get("transaction") or
                            (body if isinstance(body, dict) and len(body) > 2 else None)
                        )
                        if isinstance(raw_data, dict) and raw_data:
                            print(f"[paseetah] ✅ Got data from {endpoint.replace(PASEETAH_API,'')}")
                            break
                        raw_data = None

                # ── Step 4: Fallback — all-cities list or user portfolios ─────
                if not raw_data:
                    for fallback in [
                        f"{PASEETAH_API}/get_all_cities",
                        f"{PASEETAH_API}/portfolios/",
                    ]:
                        resp = await client.get(fallback, timeout=15)
                        if resp.status_code == 200:
                            try:
                                raw_data = resp.json()
                                if raw_data:
                                    print(f"[paseetah] ⚠️  Using fallback endpoint: {fallback.replace(PASEETAH_API,'')}")
                                    break
                            except Exception:
                                pass
                        raw_data = None

        except Exception as e:
            error_msg = f"Paseetah extraction error: {e}"

        if raw_data and isinstance(raw_data, dict):
            fields = _map_fields(raw_data, source_id, url)
            return ExtractionResult(
                source_id=source_id,
                fields=fields,
                extractor_name=self.name,
                extractor_version=self.version,
                raw_content=json.dumps(raw_data, ensure_ascii=False)[:5000],
                error=None,
            )

        return ExtractionResult(
            source_id=source_id,
            fields=[],
            extractor_name=self.name,
            extractor_version=self.version,
            raw_content=content or "",
            error=error_msg or f"Could not fetch Paseetah data for URL: {url}",
        )


# ── CLI helper ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(save_session_interactively())
