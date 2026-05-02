import google.generativeai as genai
import config
import sys

def check_key():
    print("="*40)
    print("🔍 AI API KEY VERIFICATION")
    print("="*40)
    
    api_key = config.GEMINI_API_KEY
    model_name = config.MODEL_NAME
    
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY is not set in config.py")
        return False
        
    print(f"[*] Testing Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"[*] Target Model: {model_name}")
    
    try:
        genai.configure(api_key=api_key)
        # Minimal check: list models or just try a simple generation
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Ping")
        
        if response.text:
            print("✅ SUCCESS: AI Key is valid and working!")
            print(f"[*] Response received: {response.text.strip()}")
            print("="*40)
            return True
        else:
            print("⚠️ WARNING: Received empty response from AI.")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print("\n" + "!"*40)
        print("❌ FAILED: AI Key is invalid or expired!")
        print(f"Reason: {error_msg}")
        print("!"*40 + "\n")
        
        if "API_KEY_INVALID" in error_msg:
            print("💡 TIP: Check if you copied the key correctly.")
        elif "expired" in error_msg.lower():
            print("💡 TIP: This key has expired. Please create a new one at Google AI Studio.")
        elif "quota" in error_msg.lower():
            print("💡 TIP: You have reached your API quota. Wait a bit or check your limits.")
            
        print("="*40)
        return False

if __name__ == "__main__":
    check_key()
