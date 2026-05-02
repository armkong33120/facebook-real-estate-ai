from google import genai
import config

try:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    AI_AVAILABLE = True
except Exception as e:
    AI_AVAILABLE = False

def check_ai_status():
    """ตรวจสอบการทำงานของ AI"""
    if not AI_AVAILABLE:
        return False, "AI Not Ready"
    try:
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents="Ping AI"
        )
        return True, "AI Online"
    except Exception as e:
        return False, str(e)

def extract_json_from_text(text):
    """สกัด JSON ออกจากข้อความ (ลบ Markdown code blocks ออกถ้ามี)"""
    import re
    import json
    # พยายามหา { ... }
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        json_str = match.group(1)
        # ลบ ```json ... ``` ออกถ้ามี
        json_str = re.sub(r'```json|```', '', json_str).strip()
        try:
            return json.loads(json_str)
        except:
            return None
    return None

def clean_property_text(raw_text, property_id, property_link):
    """
    ใช้ AI ในการลบข้อมูลติดต่อเดิมออก และจัดเรียงใหม่ตาม Template ที่กำหนด
    เน้นการคัดกรองคำขยะตามความต้องการของผู้ใช้
    """
    if not AI_AVAILABLE:
        return raw_text
    
    prompt = f"""
    ช่วยจัดเรียงข้อมูลประกาศอสังหาริมทรัพย์ใหม่ โดยทำตามกฎเหล็กดังนี้:
    1. ลบคำว่า "Owner Post!! (ยินดีรับเอเจนท์)", "Owner Post", "Agent Welcome" หรือคำในทำนองนี้ทิ้งให้หมด
    2. ลบข้อมูลติดต่อเดิม (เบอร์โทร, Line, FB, IG, TikTok) ของเจ้าของโพสต์หรือ Agent เดิมออกให้หมด
    3. ห้ามใส่ Link ภายนอกใดๆ เพิ่มเติมโดยเด็ดขาด (ห้ามใส่ลิงก์โพสต์ต้นฉบับ) เว้นแต่ลิงก์นั้นจะมีมากับข้อความในโพสต์ตั้งแต่แรกอยู่แล้ว
    4. จัดเรียงข้อมูลตัวทรัพย์ (ราคา, ขนาด, ทำเล, รายละเอียด) ให้ดูสะอาดและเป็นระเบียบตามตัวอย่าง
    
    ข้อมูลติดต่อใหม่ที่ต้องใส่ไว้ด้านล่าง:
    สนใจติดต่อ:
    📞 Contact โทรศัพท์
    • 094-946-3652 (คุณกวง / Khun Kuang)
    • 094-242-6936 (คุณหนิง / Khun Ning)
    • 089-496-5451 (คุณพัด / Khun Pat)
    • 06-5090-7257 (Office)
    ━━━━━━━━━━━━━━━
    💬 ช่องทางออนไลน์
    • WhatsApp : +66949463652
    • WeChat: kuanghuiagent
    • LINE: @benchamas_estate (with @)
    • {property_id}

    ข้อความต้นฉบับ:
    {raw_text}
    
    ส่งกลับมาเฉพาะข้อความที่จัดเรียงใหม่แล้วเท่านั้น ไม่ต้องมีคำเกริ่นใดๆ
    """
    
    import time
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=config.MODEL_NAME,
                contents=prompt
            )
            import re
            cleaned = response.text.strip()
            # ตัด URL ทุกประเภทออก (http/https และ facebook links)
            cleaned = re.sub(r'https?://[^\s<>"]+|www\.[^\s<>"]+', '', cleaned)
            cleaned = re.sub(r'facebook\.com/[^\s<>"]+', '', cleaned)
            return cleaned
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                print(f"[AI] ระบบไม่ว่าง (503) กำลังลองใหม่รอบที่ {attempt + 1}/3...")
                time.sleep(3)
                continue
            return f"Error cleaning text: {str(e)}"

def evaluate_property_relevance(image_path, post_text):
    """
    ดวงตา AI: ตรวจสอบรูปภาพแรกเทียบกับข้อความเพื่อวิเคราะห์ความน่าจะเป็น
    """
    if not AI_AVAILABLE:
        return {"confidence": 100, "decision": True, "reason": "AI Not Available - Bypassing"}

    from PIL import Image
    try:
        # เปิดไฟล์ภาพ
        img = Image.open(image_path)
        
        prompt = f"""
        คุณคือผู้ช่วยตรวจสอบรูปภาพอสังหาริมทรัพย์ หน้าที่ของคุณคือวิเคราะห์รูปภาพนี้เทียบกับข้อความประกาศ
        
        ข้อความประกาศ:
        {post_text}
        
        กฎการพิจารณา:
        1. ให้น้ำหนักความเป็นรูปทรัพย์ (Real Estate) เป็นหลัก (บ้าน, ห้องนอน, ครัว, ยิม, ผังห้อง, วิว)
        2. หากเป็นรูป "คน", "โปรไฟล์หน้าคน", "ใบปลิวโฆษณาที่มีตัวหนังสือเยอะ", "รูปกราฟิกเพจข่าว", หรือรูป UI อื่นๆ ให้ถือเป็นขยะ (GARBAGE)
        3. ให้คะแนนความมั่นใจ (Confidence Score) 0-100% ว่ารูปนี้คือสิ่งที่ประกาศขาย/เช่าจริงหรือไม่
        
        ส่งกลับมาเป็น JSON เท่านั้น:
        {{
            "confidence": (ตัวเลข 0-100),
            "decision": (true/false),
            "reason": "สรุปสั้นๆ ว่าทำไม"
        }}
        """
        
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=[prompt, img],
            config={"response_mime_type": "application/json"}
        )
        data = extract_json_from_text(response.text)
        if not data:
            return {"confidence": 50, "decision": True, "reason": "JSON Parse Error - Bypassing"}
        return data
    except Exception as e:
        print(f"[AI Error] การตรวจสอบภาพล้มเหลว: {str(e)}")
        return {"confidence": 50, "decision": True, "reason": "Error check - defaulting to True"}

def parse_address(property_text):
    """
    ใช้ AI วิเคราะห์หา จังหวัด และ เขต/อำเภอ โดยใช้ตรรกะการตรวจสอบตำแหน่งที่ตั้งที่แม่นยำ
    """
    if not AI_AVAILABLE:
        return {"province": "ไม่ทราบ", "district": "ไม่ทราบ"}
    
    prompt = f"""
    คุณเป็นผู้เชี่ยวชาญด้านภูมิศาสตร์ประเทศไทย หน้าที่ของคุณคือระบุตำแหน่งของอสังหาริมทรัพย์นี้ให้แม่นยำที่สุด
    
    ขั้นตอนการคิด (Thinking Process):
    1. ค้นหาชื่อโครงการ หรือ จุดเช็คอินในข้อความ (เช่น 'A Space Me นนทบุรี', 'Perfect Place กรุงเทพกรีฑา')
    2. ค้นหาที่อยู่โดยละเอียด เช่น ชื่อถนน, ซอย, ตำบล
    3. ใช้ฐานข้อมูล AI ปี 2026 ของคุณเพื่อระบุว่าสถานที่นั้นตั้งอยู่ใน "จังหวัด" และ "เขต/อำเภอ" อะไร (เอาที่อยู่เต็มๆ มาก่อน แล้วค่อยสกัดเฉพาะพิกัดหลัก)
    
    ข้อความประกาศ:
    {property_text}
    
    ส่งกลับมาในรูปแบบ JSON เท่านั้น:
    {{
      "province": "ชื่อจังหวัด (เช่น กรุงเทพมหานคร, นนทบุรี)",
      "district": "ชื่อเขตหรืออำเภอ เท่านั้น (เช่น ราชเทวี, เมืองนนทบุรี)"
    }}
    ห้ามใส่คำว่า 'เขต' หรือ 'อำเภอ' นำหน้าชื่อ ถ้าเป็นกรุงเทพฯ ให้ตอบชื่อเขตตรงๆ
    หากหาไม่พบให้ใส่คำว่า "ไม่ทราบ"
    """
    
    try:
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        data = extract_json_from_text(response.text)
        if not data:
            return {"province": "ไม่ทราบ", "district": "ไม่ทราบ"}
        return data
    except Exception as e:
        return {"province": "ไม่ทราบ", "district": "ไม่ทราบ"}

def detect_album_coordinates(image_path):
    """
    ดวงตา AI ระบุตำแหน่ง: ใช้ Spatial Reasoning ในการหาพิกัดอัลบั้มรูปจากภาพหน้าจอ
    คืนค่าเป็น (x, y) ในหน่วยพิกเซลจริงเทียบกับขนาดภาพ
    """
    if not AI_AVAILABLE:
        return None

    from PIL import Image
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        prompt = """
        วิเคราะห์ภาพหน้าจอโพสต์ Facebook นี้ และระบุ Bounding Box ของ 'อัลบั้มรูปภาพ' หรือ 'รูปภาพหลักของทรัพย์' 
        ที่ผู้ใช้น่าจะคลิกเพื่อดูรูปภาพทั้งหมด
        
        ส่งกลับมาเป็น JSON ในรูปแบบพิกัดมาตรฐาน [ymin, xmin, ymax, xmax] 
        โดยค่าทั้งหมดต้อง Normalize อยู่ในช่วง 0 ถึง 1000 และเป็นตัวเลขจำนวนเต็ม
        
        ตัวอย่าง:
        { "box_2d": [450, 100, 850, 900] }
        """
        
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=[prompt, img],
            config={"response_mime_type": "application/json"}
        )
        
        data = extract_json_from_text(response.text)
        if not data:
            return None
        box = data.get("box_2d")
        
        if not box or len(box) != 4:
            return None
            
        ymin, xmin, ymax, xmax = box
        
        # คำนวณจุดกึ่งกลาง (Center) ในหน่วยพิกเซล
        center_y_norm = (ymin + ymax) / 2
        center_x_norm = (xmin + xmax) / 2
        
        target_x = (center_x_norm / 1000) * width
        target_y = (center_y_norm / 1000) * height
        
        return int(target_x), int(target_y)
        
    except Exception as e:
        print(f"[AI Vision Error] ระบุพิกัดล้มเหลว: {str(e)}")
        return None
def analyze_post_visually(image_path, property_id, property_link):
    """
    [Vision One-Shot] ฟังก์ชันเมกะ: วิเคราะห์ทุกอย่างจบในภาพเดียว
    - OCR + Clean Text
    - Location Analysis (Province/District)
    - Coordinate Detection (Album Click)
    """
    if not AI_AVAILABLE:
        return None

    from PIL import Image
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        prompt = f"""
        คุณคือผู้ช่วยอัจฉริยะด้านอสังหาริมทรัพย์ หน้าที่ของคุณคือวิเคราะห์รูปภาพหน้าจอโพสต์ Facebook นี้และสกัดข้อมูลสำคัญออกมา
        
        ภารกิจของคุณ:
        1. [OCR & CLEAN]: อ่านข้อความทั้งหมดในภาพ และจัดเรียงใหม่ตามกฎ:
           - ลบคำขยะ (Owner Post, Agent Welcome, เบอร์โทร/Line เดิม)
           - ใส่ข้อมูลติดต่อ {property_id} ของเราแทน (คุณกวง/คุณหนิง/คุณพัด)
        2. [LOCATION]: ระบุจังหวัด และ เขต/อำเภอ จากเนื้อหาในโพสต์
        3. [COORDINATES]: ระบุ Bounding Box [ymin, xmin, ymax, xmax] ของ 'อัลบั้มรูปภาพ' หรือจุดที่ต้องคลิกเพื่อดูรูปทั้งหมด (Normalize 0-1000)
        
        ข้อมูลติดต่อใหม่ของเรา:
        📞 Contact โทรศัพท์: 094-946-3652 (คุณกวง), 094-242-6936 (คุณหนิง), 089-496-5451 (คุณพัด)
        💬 LINE: @benchamas_estate (with @)
        
        ส่งกลับมาเป็น JSON เท่านั้นในรูปแบบนี้:
        {{
            "cleaned_text": "ข้อความที่จัดเรียงใหม่",
            "location": {{
                "province": "ชื่อจังหวัด",
                "district": "ชื่อชื่อเขต/อำเภอ"
            }},
            "click_box": [ymin, xmin, ymax, xmax],
            "reason": "สรุปสั้นๆ ว่าทำไมถึงเลือกจุดนี้"
        }}
        """
        
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=[prompt, img],
            config={"response_mime_type": "application/json"}
        )
        
        data = extract_json_from_text(response.text)
        if not data:
            return None
            
        # คำนวณพิกัดจาก Box
        box = data.get("click_box")
        if box and len(box) == 4:
            ymin, xmin, ymax, xmax = box
            center_y_norm = (ymin + ymax) / 2
            center_x_norm = (xmin + xmax) / 2
            data["target_x"] = int((center_x_norm / 1000) * width)
            data["target_y"] = int((center_y_norm / 1000) * height)
            
        return data
        
    except Exception as e:
        print(f"[Vision One-Shot Error]: {str(e)}")
        return None

def verify_landing_page(original_image_path, landing_image_path, url, post_context):
    """
    [Double-Check Guard] ตรวจสอบหน้าปลายทางเทียบกับหน้าโพสต์ต้นฉบับ
    """
    if not AI_AVAILABLE:
        return {"is_valid": True, "reason": "AI Not Available"}

    from PIL import Image
    try:
        # เปิดรูปทั้งสองใบ
        img_orig = Image.open(original_image_path)
        img_land = Image.open(landing_image_path)
        
        prompt = f"""
        คุณคือผู้ตรวจสอบความปลอดภัย (Guard Dog) ขั้นสูงสุด หน้าที่ของคุณคือเปรียบเทียบรูปภาพ 2 ใบนี้:
        
        รูปภาพที่ 1 (ต้นฉบับ): คือหน้าจอโพสต์ที่เราตั้งใจจะคลิก
        รูปภาพที่ 2 (ปลายทาง): คือหน้าที่ปรากฏขึ้นมาหลังจากที่เราคลิกไปแล้ว
        
        บริบทของทรัพย์: {post_context}
        URL ปลายทาง: {url}
        
        ภารกิจ:
        1. ตรวจสอบว่า รูปภาพที่ 2 คือ 'คลังรูปภาพ' (Lightbox/Gallery) ของทรัพย์ที่ระบุในรูปภาพที่ 1 หรือไม่?
        2. หากรูปภาพที่ 2 ดูเหมือนหน้าโปรไฟล์ส่วนตัวคนอื่นที่ไม่ใช่รูปทรัพย์ หรือเป็นหน้าคอมเมนต์ ให้ตอบ false
        3. หากรูปภาพที่ 2 คือคลังรูปภาพที่มีรูปบ้าน/คอนโด และมีปุ่มนำทาง (Next/Prev) ให้ตอบ true
        
        ส่งกลับมาเป็น JSON เท่านั้น:
        {{
            "is_valid": (true/false),
            "reason": "สรุปสั้นๆ ว่าทำไมถึงคิดแบบนั้น"
        }}
        """
        
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=[prompt, img_orig, img_land],
            config={"response_mime_type": "application/json"}
        )
        
        data = extract_json_from_text(response.text)
        if not data:
            return {"is_valid": True, "reason": "JSON Parse Error - Defaulting to True"}
            
        return data
        
    except Exception as e:
        print(f"[Landing Guard Error]: {str(e)}")
        return {"is_valid": True, "reason": f"Error: {str(e)}"}
