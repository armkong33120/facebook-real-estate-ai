import os

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(SCRIPT_DIR, "uat_links.txt")
BASE_RESULT_DIR = os.path.expanduser("~/Desktop/Facebook_Property_Data")
USER_DATA_DIR = os.path.join(SCRIPT_DIR, "fb_bot_profile")

# --- API CONFIGURATION ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY ไม่ได้ตั้งค่า!")
MODEL_NAME = "gemini-2.5-flash-lite"


# --- DISPLAY / VIEWPORT ---
VIEWPORT_WIDTH = 1440
VIEWPORT_HEIGHT = 900

# --- AGENT STEERING ---
IMAGE_RELAY_TIME = 6000 # ms
RETRY_RELAY_TIME = 4000 # ms
PAGE_LOAD_TIMEOUT = 90000 # ms
MIN_IMAGES_REQUIRED = 4

# ============================================================
# ⏱️  TIMING & DELAY CONFIGURATION (ปรับได้ที่นี่ที่เดียว)
# ============================================================

# --- [BROWSER / PAGE] ---
DELAY_BROWSER_LAUNCH     = 3.0   # รอ Browser เปิดขึ้นมา
DELAY_PAGE_LOAD          = 3.0   # รอหน้าเว็บ Render หลัง navigate
DELAY_PAGE_SETTLE        = 2.0   # รอหน้าเว็บนิ่งก่อนทำขั้นตอนถัดไป
DELAY_STEP_END           = 2.0   # หน่วงก่อนจบแต่ละ Step

# --- [NAVIGATION / CLICK] ---
DELAY_AFTER_CLICK        = 3.0   # รอหน้าใหม่โหลดหลังคลิกอัลบั้ม
DELAY_ACTIVATION_CLICK   = 0.5   # คลิก Activation ก่อนเริ่ม Scroll
DELAY_SCROLL_STEP        = 0.1   # หน่วงระหว่าง Scroll แต่ละครั้ง
DELAY_AFTER_SCROLL       = 1.5   # รอให้ Page นิ่งหลัง Scroll เสร็จ
DELAY_BACK_RECOVERY      = 2.0   # รอหลังกด Back เพื่อไปตั้งหลักใหม่
DELAY_FALLBACK_WAIT      = 1.0   # หน่วงระหว่าง Fallback แต่ละ attempt
DELAY_FALLBACK_SCROLL    = 0.2   # หน่วงระหว่าง Scroll ในโหมด Fallback

# --- [IMAGE CAPTURE / DOWNLOAD] ---
DELAY_IMAGE_STILL        = 1.0   # รอภาพนิ่งก่อนแคป (ป้องกันภาพเบลอ)
DELAY_AFTER_DOWNLOAD     = 1.0   # หน่วงหลังดาวน์โหลดรูปแต่ละใบ
DELAY_IMAGE_RENDER       = 2.0   # รอ Image Render ก่อนแคป

# --- [ARROW / SLIDESHOW] ---
DELAY_ARROW_KEY          = 0.5   # หน่วงหลังกด ArrowRight

# --- [CHASER / VISION] ---
DELAY_STABLE_BEFORE_CLICK = 0.5   # หน่วงเวลาก่อนจิ้มเมื่อเป้าหมายนิ่งแล้ว
CHASE_STABILITY_COUNT     = 8     # จำนวนครั้งที่เป้าหมายต้องนิ่ง (100ms * 8 = 0.8s)
MAX_CHASE_ATTEMPTS        = 30    # จำนวนครั้งสูงสุดในการพยายามไล่ล่า (3s)

# --- [AI / API] ---
DELAY_AI_RETRY           = 3.0   # รอก่อน Retry เมื่อ API Error 503
DELAY_AI_AUDIT           = 3.0   # หน่วงระหว่าง AI Audit (Rate Limit ~15 RPM)

# --- [BETWEEN PROPERTIES] ---
DELAY_BETWEEN_MISSIONS   = 3.0   # หน่วงระหว่างทรัพย์แต่ละชิ้น

# ============================================================
