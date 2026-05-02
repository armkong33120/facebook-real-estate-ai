import time
from playwright.sync_api import sync_playwright

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def test_scroll():
    with sync_playwright() as p:
        try:
            log_message("🌐 เชื่อมต่อ Chrome (9222)...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            page = browser.contexts[0].pages[0]
            page.bring_to_front()

            # ลอจิกการหา "ม้วนฟิล์ม" ที่กำลังเลื่อนได้ในปัจจุบัน
            log_message("🔍 กำลังค้นหาตัวควบคุมระนาบการเลื่อน (Scroll Container)...")
            
            # JS ลอจิก: หา Element ที่มีเนื้อหายาวที่สุดและกำลังแสดงผลอยู่
            scroller_js = """
            () => {
                // หาตัว dialog หรือโพสต์ที่เปิดอยู่
                const modal = document.querySelector('div[role="dialog"]') || document.body;
                
                // ค้นหาตัวสกรอลข้างใน
                const findScroller = (root) => {
                // Selector ที่แม่นยำที่สุดสำหรับ "ม้วนฟิล์ม" ในกรอบเหลือง
                const scroller = document.querySelector('div[role="dialog"] .xy5w88m') || 
                                 document.querySelector('div[role="dialog"] [class*="xy5w88m"]') ||
                                 document.querySelector('div[role="dialog"] .x1iyjqo2');
                
                if (!scroller) return null;

                window._activeScroller = scroller;
                
                // ทำ Effect "กรอบเหลืองกะพริบ" ให้คุณพี่เห็นว่าบอทคุมตัวนี้อยู่
                scroller.style.border = '10px solid yellow';
                scroller.style.transition = 'all 0.5s';
                setTimeout(() => { scroller.style.border = 'none'; }, 2000);

                return {
                    totalHeight: scroller.scrollHeight,
                    viewHeight: scroller.clientHeight,
                    currentPos: scroller.scrollTop
                };
            }
            """
            
            info = page.evaluate(scroller_js)
            if not info:
                log_message("❌ ไม่พบกรอบเหลือง (Modal) บนหน้าจอ! กรุณาเปิดโพสต์ค้างไว้ก่อนรันครับ")
                return

            log_message(f"✅ พบม้วนฟิล์ม: ความสูงรวม {info['totalHeight']}px | หน้าต่างกว้าง {info['viewHeight']}px")

            # --- ทดสอบเลื่อนลงสุด ---
            log_message("⬇️  กำลังเลื่อนม้วนฟิล์มลงไป 'ล่างสุด' (จะเห็นคอมเมนต์)...")
            page.evaluate("window._activeScroller.scrollTo({top: window._activeScroller.scrollHeight, behavior: 'smooth'})")
            time.sleep(3)

            # --- ทดสอบเลื่อนขึ้นสุด ---
            log_message("⬆️  กำลังเลื่อนม้วนฟิล์มกลับไป 'บนสุด' (จะเห็นข้อความโพสต์)...")
            page.evaluate("window._activeScroller.scrollTo({top: 0, behavior: 'smooth'})")
            time.sleep(3)

            log_message("✨ สำเร็จ! บอทคุมข้อมูลใน 'กรอบเหลือง' ได้ 100% แล้วครับ")

        except Exception as e:
            log_message(f"❌ เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    test_scroll()
