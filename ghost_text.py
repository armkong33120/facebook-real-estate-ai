import re

def clean_property_text(text, ba):
    """
    [FUNCTION: Deep Purge Sanitizer]
    ทำหน้าที่: ล้างข้อมูลเอเจ้นท์เดิม และใส่ลายเซ็นของคุณกวงแทน
    หากต้องการเปลี่ยนเบอร์ติดต่อ: แก้ไขที่ signature ด้านล่างนี้ครับ
    """
    # 1. ลบเบอร์โทรศัพท์ทิ้งทั้งหมด (Regex)
    text = re.sub(r'\d{2,3}[-\s]?\d{3,4}[-\s]?\d{3,4}', '', text)
    
    # 2. รายการคำต้องฆ่า (Kill Keywords)
    kill_keywords = [
        'ติดต่อสอบถามรายละเอียด', 'ติดต่อสอบถาม', 'สอบถามรายละเอียด', 'ทักแชท', 'ทัก Inbox',
        'สนใจติดต่อ', 'ติดต่อได้ที่', 'รับเอเจ้น', 'Agent', 'Owner', 'เจ้าของโพสเอง', 
        'รับAgent', 'รับโค้เบอร์', 'รับCo-agent', 'สอบถามเพิ่มเติม', 'นัดชมห้อง', 'แอดไลน์'
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        s_line = line.strip()
        # ข้ามบรรทัดว่าง หรือบรรทัดที่มี Keyword ต้องห้าม
        if not s_line or any(k in s_line for k in kill_keywords):
            continue
            
        # ลบชื่อเล่นที่มักอยู่ในวงเล็บ หรือ 'คุณ...'
        line_clean = re.sub(r'\(K\..*?\)', '', s_line)
        line_clean = re.sub(r'คุณ\s*[\u0E00-\u0E7F]+', '', line_clean)
        line_clean = re.sub(r'\(.*?\)', '', line_clean)
        line_clean = re.sub(r'[คะค่ะ]+\s*$', '', line_clean.strip())
        
        final_line = line_clean.strip()
        if final_line and len(final_line) > 1:
            cleaned_lines.append(final_line)
    
    # 3. ใส่ลายเซ็น Professional (Signature)
    signature = f"""
━━━━━━━━━━━━━━━
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
{ba}
"""
    return '\n'.join(cleaned_lines) + signature
