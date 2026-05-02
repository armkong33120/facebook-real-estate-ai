
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            print("Navigating to Groups home...")
            await page.goto("https://www.facebook.com/groups/feed/", wait_until="commit")
            await page.wait_for_timeout(7000) # Give it time to render
            
            await page.screenshot(path="/Users/your_username/Desktop/fb_groups_home_v2.png")
            print("Screenshot saved.")
                
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
