
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            # Connect to the browser
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
            
            # Use the existing page or create a new one
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()
            
            print(f"Connected. Current URL: {page.url}")
            
            # Go to Facebook Home first to ensure we are logged in
            if "facebook.com" not in page.url:
                await page.goto("https://www.facebook.com", wait_until="networkidle")
            
            # Wait for content
            await page.wait_for_timeout(3000)
            
            # Take a screenshot of the home page
            await page.screenshot(path="/Users/your_username/Desktop/fb_home_check.png")
            print("Home screenshot saved.")
            
            # Try to search for a group as requested
            # Searching for "ขายบ้าน" (Sell house) as a test
            search_query = "ขายบ้าน"
            print(f"Searching for groups: {search_query}")
            
            # Navigate to search groups directly
            await page.goto(f"https://www.facebook.com/groups/search/groups/?q={search_query}")
            await page.wait_for_timeout(5000)
            await page.screenshot(path="/Users/your_username/Desktop/fb_search_groups.png")
            print("Search screenshot saved.")
            
            # Just stay here for a bit so I can report back
            
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(run())
