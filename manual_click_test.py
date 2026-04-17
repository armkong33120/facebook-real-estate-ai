from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://localhost:9222')
    page = browser.contexts[0].pages[0]
    page.goto('http://localhost:8000/', wait_until='domcontentloaded')
    # ensure clickLog exists
    page.evaluate("() => { localStorage.removeItem('clickLog'); }")
    time.sleep(0.5)
    # Activation click
    page.mouse.click(500,300)
    time.sleep(0.2)
    # Second click near center (use explicit move/down/up)
    time.sleep(0.5)
    el = page.evaluate("() => { const el = document.elementFromPoint(400,400); return el ? (el.tagName + (el.id?('#'+el.id):'')) : null }")
    print('elementAt(400,400)=', el)
    page.mouse.move(400,400)
    page.mouse.down()
    time.sleep(0.05)
    page.mouse.up()
    time.sleep(0.5)
    log = page.evaluate("() => localStorage.getItem('clickLog')")
    print('clickLog:', log)

print('manual test done')
