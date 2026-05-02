import re
import json
import os

RTF_FILE = "/Users/your_username/Desktop/ลิงค์สำหรับเข้ากลุ่ม.rtf"
OUTPUT_FILE = "/Users/your_username/Desktop/untitled folder/status_tracker.json"

def extract_links_from_rtf(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []
        
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # More inclusive regex for various Facebook subdomains
    pattern = r"https?://[a-zA-Z0-9.-]*facebook\.com/groups/[a-zA-Z0-9.-]+"
    links = re.findall(pattern, content)
    
    # Remove duplicates while preserving order
    unique_links = []
    seen = set()
    for link in links:
        # Clean up in case of trailing slashes or backslashes from RTF
        clean_link = link.rstrip('\\/').strip()
        if clean_link not in seen:
            unique_links.append(clean_link)
            seen.add(clean_link)
            
    return unique_links

def update_status_tracker(links):
    # Load existing status if any
    data = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}
            
    # Add new links with 'pending' status
    for link in links:
        if link not in data:
            data[link] = {
                "status": "pending",
                "last_checked": None,
                "notes": ""
            }
            
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully tracked {len(data)} total links. {len(links)} unique links extracted from RTF.")

if __name__ == "__main__":
    links = extract_links_from_rtf(RTF_FILE)
    update_status_tracker(links)
