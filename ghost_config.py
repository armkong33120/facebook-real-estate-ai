import os

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(SCRIPT_DIR, "uat_links.txt")
# ย้ายโฟลเดอร์เก็บข้อมูลไปไว้ที่หน้าจอ (Desktop) ตามที่คุณกวงต้องการ
BASE_RESULT_DIR = os.path.expanduser("~/Desktop/Facebook_Property_Data")
USER_DATA_DIR = os.path.join(SCRIPT_DIR, "fb_bot_profile")
LOG_FILE = os.path.join(SCRIPT_DIR, "ghost_history.log") # <--- ไฟล์เก็บประวัติการทำงาน
CHECKPOINT_FILE = os.path.join(SCRIPT_DIR, "ghost_checkpoint.json") # <--- ไฟล์จำตำแหน่งงานล่าสุด

# --- API CONFIGURATION ---
# หมายเหตุ: กรุณาวาง API Key ใหม่ที่นี่หากตัวเดิมโดนแบน
GEMINI_API_KEY = "AIzaSyAol8k4kUxUAg_8TbsqqmhTXMoBm8CYhOM"
MODEL_NAME = "gemini-2.5-flash-lite"

# --- AGENT STEERING ---
IMAGE_RELAY_TIME = 6000 # ms
RETRY_RELAY_TIME = 4000 # ms
PAGE_LOAD_TIMEOUT = 90000 # ms
MAX_IMAGES_PER_POST = 50
MIN_IMAGES_REQUIRED = 4 # <--- จำนวนรูปขั้นต่ำที่ต้องได้
