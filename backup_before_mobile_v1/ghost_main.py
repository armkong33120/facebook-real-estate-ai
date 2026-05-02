import time
import os
import importlib.util
import subprocess
import line_tools

# ขจัดคำเตือนจุกจิก
os.environ["NODE_OPTIONS"] = "--no-deprecation"

# --- CONFIGURATION (คุณพี่ปรับแต่งตรงนี้ได้ครับ) ---
SHOW_DEBUG_VISUALS = False  # เปลี่ยนเป็น False  หากต้องการปิดการโชว์รูปเป้าเล็ง (โหมดรันจริงจัง) True = เปิด
# ---------------------------------------------

if SHOW_DEBUG_VISUALS:
    os.environ["DEBUG_VISUALS"] = "1"
else:
    os.environ["DEBUG_VISUALS"] = "0"

def log_master(msg):
    """แสดงข้อความสรุปสถานะการทำงานหลัก"""
    print(f"\n{'='*25} {msg} {'='*25}")

def load_step(file_name):
    """โหลดโมดูลจากไฟล์ .py โดยตรง"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, file_name)
    module_name = f"step_{hash(file_name) & 0xFFFF}"
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def get_checkpoint():
    """ดึง ID ล่าสุดที่ทำสำเร็จจากไฟล์"""
    file_path = "checkpoint.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def save_checkpoint(target_id):
    """บันทึก ID ล่าสุดที่สำเร็จ"""
    with open("checkpoint.txt", "w", encoding="utf-8") as f:
        f.write(target_id)

def audit_global_stats(links_file):
    """สแกนข้อมูลเก่าเพื่อหาฐานข้อมูลสถิติที่แท้จริง"""
    base_path = os.path.expanduser("~/Desktop/Facebook_Property_Data")
    
    # ดึง ID ทั้งหมดจากไฟล์ต้นทาง
    target_ids = []
    if os.path.exists(links_file):
        with open(links_file, "r", encoding="utf-8") as f:
            for line in f:
                if " | " in line:
                    target_ids.append(line.split(" | ")[0].strip())
    
    # สแกนโฟลเดอร์ที่มีอยู่จริง
    processed_ids = {}
    if os.path.exists(base_path):
        for root, dirs, files in os.walk(base_path):
            for d in dirs:
                if d.startswith("BA "):
                    folder_path = os.path.join(root, d)
                    try:
                        images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg") and f not in ["one_shot_vision.png", "vision_map.png", "temp_download.jpg"]]
                        processed_ids[d] = len(images)
                    except:
                        pass
    
    # คำนวณเบื้องต้นเฉพาะตัวที่มีในลิสต์ 492 รายการ
    global_processed = 0
    global_failed = 0
    for rid in target_ids:
        if rid in processed_ids:
            global_processed += 1
            if processed_ids[rid] < 5:
                global_failed += 1
                
    return global_processed, global_failed, processed_ids

def main():
    log_master("เริ่มภารกิจ GHOST AGENT (V36.00+) - โหมดลูปต่อเนื่อง")
    
    global_processed = 0
    global_failed = 0

    # --- ระบบกันหน้าจอล็อค (Anti-Sleep) ---
    log_master("เปิดระบบ Anti-Sleep: ป้องกันเครื่องหลับระหว่างปฏิบัติภารกิจ")
    anti_sleep = subprocess.Popen(["caffeinate", "-di"])

    try:
        links_file = "pending_links.txt"
        if not os.path.exists(links_file):
            print(f"[Error] ไม่พบไฟล์ {links_file}")
            return

        # 3. อ่านลิงก์ทั้งหมดมาเตรียมไว้ก่อน
        with open(links_file, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if l.strip() and " | " in l]
        
        total_items = len(lines)

        # ส่งแจ้งเตือนเริ่มภารกิจเข้า LINE
        line_tools.send_line_message(f"🤖 GHOST AGENT: เริ่มปฏิบัติภารกิจแล้วครับคุณพี่! ✨\n📂 ไฟล์: {links_file}\n📊 จำนวนทั้งหมด: {total_items} รายการ")

        # 1. เช็ค Checkpoint และแสดงสถานะลำดับ
        last_id = get_checkpoint()
        skip_mode = False
        start_index = 0
        
        if last_id:
            # ค้นหาว่า last_id อยู่ลำดับที่เท่าไหร่
            for i, line in enumerate(lines):
                if line.startswith(last_id):
                    start_index = i + 1
                    break
            
            print(f"\n[System] พบจุดบันทึกครั้งล่าสุดที่ ID: {last_id}")
            print(f"[Status] ทำสำเร็จไปแล้ว {start_index} จากทั้งหมด {total_items} รายการ")
            
            choice = input("ต้องการรันต่อจากจุดที่ค้างไว้หรือไม่? (y/n): ").lower()
            if choice == 'y':
                skip_mode = True
                print(f">>> จะเริ่มรันต่อจากลำดับที่ {start_index + 1}...")
            else:
                print(">>> เริ่มใหม่ตั้งแต่ต้นไฟล์")
                last_index = 0
                last_id = None # ล้างทิ้งเพื่อให้เริ่มใหม่ตั้งแต่ต้นจริงๆ

        # 2. โหลด Module ทุกขั้นตอน
        try:
            step1 = load_step("1.เปิด google chome ใส่ลิงค์.py")
            step2 = load_step("2.Copyข้อมูลในโพสส่ง ai จัดเรียงใหม่ ส่งกลับมาไว้ใน .txt .py")
            step3 = load_step("3.เอาข้อมูลใน .txt ส่งให้ AI หา จังหวัดเขตหรืออำเภอ.py")
            step4 = load_step("4.ใช้ข้อมูลที่ AI หาได้สร้างโฟลเดอและsupโฟลเดอ.py")
            step5 = load_step("5.หาคลิกรูปในอัลบั้มโพส.py")
            step6 = load_step("6.ดูดไฟล์รูป เก็บตามข้อ 4 และเช็คค่าไฟล์ hash ป้องกันการโหลดรูปซ้ำ.py")
            step7 = load_step("7.เลื่อนรูปไปทางขวามือไปเรื่อยๆถ้าค่า hash รูปในอัลบั้มยังไม่ซ้ำ.py")
        except Exception as e:
            print(f"[Error] โหลด Module ไม่สำเร็จ: {str(e)}")
            return

        # 3. อ่านลิงก์ทั้งหมด
        with open(links_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        log_master(f"พบรายการทั้งหมด {len(lines)} รายการ")
        
        # --- [NEW] คำนวณฐานข้อมูลสถิติจากประวัติเก่า ---
        print("[System] กำลังตรวจสอบสถานะงานเก่าเพื่อสรุปสถิติสะสม...")
        start_processed, global_failed, processed_ids = audit_global_stats(links_file)
        global_processed = start_processed # เริ่มต้นจากการนับไฟล์ที่มีอยู่แล้ว
        print(f"[Stats] ประวัติประมวลผลสะสม: {global_processed} | พลาดสะสม: {global_failed}")

        # เราใช้ enumerate เพื่อให้ได้ลำดับที่แน่นอน (index + 1) ป้องกันยอดเกิน 100%
        for index, line in enumerate(lines):
            if not line.strip() or " | " not in line:
                continue
                
            parts = line.split(" | ")
            TARGET_ID = parts[0].strip()
            TARGET_URL = parts[1].strip()
            
            # ตรรกะการ Resume (Skip จนกว่าจะพ้นตัวล่าสุด)
            if last_id and not skip_mode:
                if TARGET_ID == last_id:
                    skip_mode = True
                    print(f"[Checkpoint] พบจุดล่าสุด {TARGET_ID} แล้ว คับ เริ่มรันข้อถัดไป...")
                continue
            
            # ลำดับจริงคือ index + 1
            global_processed = index + 1
            
            # [NEW] ตรวจสอบว่ามีรูปอยู่แล้วหรือไม่ (ถ้ามีครบ 5 รูปถือว่าผ่านแล้ว ให้ข้าม)
            if TARGET_ID in processed_ids and processed_ids[TARGET_ID] >= 5:
                print(f"[Skip] {TARGET_ID} - พบรูปภาพเดิมแล้ว ({processed_ids[TARGET_ID]} รูป)")
                continue

            log_master(f"ภารกิจปัจจุบัน (Global): {global_processed} | ID: {TARGET_ID}")
            print(f"[Link]: {TARGET_URL}")

            try:
                # --- PHASE 1: Navigation ---
                success1, page = step1.run_step_1(TARGET_URL, TARGET_ID)
                if not success1: 
                    print(f"[Skip] {TARGET_ID} เนื่องจากเปิดหน้าเว็บไม่ได้")
                    continue

                # --- [VERSION ONE-SHOT] ---
                log_master("เข้าสู่ระบบ Vision One-Shot Analysis")
                import vision_tools, ai_engine
                temp_map = "one_shot_vision.png"
                one_shot_success = False
                cleaned_text = ""
                address_data = None
                target_coords = None

                # ถ่ายภาพและวิเคราะห์แบบรวดเดียวจบ
                if vision_tools.capture_target_post(page, temp_map):
                    data = ai_engine.analyze_post_visually(temp_map, TARGET_ID, TARGET_URL)
                    if data:
                        cleaned_text = data.get("cleaned_text", "")
                        address_data = data.get("location")
                        tx, ty = data.get("target_x"), data.get("target_y")
                        if tx is not None and ty is not None:
                            target_coords = (tx, ty)
                            # วาดเป้าหมายและโชว์ให้คุณพี่ดู 1 วิ ก่อนลบไฟล์
                            vision_tools.mark_and_show_image(temp_map, tx, ty, duration=1)
                        
                        if cleaned_text and address_data:
                            print(f"[One-Shot] AI วิเคราะห์สำเร็จ! (จังหวัด: {address_data.get('province')})")
                            one_shot_success = True
                    # ย้ายการลบ/ย้ายไฟล์ไปทำหลังจากได้ save_dir แล้ว

                if not one_shot_success:
                    print("[Fallback] One-Shot ไม่สมบูรณ์ กำลังรันระบบ Sequential เดิม...")
                    success2, cleaned_text = step2.run_step_2(TARGET_ID, TARGET_URL)
                    if not success2: 
                        print(f"[Skip] {TARGET_ID} เนื่องจาก AI คลีนข้อมูลไม่ได้")
                        continue
                    success3, address_data = step3.run_step_3(cleaned_text)
                else:
                    # ถ้า One-Shot สำเร็จ เราก็มีครบแล้ว
                    pass
                # Step 4: Folder Creation (ใช้ข้อมูลที่ได้จาก One-Shot หรือ Fallback)
                success4, save_dir = step4.run_step_4(address_data, TARGET_ID, cleaned_text)

                # [NEW] ย้ายไฟล์ One-Shot Debug ไปไว้ในโฟลเดอร์งาน
                if success4 and os.path.exists(temp_map):
                    try:
                        final_map_path = os.path.join(save_dir, temp_map)
                        if os.path.exists(final_map_path): os.remove(final_map_path)
                        os.rename(temp_map, final_map_path)
                        print(f"[Debug] ย้ายรูป One-Shot ไปที่: {final_map_path}")
                    except:
                        pass
                elif os.path.exists(temp_map):
                    os.remove(temp_map) # ลบทิ้งหากสร้างโฟลเดอร์ไม่สำเร็จ

                # --- PHASE 3: Extraction ---
                import ai_engine
                
                mission_success = False
                for retry in range(2):
                    # Step 5: Navigation (V37.00 Chaser Edition)
                    success5 = step5.run_step_5(
                        page,
                        baseline_url=TARGET_URL, 
                        predefined_coords=target_coords if (not retry) else None
                    )
                    if not success5:
                        continue

                    # Step 6: ดูดรูปแรกเพื่อให้น้อง AI ตรวจสอบ (Pre-flight Check)
                    status, img_hash = step6.run_step_6(save_dir)
                    if status == "NEW":
                        # หาไฟล์รูปล่าสุดที่เพิ่งบันทึก (ไม่ hardcode เป็น 1.jpg อีกต่อไป)
                        jpg_files = sorted([f for f in os.listdir(save_dir) if f.endswith('.jpg') and f != "temp_download.jpg"])
                        if not jpg_files:
                            print("[System] ไม่พบไฟล์รูปที่เพิ่งบันทึก")
                            continue
                        first_img_path = os.path.join(save_dir, jpg_files[-1]) # ใช้ไฟล์ล่าสุด
                        print(f"[Vision] กำลังวิเคราะห์รูปแรก {first_img_path}...")
                        
                        analysis = ai_engine.evaluate_property_relevance(first_img_path, cleaned_text)
                        score = analysis.get("confidence", 0)
                        reason = analysis.get("reason", "No reason provided")
                        
                        if score >= 70:
                            print(f"[PASSED] AI มั่นใจ {score}%: {reason}")
                            mission_success = True
                            
                            # เริ่มลูปดูดรูปที่เหลือ (2-30)
                            photo_count = 1
                            consecutive_duplicates = 0
                            while photo_count < 30:
                                if not step7.run_step_7(): break # เลื่อนไปรูปถัดไป
                                
                                status, img_hash = step6.run_step_6(save_dir)
                                if status == "NEW":
                                    photo_count += 1
                                    consecutive_duplicates = 0
                                elif status == "DUPLICATE":
                                    consecutive_duplicates += 1
                                    if consecutive_duplicates >= 2: break
                                else: 
                                    consecutive_duplicates += 1
                                    if consecutive_duplicates >= 2: break
                            break # จบ Retry Loop เพราะทำสำเร็จแล้ว
                        else:
                            print(f"[REJECTED] AI ไม่มั่นใจ (ได้แค่ {score}%): {reason}")
                            if os.path.exists(first_img_path):
                                os.remove(first_img_path)
                            print(f"[Retry] พยายามแก้ตัวรอบที่ {retry + 1}/2...")
                            # กลับไปจุดเริ่มต้นของ Loop เพื่อลอง Scroll Up แล้วคลิกใหม่
                    else:
                        print("[System] ไม่พบรูปใหม่ในจุดที่คลิก ลองใหม่อีกครั้ง...")

                if not mission_success:
                    print(f"[Final-Skip] ยอมแพ้กับ {TARGET_ID} หลังจากลองครบ 2 ครั้งแล้ว")
                    # ส่งแจ้งเตือน LINE กรณีพัง
                    global_failed += 1
                    fail_rate = (global_failed / global_processed) * 100
                    progress_rate = (global_processed / total_items) * 100
                    line_tools.send_line_message(
                        f"❌ พลาด: {TARGET_ID}\n"
                        f"🔗 ลิงก์: {TARGET_URL}\n"
                        f"❌ พลาดสะสม: {global_failed}/{global_processed} รายการ ({fail_rate:.1f}%)\n"
                        f"🏁 ความคืบหน้า: {global_processed}/{total_items} ({progress_rate:.1f}%)"
                    )
                    
                    save_checkpoint(TARGET_ID) # ขยับเพื่อข้ามไปตัวหน้า
                    continue

                # --- [NEW] ระบบจัดการไฟล์ Debug (เก็บเฉพาะตัวที่พัง) ---
                final_images = [f for f in os.listdir(save_dir) if f.lower().endswith(".jpg") and f not in ["one_shot_vision.png", "vision_map.png", "temp_download.jpg"]]
                img_count = len(final_images)
                
                if img_count >= 5:
                    # ถ้าสำเร็จ (5 รูปขึ้นไป) -> ลบรูป Debug ทิ้งเพื่อประหยัดที่
                    debug_files = ["one_shot_vision.png", "vision_map.png"]
                    for df in debug_files:
                        target_df = os.path.join(save_dir, df)
                        if os.path.exists(target_df):
                            os.remove(target_df)
                    log_master(f"จบภารกิจ {TARGET_ID} - สำเร็จรุ่งเรือง (ได้รูป {img_count} รูป, ลบไฟล์ Debug แล้ว)")
                else:
                    # ถ้าได้รูปน้อย -> นับเป็นพลาดในสถิติด้วยตามคำขอคุณพี่
                    failed_count += 1
                    log_master(f"จบภารกิจ {TARGET_ID} - สำเร็จแต่รูปน้อย ({img_count} รูป, ก็นับเป็นพลาดสะสม)")

                if img_count < 5:
                    global_failed += 1
                
                fail_rate = (global_failed / global_processed) * 100
                progress_rate = (global_processed / total_items) * 100
                
                # กำหนดข้อความและไอคอนตามคุณภาพรูป (5 รูปคือเกณฑ์ผ่าน)
                if img_count >= 5:
                    icon = "✅"
                    status_text = "ผ่าน"
                else:
                    icon = "❌"
                    status_text = "พลาด"
                
                line_tools.send_line_message(
                    f"{icon} {status_text}: {TARGET_ID}\n"
                    f"🔗 ลิงก์: {TARGET_URL}\n"
                    f"❌ พลาดสะสม: {global_failed}/{global_processed} รายการ ({fail_rate:.1f}%)\n"
                    f"🏁 ความคืบหน้า: {global_processed}/{total_items} ({progress_rate:.1f}%)"
                )

                # บันทึก Checkpoint เมื่อทำสำเร็จ (หรือจบกระบวนการ)
                save_checkpoint(TARGET_ID)
                time.sleep(5)

            except Exception as e:
                print(f"[รอบ Error] เกิดข้อผิดพลาดกับ {TARGET_ID}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

    finally:
        if 'anti_sleep' in locals():
            anti_sleep.terminate()
            log_master("ปิดระบบ Anti-Sleep เรียบร้อย")

    log_master("สิ้นสุดการรันลูปภารกิจทั้งหมด!")
    final_fail_rate = (global_failed / global_processed) * 100 if global_processed > 0 else 0
    line_tools.send_line_message(
        f"🏁 ภารกิจเสร็จสิ้นทั้งหมดแล้วครับคุณพี่!\n"
        f"✅ สำเร็จสะสม: {max(0, global_processed - global_failed)} รายการ\n"
        f"❌ พลาดสะสม: {global_failed} รายการ ({final_fail_rate:.1f}%)\n"
        f"✨ ขอบคุณที่ใช้บริการ GHOST AGENT ครับ"
    )

if __name__ == "__main__":
    main()
