import os
import json
import time
import google.generativeai as genai
import config

# Configuration
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "group_analysis.json")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "owner_only_groups_to_leave.txt")

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel(config.MODEL_NAME)

def is_agent_prohibited(name, rules):
    """Uses AI to determine if the group forbids agents/brokers"""
    if not rules: return False
    
    prompt = f"""
    วิเคราะห์ว่ากลุ่ม Facebook นี้อนุญาตให้ "เอเจนท์ (Agent)" หรือ "นายหน้า" โพสต์ได้หรือไม่?
    
    ชื่อกลุ่ม: {name}
    กฎของกลุ่ม: {rules}
    
    กติกาการตอบ:
    - หากมีคำสั่งชัดเจนว่า "ห้ามเอเจนท์", "เฉพาะเจ้าของเท่านั้น", "Owner Only", "No Agents" ให้ตอบว่า YES
    - หากอนุญาตให้เอเจนท์โพสต์ได้ หรือเป็นกลุ่มทั่วไป ให้ตอบว่า NO
    
    คำตอบ (YES/NO):
    """
    try:
        response = model.generate_content(prompt)
        res_text = response.text.upper()
        return "YES" in res_text and "NO" not in res_text[:res_text.find("YES")] # Basic sanity check
    except Exception as e:
        print(f"      ⚠️ AI Error: {str(e)}")
        return False

def run_filter():
    print("\n" + "="*50)
    print("🔍 Filtering Agent-Prohibited Groups (Owner Only) - FIXED")
    print("="*50)
    
    if not os.path.exists(DATA_FILE):
        print("❌ Error: group_analysis.json not found.")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Initialize agent_checked field if not exists to allow resuming correctly
    for url in data:
        if "agent_checked" not in data[url]:
            data[url]["agent_checked"] = False

    # Filter only those not checked yet
    to_process = [url for url, info in data.items() if not info.get("agent_checked")]
    total_to_process = len(to_process)
    total_all = len(data)

    print(f"📊 Total groups in database: {total_all}")
    print(f"🔎 Remaining to scan: {total_to_process}")
    print("-" * 50)

    removed_count = 0
    checked_count = 0
    batch_removed_text = []
    
    try:
        for url in to_process:
            checked_count += 1
            g_info = data[url]
            name = g_info['name']
            rules = g_info.get('rules', '')
            
            print(f"[{checked_count}/{total_to_process}] Checking: {name[:40]}...")
            
            if is_agent_prohibited(name, rules):
                print("      🚫 PROHIBITED: Marked for removal.")
                batch_removed_text.append(f"NAME: {name}\nLINK: {url}\nRULES: {rules[:200]}...\n{'-'*50}\n")
                data[url]["agent_prohibited"] = True
                removed_count += 1
            else:
                data[url]["agent_prohibited"] = False
            
            data[url]["agent_checked"] = True # Mark as checked
            
            # Auto-save every 10 groups
            if checked_count % 10 == 0:
                # Save the full data structure
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                # Append to the text file
                if batch_removed_text:
                    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                        f.writelines(batch_removed_text)
                    batch_removed_text = []
                    
                print(f"      📂 Progress saved. (Total in DB: {len(data)})")
            
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user. Saving progress...")
    
    # Final cleaning: Remove 'agent_prohibited' items from group_analysis.json and save
    final_data = {url: info for url, info in data.items() if not info.get("agent_prohibited", False)}
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)
    
    if batch_removed_text:
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            f.writelines(batch_removed_text)

    print("\n" + "="*50)
    print(f"🎉 FILTERING COMPLETE!")
    print(f"✅ Groups Remaining in DB: {len(final_data)}")
    print(f"❌ Groups Removed this session: {removed_count}")
    print(f"📄 Removal list: {OUTPUT_FILE}")
    print("="*50)

if __name__ == "__main__":
    run_filter()
