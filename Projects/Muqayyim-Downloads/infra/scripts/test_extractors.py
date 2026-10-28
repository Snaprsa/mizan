"""
Smoke-test both platform extractors — saves sessions if not already cached.

Run from project root:
    python infra/scripts/test_extractors.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from dotenv import load_dotenv
load_dotenv()


async def test_aqarsas():
    print("\n" + "="*55)
    print("AqarSAS — Playwright headless login + session save")
    print("="*55)
    try:
        from extractors.aqarsas_extractor import _playwright_login, _save_session, _session_file
        # Check if session already exists and is fresh
        sf = _session_file()
        if sf.exists():
            import json, time
            d = json.loads(sf.read_text())
            age = time.time() - d.get("saved_at", 0)
            if age < 86400:  # 24h TTL — matches extractor SESSION_TTL
                print(f"  ✅ Using cached session ({int(age)}s / {int(age/3600)}h old): {sf}")
                return True
        print("  Launching headless Chromium …")
        cookies = await _playwright_login()
        _save_session(cookies)
        print(f"  ✅ Login OK — {len(cookies)} cookies saved")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


async def test_paseetah():
    print("\n" + "="*55)
    print("Paseetah — visible browser login (reCAPTCHA v2)")
    print("="*55)
    try:
        from extractors.paseetah_extractor import _session_file_path, load_session_from_file
        sf = _session_file_path()
        if sf.exists():
            cookies = load_session_from_file()
            if cookies:
                print(f"  ✅ Using cached session: {sf}")
                return True
        print("  No cached session found.")
        print("  Run this to capture session interactively:")
        print("    python infra/scripts/save_paseetah_session.py")
        return False
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


async def test_api_call(platform: str):
    """Verify the session actually works by hitting a known authenticated endpoint."""
    print(f"\n  → Testing live API call for {platform} …")
    import httpx, json
    from pathlib import Path
    root = Path(__file__).parent.parent.parent
    # Note: must be run on Mac (not in a sandboxed VM) for external requests to succeed

    if platform == "aqarsas":
        sf = root / ".aqarsas_session.json"
        if not sf.exists():
            print("    No session file — skipping"); return
        from extractors.aqarsas_extractor import _build_httpx_cookies
        cookie_list = json.loads(sf.read_text()).get("cookies", [])
        jar = _build_httpx_cookies(cookie_list)
        hdrs = {
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://aqarsas.sa",
            "Referer": "https://aqarsas.sa/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        try:
            async with httpx.AsyncClient(cookies=jar, headers=hdrs, follow_redirects=True) as c:
                r = await c.get("https://api.aqarsas.sa/useractivity/?limit=1&activity_type=deals:qitahs:ejar", timeout=10)
                try:
                    body = r.json()
                    rc = body.get("ResponseCode", "?")
                    if rc == 7:
                        print(f"    ⚠️  HTTP {r.status_code} ResponseCode=7 — not authorized (cookies not crossing subdomain)")
                    elif rc == 8:
                        print(f"    ⚠️  HTTP {r.status_code} ResponseCode=8 — malformed (missing required param or wrong format)")
                        print(f"    Response: {body}")
                    else:
                        print(f"    ✅ HTTP {r.status_code}  ResponseCode={rc}  keys={list(body.keys())[:5]}")
                except Exception:
                    print(f"    HTTP {r.status_code}  body={r.text[:200]}")
        except Exception as e:
            print(f"    ⚠️  Network error (run this script on Mac, not in VM): {type(e).__name__}: {str(e)[:80]}")

    elif platform == "paseetah":
        sf = root / ".paseetah_session.json"
        if not sf.exists():
            print("    No session file — skipping"); return
        cookies = json.loads(sf.read_text()).get("cookies", {})
        xsrf = cookies.get("XSRF-TOKEN", "")
        jar = httpx.Cookies()
        for name, value in cookies.items():
            jar.set(name, value, domain="paseetah.com")
        try:
            async with httpx.AsyncClient(cookies=jar, follow_redirects=True,
                headers={"Accept":"application/json","X-XSRF-TOKEN": xsrf,
                         "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}) as c:
                # Auth check: /api/user returns {is_logged_in, permissions}
                r = await c.get("https://paseetah.com/api/user", timeout=10)
                print(f"    HTTP {r.status_code}  content-type={r.headers.get('content-type','')[:40]}")
                if r.status_code == 200:
                    body = r.json()
                    logged_in = body.get("is_logged_in", False)
                    if logged_in:
                        print(f"    ✅ Paseetah session authenticated (is_logged_in=true)")
                        # Quick data endpoint test
                        r2 = await c.get("https://paseetah.com/api/get_all_cities", timeout=10)
                        print(f"    → /api/get_all_cities: HTTP {r2.status_code}")
                    else:
                        print(f"    ⚠️  Session exists but NOT authenticated (is_logged_in=false)")
                        print(f"    → Run: python infra/scripts/save_paseetah_session.py")
                else:
                    print(f"    ❌ Unexpected response: {r.status_code}")
        except Exception as e:
            print(f"    ⚠️  Network error (run this script on Mac, not in VM): {type(e).__name__}: {str(e)[:80]}")


async def main():
    aq_ok, ps_ok = await asyncio.gather(test_aqarsas(), test_paseetah())
    if aq_ok:
        await test_api_call("aqarsas")
    if ps_ok:
        await test_api_call("paseetah")

    print("\n" + "="*55)
    print("SUMMARY")
    print("="*55)
    print(f"  AqarSAS:  {'✅ Session ready' if aq_ok else '❌ Failed'}")
    print(f"  Paseetah: {'✅ Session ready' if ps_ok else '⚠️  Needs manual login (run save_paseetah_session.py)'}")


if __name__ == "__main__":
    asyncio.run(main())
