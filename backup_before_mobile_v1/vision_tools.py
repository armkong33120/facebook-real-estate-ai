import time
import os
from playwright.sync_api import sync_playwright
import subprocess
from PIL import Image, ImageDraw

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def capture_target_post(page, save_path):
    """
    ฟังก์ชันสำหรับถ่ายภาพหน้าจอเฉพาะส่วนที่เป็น Post Content
    - เพิ่มระบบ Auto-Stretch: ขยายหน้าจอให้ยาวขึ้นชั่วคราวเพื่อให้เห็นโพสต์ทั้งหมด
    """
    try:
        log_message(f"กำลังเตรียมแคปภาพโพสต์เจาะจงจุด: {save_path}")
        
        # 0. เก็บค่าขนาดหน้าจอเดิม และ ถ่างหน้าจอให้ยาว (5,000px) เพื่อให้เห็นโพสต์ยาวๆ
        original_viewport = page.viewport_size
        if not original_viewport:
            original_viewport = {"width": 1280, "height": 800} # ค่าสำรองถ้าหาไม่เจอ
            
        page.set_viewport_size({"width": original_viewport["width"], "height": 5000})
        time.sleep(2) # รอให้หน้าเว็บ Render หลังถ่างจอ

        # 1. ค้นหา Container หลักของโพสต์ (รองรับ m.facebook.com และ www)
        possible_selectors = [
            'div[role="main"]',
            'div[id^="m_story_permalink_view"]',
            'article',
            'div[data-tracking-duration_id]',
            'div[data-testid="fbfeed_story"]'
        ]
        
        target_element = None
        for selector in possible_selectors:
            el = page.locator(selector).first
            if el.is_visible(timeout=3000):
                target_element = el
                log_message(f"พบ Post Container ด้วย Selector: {selector}")
                break
        
        if not target_element:
            log_message("ไม่พบ Container ของโพสต์ จะใช้การถ่ายภาพทั้งหน้าแทน")
            page.screenshot(path=save_path, full_page=True)
            # คืนค่าหน้าจอ
            page.set_viewport_size(original_viewport)
            return True

        # 2. รอให้รูปภาพในโพสต์โหลดเสร็จ (ป้องกันภาพขาด)
        log_message("คอยให้รูปภาพในโพสต์โหลดเสร็จ...")
        page.evaluate("""() => {
            const images = Array.from(document.querySelectorAll('img'));
            return Promise.all(images.map(img => {
                if (img.complete) return Promise.resolve();
                return new Promise(resolve => { img.onload = img.onerror = resolve; });
            }));
        }""")
        time.sleep(2)

        # 3. ถ่ายภาพเฉพาะ Element นั้นๆ
        target_element.scroll_into_view_if_needed()
        time.sleep(1)
        
        target_element.screenshot(path=save_path)
        log_message(f"แคปภาพโพสต์สำเร็จ: {save_path}")
        
        # 4. คืนค่าขนาดหน้าจอเดิม
        page.set_viewport_size(original_viewport)
        return True

    except Exception as e:
        log_message(f"เกิดข้อผิดพลาดในการแคปภาพ: {str(e)}")
        return False

def mark_and_show_image(image_path, x, y, duration=1):
    """
    ฟังก์ชันพิเศษ: วาดเป้าหมายลงในรูปภาพและเปิดโชว์ให้ผู้ใช้ดู
    (จะทำงานเฉพาะเมื่อเปิดโหมด SHOW_DEBUG_VISUALS ใน ghost_main.py เท่านั้น)
    """
    if os.environ.get("DEBUG_VISUALS") != "1":
        return True

    try:
        # 1. เปิดรูปภาพและวาดเป้าหมาย
        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            
            # วาดกากบาท (Crosshair) สีแดง
            size = 50
            draw.line((x - size, y, x + size, y), fill="red", width=10)
            draw.line((x, y - size, x, y + size), fill="red", width=10)
            
            # วาดวงกลมล้อมรอบ
            draw.ellipse((x - size, y - size, x + size, y + size), outline="yellow", width=5)
            
            img.save(image_path)
        
        # 2. เปิดโชว์ภาพด้วยโปรแกรมของ OS
        subprocess.Popen(["open", image_path])
        
        # 3. [PRO FEATURE] ย้ายหน้าต่างไปที่จอ LG อัตโนมัติ (AppleScript)
        move_to_lg_script = """
        tell application "System Events"
            repeat 20 times -- ลองวนหาหน้าต่าง Preview 2 วินาที
                if exists (process "Preview") then
                    tell process "Preview"
                        if exists window 1 then
                            set screenBounds to bounds of every screen
                            if (count screenBounds) > 1 then
                                -- หาจอที่ไม่ใช่จอหลัก (Main Screen มักจะเป็น item 1)
                                set mainBounds to item 1 of screenBounds
                                repeat with b in screenBounds
                                    if b is not mainBounds then
                                        set targetX to (item 1 of b) + 100
                                        set targetY to (item 2 of b) + 100
                                        set {w, h} to {1280, 800} -- ขนาดหน้าต่าง
                                        set position of window 1 to {targetX, targetY}
                                        -- set size of window 1 to {w, h}
                                        exit repeat
                                    end if
                                end repeat
                            end if
                            exit repeat
                        end if
                    end tell
                end if
                delay 0.1
            end repeat
        end tell
        """
        try:
            subprocess.Popen(["osascript", "-e", move_to_lg_script])
        except:
            pass

        log_message(f"[UI] แสดงจุดเป้าหมายบนจอ LG (x={x}, y={y}) ให้ตรวจสอบ {duration} วินาที...")
        time.sleep(duration)
        
        return True
    except Exception as e:
        log_message(f"ไม่สามารถวาดเป้าหมายบนรูปได้: {str(e)}")
        return False
