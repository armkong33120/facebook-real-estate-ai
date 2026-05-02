import os
import shutil

# Configuration
BASE_PATH = "/Users/your_username/Desktop/Facebook_Property_Data"
LINKS_FILE = "/Users/your_username/Desktop/untitled folder/uat_links.txt"
RERUN_FILE = "/Users/your_username/Desktop/untitled folder/rerun_links.txt"

def safe_cleanup():
    print("--- [1/5 Search] กำลังตรวจสอบโฟลเดอร์รูปภาพที่มีปัญหา... ---")
    failed_ids = set()
    for root, dirs, files in os.walk(BASE_PATH):
        for d in dirs:
            if d.startswith("BA "):
                folder_path = os.path.join(root, d)
                try:
                    images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
                    if len(images) < 5:
                        failed_ids.add(d)
                except:
                    continue

    print(f"พบ ID ที่มีปัญหา (< 5 รูป): {len(failed_ids)} รายการ")

    print("\n--- [2/5 Load] กำลังอ่านไฟล์ uat_links.txt... ---")
    if not os.path.exists(LINKS_FILE):
        print("ERROR: ไม่พบไฟล์ uat_links.txt ที่ระบุ")
        return

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        original_lines = [l for l in f.readlines() if l.strip()]
    
    original_count = len(original_lines)
    print(f"อ่านข้อมูลได้ทั้งหมด: {original_count} บรรทัด")

    print("\n--- [3/5 Process] กำลังคัดแยกข้อมูล... ---")
    rerun_lines = []
    clean_lines = []

    for line in original_lines:
        is_found_fail = False
        # ตรวจสอบว่าบรรทัดนี้คือ ID ที่มีปัญหาหรือไม่
        # รูปแบบบรรทัด: BA 7020 | https://...
        id_part = line.split(" |")[0].strip()
        if id_part in failed_ids:
            rerun_lines.append(line)
            is_found_fail = True
        
        if not is_found_fail:
            clean_lines.append(line)

    rerun_count = len(rerun_lines)
    clean_count = len(clean_lines)
    total_after_split = rerun_count + clean_count

    print(f"คัดแยกสำเร็จ: รวมใหม่={rerun_count}, เก็บไว้={clean_count}")
    print(f"รวมหลังแยก: {total_after_split} (เทียบกับต้นฉบับ {original_count})")

    # --- SAFETY CHECK ---
    if total_after_split != original_count:
        print("!!! WARNING: ข้อมูลไม่ตรงกัน ยกเลิกการบันทึกไฟล์เพื่อป้องกันข้อมูลสูญหาย !!!")
        return

    print("\n--- [4/5 Save] กำลังบันทึกไฟล์... ---")
    # บันทึก rerun_links.txt
    with open(RERUN_FILE, "w", encoding="utf-8") as f:
        f.writelines(rerun_lines)
    
    # อัปเดต uat_links.txt
    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        f.writelines(clean_lines)
    
    print("บันทึกไฟล์ rerun_links.txt และ uat_links.txt เรียบร้อย!")

    print("\n--- [5/5 Cleanup] กำลังลบโฟลเดอร์ที่มีปัญหาออกจาก Desktop... ---")
    deleted_count = 0
    for fid in failed_ids:
        # ลบโฟลเดอร์ในทุก Province/District
        for root, dirs, files in os.walk(BASE_PATH):
            if fid in dirs:
                target_path = os.path.join(root, fid)
                try:
                    shutil.rmtree(target_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"ไม่สามารถลบ {fid} ได้: {str(e)}")
    
    print(f"ลบโฟลเดอร์ขยะสำเร็จ: {deleted_count} โฟลเดอร์")
    print("\n✅ เสร็จสิ้นกระบวนการ Big Cleanup อย่างปลอดภัยครับ!")

if __name__ == "__main__":
    safe_cleanup()
