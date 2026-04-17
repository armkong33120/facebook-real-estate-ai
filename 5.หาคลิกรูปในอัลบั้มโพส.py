import time
import config
from playwright.sync_api import sync_playwright

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def log_failed_link(url):
    file_path = "failed_links.txt"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] FAILED to open album: {url}\n")
    log_message(f"บันทึกลิงก์ที่ล้มเหลวลงใน {file_path}")

# ---------- JS: ตัวไล่ล่าเวอร์ชั่นดั้งเดิม (High Speed & Green Focus) ----------
CHASE_JS = """
async ([stabilityCount, delayStable]) => {
    // 1. หาพื้นที่ควบคุม (Scroller)
    const scroller = document.querySelector('div[role="dialog"] .xy5w88m') || 
                     document.querySelector('div[role="dialog"] div[style*="overflow-y"]') ||
                     document.querySelector('div[role="dialog"]') || 
                     document.documentElement;

    // 2. ค้นหาเป้าหมาย (อัลบั้มรูป) - รองรับทั้งโพสต์ปกติ และ Marketplace
    const album = document.querySelector('div[role="dialog"] a[href*="/photo"]') || 
                  document.querySelector('div[role="dialog"] a[href*="/commerce/listing"]') ||
                  document.querySelector('a[href*="/photo"]') ||
                  document.querySelector('a[href*="/commerce/listing"]');

    if (!album) return { success: false, msg: "หาอัลบั้มไม่เจอ (Element missing)" };

    // 3. วาดกรอบเขียวล็อกเป้า (โชว์ทันที่เพื่อการตอบสนองที่รวดเร็ว)
    const hl = document.createElement('div');
    hl.style.cssText = 'position:fixed;border:5px solid #00FF00;box-shadow:0 0 20px #00FF00;z-index:999999;pointer-events:none;transition:all 0.1s;';
    document.body.appendChild(hl);

    let stable = 0;
    const maxAttempts = 120; // ให้เวลา 12 วินาทีในการไล่ล่า

    for (let i = 0; i < maxAttempts; i++) {
        const rect = album.getBoundingClientRect();
        const sRect = (scroller === document.documentElement) ? 
                      { top: 0, height: window.innerHeight } : 
                      scroller.getBoundingClientRect();
        
        // อัปเดตกรอบเขียวให้ตามติดเป้าหมาย
        hl.style.left = rect.left + 'px';
        hl.style.top = rect.top + 'px';
        hl.style.width = rect.width + 'px';
        hl.style.height = rect.height + 'px';

        const offset = (rect.top + rect.height/2) - (sRect.top + sRect.height/2);

        if (Math.abs(offset) > 35) {
            // รูดเข้าหาทันที (Behavior: auto เพื่อความไว)
            scroller.scrollBy({ top: offset * 0.8, behavior: 'auto' });
            hl.style.borderColor = '#FF0000'; // แดง = กำลังปรับตำแหน่ง
            stable = 0;
        } else {
            hl.style.borderColor = '#00FF00'; // เขียว = เข้าเป้าแล้ว
            stable++;
        }

        if (stable >= stabilityCount) {
            // เป้าหมายนิ่งแล้ว!
            await new Promise(r => setTimeout(r, delayStable * 1000));
            hl.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
            setTimeout(() => hl.remove(), 800);
            return { success: true, x: rect.left + rect.width/2, y: rect.top + rect.height/2 };
        }

        await new Promise(r => setTimeout(r, 100)); // วนซ้ำทุก 0.1 วินาที
    }

    hl.remove();
    return { success: false, msg: "ไล่ล่าไม่สำเร็จ (Target unstable)" };
}
"""

def run_step_5(page=None, baseline_url=None, predefined_coords=None, **kwargs):
    """
    ขั้นตอนที่ 5 (V37.26 - Original Speed Production)
    - ยกยอดระบบจากตัว Debug ที่รันผ่าน 100% มาใส่ในตัวจริง
    - เน้นความไว 100ms และกรอบเขียวล็อกเป้า
    - รองรับการเปิดหน้าต่างใหม่เองหากเกิดข้อผิดพลาด (Self-Healing)
    """
    log_message("เริ่มขั้นตอนที่ 5: ระบบไล่ล่าล็อกเป้า (V37.26 - Original Mode)...")

    with sync_playwright() as p:
        try:
            # เชื่อมต่อผ่าน IPv4 เพื่อความเสถียร
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            
            # --- ระบบอัจฉริยะกู้ชีพ (Tab Recovery) ---
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            active_page = context.pages[0] if context.pages else context.new_page()
            active_page.bring_to_front()
            # -------------------------------------

            # นำทางไปยังลิงก์เป้าหมาย
            target_url = (baseline_url or active_page.url).replace("m.facebook.com", "www.facebook.com")
            current_url = active_page.url.replace("m.facebook.com", "www.facebook.com")

            if current_url != target_url:
                log_message(f"🔄 Navigate ไปที่: {target_url}")
                active_page.goto(target_url, wait_until="domcontentloaded")

            # หน่วงเวลาให้นิ่งขึ้น (เพิ่มจากเดิมเป็น 4 วิ เพื่อหลบพวก Popup ของ Browser)
            time.sleep(4)

            # เริ่มระบบไล่ล่าล็อกเป้าแบบต้นฉบับ
            result = active_page.evaluate(CHASE_JS, [config.CHASE_STABILITY_COUNT, config.DELAY_STABLE_BEFORE_CLICK])

            if result.get("success"):
                log_message(f"✅ ล็อกเป้าสำเร็จ! คลิกที่ ({result['x']:.0f}, {result['y']:.0f})")
                active_page.mouse.click(result['x'], result['y'])
                time.sleep(config.DELAY_AFTER_CLICK)
                return True
            else:
                log_message(f"❌ ภารกิจขัดข้อง: {result.get('msg')}")
                log_failed_link(target_url)
                return False

        except Exception as e:
            log_message(f"🚨 ข้อผิดพลาดใน Step 5: {str(e)}")
            return False