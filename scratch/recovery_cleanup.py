import os

BASE_PATH = "/Users/pattharawadee/Desktop/Facebook_Property_Data"
LINKS_FILE = "/Users/pattharawadee/Desktop/untitled folder/uat_links.txt"
RERUN_FILE = "/Users/pattharawadee/Desktop/untitled folder/rerun_links.txt"
CHECKPOINT = "BA 8735"

def recovery_cleanup():
    print("--- [Recovery] เริ่มต้นกระบวนการกู้คืนรายการที่ต้องรันใหม่... ---")
    
    # 1. หาตำแหน่ง Checkpoint ในไฟล์
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        all_lines = [l for l in f.readlines() if l.strip()]
    
    print(f"จำนวนรายการต้นฉบับ: {len(all_lines)}")
    
    checkpoint_found = False
    passed_limit_index = len(all_lines)
    for i, line in enumerate(all_lines):
        if line.startswith(CHECKPOINT):
            passed_limit_index = i + 1
            checkpoint_found = True
            break
            
    if not checkpoint_found:
        print(f"คำเตือน: ไม่พบ Checkpoint {CHECKPOINT} ในไฟล์ จะตรวจสอบทั้งไฟล์แทน")

    # 2. ค้นหาโฟลเดอร์ที่มีอยู่จริงทั้งหมด
    existing_folders = {} # ID: image_count
    for root, dirs, files in os.walk(BASE_PATH):
        for d in dirs:
            if d.startswith("BA "):
                folder_path = os.path.join(root, d)
                try:
                    images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
                    existing_folders[d] = len(images)
                except:
                    continue
    
    print(f"พบโฟลเดอร์ในเครื่องทั้งหมด: {len(existing_folders)} โฟลเดอร์")

    # 3. คัดแยก
    clean_lines = []
    rerun_lines = []
    
    for i, line in enumerate(all_lines):
        id_part = line.split(" |")[0].strip()
        
        # ถ้ารายการนี้อยู่ "ก่อน" หรือ "เท่ากับ" Checkpoint (แปลว่าควรจะทำเสร็จแล้ว)
        if i < passed_limit_index:
            img_count = existing_folders.get(id_part, 0)
            if img_count < 5:
                # พ่ายแพ้! (ไม่มีโฟลเดอร์ หรือ รูปน้อย) ย้ายไป Rerun
                rerun_lines.append(line)
            else:
                # สำเร็จจริงจัง
                clean_lines.append(line)
        else:
            # รายการที่ "ยังไม่ถึงคิว" ให้เก็บไว้ใน uat_links.txt ตามปกติ
            clean_lines.append(line)

    print(f"\n--- ผลสรุป ---")
    print(f"รายการที่สำเร็จเกรด A: {len(clean_lines)}")
    print(f"รายการที่ต้องรันใหม่ (รูปน้อย/ไม่มีโฟลเดอร์): {len(rerun_lines)}")
    print(f"รวมตรวจสอบแล้ว: {len(clean_lines) + len(rerun_lines)}")

    if len(clean_lines) + len(rerun_lines) != len(all_lines):
        print("!!! ผิดพลาด: จำนวนรวมไม่ตรงกับต้นฉบับ ยกเลิกการเขียนไฟล์ !!!")
        return

    # 4. บันทึกผล
    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        f.writelines(clean_lines)
    with open(RERUN_FILE, "w", encoding="utf-8") as f:
        f.writelines(rerun_lines)
        
    print("\n✅ กู้คืนและคัดแยกข้อมูลสำเร็จ!")
    print(f"ไฟล์หลัก: {LINKS_FILE} (พร้อมรันต่อ)")
    print(f"ไฟล์ซ่อม: {RERUN_FILE} (รันซ่อม 5 รูปปังๆ)")

if __name__ == "__main__":
    recovery_cleanup()
