"""HTML extraction pipeline v0.3 — extracts structured property data from Saudi RE pages.

Now works with Playwright-rendered text for JS-heavy sites like Aqar.
Strategy:
1. Use rendered body text (from Playwright) if available — this has the actual prices
2. Extract from meta/OG tags (reliable for title, city, district)
3. Parse Arabic patterns for all fields
4. Every field gets a citation
"""
import re
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from schemas.citation import CitationObject, CitationLocator

EXTRACTOR_NAME = "html_extractor"
EXTRACTOR_VERSION = "0.3.0"

# Saudi city names
SAUDI_CITIES = {
    "الرياض": "Riyadh", "رياض": "Riyadh", "riyadh": "Riyadh",
    "جدة": "Jeddah", "جده": "Jeddah", "jeddah": "Jeddah",
    "مكة": "Makkah", "مكه": "Makkah", "makkah": "Makkah",
    "المدينة المنورة": "Madinah", "المدينة": "Madinah", "المدينه": "Madinah",
    "الدمام": "Dammam", "dammam": "Dammam",
    "الخبر": "Khobar", "khobar": "Khobar",
    "تبوك": "Tabuk", "tabuk": "Tabuk",
    "أبها": "Abha", "ابها": "Abha",
    "الطائف": "Taif", "الطايف": "Taif",
    "حائل": "Hail",
    "ينبع": "Yanbu",
    "الجبيل": "Jubail",
    "بريدة": "Buraidah",
    "خميس مشيط": "Khamis Mushait",
    "نجران": "Najran",
    "جازان": "Jazan",
}

# Property types
PROPERTY_TYPES = {
    "فيلا": ("residential", "villa"), "فلل": ("residential", "villa"),
    "شقة": ("residential", "apartment"), "شقق": ("residential", "apartment"),
    "شقه": ("residential", "apartment"),
    "دور": ("residential", "floor"), "دبلكس": ("residential", "duplex"),
    "عمارة": ("residential", "building"), "عماره": ("residential", "building"),
    "أرض": ("land", "land"), "ارض": ("land", "land"),
    "قطعة أرض": ("land", "land"), "قطعه ارض": ("land", "land"),
    "محل": ("commercial", "shop"), "محلات": ("commercial", "shop"),
    "مكتب": ("commercial", "office"), "مكاتب": ("commercial", "office"),
    "معرض": ("commercial", "showroom"),
    "مستودع": ("industrial", "warehouse"),
    "استراحة": ("residential", "retreat"), "استراحه": ("residential", "retreat"),
    "مزرعة": ("land", "farm"), "مزرعه": ("land", "farm"),
    "بيت": ("residential", "house"),
    "شاليه": ("residential", "chalet"),
    "غرف": ("residential", "room"), "غرفة": ("residential", "room"),
    "مخيم": ("residential", "camp"),
    "villa": ("residential", "villa"),
    "apartment": ("residential", "apartment"),
    "land": ("land", "land"),
    "office": ("commercial", "office"),
}

DEAL_SALE = ["للبيع", "for sale", "بيع"]
DEAL_RENT = ["للإيجار", "للايجار", "ايجار", "إيجار", "for rent"]


def extract_from_html(
    html_content: str,
    source_url: str,
    source_id: str,
    retrieval_timestamp: datetime = None,
    rendered_text: str = None,
) -> Dict[str, Any]:
    """Extract property fields from HTML + optionally rendered text."""
    if retrieval_timestamp is None:
        retrieval_timestamp = datetime.now(timezone.utc)

    fields = {}

    def cite(snippet: str, conf: float, hint: str = "") -> dict:
        return CitationObject(
            source_id=source_id, source_type="url", source_name=source_url,
            retrieval_timestamp=retrieval_timestamp,
            locator=CitationLocator(text_block=snippet[:500], bounding_hint=hint),
            snippet=snippet[:500],
            extractor_name=EXTRACTOR_NAME, extractor_version=EXTRACTOR_VERSION,
            parse_confidence=conf,
        ).model_dump(mode="json")

    # ── Get best text sources ──
    og_title = _meta(html_content, "og:title") or _meta(html_content, "twitter:title")
    og_desc = _meta(html_content, "og:description") or _meta(html_content, "description")
    page_title = _tag(html_content, "title")
    title_text = og_title or page_title or ""
    
    # Use rendered text if available, otherwise strip HTML
    body_text = rendered_text if rendered_text else _strip_html(html_content)
    all_text = f"{title_text}\n{og_desc or ''}\n{body_text}"

    # ── Title ──
    if title_text:
        fields["property_title"] = {
            "raw_value": title_text[:200],
            "normalized_value": title_text[:200],
            "confidence": 0.9,
            "citation": cite(title_text[:200], 0.9, "page title"),
        }

    # ── City ──
    for ar, en in SAUDI_CITIES.items():
        if ar in all_text:
            fields["city"] = {
                "raw_value": ar, "normalized_value": en,
                "confidence": 0.9, "citation": cite(f"{ar} → {en}", 0.9, "city match"),
            }
            break

    # ── District ──
    district_pats = [
        r'حي\s+([^\s،,\.\n]+(?:\s+[^\s،,\.\n]+)?)',
        r'في\s+حي\s+([^\s،,\.\n]+(?:\s+[^\s،,\.\n]+)?)',
    ]
    for pat in district_pats:
        m = re.search(pat, all_text)
        if m:
            d = m.group(1).strip()
            skip = ["شارع", "طريق", "مدينة", "منطقة", "المملكة", "في"]
            if not any(w == d for w in skip) and len(d) > 1:
                fields["district"] = {
                    "raw_value": d, "normalized_value": d,
                    "confidence": 0.85, "citation": cite(f"حي {d}", 0.85, "district in text"),
                }
                break

    # ── Property Type ──
    for kw, (cat, sub) in PROPERTY_TYPES.items():
        if kw in title_text or kw in body_text[:500]:
            fields["property_category"] = {
                "raw_value": kw, "normalized_value": cat,
                "confidence": 0.85, "citation": cite(f"{kw} → {cat}", 0.85, "type match"),
            }
            fields["property_subtype"] = {
                "raw_value": kw, "normalized_value": sub,
                "confidence": 0.85, "citation": cite(f"{kw} → {sub}", 0.85, "subtype match"),
            }
            break

    # ── Deal Type ──
    for kw in DEAL_SALE:
        if kw in all_text[:1000]:
            fields["evidence_type"] = {
                "raw_value": kw, "normalized_value": "listing",
                "confidence": 0.8, "citation": cite(f"sale: {kw}", 0.8, "deal type"),
            }
            fields["notes"] = {
                "raw_value": "For sale", "normalized_value": "For sale",
                "confidence": 0.8, "citation": cite(kw, 0.8, "deal type"),
            }
            break
    else:
        for kw in DEAL_RENT:
            if kw in all_text[:1000]:
                fields["evidence_type"] = {
                    "raw_value": kw, "normalized_value": "listing",
                    "confidence": 0.8, "citation": cite(f"rent: {kw}", 0.8, "deal type"),
                }
                fields["notes"] = {
                    "raw_value": "For rent (إيجار)", "normalized_value": "For rent",
                    "confidence": 0.8, "citation": cite(kw, 0.8, "deal type"),
                }
                break

    # ── PRICE (most important!) ──
    price = _extract_price(body_text, all_text)
    if price:
        fields["asking_price"] = {
            "raw_value": price["raw"],
            "normalized_value": str(price["value"]),
            "confidence": price["confidence"],
            "citation": cite(price["raw"], price["confidence"], "price extraction"),
        }
    
    # ── AREA ──
    area = _extract_area(body_text)
    if area:
        fields["land_area"] = {
            "raw_value": area["raw"],
            "normalized_value": str(area["value"]),
            "confidence": area["confidence"],
            "citation": cite(area["raw"], area["confidence"], "area extraction"),
        }

    # ── COORDINATES (from HTML source — embedded in map elements) ──
    coords = _extract_coordinates(html_content)
    if coords:
        fields["latitude"] = {
            "raw_value": coords["lat_raw"], "normalized_value": str(coords["lat"]),
            "confidence": coords["confidence"],
            "citation": cite(f"{coords['lat']}, {coords['lng']}", coords["confidence"], "map coordinates"),
        }
        fields["longitude"] = {
            "raw_value": coords["lng_raw"], "normalized_value": str(coords["lng"]),
            "confidence": coords["confidence"],
            "citation": cite(f"{coords['lat']}, {coords['lng']}", coords["confidence"], "map coordinates"),
        }
        fields["google_maps_link"] = {
            "raw_value": f"https://maps.google.com/?q={coords['lat']},{coords['lng']}",
            "normalized_value": f"https://maps.google.com/?q={coords['lat']},{coords['lng']}",
            "confidence": coords["confidence"],
            "citation": cite(f"Generated from extracted coordinates", coords["confidence"], "generated link"),
        }

    # ── Currency (always SAR) ──
    fields["currency"] = {
        "raw_value": "SAR", "normalized_value": "SAR",
        "confidence": 0.95, "citation": cite("SAR default", 0.95, "default"),
    }

    # ── Reliability ──
    rel = 2
    if "aqar.fm" in source_url: rel = 2
    fields["reliability_score"] = {
        "raw_value": str(rel), "normalized_value": str(rel),
        "confidence": 1.0, "citation": cite(f"reliability {rel}", 1.0, "source type"),
    }

    return fields


def _extract_price(body_text: str, all_text: str) -> Optional[Dict]:
    """Extract price — handles Aqar format like '75000 §/سنوي' and Arabic patterns."""
    
    patterns = [
        # Aqar rendered format: "75000 §/سنوي" or "1500000 §"
        (r'(\d[\d,]{2,})\s*§', 0.85),
        # "75,000 ريال" or "1500000 ريال"
        (r'(\d[\d,]{2,})\s*(?:ريال|ر\.س|ر\.س\.)', 0.8),
        # "SAR 75,000" or "75,000 SAR"
        (r'(?:SAR|sar|SR)\s*(\d[\d,]{2,})', 0.8),
        (r'(\d[\d,]{2,})\s*(?:SAR|sar|SR)', 0.8),
        # "السعر: 75000" or "السعر 75,000"
        (r'(?:السعر|الثمن|سعر|الإيجار|الايجار)\s*[:\-–]?\s*(\d[\d,]{2,})', 0.75),
        # Just large numbers near price context (relaxed)
        (r'(\d[\d,]{4,})\s*/\s*(?:سنوي|شهري|yearly|monthly)', 0.7),
    ]
    
    best = None
    for pat, conf in patterns:
        for m in re.finditer(pat, body_text):
            raw_num = m.group(1).replace(",", "").replace("،", "")
            try:
                val = float(raw_num)
                if val < 100:
                    continue  # too small to be a price
                
                # Keep the highest-confidence match with reasonable value
                if best is None or conf > best["confidence"] or (conf == best["confidence"] and val > best["value"]):
                    raw_str = m.group(0).strip()
                    # Add period info
                    period_match = re.search(r'(سنوي|شهري|yearly|monthly|يومي|daily)', body_text[m.end():m.end()+20])
                    if period_match:
                        raw_str += f" ({period_match.group(1)})"
                    best = {"raw": raw_str, "value": val, "confidence": conf}
            except ValueError:
                pass
    
    # Also check all_text (includes meta tags) if no match in body
    if not best:
        for pat, conf in patterns[:3]:
            m = re.search(pat, all_text)
            if m:
                raw_num = m.group(1).replace(",", "").replace("،", "")
                try:
                    val = float(raw_num)
                    if val >= 100:
                        best = {"raw": m.group(0).strip(), "value": val, "confidence": conf * 0.9}
                except ValueError:
                    pass
    
    return best


def _extract_area(text: str) -> Optional[Dict]:
    """Extract area from rendered text."""
    patterns = [
        # "325م²" or "500 م²"
        (r'(\d[\d,\.]*)\s*م[²٢]', 0.85),
        # "المساحة: 500 متر"
        (r'(?:المساحة|مساحة|الأرض|area|size)\s*[:\-–]?\s*(\d[\d,\.]*)\s*(?:م|متر|sqm|m)', 0.8),
        # "500 متر مربع"
        (r'(\d[\d,\.]*)\s*متر(?:\s*مربع)?', 0.7),
        # "500 sqm"
        (r'(\d[\d,\.]*)\s*(?:sqm|sq\.?\s*m)', 0.75),
    ]
    
    for pat, conf in patterns:
        m = re.search(pat, text)
        if m:
            raw = m.group(1).replace(",", "").replace("،", "")
            try:
                val = float(raw)
                if val > 0 and val < 100000:  # sensible area range
                    return {"raw": m.group(0).strip(), "value": val, "confidence": conf}
            except ValueError:
                pass
    return None


def _meta(html: str, name: str) -> Optional[str]:
    patterns = [
        rf'<meta\s+[^>]*?(?:property|name)=["\'](?:og:|twitter:)?{re.escape(name)}["\'][^>]*?content=["\']([^"\']+)["\']',
        rf'<meta\s+[^>]*?content=["\']([^"\']+)["\'][^>]*?(?:property|name)=["\'](?:og:|twitter:)?{re.escape(name)}["\']',
    ]
    for p in patterns:
        m = re.search(p, html, re.IGNORECASE)
        if m: return m.group(1).strip()
    return None


def _tag(html: str, tag: str) -> Optional[str]:
    m = re.search(rf'<{tag}[^>]*>([^<]+)</{tag}>', html, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _extract_coordinates(html: str) -> Optional[Dict]:
    """Extract lat/lng coordinates from HTML source (map embeds, data attributes, inline JS).
    Saudi Arabia coords: lat ~16-32, lng ~34-56.
    """
    patterns = [
        # High precision coords embedded in HTML: "24.813915","46.626972"
        (r'["\']?(\d{2}\.\d{5,})["\']?\s*[,/]\s*["\']?(\d{2,3}\.\d{5,})["\']?', 0.9),
        # Google Maps URL: @24.8139,46.6269 or center=24.8139,46.6269
        (r'[@=](-?\d{2}\.\d{3,})[,%/](-?\d{2,3}\.\d{3,})', 0.85),
        # lat/lng in JSON: "lat":24.813,"lng":46.626 or "latitude":24.813
        (r'"lat(?:itude)?"[:\s]+(-?\d{2}\.\d{3,})[^"]*?"l(?:on|ng)(?:itude)?"[:\s]+(-?\d{2,3}\.\d{3,})', 0.85),
        # Data attributes: data-lat="24.813" data-lng="46.626"
        (r'data-lat[itude]*=["\'](-?\d{2}\.\d{3,})["\'].*?data-l(?:on|ng)[gitude]*=["\'](-?\d{2,3}\.\d{3,})["\']', 0.85),
        # Medium precision (4 digits)
        (r'(\d{2}\.\d{4,})\s*[,،]\s*(\d{2,3}\.\d{4,})', 0.75),
    ]
    
    for pat, conf in patterns:
        for m in re.finditer(pat, html, re.DOTALL):
            lat_str = m.group(1)
            lng_str = m.group(2)
            try:
                lat = float(lat_str)
                lng = float(lng_str)
                # Validate coordinates are in Saudi Arabia (roughly)
                if 16.0 <= lat <= 33.0 and 34.0 <= lng <= 56.0:
                    return {
                        "lat": lat, "lng": lng,
                        "lat_raw": lat_str, "lng_raw": lng_str,
                        "confidence": conf,
                    }
                # Maybe lat/lng are swapped
                if 16.0 <= lng <= 33.0 and 34.0 <= lat <= 56.0:
                    return {
                        "lat": lng, "lng": lat,
                        "lat_raw": lng_str, "lng_raw": lat_str,
                        "confidence": conf * 0.9,
                    }
            except ValueError:
                pass
    
    return None


def _strip_html(html: str) -> str:
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
