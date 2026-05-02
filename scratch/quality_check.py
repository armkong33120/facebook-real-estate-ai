import os

BASE_PATH = "/Users/your_username/Desktop/Facebook_Property_Data"
LINKS_FILE = "/Users/your_username/Desktop/untitled folder/rerun_links.txt"
CHECKPOINT_LINE = 292

def count_single_image_folders():
    # 1. ดึง ID จาก rerun_links.txt ถึงบรรทัดที่ 292
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[:CHECKPOINT_LINE]
    
    target_ids = [line.split(" |")[0].strip() for line in lines if " | " in line]
    print(f"กำลังตรวจสอบ {len(target_ids)} รายการที่รันไปแล้ว...")

    # 2. ค้นหาโฟลเดอร์และนับรูป
    stats = {
        "1_image": [],
        "2_4_images": [],
        "5_plus_images": [],
        "not_found": []
    }

    # สร้าง Cache ของโฟลเดอร์ที่มีอยู่จริงเพื่อความไว
    existing_folders = {} # id: folder_path
    for root, dirs, files in os.walk(BASE_PATH):
        for d in dirs:
            if d.startswith("BA "):
                existing_folders[d] = os.path.join(root, d)

    for ba_id in target_ids:
        if ba_id in existing_folders:
            folder_path = existing_folders[ba_id]
            images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
            count = len(images)
            if count == 1:
                stats["1_image"].append(ba_id)
            elif 1 < count < 5:
                stats["2_4_images"].append(ba_id)
            elif count >= 5:
                stats["5_plus_images"].append(ba_id)
            else:
                stats["not_found"].append(ba_id) # 0 images
        else:
            stats["not_found"].append(ba_id)

    print("\n--- ผลการตรวจสอบรูปภาพ ---")
    print(f"มีรูปเพียง 1 รูป: {len(stats['1_image'])} รายการ")
    print(f"มีรูป 2-4 รูป: {len(stats['2_4_images'])} รายการ")
    print(f"มีรูป 5 รูปขึ้นไป: {len(stats['5_plus_images'])} รายการ")
    print(f"ไม่พบโฟลเดอร์/ไม่มีรูป: {len(stats['not_found'])} รายการ")
    
    if stats["1_image"]:
        print(f"\nรายชื่อบางส่วนที่มีรูปเดียว: {', '.join(stats['1_image'][:10])}...")

if __name__ == "__main__":
    count_single_image_folders()
