"""
HTML Extractor — fetches URL content and extracts structured fields.

Pipeline:
1. Fetch HTML via httpx
2. Parse with BeautifulSoup
3. Try structured data (JSON-LD, meta tags)
4. Try site-specific selectors from field_mapping
5. Try generic regex patterns
6. Normalize values
7. Build citations
"""

import socket
import struct
from typing import Optional
from uuid import UUID

import httpx
from bs4 import BeautifulSoup


def _resolve_via_cloudflare(hostname: str) -> str | None:
    """
    Resolve hostname using Cloudflare's 1.1.1.1 via raw UDP.
    Returns first A-record IP, or None on failure.
    Used as a fallback when the system resolver fails (common in VM/NAT environments).
    """
    try:
        txid = 0xAB12
        header = struct.pack(">HHHHHH", txid, 0x0100, 1, 0, 0, 0)
        qname = b""
        for part in hostname.split("."):
            qname += bytes([len(part)]) + part.encode()
        qname += b"\x00"
        query = header + qname + struct.pack(">HH", 1, 1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        sock.sendto(query, ("1.1.1.1", 53))
        resp, _ = sock.recvfrom(512)
        sock.close()
        # Skip header (12 bytes) + question section
        i = 12 + len(qname) + 4
        while i < len(resp) - 12:
            if resp[i] & 0xC0 == 0xC0:
                i += 2
            else:
                while i < len(resp) and resp[i] != 0:
                    i += resp[i] + 1
                i += 1
            rtype = struct.unpack(">H", resp[i:i+2])[0]
            rdlen = struct.unpack(">H", resp[i+8:i+10])[0]
            if rtype == 1 and rdlen == 4:
                return ".".join(str(b) for b in resp[i+10:i+14])
            i += 10 + rdlen
    except Exception:
        pass
    return None


async def _fetch_with_dns_fallback(url: str, headers: dict) -> str:
    """
    Fetch a URL, falling back to Cloudflare DNS (1.1.1.1) when the system
    resolver fails. Returns the response text.
    httpx/anyio bypass socket.getaddrinfo, so we use aiohttp-style raw asyncio
    streams for the fallback path.
    """
    import asyncio
    import ssl
    from urllib.parse import urlparse

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    # Fast path: try httpx normally
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True,
                                     headers=headers) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.text
    except Exception as first_err:
        # Only fall back if it's a DNS/connect failure
        if "name resolution" not in str(first_err).lower() and \
           "connect" not in str(first_err).lower():
            raise

    # Fallback: resolve via Cloudflare then open raw TLS stream
    ip = _resolve_via_cloudflare(hostname)
    if not ip:
        raise RuntimeError(f"Could not resolve {hostname} via fallback DNS")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    reader, writer = await asyncio.open_connection(
        ip, port, ssl=ssl_ctx,
        server_hostname=hostname  # SNI — critical for Cloudflare shared certs
    )

    req_headers = {**headers, "Host": hostname, "Connection": "close"}
    req_str = f"GET {path} HTTP/1.1\r\n"
    req_str += "".join(f"{k}: {v}\r\n" for k, v in req_headers.items())
    req_str += "\r\n"
    writer.write(req_str.encode())
    await writer.drain()

    raw = b""
    while True:
        chunk = await asyncio.wait_for(reader.read(65536), timeout=15)
        if not chunk:
            break
        raw += chunk
    writer.close()

    # Handle HTTP/1.1 response (may redirect)
    header_end = raw.find(b"\r\n\r\n")
    headers_raw = raw[:header_end].decode("utf-8", errors="replace")
    body = raw[header_end + 4:]

    status_line = headers_raw.split("\r\n")[0]
    status_code = int(status_line.split(" ")[1])

    if status_code in (301, 302, 303, 307, 308):
        for hline in headers_raw.split("\r\n"):
            if hline.lower().startswith("location:"):
                new_url = hline.split(":", 1)[1].strip()
                if not new_url.startswith("http"):
                    new_url = f"{parsed.scheme}://{hostname}{new_url}"
                return await _fetch_with_dns_fallback(new_url, headers)

    # Handle chunked transfer encoding
    if "transfer-encoding: chunked" in headers_raw.lower():
        decoded = b""
        i = 0
        while i < len(body):
            end = body.find(b"\r\n", i)
            if end == -1:
                break
            try:
                chunk_size = int(body[i:end], 16)
            except ValueError:
                break
            if chunk_size == 0:
                break
            decoded += body[end + 2: end + 2 + chunk_size]
            i = end + 2 + chunk_size + 2
        body = decoded

    # Decompress if gzip/deflate
    content_encoding = ""
    for hline in headers_raw.split("\r\n"):
        if hline.lower().startswith("content-encoding:"):
            content_encoding = hline.split(":", 1)[1].strip().lower()
            break
    if content_encoding == "gzip" or body[:2] == b"\x1f\x8b":
        import gzip
        try:
            body = gzip.decompress(body)
        except Exception:
            pass
    elif content_encoding == "deflate":
        import zlib
        try:
            body = zlib.decompress(body)
        except Exception:
            try:
                body = zlib.decompress(body, -zlib.MAX_WBITS)
            except Exception:
                pass

    return body.decode("utf-8", errors="replace")

from extractors.base import BaseExtractor, ExtractionResult
from extractors.citation import build_citation
from extractors.confidence import score_confidence
from extractors.field_mapping import (
    get_site_config, PRICE_PATTERNS, AREA_PATTERNS, DATE_PATTERNS,
    detect_property_type,
)
from extractors.normalizer import (
    extract_number, normalize_city, normalize_date,
)

# Browser-like headers to avoid basic bot detection
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ar,en;q=0.9",
    # Avoid compressed responses we may not be able to decode reliably in every local env.
    "Accept-Encoding": "gzip, deflate",
}

# Blocked-page indicators (title or body text)
_BLOCKED_SIGNALS = [
    "you have been blocked",
    "تم حظرك",
    "access denied",
    "just a moment",  # Cloudflare challenge
    "checking your browser",
    "enable javascript",
    "captcha",
]


class HTMLExtractor(BaseExtractor):
    name = "html_extractor"
    version = "1.0.0"

    def can_handle(self, source_type: str) -> bool:
        return source_type == "url"

    async def extract(self, source_id: UUID, content: str, **kwargs) -> ExtractionResult:
        url = kwargs.get("url", "")

        # If content is empty, fetch it
        if not content:
            try:
                content = await _fetch_with_dns_fallback(url, _HEADERS)
            except Exception as e:
                return ExtractionResult(
                    source_id=source_id,
                    fields=[],
                    extractor_name=self.name,
                    extractor_version=self.version,
                    error=f"Failed to fetch URL: {e}",
                )

        # --- Detect blocked / captcha pages ---
        content_lower = content[:3000].lower()
        for signal in _BLOCKED_SIGNALS:
            if signal in content_lower:
                return ExtractionResult(
                    source_id=source_id,
                    fields=[],
                    extractor_name=self.name,
                    extractor_version=self.version,
                    error=(
                        f"Page blocked by anti-bot protection (detected: '{signal}'). "
                        f"This site requires browser-based access. "
                        f"Try uploading a saved PDF or using a direct data provider instead."
                    ),
                )

        soup = BeautifulSoup(content, "lxml")
        site_config = get_site_config(url)
        fields = []

        # --- 1. Try structured data (JSON-LD) ---
        json_ld_fields = self._extract_json_ld(soup, source_id, url)
        fields.extend(json_ld_fields)

        # --- 2. Try meta tags ---
        meta_fields = self._extract_meta_tags(soup, source_id, url, site_config)
        fields.extend(meta_fields)

        # --- 3. Try site-specific selectors ---
        if site_config:
            selector_fields = self._extract_selectors(soup, source_id, url, site_config)
            fields.extend(selector_fields)

        # --- 3b. Try site-specific JSON blob patterns (e.g. Aqar Next.js data) ---
        if site_config and site_config.get("json_patterns"):
            json_blob_fields = self._extract_json_patterns(
                content, source_id, url, site_config
            )
            fields.extend(json_blob_fields)

        # --- 4. Try generic regex on page text ---
        page_text = soup.get_text(separator="\n", strip=True)
        regex_fields = self._extract_regex(page_text, source_id, url)
        fields.extend(regex_fields)

        # --- 5. Title fallback ---
        if not any(f["field_name"] == "property_title" for f in fields):
            if soup.title and soup.title.string:
                fields.append(self._make_field(
                    "property_title", soup.title.string.strip(), soup.title.string.strip(),
                    source_id, url, "title", soup.title.string[:200], 0.6,
                ))

        # Deduplicate — keep highest confidence per field
        seen = {}
        for f in fields:
            name = f["field_name"]
            if name not in seen or f["confidence"] > seen[name]["confidence"]:
                seen[name] = f
        fields = list(seen.values())

        return ExtractionResult(
            source_id=source_id,
            fields=fields,
            extractor_name=self.name,
            extractor_version=self.version,
            raw_content=content,
        )

    def _extract_json_ld(self, soup: BeautifulSoup, source_id: UUID, url: str) -> list[dict]:
        """Extract from JSON-LD structured data."""
        import json as json_mod
        fields = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json_mod.loads(script.string)
                if isinstance(data, list):
                    data = data[0] if data else {}

                if "name" in data:
                    fields.append(self._make_field(
                        "property_title", data["name"], data["name"],
                        source_id, url, "json-ld.name", data["name"][:200], 0.9,
                    ))
                if "address" in data and isinstance(data["address"], dict):
                    addr = data["address"]
                    if "addressLocality" in addr:
                        en, ar = normalize_city(addr["addressLocality"])
                        fields.append(self._make_field(
                            "city", addr["addressLocality"], en,
                            source_id, url, "json-ld.address.addressLocality",
                            addr["addressLocality"], 0.9,
                        ))
                if "geo" in data and isinstance(data["geo"], dict):
                    geo = data["geo"]
                    if "latitude" in geo:
                        fields.append(self._make_field(
                            "latitude", str(geo["latitude"]), str(geo["latitude"]),
                            source_id, url, "json-ld.geo.latitude", str(geo["latitude"]), 0.95,
                        ))
                    if "longitude" in geo:
                        fields.append(self._make_field(
                            "longitude", str(geo["longitude"]), str(geo["longitude"]),
                            source_id, url, "json-ld.geo.longitude", str(geo["longitude"]), 0.95,
                        ))
            except Exception:
                continue
        return fields

    def _extract_meta_tags(self, soup: BeautifulSoup, source_id: UUID, url: str, site_config: Optional[dict]) -> list[dict]:
        """Extract from <meta> tags."""
        fields = []
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            fields.append(self._make_field(
                "property_title", og_title["content"], og_title["content"].strip(),
                source_id, url, 'meta[property="og:title"]', og_title["content"][:200], 0.8,
            ))
        return fields

    def _extract_selectors(self, soup: BeautifulSoup, source_id: UUID, url: str, config: dict) -> list[dict]:
        """Extract using site-specific CSS selectors."""
        fields = []
        selectors = config.get("selectors", {})

        for field_name, css_list in selectors.items():
            for css in css_list:
                el = soup.select_one(css)
                if el and el.get_text(strip=True):
                    text = el.get_text(strip=True)
                    fields.append(self._make_field(
                        field_name, text, text,
                        source_id, url, css, text[:200], 0.85,
                    ))
                    break  # Use first matching selector
        return fields

    def _extract_json_patterns(self, html: str, source_id: UUID, url: str,
                                config: dict) -> list[dict]:
        """
        Extract fields from embedded JSON blobs (e.g. Next.js __NEXT_DATA__ or
        escaped JSON in script tags). Used for sites like Aqar that bake listing
        data into script blocks rather than HTML elements.
        """
        fields = []
        patterns: dict = config.get("json_patterns", {})
        # Aqar category ID → property type
        aqar_category_map = {
            "1": "villa", "2": "apartment", "3": "land", "4": "commercial",
            "5": "office", "6": "apartment", "7": "villa", "8": "building",
        }

        for field_name, pattern in patterns.items():
            m = pattern.search(html)
            if not m:
                continue
            raw_val = m.group(1).strip()
            if not raw_val or raw_val in ("null", "undefined", ""):
                continue

            # Post-process specific fields
            normalized = raw_val
            if field_name == "asking_price":
                try:
                    normalized = str(float(raw_val))
                except ValueError:
                    pass
            elif field_name in ("area_sqm",):
                try:
                    normalized = str(float(raw_val))
                except ValueError:
                    pass
            elif field_name == "property_type_raw":
                normalized = aqar_category_map.get(raw_val, raw_val)
                field_name = "property_type"
            elif field_name in ("lat", "lng"):
                try:
                    float(raw_val)  # validate it's a number
                except ValueError:
                    continue

            snippet = m.group(0)[:200]
            fields.append(self._make_field(
                field_name, raw_val, normalized,
                source_id, url, f"json_blob:{pattern.pattern[:40]}", snippet, 0.80,
            ))
        return fields

    def _extract_regex(self, text: str, source_id: UUID, url: str) -> list[dict]:
        """Extract using generic regex patterns on page text."""
        fields = []

        # Price
        for pattern in PRICE_PATTERNS:
            match = pattern.search(text)
            if match:
                raw = match.group(0)
                num = extract_number(match.group(1))
                if num and num > 10000:  # Sanity check — prices should be significant
                    fields.append(self._make_field(
                        "asking_price", raw, str(num),
                        source_id, url, f"regex:{pattern.pattern[:50]}",
                        raw[:200], 0.7,
                    ))
                    break

        # Area
        for pattern in AREA_PATTERNS:
            match = pattern.search(text)
            if match:
                raw = match.group(0)
                num = extract_number(match.group(1))
                if num and num > 0:
                    fields.append(self._make_field(
                        "primary_area_sqm", raw, str(num),
                        source_id, url, f"regex:{pattern.pattern[:50]}",
                        raw[:200], 0.7,
                    ))
                    break

        # Date
        for pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                raw = match.group(0)
                normalized = normalize_date(raw)
                if normalized:
                    fields.append(self._make_field(
                        "listing_date", raw, normalized,
                        source_id, url, "regex:date", raw, 0.6,
                    ))
                    break

        # Property type
        ptype = detect_property_type(text[:3000])
        if ptype:
            fields.append(self._make_field(
                "property_type", ptype, ptype,
                source_id, url, "keyword_detection", ptype, 0.7,
            ))

        return fields

    def _make_field(
        self, field_name: str, raw: str, normalized: str,
        source_id: UUID, url: str, locator: str, snippet: str,
        parse_conf: float,
    ) -> dict:
        return {
            "field_name": field_name,
            "raw_value": raw,
            "normalized_value": normalized,
            "display_value": normalized,
            "confidence": score_confidence(parse_conf, source_reliability=2),
            "classification": "fact",
            "value_type": "string",
            "citation": build_citation(
                source_id=source_id,
                source_type="url",
                source_url_or_name=url,
                locator=locator,
                snippet=snippet[:500],
                extractor_name=self.name,
                extractor_version=self.version,
                parse_confidence=parse_conf,
            ),
        }
