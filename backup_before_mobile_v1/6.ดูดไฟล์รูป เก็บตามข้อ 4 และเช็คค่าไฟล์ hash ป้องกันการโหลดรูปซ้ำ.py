import os
import time
import hashlib
import requests
import config
from playwright.sync_api import sync_playwright

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def get_image_hash(file_path):
    """คำนวณค่า MD5 ของไฟล์"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def run_step_6(save_dir):
    """ฟังก์ชันหลักสำหรับขั้นตอนที่ 6: ดูดรูป High-Res และรันความเร็วสูง"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            page = browser.contexts[0].pages[0]

            # 1. รอเพียงครู่เดียวพอ (ลดเหลือ 1.5 วิ สำหรับโหลด)
            log_message("คอยภาพนิ่ง (1.5 วิ)...")
            time.sleep(config.DELAY_IMAGE_STILL)

            # 2. ขุดหาภาพ High-Res จาก srcset (DOM Method Pro)
            log_message("กำลังสกัดลิงก์ High-Res จาก CDN...")
            img_data = page.evaluate("""() => {
                const images = Array.from(document.querySelectorAll('img'));
                let bestSrc = null;
                let maxArea = 0;
                
                images.forEach(img => {
                    if (img.offsetWidth > 200 && img.offsetHeight > 200) {
                        const area = img.offsetWidth * img.offsetHeight;
                        if (area > maxArea) {
                            maxArea = area;
                            // พยายามดรอว์ค่าจาก srcset ถ้ามี (เพื่อเอาตัวที่ชัดที่สุด)
                            if (img.srcset) {
                                const sources = img.srcset.split(',').map(s => s.trim().split(' ')[0]);
                                bestSrc = sources[sources.length - 1]; // เอาตัวสุดท้ายมักจะใหญ่สุด
                            } else {
                                bestSrc = img.src;
                            }
                        }
                    }
                });
                return bestSrc;
            }""")

            if not img_data:
                log_message("ข้าม: ไม่พบรูปที่ต้องการ")
                return False, None

            # 3. ดาวน์โหลดและเช็ค Hash ใน Memory (ใช้ไฟล์ประวัติช่วย)
            history_file = os.path.join(save_dir, "processed_hashes.txt")
            seen_hashes = set()
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    seen_hashes = set(line.strip() for line in f)

            temp_path = os.path.join(save_dir, "temp_download.jpg")
            response = requests.get(img_data, timeout=10)
            if response.status_code == 200:
                with open(temp_path, "wb") as f:
                    f.write(response.content)
                
                img_hash = get_image_hash(temp_path)

                if img_hash in seen_hashes:
                    os.remove(temp_path)
                    log_message(f"พบรูปซ้ำ (Hash: {img_hash[:8]}...)")
                    return "DUPLICATE", img_hash
                else:
                    # เก็บประวัติ Hash
                    with open(history_file, "a") as f:
                        f.write(img_hash + "\n")
                    
                    # ตั้งชื่อแบบเรียงลำดับ 1, 2, 3...
                    existing_files = [f for f in os.listdir(save_dir) if f.endswith('.jpg') and f != "temp_download.jpg"]
                    new_index = len(existing_files) + 1
                    final_path = os.path.join(save_dir, f"{new_index}.jpg")
                    
                    os.rename(temp_path, final_path)
                    log_message(f"ดูดรูปที่ {new_index} สำเร็จ! รหัส: {img_hash[:8]}... (รอ 1 วิ)")
                    time.sleep(config.DELAY_AFTER_DOWNLOAD) # ลดเหลือ 1 วิ ตามคำขอ
                    return "NEW", img_hash
            
            return False, None

        except Exception as e:
            log_message(f"ข้อผิดพลาด 6: {str(e)}")
            return False, None