"""
สคริปต์สำรวจ DOM ของหน้า "เพิ่มกลุ่ม" ใน Facebook
เพื่อหา selector ที่ถูกต้องสำหรับ Checkbox
"""
import asyncio
import subprocess
import time
from playwright.async_api import async_playwright

def launch_chrome():
    subprocess.Popen(["python3", "browser_core.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

async def inspect_add_group_dialog():
    launch_chrome()
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9292")
        context = browser.contexts[0]
        
        # เปิดหน้ากลุ่มใหม่
        page = await context.new_page()
        await page.goto("https://www.facebook.com/groups/1131479790640124", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(2000)
        
        # คลิกสร้างโพสต์
        trigger = page.get_by_role("button", name="สร้างโพสต์สาธารณะ").first
        if not await trigger.is_visible():
            trigger = page.get_by_text("เขียนอะไรสักหน่อย").first
        await trigger.click()
        await page.wait_for_timeout(3000)
        
        # คลิก "เพิ่มกลุ่ม"
        add_btn = page.get_by_text("เพิ่มกลุ่ม").first
        if await add_btn.is_visible():
            await add_btn.click()
            print("✅ คลิก 'เพิ่มกลุ่ม' สำเร็จ")
        await page.wait_for_timeout(3000)
        
        # ถ่ายรูปก่อนค้นหา
        await page.screenshot(path="debug_before_search.png")
        
        # พิมพ์ค้นหา "ยานนาวา"
        search = await page.query_selector('input[placeholder*="ค้นหากลุ่ม"]')
        if not search:
            search = await page.query_selector('input[type="search"]')
        if not search:
            # หา input ทั้งหมดใน dialog
            all_inputs = await page.query_selector_all('div[role="dialog"] input')
            print(f"พบ input ทั้งหมด: {len(all_inputs)}")
            for i, inp in enumerate(all_inputs):
                ph = await inp.get_attribute("placeholder") or ""
                tp = await inp.get_attribute("type") or ""
                vis = await inp.is_visible()
                print(f"  input[{i}]: type='{tp}', placeholder='{ph}', visible={vis}")
                if vis and not search:
                    search = inp
        
        if search:
            await search.click()
            await search.fill("ยานนาวา")
            await page.wait_for_timeout(2000)
            print("✅ พิมพ์ 'ยานนาวา' สำเร็จ")
        else:
            print("❌ ไม่พบช่องค้นหา")
        
        # ถ่ายรูปหลังค้นหา
        await page.screenshot(path="debug_after_search.png")
        
        # Dump DOM ของ dialog เพื่อหา checkbox structure
        print("\n" + "=" * 60)
        print("🔍 DOM INSPECTION: หา Checkbox structure")
        print("=" * 60)
        
        dom_info = await page.evaluate("""
        () => {
            const dialog = document.querySelector('div[role="dialog"]');
            if (!dialog) return 'NO DIALOG FOUND';
            
            const results = [];
            
            // หา checkbox
            const checkboxes = dialog.querySelectorAll('[role="checkbox"]');
            results.push('=== role="checkbox" elements: ' + checkboxes.length);
            checkboxes.forEach((cb, i) => {
                results.push('  [' + i + '] tag=' + cb.tagName + ' aria-checked=' + cb.getAttribute('aria-checked') + ' class=' + cb.className.substring(0, 50));
            });
            
            // หา input checkbox
            const inputs = dialog.querySelectorAll('input[type="checkbox"]');
            results.push('\\n=== input[type="checkbox"]: ' + inputs.length);
            
            // หา listitem
            const listitems = dialog.querySelectorAll('[role="listitem"]');
            results.push('\\n=== role="listitem": ' + listitems.length);
            
            // หา row
            const rows = dialog.querySelectorAll('[role="row"]');
            results.push('\\n=== role="row": ' + rows.length);
            
            // หา option
            const options = dialog.querySelectorAll('[role="option"]');
            results.push('\\n=== role="option": ' + options.length);
            
            // หา label
            const labels = dialog.querySelectorAll('label');
            results.push('\\n=== label: ' + labels.length);
            
            // หา aria-selected
            const selected = dialog.querySelectorAll('[aria-selected]');
            results.push('\\n=== [aria-selected]: ' + selected.length);
            selected.forEach((s, i) => {
                results.push('  [' + i + '] tag=' + s.tagName + ' role=' + s.getAttribute('role') + ' aria-selected=' + s.getAttribute('aria-selected'));
            });
            
            // ดูโครงสร้างลูกหลานของ dialog (2 ชั้น)
            results.push('\\n=== Direct children of dialog:');
            Array.from(dialog.children).forEach((child, i) => {
                if (i < 5) {
                    results.push('  child[' + i + '] tag=' + child.tagName + ' role=' + (child.getAttribute('role')||'') + ' children=' + child.children.length);
                }
            });
            
            // หาทุก div ที่คลิกได้ภายในส่วนรายชื่อกลุ่ม
            // Facebook มักจะใช้ div ที่มี cursor:pointer
            const clickable = dialog.querySelectorAll('div[tabindex="0"]');
            results.push('\\n=== div[tabindex="0"] (clickable): ' + clickable.length);
            clickable.forEach((el, i) => {
                if (i < 10) {
                    const text = el.innerText.substring(0, 60).replace(/\\n/g, ' | ');
                    results.push('  [' + i + '] role=' + (el.getAttribute('role')||'none') + ' text="' + text + '"');
                }
            });
            
            return results.join('\\n');
        }
        """)
        
        print(dom_info)
        
        print("\n✅ สำรวจเสร็จ! ดูรูป debug_before_search.png และ debug_after_search.png")

asyncio.run(inspect_add_group_dialog())
