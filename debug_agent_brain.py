import os
import re
import time
from playwright.sync_api import sync_playwright
import ghost_config as config

def get_fbid(url):
    """[AGENT BRAIN] Robust ID Extraction (Supports FBID, Permalink, Posts)"""
    match = re.search(r'fbid=(\d+)|permalink/(\d+)|posts/(\d+)', url)
    if match:
        return next(g for g in match.groups() if g is not None)
    return url

def debug_agent_brain():
    # ดึงลิงก์ BA 7488 ที่มีปัญหา
    target_url = "https://www.facebook.com/share/p/1EEJ2LrHiQ/?mibextid=wwXIfr"
    
    print(f"🕵️  [AGENT BRAIN VERSION 13.40]")
    print(f"🧠 กำลังใช้ลอจิกเดียวกับบอท UAT ของ Antigravity...")
    print(f"🔗 เป้าหมาย: {target_url}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            config.USER_DATA_DIR,
            headless=False,
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            # 1. โหลดหน้าเว็บและรอ 5 วินาที
            print("⏳ Step 1: โหลดหน้าเว็บและรอ 5 วินาที (Fixed Timeout)...")
            page.goto(target_url, wait_until="load", timeout=90000)
            page.wait_for_timeout(5000)
            
            print("✅ โหลดสำเร็จ! ตรวจสอบหน้าจอแล้วกด [Enter] เพื่อเริ่มการไถแบบ Smart Wheel...")
            input()

            # 2. Smart Scroll (ใช้ Mouse Wheel จำลองการหมุนวงล้อเมาส์/รูด Trackpad)
            print("🖱️  Step 2: กำลังรูดหน้าจอลงด้วย Smart Wheel (5000px)...")
            # เล็งไปที่จุดกึ่งกลางก่อนสั่ง Wheel
            page.mouse.move(720, 380)
            page.mouse.wheel(0, 5000)
            
            print("⏳ รอ 5 วินาทีให้ UI และรูปภาพโหลดครบ...")
            page.wait_for_timeout(5000)
            
            # 3. คลิกเปิด Lightbox (ใช้ Smart Selector)
            print("🎯 Step 3: มองหาเป้าหมายแกลเลอรี่และเริ่มปฏิบัติการ (Click 500, 350)...")
            page.mouse.click(500, 350)
            
            # รอจนกว่า Lightbox จะเด้ง (เช็คจาก URL เปลี่ยนหรือมี Dialog)
            page.wait_for_timeout(6000)
            
            start_fbid = get_fbid(page.url)
            print(f"🚨 [LOCKED] Start ID: {start_fbid}")

            # 4. ลูปทดสอบถัดไป (Next)
            for i in range(1, 6):
                current_fbid = get_fbid(page.url)
                print(f"\n📸 [ใบที่ {i}] Current ID: {current_fbid}")
                
                print("   👉 กำลังสั่ง 'ถัดไป' ผ่าน Agent Engine...")
                # ลองกดปุ่ม Next ถ้ามี ถ้าไม่มีใช้ ArrowRight
                next_btn = page.query_selector('div[aria-label="รูปภาพถัดไป"], div[aria-label="Next Photo"]')
                if next_btn:
                    next_btn.click()
                else:
                    page.keyboard.press("ArrowRight")
                
                # เทคนิคพิเศษ: รอความเสถียรหลังคลิก
                page.wait_for_timeout(5000)
                
                new_fbid = get_fbid(page.url)
                if new_fbid == current_fbid:
                    print("      ⚠️ ID ไม่ขยับ... กำลังส่งสัญญาณ ArrowRight ซ้ำ (Redundancy)...")
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(3000)
                    new_fbid = get_fbid(page.url)
                
                if new_fbid != current_fbid:
                    print(f"      ✅ เปลี่ยนภาพสำเร็จ -> {new_fbid}")
                else:
                    print("      ❌ แจ้งเตือน: ปฏิบัติการ 'ถัดไป' ล้มเหลว")

        except Exception as e:
            print(f"❌ ระบบขัดข้อง: {e}")
        
        print("\n🏁 จบการสาธิต Agent Brain... กด Enter เพื่อปิด")
        input()
        context.close()

if __name__ == "__main__":
    debug_agent_brain()
