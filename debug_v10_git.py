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
import ghost_config as config

# บังคับให้ Console พิมพ์ออกมาทันที
print = functools.partial(print, flush=True)

# ตั้งค่าไดเรกทอรี
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(SCRIPT_DIR, "uat_links.txt")
TEMP_RESULT_DIR = os.path.join(SCRIPT_DIR, "temp_debug_v10_git")

def get_fbid(url):
    """V10.0: สกัดเลข fbid จาก URL บน Address Bar"""
    match = re.search(r'fbid=(\d+)|permalink/(\d+)|posts/(\d+)', url)
    if match: return next(g for g in match.groups() if g is not None)
    return url

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

def debug_v10_git_logic(page, url, ba):
    """รันขั้นตอน 1-8 แบบ Human Logic (V10.0 Pure Git Version)"""
    print(f"\n🚀 [RESTORED GIT V10.0] เริ่มปฏิบัติการกวาดรูปภาพ BA 7488...")
    all_fbids = []
    
    try:
        # [1-2] Load Home
        page.goto(url, wait_until="load", timeout=90000)
        print("   [1-2] กำลังโหลดหน้าแรก (Wait 5s)...")
        page.wait_for_timeout(5000) 
        
        # [3-4] Scroll
        print("   [3-4] Focus และไถสกอร์ลงล่าง (PageDown)...")
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
        
        temp_dir = os.path.join(TEMP_RESULT_DIR, ba)
        if not os.path.exists(temp_dir): os.makedirs(temp_dir)
        
        for i in range(50):
            current_fbid = get_fbid(page.url)
            
            if i > 0 and current_fbid == start_fbid:
                print(f"   🏁 จบภารกิจ! วนกลับมาที่เดิม ({len(all_fbids)} รูป)")
                break

            # 1. ดึงลิ้งก์รูปจาก "กึ่งกลางจอ"
            img_src = page.evaluate('''
                () => {
                    const el = document.elementFromPoint(720, 380);
                    if (!el) return null;
                    if (el.tagName === 'IMG') return el.src;
                    const nestedImg = el.querySelector('img');
                    if (nestedImg) return nestedImg.src;
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
                try:
                    req = urllib.request.Request(img_src, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = resp.read()
                    hash_tweak_save(data, os.path.join(temp_dir, f"property_{len(all_fbids)}.jpg"))
                except: pass

            # [7-8] เลื่อนถัดไป
            next_btn = page.query_selector('div[aria-label="รูปภาพถัดไป"], div[aria-label="Next Photo"]')
            if next_btn:
                next_btn.click()
            else:
                page.keyboard.press("ArrowRight")
                
            page.wait_for_timeout(5000)

        print(f"\n✅ เสร็จสิ้นภารกิจกวาด {ba}! ได้รูป {len(all_fbids)} ใบ")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def main():
    # ดึงเฉพาะ BA 7488 เพื่อการทดสอบตามสั่ง
    target_ba = "BA 7488"
    target_url = "https://www.facebook.com/share/p/1EEJ2LrHiQ/?mibextid=wwXIfr"
    
    print(f"🕵️ [GHOST GIT RESTORE] กำลังย้อนเวลาไป V10.0 Stable...")
    
    with sync_playwright() as p:
        user_data_dir = config.USER_DATA_DIR
        context = p.chromium.launch_persistent_context(
            user_data_dir, headless=False, no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0] if context.pages else context.new_page()

        print("\n💡 กด [Enter] เพื่อเริ่มรัน 'โค้ดใน Git' ของแท้ (BA 7488)...")
        input() 

        debug_v10_git_logic(page, target_url, target_ba)
        
        print("\n📂 เสร็จแล้วครับ กด Enter เพื่อปิดหน้าต่าง...")
        input()
        context.close()

if __name__ == "__main__":
    main()
