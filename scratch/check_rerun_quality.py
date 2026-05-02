import os

links_file = "rerun_links.txt"
base_path = "/Users/your_username/Desktop/Facebook_Property_Data"

if not os.path.exists(links_file):
    print(f"Error: {links_file} not found")
    exit(1)

# Extract IDs from rerun_links.txt
rerun_ids = []
with open(links_file, "r", encoding="utf-8") as f:
    for line in f:
        if " | " in line:
            rerun_ids.append(line.split(" | ")[0].strip())

total_in_list = len(rerun_ids)
found_folders = 0
low_quality = 0
broken = 0

# Map folders by ID
id_to_img_count = {}
for root, dirs, files in os.walk(base_path):
    for d in dirs:
        if d.startswith("BA "):
            folder_path = os.path.join(root, d)
            images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
            id_to_img_count[d] = len(images)

# Check rerun IDs against found folders
failed_list = []
for rid in rerun_ids:
    if rid in id_to_img_count:
        found_folders += 1
        count = id_to_img_count[rid]
        if count < 5:
            low_quality += 1
            if count == 0:
                broken += 1
            failed_list.append((rid, count))

print(f"Total IDs in Rerun List: {total_in_list}")
print(f"Already Processed (Folders exist): {found_folders}")
print(f"--- Statistics for Processed Items ---")
print(f"Good Quality (>=5): {found_folders - low_quality}")
print(f"Failed/Low Quality (<5): {low_quality}")
print(f"Broken (0 images): {broken}")
if found_folders > 0:
    print(f"Quality Success Rate: {((found_folders - low_quality)/found_folders)*100:.2f}%")
    print(f"Failure Rate: {(low_quality/found_folders)*100:.2f}%")
