
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Wait for FB to load if it's still loading
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Take a screenshot to see where we are
            await page.screenshot(path="/Users/your_username/Desktop/fb_check_status.png")
            print(f"Screenshot saved. Current URL: {page.url}")
            
            await browser.close()
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
