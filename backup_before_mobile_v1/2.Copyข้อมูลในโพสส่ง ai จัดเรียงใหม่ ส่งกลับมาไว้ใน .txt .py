import time
import os
from playwright.sync_api import sync_playwright
import ai_engine

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def run_step_2(property_id, property_link):
    """ฟังก์ชันหลักสำหรับขั้นตอนที่ 2: ดึงข้อมูลและคลีนด้วย AI"""
    os.environ["NODE_OPTIONS"] = "--no-deprecation"
    log_message(f"เริ่มขั้นตอนที่ 2: ดึงข้อมูลและคลีนด้วย AI สำหรับ {property_id}")
    
    with sync_playwright() as p:
        try:
            # เชื่อมต่อกับ Chrome
            log_message("กำลังเชื่อมต่อเข้ากับ Browser...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            log_message("เชื่อมต่อสำเร็จ (กิจกรรม 3 วิ)...")
            time.sleep(3)
            context = browser.contexts[0]
            
            if len(context.pages) == 0:
                log_message("ผิดพลาด: ไม่พบหน้าเว็บที่เปิดอยู่")
                return False, None
            
            page = context.pages[0]
            page.bring_to_front()

            log_message("กำลังค้นหาเนื้อหาโพสต์...")
            
            # รอการโหลดและคลิกดูเพิ่มเติม
            try:
                page.wait_for_selector('div[role="main"]', timeout=10000)
                time.sleep(3) # รอให้หน้าเว็บ Render (กิจกรรม 3 วิ)
                see_more_button = page.get_by_text("ดูเพิ่มเติม", exact=True)
                if see_more_button.is_visible():
                    see_more_button.click(timeout=3000)
                    log_message("คลิกปุ่ม 'ดูเพิ่มเติม' สำเร็จ (กิจกรรม 3 วิ)")
                    time.sleep(3)
            except:
                pass

            # ดึงข้อความโพสต์ (ปรับปรุงเพื่อเน้นหน้าต่าง Modal/Dialog ที่ทับอยู่)
            post_content = ""
            
            # ลำดับความสำคัญ: 1. ใน Dialog (Modal), 2. ใน Main Area, 3. ทั้งหน้า
            possible_areas = [
                page.locator('div[role="dialog"]'), 
                page.locator('div[role="main"]'),
                page.locator('body') # เปลี่ยนจาก page เป็น page.locator('body') เพื่อให้เป็น Locator เสมอ
            ]
            
            selectors = [
                'div[data-ad-comet-preview="message"]', 
                'div[data-ad-preview="message"]', 
                'div[data-testid="post_message"]',
                'div[dir="auto"]'
            ]
            
            for area in possible_areas:
                # แก้ไขปัญหา 'Page' object has no attribute 'count' โดยการเป็น Locator ทั้งหมดแล้ว
                if area.count() > 0:
                    for s in selectors:
                        # หาข้อความใน Area นั้นๆ
                        elements = area.locator(s).all()
                        for el in elements:
                            text = el.inner_text().strip()
                            # สกัดเอาข้อความประกาศที่มีคุณภาพ (ต้องยาวพอ)
                            if len(text) > 100: 
                                post_content = text
                                break
                        if post_content: break
                if post_content: break
            
            # หากยังหาไม่เจอ (Fallback)
            if not post_content:
                log_message("พยายามดึงข้อมูลแบบ Fallback (เจาะจง dir='auto')...")
                all_texts = page.locator('div[dir="auto"]').all_text_contents()
                post_content = "\n".join([t.strip() for t in all_texts if len(t.strip()) > 100])

            if not post_content or len(post_content) < 20:
                log_message("ผิดพลาด: หาข้อความเนื้อหาทรัพย์ไม่พบ กรุณาเช็คว่าหน้าเว็บโหลดเนื้อหาเสร็จหรือยัง")
                return False, None

            log_message(f"ดึงข้อมูลสำเร็จ (ความยาว {len(post_content)} ตัวอักษร)")
            
            # --- DEBUG: แสดงสิ่งที่บอทอ่านได้จริง ---
            print("\n" + "-"*15 + " DEBUG: RAW CONTENT " + "-"*15)
            # แสดงแค่หมื่นตัวแรกถ้ามันยาวเกินไป
            display_text = post_content[:1000] + "..." if len(post_content) > 1000 else post_content
            print(display_text)
            print("-"*45 + "\n")
            
            cleaned_text = ai_engine.clean_property_text(post_content, property_id, property_link)
            
            print("\n" + "="*25 + " ผลลัพธ์การจัดเรียงใหม่ " + "="*25)
            print(cleaned_text)
            print("="*75 + "\n")
            
            time.sleep(3) # หน่วงก่อนจบ Step (กิจกรรม 3 วิ)
            return True, cleaned_text

        except Exception as e:
            log_message(f"เกิดข้อผิดพลาดในขั้นตอนที่ 2: {str(e)}")
            return False, None