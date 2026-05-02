import os
import shutil

base_path = "/Users/your_username/Desktop/Facebook_Property_Data"
links_file = "/Users/your_username/Desktop/untitled folder/uat_links.txt"
rerun_file = "/Users/your_username/Desktop/untitled folder/rerun_links.txt"

failed_ids = []

# 1. ระบุ ID ที่มีรูปภาพ < 5
print("--- [Scan] กำลังตรวจสอบโฟลเดอร์รูปภาพ... ---")
for root, dirs, files in os.walk(base_path):
    for d in dirs:
        if d.startswith("BA "):
            folder_path = os.path.join(root, d)
            images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
            if len(images) < 5:
                failed_ids.append(d)

print(f"พบ ID ที่มีปัญหา (< 5 รูป): {len(failed_ids)} รายการ")

if not failed_ids:
    print("ไม่พบรายการที่ต้องจัดการ สิ้นสุดการทำงาน")
    exit()

# 2. จัดการไฟล์ uat_links.txt และ create rerun_links.txt
print("--- [File] กำลังคัดแยกข้อมูลลิงก์... ---")
with open(links_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_uat_lines = []
rerun_lines = []

for line in lines:
    is_failed = False
    for fid in failed_ids:
        if line.startswith(fid + " |"):
            rerun_lines.append(line)
            is_failed = True
            break
    if not is_failed:
        new_uat_lines.append(line)

# บันทึก rerun_links.txt
with open(rerun_file, "w", encoding="utf-8") as f:
    f.writelines(rerun_lines)

# อัปเดต uat_links.txt (ลบตัวที่พังออก)
with open(links_file, "w", encoding="utf-8") as f:
    f.writelines(new_uat_lines)

print(f"บันทึก rerun_links.txt แล้ว ({len(rerun_lines)} รายการ)")
print(f"ปรับปรุง uat_links.txt แล้ว (เหลือ {len(new_uat_lines)} รายการ)")

# 3. ลบโฟลเดอร์ขยะทิ้ง
print("--- [Cleanup] กำลังลบโฟลเดอร์ที่รูปน้อย... ---")
for fid in failed_ids:
    # ค้นหาพาธของโฟลเดอร์นั้นๆ อีกครั้งเพื่อลบ
    for root, dirs, files in os.walk(base_path):
        if fid in dirs:
            target_path = os.path.join(root, fid)
            try:
                shutil.rmtree(target_path)
                print(f"ลบ {fid} สำเร็จ")
            except Exception as e:
                print(f"ลบ {fid} ไม่สำเร็จ: {str(e)}")

print("--- [Done] จัดการล้างข้อมูลเรียบร้อยแล้วครับ! ---")
