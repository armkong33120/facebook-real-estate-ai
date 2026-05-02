import os
import json
import time
import random
import re
import subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright
import google.generativeai as genai

# Import your existing browser core
import browser_core
import config

def send_sms_notification(message):
    """Sends a notification via macOS Messages app, forcing automatic send"""
    phone_number = "+66610784261"
    try:
        # Escaping double quotes in message for applescript
        message_escaped = message.replace('"', '\\"')
        
        # More robust AppleScript that targets the service to ensure automatic sending
        applescript = f'''
        tell application "Messages"
            set targetService to 1st service whose service type is iMessage
            set targetBuddy to buddy "{phone_number}" of targetService
            send "{message_escaped}" to targetBuddy
        end tell
        '''
        subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
        print(f"[SMS] Report sent to {phone_number} (Auto-send triggered)")
    except Exception as e:
        print(f"[SMS Error] {str(e)}")

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
# Use the model name from config, which the user says is 'gemini-2.5-flash-lite'
# but I'll make it resilient in case it's actually 'gemini-1.5-flash'
MODEL_NAME = config.MODEL_NAME

STATUS_FILE = "/Users/your_username/Desktop/untitled folder/status_tracker.json"
MAX_JOINS_PER_SESSION = 999

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_status(data):
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def analyze_join_status_with_ai(screenshot_path):
    """Sends screenshot to Gemini to categorize the joining status"""
    print(f"[AI] Analyzing screenshot: {screenshot_path}")
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Open the image file
        with open(screenshot_path, "rb") as f:
            image_data = f.read()
        
        prompt = """
        Look at this Facebook group membership section. 
        Categorize the CURRENT status after clicking 'Join' into ONE of these numbers:
        1: SUCCESSFULLY JOINED (The button now says 'Joined', 'Member', or 'Following'. User was accepted immediately).
        2: REQUESTED / PENDING (Request sent, waiting for admin approval. Button now says 'Requested', 'Pending', or 'Cancel Request').
        3: MUST ANSWER QUESTIONS (A popup or area asking for 'Membership Questions', 'Answer Questions', or 'Group Rules' is visible).
        
        Return ONLY the number (1, 2, or 3). If unsure, return 2.
        """
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/png", "data": image_data}
        ])
        
        result = response.text.strip()
        # Extract the first digit found in the response
        match = re.search(r"(\d)", result)
        if match:
            return match.group(1)
        return "2" # Default to requested/pending if unclear
    except Exception as e:
        print(f"[AI Error] {str(e)}")
        return "2"

def validate_api_key():
    """Checks if the API key is valid before starting the session"""
    print("[System] Validating AI API key...")
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        # Minimal request to test the key
        model.generate_content("Ping", generation_config={"max_output_tokens": 1})
        print("✅ AI Key validated successfully.")
        return True
    except Exception as e:
        print("\n" + "!"*50)
        print("❌ CRITICAL ERROR: AI API Key is invalid or expired!")
        print(f"Details: {str(e)}")
        print("Please check config.py and provide a working Gemini API key.")
        print("!"*50 + "\n")
        return False

def join_groups():
    # 0. Validate API Key first
    if not validate_api_key():
        return

    full_data = load_status()
    # Extract just the group links (ignore session_info if it exists)
    links_data = {k: v for k, v in full_data.items() if k.startswith("http")}
    
    pending_links = [link for link, info in links_data.items() if info["status"] == "pending"]
    
    if not pending_links:
        print("[System] No pending groups to join.")
        return

    # ลุยทั้งหมดที่ยังไม่เข้า (หักลบ 42 กลุ่มที่เข้าแล้วออกไปแล้วในฐานข้อมูล)
    to_process = pending_links[:MAX_JOINS_PER_SESSION]
    
    print(f"📊 สรุปยอดคงเหลือ: ยังไม่เข้า {len(pending_links)} กลุ่ม (จากทั้งหมด 919)")
    print(f"🚀 กำลังเริ่มภารกิจจัดการส่วนที่เหลือ {len(to_process)} กลุ่มในรอบนี้...")

    if not browser_core.launch_independent_browser():
        print("[Error] Failed to launch browser.")
        return

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            stats = {"total": len(to_process), "success": 0, "questions": 0, "already_done": 0, "failed": 0}
            
            # Ensure screenshot folder exists
            ss_dir = os.path.join(os.path.dirname(STATUS_FILE), "screenshots")
            os.makedirs(ss_dir, exist_ok=True)

            processed_this_session = 0
            MAX_SESSION_LIMIT = 999  # User requested to run continuously

            for index, link in enumerate(to_process):
                if processed_this_session >= MAX_SESSION_LIMIT:
                    print(f"\n[Safety] Reached session limit of {MAX_SESSION_LIMIT} groups. Stopping for safety.")
                    break

                district = full_data[link].get("district", "ทั่วไป (รวมเขต)")
                print(f"\n--- Group {index+1}/{len(to_process)} [{district}]: {link} ---")
                
                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=60000)
                    
                    # --- 1. HUMAN-LIKE SCROLLING BEFORE JOINING ---
                    print("[Human-Like] Scrolling up and down to check content...")
                    for _ in range(random.randint(2, 4)):
                        scroll_dist = random.randint(400, 800)
                        page.mouse.wheel(0, scroll_dist) # ไถลง
                        time.sleep(random.uniform(0.8, 1.5))
                        if random.random() > 0.5:
                            page.mouse.wheel(0, -random.randint(200, 400)) # ไถกลับขึ้นมานิดนึง
                            time.sleep(random.uniform(0.5, 1.0))

                    # --- 2. JOINING PHASE ---
                    
                    # Pre-check logic (using .first to avoid strict mode violations)
                    is_joined = page.get_by_text(re.compile(r"Joined|Member|เข้าร่วมแล้ว|เป็นสมาชิกแล้ว", re.IGNORECASE)).first.is_visible()
                    if is_joined:
                        msg = f"FB Bot [{district}]: Already a member.\nLeft: {len(pending_links) - (index + 1)}"
                        print(f"[Status] Already a member in {district}. Skipping.")
                        full_data[link]["status"] = "joined"
                        stats["already_done"] += 1
                        send_sms_notification(msg)
                        continue

                    is_pending = page.get_by_text(re.compile(r"Requested|Pending|ส่งคำขอแล้ว|รอการอนุมัติ", re.IGNORECASE)).first.is_visible()
                    if is_pending:
                        msg = f"FB Bot [{district}]: Already requested.\nLeft: {len(pending_links) - (index + 1)}"
                        print(f"[Status] Already requested in {district}. Skipping.")
                        full_data[link]["status"] = "requested"
                        stats["already_done"] += 1
                        send_sms_notification(msg)
                        continue

                    # Try to find and click Join button (Support Multiple Versions)
                    join_button = page.locator('div[role="button"]:has-text("Join Group"), div[role="button"]:has-text("เข้าร่วมกลุ่ม"), div[aria-label="Join Group"], div[aria-label="เข้าร่วมกลุ่ม"]').first
                    
                    if join_button.is_visible():
                        print(f"[Action] Found Join button in {district}. Clicking...")
                        join_button.click()
                        
                        # --- AI VISION PHASE ---
                        print("[System] Waiting 2 seconds for UI update...")
                        time.sleep(2)
                        
                        # Take screenshot of the top half (1440x500) to reduce tokens
                        ss_path = os.path.join(ss_dir, f"group_{index}.png")
                        page.screenshot(path=ss_path, clip={"x": 0, "y": 0, "width": 1440, "height": 500})
                        
                        category = analyze_join_status_with_ai(ss_path)
                        print(f"[AI Result] Category: {category}")
                        
                        status_msg = ""
                        if category == "1":
                            print(f"[Success] AI says: Joined Successfully in {district}!")
                            full_data[link]["status"] = "joined_successfully"
                            stats["success"] += 1
                            status_msg = "Successfully Joined! ✅"
                        elif category == "2":
                            print(f"[Success] AI says: Request Sent in {district} (Pending Admin)!")
                            full_data[link]["status"] = "requested_no_questions"
                            stats["success"] += 1
                            status_msg = "Request Sent (Pending) ⏳"
                        elif category == "3":
                            print(f"[Action] AI says: Questions Required in {district}. Attempting to Bypass...")
                            # ลองหาปุ่ม "ส่ง" หรือ "Submit" ใน Dialog (ส่งแบบว่างๆ)
                            submit_btn = page.locator('div[role="dialog"] div[role="button"]:has-text("ส่ง"), div[role="dialog"] div[role="button"]:has-text("Submit"), div[role="dialog"] div[role="button"]:has-text("ยืนยัน")').last
                            
                            if submit_btn.is_visible():
                                print("      🔘 พบปุ่มส่ง (Submit) - กำลังกดส่งแบบไม่ตอบคำถาม...")
                                submit_btn.click()
                                time.sleep(3)
                                full_data[link]["status"] = "requested_bypass_questions"
                                status_msg = "Requested (Bypassed Questions) ⚡"
                            else:
                                print("      ✖️ ไม่พบปุ่มส่ง - พยายามปิดหน้าต่างเพื่อให้ Request ยังคงอยู่...")
                                close_btn = page.locator('div[role="dialog"] div[role="button"][aria-label="ปิด"], div[role="dialog"] div[role="button"][aria-label="Close"]').first
                                if close_btn.is_visible():
                                    close_btn.click()
                                    time.sleep(2)
                                full_data[link]["status"] = "requested_closed_dialog"
                                status_msg = "Requested (Closed Dialog) 🛡️"
                            
                            stats["success"] += 1
                        else:
                            # Unexpected response
                            full_data[link]["status"] = "check_required"
                            stats["failed"] += 1
                            status_msg = "Check Required ⚠️"
                        
                        msg = f"FB Bot [{district}]: {status_msg}\nLeft: {len(pending_links) - (index + 1)}"
                        send_sms_notification(msg)
                        processed_this_session += 1
                    else:
                        msg = f"FB Bot [{district}]: Join button not found.\nLeft: {len(pending_links) - (index + 1)}"
                        print(f"[Status] Join button not found in {district}.")
                        full_data[link]["status"] = "cannot_join"
                        stats["failed"] += 1
                        send_sms_notification(msg)

                except Exception as e:
                    print(f"[Error] {str(e)}")
                    # Capture error screenshot for Audit
                    try:
                        err_ss = os.path.join(ss_dir, f"error_{index}_{datetime.now().strftime('%H%M%S')}.png")
                        page.screenshot(path=err_ss)
                        print(f"      📸 Error artifact captured: {err_ss}")
                    except: pass
                    stats["failed"] += 1
                
                # Update status
                full_data[link]["last_checked"] = datetime.now().isoformat()
                save_status(full_data)
                
                if index < len(to_process) - 1:
                    wait_time = random.uniform(20, 40)
                    print(f"[Safety Cooldown] Idling for {wait_time:.1f}s (Scrolling feed like a human)...")
                    
                    start_idle = time.time()
                    while time.time() - start_idle < wait_time:
                        # สุ่มไถฟีดแก้เหงา
                        idle_scroll = random.randint(200, 500)
                        page.mouse.wheel(0, idle_scroll)
                        # สุ่มเวลารออ่านโพสต์สั้นๆ
                        time.sleep(random.uniform(2, 5))
                        
                        # สุ่มไถขึ้นบ้างบางครั้ง
                        if random.random() > 0.7:
                            page.mouse.wheel(0, -random.randint(100, 300))
                            time.sleep(random.uniform(1, 3))
                    
                    print("   ✅ Cooldown finished.")

            print("\n" + "="*40)
            print("🚀 SESSION SUMMARY (AI-POWERED)")
            print("="*40)
            print(f"Total Groups Processed : {stats['total']}")
            print(f"✅ Joined/Requested     : {stats['success']}")
            print(f"❓ Found Questions      : {stats['questions']} (Skipped)")
            print(f"⏩ Already Member/Req   : {stats['already_done']}")
            print(f"❌ Failed/Not Found     : {stats['failed']}")
            print("="*40)
            
            generate_report(full_data)

        except Exception as e:
            print(f"[Critical Error] {str(e)}")
        finally:
            print("[System] Closing connection...")
            try:
                browser.close()
            except: pass

def generate_report(data):
    """Categorizes groups by district and saves to a summary file"""
    report_file = "/Users/your_username/Desktop/untitled folder/categorized_groups.txt"
    
    # Filter out non-link keys
    links_only = {k: v for k, v in data.items() if k.startswith("http")}
    
    # Organize by District -> Status
    districts = {}
    
    for link, info in links_only.items():
        dist = info.get("district", "ทั่วไป (รวมเขต)")
        status = info.get("status")
        
        if dist not in districts:
            districts[dist] = {"joined": [], "requested": [], "with_questions": [], "failed": []}
            
        if status in ["joined_successfully", "joined"]:
            districts[dist]["joined"].append(link)
        elif status == "requested_no_questions":
            districts[dist]["requested"].append(link)
        elif status == "requires_manual_answers":
            districts[dist]["with_questions"].append(link)
        elif status != "pending":
            districts[dist]["failed"].append(link)

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== Facebook Group Categorization Report (By District) ===\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        # Sort districts for consistent output
        sorted_districts = sorted(districts.keys())
        
        for dist in sorted_districts:
            d_info = districts[dist]
            total_in_dist = len(d_info["joined"]) + len(d_info["requested"]) + len(d_info["with_questions"]) + len(d_info["failed"])
            
            if total_in_dist == 0: continue
            
            f.write(f"📍 เขต/โซน: {dist}\n")
            f.write("-" * 30 + "\n")
            
            if d_info["with_questions"]:
                f.write(f"  [!] ต้องตอบคำถามเอง ({len(d_info['with_questions'])}):\n")
                for link in d_info["with_questions"]:
                    f.write(f"      - {link}\n")
            
            if d_info["joined"] or d_info["requested"]:
                f.write(f"  [✓] เข้าสำเร็จ/ส่งคำขอแล้ว ({len(d_info['joined']) + len(d_info['requested'])}):\n")
                for link in d_info["joined"]:
                    f.write(f"      - {link} (Joined)\n")
                for link in d_info["requested"]:
                    f.write(f"      - {link} (Requested)\n")
            
            if d_info["failed"]:
                f.write(f"  [?] อื่นๆ ({len(d_info['failed'])}):\n")
                for link in d_info["failed"]:
                    f.write(f"      - {link}\n")
            
            f.write("\n")

    print(f"[System] Categorized report (by District) saved to: {report_file}")

if __name__ == "__main__":
    try:
        join_groups()
    except KeyboardInterrupt:
        print("\n\n🛑 หยุดการทำงานโดยผู้ใช้ (Control + C)")
        print("💾 บันทึกสถานะล่าสุดเรียบร้อยแล้ว คุณสามารถรันต่อได้ทุกเมื่อครับ")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดไม่คาดคิด: {e}")
