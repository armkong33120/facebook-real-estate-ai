import re
import os

def extract():
    input_file = "[LINE]ส่งลิงค์ทรัพย์ Facebook.txt"
    output_file = "missing_images_links.txt"
    
    if not os.path.exists(input_file):
        print(f"❌ Not found: {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pairs = []
    current_url = None
    current_ba = None
    
    # Regex for BA codes: Handles "BA 7488", "BA. 7504", "ฺBA 7778", etc.
    ba_pattern = re.compile(r'(?:BA|ฺBA)\W*(\d+)', re.IGNORECASE)
    # Regex for URLs
    url_pattern = re.compile(r'https?://(?:www\.|m\.|mbasic\.)?facebook\.com/\S+')

    for line in lines:
        urls = url_pattern.findall(line)
        bas = ba_pattern.findall(line)
        
        if urls:
            # If we already have a BA waiting, pair it
            if current_ba:
                pairs.append((current_ba, urls[0]))
                current_ba = None
            else:
                current_url = urls[0]
        
        if bas:
            ba_str = f"BA {bas[0]}"
            # If we already have a URL waiting, pair it
            if current_url:
                pairs.append((ba_str, current_url))
                current_url = None
            else:
                current_ba = ba_str

    # De-duplicate while preserving order
    seen = set()
    unique_pairs = []
    for ba, url in pairs:
        if ba not in seen:
            unique_pairs.append(f"{ba} | {url}")
            seen.add(ba)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(unique_pairs))
    
    print(f"✅ Extracted {len(unique_pairs)} unique links to {output_file}")

if __name__ == "__main__":
    extract()
