import os
import sys
import time
import json
import random
from playwright.sync_api import sync_playwright
import google.generativeai as genai
import browser_core
import config

# Configuration
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "group_analysis.json")
PROPERTY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "group_rules.txt")

# Setup Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

def clean_rules_with_ai(raw_text, name):
    """Uses AI to clean up noise and summarize the about section"""
    prompt = f"""
    คุณเป็นผู้ช่วยผู้จัดการฝ่ายการตลาดอสังหาริมทรัพย์ หน้าที่ของคุณคือการสรุปข้อมูล "เกี่ยวกับกลุ่ม" ใน Facebook 
    จากข้อความดิบ (Raw Text) ที่ให้มา โดยให้ตัดข้อมูลขยะ เช่น จำนวนสมาชิก, ปุ่มเชิญ, ปุ่มแชร์, แท็บเมนู (Discussion, Members, etc.) ออกไปทั้งหมด
    และสรุปสั้นๆ ว่ากลุ่มนี้มีรายละเอียดหรือกฎ "เกี่ยวกับอะไร" เพื่อให้รู้ว่าควรโพสต์อสังหาฯ ในกลุ่มนี้อย่างไร
    
    ชื่อกลุ่ม: {name}
    ข้อความดิบ:
    {raw_text}
    
    ---
    คำตอบ (สรุปเฉพาะเนื้อหาสำคัญและกฎของกลุ่ม ไม่ต้องเกริ่นนำ):
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"      ⚠️ AI Error: {str(e)}")
        return raw_text[:1000] # Fallback to truncated raw

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Warning: Could not save data: {str(e)}")

def analyze_rules_standalone():
    print("\n" + "="*50)
    print("🛠️  MANUAL PHASE 2: Group Rule Analyzer")
    print("="*50)
    
    # 1. Load Discovered Groups
    discovered_groups = load_data()
    if not discovered_groups:
        print("❌ Error: No discovered groups found in group_analysis.json.")
        print("   Please run Phase 1 (Discovery) first.")
        return

    # 2. Filter groups needing analysis
    target_groups = [url for url, d in discovered_groups.items() 
                     if d.get("is_property") and (not d.get("rules") or "Failed" in d["rules"])]
    
    print(f"📊 Total groups in database: {len(discovered_groups)}")
    print(f"🎯 Groups needing analysis: {len(target_groups)}")
    print("-" * 50)

    if not target_groups:
        print("✅ Everything is already up to date! Nothing to analyze.")
        return

    # 3. Launch Browser
    if not browser_core.launch_independent_browser(): return

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            for index, url in enumerate(target_groups):
                name = discovered_groups[url]['name']
                print(f"[{index+1}/{len(target_groups)}] Processing: {name}")
                
                try:
                    # Navigate to About page
                    about_url = url.rstrip('/') + "/about/" if "/about/" not in url else url
                    page.goto(about_url, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(random.uniform(4, 6)) # Human-like wait
                    
                    # --- INTELLIGENT EXTRACTION (Based on text seen by User) ---
                    about_text = page.evaluate("""() => {
                        // 1. Find all possible header elements (Thai/English)
                        const searchTerms = ['เกี่ยวกับกลุ่มนี้', 'About this group'];
                        const headers = Array.from(document.querySelectorAll('span, h1, h2, h3, div[role="heading"]'))
                            .filter(el => searchTerms.some(term => el.innerText.includes(term)));
                        
                        if (headers.length === 0) return null;
                        
                        // Pick the most specific (lowest) header
                        const header = headers[headers.length - 1];
                        
                        // 2. Find the content container that isn't just the header
                        let current = header;
                        for (let i = 0; i < 6; i++) { 
                            let parent = current.parentElement;
                            if (!parent) break;
                            if (parent.innerText.trim().length > header.innerText.trim().length + 20) {
                                // Return content after removing header text
                                return parent.innerText.replace(header.innerText, '').trim();
                            }
                            current = parent;
                        }
                        return null;
                    }""")

                    if not about_text or len(about_text.strip()) < 10:
                        # Fallback: Scrape the main card directly
                        about_text = page.evaluate("() => document.querySelector('div[role=\"main\"]')?.innerText.substring(0, 2000)")

                    # Logic for default message if still empty
                    if not about_text or len(about_text.strip()) < 10:
                        clean_rules = "ไม่มีกฏใน \"เกี่ยวกับ\" อ้างอิงชื่อกลุ่มคือกฏ"
                        print(f"      [DEBUG: NO CONTENT FOUND] Using default message.")
                    else:
                        # --- DEBUG DISPLAY: INPUT ---
                        print(f"      [DEBUG: ข้อมูลดิบที่ส่งให้ AI]:")
                        print(f"      {'-'*40}")
                        print(f"      {about_text[:600].replace(chr(10), chr(10) + '      ')}...")
                        print(f"      {'-'*40}")
                        
                        # Process with AI
                        print(f"      🤖 AI กำลังสรุปข้อมูล...")
                        clean_rules = clean_rules_with_ai(about_text, name)
                        
                        # --- DEBUG DISPLAY: OUTPUT ---
                        print(f"      [DEBUG: ผลสรุปที่ได้รับจาก AI]:")
                        print(f"      {'-'*15} สรุปข้อมูล {'-'*15}")
                        print(f"      {clean_rules.replace(chr(10), chr(10) + '      ')}")
                        print(f"      {'-'*40}\n")
                    
                    discovered_groups[url]['rules'] = clean_rules
                    save_data(discovered_groups)
                    
                    print(f"      📝 Log: Saved {len(clean_rules)} chars.\n")
                    
                except Exception as e_inner:
                    print(f"      ⚠️ Failed to visit/extract: {str(e_inner)}")
                    discovered_groups[url]['rules'] = "Failed to load group page."
                    save_data(discovered_groups)

                # Random delay between groups
                time.sleep(random.uniform(3, 7))

            # Export to human-readable txt at the end
            with open(PROPERTY_FILE, "w", encoding="utf-8") as f:
                for u, d in discovered_groups.items():
                    if d.get("is_property"):
                        f.write(f"NAME: {d['name']}\nLINK: {u}\nRULES:\n{d.get('rules', 'N/A')}\n{'-'*60}\n")
            
            print("\n" + "="*50)
            print("🎉 MANUAL PHASE 2 COMPLETE!")
            print(f"📁 Updated and exported to: {PROPERTY_FILE}")
            print("="*50)

        except Exception as e:
            print(f"❌ Critical Error: {str(e)}")
        finally:
            print("[System] Finished.")

if __name__ == "__main__":
    analyze_rules_standalone()
