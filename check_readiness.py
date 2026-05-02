import os
import sys
import subprocess
import time
import json
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# Import local config
try:
    import config
    import browser_core
except ImportError:
    print("❌ Error: config.py or browser_core.py not found in the current directory.")
    sys.exit(1)

def print_step(msg):
    print(f"\n🔍 [Step] {msg}...")

def check_python():
    print(f"   - Python version: {sys.version}")
    return True

def check_dependencies():
    missing = []
    try:
        import playwright
    except ImportError: missing.append("playwright")
    try:
        import google.generativeai
    except ImportError: missing.append("google-generativeai")
    
    if missing:
        print(f"   ❌ Missing libraries: {', '.join(missing)}")
        return False
    print("   ✅ All Python dependencies are present.")
    return True

def check_browser_path():
    chrome_path = browser_core.CHROME_BINARY
    if os.path.exists(chrome_path):
        print(f"   ✅ Chrome for Testing found at: {chrome_path}")
        # Check permissions
        if not os.access(chrome_path, os.X_OK):
            print("   ❌ Error: Chrome binary is not executable.")
            return False
        return True
    else:
        print(f"   ❌ Error: Chrome for Testing NOT FOUND at: {chrome_path}")
        return False

def check_profile():
    profile_path = config.USER_DATA_DIR
    if os.path.exists(profile_path):
        print(f"   ✅ Browser profile folder exists: {profile_path}")
    else:
        print(f"   ⚠️ Warning: Browser profile folder not found. It will be created on first run.")
    return True

def check_ai_key():
    print("   - Validating Gemini API Key...")
    genai.configure(api_key=config.GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel(config.MODEL_NAME)
        # Low token ping
        model.generate_content("Ping", generation_config={"max_output_tokens": 1})
        print("   ✅ AI API Key is valid and working.")
        return True
    except Exception as e:
        print(f"   ❌ AI API Key Error: {str(e)}")
        return False

def run_all_checks():
    print("="*50)
    print("🛡️  FB BOT READINESS & DIAGNOSTIC CHECK")
    print("="*50)
    
    success = True
    
    print_step("Python Environment")
    if not check_python(): success = False
    
    print_step("Dependencies")
    if not check_dependencies(): success = False
    
    print_step("Browser Configuration")
    if not check_browser_path(): success = False
    if not check_profile(): pass # Non-fatal
    
    print_step("AI Service")
    if not check_ai_key(): success = False
    
    print("\n" + "="*50)
    if success:
        print("🎉 STATUS: READY TO LAUNCH!")
        print("คุณสามารถรัน 'python3 fb_group_collector.py' ได้เลยครับ")
    else:
        print("❌ STATUS: NOT READY")
        print("กรุณาแก้ไขข้อผิดพลาดด้านบนก่อนรันบอทครับ")
    print("="*50)

if __name__ == "__main__":
    run_all_checks()
