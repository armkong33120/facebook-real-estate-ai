import asyncio
import os
import random
import base64
from playwright.async_api import async_playwright
import google.generativeai as genai
import config

# Config Gemini Vision
genai.configure(api_key=config.GEMINI_API_KEY)

async def get_click_coordinates(screenshot_path):
    """ส่งรูปให้ AI วิเคราะห์หาพิกัดปุ่มโพสต์"""
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    with open(screenshot_path, "rb") as f:
        image_data = f.read()

    prompt = """
    วิเคราะห์รูปภาพหน้าจอ Facebook Group นี้:
    1. มองหาปุ่ม "รูปภาพ/วิดีโอ" (Photo/video) ที่อยู่ในส่วนสร้างโพสต์ใหม่ (บนสุดของกลุ่มเท่านั้น)
    2. ปุ่มนี้มักจะมีไอคอนรูปภาพสีเขียว และอยู่โซนบนสุด (ห้ามต่ำกว่าครึ่งหน้าจอ)
    3. บอกพิกัดจุดกึ่งกลางของปุ่มนั้นในรูปแบบ JSON: {"x": พิกัดX, "y": พิกัดY}
    4. สำคัญมาก: ห้ามเลือกคอมเม้นท์หรือรูปภาพในโพสต์ของคนอื่นเด็ดขาด!
    ตอบกลับเฉพาะ JSON เท่านั้น
    """
    
    response = model.generate_content([
        prompt,
        {"mime_type": "image/png", "data": image_data}
    ])
    
    try:
        # ดึง JSON จากคำตอบของ AI
        import json
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        return json.loads(text)
    except:
        print(f"AI Response Error: {response.text}")
        return None

async def test_vision_filler():
    async with async_playwright() as p:
        try:
            print("🔗 เชื่อมต่อ Chrome (Vision Mode)...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            
            page = None
            for p_obj in context.pages:
                if "facebook.com/groups" in p_obj.url:
                    page = p_obj
                    break
            
            print(f"👀 กำลังมองหน้าจอ: {await page.title()}")
            
            # 0. เลื่อนขึ้นไปบนสุดเพื่อให้เห็นช่องโพสต์หลัก
            print("⬆️ กำลังเลื่อนขึ้นไปบนสุดของกลุ่ม...")
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)

            # 1. ถ่ายรูปหน้าจอ
            screenshot_path = "fb_screen.png"
            await page.screenshot(path=screenshot_path)
            print("📸 ถ่ายรูปหน้าจอสำเร็จ!")

            # 2. ให้ AI วิเคราะห์พิกัด
            print("🧠 กำลังส่งให้ AI วิเคราะห์หาช่องโพสต์...")
            coords = await get_click_coordinates(screenshot_path)
            
            if coords:
                print(f"🎯 AI พบจุดโพสต์ที่พิกัด: {coords}")
                
                # 3. คลิกตามพิกัดที่ AI บอก
                await page.mouse.click(coords['x'], coords['y'])
                await page.wait_for_timeout(2000)
                
                # 4. พิมพ์ข้อมูล
                textbox = await page.wait_for_selector('div[role="textbox"]', timeout=5000)
                if textbox:
                    print("⌨️ เริ่มพิมพ์แคปชั่น...")
                    await textbox.type("✅ ทดสอบ Vision AI: พิมพ์ลงช่องโพสต์หลักสำเร็จ! (รหัส BA 10439)")
                    await page.wait_for_timeout(3000) # รอให้พิมพ์เสร็จและนิ่ง
                    
                    # 5. ถ่ายรูปยืนยันผล
                    result_path = "post_result.png"
                    await page.screenshot(path=result_path)
                    print(f"📸 ถ่ายรูปยืนยันผลสำเร็จ: {result_path}")
                    print("\n✅ เสร็จสิ้น! AI มองเห็นและคลิกให้ถูกต้องแล้วครับ")
            else:
                print("❌ AI วิเคราะห์พิกัดไม่สำเร็จ")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_vision_filler())
