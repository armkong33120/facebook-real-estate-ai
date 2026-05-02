import json
import time
import random
import os
from playwright.sync_api import sync_playwright

STATUS_FILE = os.path.expanduser("~/Desktop/untitled folder/status_tracker.json")


def sync_groups():
    print("🛡️ [Sync] เริ่มต้นระบบตรวจสอบกลุ่มที่เข้าร่วมแล้ว...")
    
    with sync_playwright() as p:
        try:
            # เชื่อมต่อกับ Chrome ที่พอร์ต 9292
            browser = p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            page = context.new_page()
            
            print("🌐 [Sync] กำลังไปที่หน้า Groups Join...")
            page.goto("https://www.facebook.com/groups/joins/", wait_until="networkidle")
            time.sleep(5)
            
            # ไถหน้าจอเพื่อโหลดกลุ่มทั้งหมด (ไถ 10 รอบเพื่อให้ชัวร์)
            print("🤳 [Sync] กำลังไถหน้าจอเพื่อดึงข้อมูลกลุ่มทั้งหมด...")
            for i in range(10):
                page.mouse.wheel(0, 2000)
                time.sleep(2)
            
            # ดึงทุกลิงก์ที่เกี่ยวกับกลุ่ม
            links = page.query_selector_all('a[href*="/groups/"]')
            found_links = set()
            for link in links:
                href = link.get_attribute("href")
                if "/groups/" in href:
                    # ตัดเอาแค่ส่วน ID กลุ่ม
                    # เช่น https://www.facebook.com/groups/12345/ -> 12345
                    parts = href.split("/groups/")
                    if len(parts) > 1:
                        group_id = parts[1].split("/")[0].split("?")[0]
                        if group_id and group_id.isdigit():
                            found_links.add(group_id)
            
            print(f"✅ [Sync] พบกลุ่มที่คุณเป็นสมาชิกอยู่จริง: {len(found_links)} กลุ่ม")
            
            # โหลดข้อมูลเก่ามาเทียบ
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            updated_count = 0
            for link, info in data.items():
                if not link.startswith("http"): continue
                
                # ตรวจดูว่า ID กลุ่มนี้อยู่ในกลุ่มที่พบไหม
                is_match = False
                for fid in found_links:
                    if fid in link:
                        is_match = True
                        break
                
                if is_match and info["status"] != "joined":
                    info["status"] = "joined"
                    updated_count += 1
            
            if updated_count > 0:
                with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"🎉 [Sync] อัปเดตสถานะเป็น 'เข้าร่วมแล้ว' เพิ่มเติม: {updated_count} กลุ่ม!")
            else:
                print("✨ [Sync] ข้อมูลในระบบตรงกับ Facebook แล้ว ไม่ต้องอัปเดตเพิ่มครับ")
                
            page.close()
            
        except Exception as e:
            print(f"❌ [Sync Error] เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    sync_groups()
