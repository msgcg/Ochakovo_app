import os
import requests
from playwright.sync_api import sync_playwright

artifacts_dir = r"C:\Users\m7036\.gemini\antigravity\brain\f78f3420-65ed-4da7-827f-66d6d8690a00\screenshots"
os.makedirs(artifacts_dir, exist_ok=True)

# 1. Test PDF Export Endpoint
pdf_res = requests.get("http://127.0.0.1:8000/progress/export/pdf/?name=Максим+Соколов&score=490")
assert pdf_res.status_code == 200, f"PDF export failed: {pdf_res.status_code}"
assert pdf_res.headers.get('content-type') == 'application/pdf', "Not PDF"
print(f"PDF Export Verified: {len(pdf_res.content)} bytes, Content-Type: application/pdf")

# 2. Test Stand Lead Capture API
lead_res = requests.post("http://127.0.0.1:8000/api/candidate/stand-lead/", json={
    "full_name": "Евгений Романов",
    "phone": "+7-999-123-45-67",
    "telegram": "@eromanov",
    "university": "МГУТУ",
    "track_slug": "brewing"
})
assert lead_res.status_code == 200, f"Stand Lead API failed: {lead_res.text}"
lead_data = lead_res.json()
assert lead_data.get('ok') is True
print("Stand Lead Capture API Verified:", lead_data.get('message'), "Matched vacancies:", len(lead_data.get('matched_vacancies', [])))

# 3. Test VK ID Demo Auth
vk_res = requests.get("http://127.0.0.1:8000/auth/vk/demo/", allow_redirects=False)
assert vk_res.status_code == 302, f"VK demo failed: {vk_res.status_code}"
print("VK ID Demo Auth Verified, redirect to:", vk_res.headers.get('Location'))

# 4. Playwright Visual Verification on Desktop & Mobile
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)

    # 4.1 Home Page Desktop
    page = browser.new_page(viewport={"width": 1280, "height": 850})
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(artifacts_dir, "verified_home_desktop.png"))
    print("Saved verified_home_desktop.png")

    # Click to open Stand QR modal
    qr_btn = page.query_selector('button[onclick="openStandQrModal()"]')
    if qr_btn:
        qr_btn.click()
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(artifacts_dir, "verified_stand_qr_modal.png"))
        print("Saved verified_stand_qr_modal.png")

    # 4.2 Progress Page Desktop
    page.goto("http://127.0.0.1:8000/auth/vk/demo/?next=/progress/")
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(artifacts_dir, "verified_progress_desktop.png"))
    print("Saved verified_progress_desktop.png")

    # 4.3 Simulator Scenario with Pro Facts
    page.goto("http://127.0.0.1:8000/game/brew-yeast-flex/")
    page.wait_for_timeout(1000)
    # Click "Факты цеха"
    facts_btn = page.query_selector('button[onclick="simulator.openProFactsModal()"]')
    if facts_btn:
        facts_btn.click()
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(artifacts_dir, "verified_pro_facts_modal.png"))
        print("Saved verified_pro_facts_modal.png")

    # 4.4 Mobile Viewport (iPhone 14)
    page_m = browser.new_page(viewport={"width": 390, "height": 844})
    page_m.goto("http://127.0.0.1:8000/")
    page_m.wait_for_timeout(1000)
    page_m.screenshot(path=os.path.join(artifacts_dir, "verified_home_mobile.png"))
    print("Saved verified_home_mobile.png")

    page_m.goto("http://127.0.0.1:8000/progress/")
    page_m.wait_for_timeout(1000)
    page_m.screenshot(path=os.path.join(artifacts_dir, "verified_progress_mobile.png"))
    print("Saved verified_progress_mobile.png")

    page_m.goto("http://127.0.0.1:8000/game/brew-yeast-flex/")
    page_m.wait_for_timeout(1000)
    page_m.screenshot(path=os.path.join(artifacts_dir, "verified_game_mobile.png"))
    print("Saved verified_game_mobile.png")

    browser.close()

print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
