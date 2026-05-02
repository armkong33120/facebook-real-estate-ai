import asyncio
import os
import glob
import random
import subprocess
import time
import json
from datetime import datetime
from playwright.async_api import async_playwright, Error
import google.generativeai as genai
from config import * 
import re
from PIL import Image

# --- [NEW] ระบบ Audit Log - บันทึกทุกคำสั่งที่ส่งหา Chrome ---
def audit_log(action, details):
    log_file = "chrome_automation_audit.log"
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] ACTION: {action} | DETAILS: {details}\n")

# --- [CORE LOGGING] ---
def mission_log(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("mission_analysis.log", "a", encoding="utf-8") as f:
            f.write(f"[{now}] {message}\n")
    except: pass

def log_to_csv(ba_id, district, groups_count, hw_model, success=True):
    """บันทึกข้อมูลลงไฟล์ CSV เพื่อใช้ตรวจสอบ"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "daily_posting_log.csv"
    status = "SUCCESS" if success else "FAILED"
    line = f'"{now}","{ba_id}","{district}","{groups_count}","{hw_model}","{status}"\n'
    file_exists = os.path.exists(log_file)
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write("Timestamp,BA_ID,District,Groups_Ticked,Hardware,Status\n")
            f.write(line)
    except: pass

# --- ระบบ Stable Master (Concise iMessage) ---
genai.configure(api_key=GEMINI_API_KEY)

# --- [DYNAMIC PATHS] ---
DISTRICTS = ["ยานนาวา", "สาทร", "บางคอแหลม", "บางรัก", "คลองเตย", "คลองสาน", "ปทุมวัน", "จตุจักร", "ห้วยขวาง", "ราชเทวี", "พญาไท"]
DATA_ROOTS = [os.path.join(BASE_RESULT_DIR, "กรุงเทพมหานคร", d) for d in DISTRICTS]

NEIGHBOR_FILE = os.path.join(SCRIPT_DIR, "neighboring_districts.txt")
RECEIVER = "+66 6-1078-4261"

# --- ฟังก์ชันจำลองพฤติกรรมมนุษย์ ---

async def highlight_element(page, locator_or_selector):
    """ฟังก์ชันวาดกรอบสีแดงรอบธาตุที่บอทกำลังจะจัดการ (เพื่อการ Debug)"""
    try:
        if isinstance(locator_or_selector, str):
            locator = page.locator(locator_or_selector).first
        else:
            locator = locator_or_selector
        await locator.evaluate("el => { el.style.border = '5px solid red'; el.style.backgroundColor = 'rgba(255,0,0,0.3)'; el.style.zIndex = '9999'; }")
        await asyncio.sleep(0.5)
        await locator.evaluate("el => { el.style.border = ''; el.style.backgroundColor = ''; }")
    except: pass

async def simulate_human_scroll(page, duration_sec, scroll_step_min=200, scroll_step_max=600, pause_min=2.0, pause_max=3.0):
    start_time = time.time()
    while time.time() - start_time < duration_sec:
        scroll_amount = random.randint(scroll_step_min, scroll_step_max)
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(random.uniform(pause_min, pause_max))

async def simulate_reel_interaction(page, duration_sec):
    start_time = time.time()
    while time.time() - start_time < duration_sec:
        scroll_amount = random.randint(100, 500)
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(random.uniform(2, 3.5))
        await page.keyboard.press("ArrowDown")
        await asyncio.sleep(1.5)

async def run_warmup_sequence(page):
    print("🚶 เริ่มระบบวอร์มอัพเดินเล่น (Warmup Mode)...")
    
    feed_time = random.randint(6, 9)
    print(f"   - กำลังเดินเล่นหน้า Feed หลัก (สุ่ม {feed_time} วิ, หยุดดู 2-3 วิ, ระยะ 200-600px)...")
    await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    await simulate_human_scroll(page, feed_time)
    
    if random.choice([True, False]):
        reel_time = random.randint(6, 9)
        print(f"   - กำลังดู Reels (สุ่ม {reel_time} วิ)...")
        await page.goto("https://www.facebook.com/reel/", wait_until="domcontentloaded")
        await simulate_reel_interaction(page, reel_time)
    else:
        mp_time = random.randint(6, 10)
        print(f"   - กำลังดู Marketplace (สุ่ม {mp_time} วิ, หยุดดู 3-4 วิ, ระยะ 200-600px)...")
        await page.goto("https://www.facebook.com/marketplace/?ref=bookmark", wait_until="domcontentloaded")
        await simulate_human_scroll(page, mp_time, scroll_step_min=200, scroll_step_max=600, pause_min=3.0, pause_max=4.0)
    
    await page.goto("https://www.facebook.com/")
    await asyncio.sleep(1.5)
    
    group_feed_time = random.randint(6, 9)
    print(f"   - กำลังเช็คฟีดกลุ่ม (สุ่ม {group_feed_time} วิ, หยุดดู 2-3 วิ, ระยะ 200-600px)...")
    await page.goto("https://www.facebook.com/groups/feed/", wait_until="domcontentloaded")
    await simulate_human_scroll(page, group_feed_time)
    
    joined_time = random.randint(6, 9)
    print(f"   - กำลังดูรายการกลุ่มที่เข้าร่วม (สุ่ม {joined_time} วิ, หยุดดู 2-3 วิ, ระยะ 200-600px)...")
    await page.goto("https://www.facebook.com/groups/joins/?nav_source=tab&ordering=viewer_added", wait_until="domcontentloaded")
    await simulate_human_scroll(page, joined_time)
    
    await page.keyboard.press("Escape")
    await asyncio.sleep(1.5)
    print("✅ จบการวอร์มอัพ เข้าสู่ภารกิจหลัก")


# ============================================================
# 🛡️ ANTI-DETECTION SYSTEMS (Stealth Layer)
# ============================================================

def weighted_random_tick_count():
    """สุ่มจำนวนกลุ่มที่จะติ๊ก 0-9 ตามน้ำหนักที่กำหนดใน config"""
    choices = list(GROUP_TICK_WEIGHTS.keys())
    weights = list(GROUP_TICK_WEIGHTS.values())
    return random.choices(choices, weights=weights, k=1)[0]

async def human_delay(min_sec=1, max_sec=3):
    """หน่วงเวลาแบบสุ่ม — เลียนแบบมนุษย์หยุดคิดระหว่างพิมพ์"""
    await asyncio.sleep(random.uniform(min_sec, max_sec))

def randomize_emojis(text):
    """สุ่มตัดอิโมจิออกบางตัวเพื่อไม่ให้ซ้ำแพทเทิร์น (keep 70%)"""
    import re as _re
    def emoji_replacer(match):
        return match.group(0) if random.random() < 0.7 else ""
    emoji_pattern = r'[^\x00-\x7F\u0E00-\u0E7F\s]'
    return _re.sub(emoji_pattern, emoji_replacer, text)

def truncate_50_percent(text):
    """ตัดข้อความเหลือ ~50% แบบสุ่ม (ตัดหน้า หรือ ตัดหลัง) — เลียนแบบคนขี้เกียจพิมพ์เต็ม"""
    if len(text) <= 20:
        return text  # สั้นเกินไป ไม่ต้องตัด
    cut_style = random.choice(["front", "back"])
    keep_ratio = random.uniform(0.4, 0.6)  # เก็บ 40-60%
    cut_point = max(10, int(len(text) * keep_ratio))
    
    if cut_style == "front":
        # ตัดครึ่งหน้า — เริ่มจากกลางข้อความ
        result = text[cut_point:]
    else:
        # ตัดครึ่งหลัง
        result = text[:cut_point]
    
    # ตัดให้จบประโยคสวยๆ (ตัดหลังอักขระเว้นวรรค, ขึ้นบรรทัดใหม่, หรือมหัพภาค)
    for sep in ['\n', '. ', ' ', ', ']:
        idx = result.rfind(sep)
        if idx > len(result) * 0.7:
            result = result[:idx + len(sep)]
            break
    
    return result.strip() or text[:30]  # fallback

async def human_type(page, selector_or_element, text, speed_wpm=45):
    """พิมพ์เนื้อหา — จำลองการพิมพ์แบบคนจริงๆ 100% (Gaussian Delay, Word pauses, Typos)"""
    if isinstance(selector_or_element, str):
        element = page.locator(selector_or_element).first
    else:
        element = selector_or_element
    
    # รอให้ Element พร้อม
    try:
        await element.wait_for(state="visible", timeout=5000)
    except: pass
    
    await element.click(force=True)
    await human_delay(0.3, 0.8)
    
    # สุ่มใส่อิโมจิ หรือ ไม่ใส่อิโมจิ เพื่อไม่ให้เกิดแพทเทิร์นตายตัว
    import re as _re
    emoji_pattern = r'[^\x00-\x7F\u0E00-\u0E7F\s]'
    
    if random.choice([True, False]):
        action = random.choice(["strip_all", "strip_70"])
        if action == "strip_all":
            varied_text = _re.sub(emoji_pattern, "", text)
            print("      🛡️ [STEALTH] สุ่มปิดการใส่อิโมจิทั้งหมด", flush=True)
        else:
            def emoji_remover(match):
                return match.group(0) if random.random() < 0.3 else ""
            varied_text = _re.sub(emoji_pattern, emoji_remover, text)
            print("      🛡️ [STEALTH] สุ่มตัดอิโมจิบางส่วนออก (เหลือ 30%)", flush=True)
    else:
        varied_text = text
        print("      🛡️ [STEALTH] คงอิโมจิไว้ทั้งหมด", flush=True)

    audit_log("Human_Type_Exact", f"Typing exact text of {len(varied_text)} characters.")
    print(f"      ✍️ [TEXT] กำลังกรอกข้อความความยาว {len(varied_text)} ตัวอักษร (Gaussian typing mode)...", flush=True)
    
    mean_speed = 0.054  # เฉลี่ย 54ms ต่อตัวอักษร (ช้าลง 20%)
    std_dev = 0.018    # ค่าเบี่ยงเบนความถี่
    
    for char in varied_text:
        # สุ่มจังหวะนิ้วตก (Gaussian)
        delay = max(0.01, random.gauss(mean_speed, std_dev))
        
        # จังหวะพักสายตา (Pause after space/newline)
        if char in [' ', '\n']:
            delay += random.uniform(0.08, 0.15)
        elif char in ['!', '?', '.', ',']:
            delay += random.uniform(0.12, 0.25)

        # โอกาสพิมพ์ผิดและลบแก้ (1%)
        if random.random() < 0.01:
            # พิมพ์ตัวผิดไป 1 ตัว
            typo_char = random.choice("กขคงจฉชabc")
            await page.keyboard.type(typo_char, delay=int(delay * 1000))
            await asyncio.sleep(random.uniform(0.15, 0.3))
            await page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.08, 0.15))

        # พิมพ์ตัวอักษรจริง
        await page.keyboard.type(char, delay=int(delay * 1000))
            
    await human_delay(0.5, 1.0)




def bypass_image_hash(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        pixels = img.load()
        x, y = random.randint(0, img.width-1), random.randint(0, img.height-1)
        r, g, b = pixels[x, y]
        pixels[x, y] = (max(0, r-1), g, b)
        temp_dir = "temp_upload"
        if not os.path.exists(temp_dir): os.makedirs(temp_dir)
        temp_name = f"mod_{os.path.basename(image_path)}"
        temp_path = os.path.join(temp_dir, temp_name)
        img.save(temp_path, "JPEG", quality=95)
        return os.path.abspath(temp_path)
    except: return os.path.abspath(image_path)

def launch_chrome(profile_id=1):
    print(f"🌐 กำลังเรียกใช้ Chrome Profile {profile_id} (Port 9292)...")
    subprocess.Popen(["python3", "browser_core.py", str(profile_id)], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL,
                     start_new_session=True)
    time.sleep(5)

def send_imessage(receiver, message):
    clean_number = receiver.replace(" ", "").replace("-", "")
    safe_msg = message.replace('"', '\\"')
    apple_script = f'''
    tell application "Messages"
        try
            set targetService to 1st service whose service type is iMessage
            set targetBuddy to buddy "{clean_number}" of targetService
            send "{safe_msg}" to targetBuddy
        end try
    end tell
    '''
    subprocess.run(['osascript', '-e', apple_script])

async def ai_format_post(raw_text):
    print(f"🤖 AI ({MODEL_NAME}) กำลังจัดข้อความให้สวยงาม...")
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = f"จัดระเบียบข้อความนี้ให้อ่านง่าย ใส่ Bullet points และ Emoji (ห้ามเพิ่มเนื้อหา ห้ามแต่งเรื่อง):\n\n{raw_text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return raw_text

def pick_diverse_bas(count=10):
    all_ba = []
    total_found = 0
    skipped_finished = 0
    skipped_no_images = 0
    img_exts = ['*.jpg', '*.JPG', '*.png', '*.PNG', '*.jpeg', '*.JPEG']
    for root in DATA_ROOTS:
        if not os.path.exists(root): continue
        dist = os.path.basename(root)
        dirs = [d for d in glob.glob(os.path.join(root, "BA*")) if os.path.isdir(d)]
        total_found += len(dirs)
        for d in dirs:
            if os.path.exists(os.path.join(d, "campaign_report.txt")):
                skipped_finished += 1; continue
            ba_name = os.path.basename(d)
            images = []
            for ext in img_exts: images.extend(glob.glob(os.path.join(d, ext)))
            if not images:
                skipped_no_images += 1; continue
            all_ba.append({"name": ba_name, "path": d, "district": dist, "images": sorted(list(set(images)))})
    print(f"📊 สรุปการค้นหาทรัพย์: พบทั้งหมด {total_found} | ข้าม(ทำแล้ว) {skipped_finished} | ข้าม(ไม่มีรูป) {skipped_no_images} | พร้อมใช้งาน {len(all_ba)}")
    random.shuffle(all_ba)
    return all_ba[:count]

def load_all_groups():
    path = os.path.join(os.path.dirname(__file__), "group_analysis.json")
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def load_hardware_specs():
    path = os.path.join(os.path.dirname(__file__), "hardware_specs.json")
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def pick_groups_pool(district, all_groups, count=80):
    search_districts = get_search_districts(district)
    selected = []
    seen_links = set()
    for d in search_districts:
        for link, info in all_groups.items():
            if len(selected) >= count: break
            if link in seen_links: continue
            name = info.get("name", "").strip()
            if d in name:
                selected.append({"link": link, "name": name})
                seen_links.add(link)
    return selected

def get_search_districts(district):
    search_order = [district]
    if not os.path.exists(NEIGHBOR_FILE): return search_order
    with open(NEIGHBOR_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                parts = line.split(":", 1)
                d = parts[0].strip().split(".", 1)[-1].strip()
                if d == district:
                    neighbors = [n.strip() for n in parts[1].split(",")]
                    for n in neighbors:
                        n = n.replace("อ.", "").strip()
                        if "(" in n: n = n.split("(")[0].strip()
                        if n: search_order.append(n)
                    break
    return search_order

total_search_failures = 0

async def search_and_tick_groups(page, group_pool):
    """ค้นหาและติ๊กกลุ่มในหน้าต่าง Add Groups (Playwright Native API อย่างเดียว - ไม่ใช้ JS evaluate ในการคลิก)"""
    total_selected = 0
    ticked_info = []
    audit_log("Search_Box_Find_Attempt", "Looking for search input inside dialog using Python API...")
    
    # 1. หาช่องค้นหา — ใช้ Playwright locator หา input ใน dialog โดยตรง
    search_box = None
    # รอก่อนให้ dialog/popup เรนเดอร์เสร็จ
    await asyncio.sleep(2.0)
    
    # ลองหาช่องค้นหาใน dialog ด้วย locator
    for _ in range(6):
        try:
            # หา input ที่อยู่ใน dialog และกว้างพอ (ไม่ใช่ hidden input)
            sb = page.locator('div[role="dialog"] input[type="search"], div[role="dialog"] input[type="text"]').first
            if await sb.count() > 0:
                # เช็คขนาดว่ากว้างพอ
                box = await sb.bounding_box()
                if box and box['width'] > 100:
                    search_box = sb
                    break
        except: pass
        
        # fallback: หา input ไหนก็ได้ที่มี placeholder คำว่า "ค้นหา"
        try:
            sb = page.locator('input[placeholder*="ค้นหา"], input[placeholder*="Search"]').first
            if await sb.count() > 0:
                search_box = sb
                break
        except: pass
        
        await asyncio.sleep(0.8)
    
    if not search_box:
        print("      ❌ หาช่องค้นหาใน popup ไม่เจอเลย (ลอง 6 รอบ)")
        try: await page.screenshot(path=os.path.join(SCRIPT_DIR, "debug_no_search_box.png"))
        except: pass
        return 0, []
    
    print(f"      🔍 พบช่องค้นหาแล้ว เริ่มติ๊กกลุ่ม...")
    
    target_count = weighted_random_tick_count()
    print(f"      🎲 สุ่มติ๊ก {target_count} กลุ่ม (weighted random 0-9)", flush=True)
    
    for item in group_pool:
        if total_selected >= target_count:
            break
        
        name = item["name"]
        if not name: continue
        
        try:
            print(f"  🔎 ค้นหา: {name[:30]}...")
            audit_log("Search_And_Tick", f"Searching group: {name}")
            
            # ย่อขนาดข้อความ 45-60% ของความยาวทั้งหมด แบบเริ่มจากด้านหน้าหรือด้านหลัง แบบสุ่ม 50/50
            keep_ratio = random.uniform(0.45, 0.60)
            keep_len = max(1, int(len(name) * keep_ratio))
            
            if random.choice([True, False]):
                short_name = name[:keep_len]
            else:
                short_name = name[-keep_len:]

            print(f"  🔎 ค้นหา (แบบย่อ): {short_name}...")
            audit_log("Search_And_Tick_Short", f"Searching group (short): {short_name} for full name: {name}")
            
            # ล้างช่องค้นหาเก่า
            await search_box.click(force=True)
            await asyncio.sleep(0.2)
            await search_box.fill("")       # ล้างก่อน
            await asyncio.sleep(0.2)
            
            # พิมพ์ทีละตัวพร้อม Smart Typos (4%)
            for char in short_name:
                # โอกาสพิมพ์ผิดและลบแก้ (4%)
                if random.random() < 0.04:
                    typo_char = random.choice("กขคงจฉชabc")
                    await page.keyboard.type(typo_char, delay=random.randint(48, 96))
                    await asyncio.sleep(random.uniform(0.15, 0.3))
                    await page.keyboard.press("Backspace")
                    await asyncio.sleep(random.uniform(0.08, 0.15))
                
                await page.keyboard.type(char, delay=random.randint(48, 96))

            
            print("     ⏳ รอผลลัพธ์โหลด...")
            await asyncio.sleep(2.5)  # รอ Facebook โหลดผลลัพธ์
            
            # 2. ใช้ Playwright Locator หาแถวผลลัพธ์ (li[role="option"])
            rows = page.locator('div[role="dialog"] li[role="option"]')
            row_count = await rows.count()
            found_match = False
            
            if row_count > 0:
                # วนลูปทีละแถว ถ้าชื่อตรง → กด click() ด้วย Playwright (trigger React event จริง)
                for i in range(row_count):
                    try:
                        row = rows.nth(i)
                        row_text = await row.inner_text()
                        # เทียบชื่อกลุ่ม ให้ยืดหยุ่นที่สุด
                        if name in row_text or short_name in row_text or name[:8] in row_text:
                            # กดคลิกแถวนั้นด้วย Playwright (จะติ๊ก checkbox + trigger event ให้ Facebook รับรู้)
                            await row.click(force=True)
                            await asyncio.sleep(0.5)
                            total_selected += 1
                            ticked_info.append(item)
                            found_match = True
                            audit_log("Tick_Success", f"Group: {name} | Row {i+1}/{row_count}")
                            print(f"      ✅ ติ๊กแล้ว ({total_selected}/{target_count}): {name[:30]}...")
                            break
                    except Exception as e:
                        continue
            
            if not found_match:
                # Fallback: ลองหา checkbox ตรงๆ แล้วคลิก
                try:
                    checkboxes = page.locator('div[role="dialog"] input[type="checkbox"]')
                    cb_count = await checkboxes.count()
                    for i in range(cb_count):
                        cb = checkboxes.nth(i)
                        if await cb.is_checked(): continue
                        # เช็ค parent row ว่ามีชื่อกลุ่มตรงไหม
                        parent_row = cb.locator('xpath=ancestor::li[@role="option"]')
                        if await parent_row.count() > 0:
                            pt = await parent_row.first.inner_text()
                            if name in pt or short_name in pt or name[:8] in pt:
                                await cb.check(force=True)
                                await asyncio.sleep(0.4)
                                total_selected += 1
                                ticked_info.append(item)
                                found_match = True
                                audit_log("Tick_Success_Fallback", f"Group: {name} via checkbox.check()")
                                print(f"      ✅ ติ๊กแล้ว (fallback) ({total_selected}/{target_count}): {name[:30]}...")
                                break
                except: pass
            
            if not found_match:
                print(f"      ❌ ไม่พบ: {name[:30]}...")
                global total_search_failures
                total_search_failures += 1
                if total_search_failures > 10:
                    raise RuntimeError("🛑 [STOP] หาไม่เจอเกิน 10 รอบแล้ว หยุดทำงานทันทีเพื่อความปลอดภัย")
            else:
                total_search_failures = 0
            
            await asyncio.sleep(random.uniform(0.8, 1.5))
            
        except Exception as e:
            print(f"      ⚠️ Error: {e}")
            continue
    
    return total_selected, ticked_info

async def apply_stealth_script(context, hw):
    vendor = hw.get("gpu_vendor", "Intel Inc.")
    renderer = hw.get("gpu_renderer", "Intel(R) Iris(TM) Plus Graphics 640")
    cores = hw.get("cores", 4); memory = hw.get("memory", 8)
    res = hw.get("screen_res", "1920x1080")
    try:
        w, h = [int(x) for x in res.split("x")]
    except:
        w, h = 1920, 1080

    major_v = 148
    build_v = f"{major_v}.0.{random.randint(7700, 7800)}.{random.randint(90, 110)}"
    ua_platform = "Macintosh; Intel Mac OS X 10_15_7"
    new_ua = f"Mozilla/5.0 ({ua_platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{build_v} Safari/537.36"
    
    stealth_js = f"""
    (() => {{
        Object.defineProperty(navigator, 'userAgent', {{ get: () => '{new_ua}' }});
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {cores} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {memory} }});
        
        // --- [SPOOF SCREEN RESOLUTION] ---
        Object.defineProperty(window.screen, 'width', {{ get: () => {w} }});
        Object.defineProperty(window.screen, 'height', {{ get: () => {h} }});
        Object.defineProperty(window.screen, 'availWidth', {{ get: () => {w} }});
        Object.defineProperty(window.screen, 'availHeight', {{ get: () => {h} }});
        Object.defineProperty(window, 'innerWidth', {{ get: () => {w} }});
        Object.defineProperty(window, 'innerHeight', {{ get: () => {h} }});

        // --- [SPOOF WEBGL GPU] ---
        const getParam = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{vendor}';
            if (parameter === 37446) return '{renderer}';
            return getParam.apply(this, arguments);
        }};
    }})();
    """
    await context.add_init_script(stealth_js)
    try:
        target_page = context.pages[0]
        session = await target_page.context.new_cdp_session(target_page)
        await session.send("Network.setUserAgentOverride", {"userAgent": new_ua})
        # ปรับขนาดหน้าต่าง (Viewport) ของ Playwright ให้ตรงกัน
        for page in context.pages:
            await page.set_viewport_size({"width": w, "height": h})
    except: pass

async def test_full_post_with_groups():
    launch_chrome()
    hw_profiles = load_hardware_specs()
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            
            # --- [TAB MANAGEMENT] ปิดแท็บที่เกินมาเพื่อให้เหลือแท็บเดียวเสมอ ---
            while len(context.pages) > 1:
                await context.pages[-1].close()
                
            page = context.pages[0] if context.pages else await context.new_page()
            current_hw = random.choice(hw_profiles) if hw_profiles else {}
            await apply_stealth_script(context, current_hw)
        except Exception as e:
            print(f"❌ เชื่อมต่อไม่ได้: {e}"); return
        
        stop_requested = False
        def monitor_input():
            nonlocal stop_requested
            input("\n[!] กด Enter เพื่อหยุด\n")
            stop_requested = True
        import threading
        threading.Thread(target=monitor_input, daemon=True).start()

        ba_list = pick_diverse_bas(30)
        
        overall_group_count = 0  # นับรวมทุกกลุ่มที่โพสต์แล้ว
        
        for ba_idx, ba_data in enumerate(ba_list):
            if stop_requested: break
            
            ba_name = ba_data["name"]; district = ba_data["district"]; images = ba_data["images"]
            ba_path = ba_data["path"]
            
            # อ่านข้อความจากไฟล์ .txt ล่วงหน้า (BA นี้ใช้ข้อความเดียวตลอด)
            txt_files = [f for f in glob.glob(os.path.join(ba_path, "*.txt"))
                         if "campaign_report" not in f and "processed_hashes" not in f]
            raw_text = ""
            if txt_files:
                with open(txt_files[0], "r", encoding="utf-8") as f:
                    raw_text = f.read()
            if not raw_text:
                raw_text = f"ประกาศขายทรัพย์: {ba_name}"
            post_content = await ai_format_post(raw_text)
            
            # เตรียมรูปทั้งหมด
            processed_images = [bypass_image_hash(img) for img in images] if images else []
            
            # โหลดกลุ่มก่อน print
            all_groups_data = load_all_groups()
            group_pool = pick_groups_pool(district, all_groups_data)
            
            print(f"\n🌟 === เริ่มภารกิจ BA: {ba_name} ({district}) [{len(group_pool)} กลุ่มรอ] ===")
            
            if not group_pool:
                print("   ❌ ไม่มีกลุ่มสำหรับเขตนี้")
                continue
            
            is_first_post = True
            is_first_warmup = True
            ba_group_count = 0
            # --- [GROUP LOOP] วนกลุ่มทีละกลุ่ม เปิด tab ใหม่ทุกครั้ง ---
            for g_idx, candidate in enumerate(group_pool):
                if stop_requested: break
                if ba_group_count >= TOTAL_GROUP_TARGET: break
                
                print(f"   📊 [DEBUG REPORT] BA: {ba_name} | ผลรวมกลุ่มที่สำเร็จแล้วใน BA นี้: {ba_group_count} กลุ่ม", flush=True)
                # สุ่มเปลี่ยนตัวตน 40% / 60% ไม่เปลี่ยน (บังคับเปลี่ยนในครั้งแรกสุด)
                if is_first_post or random.random() < 0.40:
                    current_hw = random.choice(hw_profiles) if hw_profiles else {}
                    await apply_stealth_script(context, current_hw)
                    print(f"   🛡️ [STEALTH] {'บังคับเปลี่ยนตัวตนแรกสุด' if is_first_post else 'สุ่มเปลี่ยนตัวตนใหม่ (40% chance)'} -> HW: {current_hw.get('notebook_model', 'PC')}")
                    is_first_post = False
                else:
                    print("   🛡️ [STEALTH] สุ่มได้ไม่เปลี่ยนตัวตน (60% chance) -> ใช้ตัวตนเดิม")

                hw_model = current_hw.get("notebook_model", "Unknown")
                gpu = current_hw.get("gpu_renderer", "Unknown")
                cores = current_hw.get("cores", 4)
                memory = current_hw.get("memory", 8)
                res = current_hw.get("screen_res", "1920x1080")
                print(f"   🛡️ [STEALTH STATUS] HW: {hw_model} | GPU: {gpu[:35]} | Core: {cores} | RAM: {memory}GB | Screen: {res}")
                print(f"   🛡️ [STEALTH STATUS] Warmup: {'✅' if ENABLE_WARMUP else '❌'} | ImgBypass: {'✅' if ENABLE_IMAGE_UPLOAD else '❌'} | NavOverride: ✅ | Anti-Automation Flag: ✅")
                print(f"   🛡️ [STEALTH STATUS] Type: Truncate~50% ✅ | EmojiRand ✅ | Typo2% ✅ | HumanDelay ✅")

                link = candidate['link']
                group_name = candidate['name']
                
                print(f"\n   🌐 [{overall_group_count+1}/{TOTAL_GROUP_TARGET}] กำลังเข้ากลุ่ม: {group_name[:30]}...")
                
                # เปิด tab ใหม่
                try:
                    page = await context.new_page()
                except Exception:
                    print("      ❌ ไม่สามารถเปิด tab ใหม่ได้")
                    break
                
                # [STEALTH] สุ่มวอร์มอัพ 100% ของทุกๆ โพสต์/แท็บใหม่
                print("   🛡️ [STEALTH] กำลังเริ่มสุ่มวอร์มอัพเดินเล่น...")
                try:
                    # สุ่มเลือกโหมดวอร์มอัพ 1-2 โหมดจากที่มีทั้งหมด
                    warmup_options = [
                        "feed",
                        "reels_or_marketplace",
                        "group_feed",
                        "joined_groups"
                    ]
                    # สุ่มหยิบมา 1-2 อย่างเพื่อให้พฤติกรรมไม่ซ้ำซาก
                    selected_warmups = random.sample(warmup_options, k=random.randint(1, 2))
                    
                    for w_mode in selected_warmups:
                        if w_mode == "feed":
                            feed_time = random.randint(6, 9)
                            print(f"   - กำลังเดินเล่นหน้า Feed หลัก (สุ่ม {feed_time} วิ, หยุดดู 2-3 วิ, ระยะ 200-600px)...")
                            await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
                            await simulate_human_scroll(page, feed_time)
                        
                        elif w_mode == "reels_or_marketplace":
                            if random.choice([True, False]):
                                reel_time = random.randint(6, 9)
                                print(f"   - กำลังดู Reels (สุ่ม {reel_time} วิ)...")
                                await page.goto("https://www.facebook.com/reel/", wait_until="domcontentloaded")
                                await simulate_reel_interaction(page, reel_time)
                            else:
                                mp_time = random.randint(6, 10)
                                print(f"   - กำลังดู Marketplace (สุ่ม {mp_time} วิ, หยุดดู 3-4 วิ, ระยะ 200-600px)...")
                                await page.goto("https://www.facebook.com/marketplace/?ref=bookmark", wait_until="domcontentloaded")
                                await simulate_human_scroll(page, mp_time, scroll_step_min=200, scroll_step_max=600, pause_min=3.0, pause_max=4.0)
                        
                        elif w_mode == "group_feed":
                            group_feed_time = random.randint(6, 9)
                            print(f"   - กำลังเช็คฟีดกลุ่ม (สุ่ม {group_feed_time} วิ, หยุดดู 2-3 วิ, ระยะ 200-600px)...")
                            await page.goto("https://www.facebook.com/groups/feed/", wait_until="domcontentloaded")
                            await simulate_human_scroll(page, group_feed_time)
                        
                        elif w_mode == "joined_groups":
                            joined_time = random.randint(6, 9)
                            print(f"   - กำลังดูรายการกลุ่มที่เข้าร่วม (สุ่ม {joined_time} วิ, หยุดดู 2-3 วิ, ระยะ 200-600px)...")
                            await page.goto("https://www.facebook.com/groups/joins/?nav_source=tab&ordering=viewer_added", wait_until="domcontentloaded")
                            await simulate_human_scroll(page, joined_time)

                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1.0)
                    print("   - นำทางกลับมาหน้าหลัก (Home) ก่อนเข้ากลุ่ม...")
                    await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
                    await asyncio.sleep(1.5)
                except Exception as we:
                    print(f"   ⚠️ วอร์มอัพติดขัด: {we}")

                ticked_count = 0
                try:
                    await page.goto(link, wait_until="domcontentloaded", timeout=45000)
                    await human_delay(3, 5)
                    
                    # หาจุดเริ่มโพสต์
                    trigger = page.get_by_text(re.compile(r"เขียนอะไรสักหน่อย|เขียนอะไร|Write something", re.I)).first
                    if await trigger.count() == 0:
                        # fallback selectors
                        for sel in ['div[role="button"]:has-text("เขียนอะไร")', 'div[aria-label*="สร้างโพสต์"]']:
                            try:
                                t = page.locator(sel).first
                                if await t.is_visible(timeout=2000):
                                    trigger = t; break
                            except: continue
                    
                    if await trigger.count() == 0:
                        print("      ⚠️ ไม่พบปุ่มสร้างโพสต์ ข้าม (tab ค้าง)...")
                        continue
                    
                    await highlight_element(page, trigger)
                    await trigger.click()
                    await human_delay(1, 2)
                    
                    # รอ dialog
                    dialog = page.locator('div[role="dialog"]').filter(has=page.locator('div[role="textbox"], [contenteditable="true"]')).first
                    try:
                        await dialog.wait_for(state="visible", timeout=10000)
                    except:
                        print("      ⚠️ Dialog ไม่เปิด ข้าม (tab ค้าง)...")
                        await page.keyboard.press("Escape")
                        continue
                    
                    await human_delay(0.8, 1.5)
                    
                    # ล็อกโฟกัส textbox
                    textbox = dialog.locator('div[role="textbox"], [contenteditable="true"]').first
                    if await textbox.count() > 0:
                        await textbox.click(force=True)
                        await human_delay(0.2, 0.5)
                        await textbox.click(force=True)
                    
                    # 3. พิมพ์ข้อความ
                    if ENABLE_TEXT_POSTING and post_content:
                        print("      ✍️ พิมพ์เนื้อหา...")
                        try:
                            await human_type(page, textbox, post_content)
                            print("      ✅ พิมพ์ข้อความเรียบร้อย")
                        except Exception as te:
                            print(f"      ⚠️ พิมพ์ล้มเหลว: {te}")
                    
                    # 4. อัปโหลดรูป
                    if ENABLE_IMAGE_UPLOAD and processed_images:
                        print(f"      📸 อัปโหลดรูป {len(processed_images)} ใบ...")
                        try:
                            fi = page.locator('div[role="dialog"] input[type="file"]').first
                            if await fi.count() == 0:
                                fi = page.locator('input[type="file"]').first
                            if await fi.count() > 0:
                                await fi.set_input_files(processed_images)
                                await human_delay(4, 6)
                                print(f"      ✅ อัปโหลดรูปเรียบร้อย")
                        except Exception as ie:
                            print(f"      ⚠️ อัปโหลดล้มเหลว: {ie}")
                    
                    # 5. ติ๊กกลุ่มเพิ่ม — หา "เพิ่มกลุ่ม" ใน dialog แล้วค้นหา+ติ๊ก
                    if ENABLE_GROUP_TICKING:
                        # เลือกกลุ่มอื่นจาก group_pool ที่เหลือ (ข้ามตัวเอง)
                        remaining = [g for j, g in enumerate(group_pool) if j != g_idx]
                        if remaining:
                            # สุ่มตามน้ำหนัก — ได้ 0-9 กลุ่ม
                            random_tick_count = weighted_random_tick_count()
                            others = remaining[:random_tick_count] if random_tick_count > 0 else []
                            if random_tick_count == 0:
                                print(f"      🎲 สุ่มได้ 0 กลุ่ม — ข้ามการติ๊ก", flush=True)
                            else:
                                print(f"      🔍 กำลังติ๊กกลุ่มเพิ่มอีก {len(others)} กลุ่ม (สุ่มได้ {random_tick_count})...")
                            
                            add_btn = None
                            for txt in ["เพิ่มกลุ่ม", "Add groups", "+ เพิ่มกลุ่ม", "+ Add groups"]:
                                try:
                                    btn = dialog.get_by_text(txt).first
                                    if await btn.count() > 0:
                                        add_btn = btn; break
                                except: continue
                            
                            if not add_btn:
                                try:
                                    xp = page.locator("xpath=//*[contains(text(), 'เพิ่มกลุ่ม')]").first
                                    if await xp.count() > 0: add_btn = xp
                                except: pass
                            
                            if add_btn:
                                await add_btn.click(force=True)
                                await human_delay(2, 4)
                                ticked_count, _ = await search_and_tick_groups(page, others)
                                
                                # หาปุ่ม "เรียบร้อย" เฉพาะใน popup เลือกกลุ่ม (ไม่ใช่หน้าเว็บหลัก)
                                done_btn = page.locator('div[role="dialog"] div[role="button"]:has-text("เรียบร้อย"), div[role="dialog"] span:has-text("เรียบร้อย")').last
                                if await done_btn.count() > 0:
                                    await done_btn.click(force=True)
                                    await human_delay(0.5, 1.0)
                                    print(f"      ✅ ติ๊กเพิ่มสำเร็จ {ticked_count} กลุ่ม (popup ปิดแล้ว)")
                                else:
                                    # กด Escape แค่ 1 ครั้ง ปิดเฉพาะ popup กลุ่ม
                                    await page.keyboard.press("Escape")
                                    await human_delay(0.5, 1.0)
                                    print(f"      ✅ ติ๊กเพิ่มสำเร็จ {ticked_count} กลุ่ม (Escape popup)")
                            else:
                                print("      ⚠️ ไม่พบปุ่ม 'เพิ่มกลุ่ม'")
                    
                    # 6. จบ flow — ไม่ต้องปิด dialog (tab ค้างไว้ให้ user เห็นทุกอย่าง)
                    ba_group_count += (1 + ticked_count)
                    overall_group_count += (1 + ticked_count)
                    print(f"      ✅ เพิ่มอีก {1 + ticked_count} กลุ่ม (รวมของ BA {ba_name} ตอนนี้: {ba_group_count}/{TOTAL_GROUP_TARGET}) (dialog ค้าง ✅)", flush=True)
                    
                    if DEBUG_MODE:
                        print("\n✨ DEBUG_MODE: ทำงานครบ 1 รอบตามเป้าหมายแล้ว")
                        stop_requested = True
                        break
                    
                except Exception as e:
                    print(f"      ❌ ผิดพลาด: {e} (tab ค้างไว้)", flush=True)
                    try: await page.keyboard.press("Escape")
                    except: pass
                
                await human_delay(1, 3)
            
            # --- [END OF BA] ---
            print(f"\n🎯 BA {ba_name} เสร็จสิ้น (รวม {ba_group_count}/{TOTAL_GROUP_TARGET} กลุ่มสำหรับ BA นี้)")
            log_to_csv(ba_name, district, ba_group_count, current_hw.get("notebook_model", "PC"))
            
            if ba_group_count >= TOTAL_GROUP_TARGET:
                print(f"\n🏁 ครบ {TOTAL_GROUP_TARGET} กลุ่มสำหรับ BA {ba_name} แล้ว! กำลังไปทำ BA ถัดไป", flush=True)
            
            # ปิดแท็บที่เกินมาเพื่อให้เหลือแท็บเดียวเสมอสำหรับ BA ถัดไป
            print(f"   🧹 ปิดแท็บเดิมทั้งหมด เหลือไว้แท็บเดียวสำหรับ BA ถัดไป...")
            while len(context.pages) > 1:
                try:
                    await context.pages[-1].close()
                except: break
            
            print(f"   🔄 เปลี่ยน BA ถัดไป...", flush=True)
            await human_delay(2, 4)

if __name__ == "__main__":
    asyncio.run(test_full_post_with_groups())
