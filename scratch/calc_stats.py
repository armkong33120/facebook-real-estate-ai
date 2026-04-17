import os

base_path = "/Users/pattharawadee/Desktop/Facebook_Property_Data"
start_id = 8515
end_id = 8735
found_count = 0
low_count = 0
zero_count = 0

for root, dirs, files in os.walk(base_path):
    for d in dirs:
        if d.startswith("BA "):
            try:
                id_num = int(d.replace("BA ", ""))
                if start_id <= id_num <= end_id:
                    found_count += 1
                    folder_path = os.path.join(root, d)
                    images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
                    img_count = len(images)
                    if img_count < 5:
                        low_count += 1
                        if img_count == 0:
                            zero_count += 1
            except:
                continue

print(f"Total processed in range: {found_count}")
print(f"Items with < 5 images: {low_count}")
print(f"Items with 0 images: {zero_count}")
if found_count > 0:
    print(f"Success/Quality rate: {((found_count - low_count)/found_count)*100:.2f}%")
    print(f"Low image rate: {(low_count/found_count)*100:.2f}%")
