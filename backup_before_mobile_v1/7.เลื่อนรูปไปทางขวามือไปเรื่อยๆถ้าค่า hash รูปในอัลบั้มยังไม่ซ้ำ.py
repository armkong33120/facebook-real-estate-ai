import time
import config
from playwright.sync_api import sync_playwright

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def run_step_7():
    """ฟังก์ชันหลักสำหรับขั้นตอนที่ 7: เลื่อนรูปภาพโหมดความเร็วสูง (High-Speed Arrow Right)"""
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            page = browser.contexts[0].pages[0]
            page.bring_to_front()

            # 1. คลิกกึ่งกลางจอเพื่อ Activation
            page.mouse.click(720, 450)
            time.sleep(config.DELAY_ARROW_KEY)

            # 2. ส่งคำสั่งคีย์บอร์ด [ArrowRight]
            log_message("ส่งคำสั่ง [ArrowRight] (โหมดความเร็วสูง)...")
            page.keyboard.press("ArrowRight")
            
            # 3. รอให้รูปใหม่โหลด
            time.sleep(config.DELAY_IMAGE_RENDER)
            
            return True

        except Exception as e:
            log_message(f"ข้อผิดพลาด 7: {str(e)}")
            return False