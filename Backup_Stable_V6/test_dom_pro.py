import asyncio
import os
import glob
import random
import subprocess
import time
import json
from datetime import datetime
from playwright.async_api import async_playwright
import google.generativeai as genai
import config

# --- ระบบ Stable Master (Concise iMessage - ส่งผ่านชัวร์ ไม่ติดบล็อก) ---
genai.configure(api_key=config.GEMINI_API_KEY)

DATA_ROOTS = [
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ยานนาวา",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/สาทร",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/บางคอแหลม",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/บางรัก"
]
NEIGHBOR_FILE = "/Users/your_username/Desktop/untitled folder/neighboring_districts.txt"
TARGET_GROUP_COUNT = 9 
RECEIVER = "+66 6-1078-4261"
ENABLE_POST = 0  # 1 = เปิด (โพสต์จริง), 0 = ปิด (ทดสอบ ไม่กดโพสต์)

# --- ฟังก์ชันช่วยเหลือ ---

def launch_chrome():
    print("🌐 ตรวจสอบสถานะ Chrome (Port 9292)...")
    subprocess.Popen(["python3", "browser_core.py"], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL,
                     start_new_session=True)
    time.sleep(5)

def send_imessage(receiver, message):
    """ส่ง iMessage แบบบังคับใช้ระบบ iMessage (ฟรี/ปุ่มน้ำเงิน)"""
    # ใช้เบอร์แบบสากลสำหรับ iMessage (+66)
    clean_number = receiver.replace(" ", "").replace("-", "")
    if not clean_number.startswith("+"):
        clean_number = "+" + clean_number
        
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
    print("🤖 AI กำลังจัดข้อความให้สวยงาม...")
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        prompt = f"จัดระเบียบข้อความนี้ให้อ่านง่าย ใส่ Bullet points และ Emoji (ห้ามเพิ่มเนื้อหา ห้ามแต่งเรื่อง):\n\n{raw_text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except: return raw_text

def pick_diverse_bas(count=10):
    all_eligible = []
    img_exts = ['*.jpg', '*.JPG', '*.png', '*.PNG', '*.jpeg', '*.JPEG']
    for root in DATA_ROOTS:
        if not os.path.exists(root): continue
        district_name = os.path.basename(root)
        folders = [f for f in os.listdir(root) if f.startswith("BA")]
        for f in folders:
            ba_path = os.path.join(root, f)
            if not os.path.exists(os.path.join(ba_path, "campaign_report.txt")):
                images = []
                for ext in img_exts: images.extend(glob.glob(os.path.join(ba_path, ext)))
                if len(images) > 0:
                    all_eligible.append({
                        "name": f,
                        "path": ba_path,
                        "district": district_name,
                        "images": sorted(list(set(images)))
                    })
    if not all_eligible: return []
    random.shuffle(all_eligible)
    return all_eligible[:count]

def load_all_groups():
    path = os.path.join(os.path.dirname(__file__), "group_analysis.json")
    if not os.path.exists(path): return {}
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
    try:
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
    except: pass
    return search_order

async def search_and_tick_groups(page, group_pool):
    total_selected = 0
    ticked_info = []
    search_box = None
    for _ in range(5):
        search_box_handle = await page.evaluate_handle("""
        () => {
            const dialogs = document.querySelectorAll('div[role="dialog"]');
            for (const d of dialogs) {
                const inputs = d.querySelectorAll('input');
                for (const inp of inputs) {
                    const rect = inp.getBoundingClientRect();
                    if (rect.width > 100) return inp;
                }
            }
            return null;
        }
        """)
        if search_box_handle and search_box_handle.as_element():
            search_box = search_box_handle.as_element()
            break
        await page.wait_for_timeout(1000)
    
    if not search_box: return 0, []

    for item in group_pool:
        if total_selected >= TARGET_GROUP_COUNT: break
        name = item["name"]
        try:
            print(f"  🔎 ค้นหา: {name[:25]}...")
            await search_box.click(force=True)
            await page.keyboard.press("Meta+a")
            await page.keyboard.press("Backspace")
            await search_box.fill(name)
            await page.wait_for_timeout(1800)
            rows = await page.query_selector_all('div[role="dialog"] li[role="option"]')
            found_match = False
            for row in rows:
                row_text = await row.inner_text()
                if name[:10] in row_text:
                    cb = await row.query_selector('input[type="checkbox"]')
                    if cb and not await cb.is_checked():
                        await row.click()
                        total_selected += 1
                        ticked_info.append(item)
                        print(f"      ✅ ติ๊กแล้ว ({total_selected}/{TARGET_GROUP_COUNT}): {name[:25]}...")
                        found_match = True
                    break
            if not found_match:
                print(f"      ❌ ไม่พบกลุ่มที่ตรงกัน กำลังหาตัวถัดไป...")
        except: pass
    return total_selected, ticked_info

async def test_full_post_with_groups():
    launch_chrome()
    async with async_playwright() as p:
        try:
            print("🔗 เชื่อมต่อ Chrome (CDP: 9292)...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
        except Exception as e:
            print(f"❌ เชื่อมต่อไม่ได้: {e}"); return

        ba_list = pick_diverse_bas(10)
        for ba_idx, ba_data in enumerate(ba_list):
            ba_name = ba_data["name"]; ba_path = ba_data["path"]
            district = ba_data["district"]; images = ba_data["images"]
            
            print(f"\n🌟 === เริ่มภารกิจ BA Loop {ba_idx+1}/10 ===")
            print(f"📂 กำลังทำ BA: {ba_name} ({district})")
            
            # --- ระบบล้างแท็บเก่า (Clear Tab) ---
            print("🧹 ล้างแท็บเก่าที่ค้างอยู่...")
            for op in context.pages:
                try: await op.close()
                except: pass
            
            ev_dir = os.path.join(ba_path, f"Evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(ev_dir, exist_ok=True)
            
            all_groups_data = load_all_groups()
            group_pool = pick_groups_pool(district, all_groups_data)
            
            txt_files = [f for f in glob.glob(os.path.join(ba_path, "*.txt")) if "processed_hashes" not in f and "campaign_report" not in f]
            raw_text = ""
            if txt_files:
                with open(txt_files[0], "r", encoding="utf-8") as f: raw_text = f.read()
            
            post_content = await ai_format_post(raw_text)
            
            for round_idx in range(4):
                round_num = round_idx + 1
                start_offset = round_idx * 10
                if start_offset >= len(group_pool): break
                
                main_g = group_pool[start_offset]
                others_fallback = group_pool[start_offset + 1:]
                
                print(f"\n🚀 รอบที่ {round_num}/4")
                page = await context.new_page()
                try:
                    await page.goto(main_g['link'], wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(3000)
                    await page.keyboard.press("Escape")
                    
                    trigger = page.locator('div[role="button"]:has-text("สร้างโพสต์สาธารณะ"), div[role="button"]:has-text("เขียนอะไรสักหน่อย")').first
                    await trigger.click()
                    
                    dialog = page.locator('div[role="dialog"]').filter(has=page.locator('div[role="textbox"], [contenteditable="true"]')).filter(visible=True).first
                    await dialog.wait_for(state="visible", timeout=15000)
                    
                    await page.wait_for_timeout(2000)
                    try: await dialog.click(position={'x': 20, 'y': 20})
                    except: pass
                    
                    textbox = dialog.locator('div[role="textbox"], [contenteditable="true"]').first
                    await textbox.fill(post_content)
                    
                    fi = await page.query_selector('div[role="dialog"] input[type="file"]')
                    if fi:
                        await fi.set_input_files(images[:10])
                        await page.wait_for_timeout(5000)
                    
                    ticked_info = []
                    add_btn = dialog.get_by_text("เพิ่มกลุ่ม").first
                    if await add_btn.is_visible():
                        await add_btn.click()
                        await page.wait_for_timeout(2000)
                        _, ticked_info = await search_and_tick_groups(page, others_fallback)
                        done = page.locator('div[role="button"]:has-text("เรียบร้อย"), span:has-text("เรียบร้อย")').first
                        if await done.is_visible(): await done.click()
                    
                    await page.screenshot(path=os.path.join(ev_dir, f"Round_{round_num}_Evidence.png"))
                    
                    tag = "[โพสต์จริง]" if ENABLE_POST == 1 else "[โหมดทดสอบ]"
                    if ENABLE_POST == 1:
                        post_btn = page.locator('div[role="button"]').filter(has_text="โพสต์").filter(has_not_text="ไม่ระบุตัวตน").last
                        await post_btn.click(force=True)
                        await page.wait_for_timeout(10000)
                        print(f"  ✅ รอบ {round_num} โพสต์เรียบร้อย!")
                    else:
                        print("  ⚠️ โหมดทดสอบ: ไม่กดปุ่มโพสต์จริง")
                    
                    # --- รายงาน iMessage แบบละเอียด (ตามสั่ง) ---
                    finish_time = datetime.now().strftime('%H:%M')
                    tag = "[โพสต์จริง]" if ENABLE_POST == 1 else "[โหมดทดสอบ]"
                    current_round_groups = [main_g] + ticked_info
                    
                    im_text = f"{tag} BA: {ba_name} (รอบ {round_num}/4)\n"
                    im_text += f"📍 เขต: {district}\n"
                    im_text += f"📸 รูปภาพ: {len(images)} ใบ\n"
                    im_text += f"⏰ เวลา: {finish_time}\n\n"
                    
                    for i, item in enumerate(current_round_groups):
                        im_text += f"🔹 {i+1}: {item['name'][:25]}...\n"
                        im_text += f"ลิงก์ : {item['link']}\n"
                    
                    im_text += f"\n📸 บันทึกหลักฐานรอบ {round_num} แล้ว"
                    
                    # บันทึกรายละเอียดเต็มลงไฟล์
                    log_file = os.path.join(ev_dir, f"round_{round_num}_details.txt")
                    with open(log_file, "w", encoding="utf-8") as f:
                        for i, item in enumerate(current_round_groups):
                            f.write(f"{i+1}: {item['name']} | {item['link']}\n")
                    
                    send_imessage(RECEIVER, im_text)
                    # ---------------------------------------------

                except Exception as e:
                    print(f"  ❌ พลาดรอบ {round_num}: {e}")
                # หมายเหตุ: ไม่ปิด page เพื่อให้ค้างไว้ 4 แท็บให้คุณตรวจสอบ
            
            with open(os.path.join(ba_path, "campaign_report.txt"), "w", encoding="utf-8") as f:
                f.write(f"Completed: {datetime.now()}")
            print(f"✨ จบภารกิจ BA {ba_name}")

if __name__ == "__main__":
    asyncio.run(test_full_post_with_groups())
