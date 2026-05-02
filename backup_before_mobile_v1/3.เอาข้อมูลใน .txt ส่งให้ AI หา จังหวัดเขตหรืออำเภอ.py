import time
import ai_engine

def log_message(msg):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {msg}")

def run_step_3(cleaned_text):
    """ฟังก์ชันหลักสำหรับขั้นตอนที่ 3: วิเคราะห์หาที่อยู่จากข้อความที่คลีนแล้ว"""
    log_message("เริ่มขั้นตอนที่ 3: กำลังวิเคราะห์หา จังหวัด และ เขต/อำเภอ...")
    
    # ส่งข้อความให้ AI วิเคราะห์
    address_data = ai_engine.parse_address(cleaned_text)
    
    province = address_data.get("province", "Unknown")
    district = address_data.get("district", "Unknown")
    
    log_message(f"AI วิเคราะห์สำเร็จ: จังหวัด = {province}, เขต/อำเภอ = {district}")
    time.sleep(3) # กิจกรรม 3 วิ
    
    return True, address_data