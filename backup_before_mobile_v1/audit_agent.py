#!/usr/bin/env python3
import os
import time
import json
import config
import ai_engine

def log_audit(msg):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def is_image(fname):
    f = fname.lower()
    return f.endswith(('.jpg', '.jpeg', '.png', '.webp'))

def get_first_image(folder_path):
    """หาไฟล์รูปแรกที่น่าจะเป็นรูปหน้าปก (ตัวเลขต่ำสุด หรือชื่อไฟล์ลำดับแรก)"""
    files = [f for f in os.listdir(folder_path) if is_image(f)]
    # กรองรูป Debug ออก
    files = [f for f in files if f not in ["vision_map.png", "one_shot_vision.png", "landing_check.png"]]
    if not files:
        return None
    # เรียงลำดับเพื่อให้ 1.jpg หรือ BAxxxx_1.jpg มาก่อน
    files.sort()
    return os.path.join(folder_path, files[0])

def get_context(folder_path):
    """หาไฟล์ข้อความกำกับโพสต์ (BAxxxx.txt) เพื่อใช้เป็นบริบทให้ AI เช็ค"""
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".txt")]
    if not files:
        return ""
    try:
        with open(os.path.join(folder_path, files[0]), "r", encoding="utf-8") as f:
            return f.read()[:1000] # เอาแค่ 1000 ตัวอักษรก็พอ
    except:
        return ""

def run_project_audit(max_folders=None):
    base_dir = config.BASE_RESULT_DIR
    if not os.path.exists(base_dir):
        log_audit(f"Error: ไม่พบโฟลเดอร์ {base_dir}")
        return

    log_audit("=== เริ่มระบบ AI Quality Audit Agent (Sampling Mode) ===")
    log_audit(f"โมเดลที่ใช้: {config.MODEL_NAME}")
    if max_folders:
        log_audit(f"โหมดทดสอบ: จำกัดการตรวจสอบไว้ที่ {max_folders} รายการ")
    
    # 1. รวบรวมรายชื่อโฟลเดอร์ BA ทั้งหมด
    target_folders = []
    for root, dirs, files in os.walk(base_dir):
        folder_name = os.path.basename(root)
        if folder_name.startswith("BA "):
            target_folders.append(root)
    
    # เรียงลำดับเพื่อให้เริ่มจาก BA ที่เก่าสุด
    target_folders.sort()
    
    if max_folders:
        target_folders = target_folders[:max_folders]
    
    total = len(target_folders)
    log_audit(f"พบโฟลเดอร์เป้าหมายทั้งหมด: {total} รายการ")

    results = {
        "summary": {
            "total_audited": 0,
            "passed": 0,
            "failed": 0,
            "error": 0
        },
        "details": []
    }

    # 2. เริ่มลูปตรวจสอบ (Throttling 15 RPM)
    for i, folder_path in enumerate(target_folders):
        folder_name = os.path.basename(folder_path)
        log_audit(f" [{i+1}/{total}] กำลังตรวจสอบ: {folder_name}")
        
        first_img = get_first_image(folder_path)
        context = get_context(folder_path)
        
        if not first_img:
            log_audit(f" ⚠️  ข้าม {folder_name}: ไม่พบรูปภาพ")
            results["details"].append({
                "id": folder_name,
                "status": "NO_IMAGE",
                "reason": "Not found images in folder"
            })
            continue

        audit_result = ai_engine.evaluate_property_relevance(first_img, context)
        
        # จัดกลุ่มประเภทผลลัพธ์
        status = "PASSED" if audit_result.get("decision") == True else "FAILED"
        confidence = audit_result.get("confidence", 0)
        reason = audit_result.get("reason", "N/A")

        if status == "PASSED":
            results["summary"]["passed"] += 1
            log_audit(f" ✅ [BA {folder_name.split()[-1]}] ผ่านคุณภาพ (Confidence: {confidence}%)")
        else:
            results["summary"]["failed"] += 1
            log_audit(f" 🆘 [{folder_name}] AI ตรวจพบความเสี่ยง: {reason} (Confidence: {confidence}%)")

        results["details"].append({
            "id": folder_name,
            "path": folder_path,
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "image_sample": first_img
        })
        
        results["summary"]["total_audited"] += 1

        # แสดงสรุปสั้นๆ ทุก 10 รายการเพื่อให้คุณพี่ชื่นใจ
        if (i + 1) % 10 == 0:
            passed = results["summary"]["passed"]
            failed = results["summary"]["failed"]
            log_audit(f"--- [PROGRESS] ตรวจไปแล้ว {i+1} รายการ | ✅ ผ่าน: {passed} | ❌ เสี่ยง: {failed} ---")

        # Throttling Logic เพื่อให้ไม่เกิน 15 RPM
        time.sleep(3)

        # บันทึกสถานะชั่วคราวทุก 50 รายการกันโปรแกรมหลุด
        if (i + 1) % 50 == 0:
            with open("audit_results_checkpoint.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    # 3. สรุปผลสุดท้าย
    with open("audit_results_final.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # สร้าง Markdown Report สรุปเฉพาะตัวที่พัง
    generate_markdown_report(results)
    
    log_audit("=== ภารกิจ Audit เสร็จสมบูรณ์! ===")
    log_audit(f"ตรวจทั้งหมด: {results['summary']['total_audited']}")
    log_audit(f"✅ ผ่าน: {results['summary']['passed']}")
    log_audit(f"❌ พลาด: {results['summary']['failed']}")

def generate_markdown_report(results):
    report_path = "audit_report_summary.md"
    failed_items = [d for d in results["details"] if d["status"] == "FAILED"]
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# รายงานตรวจสอบคุณภาพ AI Audit Report\n\n")
        f.write(f"**สถานะภาพรวม:**\n")
        f.write(f"- ตรวจสอบทั้งหมด: {results['summary']['total_audited']} รายการ\n")
        f.write(f"- ✅ ผ่านคุณภาพ: {results['summary']['passed']} รายการ\n")
        f.write(f"- ❌ ตรวจพบความเสี่ยง: {results['summary']['failed']} รายการ\n\n")
        
        f.write("## รายการที่ควรตรวจสอบซ้ำ (Failed/Suspected)\n")
        f.write("| ID | Confidence | Reason | Path |\n")
        f.write("|----|------------|--------|------|\n")
        for item in failed_items:
            f.write(f"| {item['id']} | {item['confidence']}% | {item['reason']} | {item['path']} |\n")

if __name__ == "__main__":
    import sys
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass
    run_project_audit(max_folders=limit)
