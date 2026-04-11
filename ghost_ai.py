import json
import re
import google.generativeai as genai
from ghost_config import GEMINI_API_KEY, MODEL_NAME

# Setup Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    HAS_AI = True
except Exception as e:
    print(f"⚠️ Warning: Gemini Configuration Failed: {e}")
    HAS_AI = False

def load_landmarks():
    """โหลดข้อมูลพจนานุกรมพิกัดเพื่อความแม่นยำสูงสุด"""
    try:
        with open("ghost_landmarks.json", "r", encoding="utf-8") as f:
            return json.load(f).get("landmarks", [])
    except:
        return []

def analyze_location_with_ai(text):
    """
    [FUNCTION: Hybrid Location Expert]
    ลำดับการทำงาน:
    1. พยายามสแกนหา 'ชื่อโครงการ' ในพจนานุกรมก่อน (แม่นยำ 100% ไม่พึ่ง AI)
    2. หากไม่เจอ: ส่งข้อมูลโครงการใกล้เคียงให้ AI ช่วยตัดสินใจ
    """
    if not text:
        return "ไม่ระบุ", "ไม่ระบุ"
        
    # [STEP 1] ค้นหาในพจนานุกรม (Landmark Dictionary Lookup)
    landmarks = load_landmarks()
    for lm in landmarks:
        for kw in lm.get("keywords", []):
            if kw.lower() in text.lower():
                print(f"       ✅ พบข้อมูลในพจนานุกรม: {kw} -> {lm['district']}")
                return lm["province"], lm["district"]

    # [STEP 2] หากไม่เจอในพจนานุกรม ให้ใช้ AI ช่วยวิเคราะห์
    if not HAS_AI:
        return "ไม่ระบุ", "ไม่ระบุ"

    # สร้างรายชื่อ Landmark อ้างอิงเพื่อส่งไปให้ AI ดูเป็นตัวอย่างพิกัด
    guide = "\n".join([f"- {lm['keywords'][0]}: {lm['district']}" for lm in landmarks[:5]])

    prompt = f"""
    คุณคือผู้เชี่ยวชาญด้านพิกัดเขตปกครองของไทย (Thailand Administrative Expert):
    ภารกิจ: ระบุ 'จังหวัด' และ 'เขต/อำเภอ' (Khet/Amphoe) ที่ถูกต้องตามกฎหมาย 100%
    
    คู่มืออ้างอิงพิกัดย่านใกล้เคียง:
    {guide}
    
    กฎเหล็กในการวิเคราะห์:
    1. ตรวจสอบ 'แขวง/ตำบล' (Khwaeng/Tambon) จากที่อยู่หรือชื่อโครงการเพื่อระบุ 'เขต/อำเภอ' ที่ถูกต้อง
    2. ระวัง: ย่านการค้ามักคาบเกี่ยวหลายเขต (เช่น กรุงเทพกรีฑา มีทั้งเขตสะพานสูงและเขตลาดกระบัง) ให้เลือกเขตที่โครงการนั้นตั้งอยู่จริงตามทะเบียนราษฎร์
    3. ตรวจสอบชื่อคอนโด/หมู่บ้าน และลิงก์ Google Maps (ถ้ามี) อย่างละเอียด
    4. ห้ามเดาจากชื่อย่านกว้างๆ ให้ระบุตามขอบเขตการปกครองจริง (Official Administrative Boundaries)
    
    ตอบเป็น JSON เท่านั้น: {{"province":"...", "district":"..."}}
    
    ข้อความที่ต้องวิเคราะห์:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        
        # Regex extraction for robustness
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return str(data.get("province") or "ไม่ระบุ"), str(data.get("district") or "ไม่ระบุ")
        else:
            print(f"   ⚠️ AI Debug: พิกัดระบุไม่ได้ (Raw: {res_text})")
    except Exception as e:
        if "403" in str(e):
            print("   ❌ AI Error: API Key โดนแบน (Leaked/Expired). กรุณาเปลี่ยน Key ใน ghost_config.py")
        else:
            print(f"   ⚠️ AI Error: {e}")
            
    return "ไม่ระบุ", "ไม่ระบุ"

def verify_api_connectivity():
    """
    [FUNCTION: Pre-Flight AI Check]
    ทำหน้าที่: ตรวจสอบความถูกต้องของ API Key ก่อนเริ่มงานจริง
    """
    if not HAS_AI:
        return False, "Gemini Library not installed."
        
    try:
        # ส่งข้อความทดสอบสั้นๆ เพื่อเช็คสิทธิ์ (Auth Check)
        test_response = model.generate_content("Ping")
        if test_response.text:
            return True, "AI Online & API Key Valid ✅"
    except Exception as e:
        if "403" in str(e):
            return False, "API Key โดนแบน (Leaked/Expired). กรุณาเปลี่ยน Key ใน ghost_config.py ❌"
        return False, f"API Connection Error: {str(e)} ❌"
    
    return False, "Unknown AI Connectivity Issue ❌"
