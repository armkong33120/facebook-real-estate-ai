
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # 1. Click the "+ เพิ่มกลุ่ม" button
            # From vision analysis, it's near the top under the profile name
            # We can try to find it by text or aria-label
            add_group_btn = page.get_by_text("+ เพิ่มกลุ่ม")
            if await add_group_btn.count() > 0:
                print("Clicking '+ เพิ่มกลุ่ม'...")
                await add_group_btn.first.click()
                await page.wait_for_timeout(3000)
                
                # 2. Look for the search input in the newly opened view
                # Usually it has a placeholder like "ค้นหากลุ่ม"
                search_input = page.get_by_placeholder("ค้นหากลุ่ม")
                if await search_input.count() == 0:
                    # Fallback to any textbox in the dialog
                    search_input = page.get_by_role("textbox")
                
                if await search_input.count() > 0:
                    search_term = "คอนโด" # Test search term
                    print(f"Typing search term: {search_term}")
                    await search_input.first.fill(search_term)
                    await page.wait_for_timeout(3000)
                    
                    await page.screenshot(path="/Users/your_username/Desktop/fb_add_group_search.png")
                    print("Search screenshot saved.")
                else:
                    print("Could not find search input after clicking '+ เพิ่มกลุ่ม'.")
                    await page.screenshot(path="/Users/your_username/Desktop/fb_add_group_failed_search.png")
            else:
                print("Could not find '+ เพิ่มกลุ่ม' button.")
                
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
