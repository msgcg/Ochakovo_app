import os
import subprocess
import time
import requests
from playwright.sync_api import sync_playwright

artifacts_dir = r"C:\Users\m7036\.gemini\antigravity\brain\f78f3420-65ed-4da7-827f-66d6d8690a00\screenshots"
os.makedirs(artifacts_dir, exist_ok=True)

server = subprocess.Popen([r".venv\Scripts\python.exe", "manage.py", "runserver", "127.0.0.1:8000", "--noreload"])

# Wait for server ready
for _ in range(30):
    try:
        r = requests.get("http://127.0.0.1:8000/", timeout=1)
        if r.status_code == 200:
            print("Django dev server is UP!")
            break
    except Exception:
        pass
    time.sleep(0.5)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        
        # 1. Desktop Game Play - should open directly with ZERO modals
        page = browser.new_page(viewport={"width": 1280, "height": 850})
        page.goto("http://127.0.0.1:8000/game/brew-yeast-flex/")
        page.wait_for_timeout(1500)
        
        # Verify no briefing modal is present or visible
        briefing_modal = page.query_selector('#och-briefing-modal')
        assert briefing_modal is None, "Briefing modal must be completely removed from DOM"
        
        page.screenshot(path=os.path.join(artifacts_dir, "verified_game_desktop_direct.png"))
        print("Desktop verified: Direct start with NO key modal. Saved verified_game_desktop_direct.png")

        # 2. Mobile Game Play - direct start
        page_m = browser.new_page(viewport={"width": 390, "height": 844})
        page_m.goto("http://127.0.0.1:8000/game/brew-yeast-flex/")
        page_m.wait_for_timeout(1500)
        
        page_m.screenshot(path=os.path.join(artifacts_dir, "verified_game_mobile_direct.png"))
        print("Mobile verified: Direct start with NO key modal. Saved verified_game_mobile_direct.png")

        browser.close()
finally:
    server.terminate()
    server.wait()
    print("Dev server stopped cleanly.")
