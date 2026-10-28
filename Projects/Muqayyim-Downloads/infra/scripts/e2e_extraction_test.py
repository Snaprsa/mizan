"""
End-to-End Extraction Test with Real URLs
==========================================
Tests the full extraction pipeline against live AqarSAS and Paseetah URLs.

Run from project root on your Mac (NOT in a sandbox VM):
    cd Projects/Muqayyim-Downloads
    source .venv/bin/activate
    python infra/scripts/e2e_extraction_test.py

Prerequisites:
    1. AqarSAS session: auto-renewed (headless Playwright, no CAPTCHA)
    2. Paseetah session: run once manually →
           python infra/scripts/save_paseetah_session.py
    3. .env loaded (DATABASE_URL, ANTHROPIC_API_KEY, etc.)
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

# ── path bootstrap ────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv()


# ── real test URLs (discovered from live session, March 2026) ────────────────
TEST_CASES = [
    {
        "platform": "aqarsas",
        "url": "https://aqarsas.sa/lands/2203382",
        "description": "Land parcel 165/2/2 — Al-Kharj, Riyadh region (2 known transactions)",
        "expect_fields": ["area_sqm", "city_en", "district"],
    },
    {
        "platform": "aqarsas",
        "url": "https://aqarsas.sa/lands/2415208",
        "description": "Land parcel — Al-Riyadh",
        "expect_fields": ["area_sqm"],
    },
    {
        "platform": "aqarsas",
        "url": "https://aqarsas.sa/lands/345203",
        "description": "Land parcel — older listing",
        "expect_fields": ["area_sqm"],
    },
]

# Paseetah URLs require an authenticated session (reCAPTCHA v2 once)
PASEETAH_CASES = [
    {
        "platform": "paseetah",
        "url": "https://paseetah.com/paseetah-record",
        "description": "Paseetah record page (requires auth)",
        "expect_fields": [],
    },
]


async def run_aqarsas_test(case: dict) -> dict:
    """Run extraction for one AqarSAS URL."""
    from extractors.aqarsas_extractor import AqarSASExtractor

    extractor = AqarSASExtractor()
    source_id = uuid4()

    print(f"\n{'─'*60}")
    print(f"  Platform : AqarSAS")
    print(f"  URL      : {case['url']}")
    print(f"  Desc     : {case['description']}")
    print(f"{'─'*60}")

    result = await extractor.extract(source_id=source_id, url=case["url"])

    ok = not result.error and len(result.fields) > 0
    print(f"  Result   : {'✅ OK' if ok else '❌ FAILED'}")
    print(f"  Fields   : {len(result.fields)}")
    if result.error:
        print(f"  Error    : {result.error[:120]}")

    field_names = [f["field_name"] for f in result.fields]
    for fname in case.get("expect_fields", []):
        found = fname in field_names
        print(f"  {'✅' if found else '⚠️ '} {fname}: {'found' if found else 'MISSING'}")

    if result.fields:
        print(f"\n  Extracted fields:")
        for f in result.fields:
            print(f"    {f['field_name']:<20} = {f['normalized_value'][:60]!r}  (conf={f['confidence']:.2f})")

    return {"url": case["url"], "ok": ok, "fields": len(result.fields), "error": result.error}


async def run_paseetah_test(case: dict) -> dict:
    """Run extraction for one Paseetah URL."""
    from extractors.paseetah_extractor import PaseetahExtractor, load_session_from_file

    # Check session first
    cookies = load_session_from_file()
    if not cookies:
        print(f"\n  ⚠️  Paseetah session not available.")
        print(f"  Run:  python infra/scripts/save_paseetah_session.py")
        return {"url": case["url"], "ok": False, "fields": 0, "error": "No session"}

    extractor = PaseetahExtractor()
    source_id = uuid4()

    print(f"\n{'─'*60}")
    print(f"  Platform : Paseetah")
    print(f"  URL      : {case['url']}")
    print(f"  Desc     : {case['description']}")
    print(f"{'─'*60}")

    result = await extractor.extract(source_id=source_id, url=case["url"])

    ok = not result.error
    print(f"  Result   : {'✅ OK' if ok else '❌ FAILED'}")
    print(f"  Fields   : {len(result.fields)}")
    if result.error:
        print(f"  Error    : {result.error[:120]}")

    if result.fields:
        print(f"\n  Extracted fields:")
        for f in result.fields:
            print(f"    {f['field_name']:<20} = {f['normalized_value'][:60]!r}  (conf={f['confidence']:.2f})")

    return {"url": case["url"], "ok": ok, "fields": len(result.fields), "error": result.error}


async def main():
    print("=" * 60)
    print("Muqayyim — E2E Extraction Test")
    print("=" * 60)
    print(f"  Root: {ROOT}")
    print(f"  Time: {__import__('datetime').datetime.utcnow().isoformat()}Z")

    results = []

    # ── AqarSAS tests ──────────────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print("AqarSAS Tests")
    print(f"{'═'*60}")

    for case in TEST_CASES:
        try:
            r = await run_aqarsas_test(case)
            results.append(r)
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            results.append({"url": case["url"], "ok": False, "fields": 0, "error": str(e)})

    # ── Paseetah tests ─────────────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print("Paseetah Tests")
    print(f"{'═'*60}")

    for case in PASEETAH_CASES:
        try:
            r = await run_paseetah_test(case)
            results.append(r)
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            results.append({"url": case["url"], "ok": False, "fields": 0, "error": str(e)})

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print("SUMMARY")
    print(f"{'═'*60}")
    passed = sum(1 for r in results if r["ok"])
    total  = len(results)
    print(f"  {passed}/{total} tests passed\n")
    for r in results:
        icon = "✅" if r["ok"] else "❌"
        url_short = r["url"].replace("https://", "").replace("www.", "")
        print(f"  {icon}  {url_short:<45}  fields={r['fields']}")
        if r["error"]:
            print(f"       error: {str(r['error'])[:80]}")

    return passed == len([r for r in results if "paseetah" not in r["url"]])


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
