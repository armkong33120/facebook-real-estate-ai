import os
# --- SUPPRESS NOISY LOGS ---
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'

import io
import json
import subprocess
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# Import Our Custom Modules
import ghost_config as config
from ghost_ai import verify_api_connectivity
from ghost_scraper import run_ghost_pipeline

def ghost_log(message):
    """ฟังก์ชันสำหรับบันทึกประวัติลงไฟล์ .log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config.LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def load_checkpoint():
    """โหลดข้อมูลจุดพักงานล่าสุดจากไฟล์ JSON"""
    if os.path.exists(config.CHECKPOINT_FILE):
        try:
            with open(config.CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return None

def save_checkpoint(ba):
    """บันทึกจุดพักงาน โดยระบุว่าตัวที่สำเร็จล่าสุดคือ BA อะไร"""
    data = {
        "last_ba": ba,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(config.CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def clear_checkpoint():
    """ล้างจุดพักงานเมื่อรันจบทั้งหมดสำเร็จ"""
    if os.path.exists(config.CHECKPOINT_FILE):
        os.remove(config.CHECKPOINT_FILE)

def load_mapping():
    """โหลดรายการลิงก์จาก uat_links.txt"""
    if not os.path.exists(config.MAPPING_FILE):
        print(f"❌ Error: ไม่พบไฟล์ {config.MAPPING_FILE}")
        return {}
    
    mapping = {}
    with open(config.MAPPING_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if "|" in line:
                ba, url = line.split("|")
                mapping[ba.strip()] = url.strip()
    return mapping

def main():
    # --- PHASE 0: PRE-FLIGHT CHECK ---
    print("🔍 กำลังตรวจสอบการเชื่อมต่อ AI (Pre-Flight Check)...")
    success, msg = verify_api_connectivity()
    if not success:
        print(f"\n🛑 ปฏิบัติการถูกระงับ: {msg}")
        return
    print(f"✅ {msg}")

    mapping = load_mapping()
    if not mapping:
        print("💡 ไม่มีรายชื่อลิงก์ใน uat_links.txt ให้ปฏิบัติการ")
        return

    # --- PHASE 1: MODE SELECTION & CHECKPOINT ---
    checkpoint = load_checkpoint()
    skip_mode = False
    last_ba = checkpoint.get("last_ba") if checkpoint else None

    print("\n════════════════════════════════════════════════")
    print("🕵️  GHOST AGENT V13.80 (GENAI MODERN MIGRATION)")
    if checkpoint:
        print(f"🔄 พบประวัติการทำงานค้างอยู่ที่: {last_ba}")
        print("   [1] รันต่อจากจุดเดิม (Resume)")
        print("   [2] เริ่มต้นใหม่ทั้งหมด (Start Over)")
    else:
        print("   [1] เริ่มต้นงานใหม่ (Start New Mission)")
    
    print("   [3] กำหนดช่วงเอง (Custom Range)")
    choice = input("👉 เลือกโหมดปฏิบัติการ (ใส่เลข 1, 2 หรือ 3): ").strip()

    if choice == "2":
        print("🗑️  ล้างหน่วยความจำ... เริ่มต้นใหม่ทั้งหมด")
        clear_checkpoint()
    elif choice == "3":
        items = list(mapping.items())
        print(f"📊 มีทรัพย์ทั้งหมด {len(items)} รายการ (1 ถึง {len(items)})")
        try:
            start_idx = int(input(f"   🚩 เริ่มที่ลำดับ (1-{len(items)}): ") or 1)
            end_input = input(f"   🏁 จบที่ลำดับ (ค่าว่าง = จนสุดไฟล์): ").strip()
            end_idx = int(end_input) if end_input else len(items)
            mapping = dict(items[start_idx-1 : end_idx])
            print(f"🎯 กำหนดช่วงสำเร็จ: เตรียมรันลำดับที่ {start_idx} ถึง {end_idx}")
        except ValueError:
            print("⚠️  ค่าที่กรอกไม่ใช่ตัวเลข... จะรันตามปกติ")
    elif choice == "1" and checkpoint:
        print(f"⏩ โหมดกู้คืนงาน: เตรียมกระโดดไปเริ่มต่อจาก {last_ba}...")
        skip_mode = True
        
    print(f"🚀 เตรียมปฏิบัติการกวาดทรัพย์ทั้งหมด {len(mapping)} รายการ")
    print("════════════════════════════════════════════════")
    
    with sync_playwright() as p:
        # เปิด Browser พร้อม Profile เดิม (ไม่ต้อง Login ใหม่)
        context = p.chromium.launch_persistent_context(
            config.USER_DATA_DIR,
            headless=False,
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0] if context.pages else context.new_page()

        ghost_log("=== เริ่มต้นปฏิบัติการรอบใหม่ ===")
        for ba, url in mapping.items():
            # ตรรกะกระโดดข้ามตัวที่ทำเสร็จแล้ว
            if skip_mode:
                if ba == last_ba:
                    skip_mode = False # เจอตัวล่าสุดแล้ว ตัวถัดไปเริ่มทำได้
                    continue
                continue

            try:
                run_ghost_pipeline(page, url, ba)
                save_checkpoint(ba) # บันทึกความสำเร็จรายตัว
                ghost_log(f"✅ สำเร็จ: ทรัพย์ {ba} ({url})")
            except RuntimeError as e:
                # กรณี Error รุนแรง (ไฟล์พัง/รูปหาย) ให้หยุดรันทั้งหมดทันที
                error_msg = f"🛑 หยุดปฏิบัติการฉุกเฉิน (CRITICAL STOP): {str(e)}"
                print(f"\n{error_msg}")
                ghost_log(error_msg)
                print(f"⚠️ บันทึกจุดค้างงานไว้ที่: {ba}")
                # หมายเหตุ: เราไม่ save_checkpoint ตัวที่พาร์ค เพราะมันไม่สำเร็จ
                break # หยุดรันคิวที่เหลือทั้งหมด
            except Exception as e:
                # กรณี Error ทั่วไป ให้ข้ามไปทำทรัพย์ถัดไป
                error_msg = f"❌ ข้ามทรัพย์ {ba} (General Error): {str(e)}"
                print(error_msg)
                ghost_log(error_msg)
        
        # หากรันจบ loop โดยไม่มีการ break (แสดงว่าสำเร็จครบทุกตัว)
        else:
            print("\n🏆 ปฏิบัติการกวาดทรัพย์เสร็จสิ้นครบทุกรายการ!")
            clear_checkpoint() # ล้างจุดพักงานเพื่อให้รันรอบหน้าเริ่มใหม่หมด
            ghost_log("=== จบภารกิจรอบนี้ (สมบูรณ์) ===")

        print("\n📂 กำลังเปิดโฟลเดอร์ผลลัพธ์ให้ตรวจสอบ...")
        subprocess.run(["open", config.BASE_RESULT_DIR])
        time.sleep(5)
        context.close()

if __name__ == "__main__":
    main()
