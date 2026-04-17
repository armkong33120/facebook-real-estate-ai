import os
import time

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def run_step_4(address_data, property_id, cleaned_text):
    """ฟังก์ชันหลักสำหรับขั้นตอนที่ 4: จัดการโฟลเดอร์เก็บข้อมูล"""
    log_message("เริ่มขั้นตอนที่ 4: กำลังจัดการโครงสร้างโฟลเดอร์...")
    
    province = address_data.get("province", "Unknown")
    district = address_data.get("district", "Unknown")
    
    # 1. กำหนดโครงสร้าง Path (Desktop -> Facebook_Data -> PROVINCE -> DISTRICT -> ID)
    base_dir = os.path.expanduser("~/Desktop/Facebook_Property_Data")
    target_dir = os.path.join(base_dir, province, district, property_id)
    
    try:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            log_message(f"สร้างโฟลเดอร์ใหม่สำเร็จ: {target_dir}")
        else:
            log_message(f"พบโฟลเดอร์เดิม: {target_dir}")
        
        # 2. บันทึกไฟล์ข้อความสรุป (cleaned_text)
        text_filename = f"{property_id}.txt"
        text_path = os.path.join(target_dir, text_filename)
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
            
        log_message(f"บันทึกไฟล์ข้อความสำเร็จ: {text_path}")
        time.sleep(3) # กิจกรรม 3 วิ
        
        return True, target_dir
        
    except Exception as e:
        log_message(f"เกิดข้อผิดพลาดในขั้นตอนที่ 4: {str(e)}")
        return False, None