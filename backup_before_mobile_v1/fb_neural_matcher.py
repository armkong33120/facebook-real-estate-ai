import os
import json

# Configuration
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "group_analysis.json")
PROPERTY_BASE_DIR = "/Users/your_username/Desktop/Facebook_Property_Data/กรุงเทพมหานคร"
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neural_match_report.md")

# Sample BAs
SELECTED_BAS = [
    "จตุจักร/BA 10426", "พระโขนง/BA 10521", "พระโขนง/BA 10211", "จตุจักร/BA 10216",
    "วัฒนา/BA 10204", "พระโขนง/BA 10367", "ห้วยขวาง/BA 10556", "สวนหลวง/BA 10162",
    "พระโขนง/BA 10085", "วัฒนา/BA 10034"
]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def extract_ba_profile(ba_path):
    full_path = os.path.join(PROPERTY_BASE_DIR, ba_path)
    ba_id = os.path.basename(ba_path)
    txt_file = os.path.join(full_path, f"{ba_id}.txt")
    profile = {"id": ba_id, "district": ba_path.split('/')[0], "type": "คอนโด"}
    if os.path.exists(txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "ประเภท: บ้าน" in content: profile["type"] = "บ้าน"
            elif "ประเภท: ที่ดิน" in content: profile["type"] = "ที่ดิน"
    return profile

def neural_match():
    print("\n" + "="*50)
    print("🕸️  PHASE 4: Neural Matcher Simulation")
    print("="*50)
    
    groups = load_data()
    categorized_groups = {k: v for k, v in groups.items() if "categories" in v}
    
    report_lines = ["# Neural Matcher Simulation Report (Tiered Logic)\n\n"]
    report_lines.append(f"Matching 10 BAs against {len(categorized_groups)} categorized groups.\n\n")

    for ba_rel_path in SELECTED_BAS:
        profile = extract_ba_profile(ba_rel_path)
        district = profile["district"]
        asset_type = profile["type"]
        
        print(f"🎯 Matching BA: {profile['id']} ({district})")
        
        exact_matches = []
        fallback_matches = []
        uncertain_matches = []
        
        for url, g in categorized_groups.items():
            cats = g["categories"]
            
            # OLD LOGIC (COMMENTED OUT)
            # is_loc_match = district in cats["districts"]
            # is_general_match = "กรุงเทพฯ ทุกเขต" in cats["districts"]
            # is_type_match = any(asset_type in t for t in cats["asset_types"])
            # policy_ok = cats["agent_policy"] != "เฉพาะเจ้าของ"
            # 
            # if is_type_match and policy_ok:
            #     match_info = {"name": g["name"], "url": url, "score": cats["match_score"], "reason": cats["suggested_action"]}
            #     
            #     if cats["is_uncertain"]:
            #         uncertain_matches.append(match_info)
            #     elif is_loc_match:
            #         exact_matches.append(match_info)
            #     elif is_general_match:
            #         fallback_matches.append(match_info)

            # --- NEW LOGIC PLACEHOLDER ---
            # TODO: Define new matching logic here
            is_match = False # Default to False until logic is defined
            if is_match:
                 pass
            # -----------------------------

        
        # Merge Tier 1 (Exact) + Tier 2 (Fallback) up to 40
        final_list = sorted(exact_matches, key=lambda x: x["score"], reverse=True)
        if len(final_list) < 40:
            final_list += sorted(fallback_matches, key=lambda x: x["score"], reverse=True)[:(40 - len(final_list))]
        
        report_lines.append(f"## {profile['id']} ({district} - {asset_type})\n")
        report_lines.append(f"✅ **Recommended Groups**: {len(final_list)} groups\n")
        
        if final_list:
            report_lines.append("| Name | Score | Reason |\n| :--- | :--- | :--- |\n")
            for m in final_list:
                report_lines.append(f"| [{m['name']}]({m['url']}) | {m['score']} | {m['reason']} |\n")
        
        if uncertain_matches:
            report_lines.append(f"\n⚠️ **Uncertain Groups (Need Review)**: {len(uncertain_matches)}\n")
            report_lines.append("| Name | AI Concern |\n| :--- | :--- |\n")
            for u in uncertain_matches:
                report_lines.append(f"| [{u['name']}]({u['url']}) | {u['reason']} |\n")
        
        report_lines.append("\n---\n")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.writelines(report_lines)
    print(f"🎉 Simulation Complete! Report: {REPORT_FILE}")

if __name__ == "__main__":
    neural_match()
