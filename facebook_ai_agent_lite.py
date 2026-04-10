import os
import time
import json
import urllib.request
import io
import functools
import subprocess
import re
from PIL import Image
from playwright.sync_api import sync_playwright
import google.generativeai as genai

# บังคับให้ Console พิมพ์ออกมาทันที
print = functools.partial(print, flush=True)

# --- CONFIG ---
API_KEY = "AIzaSyDpGPdrSJWzZTIU3jmqEBkwNtHpwn_6a3w"
genai.configure(api_key=API_KEY)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(SCRIPT_DIR, "uat_links.txt")
BASE_RESULT_DIR = os.path.join(SCRIPT_DIR, "Facebook_Property_Data")

def analyze_location_with_ai(text):
    """ส่งข้อความให้ AI วิเคราะห์ จังหวัด-เขต"""
    print(f"   🤖 กำลังส่งข้อมูลให้ AI วิเคราะห์ทำเล...")
    prompt = f"คุณคือผู้เชี่ยวชาญอสังหาฯ ไทย จงสกัดข้อมูล 'จังหวัด' และ 'เขต/อำเภอ' จากข้อความนี้ และตอบกลับเป็น JSON เท่านั้น: {{ 'province': '...', 'district': '...' }}\nข้อความ: {text}"
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        data = json.loads(response.text.strip())
        return data.get("province", "ไม่ระบุ"), data.get("district", "ไม่ระบุ")
    except:
        return "ไม่ระบุ", "ไม่ระบุ"

def get_fbid(url):
    """สกัดเลข fbid จาก URL บน Address Bar"""
    match = re.search(r'fbid=(\d+)', url)
    return match.group(1) if match else url

def hash_tweak_save(img_data, save_path):
    """V11.0: บันทึกรูปด้วยการปรับ Hash (Lossless)"""
    try:
        img = Image.open(io.BytesIO(img_data))
        img = img.convert("RGB")
        data = list(img.getdata())
        image_out = Image.new("RGB", img.size)
        image_out.putdata(data)
        r, g, b = image_out.getpixel((0,0))
        image_out.putpixel((0,0), ((r + 1) % 256, g, b))
        image_out.save(save_path, "JPEG", quality=95, optimize=True)
        return True
    except: return False

def ultimate_ghost_agent_v11(page, url, ba):
    """รันระบบ Ultimate V11.0: AI Scan -> Hierarchy Folder -> V10 Scraper"""
    print(f"\n🚀 [ULTIMATE V11.0] เริ่มปฏิบัติการทรัพย์ {ba}...")
    
    try:
        # [1] Load & Scan Location
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(5000)
        
        # กวาดข้อความส่งให้ AI
        print("   🔍 [AI PHASE] กำลังสแกนทำเลจากเนื้อหาโพสต์...")
        raw_text = page.evaluate('() => document.body.innerText')
        province, district = analyze_location_with_ai(raw_text[:2000])
        print(f"       📍 พิกัดที่พบ: {province} / {district}")
        
        # [2] Setup Folder Hierarchy
        target_dir = os.path.join(BASE_RESULT_DIR, province, district, ba)
        if not os.path.exists(target_dir): os.makedirs(target_dir)
        
        # [3] Navigation & Scroll (V10 Mode)
        page.mouse.click(720, 380)
        page.wait_for_timeout(2000)
        for _ in range(3): page.keyboard.press("PageDown")
        page.wait_for_timeout(5000)
        
        # [4] Open Lightbox
        print("   🖼️ [SCRAPE PHASE] เริ่มปฏิบัติการดูดรูปภาพ (V10 Mode)...")
        page.mouse.click(500, 350)
        page.wait_for_timeout(5000)
        
        start_fbid = get_fbid(page.url)
        all_ids = []
        
        for i in range(50):
            current_fbid = get_fbid(page.url)
            if i > 0 and current_fbid == start_fbid:
                print(f"       🏁 จบภารกิจ! วนครบ {len(all_ids)} รูปถ้วน")
                break
                
            # ดึงรูปกึ่งกลางจอ
            img_src = page.evaluate('''
                () => {
                    const el = document.elementFromPoint(720, 380);
                    if (el && el.tagName === 'IMG') return el.src;
                    const nested = el ? el.querySelector('img') : null;
                    if (nested) return nested.src;
                    const dialog = document.querySelector('div[role="dialog"]');
                    const imgs = dialog ? Array.from(dialog.querySelectorAll('img')).filter(img => img.width > 400) : [];
                    return imgs.length > 0 ? imgs[0].src : null;
                }
            ''')
            
            if img_src:
                all_ids.append(current_fbid)
                print(f"       📸 ใบที่ {len(all_ids)}: กำลังบันทึก ({current_fbid})")
                try:
                    req = urllib.request.Request(img_src, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = resp.read()
                    hash_tweak_save(data, os.path.join(target_dir, f"property_{len(all_ids)}.jpg"))
                except: pass
            
            # กดถัดไป + Relay 5s
            next_btn = page.query_selector('div[aria-label="รูปภาพถัดไป"], div[aria-label="Next Photo"]')
            if next_btn: next_btn.click()
            else: page.keyboard.press("ArrowRight")
            page.wait_for_timeout(5000)

        print(f"✅ สำเร็จ! ข้อมูลจัดเก็บไว้ที่: {province}/{district}/{ba}")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def main():
    if not os.path.exists(MAPPING_FILE): return
    mapping = {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if "|" in line:
                ba, url = line.split("|")
                mapping[ba.strip()] = url.strip()
                break

    print(f"🕵️ [GHOST AGENT V11.0] The Ultimate Unified Agent Ready...")
    
    with sync_playwright() as p:
        user_data_dir = os.path.join(SCRIPT_DIR, "fb_bot_profile")
        context = p.chromium.launch_persistent_context(
            user_data_dir, headless=False, no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0] if context.pages else context.new_page()

        print("\n💡 กด [Enter] เพื่อเริ่มงาน V11.0 Ultimate (Location + Scraper)...")
        input() 

        for ba, url in mapping.items():
            ultimate_ghost_agent_v11(page, url, ba)
        
        print("\n📂 เปิดโฟลเดอร์ผลลัพธ์เพื่อตรวจสอบความถูกต้อง...")
        subprocess.run(["open", BASE_RESULT_DIR])
        time.sleep(5)
        context.close()

if __name__ == "__main__":
    main()
