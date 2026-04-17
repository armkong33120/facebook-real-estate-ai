import requests
import json

# --- LINE API CONFIGURATION ---
CHANNEL_ACCESS_TOKEN = "JuAV79Vh4d0TRxKT1q+d7ASxFRDmOB3hBZ/HUCqaH4151Ov7p0ZhmBzK158JzVo/7K0r96suN4EuHcSBl2RpamYxgNwzQqZnvdqIWmtRaD0XUOjh2oxNxi0ORDXwNJG8NgaGY3BFZd/hmD6V8J4rsAdB04t89/1O/w1cDnyilFU="
USER_ID = "Uafa952990297fbb9a124a9aa88657570"

def send_line_message(message_text):
    """
    ส่งข้อความผ่าน LINE Messaging API (Push Message)
    """
    url = "https://api.line.me/v2/bot/message/push"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    
    payload = {
        "to": USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return True
        else:
            print(f"[LINE Error] Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[LINE Exception] {str(e)}")
        return False

if __name__ == "__main__":
    # ทดสอบส่งข้อความ
    test_msg = "🤖 GHOST AGENT: ระบบแจ้งเตือนเชื่อมต่อสำเร็จแล้วครับคุณพี่! ✨"
    if send_line_message(test_msg):
        print("ส่งข้อความทดสอบสำเร็จ!")
    else:
        print("ส่งข้อความทดสอบล้มเหลว")
