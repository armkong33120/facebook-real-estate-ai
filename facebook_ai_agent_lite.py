import os
import re
import time
import io
import json
import subprocess
import urllib.request
from PIL import Image
from playwright.sync_api import sync_playwright

# ลองพยายาม import google-generativeai
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# --- CONFIGURATION ---
MAPPING_FILE = "uat_links.txt"
BASE_RESULT_DIR = "Facebook_Property_Data"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

GEMINI_API_KEY = "AIzaSyAFAdJZBTICZGAdDW-YljnOgcE2B1hFvXk" # <--- วาง API Key ใหม่ตรงนี้ด้วยตัวเองครับ
if HAS_GEMINI:
    genai.configure(api_key=GEMINI_API_KEY)
    # ใช้รุ่นตามคำสั่งคุณกวงเป๊ะๆ (2.5-flash-lite)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

def analyze_location_with_ai(text):
    if not HAS_GEMINI or not text:
        return "ไม่ระบุ", "ไม่ระบุ"
    # Prompt ระดับ Expert: สั่งให้ AI ตรวจสอบพิกัดเหมือน Google Maps Expert
    prompt = f"""
    ในฐานะผู้เชี่ยวชาญ Google Maps และพิกัดอสังหาริมทรัพย์ในไทย:
    1. ตรวจสอบชื่อคอนโด/โครงการ และลิงก์ Google Maps (ถ้ามี) ในข้อความนี้
    2. ระบุ 'จังหวัด' และ 'เขต/อำเภอ' ที่ถูกต้องตามเขตการปกครองจริง (Official District)
    3. ตอบเป็น JSON เท่านั้น: {{"province":"...", "district":"..."}}
    
    ข้อความ:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        print(f"      DEBUG [AI Raw]: {res_text}") # ส่องดูคำตอบดิบ
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("province", "ไม่ระบุ"), data.get("district", "ไม่ระบุ")
        else:
            print("      DEBUG: ไม่พบรูปแบบ JSON ในคำตอบ AI")
    except Exception as e: 
        print(f"      DEBUG: AI Error - {str(e)}")
    return "ไม่ระบุ", "ไม่ระบุ"

def clean_property_text(text, ba):
    """[V12.3 Deep Purge] ลบชื่อและเบอร์โทรเดิมออกแบบเนียนกริบ"""
    text = re.sub(r'\d{2,3}[-\s]?\d{3,4}[-\s]?\d{3,4}', '', text)
    kill_keywords = [
        'ติดต่อสอบถามรายละเอียด', 'ติดต่อสอบถาม', 'สอบถามรายละเอียด', 'ทักแชท', 'ทัก Inbox',
        'สนใจติดต่อ', 'ติดต่อได้ที่', 'รับเอเจ้น', 'Agent', 'Owner', 'เจ้าของโพสเอง', 
        'รับAgent', 'รับโค้เบอร์', 'รับCo-agent', 'สอบถามเพิ่มเติม', 'นัดชมห้อง', 'แอดไลน์'
    ]
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        s_line = line.strip()
        if not s_line or any(k in s_line for k in kill_keywords): continue
        line_no_names = re.sub(r'\(K\..*?\)', '', s_line)
        line_no_names = re.sub(r'คุณ\s*[\u0E00-\u0E7F]+', '', line_no_names)
        line_no_names = re.sub(r'\(.*?\)', '', line_no_names)
        line_no_names = re.sub(r'[คะค่ะ]+\s*$', '', line_no_names.strip())
        final_line = line_no_names.strip()
        if final_line and len(final_line) > 1: cleaned_lines.append(final_line)
    
    signature = f"""\n━━━━━━━━━━━━━━━\n📞 Contact โทรศัพท์\n• 094-946-3652 (คุณกวง / Khun Kuang)\n• 094-242-6936 (คุณหนิง / Khun Ning)\n• 089-496-5451 (คุณพัด / Khun Pat)\n• 06-5090-7257 (Office)\n━━━━━━━━━━━━━━━\n💬 ช่องทางออนไลน์\n• WhatsApp : +66949463652\n• WeChat: kuanghuiagent\n• LINE: @benchamas_estate (with @)\n{ba}\n"""
    return '\n'.join(cleaned_lines) + signature

def get_fbid(url):
    match = re.search(r'fbid=(\d+)|permalink/(\d+)|posts/(\d+)', url)
    if match: return next(g for g in match.groups() if g is not None)
    return url

def hash_tweak_save(img_data, save_path):
    try:
        img = Image.open(io.BytesIO(img_data))
        img = img.convert("RGB")
        data = list(img.getdata())
        image_out = Image.new("RGB", img.size)
        image_out.putdata(data)
        r, g, b = image_out.getpixel((0,0))
        image_out.putpixel((0,0), ((r + 1) % 256, g, b))
        image_out.save(save_path, "JPEG", quality=95, optimize=True)
        return True
    except: return False

def ultimate_ghost_agent_v12(page, url, ba):
    print(f"\n🚀 [GHOST V12.8] เริ่มปฏิบัติการทรัพย์ {ba}...")
    try:
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(8000)
        
        # [1] ดึงเนื้อหาจาก Modal
        print("   🔍 กำลังสกัดเนื้อหาจากหน้าต่างลอย (Modal Archer)...")
        post_content = page.evaluate('''() => {
            const dialog = document.querySelector('div[role="dialog"]');
            if (dialog) {
                const buttons = Array.from(dialog.querySelectorAll('div[role="button"]'));
                const seeMore = buttons.find(b => b.innerText.includes('ดูเพิ่มเติม') || b.innerText.includes('See more'));
                if (seeMore) seeMore.click();
                const body = dialog.querySelector('div[dir="auto"]');
                return body ? body.innerText : dialog.innerText;
            }
            return "";
        }''')
        
        if not post_content:
            post_content = page.evaluate('() => document.body.innerText')[:2000]

        # [2] วิเคราะห์ทำเล + [3] ฟอกข้อมูล
        province, district = analyze_location_with_ai(post_content[:2000])
        final_info_text = clean_property_text(post_content, ba)
        
        # [4] บันทึกไฟล์
        target_dir = os.path.join(BASE_RESULT_DIR, province, district, ba)
        if not os.path.exists(target_dir): os.makedirs(target_dir)
        with open(os.path.join(target_dir, "property_info.txt"), "w", encoding="utf-8") as f:
            f.write(final_info_text)
        print(f"       📍 พิกัด (AI 2.5): {province}/{district} | 📄 บันทึกข้อความสำเร็จ!")

        # [5] Scrape รูปภาพ (V10.0 Classic Recovery)
        print("   🖼️ [V10.0 CLASSIC] เริ่มปฏิบัติการกวาดรูปภาพ...")
        page.evaluate('''() => {
            const dialog = document.querySelector('div[role="dialog"]');
            if (dialog) {
                const img = dialog.querySelector('img');
                if (img) img.click();
            }
        }''')
        page.wait_for_timeout(6000)
        
        start_fbid = get_fbid(page.url)
        print(f"       ✅ ล็อกเป้าหมายเริ่มต้น: {start_fbid}")
        all_ids = []
        
        for i in range(50):
            current_fbid = get_fbid(page.url)
            if i > 0 and current_fbid == start_fbid:
                print(f"   🏁 จบภารกิจ! วนกลับมาที่เดิม ({len(all_ids)} รูป)")
                break
                
            img_src = page.evaluate('''() => {
                const dialogs = Array.from(document.querySelectorAll('div[role="dialog"]'));
                const target = dialogs.length > 1 ? dialogs[dialogs.length - 1] : dialogs[0];
                if (!target) return null;
                const imgs = Array.from(target.querySelectorAll('img')).filter(img => img.width > 400);
                return imgs.length > 0 ? imgs[0].src : null;
            }''')
            
            if img_src:
                all_ids.append(current_fbid)
                print(f"       📸 ใบที่ {len(all_ids)}: เก็บเลข ID {current_fbid} สำเร็จ")
                try:
                    req = urllib.request.Request(img_src, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = resp.read()
                    hash_tweak_save(data, os.path.join(target_dir, f"property_{len(all_ids)}.jpg"))
                except: pass
            
            # คลิกถัดไป (Relay 6s-8s เพื่อความเสถียร)
            next_btn = page.query_selector('div[aria-label="รูปภาพถัดไป"], div[aria-label="Next Photo"]')
            if next_btn: 
                next_btn.click()
            else: 
                page.keyboard.press("ArrowRight")
            
            page.wait_for_timeout(6000) 
            
            # ตรวจสอบว่ารูปเปลี่ยนจริงไหม ถ้าไม่เปลี่ยนให้ซ้ำด้วย ArrowRight
            if get_fbid(page.url) == current_fbid:
                page.keyboard.press("ArrowRight")
                page.wait_for_timeout(4000)

    except Exception as e: print(f"   ❌ Error: {str(e)}")

def main():
    if not os.path.exists(MAPPING_FILE): return
    mapping = {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if "|" in line:
                p = line.split("|")
                mapping[p[0].strip()] = p[1].strip()
    
    with sync_playwright() as p:
        user_data_dir = os.path.join(SCRIPT_DIR, "fb_bot_profile")
        context = p.chromium.launch_persistent_context(user_data_dir, headless=False, no_viewport=True)
        page = context.pages[0] if context.pages else context.new_page()
        print("\n💡 กด [Enter] เพื่อเริ่ม Full Pipeline (AI 2.5 + V10 Image)...")
        print(f"\n🚀 เริ่มปฏิบัติการดูดทรัพย์ทั้งหมด {len(mapping)} ลิงก์...")
        for ba, url in mapping.items():
            try:
                ultimate_ghost_agent_v12(page, url, ba)
            except Exception as e:
                print(f"❌ ข้ามทรัพย์ {ba} เนื่องจากเกิดข้อผิดพลาด: {str(e)}")
        
        print("\n🏆 จบภารกิจกวาดทรัพย์ทุกรายรายการ! กำลังเปิดโฟลเดอร์ผลลัพธ์...")
        subprocess.run(["open", BASE_RESULT_DIR])
        time.sleep(5)
        context.close()

if __name__ == "__main__": main()
