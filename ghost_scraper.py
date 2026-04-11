import os
import re
import random
import urllib.request
from ghost_config import IMAGE_RELAY_TIME, RETRY_RELAY_TIME, BASE_RESULT_DIR, MIN_IMAGES_REQUIRED
from ghost_ai import analyze_location_with_ai
from ghost_text import clean_property_text
from ghost_visual import hash_tweak_save, get_image_hash

def ghost_modal_archer(page):
    """
    [FUNCTION: Modal Archer]
    ทำหน้าที่: เจาะทะลวงหน้าต่างลอย Facebook เพื่อดูดเนื้อหาโพสต์
    """
    return page.evaluate('''() => {
        // [AGENT BRAIN V13.65] ค้นหาเฉพาะ Dialog ที่น่าจะเป็นเนื้อหาอสังหาจริงๆ
        const dialogs = Array.from(document.querySelectorAll('div[role="dialog"]'));
        
        // กรองหา Dialog ที่ 'กว้าง' พอจะเป็นเนื้อหาโพสต์ (เมินแจ้งเตือนที่มักจะแคบ)
        const contentDialog = dialogs.find(d => {
            const rect = d.getBoundingClientRect();
            const isWide = rect.width > 450;
            const isNotNotification = !d.innerText.includes('การแจ้งเตือน') && !d.innerText.includes('Notifications');
            return isWide && isNotNotification;
        }) || dialogs[0]; // Fallback ไปตัวแรกถ้าหาไม่เจอ

        if (contentDialog) {
            // คลิก 'ดูเพิ่มเติม' หากมี
            const buttons = Array.from(contentDialog.querySelectorAll('div[role="button"]'));
            const seeMore = buttons.find(b => b.innerText.includes('ดูเพิ่มเติม') || b.innerText.includes('See more'));
            if (seeMore) seeMore.click();
            
            // พยายามหา div dir="auto" ใน Dialog นี้
            const body = contentDialog.querySelector('div[dir="auto"]');
            return body ? body.innerText : contentDialog.innerText;
        }
        return "";
    }''')

def ghost_human_wait(page, base_ms):
    """[AGENT BRAIN: Stealth Wait] สุ่มเวลาช่วง 80% - 130% ของเวลาหลัก"""
    jitter_factor = random.uniform(0.8, 1.3)
    wait_time = int(base_ms * jitter_factor)
    page.wait_for_timeout(wait_time)

def ghost_human_click(page, x, y):
    """[AGENT BRAIN: Stealth Click] คลิกแบบสุ่มระยะ 3-5 พิกเซลรอบเป้าหมาย"""
    jx = x + random.randint(-4, 4)
    jy = y + random.randint(-4, 4)
    page.mouse.click(jx, jy)

def open_lightbox(page):
    """
    [HUMAN-HAND V10 MODE] กู้ร่างพิกัด Macbook แท้ของคุณกวงจูนไว้
    ทำหน้าที่: คลิกและเลื่อนตามพิกัดเป๊ะๆ เพื่อเปิด Lightbox (V15.00 Structural Mode)
    """
    print("      🎯 [HAND-MODE] เริ่มล็อกพิกัดตามขนาดจอ Macbook (Human-Hand)...")
    try:
        # 1. คลิกกลางจอแบบรัวเพื่อ Focus (Triple-Click 720, 380) พร้อม Jitter
        print("      🎯 [AGENT BRAIN] กำลังรัวคลิกกลางจอกระตุ้น Focus (720, 380)...")
        for _ in range(3):
            ghost_human_click(page, 720, 380)
            ghost_human_wait(page, 500)
        ghost_human_wait(page, 2000)
        
        # 2. [AGENT BRAIN] รูดสกอร์บาร์ด้วยระบบ Smart Wheel (Hardware Simulation)
        print("      🔄 [SMART WHEEL] กำลังรูดสกอร์บาร์ลงด้านล่างให้สุดเพื่อโหลดรูปภาพ...")
        page.mouse.wheel(0, 5000)
        ghost_human_wait(page, 5000)
        
        # 3. คลิกเปิด Lightbox (พิกัดเป้าหมาย 500, 350) พร้อมระบบสแกนหาแบบความละเอียดสูง (V14.10)
        base_y = 350
        # สแกนพิกัดขยับ "ขึ้นด้านบน" เท่านั้น ตามที่คุณกวงสั่งกำชับ (Upward Only)
        offsets = [0, -50, -100, -150, -200, -250, -300] 
        
        for offset in offsets:
            target_y = base_y + offset
            if target_y < 50: continue # ไม่กดสูงเกินไปจนโดน Toolbar
            if offset != 0:
                print(f"      🔍 [HUNT: Gallery] ลองขยับพิกัดแนวตั้ง: {offset}px (Target Y: {target_y})")
            
            ghost_human_click(page, 500, target_y)
            ghost_human_wait(page, 3000) # รอสั้นๆ เพื่อเช็คว่าเปิดหรือยัง
            
            # เช็คว่า Lightbox เปิดหรือยัง (หา div role="dialog")
            is_opened = page.query_selector('div[role="dialog"]')
            if is_opened:
                if offset != 0:
                    print(f"      ✅ [HUNT SUCCESS] เจอแกลเลอรี่ที่ Offset {offset}px!")
                else:
                    print("      🖱️  คลิกที่พิกัด 500, 350 เพื่อเปิดแกลเลอรี่... (สำเร็จ)")
                ghost_human_wait(page, 3000)
                return True
        
        print("      ⚠️ [HUNT FAILED] สแกนหาจุดเปิดแกลเลอรี่ไม่สำเร็จ...")
        return False
    except Exception as e:
        print(f"      ⚠️ Hand-Mode Error: {e}")
        return False

def run_ghost_pipeline(page, url, ba):
    """
    [FUNCTION: Main Extraction Pipeline]
    ทำหน้าที่: ลำดับขั้นตอนการดูดข้อมูลทั้งหมดของ 1 ทรัพย์
    """
    print(f"\n🚀 [GHOST AGENT V13] เริ่มปฏิบัติการทรัพย์ {ba}...")
    
    try:
        # 1. เข้าสู่หน้าโพสต์
        print(f"   🔗 ลิงก์หลัก: {url}")
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(8000)
        
        # 2. ดูดข้อความและวิเคราะห์พิกัด
        print("   🔍 สกัดเนื้อหา (Modal Archer)...")
        post_content = ghost_modal_archer(page)
        if not post_content:
            post_content = page.evaluate('() => document.body.innerText')[:2000]
            
        province, district = analyze_location_with_ai(post_content[:2000])
        print(f"       📍 พิกัด: {province}/{district}")
        
        # 3. เตรียมโฟลเดอร์และบันทึกข้อความ
        target_dir = os.path.join(BASE_RESULT_DIR, province, district, ba)
        if not os.path.exists(target_dir): os.makedirs(target_dir)
        
        final_info = clean_property_text(post_content, ba)
        info_path = os.path.join(target_dir, "property_info.txt")
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(final_info)
        
        if not os.path.exists(info_path) or os.path.getsize(info_path) < 10:
            raise RuntimeError(f"CRITICAL: ไม่สามารถบันทึกข้อมูลข้อความลงไฟล์ .txt ได้ ({ba})")
            
        print("       📄 บันทึกข้อความขาวสะอาด (.txt) สำเร็จ!")
        
        # 4. เริ่มดูดรูปภาพ (V13.60 PURE VISUAL PROGRESS)
        print("   🖼️ [PURE VISUAL ENGINE] เริ่มปฏิบัติการกวาดรูปภาพ (ใช้ระบบ Hash 100%)...")
        opened = open_lightbox(page)
        
        harvested_hashes = set() # เก็บลายนิ้วมือรูปเพื่อเช็คความคืบหน้า
        consecutive_empty_hits = 0 # ตัวนับความล้มเหลวต่อเนื่อง (V13.90)
        
        for i in range(50):
            # 4.1 ดึงลิ้งก์รูปจาก "โครงสร้างแกลเลอรี่" โดยตรง (V15.00 Structural Search)
            # เราจะไม่ใช้แค่พิกัดคลิก แต่จะใช้การสแกนหา Object ที่เป็นรูปทรัพย์จริงๆ
            img_src = page.evaluate('''() => {
                const dialog = document.querySelector('div[role="dialog"]');
                if (!dialog) return null;

                // 1. ค้นหารูปภาพทั้งหมดใน Dialog
                const imgs = Array.from(dialog.querySelectorAll('img'));
                if (imgs.length === 0) return null;

                // 2. กรองเฉพาะรูปที่มีขนาดใหญ่พอจะเป็นรูปทรัพย์ (ตัด icon/pixel ทิ้ง)
                const validImgs = imgs.filter(img => {
                    const rect = img.getBoundingClientRect();
                    return rect.width > 200 && rect.height > 200 && !img.src.includes('static.xx.fbcdn.net');
                });

                if (validImgs.length === 0) return null;

                // 3. เลือกรูปที่ "อยู่กึ่งกลางที่สุด" หรือ "ใหญ่ที่สุด"
                // ลอจิก: เลือกรูปที่มีพื้นที่ (Area) มากที่สุด
                validImgs.sort((a, b) => (b.width * b.height) - (a.width * a.height));
                const bestImg = validImgs[0];

                return JSON.stringify({
                    src: bestImg.src,
                    width: bestImg.width,
                    height: bestImg.height
                });
            }''')

            final_src = None
            if img_src:
                try:
                    res_data = json.loads(img_src)
                    final_src = res_data.get('src')
                    if i == 0:
                        print(f"       ✅ พบภาพโครงสร้างความละเอียด: {res_data.get('width')}x{res_data.get('height')}")
                except:
                    final_src = None

            if final_src:
                try:
                    # โหลดข้อมูลรูปภาพดิบเพื่อเอามาทำ Hash
                    req = urllib.request.Request(final_src, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        img_data = resp.read()
                    
                    current_hash = get_image_hash(img_data)
                    
                    # [AGENT BRAIN V13.61] กลไกตรวจสอบรูปซ้ำ (Hash Detected)
                    if current_hash in harvested_hashes:
                        print(f"   🏁 จบภารกิจ! ตรวจพบลายนิ้วมือรูปซ้ำ (Hash Detected) ณ รูปที่ {len(harvested_hashes)+1}")
                        break
                    
                    # 3. บันทึกรูป (Tweak Hash ป้องกันการตรวจจับจาก FB)
                    img_index = len(harvested_hashes) + 1
                    print(f"       📸 ใบที่ {img_index}: กำลังบันทึกไฟล์ (Hash: {current_hash[:8]}...)")
                    hash_tweak_save(img_data, os.path.join(target_dir, f"property_{img_index}.jpg"))
                    
                    harvested_hashes.add(current_hash)
                    consecutive_empty_hits = 0 # รีเซ็ตเมื่อเจอรูปสำเร็จ
                    
                except Exception as e:
                    print(f"       ⚠️ พลาดการประมวลผลรูปที่ {len(harvested_hashes)+1}: {e}")
            else:
                consecutive_empty_hits += 1
                print(f"       ⚠️ ใบที่ {i+1}: มองไม่เห็นรูปที่จุดกึ่งกลาง... (ต่อเนื่องครั้งที่ {consecutive_empty_hits})")
                
                if consecutive_empty_hits >= 5:
                    raise RuntimeError("VISIBILITY_LOSS")

            # 4.2 เลื่อนถัดไป (Agent Relay 7s เพื่อความเสถียรสูงสุด - V15.00)
            next_btn = page.query_selector('div[aria-label="รูปภาพถัดไป"], div[aria-label="Next Photo"]')
            if next_btn:
                next_btn.click()
            else:
                page.keyboard.press("ArrowRight")
                
            ghost_human_wait(page, 7000) 

        # [!] ตรวจสอบความถูกต้องขั้นสุดท้าย
        actual_images = [f for f in os.listdir(target_dir) if f.endswith(".jpg")]
        if len(actual_images) < MIN_IMAGES_REQUIRED:
            raise RuntimeError(f"CRITICAL: รูปภาพไม่ครบถ้วน (พบ {len(actual_images)} / ต้องการ {MIN_IMAGES_REQUIRED}) สำหรับทรัพย์ {ba}")
        
        print(f"       ✅ สำเร็จระดับ V10: เก็บรูปได้ {len(actual_images)} ใบ")

    except Exception as e:
        raise e
