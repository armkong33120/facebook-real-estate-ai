import os

BASE_DIR = "/Users/your_username/.gemini/antigravity/scratch/mnt_c/Users/Lab_test/Desktop/Facebook_Property_Data"

def analyze_ba_shared():
    stats = {}
    total_ba = 0
    
    if not os.path.exists(BASE_DIR):
        print(f"❌ Directory not found on Shared Drive: {BASE_DIR}")
        return

    # Path: Province / District / PropertyID
    provinces = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d)) and not d.startswith('_')]
    
    for province in provinces:
        prov_path = os.path.join(BASE_DIR, province)
        try:
            districts = [d for d in os.listdir(prov_path) if os.path.isdir(os.path.join(prov_path, d))]
        except: continue
        
        for district in districts:
            dist_path = os.path.join(prov_path, district)
            try:
                prop_ids = [d for d in os.listdir(dist_path) if os.path.isdir(os.path.join(dist_path, d))]
                ba_in_dist = [d for d in prop_ids if d.upper().startswith("BA")]
                
                if ba_in_dist:
                    key = f"{province} / {district}"
                    stats[key] = stats.get(key, 0) + len(ba_in_dist)
                    total_ba += len(ba_in_dist)
            except: continue

    print("="*65)
    print(f"📊 BA PROPERTY DISTRIBUTION - SHARED DRIVE (Total BA: {total_ba})")
    print("="*65)
    print(f"{'Location (Province / District)':<40} | {'Count':<5} | {'%'}")
    print("-" * 65)
    
    # Sort by count descending
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    
    for loc, count in sorted_stats:
        percentage = (count / total_ba) * 100 if total_ba > 0 else 0
        print(f"{loc:<40} | {count:<5} | {percentage:>6.2f}%")
    print("="*65)

if __name__ == "__main__":
    analyze_ba_shared()
