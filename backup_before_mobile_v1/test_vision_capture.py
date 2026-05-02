import time
from playwright.sync_api import sync_playwright
import vision_tools

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def test_capture():
    """สคริปต์ทดสอบการแคปภาพโพสต์จาก Browser ที่เปิดอยู่"""
    save_path = "test_post_capture.png"
    
    with sync_playwright() as p:
        try:
            log_message("กำลังเชื่อมต่อกับ Browser (Port 9222)...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            if len(browser.contexts) == 0:
                log_message("ไม่พบบริบทของ Browser กรุณาเปิด Chrome ไว้ก่อน")
                return
            
            context = browser.contexts[0]
            if len(context.pages) == 0:
                log_message("ไม่พบหน้า Page ที่เปิดอยู่")
                return
            
            page = context.pages[0]
            page.bring_to_front()
            
            log_message(f"หน้าปัจจุบันคือ: {page.url}")
            
            success = vision_tools.capture_target_post(page, save_path)
            
            if success:
                log_message(f"--- ทดสอบสำเร็จ! กรุณาเปิดไฟล์ {save_path} เพื่อดูผลลัพธ์ ---")
            else:
                log_message("--- ทดสอบล้มเหลว ---")

        except Exception as e:
            log_message(f"ข้อผิดพลาดในการทดสอบ: {str(e)}")

if __name__ == "__main__":
    test_capture()
