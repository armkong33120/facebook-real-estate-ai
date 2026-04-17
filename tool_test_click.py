import os
import sys
import time
import config
from playwright.sync_api import sync_playwright

# โหลด Module จากชื่อไฟล์โดยตรง (เหมือน ghost_main.py)
import importlib.util

def load_module(file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, file_name)
    spec = importlib.util.spec_from_file_location("test_module", full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

step5 = load_module("5.หาคลิกรูปในอัลบั้มโพส.py")
ai_engine = load_module("ai_engine.py")
vision_tools = load_module("vision_tools.py")

def main():
    print("\n" + "="*50)
    print("🎯  TOOL: TEST CLICK STEP 5 (Vision Analysis)")
    print("="*50)
    
    # 1. รับ URL ที่ต้องการทดสอบ
    url = input("\n🔗 ใส่ URL โพสต์ที่ต้องการทดสอบ: ").strip()
    if not url:
        print("❌ ต้องใส่ URL ครับ")
        return

    ba_id = input("🆔 ใส่ BA ID (เช่น BA 7488) [กด Enter เพื่อข้าม]: ").strip() or "BA_TEST"
    
    # 2. เตรียม Folder สำหรับจดจำ (Debug)
    save_dir = os.path.join(config.BASE_RESULT_DIR, ba_id)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print("\n🔍  กำลังเริ่มการทดสอบ...")

    with sync_playwright() as p:
        try:
            # 3. เชื่อมต่อ Browser
            print("🌐 เชื่อมต่อ Chrome (9222)...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            page = browser.contexts[0].pages[0]
            page.bring_to_front()

            # 4. ไปที่ URL
            print(f"🚀 กำลังเปิดหน้าเว็บ: {url}")
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(config.DELAY_PAGE_LOAD)

            # 5. วิเคราะห์ด้วย AI (One-Shot)
            print("\n🤖  วิเคราะห์หน้าเว็บด้วย AI One-Shot...")
            temp_map = "one_shot_vision.png"
            target_coords = None
            post_context = ""

            if vision_tools.capture_target_post(page, temp_map):
                data = ai_engine.analyze_post_visually(temp_map, ba_id, url)
                if data:
                    tx, ty = data.get("target_x"), data.get("target_y")
                    post_context = data.get("cleaned_text", "")
                    if tx is not None and ty is not None:
                        target_coords = (tx, ty)
                        print(f"✅ AI ตรวจพบตำแหน่งคลิกที่: ({tx}, {ty})")
                        # วาดจุดและโชว์
                        vision_tools.mark_and_show_image(temp_map, tx, ty, duration=2)
                    else:
                        print("⚠️ AI ไม่พบตำแหน่งพิกัด (X, Y)")
                else:
                    print("❌ AI วิเคราะห์ไม่สำเร็จ")
            else:
                print("❌ แคปภาพหน้าจอไม่ได้")

            # 6. รัน Step 5 จริง
            print("\n⚙️  กำลังเรียกใช้ run_step_5...")
            success = step5.run_step_5(
                baseline_url=url,
                predefined_coords=target_coords,
                save_dir=save_dir,
                post_context=post_context
            )

            if success:
                print("\n✅  ผลลัพธ์: เข้าอัลบั้มสำเร็จ!")
            else:
                print("\n❌  ผลลัพธ์: ล้มเหลวไม่สามารถเข้าอัลบั้มได้")

        except Exception as e:
            print(f"\n💥 เกิดข้อผิดพลาด: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
