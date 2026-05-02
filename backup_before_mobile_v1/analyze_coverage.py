import json
import os

# Configuration
DATA_FILE = "group_analysis.json"
NEIGHBOR_FILE = "neighboring_districts.txt"
TARGET_PER_AREA = 5 # ปรับลดลงเหลือ 5 เพราะเราตัดกลุ่มทั่วไปออก (เน้นคุณภาพกลุ่มเจาะจง)

def load_neighbor_map(file_path):
    neighbor_map = {}
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                parts = line.split(":", 1)
                district = parts[0].strip().split(".", 1)[-1].strip()
                neighbors = [n.strip() for n in parts[1].split(",")]
                neighbor_map[district] = [district] + neighbors
    return neighbor_map

def analyze_by_type(asset_type_filter, data, neighbor_map):
    print(f"\n🏠 ANALYZING ASSET TYPE: {asset_type_filter}")
    print("-" * 80)
    
    # Count groups per district for THIS asset type (EXCLUDING General BKK)
    district_counts = {}
    for url, info in data.items():
        cats = info.get("categories", {})
        districts = cats.get("districts", [])
        asset_types = cats.get("asset_types", [])
        
        # Check if matches asset type (e.g. "คอนโด" or "บ้าน")
        if asset_type_filter not in asset_types:
            continue
            
        # EXCLUDE "กรุงเทพฯ ทุกเขต" to see real local strength
        if "กรุงเทพฯ ทุกเขต" in districts:
            continue
            
        for d in districts:
            district_counts[d] = district_counts.get(d, 0) + 1

    results = []
    for district, area_set in neighbor_map.items():
        total_available = 0
        details = []
        for d in area_set:
            count = district_counts.get(d, 0)
            total_available += count
            if count > 0:
                details.append(f"{d}({count})")
        
        coverage_pct = min(100, (total_available / TARGET_PER_AREA) * 100)
        results.append({
            "district": district,
            "total": total_available,
            "pct": coverage_pct,
            "details": ", ".join(details)
        })

    results.sort(key=lambda x: x["pct"])
    print(f"{'DISTRICT':<18} | {'LOCAL GRPS':<10} | {'COVERAGE %':<10} | {'SUPPORTED BY'}")
    print("-" * 80)
    
    for r in results:
        status = "🔴" if r["pct"] < 50 else ("🟡" if r["pct"] < 100 else "🟢")
        print(f"{status} {r['district']:<16} | {r['total']:<10} | {r['pct']:>8.1f}% | {r['details']}")
    
    return results

def run_analysis():
    if not os.path.exists(DATA_FILE):
        print("❌ Error: group_analysis.json not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    neighbor_map = load_neighbor_map(NEIGHBOR_FILE)
    
    print("\n" + "="*80)
    print("🎯 HARDCORE COVERAGE ANALYSIS (Excluding General BKK Groups)")
    print("="*80)

    # Analyze Condos
    condo_results = analyze_by_type("คอนโด", data, neighbor_map)
    
    # Analyze Houses
    house_results = analyze_by_type("บ้าน", data, neighbor_map)

    # Final Summary
    print("\n" + "="*80)
    print("📊 FINAL HARDCORE SUMMARY")
    
    c_ok = len([r for r in condo_results if r["pct"] >= 100])
    h_ok = len([r for r in house_results if r["pct"] >= 100])
    
    print(f"🏢 CONDO: {c_ok}/{len(neighbor_map)} Areas Fully Covered")
    print(f"🏡 HOUSE: {h_ok}/{len(neighbor_map)} Areas Fully Covered")
    print("="*80)

if __name__ == "__main__":
    run_analysis()
