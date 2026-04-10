import re
import os
import time
import random
import json
import urllib.request
import io
import functools
from PIL import Image
from playwright.sync_api import sync_playwright
import google.generativeai as genai

# บังคับให้ Console พิมพ์ออกมาทันที
print = functools.partial(print, flush=True)

# --- CONFIG ---
# --- CONFIG ---
API_KEY = "AIzaSyDpGPdrSJWzZTIU3jmqEBkwNtHpwn_6a3w"
genai.configure(api_key=API_KEY)

# ตั้งค่าไดเรกทอรี
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(SCRIPT_DIR, "missing_images_links.txt")
BASE_TARGET_DIR = os.path.join(SCRIPT_DIR, "ฐานข้อมูลอสังหา_Facebook")

def extract_category_with_vision(text, image_paths=None):
    prompt = f"วิเคราะห์อสังหาฯ และตอบเป็น JSON เท่านั้น:\n{text}\nรูปแบบ: {{\"province\": \"...\", \"district\": \"...\", \"property_type\": \"...\", \"cleaned_text\": \"...\"}}"
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    content = [prompt]
    if image_paths:
        for p in image_paths[:3]:
            try: content.append(Image.open(p))
            except: pass
    try:
        response = model.generate_content(content, generation_config={"response_mime_type": "application/json"})
        data = json.loads(response.text.strip())
        return data.get("province", "ไม่ระบุ"), data.get("district", "ไม่ระบุ"), data.get("property_type", "ไม่ระบุ"), data.get("cleaned_text", text)
    except:
        return "ไม่ระบุ", "ไม่ระบุ", "ไม่ระบุ", text

def download_images(image_urls, save_dir):
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    saved_paths = []
    count = 1
    for url in image_urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            img = Image.open(io.BytesIO(data))
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            p = os.path.join(save_dir, f"img_{count}.jpg")
            img.save(p, "JPEG", quality=90)
            saved_paths.append(p)
            count += 1
        except: pass
    return saved_paths

def main():
    if not os.path.exists(MAPPING_FILE):
        print("❌ ไม่พบไฟล์ missing_images_links.txt")
        return
    
    mapping = {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if "|" in line:
                ba, url = line.split("|")
                mapping[ba.strip()] = url.strip()

    print(f"🚀 เริ่มระบบกู้คืนชุดเสถียร (จำนวน {len(mapping)} รายการ)")
    
    with sync_playwright() as p:
        # ใช้ Browser ปกติเพื่อให้ผู้ใช้สังเกตการณ์ได้
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("\n" + "="*50)
        print("🛑 [PAUSE] กรุณาจัดการ Log in ในหน้าจอ Browser ให้เรียบร้อย")
        print("เมื่อพร้อมแล้ว ให้กลับมาที่หน้านี้ (Terminal) แล้วกด [Enter] เพื่อเริ่มรัน...")
        print("="*50)
        input() 

        for ba, url in mapping.items():
            print(f"\nProcessing {ba}: {url}")
            try:
                # ใช้ m.facebook.com (Mobile View) ตามลอจิก 1300+ เดิม
                m_url = url.replace("www.facebook.com", "m.facebook.com").replace("mbasic.facebook.com", "m.facebook.com")
                page.goto(m_url, timeout=60000)
                page.wait_for_timeout(3000)
                
                # ดึงข้อความ
                fb_text = page.inner_text("body")
                
                # หา URL รูปภาพโดยตรงจากหน้าโพสต์ (ไม่ต้องคลิกเจาะ)
                img_elements = page.query_selector_all("img")
                img_urls = []
                for img in img_elements:
                    src = img.get_attribute("src")
                    # คัดกรองรูปภาพขนาดใหญ่ที่ไม่ใช่ไอคอน
                    if src and "fbcdn.net" in src and "p200x200" not in src and "s160x160" not in src:
                        if src not in img_urls: img_urls.append(src)

                if len(img_urls) < 1:
                    print("   ⚠️ ไม่พบรูปภาพที่เข้าเงื่อนไข")
                    continue

                # วิเคราะห์และจัดหมวดหมู่
                temp_dir = os.path.join(SCRIPT_DIR, "temp_vision")
                img_paths = download_images(img_urls[:2], temp_dir)
                prov, dist, ptype, clean_txt = extract_category_with_vision(fb_text, img_paths)
                print(f" ✨ {prov} > {dist} > {ptype} (พบรูป {len(img_urls)} ใบ)")

                # บันทึกรูปทั้งหมดลงโฟลเดอร์
                final_dir = os.path.join(BASE_TARGET_DIR, prov, dist, ptype, ba)
                os.makedirs(final_dir, exist_ok=True)
                download_images(img_urls, final_dir)
                
                with open(os.path.join(final_dir, f"{ba}.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"{clean_txt}\n\n{ba}\n====================")
                
                print(f"   ✅ บันทึกรูป {len(img_urls)} ใบ ลงโฟลเดอร์เรียบร้อย!")
                for p in img_paths: 
                    try: os.remove(p)
                    except: pass
                
                # --- จุดพักตรวจสอบ ---
                print("\n" + "-"*30)
                print(f"🏁 ประมวลผล {ba} เสร็จสมบูรณ์")
                input("👉 กด [Enter] เพื่อรันรายการถัดไป หรือกด [Ctrl+C] เพื่อออกมาแก้ไข...")
                print("-"*30)

            except Exception as e:
                print(f"   ❌ ข้าม {ba} เนื่องจาก: {str(e)}")
            
            time.sleep(random.uniform(3, 6))

        browser.close()

if __name__ == "__main__":
    main()
