import asyncio
from playwright.async_api import async_playwright
import os

async def diagnose_facebook_dialogs():
    async with async_playwright() as p:
        print("🔍 Connecting to Chrome on 9292 for Diagnosis...")
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            print(f"🌐 Current Page URL: {page.url}")
            
            # 1. Capture current state screenshot
            await page.screenshot(path="debug_state_1.png")
            print("📸 Captured initial screenshot: debug_state_1.png")
            
            # 2. Try to find and click the "Create Post" button if it exists
            trigger = page.locator('div[role="button"]:has-text("สร้างโพสต์สาธารณะ"), div[role="button"]:has-text("เขียนอะไรสักหน่อย")').first
            if await trigger.is_visible():
                print("✅ Found 'Create Post' trigger. Clicking...")
                await trigger.click()
                await asyncio.sleep(5) # Wait for dialog to appear
                await page.screenshot(path="debug_state_2_after_click.png")
                print("📸 Captured after-click screenshot: debug_state_2_after_click.png")
            else:
                print("❌ 'Create Post' trigger not found on this page.")
            
            # 3. List ALL dialogs and their attributes
            dialogs = await page.query_selector_all('div[role="dialog"]')
            print(f"📊 Found {len(dialogs)} dialogs on page.")
            
            for i, d in enumerate(dialogs):
                label = await d.get_attribute("aria-label")
                labelledby = await d.get_attribute("aria-labelledby")
                inner_text = await d.inner_text()
                is_visible = await d.is_visible()
                print(f"--- Dialog {i+1} ---")
                print(f"  Label: {label}")
                print(f"  LabelledBy: {labelledby}")
                print(f"  Visible: {is_visible}")
                print(f"  Text Sample: {inner_text[:100]}...")
                
                # Check for textbox inside this dialog
                textbox = await d.query_selector('div[role="textbox"], [contenteditable="true"]')
                print(f"  Has Textbox: {textbox is not None}")

        except Exception as e:
            print(f"❌ Diagnosis failed: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_facebook_dialogs())
