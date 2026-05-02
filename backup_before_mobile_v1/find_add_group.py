
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Go to Groups home
            print("Navigating to Groups home...")
            await page.goto("https://www.facebook.com/groups/feed/", wait_until="networkidle")
            await page.wait_for_timeout(5000)
            
            # Take a screenshot to find "เพิ่มกลุ่ม"
            await page.screenshot(path="/Users/your_username/Desktop/fb_groups_home.png")
            
            # Search for the text "เพิ่มกลุ่ม" in the page
            content = await page.content()
            if "เพิ่มกลุ่ม" in content:
                print("Found 'เพิ่มกลุ่ม' in page content.")
            else:
                print("'เพิ่มกลุ่ม' not found in page content.")
                
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
