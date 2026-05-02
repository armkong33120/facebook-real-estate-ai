import os
import sys
import time
import re
import json
import random
from playwright.sync_api import sync_playwright
import google.generativeai as genai
import browser_core
import config

# Configuration
TARGET_URL = "https://www.facebook.com/groups/joins/?nav_source=tab&ordering=viewer_added"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "group_analysis.json")
# Forced reset for a fresh start requested by user
if os.path.exists(DATA_FILE):
    os.remove(DATA_FILE)
    print("🗑️ Database reset: Starting fresh as requested.")

PROPERTY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "group_rules.txt")
LINKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all_links.txt")
OTHER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "other_groups.txt")
TARGET_COUNT = 9999  # Collecting all groups (unlimited)

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
MODEL_NAME = config.MODEL_NAME

def load_existing_analysis():
    """Loads previous analysis to allow resuming"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_current_analysis(data):
    """Saves the ongoing analysis to prevent data loss"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Warning: Could not auto-save data: {str(e)}")

def clean_group_name(text):
    """Strips noise from Facebook group list items like notifications and welcome messages"""
    if not text: return ""
    # Remove notification prefixes and suffixes
    text = re.sub(r'ยังไม่ได้อ่าน', '', text)
    text = re.sub(r'ยินดีต้อนรับสู่ ', '', text)
    text = re.sub(r'ตอนนี้คุณสามารถโพสต์.*$', '', text, flags=re.DOTALL)
    # Remove member counts and timestamps
    text = re.sub(r'สมาชิก [\d.,]+ หมื่น? คน', '', text)
    text = re.sub(r'[\d.,]+ (หมื่น|พัน|ล้าน) คน', '', text)
    text = re.sub(r'\d+ (ชั่วโมง|นาที|วัน|สัปดาห์|เดือน|ปี)', '', text)
    # Get only the first line (usually the name)
    text = text.split('\n')[0].strip()
    return text

def batch_categorize_with_ai(names):
    """Uses Gemini to categorize a BATCH of group names as Property/Non-Property"""
    if not names: return []
    print(f"   [AI] Batch Categorizing {len(names)} names...")
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        names_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(names)])
        prompt = f"""วิเคราะห์รายชื่อกลุ่ม Facebook ต่อไปนี้ว่าเกี่ยวข้องกับ "อสังหาริมทรัพย์" (ซื้อ/ขาย/เช่า บ้าน, ที่ดิน, คอนโด) หรือไม่?
        กติกา: ตอบ NUMBER: YES หรือ NUMBER: NO เท่านั้น หนึ่งบรรทัดต่อหนึ่งกลุ่ม
        
        รายชื่อ:
        {names_list}
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        results = [False] * len(names)
        matches = re.findall(r"(\d+):\s*(YES|NO)", text, re.IGNORECASE)
        for idx_str, val in matches:
            idx = int(idx_str) - 1
            if 0 <= idx < len(names): results[idx] = (val.upper() == "YES")
        return results
    except Exception as e:
        print(f"   [AI Error] {str(e)}")
        return [False] * len(names)

def analyze_posting_rules_with_ai(name, about_text):
    """Uses Gemini to extract posting rules from group description"""
    if not about_text: return "No rules found."
    print(f"   [AI] Analyzing rules for: {name}...")
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = f"""
        คุณเป็นผู้ช่วยจัดการข้อมูลอสังหาริมทรัพย์ หน้าที่ของคุณคือการอ่านข้อมูลดิบที่ได้จาก Facebook Group และสกัดเอา "กฎของกลุ่ม" หรือ "รายละเอียดกลุ่ม" ที่เจ้าของกลุ่มตั้งไว้จริงๆ ออกมา

        ชื่อกลุ่ม: "{name}"
        ข้อมูลดิบที่ได้มา:
        {about_text}
        
        กติกาการสกัดข้อมูล:
        1. ตัดข้อความขยะที่ไม่เกี่ยวข้องกับกฎกลุ่มออกให้หมด (เช่น จำนวนแจ้งเตือน, ชื่อผู้สร้างกลุ่ม, จำนวนสมาชิก, ปุ่มเชิญ, ปุ่มแชร์, เมนูต่างๆ ของ Facebook)
        2. สรุปเฉพาะส่วนที่เป็น "กฎการโพสต์" หรือ "สิ่งที่กลุ่มต้องการ" เท่านั้น
        3. หากข้อมูลดิบไม่มีข้อมูลเกี่ยวกับกฎกลุ่มเลย หรือมีแต่ขยะ ให้ตอบว่า "ไม่มีข้อมูลกฎกลุ่ม"
        
        ผลลัพธ์:
        """
        response = model.generate_content(prompt)
        result = response.text.strip()
        if "ไม่มีข้อมูลกฎกลุ่ม" in result:
            return None
        return result
    except Exception as e:
        print(f"   [AI Rule Error] {str(e)}")
        return "Analysis failed."

def collect_and_analyze():
    print(f"🚀 Starting Comprehensive Group Collector & Rule Analyzer (Collecting ALL groups)")
    
    # 0. Load Existing Data for Resume
    discovered_groups = load_existing_analysis()
    if discovered_groups:
        print(f"🔄 Resuming from previous run. Loaded {len(discovered_groups)} groups.")

    if not browser_core.launch_independent_browser(url=TARGET_URL): return

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            # --- PHASE 1: DISCOVERY & CATEGORIZATION ---
            print("\n" + "="*40 + "\nPHASE 1: DISCOVERING & CATEGORIZING GROUPS\n" + "="*40)
            last_count = 0
            no_change_count = 0
            
            while True:
                # 1. Capture ALL links that look like groups for transparent debugging
                raw_elements = page.query_selector_all("a[href*='/groups/']")
                
                # 2. Identify the actual "Cards" (containers)
                # On the 'joins' page, groups are typically inside div[role='listitem']
                cards = page.query_selector_all("div[role='listitem']")
                
                print(f"   [Raw Capture Log]")
                new_names_to_categorize = []
                batch_urls = []

                # First, log everything the bot sees (as requested by user)
                for el in raw_elements:
                    href = el.get_attribute("href") or ""
                    text = el.inner_text().strip().split('\n')[0]
                    clean_captured_name = clean_group_name(text)
                    
                    # Log raw findings
                    short_url = href.split('?')[0][-30:] if href else "None"
                    
                    # Filtering criteria
                    is_noise = False
                    reason = ""
                    
                    if not clean_captured_name:
                        is_noise, reason = True, "Empty Name"
                    elif any(term in clean_captured_name for term in ["ฟีดของคุณ", "ค้นพบ", "กลุ่มของคุณ", "สร้างกลุ่มใหม่", "ดูทั้งหมด"]):
                        is_noise, reason = True, "Sidebar Menu"
                    elif "permalink" in href or "notif_id" in href:
                        is_noise, reason = True, "Not a group root link"
                    elif len(clean_captured_name) < 3:
                        is_noise, reason = True, "Name too short"

                    # Print discovery status
                    if is_noise:
                        if clean_captured_name and len(clean_captured_name) > 1: # Only print non-empty noise
                            print(f"      [Raw] URL: ...{short_url} | Text: {clean_captured_name[:30]:<30} | ❌ IGNORED ({reason})")
                    else:
                        # Check if it's inside a listitem (Card) to be sure it's a real group card
                        # Usually, the group name in a card is in a specific SPAN or H-tag
                        # But for now, if it's not noise and has a clean URL, we consider it a candidate
                        pass

                # Actually process cards for valid data
                for card in cards:
                    # Within each card, find the main link (usually the one with the name)
                    # We look for a link that isn't the "Visit Group" button
                    card_links = card.query_selector_all("a[href*='/groups/']")
                    if not card_links: continue
                    
                    # The name is usually in the first link or one with a non-empty aria-label
                    target_link = None
                    for l in card_links:
                        l_text = l.inner_text().strip()
                        if l_text and l_text != "ดูกลุ่ม" and l_text != "Visit Group":
                            target_link = l
                            break
                    
                    if not target_link: target_link = card_links[0]
                    
                    href = target_link.get_attribute("href")
                    if not href: continue
                    
                    url_clean = href.split('?')[0].rstrip('/')
                    if url_clean in discovered_groups: continue
                    
                    full_url = url_clean if url_clean.startswith("http") else "https://www.facebook.com" + url_clean
                    name = clean_group_name(target_link.inner_text())
                    
                    if not name or name in ["ฟีดของคุณ", "ค้นพบ", "ดูกลุ่ม", "Visit Group"]: continue

                    discovered_groups[full_url] = {"name": name, "is_property": True, "rules": None}
                    print(f"      [Found] {name:<40} | ✅ SAVED") 
                    new_names_to_categorize.append(name)
                    batch_urls.append(full_url)
                    
                    if len(new_names_to_categorize) >= 20: 
                        save_current_analysis(discovered_groups)
                        new_names_to_categorize, batch_urls = [], []

                if new_names_to_categorize:
                    save_current_analysis(discovered_groups)

                current_count = len(discovered_groups)
                print(f"[Progress] Found {current_count} groups so far...")
                
                if current_count == last_count: 
                    no_change_count += 1
                    if no_change_count == 3:
                        diag_path = os.path.expanduser("~/Desktop/collector_diagnostic.png")
                        print(f"📸 Debug: No new groups for 3 cycles. Saving screenshot: {diag_path}")
                        page.screenshot(path=diag_path)
                    if no_change_count >= 10: break
                else: 
                    no_change_count = 0
                
                last_count = current_count
                page.evaluate("window.scrollBy(0, 1500)")
                time.sleep(3.0)

            # --- PHASE 2: RULE ANALYSIS (For Property Groups Only) ---
            # Reload to sync with Discovery
            property_groups = [url for url, data in discovered_groups.items() if data["is_property"]]
            print("\n" + "="*40 + f"\nPHASE 2: ANALYZING RULES FOR {len(property_groups)} PROPERTY GROUPS\n" + "="*40)
            
            for index, url in enumerate(property_groups):
                # SKIP if already analyzed in Phase 2
                if discovered_groups[url].get("rules") and "Analysis failed" not in discovered_groups[url]["rules"]:
                    print(f"[{index+1}/{len(property_groups)}] ⏩ Already analyzed: {discovered_groups[url]['name']}")
                    continue

                print(f"[{index+1}/{len(property_groups)}] Visiting: {discovered_groups[url]['name']}")
                try:
                    # Navigate directly to the 'About' page
                    about_url = url.rstrip('/') + "/about/" if "/about/" not in url else url
                    page.goto(about_url, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(4) 
                    
                    about_text = ""
                    # Priority: Find content by text headers or specific ARIA labels
                    header_selectors = [
                        "div:has(> span:text-is('เกี่ยวกับกลุ่มนี้')) + div",
                        "div:has(> span:text-is('About this group')) + div",
                        "div[aria-label='About']", 
                        "div[aria-label='เกี่ยวกับ']",
                        "div.x1iyjqo2.x1n2onr6" 
                    ]
                    
                    for selector in header_selectors:
                        try:
                            el = page.query_selector(selector)
                            if el:
                                about_text = el.inner_text().strip()
                                if about_text: break
                        except: continue
                    
                    if not about_text:
                        # Fallback: Just grab a chunk of text content that isn't headers/footers
                        about_text = page.evaluate("() => document.body.innerText.substring(0, 3000)")

                    # --- AI RULE ANALYSIS WITH FALLBACK ---
                    print(f"   [AI Filtering] Analyzing rules for quality...")
                    rules_summary = analyze_posting_rules_with_ai(discovered_groups[url]['name'], about_text)
                    
                    if not rules_summary:
                        print(f"   [Fallback] No real rules found. Using group name as rules.")
                        rules_summary = f"กฎกลุ่มพื้นฐาน (อ้างอิงจากชื่อกลุ่ม): {discovered_groups[url]['name']}"
                    
                    print(f"   [Processed Rules]: {rules_summary[:200]}...\n")
                    
                    discovered_groups[url]['rules'] = rules_summary
                    # AUTO-SAVE after individual rule analysis
                    save_current_analysis(discovered_groups)
                    
                except Exception as e_rule:
                    print(f"   [Error] Could not extract rules: {str(e_rule)}")
                    discovered_groups[url]['rules'] = "Failed to load group page."
                
                # Human-like delay between page visits
                time.sleep(random.uniform(3, 7))

            # --- PHASE 3: SAVING RESULTS ---
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(discovered_groups, f, indent=4, ensure_ascii=False)
            
            # 1. Save all links (URLs only) for the 474+ groups
            with open(LINKS_FILE, "w", encoding="utf-8") as f:
                for u in discovered_groups.keys():
                    f.write(f"{u}\n")
            
            # 2. Save group names and rules
            with open(PROPERTY_FILE, "w", encoding="utf-8") as f:
                for u, d in discovered_groups.items():
                    if d["is_property"]:
                        f.write(f"NAME: {d['name']}\nLINK: {u}\nRULES:\n{d['rules']}\n{'-'*50}\n")
            
            with open(OTHER_FILE, "w", encoding="utf-8") as f:
                for u, d in discovered_groups.items():
                    if not d["is_property"]: f.write(f"{d['name']} | {u}\n")

            # --- PHASE 4: SUMMARY REPORT ---
            print("\n" + "="*40)
            print("📊 FINAL SUMMARY REPORT")
            print("="*40)
            print(f"Total Groups Discovered : {len(discovered_groups)}")
            print(f"Property-Related groups : {len(property_groups)}")
            print(f"Other/General groups    : {len([u for u,d in discovered_groups.items() if not d['is_property']])}")
            print(f"Rule Analysis Complete  : {len([u for u,d in discovered_groups.items() if d['is_property'] and d.get('rules')])}")
            print("="*40)
            print(f"Saved to: {DATA_FILE}")
            print("="*40 + "\n")

        except Exception as e: print(f"❌ Error: {str(e)}")
        finally: 
            print("[System] Finished.")

if __name__ == "__main__":
    collect_and_analyze()
