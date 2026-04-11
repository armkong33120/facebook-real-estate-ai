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
    [HUMAN-HAND V10 MODE] กู้ร่างพิกัด Macbook แท้ที่คุณกวงจูนไว้
    ทำหน้าที่: คลิกและเลื่อนตามพิกัดเป๊ะๆ เพื่อเปิด Lightbox (V13.70 แฝงร่างมนุษย์)
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
        
        # 3. คลิกเปิด Lightbox ที่พิกัดเป๊ะๆ (500, 350) พร้อม Jitter
        print("      🖱️  คลิกที่พิกัด 500, 350 เพื่อเปิดแกลเลอรี่...")
        ghost_human_click(page, 500, 350)
        ghost_human_wait(page, 5000)
        return True
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
        
        for i in range(50):
            # 4.1 ดึงลิ้งก์รูปจาก "กึ่งกลางจอ"
            img_src = page.evaluate('''() => {
                const el = document.elementFromPoint(720, 380);
                if (!el) return null;
                if (el.tagName === 'IMG') return el.src;
                const nestedImg = el.querySelector('img');
                if (nestedImg) return nestedImg.src;
                
                // Fallback: หากึ่งกลางไม่ได้จริงๆ ให้เอารูปที่ใหญ่ที่สุดใน Dialog
                const dialog = document.querySelector('div[role="dialog"]');
                if (dialog) {
                    const imgs = Array.from(dialog.querySelectorAll('img')).filter(img => img.width > 400);
                    return imgs.length > 0 ? imgs[0].src : null;
                }
                return null;
            }''')

            if img_src:
                try:
                    # โหลดข้อมูลรูปภาพดิบเพื่อเอามาทำ Hash
                    req = urllib.request.Request(img_src, headers={'User-Agent': 'Mozilla/5.0'})
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
                    
                except Exception as e:
                    print(f"       ⚠️ พลาดการประมวลผลรูปที่ {len(harvested_hashes)+1}: {e}")
            else:
                print(f"       ⚠️ ใบที่ {i+1}: มองไม่เห็นรูปที่จุดกึ่งกลาง...")

            # 4.2 เลื่อนถัดไป (Agent Relay 5s เพื่อความเสถียร)
            next_btn = page.query_selector('div[aria-label="รูปภาพถัดไป"], div[aria-label="Next Photo"]')
            if next_btn:
                next_btn.click()
            else:
                page.keyboard.press("ArrowRight")
                
            ghost_human_wait(page, 5000) 

        # [!] ตรวจสอบความถูกต้องขั้นสุดท้าย
        actual_images = [f for f in os.listdir(target_dir) if f.endswith(".jpg")]
        if len(actual_images) < MIN_IMAGES_REQUIRED:
            raise RuntimeError(f"CRITICAL: รูปภาพไม่ครบถ้วน (พบ {len(actual_images)} / ต้องการ {MIN_IMAGES_REQUIRED}) สำหรับทรัพย์ {ba}")
        
        print(f"       ✅ สำเร็จระดับ V10: เก็บรูปได้ {len(actual_images)} ใบ")

    except Exception as e:
        raise e
