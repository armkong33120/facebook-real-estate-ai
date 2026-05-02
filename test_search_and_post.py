
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Step 1: Test searching for a group name
            search_query = "Bangkok Property"
            print(f"Searching for groups: {search_query}")
            await page.goto(f"https://www.facebook.com/search/groups/?q={search_query}")
            await page.wait_for_timeout(5000)
            await page.screenshot(path="/Users/your_username/Desktop/fb_search_result.png")
            
            # Step 2: Go back to the previous group and try to click the post box using the Thai text
            group_url = "https://www.facebook.com/groups/506820490090145"
            await page.goto(group_url)
            await page.wait_for_timeout(5000)
            
            # Try to click the box with Thai text
            post_box_thai = page.get_by_text("เขียนอะไรสักหน่อย....")
            if await post_box_thai.count() > 0:
                print("Found Thai post box, clicking...")
                await post_box_thai.first.click()
                await page.wait_for_timeout(3000)
                
                # Check for "สร้างโพสต์สาธารณะ" (Create public post) or similar in the popup
                await page.screenshot(path="/Users/your_username/Desktop/fb_post_popup.png")
                
                textbox = page.get_by_role("textbox")
                if await textbox.count() > 0:
                    await textbox.first.fill("สวัสดีครับ ทดสอบระบบโพสต์เฉยๆ ครับ")
                    await page.wait_for_timeout(2000)
                    await page.screenshot(path="/Users/your_username/Desktop/fb_typed_thai.png")
                else:
                    print("Could not find textbox in popup.")
            else:
                print("Still could not find the post box with Thai text.")
                
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
