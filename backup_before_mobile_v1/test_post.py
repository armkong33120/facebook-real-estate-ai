
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            group_url = "https://www.facebook.com/groups/506820490090145"
            print(f"Navigating to group: {group_url}")
            
            await page.goto(group_url, wait_until="commit")
            await page.wait_for_timeout(5000) # Wait for UI
            
            await page.screenshot(path="/Users/your_username/Desktop/fb_group_view.png")
            
            # Look for the post box
            # Facebook often uses role="button" with text containing "Write something" or "สร้างโพสต์"
            post_box = page.get_by_role("button", name="Write something")
            if await post_box.count() == 0:
                 post_box = page.get_by_role("button", name="สร้างโพสต์")
            
            if await post_box.count() > 0:
                print("Found post box, clicking...")
                await post_box.first.click()
                await page.wait_for_timeout(2000)
                
                # Try to type something
                # Usually there's a div with role="textbox"
                textbox = page.get_by_role("textbox")
                if await textbox.count() > 0:
                    await textbox.first.fill("Test post to check status - " + str(asyncio.get_event_loop().time()))
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path="/Users/your_username/Desktop/fb_typing_test.png")
                    print("Typed test message and took screenshot.")
                else:
                    print("Could not find textbox after clicking post box.")
            else:
                print("Could not find post box. Maybe not a member or blocked from viewing?")
                
            await page.screenshot(path="/Users/your_username/Desktop/fb_final_check.png")
            
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
