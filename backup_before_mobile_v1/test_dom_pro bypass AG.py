import os, sys, glob, json, subprocess, time, asyncio, random, re, hashlib
import google.generativeai as genai
import config
from playwright.async_api import async_playwright
from datetime import datetime

# --- ระบบ Stealth Bypass AG (Extreme Privacy Edition) ---
genai.configure(api_key=config.GEMINI_API_KEY)
MODEL_NAME = config.MODEL_NAME

DATA_ROOTS = [
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/คลองสาน",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ปทุมวัน",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/จตุจักร",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ห้วยขวาง",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ราชเทวี",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/พญาไท"
]
NEIGHBOR_FILE = "/Users/your_username/Desktop/untitled folder/neighboring_districts.txt"
RECEIVER = "+66 6-1078-4261"
ENABLE_POST = 1         # 1 = โพสต์จริง, 0 = ทดสอบ
ENABLE_ADD_GROUPS = 0  # 1 = เปิดระบบเลือกกลุ่มเพิ่ม (เสี่ยงกว่า), 0 = ปิด (โพสต์ทีละลิงก์ - ปลอดภัยสุด)

# --- ฟังก์ชัน Bypass & Stealth ---

def modify_image_hash(image_path):
    """เปลี่ยนค่า Hash ของรูปภาพโดยไม่ทำให้เสียคุณภาพ (Append random bytes)"""
    try:
        with open(image_path, "ab") as f:
            f.write(os.urandom(8)) # เพิ่มข้อมูลสุ่ม 8 byte ที่ท้ายไฟล์
        return True
    except: return False

async def human_type(page, selector_or_locator, text, speed_wpm=45):
    """พิมพ์แบบเนียนกว่าเดิม มีจังหวะหยุดหายใจ"""
    if isinstance(selector_or_locator, str):
        element = page.locator(selector_or_locator).first
    else:
        element = selector_or_locator
    await element.click()
    
    base_delay = 60 / (speed_wpm * 5)
    lines = text.split('\n')
    for line_idx, line in enumerate(lines):
        for char in line:
            await page.keyboard.type(char, delay=random.uniform(base_delay*0.4, base_delay*1.8))
            if random.random() > 0.97: # สุ่มพิมพ์ผิดบ่อยขึ้นนิดนึง
                await page.keyboard.type(random.choice("กขค"), delay=120)
                await asyncio.sleep(0.4)
                await page.keyboard.press("Backspace")
        
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(0.5, 1.2))
        if line_idx % 2 == 0: # หยุดพักสายตาทุก 2 บรรทัด
            await asyncio.sleep(random.uniform(2, 4))

async def human_click(page, selector):
    element = page.locator(selector).first
    box = await element.bounding_box()
    if box:
        await page.mouse.move(
            box['x'] + box['width'] * random.uniform(0.2, 0.8),
            box['y'] + box['height'] * random.uniform(0.2, 0.8),
            steps=random.randint(15, 30)
        )
        await asyncio.sleep(random.uniform(0.3, 0.6))
        await page.mouse.click(
            box['x'] + box['width'] * random.uniform(0.2, 0.8),
            box['y'] + box['height'] * random.uniform(0.2, 0.8)
        )

# --- แกนกลางระบบ ---

def pick_one_ba():
    all_valid_bas = []
    for root in DATA_ROOTS:
        folders = [f for f in glob.glob(os.path.join(root, "*")) if os.path.isdir(f)]
        for f in folders:
            if not os.path.exists(os.path.join(f, "campaign_report.txt")):
                imgs = glob.glob(os.path.join(f, "*.jpg")) + glob.glob(os.path.join(f, "*.png"))
                if len(imgs) >= 3:
                    all_valid_bas.append(f)
    
    if not all_valid_bas: return None
    chosen = random.choice(all_valid_bas)
    return chosen

async def post_one_by_one():
    print("\n" + "="*60)
    print("🛡️  SYSTEM: BYPASS AG DEEP DEBUG MODE ACTIVATED")
    print("="*60)
    
    # 1. โหลดข้อมูลกลุ่มทั้งหมด
    print(f"🔍 [1/5] Loading group database...")
    with open("group_analysis.json", "r") as f:
        all_group_data = json.load(f)
    print(f"   ✅ Found {len(all_group_data)} total groups in database.")
    
    # 2. คัดเลือก 20 BA
    print(f"🔍 [2/5] Scanning for pending BA folders...")
    all_valid_bas = []
    for root in DATA_ROOTS:
        folders = [f for f in glob.glob(os.path.join(root, "*")) if os.path.isdir(f)]
        for f in folders:
            if not os.path.exists(os.path.join(f, "campaign_report.txt")):
                imgs = glob.glob(os.path.join(f, "*.jpg")) + glob.glob(os.path.join(f, "*.png"))
                if len(imgs) >= 3:
                    all_valid_bas.append(f)
    
    selected_bas = all_valid_bas[:20]
    if not selected_bas:
        print("❌ ERROR: No pending BA folders found!")
        return

    print(f"   ✅ Selected {len(selected_bas)} BA folders for this session.")

    async with async_playwright() as p:
        print(f"🔗 [3/5] Connecting to Chrome on Port 9292...")
        browser = await p.chromium.connect_over_cdp("http://localhost:9292")
        context = browser.contexts[0]
        print(f"   ✅ Connection established.")

        for ba_idx, ba_path in enumerate(selected_bas):
            ba_name = os.path.basename(ba_path)
            parent_path = os.path.dirname(ba_path)
            district_name = os.path.basename(parent_path)
            
            print(f"\n" + "-"*50)
            print(f"📦 MISSION BA {ba_idx+1}/20: {ba_name}")
            print(f"📍 TARGET DISTRICT: {district_name}")
            print("-"*50)

            # Matching Logic Debug
            print(f"🔍 [Matching] Analyzing groups for '{district_name}'...")
            matched_groups = []
            for g_link, g_info in all_group_data.items():
                g_text = (g_info.get("name", "") + g_info.get("rules", "")).lower()
                if district_name.lower() in g_text:
                    matched_groups.append(g_link)
            
            print(f"   🎯 Found {len(matched_groups)} groups exactly matching '{district_name}'")
            if len(matched_groups) < 40:
                needed = 40 - len(matched_groups)
                print(f"   ➕ Adding {needed} general groups to reach target of 40...")
                others = [k for k in all_group_data.keys() if k not in matched_groups]
                random.shuffle(others)
                matched_groups.extend(others[:needed])
            
            target_groups = matched_groups[:40]
            random.shuffle(target_groups)
            print(f"   ✅ Target set: 40 groups ready.")

            # Image Hash Debug
            images = glob.glob(os.path.join(ba_path, "*.jpg")) + glob.glob(os.path.join(ba_path, "*.png"))
            print(f"🖼️ [Images] Modifying hashes for {len(images)} files...")
            for img in images:
                if modify_image_hash(img):
                    print(f"   ⚡ Hash changed: {os.path.basename(img)}")

            # Content Prepare Debug
            print(f"📝 [Content] Generating AI post description...")
            txt_files = glob.glob(os.path.join(ba_path, "*.txt"))
            raw_content = ""
            if txt_files:
                with open(txt_files[0], "r", encoding="utf-8") as f: raw_content = f.read()
            
            model = genai.GenerativeModel(MODEL_NAME)
            prompt = f"จัดระเบียบข้อความขายอสังหาฯ เขต {district_name} นี้ให้น่าอ่าน (ใส่ emoji สุ่มๆ): \n\n{raw_content}"
            response = model.generate_content(prompt)
            post_content = response.text
            print(f"   ✅ AI content ready ({len(post_content)} chars)")

            # Loop Groups Debug
            for g_idx, group_link in enumerate(target_groups):
                print(f"\n👉 [Group {g_idx+1}/40] Processing: {group_link}")
                
                try:
                    page = await context.new_page()
                    v_w, v_h = random.randint(1280, 1440), random.randint(800, 900)
                    print(f"   🖥️ Viewport set to {v_w}x{v_h} (Fingerprint Bypass)")
                    await page.set_viewport_size({"width": v_w, "height": v_h})
                    
                    print(f"   🌐 Navigating to group...")
                    await page.goto(group_link, wait_until="domcontentloaded")
                    
                    # --- 1. ส่องกลุ่มก่อนโพสต์ ---
                    scroll_count = random.randint(2, 4)
                    print(f"   🤳 [Pre-Post Scroll] Starting {scroll_count} scrolls (10-20s goal)...")
                    for s in range(scroll_count):
                        dist = random.randint(300, 600)
                        wait = random.uniform(2, 4)
                        print(f"      - Scroll {s+1}: Moving down {dist}px, waiting {wait:.1f}s")
                        await page.mouse.wheel(0, dist)
                        await asyncio.sleep(wait)
                    await page.mouse.wheel(0, -2000)
                    await asyncio.sleep(2)
                    
                    print(f"   🖱️ Searching for 'Create Post' button...")
                    # เพิ่ม Selector ให้ครอบคลุมหลายแบบ
                    trigger = page.locator('div[role="button"]:has-text("สร้างโพสต์สาธารณะ"), div[role="button"]:has-text("เขียนอะไรสักหน่อย"), div[role="link"]:has-text("เขียนอะไรบางอย่าง"), div[aria-label="สร้างโพสต์สาธารณะ"]').first
                    
                    if await trigger.is_visible():
                        await trigger.click()
                        print(f"      ✅ Dialog opened.")
                        await asyncio.sleep(3)
                        
                        print(f"   ⌨️ [Stealth Typing] Starting human-like typing...")
                        await human_type(page, 'div[role="dialog"] div[role="textbox"]', post_content)
                        
                        print(f"   📁 [Upload] Selecting {min(8, len(images))} images...")
                        fi = await page.query_selector('div[role="dialog"] input[type="file"]')
                        if fi:
                            await fi.set_input_files(images[:8])
                            await asyncio.sleep(6)

                        if ENABLE_POST == 1:
                            print(f"   🚀 [Action] CLICKING POST BUTTON!")
                            post_btn = page.locator('div[role="button"]:has-text("โพสต์")').last
                            await post_btn.click()
                            print(f"      ✅ Post submitted successfully!")
                            with open(os.path.join(ba_path, "campaign_report.txt"), "a", encoding="utf-8") as f:
                                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Posted to: {group_link}\n")
                        else:
                            print("   ⚠️ [Action] DRY RUN: Post button NOT clicked.")

                        # --- 2. ส่องกลุ่มหลังโพสต์ (20-30 วิ) ---
                        # โพสต์เสร็จแล้ว ไถดูหน้ากลุ่มต่อเหมือนคนเช็คผลงาน
                        mid_scroll_count = random.randint(3, 5)
                        print(f"   🤳 [Post-Post Scroll] Browsing group feed for 20-30s...")
                        for ms in range(mid_scroll_count):
                            dist = random.randint(400, 700)
                            wait = random.uniform(4, 6)
                            print(f"      - Scroll {ms+1}: Moving down {dist}px, waiting {wait:.1f}s")
                            await page.mouse.wheel(0, dist)
                            await asyncio.sleep(wait)
                        await page.mouse.wheel(0, -3000)
                        await asyncio.sleep(2)
                    else:
                        print("   ⚠️ [Skip] Create Post button not found (Private group or Not a member).")
                    
                    await page.close()
                    
                    # Cooldown Debug
                    wait_time = random.uniform(20, 40)
                    print(f"😴 [Cooldown] Waiting {wait_time:.1f}s before next group...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    print(f"   ❌ FATAL ERROR in Group Loop: {e}")
                    # Capture error screenshot for Audit
                    try:
                        os.makedirs("screenshots/errors", exist_ok=True)
                        err_ss = f"screenshots/errors/err_{ba_name}_{datetime.now().strftime('%H%M%S')}.png"
                        await page.screenshot(path=err_ss)
                        print(f"      📸 Error artifact captured: {err_ss}")
                        await page.close()
                    except: pass

            print(f"\n🏁 COMPLETED BA: {ba_name}")

if __name__ == "__main__":
    try:
        asyncio.run(post_one_by_one())
    except KeyboardInterrupt:
        print("\n\n🛑 หยุดการทำงานโดยผู้ใช้ (Control + C)")
        print("🖥️ บราวเซอร์ยังคงเปิดอยู่ คุณสามารถใช้งานต่อได้ทันทีครับ")
        sys.exit(0)
