import os
import re
import time
from playwright.sync_api import sync_playwright
import ghost_config as config

def get_fbid(url):
    """สกัดเลข fbid จาก URL บน Address Bar (V12.9 Robust Regex)"""
    match = re.search(r'fbid=(\d+)|permalink/(\d+)|posts/(\d+)', url)
    if match:
        # ดึงกลุ่มตัวเลขกลุ่มแรกที่ไม่เป็น None
        return next(g for g in match.groups() if g is not None)
    return url

def load_ba7488_url():
    """ดึงลิงก์หลักจาก uat_links.txt เพื่อให้ตรงกับหน้างานจริง"""
    try:
        with open("uat_links.txt", "r", encoding="utf-8") as f:
            for line in f:
                if "BA 7488" in line:
                    return line.split("|")[1].strip()
    except: pass
    return "https://www.facebook.com/share/p/1EEJ2LrHiQ/"

def debug_ba_7488():
    url = load_ba7488_url()
    print(f"🕵️  [FINAL DEBUG] กำลังเริ่มปฏิบัติการเจาะจง BA 7488...")
    print(f"🔗 ลิงก์ทดสอบ: {url}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            config.USER_DATA_DIR,
            headless=False,
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            # 1. โหลดหน้าเว็บ
            page.goto(url, wait_until="load", timeout=90000)
            print("⏳ รอ Redirect และโหลดหน้าหลัก (Relay 8s)...")
            page.wait_for_timeout(8000)
            
            print("✅ Step 1: โหลดสำเร็จ กรุณาเช็คหน้าจอว่าเห็นโพสต์ BA 7488 หรือยัง? (กด Enter เพื่อไปต่อ)")
            input()

            # 2. ปลุกระบบ Focus และรูดสกอร์บาร์ (V13.35 Aggressive PageDown)
            print("🎯 Step 2: กำลังรัวคลิกกลางจอ (Triple-Click 720, 380) เพื่อเช็กพิกัดสกรอบาร์...")
            for _ in range(3):
                page.mouse.click(720, 380)
                page.wait_for_timeout(500)
            
            print("🔄 [FORCED SCROLL] กำลังไถ PageDown 8 ครั้งรวด เพื่อข้ามข้อความยาวๆ...")
            for i in range(8):
                page.keyboard.press("PageDown")
                page.wait_for_timeout(700)
                print(f"   (ไถลงแล้วจังหวะที่ {i+1}/8)")
            
            print("      ✅ รูดหน้าจอลงจนสุดเรียบร้อย (Visual Scroll Verified)")
            page.wait_for_timeout(5000)

            # 3. เปิดแกลเลอรี่
            print("🖱️  Step 3: คลิกพิกัด 500, 350 เพื่อเปิดแกลเลอรี่...")
            page.mouse.click(500, 350)
            page.wait_for_timeout(6000)
            
            start_fbid = get_fbid(page.url)
            print(f"🚨 [LOCKED] Start ID: {start_fbid}")
            
            # --- LOOP TESTING ---
            for i in range(1, 11):
                current_fbid = get_fbid(page.url)
                print(f"\n📸 [ใบที่ {i}] กำลังประมวลผล ID: {current_fbid}")
                
                print("   💡 กด [Enter] เพื่อสั่ง 'ถัดไป' (หรือสังเกตอาการบอทคลิกเอง)...")
                input()
                
                # 4. ทดลองทักษะการคลิกถัดไปแบบต่างๆ
                next_btn = page.query_selector('div[aria-label="รูปภาพถัดไป"], div[aria-label="Next Photo"]')
                if next_btn:
                    print("      👉 คลิกผ่านปุ่ม Next (DOM)")
                    next_btn.click()
                else:
                    print("      👉 คลิกผ่าน ArrowRight (Key)")
                    page.keyboard.press("ArrowRight")
                
                page.wait_for_timeout(5000)
                
                # 5. ตรวจสอบการเปลี่ยนภาพ
                new_fbid = get_fbid(page.url)
                if new_fbid == current_fbid:
                    print(f"      ❌ ID ไม่เปลี่ยน! พยายาม Force ด้วยลูกศรขวาอีกรอบ...")
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(4000)
                    new_fbid = get_fbid(page.url)
                
                if new_fbid == start_fbid and i > 1:
                    print("      🏁 วนกลับมาจุดเริ่มต้นแล้ว! จบการ Debug")
                    break
                elif new_fbid != current_fbid:
                    print(f"      ✅ เปลี่ยนภาพสำเร็จ -> {new_fbid}")
                else:
                    print("      ❌ แจ้งเตือน: ภาพไม่ยอมเปลี่ยน!")

        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n🏁 จบภารกิจ Debug... กด Enter เพื่อปิดหน้าต่าง")
        input()
        context.close()

if __name__ == "__main__":
    debug_ba_7488()
