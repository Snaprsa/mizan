"""
Debug AqarSAS login via real browser to see the visual error message.
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from dotenv import load_dotenv
load_dotenv()

async def main():
    from playwright.async_api import async_playwright
    email = os.environ.get("AQARSAS_EMAIL", "")
    password = os.environ.get("AQARSAS_PASSWORD", "")
    print(f"Trying AqarSAS login with: {email}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Intercept all API requests
        api_calls = []
        async def on_request(req):
            if "api.aqarsas" in req.url:
                api_calls.append({"url": req.url, "method": req.method})
        async def on_response(resp):
            if "api.aqarsas" in resp.url:
                try:
                    body = await resp.json()
                    api_calls.append({"url": resp.url, "status": resp.status, "body": body})
                except:
                    api_calls.append({"url": resp.url, "status": resp.status})

        page.on("request", on_request)
        page.on("response", on_response)

        await page.goto("https://aqarsas.sa/login", wait_until="load", timeout=30000)
        await page.wait_for_timeout(1500)

        # Fill form
        await page.locator('input[name="email"]').fill(email)
        await page.locator('input[name="password"]').fill(password)
        await page.locator('button[type="submit"], input[type="submit"]').first.click()

        # Wait for response
        await page.wait_for_timeout(4000)

        # Check for error messages on page
        error_selectors = [
            ".error", ".alert", "[class*=error]", "[class*=alert]",
            "[class*=Error]", "p.text-red", ".text-red-500", ".text-danger"
        ]
        error_text = ""
        for sel in error_selectors:
            try:
                el = page.locator(sel).first
                t = await el.inner_text(timeout=500)
                if t.strip():
                    error_text += f"[{sel}]: {t.strip()}\n"
            except:
                pass

        current_url = page.url
        print(f"\nCurrent URL after submit: {current_url}")
        print(f"Error messages found: {error_text or 'none'}")
        print(f"\nAPI calls captured:")
        for call in api_calls:
            print(f"  {call}")

        await browser.close()

asyncio.run(main())
