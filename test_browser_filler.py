import asyncio
import os
import random
import json
from playwright.async_api import async_playwright
import google.generativeai as genai
import config

genai.configure(api_key=config.GEMINI_API_KEY)

async def ai_format_post(raw_text):
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    prompt = f"จัดระเบียบข้อความนี้ให้อ่านง่าย ใส่ Bullet points และ Emoji:\n\n{raw_text}"
    response = model.generate_content(prompt)
    return response.text.strip()

async def test_filler_agent_style():
    async with async_playwright() as p:
        try:
            print("🔗 กำลังเชื่อมต่อกับ Chrome (Agent Style)...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9292")
            context = browser.contexts[0]
            
            # ค้นหาหน้า Facebook
            page = None
            for p_obj in context.pages:
                if "facebook.com" in p_obj.url:
                    page = p_obj
                    break
            
            if not page:
                print("❌ ไม่พบหน้า Facebook เปิดอยู่")
                return

            print(f"✅ ทำงานบนหน้า: {await page.title()}")
            
            raw_text = "**ประกาศเช่าบ้าน 2 ชั้น ย่านพระราม 3 - ช่องนนทรี**\nรหัสทรัพย์: BA 10439\nกินหมูกระทะหน้าบ้านได้!"
            post_content = await ai_format_post(raw_text)
            
            print("\n⏳ กำลังเฝ้าสแกนหาช่องโพสต์หลัก (Agent Scanning)...")
            
            while True:
                textboxes = await page.query_selector_all('div[role="textbox"]')
                candidates = []
                
                for i, textbox in enumerate(textboxes):
                    if await textbox.is_visible():
                        aria_label = await textbox.get_attribute("aria-label") or ""
                        box = await textbox.bounding_box()
                        
                        score = 0
                        if any(kw in aria_label.lower() for kw in ["สร้างโพสต์", "post", "write something", "คุณกำลังคิดอะไรอยู่"]):
                            score += 100
                        if any(kw in aria_label.lower() for kw in ["comment", "คอมเม้นท์", "ตอบกลับ", "reply"]):
                            score -= 50
                        if box and box['width'] > 400:
                            score += 50
                        if box and box['y'] < 800:
                            score += 30
                        
                        candidates.append({"element": textbox, "score": score, "label": aria_label})
                
                candidates.sort(key=lambda x: x['score'], reverse=True)
                
                if candidates and candidates[0]['score'] > 80:
                    target = candidates[0]
                    print(f"🎯 เจอช่องที่คะแนนสูงสุดแล้ว! ({target['score']}) Label: {target['label']}")
                    
                    await target['element'].focus()
                    for char in post_content:
                        await page.keyboard.type(char)
                        await asyncio.sleep(random.uniform(0.01, 0.04))
                    
                    print("\n✅ เสร็จสิ้น! พิมพ์ข้อมูลลงช่องโพสต์หลักสำเร็จ")
                    return
                
                await asyncio.sleep(1) # รอ 1 วินาทีแล้วสแกนใหม่
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_filler_agent_style())
