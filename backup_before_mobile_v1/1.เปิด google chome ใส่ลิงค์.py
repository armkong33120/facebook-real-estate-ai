import time
import os
from playwright.sync_api import sync_playwright
import browser_core
import config

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def run_step_1(url, property_id):
    """ฟังก์ชันหลักสำหรับขั้นตอนที่ 1: เปิด Browser และเตรียมพร้อมทำงาน"""
    # ปิดคำเตือนทางเทคนิคที่กวนใจ
    os.environ["NODE_OPTIONS"] = "--no-deprecation"
    log_message(f"เริ่มขั้นตอนที่ 1: จัดการ Browser สำหรับ {property_id}")
    
    # 1. ปิดตัวเก่าและเปิดใหม่เพื่อให้ได้ Clean Session พร้อม Debug Port
    browser_core.launch_independent_browser(url)
    log_message("กำลังรอ Browser ตั้งตัว (5 วินาที)...")
    time.sleep(5) 

    with sync_playwright() as p:
        try:
            # 2. เชื่อมต่อผ่าน CDP
            log_message("กำลังเชื่อมต่อ Playwright เข้ากับ Chrome...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            log_message("เชื่อมต่อสำเร็จ กำลังเตรียมระบบ (กิจกรรม 3 วิ)...")
            time.sleep(3)
            context = browser.contexts[0]
            
            # 3. เลือกหน้า Page
            if len(context.pages) > 0:
                page = context.pages[0]
            else:
                page = context.new_page()
            time.sleep(3) # รอจังหวะหน้า Page (กิจกรรม 3 วิ)

            # ปรับขนาดหน้าจอ
            page.set_viewport_size({"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT})
            log_message("ปรับหน้าจอเรียบร้อย (กิจกรรม 3 วิ)...")
            time.sleep(3)

            # นำทางไปยัง URL เป้าหมายถ้ายังไม่อยู่ในจุดที่ต้องการ
            log_message(f"หน้าเว็บปัจจุบันคือ: {page.url}")
            if "facebook.com" not in page.url:
                log_message(f"กำลังนำทางไปที่: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(3) # รอให้หน้าเว็บแสดงผลนิ่ง (กิจกรรม 3 วิ)
            
            log_message(f"--- ขั้นตอนที่ 1 สำเร็จ: Browser พร้อมใช้งาน ---")
            time.sleep(3) # หน่วงก่อนจบ Step (กิจกรรม 3 วิ)
            return True, page

        except Exception as e:
            log_message(f"เกิดข้อผิดพลาดในขั้นตอนที่ 1: {str(e)}")
            return False, None