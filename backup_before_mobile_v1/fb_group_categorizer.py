import os
import json
import time
import google.generativeai as genai
import config

# Configuration
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "group_analysis.json")

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

def categorize_group(name, about_text):
    """Uses AI to categorize the group into structured tags with fallback logic"""
    # Check if about_text is missing or just a default "no rules" message
    has_real_rules = about_text and len(about_text) > 50 and "ไม่มีกฏใน" not in about_text
    
    prompt = f"""
    คุณเป็นผู้เชี่ยวชาญด้านการตลาดอสังหาริมทรัพย์ หน้าที่ของคุณคือการวิเคราะห์และติดแท็กกลุ่ม Facebook
    เพื่อให้ระบบ Matching จับคู่ทรัพย์ไปโพสต์ได้อย่างแม่นยำ
    
    ชื่อกลุ่ม: {name}
    ข้อมูลกฎกลุ่ม (About): {about_text if has_real_rules else "ไม่มีข้อมูลกฎกลุ่ม (ให้อ้างอิงจากรายชื่อกลุ่มเป็นหลัก)"}
    
    ---
    คำแนะนำพิเศษ: 
    - หากข้อมูลกฎกลุ่มว่างเปล่าหรือไม่ชัดเจน ให้ใช้ความหมายจาก "ชื่อกลุ่ม" เป็นเกณฑ์ตัดสิน 100%
    - หากชื่อกลุ่มระบุเขตหลายเขต (เช่น สาทร-สีลม) ให้ใส่มาให้ครบใน districts
    - หากกลุ่มมีแนวโน้มเป็นกลุ่มทั่วไป ไม่ระบุพิกัดชัดเจน ให้ใส่ "กรุงเทพฯ ทุกเขต" ใน districts
    
    ให้ตอบกลับในรูปแบบ JSON เท่านั้น:
    {{
      "districts": ["ชื่อเขต1", "ชื่อเขต2"], 
      "asset_types": ["คอนโด", "บ้าน", "ที่ดิน"],
      "transaction_types": ["เช่า", "ขาย", "ทั้งสองอย่าง"],
      "agent_policy": "อนุญาตเอเจนท์" | "เฉพาะเจ้าของ" | "กฎพิเศษ (ระบุสั้นๆ)",
      "match_score": 1-10,
      "is_uncertain": true/false,
      "suggested_action": "เหตุผลสั้นๆ ว่าทำไมถึงแยกหมวดหมู่นี้"
    }}
    
    JSON Output:
    """

    try:
        response = model.generate_content(prompt)
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except Exception as e:
        print(f"      ⚠️ AI Categorization Error: {str(e)}")
        return None

def run_categorization():
    print("\n" + "="*50)
    print("🧠 PHASE 3: Neural Group Categorizer (Updated Logic)")
    print("="*50)
    
    if not os.path.exists(DATA_FILE):
        print("❌ Error: group_analysis.json not found.")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    groups_to_process = [k for k, v in data.items() if "categories" not in v]
    print(f"📊 Total groups: {len(data)}")
    print(f"🎯 Groups to categorize: {len(groups_to_process)}")
    print("-" * 50)

    count = 0
    for url in groups_to_process:
        count += 1
        name = data[url]['name']
        about = data[url].get('rules', '')
        
        print(f"[{count}/{len(groups_to_process)}] Analyzing: {name}")
        categories = categorize_group(name, about)
        
        if categories:
            data[url]['categories'] = categories
            print(f"      ✅ Districts: {categories['districts']} | Uncertain: {categories['is_uncertain']}")
        
        if count % 10 == 0:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"      📂 Progress auto-saved.")

        time.sleep(1.0)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print("\n" + "="*50)
    print("🎉 CATEGORIZATION PREPARED!")
    print("="*50)

if __name__ == "__main__":
    run_categorization()
