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
import re

# --- ระบบ Stable Master (SILENT MODE - NO iMESSAGE) ---
genai.configure(api_key=config.GEMINI_API_KEY)

DATA_ROOTS = [
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ยานนาวา",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/สาทร",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/บางคอแหลม",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/บางรัก",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/คลองเตย",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/คลองสาน",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ปทุมวัน",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/จตุจักร",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ห้วยขวาง",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ราชเทวี",
    "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/พญาไท"
]
NEIGHBOR_FILE = "/Users/your_username/Desktop/untitled folder/neighboring_districts.txt"
TARGET_GROUP_COUNT = 1 # ลดเหลือ 1 กลุ่มเพื่อทดสอบเร็วๆ
RECEIVER = "+66 6-1078-4261"
ENABLE_POST = 0         # โหมดทดสอบ (ไม่กดโพสต์)

# --- ฟังก์ชันจำลองพฤติกรรมมนุษย์ ---
async def human_delay(min_sec=1, max_sec=3):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

def randomize_emojis(text):
    def emoji_replacer(match):
        return match.group(0) if random.random() < 0.7 else ""
    emoji_pattern = r'[^\x00-\x7F\u0E00-\u0E7F\s]'
    return re.sub(emoji_pattern, emoji_replacer, text)

async def human_type(page, selector_or_element, text, speed_wpm=100):
    if isinstance(selector_or_element, str):
        element = page.locator(selector_or_element).first
    else:
        element = selector_or_element
    await element.click()
    base_delay = 60 / (speed_wpm * 5) 
    varied_text = randomize_emojis(text)
    lines = varied_text.split('\n')
    for line_idx, line in enumerate(lines):
        for char in line:
            await page.keyboard.type(char, delay=random.uniform(base_delay*0.5, base_delay*1.5))
            if random.random() > 0.98:
                await page.keyboard.type(random.choice("กขคabc"), delay=100)
                await asyncio.sleep(0.3)
                await page.keyboard.press("Backspace")
        if line_idx < len(lines) - 1:
            await page.keyboard.press("Enter")
            await asyncio.sleep(random.uniform(0.3, 0.8))

async def human_click(page, selector_or_locator):
    if isinstance(selector_or_locator, str):
        element = page.locator(selector_or_locator).first
    else:
        element = selector_or_locator
    box = await element.bounding_box()
    if box:
        target_x = box['x'] + box['width'] * random.uniform(0.2, 0.8)
        target_y = box['y'] + box['height'] * random.uniform(0.2, 0.8)
        await page.mouse.move(target_x, target_y, steps=random.randint(10, 25))
        await asyncio.sleep(random.uniform(0.2, 0.5))
        await page.mouse.click(target_x, target_y)

def launch_chrome(profile_id=1):
    print(f"🌐 [Silent] กำลังเรียกใช้ Chrome Profile {profile_id}...")
    subprocess.Popen(["python3", "browser_core.py", str(profile_id)], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL,
                     start_new_session=True)
    time.sleep(5)

def send_imessage(receiver, message):
    # ปิดการส่งจริง เปลี่ยนเป็น print แทน
    print(f"🔇 [iMessage Blocked] To: {receiver} | Message: {message}")

async def ai_format_post(raw_text):
    print("🤖 AI กำลังจัดข้อความให้สวยงาม...")
    try:
        # ใช้ gemini-1.5-flash แทนเผื่อรุ่นที่ใส่มาไม่มี
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"จัดระเบียบข้อความนี้ให้อ่านง่าย ใส่ Bullet points และ Emoji (ห้ามเพิ่มเนื้อหา ห้ามแต่งเรื่อง):\n\n{raw_text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e: 
        print(f"  ⚠️ AI Error: {e}")
        return raw_text

def pick_diverse_bas(count=1):
    all_ba = []
    img_exts = ['*.jpg', '*.JPG', '*.png', '*.PNG', '*.jpeg', '*.JPEG']
    for root in DATA_ROOTS:
        if not os.path.exists(root): continue
        dist = os.path.basename(root)
        dirs = [d for d in glob.glob(os.path.join(root, "BA*")) if os.path.isdir(d)]
        for d in dirs:
            if os.path.exists(os.path.join(d, "campaign_report_silent.txt")): continue
            ba_name = os.path.basename(d)
            images = []
            for ext in img_exts: images.extend(glob.glob(os.path.join(d, ext)))
            if not images: continue
            all_ba.append({"name": ba_name, "path": d, "district": dist, "images": sorted(list(set(images)))})
    random.shuffle(all_ba)
    return all_ba[:count]

def load_all_groups():
    path = os.path.join(os.path.dirname(__file__), "group_analysis.json")
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def pick_groups_pool(district, all_groups, count=5):
    # เลือกกลุ่มเดียวพอเพื่อทดสอบ
    selected = []
    for link, info in all_groups.items():
        if len(selected) >= count: break
        selected.append({"link": link, "name": info.get("name", "Group")})
    return selected

async def test_silent_run():
    # launch_chrome() - ปิดไว้เพราะเปิดรอแล้ว
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
        except Exception as e:
            print(f"❌ เชื่อมต่อไม่ได้: {e}"); return

        ba_list = pick_diverse_bas(1)
        if not ba_list:
            print("❌ ไม่พบทรัพย์ที่พร้อมโพสต์"); return
        
        ba_data = ba_list[0]
        print(f"\n🚀 [Silent Test] เริ่มทดสอบ 1 BA: {ba_data['name']} ({ba_data['district']})")
        
        # ปิดแท็บอื่น
        for op in context.pages:
            try: await op.close()
            except: pass
        
        # อ่านข้อความ
        txt_files = [f for f in glob.glob(os.path.join(ba_data['path'], "*.txt")) if "report" not in f]
        raw_text = ""
        if txt_files:
            with open(txt_files[0], "r", encoding="utf-8") as f: raw_text = f.read()
        
        post_content = await ai_format_post(raw_text)
        all_groups = load_all_groups()
        group_pool = pick_groups_pool(ba_data['district'], all_groups)
        
        if not group_pool:
            print("❌ ไม่พบกลุ่มสำหรับโพสต์"); return
            
        page = await context.new_page()
        try:
            print(f"🔗 กำลังไปที่กลุ่ม: {group_pool[0]['name']}")
            await page.goto(group_pool[0]['link'], wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            trigger = page.locator('div[role="button"]:has-text("สร้างโพสต์สาธารณะ"), div[role="button"]:has-text("เขียนอะไรสักหน่อย")').first
            if await trigger.is_visible():
                print("✅ พบปุ่มสร้างโพสต์")
                await trigger.click()
                await page.wait_for_timeout(2000)
                
                # ลองพิมพ์ข้อความ (จำลอง)
                textbox = page.locator('div[role="dialog"] div[role="textbox"], div[role="dialog"] [contenteditable="true"]').first
                if await textbox.is_visible():
                    print("⌨️ กำลังจำลองการพิมพ์...")
                    await textbox.fill(post_content[:50] + "...") # พิมพ์แค่บางส่วนเพื่อทดสอบ
                    
                    print("📸 กำลังจำลองการเลือกรูป...")
                    # ในโหมดทดสอบ เราจะไม่ upload จริงเพื่อความเร็ว แต่อยากเช็คว่าเห็น input ไหม
                    fi = await page.query_selector('div[role="dialog"] input[type="file"]')
                    if fi: print("✅ พบช่องเลือกรูปภาพ")
                
                print("📸 แคปภาพหน้าจอเป็นหลักฐาน...")
                await page.screenshot(path="/tmp/silent_test_evidence.png")
                send_imessage(RECEIVER, f"SUCCESS: Silent test for {ba_data['name']} completed.")
            else:
                print("❌ ไม่พบปุ่มสร้างโพสต์ (อาจไม่ได้เป็นสมาชิกกลุ่มหรือกลุ่มปิด)")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
        finally:
            await page.close()
            print("\n✨ จบการทดสอบ 1 BA (Silent Mode) เรียบร้อย")

if __name__ == "__main__":
    asyncio.run(test_silent_run())
