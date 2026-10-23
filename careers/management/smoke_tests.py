import os
import sys
import json
import django
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ochakovo_project.settings')
django.setup()

from django.test import Client
from careers.models import GameSession, GameScenario

def run_smoke_tests():
    c = Client()
    endpoints = [
        ('/', 200, 'Home Page'),
        ('/game/', 200, 'Game Select Page'),
        ('/game/brew-double-fermentation/', 200, 'Simulator Cockpit'),
        ('/vacancies/', 200, 'Vacancies Catalog'),
        ('/vacancies/master-tehnolog-proizvodstva/', 200, 'Vacancy Detail'),
        ('/story/', 200, 'Story & Values'),
        ('/manifest.json', 200, 'PWA Manifest'),
        ('/sw.js', 200, 'Service Worker'),
        ('/offline/', 200, 'PWA Offline Page')
    ]

    print("=== STARTING SMOKE TESTS ===")
    all_ok = True
    for url, expected_status, label in endpoints:
        resp = c.get(url)
        status = resp.status_code
        if status == expected_status:
            print(f"[OK] {label} -> {url} (HTTP {status})")
        else:
            print(f"[FAIL] {label} -> {url} (Expected {expected_status}, got {status})")
            all_ok = False

    # Test API game action turn
    sc = GameScenario.objects.first()
    session = GameSession.objects.create(
        scenario=sc,
        current_node_id='start',
        score=50,
        temperature=28.5,
        brix=8.4,
        line_speed=28000,
        purity=92,
        balance=45
    )

    action_payload = {
        'session_id': str(session.session_uuid),
        'equipment_code': 'valve_cooling',
        'user_text': 'Открываю клапан охлаждения на 40%'
    }
    resp = c.post(
        '/api/game/action/',
        data=json.dumps(action_payload),
        content_type='application/json'
    )
    if resp.status_code == 200 and resp.json().get('ok'):
        data = resp.json()
        print(f"[OK] API Game Action Turn -> Score: {data.get('score')}, Temp: {data.get('temperature')}°C, Reply: {data.get('mentor_reply')[:45]}...")
    else:
        print(f"[FAIL] API Game Action Turn -> {resp.status_code}, {resp.content}")
        all_ok = False

    # Test Candidate Fast Apply API
    apply_payload = {
        'full_name': 'Тестовый Кандидат',
        'phone': '+7 (999) 111-22-33',
        'email': 'candidate@test.ru',
        'university': 'РТУ МИРЭА',
        'course_or_status': '3 курс',
        'session_id': str(session.session_uuid)
    }
    resp_app = c.post(
        '/api/candidate/apply/',
        data=json.dumps(apply_payload),
        content_type='application/json'
    )
    if resp_app.status_code == 200 and resp_app.json().get('ok'):
        print(f"[OK] API Candidate Apply -> App ID: {resp_app.json().get('application_id')}")
    else:
        print(f"[FAIL] API Candidate Apply -> {resp_app.status_code}, {resp_app.content}")
        all_ok = False

    # Test Interactive Vacancies Live Search API
    resp_search = c.get('/api/vacancies/search/?q=технолог&has_game=1')
    if resp_search.status_code == 200 and resp_search.json().get('ok'):
        sdata = resp_search.json()
        print(f"[OK] API Vacancies Live Search -> Found: {sdata.get('count')} matching items with simulator")
    else:
        print(f"[FAIL] API Vacancies Live Search -> {resp_search.status_code}, {resp_search.content}")
        all_ok = False

    # Test Vacancies Sync API
    resp_sync = c.post('/api/vacancies/sync/')
    if resp_sync.status_code == 200 and resp_sync.json().get('ok'):
        sync_data = resp_sync.json()
        print(f"[OK] API Vacancies Sync -> {sync_data.get('message')}")
    else:
        print(f"[FAIL] API Vacancies Sync -> {resp_sync.status_code}, {resp_sync.content}")
        all_ok = False

    # Test Humorous Easter Egg in Simulator
    resp_humor = c.post(
        '/api/game/action/',
        data=json.dumps({
            'session_id': str(session.session_uuid),
            'user_text': 'Михалыч, а можно в окрошку кефир налить?'
        }),
        content_type='application/json'
    )
    reply_lower = resp_humor.json().get('mentor_reply', '').lower()
    if resp_humor.status_code == 200 and any(w in reply_lower for w in ('кефир', 'окрошк', 'квас')):
        print(f"[OK] Humor Easter Egg -> Reply: {resp_humor.json().get('mentor_reply')[:60]}...")
    else:
        print(f"[FAIL] Humor Easter Egg -> {resp_humor.status_code}, {resp_humor.content}")
        all_ok = False

    # Test Whisper Vulkan / CPU STT API & GGML settings
    from careers.services.whisper_service import WhisperVulkanService
    whisper_ready = WhisperVulkanService.is_available()
    mode, fallback = WhisperVulkanService.get_acceleration_config()
    print(f"[OK] Whisper Engine -> Available: {whisper_ready}, Mode: {mode}, Fallback CPU: {fallback}")
    resp_stt = c.post('/api/game/stt/', data=b'', content_type='application/octet-stream')
    if resp_stt.status_code == 400: # correctly rejects empty audio
        print(f"[OK] API Game STT Endpoint -> /api/game/stt/ responds correctly to input validation")
    else:
        print(f"[FAIL] API Game STT Endpoint -> {resp_stt.status_code}")
        all_ok = False

    print("=== SMOKE TESTS RESULT: " + ("ALL PASSED 100%" if all_ok else "ERRORS DETECTED") + " ===")
    return all_ok

if __name__ == '__main__':
    run_smoke_tests()
