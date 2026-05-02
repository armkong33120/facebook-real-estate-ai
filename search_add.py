
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Find all elements containing "เพิ่ม"
            elements = await page.query_selector_all("text='เพิ่ม'")
            print(f"Found {len(elements)} elements with text 'เพิ่ม'")
            for i, el in enumerate(elements):
                text = await el.inner_text()
                print(f"Element {i}: '{text}'")
            
            # Also check for "Add" in case it's English
            elements_en = await page.query_selector_all("text='Add'")
            print(f"Found {len(elements_en)} elements with text 'Add'")

        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
