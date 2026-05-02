import importlib.util
import time
import socket
import os

cwd = os.getcwd()

def wait_for_port(host, port, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        try:
            s = socket.create_connection((host, port), timeout=1)
            s.close()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

print('Test runner starting...')
print('Waiting 2s for server startup...')
time.sleep(2)

print('Checking CDP (127.0.0.1:9222)...')
if not wait_for_port('127.0.0.1', 9222, timeout=20):
    print('WARNING: CDP not ready on 9222 (tests may fail)')
else:
    print('CDP is listening on 9222')

# Run step6
try:
    path6 = os.path.join(cwd, '6.ดูดไฟล์รูป เก็บตามข้อ 4 และเช็คค่าไฟล์ hash ป้องกันการโหลดรูปซ้ำ.py')
    step6 = load_module(path6, 'step6')
    print('Calling run_step_6(save_dir=test_gallery/save)')
    res6 = step6.run_step_6(os.path.join('test_gallery','save'))
    print('run_step_6 ->', res6)
except Exception as e:
    print('step6 failed:', repr(e))

# Run step7
try:
    path7 = os.path.join(cwd, '7.เลื่อนรูปไปทางขวามือไปเรื่อยๆถ้าค่า hash รูปในอัลบั้มยังไม่ซ้ำ.py')
    step7 = load_module(path7, 'step7')
    print('Calling run_step_7()')
    res7 = step7.run_step_7()
    print('run_step_7 ->', res7)
except Exception as e:
    print('step7 failed:', repr(e))

# Run step5 with predefined coords
try:
    path5 = os.path.join(cwd, '5.หาคลิกรูปในอัลบั้มโพส.py')
    step5 = load_module(path5, 'step5')
    print("Calling run_step_5(baseline_url='http://localhost:8000/', predefined_coords=(400,300))")
    res5 = step5.run_step_5(baseline_url='http://localhost:8000/', force_scroll_up=False, predefined_coords=(400,300))
    print('run_step_5 ->', res5)
except Exception as e:
    print('step5 failed:', repr(e))

print('Test runner finished.')
