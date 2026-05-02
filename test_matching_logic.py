import json
import os
import random

# Configuration
DATA_FILE = "group_analysis.json"
NEIGHBOR_FILE = "neighboring_districts.txt"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_neighbor_map():
    neighbor_map = {}
    if not os.path.exists(NEIGHBOR_FILE): return {}
    with open(NEIGHBOR_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                parts = line.split(":", 1)
                district = parts[0].strip().split(".", 1)[-1].strip()
                neighbors = [n.strip() for n in parts[1].split(",")]
                neighbor_map[district] = [district] + neighbors
    return neighbor_map

def find_best_groups(district, asset_type, data, area_set):
    matches = []
    seen_urls = set()
    
    for url, info in data.items():
        if url in seen_urls: continue
        
        cats = info.get("categories", {})
        g_districts = cats.get("districts", [])
        g_assets = cats.get("asset_types", [])
        
        if asset_type not in g_assets:
            continue
            
        is_direct = district in g_districts
        is_neighbor = any(d in area_set for d in g_districts)
        is_general = "กรุงเทพฯ ทุกเขต" in g_districts
        
        if is_direct or is_neighbor or is_general:
            # Score: Direct(10) > Neighbor(5) > General(2)
            score = 10 if is_direct else (5 if is_neighbor else 2)
            matches.append({
                "name": info["name"],
                "url": url,
                "score": score,
                "type": "DIRECT" if is_direct else ("NEIGHBOR" if is_neighbor else "GENERAL")
            })
            seen_urls.add(url)
    
    # Sort by score (Primary first) then random within score to see variety
    matches.sort(key=lambda x: (x["score"], random.random()), reverse=True)
    return matches[:40]

def run_test():
    data = load_data()
    neighbor_map = load_neighbor_map()
    districts = list(neighbor_map.keys())
    asset_types = ["คอนโด", "บ้าน"]

    print("\n" + "="*80)
    print("🧪 DEEP MATCHING TEST: 3 SAMPLES x 40 GROUPS")
    print("="*80)

    # Pick 3 random samples
    selected_districts = random.sample(districts, 3)
    
    for i, d in enumerate(selected_districts):
        a_type = random.choice(asset_types)
        area_set = neighbor_map.get(d, [d])
        best_matches = find_best_groups(d, a_type, data, area_set)
        
        print(f"\n🔥 TEST #{i+1}: {a_type} @ เขต{d}")
        print(f"📍 Area Set Includes: {', '.join(area_set)}")
        print(f"📊 Found {len(best_matches)} matching groups:")
        print("-" * 80)
        
        if not best_matches:
            print("❌ No matching groups found!")
        else:
            for idx, m in enumerate(best_matches):
                print(f"{idx+1:>2}. [{m['type']}] {m['name'][:65]}")
        
        print("\n" + "-"*80)
    
    print("\n" + "="*80)
    print("✅ DEEP TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    run_test()
