
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Search for any element containing "เพิ่มกลุ่ม"
            elements = await page.query_selector_all("text='เพิ่มกลุ่ม'")
            print(f"Found {len(elements)} elements with text 'เพิ่มกลุ่ม'")
            
            for i, el in enumerate(elements):
                box = await el.bounding_box()
                print(f"Element {i}: Visible={await el.is_visible()}, Box={box}")
                if await el.is_visible():
                    # Take a small screenshot of the element
                    await page.screenshot(path=f"/Users/your_username/Desktop/element_find_{i}.png", clip=box)
            
            # If no elements found with exact text, search for partial
            if not elements:
                all_text = await page.evaluate("() => document.body.innerText")
                if "เพิ่มกลุ่ม" in all_text:
                    print("'เพิ่มกลุ่ม' exists in innerText but maybe not as a simple text node.")
                else:
                    print("'เพิ่มกลุ่ม' not found in innerText.")

        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
