import importlib.util
import os
import time
from playwright.sync_api import sync_playwright

print('\nClearing click log and waiting 1s...')
print('\nTests finished.')
import importlib.util
import os
import time
import random
import io
import contextlib
from playwright.sync_api import sync_playwright

cwd = os.getcwd()

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def read_click_log():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]
        page.goto('http://localhost:8000/', wait_until='domcontentloaded')
        raw = page.evaluate("() => localStorage.getItem('clickLog')")
        return raw

def clear_click_log():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]
        page.goto('http://localhost:8000/', wait_until='domcontentloaded')
        page.evaluate("() => localStorage.removeItem('clickLog')")

def get_img_rect():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]
        page.goto('http://localhost:8000/', wait_until='domcontentloaded')
        rect = page.evaluate("() => { const el = document.querySelector('img'); if(!el) return null; const r = el.getBoundingClientRect(); return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}; }")
        return rect

def predict_click(tx, ty, seed):
    rng = random.Random(seed)
    jx = rng.randint(-20,20)
    jy = rng.randint(-50,50)
    click_x = min(max(tx,150),1000) + jx
    click_y = 400 + jy
    return click_x, click_y


print('Clear any existing click log...')
clear_click_log()

# Load step5 module
path5 = os.path.join(cwd, '5.หาคลิกรูปในอัลบั้มโพส.py')
step5 = load_module(path5, 'step5')

rect = get_img_rect()
print('Image rect:', rect)

# find a seed that hits or misses
hit_seed = None
miss_seed = None
tx, ty = 400, 300
for s in range(0, 2000):
    cx, cy = predict_click(tx, ty, s)
    if rect and (rect['left'] <= cx <= rect['right'] and rect['top'] <= cy <= rect['bottom']):
        if hit_seed is None:
            hit_seed = s
    else:
        if miss_seed is None:
            miss_seed = s
    if hit_seed is not None and miss_seed is not None:
        break

print('Found seeds -> hit:', hit_seed, 'miss:', miss_seed)

def run_and_capture(seed, tx, ty, label, baseline_url='http://localhost:8000/'):
    print(f"\n=== {label}: seed={seed} url={baseline_url} ===")
    clear_click_log()
    time.sleep(0.3)
    # set RNG state so step5's random calls are deterministic
    random.seed(seed)
    # capture stdout from step5
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = step5.run_step_5(baseline_url=baseline_url, force_scroll_up=False, predefined_coords=(tx,ty))
    out = buf.getvalue()
    print('run_step_5 returned ->', res)
    print('Captured output:\n', out)
    # predicted coords
    cx, cy = predict_click(tx, ty, seed)
    print('Predicted click (x,y):', cx, cy)
    print('Within image rect?:', rect and (rect['left'] <= cx <= rect['right'] and rect['top'] <= cy <= rect['bottom']))
    log = read_click_log()
    print('clickLog:', log)

if hit_seed is not None:
    run_and_capture(hit_seed, tx, ty, 'HIT TEST')
else:
    print('No hit seed found in range')

if miss_seed is not None:
    run_and_capture(miss_seed, tx, ty, 'MISS TEST')
else:
    print('No miss seed found in range')

print('\nTests finished.')
