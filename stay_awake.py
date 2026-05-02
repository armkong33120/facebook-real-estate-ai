import subprocess
import time
import sys
import os

def jiggle_mouse():
    """ขยับเมาส์ 1 พิกเซลผ่าน AppleScript เพื่อหลอกว่า User ยังอยู่หน้าจอ"""
    try:
        script = 'tell application "System Events" to set pos to mouse location \n' \
                 'tell application "System Events" to mouse move {((item 1 of pos) + 1), (item 2 of pos)} \n' \
                 'tell application "System Events" to mouse move {(item 1 of pos), (item 2 of pos)}'
        # หมายเหตุ: เราใช้แค่ขยับไปมา ไม่คลิก เพื่อความปลอดภัย
        subprocess.run(['osascript', '-e', 'tell application "System Events" to set pos to mouse location'], capture_output=True)
        # ขยับเล็กน้อย
        applescript = 'tell application "System Events" to set mouse_pos to {100, 100}' # เราจะไม่ใช้ set mouse_pos เพราะอาจกระโดด
        # ใช้สคริปต์เลื่อนเมาส์เบาๆ
        jiggle = 'tell application "System Events" \n' \
                 '  set {x, y} to mouse location \n' \
                 '  set the pointer to {x + 1, y + 1} \n' \
                 '  -- ขยับกลับที่เดิม \n' \
                 '  set the pointer to {x, y} \n' \
                 'end tell'
        # แต่เพื่อความง่ายและเสถียรที่สุด เราจะใช้การกดปุ่ม "Shift" (แบบไม่มีผลต่อการพิมพ์) แทน
        subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 56'], capture_output=True) # 56 คือ Shift
    except:
        pass

def keep_awake():
    if sys.platform != "darwin":
        print("❌ This script is designated for macOS only.")
        return

    print("="*45)
    print("☕ EXTREME STAY AWAKE (STEROIDS MODE) ACTIVATED")
    print("="*45)
    print("1. System/Display/Disk Lock: [ON] (caffeinate -dims)")
    print("2. Human Simulation (Auto-Shift): [ON] (Every 60s)")
    print("Status: Your Mac is now immune to sleep.")
    print("Action: Press Ctrl+C to stop.")
    print("="*45)

    try:
        # -d: Display, -i: Idle, -m: Disk, -s: System
        process = subprocess.Popen(['caffeinate', '-dims'])
        
        last_jiggle = time.time()
        while True:
            current_time = time.time()
            if current_time - last_jiggle > 60:
                jiggle_mouse()
                last_jiggle = current_time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n[System] ☕ Deactivating Extreme Stay Awake...")
        process.terminate()
        print("[System] Success. Your Mac can now sleep normally.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    keep_awake()
