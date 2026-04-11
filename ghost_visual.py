import io
import hashlib
from PIL import Image

def get_image_hash(img_data):
    """คำนวณค่า MD5 Hash ของข้อมูลรูปภาพดิบ เพื่อใช้ตรวจจับรูปซ้ำ"""
    return hashlib.md5(img_data).hexdigest()

def hash_tweak_save(img_data, save_path):
    """
    [FUNCTION: Image Hash Tweaker]
    ทำหน้าที่: บันทึกรูปภาพพร้อมปรับค่า 1 พิกเซล (Lossless) 
    เพื่อให้ Hash ID ของรูปเปลี่ยนไป ป้องกันการโดนตรวจจับว่าซ้ำ
    """
    try:
        img = Image.open(io.BytesIO(img_data))
        img = img.convert("RGB")
        
        # คัดลอกข้อมูลพิกเซล (Lossless)
        data = list(img.getdata())
        image_out = Image.new("RGB", img.size)
        image_out.putdata(data)
        
        # ปรับค่า 1 พิกเซลที่มุม (0,0) เล็กน้อย (+1) แทบมองไม่เห็นด้วยตาเปล่า
        r, g, b = image_out.getpixel((0,0))
        image_out.putpixel((0,0), ((r + 1) % 256, g, b))
        
        # บันทึกเป็น JPEG คุณภาพสูง
        image_out.save(save_path, "JPEG", quality=95, optimize=True)
        return True
    except Exception as e:
        print(f"   ⚠️ Visual Error: บันทึกรูปไม่สำเร็จ - {e}")
        return False
