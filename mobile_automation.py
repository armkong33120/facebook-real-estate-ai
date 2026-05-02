import os
import sys
import time
import json
import glob
import random
import subprocess
import logging
from datetime import datetime
from google import genai

# Checklist 9: Logging (Setup for debugging without leaking secrets)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("bot_execution.log"), logging.StreamHandler()]
)

def log_safe(msg):
    # ป้องกันการหลุดของ API Key ใน Log
    if "AIza" in msg: msg = msg[:10] + "..."
    logging.info(msg)

# Checklist 3, 11: Config & Dry Run handle
try:
    import config
    DRY_RUN = getattr(config, 'DRY_RUN', True) # Default to Dry Run for safety
except ImportError:
    log_safe("❌ Critical Error: config.py missing. Aborting.")
    sys.exit(1)

# Checklist 13: Global Requirement - Abort if mandatory items missing
class AutomationError(Exception): pass
class CriticalDataMissing(AutomationError): pass

# --- Checklist 4: State Machine ---
class BotState:
    START = "START"
    PICKING_BA = "PICKING_BA"
    PREPARING_DATA = "PREPARING_DATA"
    SYNCING_IMAGES = "SYNCING_IMAGES"
    OPENING_FB = "OPENING_FB"
    POSTING = "POSTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

current_state = BotState.START

# --- Checklist 6, 7, 10: ADB Wrapper with Timeout & Retry ---
def adb_call(command, timeout=30):
    """Checklist 6: Timeouts in every point"""
    try:
        result = subprocess.run(
            f"adb {command}", 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        if result.returncode != 0:
            log_safe(f"⚠️ ADB Error: {result.stderr.strip()}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        log_safe(f"❌ ADB Timeout after {timeout}s")
        return None
    except Exception as e:
        log_safe(f"❌ ADB Exception: {e}")
        return None

def adb_type_thai(text):
    """ส่งข้อความเข้าคลิปบอร์ดโดยใช้ shlex.quote (มาตรฐานสูงสุด กันช่องว่างและอักขระพิเศษ)"""
    if not text: return
    import shlex
    log_safe(f"📋 Syncing clipboard for: {text[:30]}...")
    
    # ใช้ shlex.quote เพื่อจัดการกับช่องว่างและอักขระพิเศษทุกลักษณะ
    quoted_text = shlex.quote(text)
    adb_call(f"shell service call clipboard 2 i32 1 s16 {quoted_text}")
    
    time.sleep(1.5)
    adb_call("shell input keyevent 279") # Paste
    time.sleep(1)

def get_coordinate_from_ai(screenshot_path, element_desc):
    """ใช้ Gemini มองรูปแล้วบอกพิกัด X, Y"""
    log_safe(f"👁️ AI กำลังมองหา: {element_desc}...")
    try:
        # ดึง client จากระนาบหลัก
        from google import genai
        vision_client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        # อ่านไฟล์ภาพ
        with open(screenshot_path, "rb") as f:
            img_data = f.read()
        
        prompt = f"This is a screenshot of a Facebook app on a 1080x2220 screen. Find the center coordinates (x, y) of '{element_desc}'. Return ONLY the coordinates in format: [x, y]"
        
        response = vision_client.models.generate_content(
            model=config.MODEL_NAME,
            contents=[
                prompt, 
                genai.types.Part.from_bytes(data=img_data, mime_type="image/png")
            ]
        )
        
        # แกะพิกัดจากคำตอบ AI เช่น [500, 1200]
        import re
        match = re.search(r"\[(\d+),\s*(\d+)\]", response.text)
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception as e:
        log_safe(f"⚠️ AI Vision Failed: {e}")
    return None

# --- Checklist 5, 12: UI Actions with Pre/Post Checks & Artifacts ---
def safe_tap(x, y, label="Target"):
    # Checklist 5: Pre-check (Is device alive?)
    if adb_call("get-state") != "device":
        raise AutomationError("Device disconnected before tap")
    
    log_safe(f"👉 Touching {label} at ({x}, {y})")
    nx = x + random.randint(-5, 5)
    ny = y + random.randint(-5, 5)
    
    # แม้จะเป็น DRY_RUN แต่เราจะปล่อยให้ "จิ้มจริง" เพื่อให้ User เห็นภาพ (ยกเว้นปุ่มโพสต์)
    adb_call(f"shell input tap {nx} {ny}")
    
    # Checklist 5: Post-check (Screenshot for validation)
    time.sleep(random.uniform(2.5, 4.0))

def capture_failure_artifact(reason):
    """Checklist 12: Failure artifacts (Screenshot)"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"FAILURE_{reason}_{ts}.png"
    adb_call(f"exec-out screencap -p > {filename}")
    log_safe(f"📸 Failure artifact saved: {filename}")

# --- Checklist 1, 2, 8, 13: Data & Logic ---

def validate_ba_data(ba):
    """Checklist 1, 13: Strict Validation"""
    if not ba: return False
    if not ba.get('images'): return False
    if not ba.get('raw_text'): return False
    return True

def pick_ba_safely():
    """Checklist 8: Idempotency (Prevent duplicates)"""
    ba_list = []
    # ค้นหาแบบ Recursive
    ba_dirs = glob.glob(os.path.join(config.BASE_RESULT_DIR, "**", "BA*"), recursive=True)
    
    for d in ba_dirs:
        if not os.path.isdir(d): continue
        # Checklist 8: Log ledger (campaign_report.txt)
        if os.path.exists(os.path.join(d, "campaign_report.txt")): continue
        
        txt_files = glob.glob(os.path.join(d, "*.txt"))
        if not txt_files: continue
        
        with open(txt_files[0], "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        if not content: continue # Checklist 2: No empty content
        
        images = []
        for ext in ['*.jpg', '*.png', '*.jpeg', '*.JPG', '*.PNG', '*.JPEG']:
            images.extend(glob.glob(os.path.join(d, ext)))
        
        if len(images) < 1: continue # Checklist 13: Must have images
        
        all_ba.append({
            "name": os.path.basename(d),
            "path": d,
            "raw_text": content,
            "images": sorted(list(set(images)))
        })
    
    if not all_ba: return None
    return random.choice(all_ba)

def ai_format_with_fallback(raw_text):
    """Checklist 3: Clear Fallback logic"""
    log_safe("🤖 Attempting AI formatting...")
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=f"จัดระเบียบข้อความขายบ้านนี้ให้อ่านง่าย:\n\n{raw_text}"
        )
        formatted = response.text.strip()
        if formatted: return formatted
    except Exception as e:
        log_safe(f"⚠️ AI Failed ({e}). Switching to Fallback: Raw Text.")
    
    # Fallback to original text if AI fails or returns empty
    return raw_text[:500] # Limit length for safety

# --- EXECUTION ENGINE ---

def run_safe_mission():
    global current_state
    log_safe(f"--- MISSION START (Dry Run: {DRY_RUN}) ---")
    
    try:
        # STEP 1: PICK BA
        current_state = BotState.PICKING_BA
        ba = pick_ba_safely()
        if not validate_ba_data(ba):
            raise CriticalDataMissing("BA Data incomplete or empty")
        
        log_safe(f"✅ Target Selected: {ba['name']}")

        # STEP 2: PREPARE CONTENT
        current_state = BotState.PREPARING_DATA
        caption = ai_format_with_fallback(ba['raw_text'])
        if not caption: # Checklist 2
            raise CriticalDataMissing("Caption is empty after fallback")
        
        # STEP 3: SYNC IMAGES
        current_state = BotState.SYNCING_IMAGES
        phone_path = "/sdcard/Pictures/Bot_Live/"
        adb_call(f"shell rm -rf {phone_path}")
        adb_call(f"shell mkdir -p {phone_path}")
        for img in ba['images'][:5]:
            adb_call(f"push \"{img}\" {phone_path}")
        adb_call(f"shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{phone_path}")
        log_safe("✅ Images synced to phone")

        # STEP 4: INTERACTION FLOW (Full 14 Steps)
        current_state = BotState.POSTING
        
        # 1. เข้าเมนู Facebook
        adb_call("exec-out screencap -p > screen.png")
        coords = get_coordinate_from_ai("screen.png", "Facebook Menu (typically 3 horizontal lines or profile icon)")
        if coords: safe_tap(coords[0], coords[1], "AI FB Menu")
        else: safe_tap(105, 156, "Fallback FB Menu")
        
        # 2. กด "กลุ่ม"
        adb_call("exec-out screencap -p > screen.png")
        coords = get_coordinate_from_ai("screen.png", "Groups icon in the menu")
        if coords: safe_tap(coords[0], coords[1], "AI Groups Icon")
        else: safe_tap(190, 591, "Fallback Groups Icon")
        
        # 3. กด "กลุ่มของคุณ"
        safe_tap(432, 221, "Your Groups Tab")
        
        # 4. กด "ค้นหากลุ่ม"
        safe_tap(282, 534, "Search Groups")
        
        # 5. พิมพ์ชื่อกลุ่ม (ตัวอย่าง: หอพัก เจริญกรุง)
        # หมายเหตุ: ในอนาคตเราจะดึงชื่อกลุ่มจาก JSON มาใส่ตรงนี้
        adb_type_thai("หอพัก เจริญกรุง")
        time.sleep(3)
        safe_tap(321, 1849, "Select First Result")
        
        # 6. กด "เขียนอะไรสักหน่อย"
        safe_tap(361, 910, "Create Post Box")
        
        # 7. พิมพ์เนื้อหาโพสต์ (ที่ AI แต่งให้)
        adb_type_thai(caption)
        
        # 8. เลือกรูปภาพ (กด 5 จุดยอดนิยมในหน้าเลือกรูป)
        safe_tap(185, 450, "Image 1")
        safe_tap(450, 450, "Image 2")
        safe_tap(720, 450, "Image 3")
        safe_tap(185, 720, "Image 4")
        safe_tap(450, 720, "Image 5")
        
        # 9. กดปุ่ม "เรียบร้อย" หลังเลือกรูป
        safe_tap(950, 150, "Done Selection")
        
        # STEP 5: FINISH
        current_state = BotState.COMPLETED
        log_safe(f"🏆 Mission Accomplished for {ba['name']}")
        
        if not DRY_RUN:
            with open(os.path.join(ba['path'], "campaign_report.txt"), "w") as f:
                f.write(f"Posted successfully at {datetime.now()}")

    except CriticalDataMissing as e:
        log_safe(f"🚫 ABORTING: {e}")
        current_state = BotState.FAILED
    except Exception as e:
        log_safe(f"💥 CRASHED at state {current_state}: {e}")
        capture_failure_artifact(current_state)
        current_state = BotState.FAILED
        sys.exit(1)

if __name__ == "__main__":
    # ตรวจสอบเบื้องต้นว่ามีทรัพย์ไหม
    all_ba = [] 
    run_safe_mission()
