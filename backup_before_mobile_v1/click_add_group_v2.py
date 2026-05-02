
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Ensure modal is open
            if await page.get_by_text("สร้างโพสต์").count() == 0:
                print("Opening modal...")
                await page.get_by_text("เขียนอะไรสักหน่อย....").first.click()
                await page.wait_for_timeout(3000)

            # Try to find the button by different strategies
            print("Searching for '+ เพิ่มกลุ่ม' button...")
            
            # Try finding elements containing "เพิ่มกลุ่ม"
            # We can use a CSS selector for elements containing the text
            btn = page.locator("xpath=//*[contains(text(), 'เพิ่มกลุ่ม')]")
            
            if await btn.count() > 0:
                print(f"Found {await btn.count()} elements with 'เพิ่มกลุ่ม'. Clicking the first visible one...")
                for i in range(await btn.count()):
                    if await btn.nth(i).is_visible():
                        await btn.nth(i).click()
                        print("Clicked!")
                        await page.wait_for_timeout(3000)
                        
                        # Now look for search
                        await page.screenshot(path="/Users/your_username/Desktop/fb_after_click_add.png")
                        
                        search_box = page.get_by_placeholder("ค้นหากลุ่ม")
                        if await search_box.count() > 0:
                            await search_box.first.fill("อสังหา")
                            await page.wait_for_timeout(3000)
                            await page.screenshot(path="/Users/your_username/Desktop/fb_add_group_results.png")
                            print("Success! Search results captured.")
                            return
            else:
                print("No elements with 'เพิ่มกลุ่ม' found via XPath.")
                # Take a screenshot to see if the modal is actually open
                await page.screenshot(path="/Users/your_username/Desktop/fb_modal_check_2.png")

        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
