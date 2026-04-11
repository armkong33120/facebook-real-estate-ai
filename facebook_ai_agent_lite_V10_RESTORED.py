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

# บังคับให้ Console พิมพ์ออกมาทันที
print = functools.partial(print, flush=True)

# ตั้งค่าไดเรกทอรี
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(SCRIPT_DIR, "uat_links.txt")
TEMP_RESULT_DIR = os.path.join(SCRIPT_DIR, "temp_debug_v10_0")

def get_fbid(url):
    """สกัดเลข fbid จาก URL บน Address Bar"""
    match = re.search(r'fbid=(\d+)', url)
    return match.group(1) if match else url

def hash_tweak_save(img_data, save_path):
    """V10.0: บันทึกรูปด้วยการปรับ Hash (Lossless)"""
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

def debug_v10_0_human_logic(page, url, ba):
    """รันขั้นตอน 1-8 แบบ Human Logic (V10.0): ใช้ Page URL เป็นตัวตัดสิน"""
    print(f"\n🚀 [HUMAN-HAND V10.0] ปฏิบัติการกวาดรูปภาพรอบตัดสิน...")
    all_fbids = []
    start_fbid = ""
    
    try:
        # [1-2] Load Home
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(5000) 
        
        # [3-4] Scroll
        page.mouse.click(720, 380)
        page.wait_for_timeout(2000)
        for _ in range(3): page.keyboard.press("PageDown")
        page.wait_for_timeout(5000) 
        
        # [5] Open Lightbox
        print("   [5] เปิด Lightbox และเริ่มล็อกเป้าหมาย (Relay 5s)...")
        page.mouse.click(500, 350)
        page.wait_for_timeout(5000)
        
        # เก็บ ID ใบแรก
        start_fbid = get_fbid(page.url)
        print(f"       ✅ ล็อกเป้าหมายเริ่มต้น (Start ID): {start_fbid}")
        
        # [6-8] วนลูปดูดรูป
        temp_dir = os.path.join(TEMP_RESULT_DIR, ba)
        if not os.path.exists(temp_dir): os.makedirs(temp_dir)
        
        for i in range(50):
            current_fbid = get_fbid(page.url)
            
            # ตรรกะเช็คซ้ำ: ถ้าไม่ใช่ใบแรก และ ID บน Address Bar ดันไปตรงกับใบเริ่มแรก = วนครบแล้ว
            if i > 0 and current_fbid == start_fbid:
                print(f"   🏁 จบภารกิจ! เลข ID บนเบราว์เซอร์วนกลับมาที่เดิม ({len(all_fbids)} รูป)")
                break

            # 1. ดึงลิ้งก์รูปจาก "กึ่งกลางจอ" (เหมือนคนเล็งไปที่รูปแล้วขวาเซฟ)
            img_src = page.evaluate('''
                () => {
                    const el = document.elementFromPoint(720, 380);
                    if (!el) return null;
                    // ถ้าจุดกึ่งกลางเป็น Overlay ให้หา <img> ที่อยู่ใกล้ที่สุด
                    if (el.tagName === 'IMG') return el.src;
                    const nestedImg = el.querySelector('img');
                    if (nestedImg) return nestedImg.src;
                    
                    // Fallback: หากึ่งกลางไม่ได้จริงๆ ให้เอารูปที่ใหญ่ที่สุดใน Dialog
                    const dialog = document.querySelector('div[role="dialog"]');
                    if (dialog) {
                        const imgs = Array.from(dialog.querySelectorAll('img')).filter(img => img.width > 400);
                        return imgs.length > 0 ? imgs[0].src : null;
                    }
                    return null;
                }
            ''')

            if img_src:
                all_fbids.append(current_fbid)
                print(f"       📸 ใบที่ {len(all_fbids)}: เก็บเลข ID {current_fbid} สำเร็จ")
                
                # บันทึกไฟล์
                try:
                    req = urllib.request.Request(img_src, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = resp.read()
                    hash_tweak_save(data, os.path.join(temp_dir, f"property_{len(all_fbids)}.jpg"))
                except: pass
            else:
                print(f"       ⚠️ ใบที่ {i+1}: มองไม่เห็นรูปที่จุดกึ่งกลาง...")

            # [7-8] เลื่อนถัดไป (คลิกปุ่ม 'รูปภาพถัดไป' จริงๆ)
            next_btn = page.query_selector('div[aria-label="รูปภาพถัดไป"], div[aria-label="Next Photo"]')
            if next_btn:
                next_btn.click()
            else:
                page.keyboard.press("ArrowRight")
                
            page.wait_for_timeout(5000) # Relay 5s ทุกลำดับ

        print(f"\n✅ เสร็จสิ้นภารกิจกวาด BA 7020! ได้รูปครบถ้วน {len(all_fbids)} ใบ")

    except Exception as e:
        print(f"   ❌ Relay Error: {str(e)}")

def main():
    if not os.path.exists(MAPPING_FILE): return
    mapping = {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if "|" in line:
                ba, url = line.split("|")
                mapping[ba.strip()] = url.strip()
                break

    print(f"🕵️ [GHOST AGENT V10.0] Human-Hand Ready...")
    
    with sync_playwright() as p:
        user_data_dir = os.path.join(SCRIPT_DIR, "fb_bot_profile")
        context = p.chromium.launch_persistent_context(
            user_data_dir, headless=False, no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0] if context.pages else context.new_page()

        print("\n💡 กด [Enter] เพื่อเริ่มงาน V10.0 (The Final UAT)...")
        input() 

        for ba, url in mapping.items():
            debug_v10_0_human_logic(page, url, ba)
        
        print("\n📂 กำลังเปิดผลลัพธ์ให้ตรวจงานครับ...")
        subprocess.run(["open", TEMP_RESULT_DIR])
        time.sleep(5)
        context.close()

if __name__ == "__main__":
    main()
