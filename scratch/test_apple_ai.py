import sys
import asyncio

try:
    import apple_fm_sdk as fm
    print("✅ พบการติดตั้งไลบรารี apple_fm_sdk บนเครื่อง")
except ImportError:
    print("❌ แจ้งเตือน: ไม่พบโมดูล 'apple_fm_sdk'")
    print("กำลังพยายามติดตั้งผ่าน pip...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "apple-fm-sdk"])
    try:
        import apple_fm_sdk as fm
    except ImportError:
         print("❌ การติดตั้งล้มเหลว โปรดตรวจสอบให้แน่ใจว่าได้ติดตั้ง Xcode รุ่นล่าสุดแล้ว")
         sys.exit(1)

async def test_apple_intelligence():
    print("⏳ กำลังตรวจสอบ Apple Intelligence System ...")
    
    try:
        model = fm.SystemLanguageModel()
        # เช็คความพร้อมของโมเดล
        # ตาม document อาจจะไม่มี parameter กลับมาเป็น tuple แต่จะส่งค่า boolean มาอย่างเดียวก็เป็นได้ 
        # จึงป้องกัน Error โดยให้เช็คว่ามันคืนค่าแบบไหน
        status = model.is_available()
        
        is_ready = status[0] if isinstance(status, tuple) else status
        error_msg = status[1] if isinstance(status, tuple) else "Not available on this device"
        
        if is_ready:
            print("✅ สุดยอด! เครื่อง Mac ของคุณเชื่อมต่อ Foundation Model ของ Apple ได้สำเร็จ")
            session = fm.LanguageModelSession()
            
            prompt = "ขอประโยคสั้นๆ 1 ประโยค ให้กำลังใจคนที่เขียนโปรแกรมมาทั้งวัน"
            print(f"👉 กำลังส่งคำสั่งไปที่ AI บนเครื่อง: '{prompt}'")
            
            response = await session.respond(prompt)
            print("\n🤖 ==================================")
            print(f"ข้อความจาก Apple Intelligence:")
            print(f"{response}")
            print("==================================\n")
        else:
            print(f"❌ เครื่องไม่พร้อมเรียกใช้ System Model: {error_msg}")
            
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาดระหว่างรันคำสั่ง: {e}")

if __name__ == "__main__":
    print("\n--- เริ่มต้นสคริปต์ Debug Apple Intelligence (Isolated Test) ---")
    asyncio.run(test_apple_intelligence())
