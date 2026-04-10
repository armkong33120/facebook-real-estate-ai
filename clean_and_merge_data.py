import re
import os

def clean_and_merge():
    # Paths to the 4 files
    files = [
        "/Users/pattharawadee/Desktop/untitled folder/[LINE]ส่งลิงค์ทรัพย์ Facebook.txt",
        "/Users/pattharawadee/Downloads/[LINE]ส่งลิงค์ทรัพย์🌊จ.ชลบุรี.txt",
        "/Users/pattharawadee/Downloads/[LINE]ส่งลิงค์ทรัพย์ Facebook กรุงเทพ.txt",
        "/Users/pattharawadee/Downloads/[LINE]ส่งลิงค์ทรัพย์🗻จ.เชียงใหม่.txt"
    ]
    
    output_file = "/Users/pattharawadee/Desktop/untitled folder/missing_images_links.txt"
    
    # Negative keywords that trigger exclusion
    negative_patterns = [
        "ไม่ต้องโพสต์", "ไม่ให้โพสต์", "ไม่ต้องโพส", "ไม่ให้โพส",
        "ไม่รับเอเจนท์", "ไม่รับ agent", "owner only", "ไม่ต้องทัก",
        "ติดจอง", "ขายแล้ว", "เช่าแล้ว", "ปิดประกาศ", "ลบ", "งด"
    ]
    
    ba_pattern = re.compile(r'(?:BA|BC|BM|ฺBA)\W*(\d+)', re.IGNORECASE)
    url_pattern = re.compile(r'https?://(?:www\.|m\.|mbasic\.|web\.)?facebook\.com/\S+')
    
    all_valid_listings = {} # Code -> URL
    blacklisted_codes = set()
    total_found = 0
    total_excluded = 0

    for file_path in files:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            continue
            
        print(f"🔍 Processing: {os.path.basename(file_path)}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_url = None
        current_ba = None
        
        for i, line in enumerate(lines):
            # Check for negative keywords in this line
            has_negative = any(neg in line for neg in negative_patterns)
            
            urls = url_pattern.findall(line)
            bas = ba_pattern.findall(line)
            
            # If negative keyword found, blacklist the current BA or the immediate previous/next BA
            if has_negative:
                if current_ba:
                    blacklisted_codes.add(current_ba)
                    if current_ba in all_valid_listings:
                        del all_valid_listings[current_ba]
                    total_excluded += 1
                # Also check a few lines back just in case the "don't post" is right after a BA mention in a separate line
                for j in range(max(0, i-2), i):
                    prev_bas = ba_pattern.findall(lines[j])
                    if prev_bas:
                        code = f"{file_path[:2]} {prev_bas[0]}" # Simplified prefix tracking
                        # More direct: extract the exact prefix from the found text
                        # Wait, a better way: extract full BA XXXX
                        full_code_match = re.search(r'(?:BA|BC|BM|ฺBA)\W*\d+', lines[j], re.I)
                        if full_code_match:
                            code = full_code_match.group(0).upper().replace(".", "").replace(" ", " ")
                            # Normalize "BA  7489" to "BA 7489"
                            code = " ".join(code.split())
                            blacklisted_codes.add(code)
                            if code in all_valid_listings:
                                del all_valid_listings[code]
                                total_excluded += 1

            if urls:
                if current_ba:
                    if current_ba not in blacklisted_codes:
                        all_valid_listings[current_ba] = urls[0]
                        total_found += 1
                    current_ba = None
                else:
                    current_url = urls[0]
            
            if bas:
                # Get the full original string like "BA 7488"
                code_match = ba_pattern.search(line)
                if code_match:
                    code = code_match.group(0).upper().replace(".", "").replace(" ", " ")
                    code = " ".join(code.split())
                    
                    if current_url:
                        if code not in blacklisted_codes:
                            all_valid_listings[code] = current_url
                            total_found += 1
                        current_url = None
                    else:
                        current_ba = code

    # Final cleanup: Remove any from blacklist that might have slipped in
    for bc in blacklisted_codes:
        if bc in all_valid_listings:
            del all_valid_listings[bc]

    # Sort items and write output
    sorted_items = sorted(all_valid_listings.items())
    with open(output_file, 'w', encoding='utf-8') as f:
        for code, url in sorted_items:
            f.write(f"{code} | {url}\n")
            
    print("\n" + "="*40)
    print(f"📊 SUMMARY:")
    print(f"✅ Total Valid Listings: {len(all_valid_listings)}")
    print(f"❌ Total Excluded (Filters): {len(blacklisted_codes)}")
    print(f"📂 Output written to: missing_images_links.txt")
    print("="*40)

    # Show first 5 excluded codes for verification
    if blacklisted_codes:
        print("\n🔍 Sample of excluded codes (for verification):")
        for bc in list(blacklisted_codes)[:5]:
            print(f"- {bc}")

if __name__ == "__main__":
    clean_and_merge()
