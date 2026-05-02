import os
import time
import random
import re
from playwright.sync_api import sync_playwright
import browser_core
import config

def handle_microsoft_interrupts(page):
    """
    Handles common Microsoft login interrupts like 'Stay signed in' or 'More information required'.
    """
    print("[System] Checking for Microsoft security interrupts...")
    
    # Wait a bit for the page to settle
    time.sleep(5)
    
    # 1. 'Stay signed in?' prompt
    try:
        # Try different names for 'Yes' depending on language
        stay_signed_in_btn = page.get_by_role("button", name=re.compile(r"Yes|ใช่"))
        if stay_signed_in_btn.is_visible(timeout=5000):
            print("[Action] Clicking 'Yes' on Stay signed in prompt")
            stay_signed_in_btn.click()
            time.sleep(2)
    except:
        pass

    # 2. 'More information required' interrupt
    # This one often requires manual intervention if it's a real SSPR interrupt
    # We check if the URL contains 'interrupt' or if we are still on a login-like domain
    current_url = page.url.lower()
    if "interrupt" in current_url or "kmsi" in current_url or "login.microsoftonline.com" in current_url:
        print("⚠️ [Warning] Detected a security interrupt or login prompt.")
        print(f"Current URL: {page.url}")
        print("Please check the browser window and manually complete any required steps (like clicking 'Next' or 'Skip').")
        print("The bot will wait for up to 60 seconds for you to handle this...")
        
        # Wait for either the interrupt to disappear or for a timeout
        for i in range(60):
            new_url = page.url.lower()
            if "onedrive" in new_url and "interrupt" not in new_url:
                print("[System] Interrupt cleared! Proceeding...")
                time.sleep(3) # Let the page load
                return True
            time.sleep(1)
            if i % 10 == 0:
                print(f"   ...waiting for manual action ({60-i}s left)")
        
    return "onedrive" in page.url.lower()

def upload_to_onedrive(file_path, target_folder=None, launch_new=True):
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return False

    print(f"\n📦 Preparing to upload: {os.path.basename(file_path)}")
    
    # 1. Launch Browser (Only if requested)
    if launch_new:
        print("[System] Launching a fresh browser instance...")
        if not browser_core.launch_independent_browser("https://onedrive.live.com"):
            return False
    else:
        print("[System] Connecting to the CURRENTLY OPEN browser...")

    with sync_playwright() as p:
        try:
            # 2. Connect to the browser
            print("[System] Connecting to browser instance...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            # Give it all a moment to sync
            time.sleep(2)
            
            # Find the OneDrive page among open pages
            page = None
            for cp in context.pages:
                if "onedrive" in cp.url.lower() or "sharepoint" in cp.url.lower():
                    page = cp
                    print(f"[System] Found existing OneDrive page: {cp.url}")
                    break
            
            if not page:
                print("[System] No OneDrive page found, creating a new one.")
                page = context.new_page()
                page.goto("https://onedrive.live.com")
            
            # 3. Handle Login/Interrupts
            handle_microsoft_interrupts(page)
            
            # Wait for OneDrive to load (looking for the upload trigger)
            print("[Action] Waiting for OneDrive dashboard to be ready...")
            try:
                # Combined selector for standard OneDrive and SharePoint OneDrive
                page.wait_for_selector('button[title*="Create or upload"], button:has-text("Add new"), button:has-text("Upload"), button:has-text("เพิ่มใหม่")', timeout=60000)
            except:
                print("❌ [Error] Timeout waiting for OneDrive to load. Are you logged in?")
                return False
            
            # 4. Trigger Upload
            print("[Action] Triggering upload flow...")
            
            # Selectors include "Create or upload" (SharePoint style) and others
            upload_trigger = page.get_by_role("button", name=re.compile(r"Create or upload|Add new|เพิ่มใหม่|Upload|อัปโหลด", re.IGNORECASE))
            
            if not upload_trigger.is_visible():
                # Fallback to title-based selector for SharePoint
                upload_trigger = page.locator('button[title*="Create or upload"]')

            if upload_trigger.is_visible():
                print(f"   [Mode] Using trigger: {upload_trigger.get_attribute('title') or 'Upload button'}")
                upload_trigger.click()
                time.sleep(2) # Give menu time to animate
                
                # Wait for menu and click "Files upload"
                print("   [Action] Clicking 'Files upload' menu item...")
                try:
                    with page.expect_file_chooser(timeout=20000) as fc_info:
                        # Sequential attempt for reliability
                        menu_selectors = [
                            'role=menuitem[name*="Files upload"]',
                            '[role="menuitem"][title*="Files upload"]',
                            'button[title*="Files upload"]',
                            'span:has-text("Files upload")',
                            'button:has-text("Files upload")'
                        ]
                        
                        clicked = False
                        for sel in menu_selectors:
                            try:
                                item = page.locator(sel).first
                                if item.count() > 0:
                                    item.click(timeout=3000)
                                    clicked = True
                                    break
                            except:
                                continue
                        
                        if not clicked:
                            raise Exception("Could not find or click any menu item for upload")
                    
                    file_chooser = fc_info.value
                    file_chooser.set_files(file_path)
                except Exception as menu_err:
                    print(f"⚠️ [Warning] Failed to click upload menu item: {str(menu_err)}")
                    # Last resort: try to find any file input and set it directly
                    print("   [System] Attempting last resort: direct file input injection...")
                    file_input = page.query_selector('input[type="file"]')
                    if file_input:
                        file_input.set_input_files(file_path)
                    else:
                        raise menu_err
            else:
                print("❌ [Error] Could not find a suitable upload button.")
                return False

            print("[Status] File selected. Uploading...")
            
            # 5. Wait for success message (Toast)
            try:
                page.wait_for_selector('div[role="alert"], span:has-text("Uploaded"), span:has-text("อัปโหลด"), span:has-text("Finished")', timeout=45000)
                print(f"✅ [Success] Uploaded {os.path.basename(file_path)} successfully!")
                return True
            except:
                print("⚠️ [Warning] Upload might still be in progress or toast was missed. Please check the browser.")
                return True 

        except Exception as e:
            print(f"❌ [Error] Upload failed: {str(e)}")
            return False
        finally:
            print("[System] Closing connection.")

if __name__ == "__main__":
    TEST_FILE = os.path.expanduser("~/Desktop/test_upload.txt")
    # Ensure test file exists
    if not os.path.exists(TEST_FILE):
        with open(TEST_FILE, "w") as f:
            f.write("Test upload content from Antigravity bot.")
            
    upload_to_onedrive(TEST_FILE)
