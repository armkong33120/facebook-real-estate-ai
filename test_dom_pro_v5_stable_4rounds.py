import asyncio
import os
import glob
import random
import subprocess
import time
from playwright.async_api import async_playwright
import google.generativeai as genai
import config
import json

genai.configure(api_key=config.GEMINI_API_KEY)

DATA_ROOT = "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร/ยานนาวา"
NEIGHBOR_FILE = "/Users/your_username/Desktop/untitled folder/neighboring_districts.txt"
TARGET_GROUP_COUNT = 9 

async def ai_format_post(raw_text):
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    prompt = f"จัดระเบียบข้อความนี้ให้อ่านง่าย ใส่ Bullet points และ Emoji (ห้ามเพิ่มเนื้อหา ห้ามแต่งเรื่อง):\n\n{raw_text}"
    response = model.generate_content(prompt)
    return response.text.strip()

def pick_random_ba():
    ba_folders = [f for f in os.listdir(DATA_ROOT) if f.startswith("BA")]
    if not ba_folders: return None, None, [], ""
    chosen = random.choice(ba_folders)
    ba_path = os.path.join(DATA_ROOT, chosen)
    txt_files = [f for f in glob.glob(os.path.join(ba_path, "*.txt")) if "processed_hashes" not in f]
    raw_text = ""
    if txt_files:
        with open(txt_files[0], "r", encoding="utf-8") as f:
            raw_text = f.read()
    images = sorted(glob.glob(os.path.join(ba_path, "*.jpg")))
    district = os.path.basename(os.path.dirname(ba_path))
    return chosen, raw_text, images, district

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
                    clean = []
                    for n in neighbors:
                        n = n.replace("อ.", "").strip()
                        if "(" in n: n = n.split("(")[0].strip()
                        if n: clean.append(n)
                    search_order.extend(clean)
                    break
    return search_order

def launch_chrome():
    print("🌐 เปิด Chrome (Port 9292)...")
    subprocess.Popen(["python3", "browser_core.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

def load_all_groups():
    path = os.path.join(os.path.dirname(__file__), "group_analysis.json")
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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
        if len(selected) >= count: break
    return selected

async def search_and_tick_groups(page, group_names):
    total_selected = 0
    search_box = await page.evaluate_handle("""
    () => {
        const dialog = document.querySelector('div[role="dialog"]');
        if (!dialog) return null;
        const inputs = dialog.querySelectorAll('input');
        for (const inp of inputs) {
            const rect = inp.getBoundingClientRect();
            if (rect.width > 100 && rect.height > 0) return inp;
        }
        return null;
    }
    """)
    if not search_box: return 0
    for name in group_names:
        name = name.strip()
        if total_selected >= TARGET_GROUP_COUNT: break
        print(f"  🔎 ค้นหาชื่อกลุ่ม: '{name}'...")
        el = search_box.as_element()
        await el.click(force=True)
        await page.keyboard.press("Meta+a")
        await page.keyboard.press("Backspace")
        await el.fill(name)
        await page.wait_for_timeout(1500)
        rows = await page.query_selector_all('div[role="dialog"] li[role="option"]')
        for row in rows:
            row_text = await row.inner_text()
            if name in row_text:
                cb = await row.query_selector('input[type="checkbox"]')
                if cb and not await cb.is_checked():
                    await row.scroll_into_view_if_needed()
                    await row.click()
                    total_selected += 1
                    print(f"      ✅ ติ๊กแล้ว (รวม: {total_selected})")
                break
    return total_selected

async def test_full_post_with_groups():
    launch_chrome()
    ba_name, raw_text, images, district = pick_random_ba()
    if not ba_name: return
    all_groups_data = load_all_groups()
    group_pool = pick_groups_pool(district, all_groups_data, count=80)
    print(f"✅ เตรียมรายชื่อ {len(group_pool)} กลุ่ม สำหรับเขต {district}")
    print("\n🤖 AI จัดข้อความ...")
    post_content = await ai_format_post(raw_text)
    async with async_playwright() as p:
        try:
            print("🔗 เชื่อมต่อ Chrome...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            print("🧹 ล้างแท็บเก่า...")
            for old_p in context.pages:
                try: await old_p.close()
                except: pass
            for round_idx in range(4):
                round_num = round_idx + 1
                start_idx = round_idx * 10
                if start_idx + 10 > len(group_pool): break
                current_set = group_pool[start_idx : start_idx + 10]
                backups = group_pool[40:]
                main_group = current_set[0]
                search_names = [g["name"] for g in current_set[1:]] + [g["name"] for g in backups]
                
                print(f"\n🚀 === รอบที่ {round_num}/4: เริ่มต้น ===")
                print(f"📍 กลุ่มหลัก: {main_group['name']}")
                
                page = await context.new_page()
                print(f"  🌐 กำลังเปิดลิงก์...")
                await page.goto(main_group['link'], wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                await page.evaluate("window.scrollTo(0, 0)")
                
                print(f"  🔍 กำลังหาปุ่ม 'สร้างโพสต์'...")
                trigger = None
                try:
                    await page.wait_for_selector('div[role="button"]:has-text("สร้างโพสต์สาธารณะ"), div[role="button"]:has-text("เขียนอะไรสักหน่อย")', timeout=10000)
                    trigger = page.locator('div[role="button"]:has-text("สร้างโพสต์สาธารณะ"), div[role="button"]:has-text("เขียนอะไรสักหน่อย")').first
                except: pass
                
                if trigger and await trigger.is_visible():
                    print(f"  ✅ พบปุ่มสร้างโพสต์แล้ว! กำลังคลิก...")
                    await trigger.click()
                    
                    print(f"  ⏳ กำลังรอ Dialog 'สร้างโพสต์' เปิด...")
                    dialog = await page.wait_for_selector('div[role="dialog"]', timeout=15000)
                    print(f"  ✅ Dialog เปิดแล้ว!")
                    
                    print(f"  ✍️ กำลังหาช่องพิมพ์ข้อความ...")
                    textbox = None
                    await page.wait_for_timeout(2000) # รอให้ช่องพิมพ์ Render ให้เสร็จ
                    
                    # คลิกมุมบนซ้ายของ Dialog เพื่อ Focus (ปลอดภัยกว่า x: 100)
                    try: await dialog.click(position={'x': 20, 'y': 20})
                    except: pass
                    
                    for i in range(20):
                        # ใช้ Locator แบบเจาะจงที่ทำงานได้จริงใน FB Dialog
                        found = page.locator('div[role="dialog"] div[role="textbox"], div[role="dialog"] [contenteditable="true"]').first
                        if await found.is_visible():
                            textbox = found; break
                        await page.wait_for_timeout(500)
                    
                    if textbox:
                        print(f"  ✅ พบช่องพิมพ์แล้ว! กำลังวางข้อความ...")
                        await textbox.click()
                        await page.wait_for_timeout(500)
                        await textbox.fill(post_content)
                        print(f"  ✅ วางข้อความสำเร็จ")
                        await page.wait_for_timeout(1000)
                        
                        print(f"  🖼️ กำลังแนบรูปภาพ ({min(len(images), 10)} รูป)...")
                        fi = await page.query_selector('div[role="dialog"] input[type="file"]')
                        if fi:
                            await fi.set_input_files(images[:10])
                            print(f"  ✅ แนบรูปสำเร็จ! (รอโหลด 5 วินาที)")
                            await page.wait_for_timeout(5000)
                            
                        print(f"  🏘️ กำลังกดปุ่ม 'เพิ่มกลุ่ม'...")
                        add_btn = page.get_by_text("เพิ่มกลุ่ม").first
                        if await add_btn.is_visible():
                            await add_btn.click()
                            await page.wait_for_timeout(3000)
                            print(f"  🔍 เริ่มค้นหาชื่อกลุ่มอีก 9 กลุ่ม...")
                            ticked = await search_and_tick_groups(page, search_names)
                            if ticked > 0:
                                print(f"  ✅ เลือกกลุ่มเพิ่มได้ {ticked} กลุ่ม")
                                done_btn = page.get_by_text("เรียบร้อย").first
                                if await done_btn.is_visible():
                                    await done_btn.click()
                                    print(f"  ✅ กดปุ่ม 'เรียบร้อย' แล้ว")
                    else:
                        print(f"  ❌ ไม่พบช่องพิมพ์ข้อความ (ข้ามรอบนี้)")
                
                print(f"🏁 จบรอบที่ {round_num} (สถานะ: เปิดค้างไว้ที่แท็บ {round_num})")
            print(f"\n🎉 ภารกิจเสร็จสิ้น! ทั้ง 4 แท็บเปิดค้างไว้ให้คุณตรวจสอบแล้ว")
        except Exception as e: print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_full_post_with_groups())
