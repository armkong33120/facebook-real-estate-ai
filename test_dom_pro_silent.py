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

# --- ระบบ Stable Master (SILENT MODE - PRODUCTION) ---
# ฉบับปรับปรุงตามคำอนุมัติ: ไม่ส่ง iMessage, โพสต์จริง (ENABLE_POST=1)
genai.configure(api_key=config.GEMINI_API_KEY)

DATA_ROOTS = [
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ยานนาวา"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/สาทร"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/บางคอแหลม"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/บางรัก"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/คลองเตย"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/คลองสาน"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ปทุมวัน"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/จตุจักร"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ห้วยขวาง"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ราชเทวี"),
    os.path.expanduser("~/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/พญาไท")
]
NEIGHBOR_FILE = os.path.expanduser("~/Desktop/untitled folder/neighboring_districts.txt")
TARGET_GROUP_COUNT = 9 
ENABLE_POST = 0         # โหมดทดสอบ (ปิดโพสต์จริง)


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
    print(f"🌐 [Silent] มั่นใจว่า Chrome Profile {profile_id} เปิดอยู่บน Port 9292...")
    # ตรวจสอบว่ามีคนเปิดอยู่ไหม ถ้าไม่มีค่อยเปิด
    try:
        import urllib.request
        # ใช้ 127.0.0.1
        urllib.request.urlopen("http://127.0.0.1:9292/json/version", timeout=2)
        print("✅ Chrome พร้อมใช้งานแล้ว")
    except:
        print("🚀 ไม่พบ Chrome กำลังเรียกใช้ browser_core.py...")
        subprocess.Popen(["python3", "browser_core.py", str(profile_id)], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         start_new_session=True)
        # รอให้นานขึ้นเพื่อให้ Browser พร้อมจริงๆ
        for i in range(15):
            try:
                time.sleep(1)
                urllib.request.urlopen("http://127.0.0.1:9292/json/version", timeout=1)
                print(f"✅ Chrome พร้อมแล้ว (ใช้เวลา {i+1} วินาที)")
                return
            except:
                pass
        print("⚠️ คำเตือน: Chrome อาจจะยังไม่พร้อม")

async def ai_format_post(raw_text):
    print("🤖 AI กำลังจัดข้อความให้สวยงาม...")
    try:
        # ใช้รุ่นจาก config
        model = genai.GenerativeModel(config.MODEL_NAME) 
        prompt = f"จัดระเบียบข้อความนี้ให้อ่านง่าย ใส่ Bullet points และ Emoji (ห้ามเพิ่มเนื้อหา ห้ามแต่งเรื่อง):\n\n{raw_text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e: 
        print(f"  ⚠️ AI Error: {e} (ใช้ข้อความดิบแทน)")
        return raw_text

def pick_diverse_bas(count=30):
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
    with open(path, "r", encoding="utf-8") as f: 
        return json.load(f)

def pick_groups_pool(district, all_groups, count=80):
    if not all_groups: return []
    # เลียนแบบ logic เดิมของลูกค้า
    selected = []
    seen_links = set()
    # ดึงชื่อเขตใกล้เคียง (ถ้ามี)
    search_districts = [district]
    if os.path.exists(NEIGHBOR_FILE):
        try:
            with open(NEIGHBOR_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if district in line and ":" in line:
                        neighbors = [n.strip() for n in line.split(":", 1)[1].split(",")]
                        search_districts.extend(neighbors)
                        break
        except: pass
    
    for d in search_districts:
        for link, info in all_groups.items():
            if len(selected) >= count: break
            if link in seen_links: continue
            if d in info.get("name", ""):
                selected.append({"link": link, "name": info.get("name", "")})
                seen_links.add(link)
    
    # ถ้ายังไม่ครบ 80 เอาที่เหลือมาเสริม
    if len(selected) < count:
        for link, info in all_groups.items():
            if len(selected) >= count: break
            if link not in seen_links:
                selected.append({"link": link, "name": info.get("name", "")})
                seen_links.add(link)
    return selected

async def search_and_tick_groups(page, group_pool):
    total_selected = 0
    ticked_info = []
    print(f"  🔍 เริ่มการค้นหาและติ๊กกลุ่มเสริม (เป้าหมาย {TARGET_GROUP_COUNT} กลุ่ม)")
    
    try:
        # หาช่อง Search ใน Dialog
        search_box = page.locator('div[role="dialog"] input[placeholder*="ค้นหา"], div[role="dialog"] input[aria-label*="ค้นหา"]').first
        if not await search_box.is_visible(): 
            print("    ⚠️ ไม่พบช่องค้นหากลุ่ม")
            return 0, []
        
        for item in group_pool:
            if total_selected >= TARGET_GROUP_COUNT: break
            
            group_name = item["name"]
            print(f"    🔎 กำลังค้นหา: {group_name[:30]}...")
            
            # ล้างช่อง Search และพิมพ์ใหม่
            await search_box.click()
            await page.keyboard.press("Meta+a")
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.5)
            await search_box.fill(group_name)
            await asyncio.sleep(2) # รอผลลัพธ์โหลด
            
            # หาแถวที่มีชื่อกลุ่มตรงกัน
            # Facebook มักใช้ role="listitem" หรือ role="option" ในหน้านี้
            rows = await page.locator('div[role="dialog"] [role="listitem"], div[role="dialog"] [role="option"]').all()
            
            for row in rows:
                text = await row.inner_text()
                if group_name[:10].lower() in text.lower():
                    # หาปุ่ม Checkbox ในแถวนั้น
                    checkbox = row.locator('div[role="checkbox"], input[type="checkbox"]').first
                    if await checkbox.is_visible():
                        status = await checkbox.get_attribute("aria-checked")
                        if status != "true":
                            print(f"      ✅ พบกลุ่มและกำลังติ๊ก: {group_name[:20]}")
                            await row.click()
                            total_selected += 1
                            ticked_info.append(item)
                            await asyncio.sleep(0.8)
                        else:
                            print(f"      ℹ️ กลุ่มนี้ถูกติ๊กอยู่แล้ว: {group_name[:20]}")
                            total_selected += 1 # นับรวมด้วยถ้ามันติ๊กอยู่แล้ว
                        break
            
            if total_selected >= TARGET_GROUP_COUNT: break

    except Exception as e:
        print(f"    ❌ เกิดข้อผิดพลาดขณะติ๊กกลุ่ม: {e}")
        
    print(f"  📊 สรุป: ติ๊กกลุ่มเสริมสำเร็จทั้งหมด {total_selected} กลุ่ม")
    return total_selected, ticked_info

async def run_silent_production():
    launch_chrome()
    async with async_playwright() as p:
        try:
            # ใช้ 127.0.0.1 แทน localhost เพื่อเลี่ยงปัญหา IPv6 (::1)
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9292")
            context = browser.contexts[0]
        except Exception as e:
            print(f"❌ Connection Error: {e}"); return

        ba_list = pick_diverse_bas(1) # ทดสอบแค่ 1 BA ตามสั่ง
        print(f"📋 เริ่มการทดสอบ 1 ทรัพย์: {ba_list[0]['name']}")
        
        for ba_idx, ba_data in enumerate(ba_list):
            print(f"\n🌟 เริ่มงาน BA: {ba_data['name']} ({ba_data['district']})")
            
            # ล้างหน้าต่าง (เฉพาะตอนเริ่ม BA)
            for op in context.pages:
                try: await op.close()
                except: pass
            
            # เตรียมเนื้อหา
            txt_files = [f for f in glob.glob(os.path.join(ba_data['path'], "*.txt")) if "report" not in f]
            raw_text = ""
            if txt_files:
                with open(txt_files[0], "r", encoding="utf-8") as f: raw_text = f.read()
            
            post_content = await ai_format_post(raw_text)
            all_groups_data = load_all_groups()
            group_pool = pick_groups_pool(ba_data['district'], all_groups_data)
            
            # แบ่งเป็น 4 รอบเหมือนต้นฉบับ
            pool_idx = 0
            for r in range(1, 5):
                if pool_idx >= len(group_pool): break
                main_g = group_pool[pool_idx]
                pool_idx += 1
                
                print(f"  🚀 รอบที่ {r}/4 | กลุ่มหลัก: {main_g['name'][:30]}")
                page = await context.new_page()
                try:
                    await page.goto(main_g['link'], timeout=60000)
                    await asyncio.sleep(3)
                    await page.keyboard.press("Escape")
                    
                    trigger = page.locator('div[role="button"]:has-text("สร้างโพสต์สาธารณะ"), div[role="button"]:has-text("เขียนอะไรสักหน่อย")').first
                    await trigger.wait_for(state="visible", timeout=20000)
                    await trigger.click()
                    
                    dialog = page.locator('div[role="dialog"]').filter(visible=True).first
                    textbox = dialog.locator('div[role="textbox"], [contenteditable="true"]').first
                    await human_type(page, textbox, post_content)
                    
                    # รูปภาพ
                    fi = await page.query_selector('div[role="dialog"] input[type="file"]')
                    if fi:
                        await fi.set_input_files(ba_data['images'][:10])
                        await asyncio.sleep(5)
                    
                    # เพิ่มกลุ่ม
                    add_btn = dialog.get_by_text("เพิ่มกลุ่ม").first
                    if await add_btn.is_visible():
                        await add_btn.click()
                        await asyncio.sleep(2)
                        _, _ = await search_and_tick_groups(page, group_pool[pool_idx:pool_idx+15])
                        done = page.locator('div[role="button"]:has-text("เรียบร้อย"), span:has-text("เรียบร้อย")').first
                        if await done.is_visible(): await done.click()
                    
                    if ENABLE_POST == 1:
                        post_btn = page.locator('div[role="button"]:has-text("โพสต์")').last
                        await post_btn.click()
                        print("    ✅ โพสต์สำเร็จ (รอ 10 วิ)")
                        await asyncio.sleep(10)
                        await page.close() # ถ้าโพสต์จริงให้ปิดแท็บเพื่อล้างหน่วยความจำ
                    else:
                        print(f"    🧪 [Test Mode] รอบที่ {r} เสร็จสิ้น (ค้างหน้าจอไว้ตามสั่ง)")
                        # ถ้าเป็นรอบสุดท้าย ให้หยุดรอตรวจ
                        if r == 4 or pool_idx >= len(group_pool):
                            print("\n🏁 จบการทดสอบครบ 4 รอบแล้วครับ! เปิดหน้าจอค้างไว้ให้ตรวจทั้งหมด 4 แท็บครับ")
                            while True: await asyncio.sleep(3600) 
                except Exception as e:
                    print(f"    ❌ พลาดรอบ {r}: {e}")
                    # ถ้าพลาด อาจจะปิดแท็บนั้นไปเลยเพื่อไม่ให้รก
                    try: await page.close()
                    except: pass
            
            # ลบส่วน await page.close() ที่เคยอยู่ตรงนี้ออกเพื่อให้แท็บค้างไว้ค้างไว้จริง ๆ
            
            # บันทึกสถานะ (สำหรับโหมดทดสอบอาจจะไม่ต้องบันทึกก็ได้ แต่ใส่ไว้กันพลาด)
            # with open(os.path.join(ba_data['path'], "campaign_report_silent.txt"), "w") as f:
            #    f.write(f"Tested at {datetime.now()}")
            
            # พักระหว่าง BA
            if (ba_idx + 1) % 3 == 0:
                rest = random.randint(3600, 5400)
                print(f"☕ พักเบรกใหญ่ {rest//60} นาที...")
                await asyncio.sleep(rest)
            else:
                await asyncio.sleep(random.randint(60, 180))

if __name__ == "__main__":
    asyncio.run(run_silent_production())
