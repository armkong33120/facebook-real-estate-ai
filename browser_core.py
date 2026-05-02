import os
import subprocess
import time
import config

# Path ของ Google Chrome for Testing บนเครื่องคุณ
CHROME_BINARY = "/Users/your_username/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

def kill_existing_chrome():
    """สั่งปิด Google Chrome for Testing และกระบวนการที่ค้างอยู่ที่ Port 9222"""
    print("[System] กำลังล้างระบบที่ค้างคาเพื่อความเสถียร...")
    try:
        # ปิด Chrome ทุกตัวที่ชื่อ "Google Chrome for Testing"
        subprocess.run(["pkill", "-f", "Google Chrome for Testing"], stderr=subprocess.DEVNULL)
        # หมายเหตุ: เราจะไม่ kill port 9222 เพราะอาจจะกวนการทำงานของ IDE (Antigravity)
        # เราจะใช้ Port 9292 แทนในการทำงาน
        time.sleep(3) 
    except:
        pass

def launch_independent_browser(url="about:blank"):
    """
    เปิด Google Chrome for Testing แบบอิสระ (Launch & Detach)
    """
    # 1. ล้างตัวเก่าก่อนเสมอ
    kill_existing_chrome()
    
    # 2. เตรียมคำสั่งรัน
    cmd = [
        CHROME_BINARY,
        f"--user-data-dir={config.USER_DATA_DIR}",
        "--remote-debugging-port=9292",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-notifications",
        "--disable-popup-blocking",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        f"--window-size={config.VIEWPORT_WIDTH},{config.VIEWPORT_HEIGHT}",
        "--start-maximized",
        url
    ]
    
    try:
        # เปิดแบบอิสระ ไม่รอให้สคริปต์จบ
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[System] เปิด Browser เรียบร้อยที่ URL: {url}")
        time.sleep(3) # รอให้หน้าต่าง Browser ปรากฏ (กิจกรรม 3 วิ)
        return True
    except Exception as e:
        print(f"[Error] ไม่สามารถเปิด Browser ได้: {str(e)}")
        return False


if __name__ == "__main__":
    launch_independent_browser()
