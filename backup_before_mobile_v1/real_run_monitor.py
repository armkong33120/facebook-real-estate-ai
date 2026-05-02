import importlib.util
import os
import io
import contextlib
import re
import time
import datetime

cwd = os.getcwd()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def parse_first_url(uat_path='uat_link.txt'):
    if not os.path.exists(uat_path):
        return None
    with open(uat_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # try to extract an http/https token
            parts = re.split(r"\s+|\|", line)
            for p in parts:
                if p.startswith('http://') or p.startswith('https://'):
                    return p
    return None


def run_and_capture(callable_fn, *args, **kwargs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            res = callable_fn(*args, **kwargs)
        except Exception as e:
            res = ('EXCEPTION', str(e))
    out = buf.getvalue()
    return res, out


def extract_click_coords(text):
    return re.findall(r'คลิกพิกัด\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', text)


def detect_fallback(text):
    t = text.lower()
    return ('fail' in t) or ('fallback' in t) or ('failed' in t)


def extract_step6_info(text):
    duplicate = bool(re.search(r'พบรูปซ้ำ', text))
    new_match = re.search(r'ดูดรูปที่\s*(\d+)', text)
    hash_match = re.search(r'รหัส:\s*([0-9a-fA-F]+)', text)
    return {
        'duplicate': duplicate,
        'new_index': new_match.group(1) if new_match else None,
        'hash': hash_match.group(1) if hash_match else None
    }


def main():
    baseline = parse_first_url()
    if not baseline:
        print('No baseline URL found in uat_link.txt')
        return

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    save_dir = os.path.join(cwd, f'monitor_run_save_{timestamp}')
    os.makedirs(save_dir, exist_ok=True)

    # module paths (exact filenames)
    path5 = os.path.join(cwd, '5.หาคลิกรูปในอัลบั้มโพส.py')
    path6 = os.path.join(cwd, '6.ดูดไฟล์รูป เก็บตามข้อ 4 และเช็คค่าไฟล์ hash ป้องกันการโหลดรูปซ้ำ.py')
    path7 = os.path.join(cwd, '7.เลื่อนรูปไปทางขวามือไปเรื่อยๆถ้าค่า hash รูปในอัลบั้มยังไม่ซ้ำ.py')

    print('Baseline URL:', baseline)
    print('Save dir:', save_dir)

    step5 = load_module(path5, 'step5')
    step6 = load_module(path6, 'step6')
    step7 = load_module(path7, 'step7')

    log_parts = []

    # Step 5
    print('\n=== Running Step 5 (open album) ===')
    res5, out5 = run_and_capture(step5.run_step_5, baseline, False, None)
    print(out5)
    log_parts.append(('step5', out5))
    coords = extract_click_coords(out5)
    fallback_flag = detect_fallback(out5)

    # Step 6
    print('\n=== Running Step 6 (download & hash) ===')
    res6, out6 = run_and_capture(step6.run_step_6, save_dir)
    print(out6)
    log_parts.append(('step6', out6))
    info6 = extract_step6_info(out6)

    # Step 7
    print('\n=== Running Step 7 (arrow right) ===')
    res7, out7 = run_and_capture(step7.run_step_7)
    print(out7)
    log_parts.append(('step7', out7))

    # Summarize
    summary = {
        'baseline': baseline,
        'step5_result': str(res5),
        'step5_clicks': coords,
        'step5_fallback_triggered': bool(fallback_flag),
        'step6_result': str(res6),
        'step6_info': info6,
        'step7_result': str(res7)
    }

    log_file = os.path.join(save_dir, 'monitor_real_run.log')
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f'Monitor run at {timestamp}\n')
        f.write('Summary:\n')
        for k, v in summary.items():
            f.write(f'{k}: {v}\n')
        f.write('\nFull logs:\n')
        for name, part in log_parts:
            f.write(f'--- {name} ---\n')
            f.write(part + '\n')

    print('\n=== SUMMARY ===')
    for k, v in summary.items():
        print(f'{k}: {v}')
    print('\nLog written to', log_file)


if __name__ == '__main__':
    main()
