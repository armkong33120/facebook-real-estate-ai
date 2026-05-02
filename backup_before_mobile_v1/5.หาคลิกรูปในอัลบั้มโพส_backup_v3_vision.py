import time
import random
import os
from playwright.sync_api import sync_playwright

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def show_red_dot(page, x, y):
    """ฟังก์ชันพิเศษ: สร้างจุดสีแดงกะพริบบนหน้าจอเพื่อให้สกินเห็นว่าบอทจะกดตรงไหน"""
    js_code = f"""
    (lambda() {{
        const dot = document.createElement('div');
        dot.style.position = 'fixed';
        dot.style.left = '{x}px';
        dot.style.top = '{y}px';
        dot.style.width = '60px';
        dot.style.height = '60px';
        dot.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
        dot.style.borderRadius = '50%';
        dot.style.border = '5px solid yellow';
        dot.style.zIndex = '1000000';
        dot.style.pointerEvents = 'none';
        dot.style.transform = 'translate(-50%, -50%)';
        dot.style.boxShadow = '0 0 30px rgba(255,0,0,1), 0 0 50px rgba(255,255,255,0.5)';
        document.body.appendChild(dot);
        
        let count = 0;
        const interval = setInterval(() => {{
            dot.style.opacity = dot.style.opacity === '0' ? '1' : '0';
            count++;
            if (count > 20) {{ // กะพริบ 5 วินาที
                clearInterval(interval);
                dot.remove();
            }}
        }}, 250);
    }})();
    """
    try:
        page.evaluate(js_code)
        # ไม่ต้องหน่วงนานเพื่อให้ระบบไหลลื่น
        time.sleep(1)
    except:
        pass

def save_failed_link(url):
    """บันทึกลิงก์ที่เข้าอัลบั้มไม่สำเร็จลงไฟล์"""
    file_path = "failed_links.txt"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] FAILED to open album: {url}\n")
    log_message(f"บันทึกลิงก์ที่ล้มเหลวลงใน {file_path}")

def run_step_5(baseline_url=None, force_scroll_up=False):
    """ฟังก์ชันหลักสำหรับขั้นตอนที่ 5: คลิกเปิดอัลบั้ม (เพิ่มระบบ Recovery เมื่อติดขัด)"""
    log_message("เริ่มขั้นตอนที่ 5: กำลังวัดผลการคลิก (Speed-Mode 2s)...")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            page = browser.contexts[0].pages[0]
            page.bring_to_front()

            # 1. ตรวจสอบและดึงบอทกลับสู่หน้า Post หลักหากหลงทาง
            old_url = baseline_url if baseline_url else page.url
            if page.url != old_url:
                log_message(f"--- [RECOVERY] ระบบจะวาร์ปกลับไปที่หน้าหลัก: {old_url} ---")
                page.goto(old_url, wait_until="domcontentloaded")
                time.sleep(2)

            # 2. ทำการเลื่อนขึ้นหากเป็นโหมดแก้ตัว (Recovery)
            if force_scroll_up:
                log_message("--- [RECOVERY] บรรดา AI ร้องเตือน! กำลังไถจอขึ้นเพื่อหาจุดใหม่ ---")
                page.mouse.wheel(0, -300)
                time.sleep(1.5)
            
            log_message(f"--- [Baseline URL]: {old_url} ---")

            # 3. รอบการพยายามคลิกปกติ (3 ครั้ง)
            for attempt in range(1, 4):
                log_message(f"--- พยายามครั้งที่ {attempt}/3 (กิจกรรม 3 วิ) ---")
                
                # Activation Click
                page.mouse.click(500, 300)
                time.sleep(1)
                
                # ไถเมาส์ลง (Down)
                for _ in range(7):
                    page.mouse.wheel(0, 200)
                    time.sleep(0.2)
                time.sleep(1)

                # สุ่มจุดคลิก (พิกัดเป้าหมาย)
                click_x = 500 + random.randint(-50, 50)
                click_y = 650 + random.randint(-50, 50)
                
                show_red_dot(page, click_x, click_y)
                page.mouse.click(click_x, click_y)
                
                log_message("รอตรวจจับ URL เปลี่ยน (กิจกรรม 2 วิ)...")
                time.sleep(2)
                
                if page.url != old_url or "/photo" in page.url:
                    log_message(f"--- [PASSED] เข้าสู่อัลบั้มสำเร็จ ---")
                    return True
                
                log_message("วืด! กำลังพยายามใหม่...")

            # 3. [ระบบฉุกเฉิน] ถ้ากด 3 ครั้งแล้วไม่ไป ให้ลอง "ไถขึ้น (Scroll Up)" 
            log_message("!!! เข้าสู่โหมด Recovery: พยายามไถจอขึ้นเพื่อหาจุดคลิกใหม่ !!!")
            for recovery_loop in range(1, 4):
                log_message(f"--- Recovery รอบที่ {recovery_loop}/3 (ไถขึ้น 20%) ---")
                
                # ไถขึ้น (Scroll Up)
                page.mouse.wheel(0, -300)
                time.sleep(1)
                
                # ลองคลิกจุดสุ่มอีกครั้ง
                page.mouse.click(500 + random.randint(-100, 100), 500 + random.randint(-100, 100))
                time.sleep(2)
                
                if page.url != old_url or "/photo" in page.url:
                    log_message(f"--- [SUCCESS] กู้คืนสถานะสำเร็จ! เข้าสู่อัลบั้มแล้ว ---")
                    return True
            
            # 4. ถ้าจบทุกขั้นตอนแล้วยังไม่ไป ให้บันทึกความล้มเหลวและข้ามไป
            log_message("[FAILED] ไม่สามารถเข้าสู่อัลบั้มได้หลังจากพยายามเต็มรูปแบบ")
            save_failed_link(old_url)
            return False

        except Exception as e:
            log_message(f"เกิดข้อผิดพลาดในขั้นตอนที่ 5: {str(e)}")
            return False