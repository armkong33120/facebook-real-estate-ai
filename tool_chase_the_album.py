import time
import os
import config
from playwright.sync_api import sync_playwright

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

# ---------- JS: ตัวไล่ล่าเวอร์ชั่นดั้งเดิม (Fast & Green Focus) ----------
# เวอร์ชั่นนี้จะเน้นความเร็ว 100ms และไม่มีการสแกนหลายรอบให้เสียเวลา
CHASE_JS_ORIGINAL = """
async ([stabilityCount, delayStable]) => {
    // 1. หาพื้นที่ควบคุม (Scroller)
    const scroller = document.querySelector('div[role="dialog"] .xy5w88m') || 
                     document.querySelector('div[role="dialog"] div[style*="overflow-y"]') ||
                     document.querySelector('div[role="dialog"]') || 
                     document.documentElement;

    // 2. หาเป้าหมาย (อัลบั้มรูป)
    const findAlbum = () => {
        return document.querySelector('div[role="dialog"] a[href*="/photo"]') || 
               document.querySelector('a[href*="/photo"]');
    };

    const album = findAlbum();
    if (!album) return { success: false, msg: "หาอัลบั้มไม่เจอ" };

    // 3. สร้างกรอบเขียวล็อกเป้า (โชว์ทันทีแบบที่พี่ชอบ)
    const hl = document.createElement('div');
    hl.style.cssText = 'position:fixed;border:5px solid #00FF00;box-shadow:0 0 20px #00FF00;z-index:999999;pointer-events:none;transition:all 0.1s;';
    document.body.appendChild(hl);

    let stable = 0;
    const maxAttempts = 100; // วิ่งสู้ฟัด 10 วินาที

    for (let i = 0; i < maxAttempts; i++) {
        const rect = album.getBoundingClientRect();
        const sRect = (scroller === document.documentElement) ? 
                      { top: 0, height: window.innerHeight } : 
                      scroller.getBoundingClientRect();
        
        // อัปเดตตำแหน่งกรอบเขียว
        hl.style.left = rect.left + 'px';
        hl.style.top = rect.top + 'px';
        hl.style.width = rect.width + 'px';
        hl.style.height = rect.height + 'px';

        const offset = (rect.top + rect.height/2) - (sRect.top + sRect.height/2);

        if (Math.abs(offset) > 30) {
            // รูดเข้าหาเป้าหมายทันที
            scroller.scrollBy({ top: offset * 0.8, behavior: 'auto' });
            hl.style.borderColor = '#FF0000'; // แดงคือยังไม่เข้าเป้า
            stable = 0;
        } else {
            hl.style.borderColor = '#00FF00'; // เขียวคือนิ่งแล้ว
            stable++;
        }

        if (stable >= stabilityCount) {
            // นิ่งแล้ว รอจิ้ม!
            await new Promise(r => setTimeout(r, delayStable * 1000));
            hl.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
            setTimeout(() => hl.remove(), 500);
            return { success: true, x: rect.left + rect.width/2, y: rect.top + rect.height/2 };
        }

        await new Promise(r => setTimeout(r, 100)); // วนซ้ำทุก 0.1 วินาที (ความเร็วสูง)
    }

    hl.remove();
    return { success: false, msg: "ไล่ล่าไม่สำเร็จ (Timeout)" };
}
"""

def run_chase_test():
    with sync_playwright() as p:
        try:
            log_message("🌐 เชื่อมต่อ Browser (ระบบอิสระ 100%)...")
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            
            # --- ระบบอัจฉริยะ: กัน Tab หลุด ---
            if not browser.contexts:
                context = browser.new_context()
            else:
                context = browser.contexts[0]
            
            if not context.pages:
                page = context.new_page()
            else:
                page = context.pages[0]
            # -------------------------------
            
            page.bring_to_front()

            failed_file = "failed_links.txt"
            if not os.path.exists(failed_file):
                log_message("✅ ไม่พบไฟล์ failed_links.txt")
                return

            with open(failed_file, "r", encoding="utf-8") as f:
                urls = [l.split("FAILED to open album: ")[1].strip() for l in f if "FAILED to open album: " in l]
            
            urls = list(dict.fromkeys(urls)) # คลีนลิ้งก์ซ้ำ
            if not urls:
                 log_message("✅ ลิงก์ที่ล้มเหลวถูกจัดการหมดแล้ว!")
                 return

            log_message(f"🎯 เริ่มโหมด 'ไล่ล่าล็อกเป้า' (Original Speed) {len(urls)} รายการ")

            for i, url in enumerate(urls, 1):
                clean_url = url.replace("m.facebook.com", "www.facebook.com")
                log_message(f"[{i}/{len(urls)}] 🚀 พุ่งไปที่: {clean_url}")
                page.goto(clean_url, wait_until="domcontentloaded")
                
                time.sleep(1.5) # หน่วงรอหน้าเว็บแวบเดียว
                
                # รัน JS ไล่ล่าแบบดั้งเดิม
                result = page.evaluate(CHASE_JS_ORIGINAL, [config.CHASE_STABILITY_COUNT, config.DELAY_STABLE_BEFORE_CLICK])
                
                if result.get("success"):
                    log_message(f"✅ ล็อกเป้าสำเร็จ! คลิกที่ ({result['x']:.0f}, {result['y']:.0f})")
                    page.mouse.click(result['x'], result['y'])
                    time.sleep(3)
                else:
                    log_message(f"❌ พลาด: {result.get('msg')}")

            log_message("\n✨ ภารกิจสำเร็จตามคำสั่งครับคุณพี่!")

        except Exception as e:
            log_message(f"💥 เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    run_chase_test()
