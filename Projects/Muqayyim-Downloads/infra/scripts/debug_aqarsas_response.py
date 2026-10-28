"""
Debug: Print the full raw API response from AqarSAS landdetails endpoint.
Run from project root: python infra/scripts/debug_aqarsas_response.py
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()


async def main():
    from extractors.aqarsas_extractor import _get_session, _build_httpx_cookies, AQARSAS_API, AQARSAS_BASE
    import httpx

    print("Loading session...")
    cookie_list = await _get_session()
    jar = _build_httpx_cookies(cookie_list)

    headers = {
        "Accept": "application/json",
        "Origin": AQARSAS_BASE,
        "Referer": AQARSAS_BASE + "/",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }

    url = f"{AQARSAS_API}/landdetails/?id=2203382&src=aqarsasteam"
    print(f"Fetching: {url}\n")

    async with httpx.AsyncClient(cookies=jar, headers=headers, follow_redirects=True) as client:
        r = await client.get(url, timeout=15)
        print(f"Status: {r.status_code}")
        try:
            data = r.json()
            print(f"\nFull response JSON:")
            print(json.dumps(data, ensure_ascii=False, indent=2))

            # Show the Obj/data section specifically
            obj = data.get("Obj") or data.get("obj") or data.get("data")
            if obj:
                print(f"\n--- Obj keys: {list(obj.keys()) if isinstance(obj, dict) else type(obj)} ---")
            else:
                print(f"\n--- No Obj found. Top-level keys: {list(data.keys())} ---")
        except Exception as e:
            print(f"Could not parse JSON: {e}")
            print(r.text[:2000])


if __name__ == "__main__":
    asyncio.run(main())
