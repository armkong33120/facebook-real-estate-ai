import os
import time
import json
import random
import glob
from playwright.sync_api import sync_playwright
import google.generativeai as genai
import browser_core
import config

# Configuration
PROPERTY_DATA_DIR = os.path.expanduser("~/Desktop/Facebook_Property_Data")
GROUP_ANALYSIS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "group_analysis.json")
POSTING_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posting_history.json")

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
MODEL_NAME = config.MODEL_NAME

def load_posting_history():
    if os.path.exists(POSTING_HISTORY_FILE):
        with open(POSTING_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_posting_history(history):
    with open(POSTING_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def get_properties_to_post():
    """Scans the property data directory for folders containing images and text"""
    properties = []
    # Structure: Province / District / PropertyID
    provinces = [d for d in os.listdir(PROPERTY_DATA_DIR) if os.path.isdir(os.path.join(PROPERTY_DATA_DIR, d)) and not d.startswith('_')]
    
    for province in provinces:
        prov_path = os.path.join(PROPERTY_DATA_DIR, province)
        districts = [d for d in os.listdir(prov_path) if os.path.isdir(os.path.join(prov_path, d))]
        
        for district in districts:
            dist_path = os.path.join(prov_path, district)
            prop_ids = [d for d in os.listdir(dist_path) if os.path.isdir(os.path.join(dist_path, d))]
            
            for prop_id in prop_ids:
                prop_path = os.path.join(dist_path, prop_id)
                images = glob.glob(os.path.join(prop_path, "*.jpg")) + glob.glob(os.path.join(prop_path, "*.png"))
                txt_files = glob.glob(os.path.join(prop_path, "*.txt"))
                
                if images and txt_files:
                    # Find the main txt file (usually matches original name)
                    desc_file = txt_files[0]
                    properties.append({
                        "id": prop_id,
                        "province": province,
                        "district": district,
                        "images": sorted(images),
                        "desc_path": desc_file,
                        "path": prop_path
                    })
    return properties

def clean_text_for_group(text, rules):
    """Uses AI to adjust the property description based on group rules"""
    if not rules or "Rules not found" in rules:
        return text
    
    # Quick check: if rules say "No links", we should probably strip them
    if "ห้ามลงลิ้งก์" in rules or "No links" in rules:
        # Simple regex to strip common URLs
        text = re.sub(r'https?://\S+', '', text)
    
    return text

def post_to_facebook_group(page, group_url, property_info):
    """Automates the posting process in a single group"""
    print(f"   [Action] Navigating to group: {group_url}")
    page.goto(group_url, wait_until="networkidle", timeout=60000)
    time.sleep(random.uniform(3, 5))

    try:
        # 1. Click the "Create a public post" or "Write something" trigger
        # Facebook's selectors change often, so we try multiple common ones
        post_trigger_selectors = [
            'span:has-text("Create a public post...")',
            'span:has-text("Write something...")',
            'div[role="button"]:has-text("Create a public post...")',
            'span:has-text("เลือกรูปภาพ")', # Sometimes it's the photo button directly
            'div[aria-label*="สร้างโพสต์"]',
            'div[aria-label*="Create a post"]'
        ]
        
        found_trigger = False
        for sel in post_trigger_selectors:
            trigger = page.query_selector(sel)
            if trigger and trigger.is_visible():
                trigger.click()
                found_trigger = True
                break
        
        if not found_trigger:
            # Fallback: Try to find any clickable area in the composer section
            page.mouse.click(500, 400) # Aim for the middle-top area
            time.sleep(2)

        time.sleep(2)
        
        # 2. Upload Images
        # We look for the hidden file input
        file_input = page.query_selector('input[type="file"][accept*="image"]')
        if file_input:
            # Limit to 10 images to avoid UI lag/limits
            files_to_upload = property_info["images"][:10]
            print(f"   [Action] Uploading {len(files_to_upload)} images...")
            file_input.set_input_files(files_to_upload)
            time.sleep(5) # Wait for upload progress
        
        # 3. Paste Description
        with open(property_info["desc_path"], 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        # Clean text based on rules (this is where you'd call clean_text_for_group)
        # For now, let's just use the raw text or simple cleanup
        msg_box = page.query_selector('div[role="textbox"]')
        if msg_box:
            print("   [Action] Typing description...")
            msg_box.fill(full_text)
            time.sleep(2)
        
        # 4. Final Click Post
        post_btn = page.query_selector('div[aria-label="Post"], div[aria-label="โพสต์"]')
        if post_btn:
            print("   [Action] Clicking POST button!")
            # post_btn.click() # Uncomment this for FULL AUTO
            print("   [Status] Success! (Simulated - click() is currently commented for safety)")
            return True
        else:
            print("   [Error] Post button not found.")
            return False

    except Exception as e:
        print(f"   [Error] Posting failed: {str(e)}")
        return False

def run_poster():
    print("🚀 Starting Facebook Property Posting Bot...")
    
    # Load required data
    all_properties = get_properties_to_post()
    if not os.path.exists(GROUP_ANALYSIS_FILE):
        print(f"❌ Error: {GROUP_ANALYSIS_FILE} not found. Run collector first.")
        return
        
    with open(GROUP_ANALYSIS_FILE, 'r', encoding='utf-8') as f:
        group_data = json.load(f)
    
    history = load_posting_history()
    
    # Filter for property groups and sort by relevance
    property_groups = {url: data for url, data in group_data.items() if data.get("is_property")}
    
    if not all_properties:
        print("[System] No properties found in Desktop directory.")
        return

    # Select property to post
    # In a real run, you might loop through all, but let's start with the newest or a random one
    target_property = all_properties[0] 
    print(f"\n📦 Selected Property: {target_property['id']} ({target_property['district']}, {target_property['province']})")

    # Match groups
    matched_groups = []
    for url, data in property_groups.items():
        name = data["name"].lower()
        relevance = 0
        if target_property["district"].lower() in name: relevance += 10
        if target_property["province"].lower() in name: relevance += 5
        if relevance > 0:
            matched_groups.append((relevance, url))
    
    # Sort by relevance high to low
    matched_groups.sort(key=lambda x: x[0], reverse=True)
    
    if not matched_groups:
        print("[System] No highly relevant groups found. Using general property groups.")
        # Just grab some random property groups if no specific match
        general_groups = list(property_groups.keys())[:5]
        matched_groups = [(0, url) for url in general_groups]

    print(f"🎯 Matched {len(matched_groups)} potential groups.")

    # 1. Launch Browser
    if not browser_core.launch_independent_browser(): return

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            posts_done = 0
            MAX_POSTS = 5 # Safety limit per session

            for rel, url in matched_groups:
                if posts_done >= MAX_POSTS: break
                
                # Check history
                history_key = f"{target_property['id']}_{url}"
                if history_key in history:
                    print(f"⏩ Already posted {target_property['id']} to {url}. Skipping.")
                    continue
                
                print(f"\n--- Posting Task {posts_done+1}/{MAX_POSTS} ---")
                success = post_to_facebook_group(page, url, target_property)
                
                if success:
                    history[history_key] = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "property": target_property['id'],
                        "group": url
                    }
                    save_posting_history(history)
                    posts_done += 1
                    
                    # Human-like cooldown
                    wait_time = random.uniform(300, 600) # 5-10 minutes
                    print(f"⏳ Sleeping for {wait_time/60:.1f} minutes to avoid spam detection...")
                    time.sleep(wait_time)

            print("\n" + "="*40)
            print("✨ POSTING SESSION FINISHED")
            print(f"Total properties posted: {posts_done}")
            print("="*40)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
        finally:
            print("[System] Closing.")

if __name__ == "__main__":
    run_poster()
