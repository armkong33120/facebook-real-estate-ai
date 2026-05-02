
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Navigate to the group again to trigger the modal
            group_url = "https://www.facebook.com/groups/506820490090145"
            await page.goto(group_url)
            await page.wait_for_timeout(5000)
            
            # Click the post box
            await page.get_by_text("เขียนอะไรสักหน่อย....").first.click()
            await page.wait_for_timeout(3000)
            
            # Take a high-res screenshot of the modal
            await page.screenshot(path="/Users/your_username/Desktop/fb_modal_full.png")
            print("Modal screenshot saved.")

        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
