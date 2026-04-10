import os
import functools
import json
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# บังคับให้ Console พิมพ์ออกมาทันที
print = functools.partial(print, flush=True)

# --- CONFIG ---
API_KEY = "AIzaSyDpGPdrSJWzZTIU3jmqEBkwNtHpwn_6a3w"
genai.configure(api_key=API_KEY)

def analyze_location_with_ai(text):
    """ส่งข้อความให้ AI วิเคราะห์ทำเล"""
    print(f"   🤖 กำลังส่งข้อมูลให้ AI วิเคราะห์...")
    prompt = f"""
    คุณคือผู้เชี่ยวชาญด้านอสังหาริมทรัพย์ในไทย 
    หน้าที่ของคุณคือสกัดข้อมูล 'จังหวัด' และ 'เขต/อำเภอ' จากข้อความโพสต์ Facebook ต่อไปนี้
    และตอบกลับในรูปแบบ JSON เท่านั้น ห้ามมีข้อความอื่นปน
    
    รูปแบบ:
    {{
      "province": "ชื่อจังหวัด",
      "district": "ชื่อเขตหรืออำเภอ"
    }}
    
    ข้อความโพสต์:
    {text}
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        data = json.loads(response.text.strip())
        return data.get("province", "ไม่ระบุ"), data.get("district", "ไม่ระบุ")
    except Exception as e:
        print(f"   ❌ AI Error: {str(e)}")
        return "ไม่ระบุ", "ไม่ระบุ"

def debug_location_ai(url):
    """ทดสอบขั้นตอนการกวาดข้อความและวิเคราะห์ทำเล"""
    print(f"\n🔍 [AI DEBUG] เริ่มทดสอบสแกนทำเลจากลิงก์...")
    
    with sync_playwright() as p:
        # ใช้ Profile เดิมเพื่อให้ไม่ต้อง Log in ใหม่
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(SCRIPT_DIR, "fb_bot_profile")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir, headless=False, no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        print(f"   [1] กำลังโหลดหน้าเว็บ: {url}")
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(5000)
        
        # [2] กวาดข้อความโพสต์ (Smart Search)
        print("   [2] กำลังกวาดข้อความโพสต์ (Smart Search)...")
        
        # พยายามกดปุ่ม "ดูเพิ่มเติม" (See More)
        try:
            see_more = page.locator('div[role="button"]:has-text("ดูเพิ่มเติม"), div[role="button"]:has-text("See More")').first
            if see_more.is_visible():
                see_more.click()
                print("       ✅ กดปุ่ม 'ดูเพิ่มเติม' สำเร็จ")
                page.wait_for_timeout(2000)
        except: pass
        
        # ดึงข้อความแบบเจาะจง (Article Filter Mode)
        print("   [2] กำลังกรองโพสต์ (Article Filter Mode)...")
        post_text = page.evaluate('''
            () => {
                // 1. หาโพสต์ทั้งหมดในหน้า (ตัด Sidebar ทิ้ง)
                const articles = Array.from(document.querySelectorAll('div[role="article"]'));
                for (let art of articles) {
                    const txt = art.innerText;
                    // ต้องเป็นโพสต์ที่มีคำสำคัญของทรัพย์เราจริงๆ
                    if (txt.includes('Fuse') || txt.includes('คอนโด') || txt.includes('ปล่อยเช่า')) {
                        // เจาะหาเนื้อความใน div dir="auto" ที่อยู่ข้างใน article นี้
                        const body = art.querySelector('div[dir="auto"]');
                        if (body && body.innerText.length > 50) return body.innerText;
                        return txt;
                    }
                }
                
                // 2. Fallback: ถ้าวิธีแรกไม่เจอ ให้ลองหา div ที่ใหญ่ที่สุดที่มีคีย์เวิร์ด
                const allDivs = Array.from(document.querySelectorAll('div[dir="auto"]'))
                                     .filter(d => d.innerText.includes('Fuse') || d.innerText.includes('คอนโด'));
                if (allDivs.length > 0) {
                    return allDivs.reduce((prev, curr) => prev.innerText.length > curr.innerText.length ? prev : curr).innerText;
                }
                
                return ""; 
            }
        ''')
        
        # หากยังหาไม่เจอด้วยระบบ Article ให้ไปขุดจาก Dump โดยตรงแบบเจาะจงจุด
        if not post_text or len(post_text) < 50:
            print("       ⚠️ ใช้ระบบ Article Filter ไม่เจอ... กำลังพยายามขุดจาก Dump โดยตรง...")
            import re
            match = re.search(r'(คอนโด\s*:\s*Fuse.*?)(?=ความคิดเห็น|\n\n\n)', raw_full_text, re.DOTALL)
            if match:
                post_text = match.group(1)
                print("       🎯 ขุดพบเนื้อหาโพสต์จาก Dump สำเร็จ!")
            else:
                post_text = raw_full_text[:3000] 
        
        clean_text = post_text[:3000].replace('\n', ' ')
        print(f"       ✅ ดึงข้อความได้สำเร็จ (ความยาว {len(clean_text)} ตัวอักษร)")
        print(f"       📝 ตัวอย่างข้อความ: {clean_text[:150]}...")
        
        # [3] ส่งให้ AI วิเคราะห์
        province, district = analyze_location_with_ai(clean_text)
        
        print("\n" + "="*30)
        print(f"📍 ผลลัพธ์การวิเคราะห์ทำเล:")
        print(f"   🏙️ จังหวัด: {province}")
        print(f"   🏘️ เขต/อำเภอ: {district}")
        print("="*30)
        
        print("\n💡 ตรวจสอบผลลัพธ์ด้านบนว่าถูกต้องหรือไม่...")
        print("เมื่อตรวจสอบเสร็จแล้ว กด [Enter] เพื่อจบการ Debug...")
        input()
        context.close()

if __name__ == "__main__":
    test_url = "https://www.facebook.com/groups/988352639198652/permalink/1714400799927162"
    debug_location_ai(test_url)
