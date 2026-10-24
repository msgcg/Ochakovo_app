from .services.vk_parser import parse_vk_public_profile
from .services.cumulative_matcher import calculate_cumulative_profile
from .scenarios_facts import SCENARIO_PRO_FACTS
from .services.pdf_export_service import SkillsPdfService
from datetime import datetime
import os
import csv
import requests
import json
import uuid
import re
from pathlib import Path
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.urls import reverse
from django.db.models import Q
from .models import (
    InternshipTrack,
    Vacancy,
    GameScenario,
    ScenarioNode,
    ScenarioChoice,
    GameSession,
    JobApplication,
    StoryMilestone,
    CompanyPerk,
)
from .services.sber_service import OchakovoAIService
from .services.vacancy_crawler import sync_vacancies_to_database, fetch_official_vacancies
from .services.scenario_matcher import match_game_scenario
def home_view(request):
    """Главная посадочная страница бренда работодателя «Очаково»"""
    tracks = InternshipTrack.objects.all().order_by('order')
    featured_vacancies = Vacancy.objects.filter(is_active=True).order_by('order')[:6]
    scenarios = GameScenario.objects.all().order_by('order')[:3]
    milestones = StoryMilestone.objects.all().order_by('order')
    perks = CompanyPerk.objects.all().order_by('order')
    context = {
        'tracks': tracks,
        'featured_vacancies': featured_vacancies,
        'scenarios': scenarios,
        'milestones': milestones,
        'perks': perks,
    }
    return render(request, 'careers/home.html', context)
def game_select_view(request):
    """Выбор производственного сценария / роли в цеху"""
    scenarios = GameScenario.objects.select_related('track', 'target_vacancy').all().order_by('order')
    return render(request, 'careers/game_select.html', {'scenarios': scenarios})
def game_play_view(request, scenario_slug):
    """Интерактивный симулятор завода Очаково: HUD, стойка оборудования, диалог с наставником"""
    SLUG_ALIASES = {
        'bottling_jam': 'krones-robot-tilt',
        'bottling-jam': 'krones-robot-tilt',
        'lab_purity': 'okroshka-detective',
        'lab-purity': 'okroshka-detective',
        'brewing_emergency': 'brew-yeast-flex',
        'brewing-emergency': 'brew-yeast-flex',
        'brew_yeast_flex': 'brew-yeast-flex',
        'brew-yeast-flex': 'brew-yeast-flex',
        'yeast_flex': 'brew-yeast-flex',
        'yeast-flex': 'brew-yeast-flex',
        'krones_robot_tilt': 'krones-robot-tilt',
        'krones-robot-tilt': 'krones-robot-tilt',
        'robot_tilt': 'krones-robot-tilt',
        'robot-tilt': 'krones-robot-tilt',
        'okroshka_detective': 'okroshka-detective',
        'okroshka-detective': 'okroshka-detective',
        'okroshka': 'okroshka-detective',
        'warehouse_drift': 'warehouse-drift',
        'warehouse-drift': 'warehouse-drift',
        'drift': 'warehouse-drift',
        'secret_drop_1978': 'secret-drop-1978',
        'secret-drop-1978': 'secret-drop-1978',
        'secret_drop': 'secret-drop-1978',
        'secret-drop': 'secret-drop-1978',
        'brew_double_fermentation': 'brew-double-fermentation',
        'brew-double-fermentation': 'brew-double-fermentation',
        'double_fermentation': 'brew-double-fermentation',
        'double-fermentation': 'brew-double-fermentation',
        'bot_line_glitch': 'bot-line-glitch',
        'bot-line-glitch': 'bot-line-glitch',
        'line_glitch': 'bot-line-glitch',
        'line-glitch': 'bot-line-glitch',
    }
    resolved_slug = SLUG_ALIASES.get(scenario_slug, scenario_slug)
    scenario = GameScenario.objects.filter(slug=resolved_slug).first()
    if not scenario:
        scenario = GameScenario.objects.filter(slug=resolved_slug.replace('_', '-')).first()
    if not scenario:
        scenario = GameScenario.objects.filter(slug=resolved_slug.replace('-', '_')).first()
    if not scenario:
        scenario = GameScenario.objects.first()
    if not scenario:
        raise Http404("Сценарии симулятора не найдены.")
    
    # Инициализация или продолжение сессии в куки/запросе
    session_id = request.GET.get('session')
    session = None
    if session_id:
        try:
            session = GameSession.objects.get(session_uuid=session_id, scenario=scenario)
        except (GameSession.DoesNotExist, ValueError):
            session = None
    if not session or session.status != 'active':
        session = GameSession.objects.create(
            scenario=scenario,
            current_node_id='start',
            score=50,
            temperature=scenario.initial_temperature,
            brix=scenario.initial_brix,
            line_speed=scenario.initial_line_speed,
            purity=scenario.initial_purity,
            balance=scenario.initial_balance,
            dialogue_history=[]
        )
    # Получаем текущий узел графа
    current_node = ScenarioNode.objects.filter(scenario=scenario, node_id=session.current_node_id).first()
    if not current_node:
        current_node = ScenarioNode.objects.filter(scenario=scenario, node_id='start').first()
    choices = current_node.choices.all().order_by('order') if current_node else []
    # Список сценариев для карусели цехов
    all_scenarios = list(GameScenario.objects.all().order_by('order', 'id'))
    current_idx = 0
    for idx, sc in enumerate(all_scenarios):
        if sc.id == scenario.id:
            current_idx = idx
            break
    prev_scenario = all_scenarios[current_idx - 1] if current_idx > 0 else all_scenarios[-1]
    next_scenario = all_scenarios[(current_idx + 1) % len(all_scenarios)] if all_scenarios else None
    has_owner_gigachat = OchakovoAIService.has_configured_credentials()
    ai_mode = 'gigachat' if has_owner_gigachat else 'offline'
    context = {
        'scenario': scenario,
        'session': session,
        'current_node': current_node,
        'choices': choices,
        'all_scenarios': all_scenarios,
        'prev_scenario': prev_scenario,
        'next_scenario': next_scenario,
        'carousel_position': f"{current_idx + 1} / {len(all_scenarios)}" if all_scenarios else "1 / 1",
        'ai_mode': ai_mode,
        'has_custom_gigachat': False,
        'has_gigachat_credentials': True,
        'pro_facts': SCENARIO_PRO_FACTS.get(scenario.slug, {}),
        'cumulative_profile': calculate_cumulative_profile(request.session, current_scenario=scenario, current_score=session.score if session else 95),
    }
    return render(request, 'careers/game_play.html', context)
@csrf_exempt
@require_POST
def game_action_api(request):
    """
    AJAX API: обработка шага в симуляторе завода Очаково
    Принимает выбор кнопки, свободный текст (или транскрипт голоса) или применение оборудования.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    session_uuid = data.get('session_id')
    choice_id = data.get('choice_id')
    user_text = (data.get('user_text') or '').strip()
    equipment_code = (data.get('equipment_code') or '').strip()
    is_recommended_choice = bool(choice_id or data.get('is_recommended_choice'))
    session = get_object_or_404(GameSession, session_uuid=session_uuid)
    scenario = session.scenario
    reply_text = ""
    feedback_text = ""
    verdict = "success"
    temp_delta = 0.0
    brix_delta = 0.0
    line_delta = 0
    purity_delta = 0
    balance_delta = 0
    score_delta = 15
    is_completed = False
    is_failed = False
    next_node_id = session.current_node_id
    ai_res = {}
    # 1. Если был выбран готовый вариант действия
    if choice_id:
        try:
            choice = ScenarioChoice.objects.get(id=choice_id)
            score_delta = choice.score_delta
            temp_delta = choice.temp_delta
            brix_delta = choice.brix_delta
            line_delta = choice.line_speed_delta
            purity_delta = choice.purity_delta
            balance_delta = choice.balance_delta
            next_node_id = choice.next_node_id
            target_node = ScenarioNode.objects.filter(scenario=scenario, node_id=next_node_id).first()
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            # Проверяем, верен ли выбор действия:
            # верный = положительный прирост баллов и не ведёт в узел срыва/провала
            is_choice_correct = (score_delta > 0) and (next_node_id != 'fail_spoiled') and (not (target_node and target_node.is_terminal and not target_node.is_success))
            if is_choice_correct:
                session.current_node_id = next_node_id
                has_next_choices = ScenarioChoice.objects.filter(node=target_node).exists() if target_node else False
                if target_node and target_node.is_terminal and target_node.is_success:
                    is_completed = True
                    is_failed = False
                    verdict = "success"
                    score_delta = max(35, score_delta)
                    reply_text = choice.mentor_quick_reaction or (target_node.dialogue_text if target_node else f"Отличный выбор! {mentor_name} одобряет: технологический регламент выполнен безупречно!")
                    feedback_text = (target_node.narrative_context if target_node else None) or choice.tactical_hint or "Производственный норматив комбината «Очаково» выдержан на 100%."
                elif has_next_choices:
                    # Даем игроку продолжить ветку сценария на следующем узле
                    is_completed = False
                    is_failed = False
                    verdict = "success"
                    reply_text = choice.mentor_quick_reaction or (target_node.dialogue_text if target_node else f"Верно! {mentor_name} одобряет: переходим к следующему шагу регламента.")
                    feedback_text = choice.tactical_hint or (target_node.narrative_context if target_node else "") or "Шаг регламента успешно пройден."
                elif session.turns_count >= 1:
                    is_completed = True
                    is_failed = False
                    verdict = "success"
                    score_delta = max(30, score_delta)
                    reply_text = choice.mentor_quick_reaction or f"Отличная работа! {mentor_name} жмёт руку: смена успешно отработана, все параметры в норме!"
                    feedback_text = choice.tactical_hint or "Смена успешно завершена в полном соответствии с регламентом комбината «Очаково»."
                else:
                    is_completed = False
                    is_failed = False
                    verdict = "success"
                    reply_text = choice.mentor_quick_reaction or f"Хорошее начало! {mentor_name} подтверждает: регламент соблюдается. Проверь показания и сделай следующее действие!"
                    feedback_text = choice.tactical_hint or "Параметры линии стабилизируются."
            else:
                is_completed = False
                is_failed = False
                verdict = "warning"
                score_delta = max(-10, score_delta)
                temp_delta = min(0.6, max(-0.3, temp_delta))
                if session.temperature + temp_delta >= 29.5:
                    temp_delta = max(0.0, round(29.2 - session.temperature, 1))
                if session.purity + purity_delta <= 45:
                    purity_delta = -4
                reply_text = (
                    f"Так, внимание! Наставник {mentor_name} предостерегает: «Ты что творишь?! "
                    f"Действие „{choice.choice_text}“ здесь недопустимо — так мы партию запорем или сорвем график! "
                    "Включай голову: посмотри на панель датчиков цеха. Напиши мне в рацию или выбери правильное действие, пока есть время!»"
                )
                feedback_text = choice.tactical_hint or "Неверный выбор действия. Наставник сделал предупреждение и дал шанс исправить ситуацию через диалог."
        except ScenarioChoice.DoesNotExist:
            pass
    # 2. Если отправлен свободный текст или перетащено оборудование цеха
    if not choice_id and (user_text or equipment_code):
        ai_res = OchakovoAIService.process_turn(
            scenario=scenario,
            session=session,
            user_message=user_text,
            equipment_code=equipment_code,
            dialogue_history=session.dialogue_history,
            is_recommended_choice=is_recommended_choice
        )
        verdict = ai_res.get('verdict', 'success')
        reply_text = OchakovoAIService._clean_mentor_reply(ai_res.get('mentor_reply', 'Указание принято.'))
        feedback_text = ai_res.get('feedback', '')
        temp_delta = ai_res.get('temp_delta', 0.0)
        brix_delta = ai_res.get('brix_delta', 0.0)
        line_delta = ai_res.get('line_speed_delta', 0)
        purity_delta = ai_res.get('purity_delta', 0)
        balance_delta = ai_res.get('balance_delta', 0)
        score_delta = ai_res.get('score_delta', 15)
        is_completed = ai_res.get('is_completed', False)
        is_failed = ai_res.get('is_failed', False)
        if ai_res.get('score') is not None and (is_completed or is_failed):
            session.score = ai_res['score']
    # Обновляем состояние сессии
    if ai_res.get('score') is None:
        session.score = max(0, min(100, session.score + score_delta))
    session.temperature = round(session.temperature + temp_delta, 1)
    session.brix = round(max(0.0, session.brix + brix_delta), 1)
    session.line_speed = max(0, session.line_speed + line_delta)
    session.purity = max(0, min(100, session.purity + purity_delta))
    session.balance = max(0, min(100, session.balance + balance_delta))
    session.turns_count += 1
    # Производственный регламент комбината «Очаково» (с балансом игры и строгости):
    # Даем игроку 2-3 шага на исправление ситуации, не срывая смену моментально на первом ходу
    if not is_completed:
        if session.temperature >= 29.8 and session.turns_count >= 2:
            is_failed = True
            feedback_text = feedback_text or "Температура сусла превысила критические 29.8°C: термическая гибель закваски, затор скис."
            verdict = "critical_fail"
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            if not any(w in reply_text.lower() for w in ["сорвана", "дождались", "отстранил", "скис"]):
                reply_text = f"Тревога! Аварийный датчик ЦКТ зафиксировал {session.temperature:.1f}°C! Сусло перегрелось и скисло. Наставник {mentor_name} останавливает смену!"
        elif session.temperature >= 29.8 and session.turns_count < 2:
            session.temperature = 29.3
            verdict = "warning"
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            reply_text = f"Опасный нагрев! Датчик ЦКТ подобрался к 29.3°C! {mentor_name} предупреждает: «Срочно открой клапан охлаждения гликолем (-3°C), иначе закваска погибнет!»"
        elif session.purity <= 40 and session.turns_count >= 2:
            is_failed = True
            feedback_text = feedback_text or "Чистота контура CIP упала ниже 40%: критическая угроза микробиологической чистоты напитка."
            verdict = "critical_fail"
        elif session.purity <= 40 and session.turns_count < 2:
            session.purity = 44
            verdict = "warning"
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            reply_text = f"Внимание! Чистота контура CIP на грани 44%! {mentor_name}: «Срочно запусти промывку дезинфектантом перед подачей сусла!»"
        elif session.score <= 15 and session.turns_count >= 2:
            is_failed = True
            feedback_text = feedback_text or "Критическое количество технологических ошибок: наставник отстранил стажёра от смены."
            verdict = "critical_fail"
    if is_completed:
        session.status = 'completed'
        session.current_node_id = 'success_shift'
        session.score = max(session.score, 90)
        session.feedback_text = feedback_text or "Смена успешно закрыта: технологический регламент комбината «Очаково» выдержан на 100%!"
    elif is_failed:
        session.status = 'failed'
        session.current_node_id = 'fail_spoiled'
        session.score = min(session.score, 35)
        session.feedback_text = feedback_text or "Смена сорвана: нарушение технологического регламента производства."
    else:
        session.current_node_id = next_node_id
    # Запись в историю реплик
    history = session.dialogue_history or []
    if user_text or equipment_code:
        action_label = f"[{equipment_code}] " if equipment_code else ""
        history.append({
            'role': 'candidate',
            'text': f"{action_label}{user_text}".strip(),
            'turn': session.turns_count
        })
    history.append({
        'role': 'mentor',
        'text': reply_text,
        'verdict': verdict,
        'turn': session.turns_count
    })
    session.dialogue_history = history
    session.save()
    # Загружаем доступные варианты для следующего узла
    choices_data = []
    if not (is_completed or is_failed):
        # 1. Если ИИ вернул тактические подсказки / рекомендуемые действия (offer_hints)
        if ai_res and ai_res.get('suggested_actions'):
            for act in ai_res['suggested_actions']:
                if isinstance(act, dict):
                    choices_data.append({
                        'id': None,
                        'choice_text': act.get('text', ''),
                        'tactical_hint': act.get('hint', ''),
                        'equipment_code': act.get('equipment_code', '')
                    })
                elif isinstance(act, str):
                    choices_data.append({
                        'id': None,
                        'choice_text': act,
                        'tactical_hint': 'Совет наставника',
                        'equipment_code': ''
                    })
        # 2. Если вариантов от ИИ нет, подгружаем узловые действия из БД
        if not choices_data:
            next_node = ScenarioNode.objects.filter(scenario=scenario, node_id=session.current_node_id).first()
            if next_node:
                for ch in next_node.choices.all().order_by('order'):
                    choices_data.append({
                        'id': ch.id,
                        'choice_text': ch.choice_text,
                        'tactical_hint': ch.tactical_hint,
                        'equipment_code': ch.equipment_code
                    })
        # 3. Дефолтные кнопки цеха, если список всё ещё пуст
        if not choices_data:
            for act in OchakovoAIService._get_default_scenario_actions(scenario, session):
                choices_data.append({
                    'id': None,
                    'choice_text': act.get('text', ''),
                    'tactical_hint': act.get('hint', ''),
                    'equipment_code': act.get('equipment_code', '')
                })
    return JsonResponse({
        'ok': True,
        'status': session.status,
        'score': session.score,
        'temperature': session.temperature,
        'brix': session.brix,
        'line_speed': session.line_speed,
        'purity': session.purity,
        'balance': session.balance,
        'mentor_reply': reply_text,
        'feedback': feedback_text,
        'verdict': verdict,
        'choices': choices_data,
        'is_completed': is_completed,
        'is_failed': is_failed,
        'target_vacancy': {
            'title': scenario.target_vacancy.title if scenario.target_vacancy else scenario.title,
            'salary': scenario.target_vacancy.salary_text if scenario.target_vacancy else 'от 85 000 ₽',
            'slug': scenario.target_vacancy.slug if scenario.target_vacancy else ''
        }
    })
@csrf_exempt
@require_POST
def game_credentials_api(request):
    """
    API управления учетными данными GigaChat и переключения режима ИИ:
    - 'set_gigachat': проверка и сохранение Client ID и Client Secret в сессии
    - 'set_offline': принудительное переключение на локальный биохимический движок
    - 'clear': сброс сохраненных ключей
    - 'get_status': получение текущего режима
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    action = data.get('action', 'set_gigachat')
    if action == 'set_gigachat':
        client_id = (data.get('client_id') or '').strip()
        client_secret = (data.get('client_secret') or '').strip()
        auth_key = (data.get('auth_key') or '').strip()
        if not auth_key and not (client_id and client_secret):
            return JsonResponse({
                'ok': False,
                'status': 'error',
                'message': 'Необходимо указать Client ID и Client Secret (или готовый Auth Key в Base64).'
            }, status=400)
        # Проверяем доступность токена GigaChat через Sber API
        token = OchakovoAIService.get_gigachat_token(auth_key=auth_key, client_id=client_id, client_secret=client_secret)
        if not token:
            return JsonResponse({
                'ok': False,
                'status': 'error',
                'message': 'Не удалось авторизоваться в GigaChat API. Проверьте правильность Client ID и Client Secret или доступ к ngw.devices.sberbank.ru.'
            }, status=401)
        request.session['sber_credentials'] = {
            'client_id': client_id,
            'client_secret': client_secret,
            'auth_key': auth_key
        }
        request.session['force_offline_ai'] = False
        request.session.modified = True
        return JsonResponse({
            'ok': True,
            'status': 'ok',
            'mode': 'gigachat',
            'message': 'Авторизация в Сбер GigaChat прошла успешно! Активирован режим онлайн-нейросети с Function Calling.'
        })
    elif action == 'set_offline':
        request.session['force_offline_ai'] = True
        request.session.modified = True
        return JsonResponse({
            'ok': True,
            'status': 'ok',
            'mode': 'offline',
            'message': 'Активирован интеллектуальный локальный движок комбината «Очаково» (Smart Heuristic Engine).'
        })
    elif action == 'clear':
        if 'sber_credentials' in request.session:
            del request.session['sber_credentials']
        request.session['force_offline_ai'] = False
        request.session.modified = True
        return JsonResponse({
            'ok': True,
            'status': 'ok',
            'mode': 'offline',
            'message': 'Учетные данные GigaChat сброшены.'
        })
    elif action == 'get_status':
        session_creds = request.session.get('sber_credentials', {})
        has_custom = bool(session_creds.get('client_id') and session_creds.get('client_secret')) or bool(session_creds.get('auth_key'))
        has_env = bool(getattr(settings, 'GIGACHAT_CLIENT_ID', '')) or bool(getattr(settings, 'GIGACHAT_AUTH_KEY', ''))
        force_offline = request.session.get('force_offline_ai', False)
        mode = 'offline' if force_offline else ('gigachat' if (has_custom or has_env) else 'offline')
        return JsonResponse({
            'ok': True,
            'mode': mode,
            'has_credentials': has_custom or has_env,
            'force_offline': force_offline
        })
    return JsonResponse({'ok': False, 'status': 'error', 'message': 'Неизвестное действие.'}, status=400)
@csrf_exempt
def game_tts_api(request):
    """Генерация аудио реплики наставника через Edge-TTS / Google TTS"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            text = (data.get('text') or '').strip()
            voice = (data.get('voice') or data.get('speaker_gender') or 'male').strip()
        except Exception:
            text = request.POST.get('text', '').strip()
            voice = request.POST.get('voice', 'male').strip()
    else:
        text = request.GET.get('text', '').strip()
        voice = request.GET.get('voice', 'male').strip()
    if not text:
        return HttpResponse(b'', content_type='audio/mpeg')
    audio_bytes, content_type = OchakovoAIService.synthesize_speech(text, voice_type=voice)
    if audio_bytes:
        resp = HttpResponse(audio_bytes, content_type=content_type)
        resp['Cache-Control'] = 'public, max-age=86400'
        return resp
    return HttpResponse(b'', status=204)
@csrf_exempt
@require_POST
def game_stt_api(request):
    """
    Распознавание речи кандидата (STT) через локальный Whisper Vulkan GPU.
    Принимает аудиозапись с микрофона (multipart/form-data или raw audio stream).
    """
    audio_data = None
    if request.FILES.get('audio'):
        audio_data = request.FILES['audio'].read()
    elif request.body:
        audio_data = request.body
    if not audio_data:
        return JsonResponse({'ok': False, 'error': 'Аудиоданные не получены'}, status=400)
    from .services.whisper_service import WhisperVulkanService
    result = WhisperVulkanService.transcribe(audio_data)
    return JsonResponse(result)
def candidate_progress_view(request):
    """
    Раздел личного прогресса и карьерных достижений стажёра завода «Очаково».
    Позволяет отслеживать баллы по всем цехам, победный стрик,
    квалификационный разряд и сформировать производственный сертификат для hh.ru.
    """
    scenarios = GameScenario.objects.all().order_by('order', 'id')
    vacancies = Vacancy.objects.filter(is_active=True, hh_url__isnull=False).exclude(hh_url='').order_by('-salary_max')[:8]
    if not vacancies.exists():
        vacancies = Vacancy.objects.filter(is_active=True).order_by('-salary_max')[:8]
    tracks = InternshipTrack.objects.all().order_by('order')
    cum_profile = calculate_cumulative_profile(request.session, current_score=request.session.get('current_score', 95))
    context = {
        'scenarios': scenarios,
        'vacancies': vacancies,
        'tracks': tracks,
        'cumulative_profile': cum_profile,
        'page_title': 'Мой прогресс стажировки | Очаково 2026',
    }
    return render(request, 'careers/progress.html', context)
@require_POST
def candidate_progress_api(request):
    """
    API синхронизации прогресса стажёра между клиентом (localStorage) и сервером.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    total_score = int(data.get('total_score', 0))
    cases = data.get('completed_cases', [])
    total_cases = GameScenario.objects.count()
    max_score = total_cases * 100
    rank1 = int(max_score * 0.25)
    rank2 = int(max_score * 0.50)
    rank3 = int(max_score * 0.75)
    if total_score >= rank3:
        rank_title = "Шеф-наставник комбината"
        next_threshold = max_score
    elif total_score >= rank2:
        rank_title = "Инженер-технолог смены"
        next_threshold = rank3
    elif total_score >= rank1:
        rank_title = "Младший сменный мастер"
        next_threshold = rank2
    else:
        rank_title = "Кандидат-практикант"
        next_threshold = rank1
    return JsonResponse({
        'ok': True,
        'total_score': total_score,
        'rank_title': rank_title,
        'next_threshold': next_threshold,
        'cases_count': len(cases),
        'total_cases_count': total_cases
    })
@require_POST
def apply_candidate_api(request):
    """
    Быстрая подача заявки студента на практику или вакансию
    с прикреплением подтверждённого сертификата пройденных цеховых кейсов
    и автоматическим перенаправлением на страницу отклика hh.ru.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    telegram = data.get('telegram', '').strip()
    university = data.get('university', '').strip()
    study_field = data.get('study_field', '').strip()
    course_or_status = data.get('course_or_status', 'Студент / Выпускник').strip()
    session_id = data.get('session_id')
    vacancy_slug = data.get('vacancy_slug')
    vacancy_id = data.get('vacancy_id')
    if not full_name or not phone:
        return JsonResponse({'ok': False, 'error': 'Пожалуйста, укажите ваше имя и контактный телефон.'}, status=400)
    target_vacancy = None
    target_track = None
    if vacancy_slug:
        target_vacancy = Vacancy.objects.filter(slug=vacancy_slug).first()
    elif vacancy_id:
        target_vacancy = Vacancy.objects.filter(id=vacancy_id).first()
    if target_vacancy:
        target_track = target_vacancy.track
    session = None
    game_score = None
    if session_id:
        try:
            session = GameSession.objects.get(session_uuid=session_id)
            game_score = session.score
            if not target_vacancy and session.scenario.target_vacancy:
                target_vacancy = session.scenario.target_vacancy
                target_track = target_vacancy.track
        except Exception:
            pass
    # Разбор переданных кейсов из локального прогресса соискателя
    completed_cases_raw = data.get('completed_cases')
    completed_cases = []
    if isinstance(completed_cases_raw, str):
        try:
            completed_cases = json.loads(completed_cases_raw)
        except Exception:
            completed_cases = []
    elif isinstance(completed_cases_raw, list):
        completed_cases = completed_cases_raw
    # Если передан session_id, но нет массива кейсов — фиксируем текущий
    if session and not completed_cases:
        completed_cases.append({
            'slug': session.scenario.slug,
            'title': session.scenario.title,
            'workshop': session.scenario.workshop_name,
            'mentor': session.scenario.mentor_name,
            'score': session.score,
            'status': session.status
        })
    # Расчет суммарного рейтинга и квалификационного разряда
    total_score = sum(int(c.get('score', 0)) for c in completed_cases) if completed_cases else (game_score or 50)
    if total_score >= 270:
        rank_title = "Шеф-наставник комбината"
    elif total_score >= 180:
        rank_title = "Инженер-технолог смены"
    elif total_score >= 90:
        rank_title = "Младший сменный мастер"
    else:
        rank_title = "Кандидат-практикант"
    # Формируем официальный производственный сертификат стажёра для hh.ru
    vac_name = target_vacancy.title if target_vacancy else "Оплачиваемая практика в АО «Очаково»"
    cert_lines = [
        "===========================================================",
        "ПРОИЗВОДСТВЕННЫЙ СЕРТИФИКАТ СТАЖЁРА КОМБИНАТА «ОЧАКОВО» (2026)",
        f"Вакансия: {vac_name}",
        f"Соискатель: {full_name} | Тел: {phone} | Email: {email or 'не указан'}",
        f"Учебное заведение: {university or 'ВУЗ / Колледж'} ({study_field or 'Техническая специальность'}, {course_or_status})",
        f"Итоговый карьерный рейтинг: {total_score} баллов | Разряд: {rank_title}",
        "-----------------------------------------------------------",
        "ПОДТВЕРЖДЁННЫЕ ПРАКТИЧЕСКИЕ КЕЙСЫ НА СИМУЛЯТОРЕ ЗАВОДА:"
    ]
    if completed_cases:
        for idx, c in enumerate(completed_cases, 1):
            c_title = c.get('title') or c.get('name') or 'Смена'
            c_workshop = c.get('workshop') or 'Производственный цех'
            c_score = c.get('score', 95)
            c_mentor = c.get('mentor') or 'Сменный наставник'
            cert_lines.append(f"{idx}. {c_title} [{c_workshop}] — {c_score}/100 баллов (Наставник: {c_mentor})")
    elif session:
        cert_lines.append(f"1. {session.scenario.title} [{session.scenario.workshop_name}] — {session.score}/100 баллов (Наставник: {session.scenario.mentor_name})")
    else:
        cert_lines.append("• Базовый квалификационный профиль стажёра пищевого производства.")
    cert_lines.extend([
        "-----------------------------------------------------------",
        "ПОДТВЕРЖДЁННЫЕ ПРОИЗВОДСТВЕННЫЕ НАВЫКИ:",
        "• Терморегуляция рубашки охлаждения ЦКТ (-3°C гликоль) по стандарту 1978 года;",
        "• Диагностика и устранение блокировок упаковочных роботов Krones (35 000+ банок/час);",
        "• Контроль параметров плотности затора рефрактометром Brix и титруемой кислотности pH;",
        "• Работа с терминалом WMS и регламентом скоростного паллетирования продукции.",
        "==========================================================="
    ])
    user_comment = data.get('comment', '').strip()
    if user_comment:
        cert_lines.append("\nМотивация соискателя:")
        cert_lines.append(user_comment)
    full_cover_letter = "\n".join(cert_lines)
    # Определение реального URL вакансии на hh.ru
    # Официальный каталог вакансий Очаково на hh.ru: https://hh.ru/vacancies/ochakovo
    official_company_hh_url = "https://hh.ru/vacancies/ochakovo"
    target_hh_url = official_company_hh_url
    hh_vacancy_id = None
    if target_vacancy:
        if target_vacancy.hh_url and target_vacancy.hh_url.strip():
            target_hh_url = target_vacancy.hh_url.strip()
            m = re.search(r'vacancy/(\d+)', target_hh_url)
            if m:
                hh_vacancy_id = m.group(1)
        elif target_vacancy.slug.startswith('hh-'):
            hh_vacancy_id = target_vacancy.slug.replace('hh-', '')
            target_hh_url = f"https://hh.ru/vacancy/{hh_vacancy_id}"
        elif target_vacancy.track:
            fallback_vac = Vacancy.objects.filter(
                track=target_vacancy.track, 
                hh_url__isnull=False
            ).exclude(hh_url='').first()
            if fallback_vac and fallback_vac.hh_url:
                target_hh_url = fallback_vac.hh_url
                m = re.search(r'vacancy/(\d+)', target_hh_url)
                if m:
                    hh_vacancy_id = m.group(1)
    # Канонический URL вакансии на hh.ru гарантированно открывается у любых пользователей
    if hh_vacancy_id:
        hh_response_url = f"https://hh.ru/vacancy/{hh_vacancy_id}"
    else:
        hh_response_url = target_hh_url
    vk_user = request.session.get('vk_user') or {}
    vk_url = vk_user.get('profile_url', '')

    app = JobApplication.objects.create(
        full_name=full_name,
        phone=phone,
        email=email,
        telegram=telegram,
        vk_url=vk_url,
        university=university or "ВУЗ / Колледж",
        study_field=study_field or "Техническая специальность",
        course_or_status=course_or_status,
        target_track=target_track,
        target_vacancy=target_vacancy,
        game_session=session,
        game_score=game_score or total_score,
        cumulative_score=total_score or game_score or 95,
        recommended_role=target_vacancy.title if target_vacancy else "Мастер-технолог смены",
        internship_reduction="Сокращение стажировки на 50%",
        completed_cases=completed_cases,
        hh_response_url=hh_response_url,
        cover_letter=full_cover_letter,
        source='vk' if vk_url else ('simulator' if session else 'site'),
        status='new'
    )
    return JsonResponse({
        'ok': True,
        'application_id': app.id,
        'hh_url': hh_response_url,
        'hh_vacancy_id': hh_vacancy_id,
        'cover_letter': full_cover_letter,
        'total_score': total_score,
        'rank_title': rank_title,
        'cases_count': len(completed_cases),
        'message': f'Отлично, {full_name}! Ваша заявка зарегистрирована в HR «Очаково», а сертификат с {total_score} баллами скопирован в буфер обмена для отклика на hh.ru!'
    })
def vacancies_list_view(request):
    """Каталог сезонных вакансий и программ оплачиваемой практики с онлайн-актуализацией"""
    # Если в базе мало вакансий (первый запуск), подтягиваем официальные позиции с ochakovo.ru
    if Vacancy.objects.count() < 10:
        try:
            sync_vacancies_to_database(force_refresh=False)
        except Exception:
            pass
    city = request.GET.get('city', '').strip()
    track_slug = request.GET.get('track', '').strip()
    q = request.GET.get('q', '').strip()
    has_game = request.GET.get('has_game', '').strip() in ('1', 'true', 'yes')
    qs = Vacancy.objects.filter(is_active=True).select_related('track')
    if city:
        qs = qs.filter(city=city)
    if track_slug:
        qs = qs.filter(track__slug=track_slug)
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(department__icontains=q) |
            Q(responsibilities__icontains=q)
        )
    vacancies = list(qs)
    if has_game:
        vacancies = [v for v in vacancies if v.matched_scenario]
    tracks = InternshipTrack.objects.all().order_by('order')
    
    # Города: Москва всегда первая, остальные по алфавиту
    raw_cities = set(Vacancy.objects.values_list('city', flat=True).distinct())
    cities = []
    if 'Москва' in raw_cities:
        cities.append('Москва')
        raw_cities.remove('Москва')
    cities.extend(sorted(list(raw_cities)))
    # Считаем, сколько вакансий имеют игровой симулятор
    total_with_simulator = sum(1 for v in Vacancy.objects.filter(is_active=True) if v.matched_scenario)
    context = {
        'vacancies': vacancies,
        'tracks': tracks,
        'cities': cities,
        'current_city': city,
        'current_track': track_slug,
        'search_query': q,
        'has_game': has_game,
        'total_vacancies_count': Vacancy.objects.filter(is_active=True).count(),
        'total_with_simulator': total_with_simulator,
    }
    return render(request, 'careers/vacancies_list.html', context)
@require_GET
def vacancies_search_api(request):
    """
    Интерактивный AJAX API для мгновенного поиска и фильтрации вакансий без перезагрузки страницы.
    Возвращает актуальный список с regex-сопоставлением с игровым симулятором завода.
    """
    q = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    track_slug = request.GET.get('track', '').strip()
    has_game = request.GET.get('has_game', '').strip() in ('1', 'true', 'yes')
    qs = Vacancy.objects.filter(is_active=True).select_related('track')
    if city:
        qs = qs.filter(city=city)
    if track_slug:
        qs = qs.filter(track__slug=track_slug)
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(department__icontains=q) |
            Q(responsibilities__icontains=q)
        )
    results = []
    for vac in qs:
        scenario = vac.matched_scenario
        if has_game and not scenario:
            continue
        results.append({
            'id': vac.id,
            'slug': vac.slug,
            'title': vac.title,
            'city': vac.city,
            'track_slug': vac.track.slug if vac.track else '',
            'track_name': vac.track.title if vac.track else 'Производство',
            'track_color': vac.track.accent_color if vac.track else '#D50032',
            'salary_text': vac.salary_text,
            'schedule': vac.schedule,
            'experience_level': vac.experience_level,
            'is_seasonal_peak': vac.is_seasonal_peak,
            'is_student_friendly': vac.is_student_friendly,
            'has_dormitory': vac.has_dormitory,
            'description_snippet': vac.description[:160] + ('...' if len(vac.description) > 160 else ''),
            'hh_url': vac.hh_url,
            'detail_url': reverse('careers:vacancy_detail', kwargs={'slug': vac.slug}),
            'matched_scenario': scenario,
            'game_url': reverse('careers:game_play', kwargs={'scenario_slug': scenario['scenario_slug']}) if scenario else None
        })
    return JsonResponse({
        'ok': True,
        'count': len(results),
        'total_in_db': Vacancy.objects.filter(is_active=True).count(),
        'items': results
    })
@csrf_exempt
@require_POST
def vacancies_sync_api(request):
    """
    Принудительная синхронизация актуальных вакансий с официального сайта ochakovo.ru
    """
    try:
        res = sync_vacancies_to_database(force_refresh=True)
        return JsonResponse({
            'ok': True,
            'message': f"Синхронизировано {res['total_fetched']} вакансий с официального сайта «Очаково»!",
            'data': res
        })
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)
def vacancy_detail_view(request, slug):
    """Карточка вакансии с Schema.org разметкой JobPosting"""
    vacancy = get_object_or_404(Vacancy, slug=slug, is_active=True)
    related_scenarios = GameScenario.objects.filter(
        Q(target_vacancy=vacancy) | Q(track=vacancy.track)
    ).order_by('order')[:2]
    context = {
        'vacancy': vacancy,
        'related_scenarios': related_scenarios,
    }
    return render(request, 'careers/vacancy_detail.html', context)
def story_view(request):
    """История комбината «Очаково», технологии и ценности"""
    milestones = StoryMilestone.objects.all().order_by('order')
    perks = CompanyPerk.objects.all().order_by('order')
    return render(request, 'careers/story.html', {'milestones': milestones, 'perks': perks})
def offline_view(request):
    """Офлайн-страница для PWA с прямым доступом ко всем 7 кейсам симулятора"""
    scenarios = GameScenario.objects.all().order_by('order', 'id')
    vacancies = Vacancy.objects.filter(is_active=True).order_by('-salary_max')[:4]
    return render(request, 'careers/offline.html', {
        'scenarios': scenarios,
        'vacancies': vacancies,
        'page_title': 'Автономный режим | Очаково 2026',
    })
def manifest_view(request):
    """Выдача PWA Web App Manifest с корректным Content-Type"""
    manifest_path = settings.BASE_DIR / 'static' / 'manifest.json'
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/manifest+json; charset=utf-8')
    except Exception:
        return JsonResponse({'error': 'manifest not found'}, status=404)
def video_stream_view(request, filename):
    """
    Потоковая выдача видеороликов вакансий и инструктажей цеха завода «Очаково».
    Поддерживает стандартные HTTP Range-запросы (HTTP 206 Partial Content, Accept-Ranges: bytes),
    что критически важно для браузеров (Chromium, Firefox, Safari) для воспроизведения AAC-аудиодорожки
    и плавной перемотки без потери звука.
    """
    from django.http import Http404, HttpResponse, FileResponse
    video_dir = Path(settings.MEDIA_ROOT) / 'videos'
    video_path = video_dir / filename
    if not video_path.exists() or not video_path.is_file():
        raise Http404("Видеоролик не найден")
    file_size = video_path.stat().st_size
    range_header = request.headers.get('Range', '').strip()
    if range_header and range_header.startswith('bytes='):
        range_val = range_header.replace('bytes=', '').strip()
        parts = range_val.split('-')
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
        if end >= file_size:
            end = file_size - 1
        if start > end:
            start = 0
        length = end - start + 1
        with open(video_path, 'rb') as f:
            f.seek(start)
            data = f.read(length)
        resp = HttpResponse(data, status=206, content_type='video/mp4')
        resp['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        resp['Accept-Ranges'] = 'bytes'
        resp['Content-Length'] = str(length)
        resp['Cache-Control'] = 'public, max-age=86400'
        return resp
    else:
        resp = FileResponse(open(video_path, 'rb'), content_type='video/mp4')
        resp['Accept-Ranges'] = 'bytes'
        resp['Content-Length'] = str(file_size)
        resp['Cache-Control'] = 'public, max-age=86400'
        return resp
def service_worker_view(request):
    """Выдача Service Worker с корня домена с корректным Service-Worker-Allowed header"""
    sw_path = settings.BASE_DIR / 'static' / 'sw.js'
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        resp = HttpResponse(content, content_type='application/javascript; charset=utf-8')
        resp['Service-Worker-Allowed'] = '/'
        return resp
    except Exception:
        return HttpResponse('console.log("sw not found");', content_type='application/javascript')
# ==============================================================================
# VK ID OAUTH 2.0 & STAND LEAD CAPTURE & PDF EXPORT
# ==============================================================================
# ==============================================================================
# ПАРСЕР ПРОФИЛЯ ВК (ВХОД БЕЗ OAUTH 2.0) & ДИНАМИЧЕСКИЙ QR СТЕНДА
# ==============================================================================
@csrf_exempt
@require_POST
def vk_parse_login_api(request):
    """
    Авторизация кандидата через ссылку или юзернейм ВКонтакте (без OAuth 2.0).
    Парсит открытый профиль, подтягивает имя, аватарку и ID, сохраняя в сессию.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    query = data.get('query', '').strip()
    next_url = data.get('next') or request.session.get('vk_oauth_next', '/progress/')
    user_profile = parse_vk_public_profile(query)
    request.session['vk_user'] = user_profile
    request.session.modified = True

    try:
        JobApplication.objects.update_or_create(
            vk_url=user_profile.get('profile_url', ''),
            defaults={
                'full_name': user_profile.get('full_name') or user_profile.get('first_name', 'Кандидат ВК'),
                'university': user_profile.get('university') or "ВУЗ соискателя",
                'study_field': user_profile.get('study_field') or "Технология напитков",
                'source': 'vk',
                'cumulative_score': 95,
                'recommended_role': 'Мастер-технолог бродильного цеха',
                'internship_reduction': 'Сокращение стажировки на 50%',
                'status': 'new'
            }
        )
    except Exception as e:
        print(f'[VK Lead Register Error] {e}')

    return JsonResponse({
        'ok': True,
        'user': user_profile,
        'redirect_url': next_url
    })
def dynamic_stand_qr_api(request):
    """
    Динамическая генерация валидного SVG QR-кода на симулятор смены в зависимости от текущего домена/хоста.
    """
    target = request.GET.get('target', '').strip()
    if not target:
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        scenario_slug = request.GET.get('scenario', 'brew-yeast-flex')
        target = f"{scheme}://{host}/game/{scenario_slug}/?from=stand_qr"
    try:
        from reportlab.graphics.barcode.qr import QrCodeWidget
        w = QrCodeWidget(target)
        w.draw()
        modules = w.qr.modules
        n = len(modules)
        border = 2
        total = n + border * 2
        rects = []
        for r, row in enumerate(modules):
            for c, cell in enumerate(row):
                if cell:
                    rects.append(f'<rect x="{c + border}" y="{r + border}" width="1.02" height="1.02" fill="#0F172A"/>')
        
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}" width="180" height="180" shape-rendering="crispEdges">'
            f'<rect width="{total}" height="{total}" fill="#FFFFFF"/>'
            + "".join(rects) +
            '</svg>'
        )
        resp = HttpResponse(svg, content_type='image/svg+xml')
        resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    except Exception as exc:
        print(f"[Dynamic Stand QR Error] {exc}")
        return redirect(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={target}")
def vk_oauth_login_view(request):
    """
    Вход ВКонтакте без OAuth 2.0:
    Перенаправляет на модальное окно парсинга публичного профиля.
    """
    next_url = request.GET.get('next', '/progress/')
    return redirect(f"/?open_vk=1&next={next_url}")
def vk_oauth_callback_view(request):
    """
    Обработка ответа OAuth 2.0 от ВКонтакте: получение токена и профиля кандидата.
    """
    code = request.GET.get('code')
    error = request.GET.get('error')
    next_url = request.session.get('vk_oauth_next', '/progress/')
    if error or not code:
        return redirect(f"{next_url}?vk_error=cancelled")
    client_id = getattr(settings, 'VK_CLIENT_ID', os.environ.get('VK_CLIENT_ID', ''))
    client_secret = getattr(settings, 'VK_CLIENT_SECRET', os.environ.get('VK_CLIENT_SECRET', ''))
    redirect_uri = getattr(settings, 'VK_REDIRECT_URI', os.environ.get('VK_REDIRECT_URI', ''))
    if not redirect_uri:
        redirect_uri = request.build_absolute_uri('/auth/vk/callback/')
    try:
        token_url = "https://oauth.vk.com/access_token"
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': code
        }
        resp = requests.get(token_url, params=params, timeout=10)
        token_data = resp.json()
        access_token = token_data.get('access_token')
        user_id = token_data.get('user_id')
        user_email = token_data.get('email', '')
        if access_token and user_id:
            profile_resp = requests.get("https://api.vk.com/method/users.get", params={
                'user_ids': user_id,
                'fields': 'photo_200,city,bdate',
                'access_token': access_token,
                'v': '5.199'
            }, timeout=10)
            pdata = profile_resp.json().get('response', [{}])[0]
            first_name = pdata.get('first_name', 'Стажёр')
            last_name = pdata.get('last_name', 'Очаково')
            full_name = f"{first_name} {last_name}".strip()
            avatar = pdata.get('photo_200', '')
            city = pdata.get('city', {}).get('title', 'Москва')
            request.session['vk_user'] = {
                'id': user_id,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name,
                'avatar': avatar,
                'email': user_email,
                'city': city,
                'is_demo': False
            }
            return redirect(f"{next_url}?vk_auth=success")
    except Exception as exc:
        print(f"[VK OAuth Error] {exc}")
    return redirect(f"{next_url}?vk_error=network_error")
def vk_oauth_demo_view(request):
    """
    Моментальный 1-клик демо-вход через VK ID для стенда или локального тестирования.
    Позволяет протестировать весь цикл авторизации соискателя без регистрации VK App.
    """
    next_url = request.session.get('vk_oauth_next') or request.GET.get('next', '/progress/')
    # Устанавливаем реалистичный профиль московского студента-технолога
    request.session['vk_user'] = {
        'id': 70364404,
        'first_name': 'Максим',
        'last_name': 'Соколов',
        'full_name': 'Максим Соколов',
        'avatar': '/static/img/avatar_student_boy.jpg',
        'email': 'sokolov.ochakovo@vk.com',
        'city': 'Москва',
        'university': 'МГУТУ им. К.Г. Разумовского',
        'study_field': 'Технология бродильных производств и виноделие',
        'is_demo': True
    }
    return redirect(f"{next_url}?vk_auth=demo_success")
def candidate_logout_view(request):
    """Выход кандидата из сессии VK ID"""
    if 'vk_user' in request.session:
        del request.session['vk_user']
    next_url = request.GET.get('next', '/')
    return redirect(next_url)
@csrf_exempt
@require_POST
def stand_lead_capture_api(request):
    """
    Быстрый сбор лидов и контактов соискателей на выставочном стенде / по QR-коду.
    Мгновенно подбирает 3 наиболее релевантные вакансии и сохраняет заявку.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    full_name = (data.get('full_name') or '').strip()
    phone = (data.get('phone') or '').strip()
    telegram = (data.get('telegram') or '').strip()
    email = (data.get('email') or '').strip()
    university = (data.get('university') or 'Стенд / Карьерный форум').strip()
    track_slug = (data.get('track_slug') or '').strip()
    if not full_name or not (phone or telegram or email):
        return JsonResponse({'ok': False, 'error': 'Укажите ФИО и хотя бы один контакт (телефон, Telegram или Email)'}, status=400)
    # Поиск подходящего карьерного трека
    target_track = None
    if track_slug:
        target_track = InternshipTrack.objects.filter(slug=track_slug).first()
    if not target_track:
        target_track = InternshipTrack.objects.first()
    # Поиск 3 лучших вакансий
    matched_vacs = Vacancy.objects.filter(is_active=True)
    if target_track:
        matched_vacs = matched_vacs.filter(track=target_track)
    matched_vacs = matched_vacs.order_by('-salary_max')[:3]
    vacancies_data = []
    for v in matched_vacs:
        vacancies_data.append({
            'id': v.id,
            'title': v.title,
            'salary': f"от {v.salary_min:,} до {v.salary_max:,} ₽".replace(',', ' ') if v.salary_max else "по договоренности",
            'department': v.department,
            'url': v.hh_url or f"/vacancies/{v.slug}/"
        })
    # Сохранение заявки в базу
    best_vac = matched_vacs.first() if matched_vacs.exists() else None
    app = JobApplication.objects.create(
        full_name=full_name,
        phone=phone,
        telegram=telegram,
        email=email or f"{telegram.replace('@', '')}@t.me",
        university=university,
        study_field='Практика со стенда комбината',
        target_track=target_track,
        target_vacancy=best_vac,
        source='stand_qr',
        cumulative_score=request.session.get('current_score', 85),
        recommended_role=best_vac.title if best_vac else "Мастер-технолог смены",
        internship_reduction="Сокращение стажировки на 50%",
        status='new',
        cover_letter=f"Экспресс-заявка с выставочного стенда АО «Очаково» (QR-вход)."
    )
    return JsonResponse({
        'ok': True,
        'message': f"Спасибо, {full_name}! Ваша заявка принята в приоритетную очередь HR комбината.",
        'application_id': app.id,
        'matched_vacancies': vacancies_data,
        'bonuses': [
            "Сокращение срока стажировки до 1 месяца",
            "Прямое направление в HR без промежуточных этапов",
            "Допуск к испытаниям на должности 2 категории (от 80 000 ₽)"
        ]
    })
def export_skills_pdf_view(request):
    """
    Генерация и скачивание официального PDF паспорта компетенций соискателя комбината «Очаково».
    """
    vk_user = request.session.get('vk_user', {})
    full_name = request.GET.get('name') or vk_user.get('full_name') or 'Стажёр комбината «Очаково»'
    university = request.GET.get('uni') or vk_user.get('university') or 'Московский технологический университет'
    score = int(request.GET.get('score', 420))
    rank_title = request.GET.get('rank') or 'Младший технолог-практикант (Разряд II)'
    candidate_data = {
        'full_name': full_name,
        'university': university,
        'total_score': score,
        'rank_title': rank_title,
    }
    try:
        pdf_bytes = SkillsPdfService.generate_passport(candidate_data)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"Ochakovo_Skills_Passport_{datetime.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as exc:
        print(f"[PDF Export Error] {exc}")
        return HttpResponse(f"Ошибка формирования PDF: {exc}", status=500)


# ==============================================================================
# АДМИНИСТРАТИВНЫЙ ДАШБОРД АНАЛИТИКИ И ВЫГРУЗКИ ПОСЕТИТЕЛЕЙ САЙТА
# ==============================================================================
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg

@staff_member_required(login_url='/admin/login/')
def admin_analytics_dashboard_view(request):
    """
    Интерактивный дашборд статистики всех посетителей комбината «Очаково»:
    воронка конверсии, распределение по каналам (QR-стенды, VK, сайт),
    типы устройств и динамика активности соискателей.
    """
    from .models import SiteVisitor, GameSession, JobApplication, Vacancy, GameScenario
    
    total_visitors = SiteVisitor.objects.count()
    total_page_views = sum(SiteVisitor.objects.values_list('page_views_count', flat=True)) or 0
    
    # 1. Каналы трафика (источники)
    source_counts = dict(SiteVisitor.objects.values('source').annotate(c=Count('id')).values_list('source', 'c'))
    sources_data = [
        {
            'key': 'stand_qr',
            'name': 'Стенды / QR-коды',
            'icon': '📱',
            'color': '#F59E0B',
            'bg': '#FEF3C7',
            'count': source_counts.get('stand_qr', 0),
            'percent': round(source_counts.get('stand_qr', 0) / max(1, total_visitors) * 100, 1)
        },
        {
            'key': 'vk',
            'name': 'ВКонтакте (VK ID)',
            'icon': '🌐',
            'color': '#0284C7',
            'bg': '#E0F2FE',
            'count': source_counts.get('vk', 0),
            'percent': round(source_counts.get('vk', 0) / max(1, total_visitors) * 100, 1)
        },
        {
            'key': 'site',
            'name': 'Прямой заход на сайт',
            'icon': '💻',
            'color': '#334155',
            'bg': '#F1F5F9',
            'count': source_counts.get('site', 0),
            'percent': round(source_counts.get('site', 0) / max(1, total_visitors) * 100, 1)
        },
        {
            'key': 'hh',
            'name': 'HeadHunter (hh.ru)',
            'icon': '💼',
            'color': '#D50032',
            'bg': '#FEE2E2',
            'count': source_counts.get('hh', 0),
            'percent': round(source_counts.get('hh', 0) / max(1, total_visitors) * 100, 1)
        },
    ]
    
    # 2. Устройства и платформы
    device_counts = dict(SiteVisitor.objects.values('device_type').annotate(c=Count('id')).values_list('device_type', 'c'))
    devices_data = [
        {'name': 'Смартфоны', 'icon': '📱', 'count': device_counts.get('mobile', 0), 'percent': round(device_counts.get('mobile', 0) / max(1, total_visitors) * 100, 1)},
        {'name': 'ПК / Ноутбуки', 'icon': '🖥️', 'count': device_counts.get('desktop', 0), 'percent': round(device_counts.get('desktop', 0) / max(1, total_visitors) * 100, 1)},
        {'name': 'Планшеты', 'icon': '📟', 'count': device_counts.get('tablet', 0), 'percent': round(device_counts.get('tablet', 0) / max(1, total_visitors) * 100, 1)},
    ]
    
    # 3. Воронка конверсии кандидатов
    played_count = SiteVisitor.objects.filter(has_played_game=True).count()
    completed_count = SiteVisitor.objects.filter(has_completed_shift=True).count()
    applied_count = JobApplication.objects.count()
    approved_count = JobApplication.objects.filter(status='practice_approved').count()
    
    funnel_stages = [
        {'step': 1, 'name': 'Посетители сайта', 'count': total_visitors, 'percent': 100, 'color': '#3B82F6', 'desc': 'Уникальные визиты и сессии'},
        {'step': 2, 'name': 'Запуск симулятора', 'count': played_count, 'percent': round(played_count / max(1, total_visitors) * 100, 1), 'color': '#8B5CF6', 'desc': 'Вход в цеховой инцидент завода'},
        {'step': 3, 'name': 'Успешная смена', 'count': completed_count, 'percent': round(completed_count / max(1, total_visitors) * 100, 1), 'color': '#10B981', 'desc': 'Партия напитка сварена и спасена'},
        {'step': 4, 'name': 'Подано заявок на практику', 'count': applied_count, 'percent': round(applied_count / max(1, total_visitors) * 100, 1), 'color': '#F59E0B', 'desc': 'Заполнен отклик с подтверждением навыков'},
        {'step': 5, 'name': 'Одобрены на практику', 'count': approved_count, 'percent': round(approved_count / max(1, total_visitors) * 100, 1), 'color': '#D50032', 'desc': 'Оформлен трудовой договор и сокращение стажировки'},
    ]
    
    # 4. Последние визиты и недавние заявки
    recent_visitors = SiteVisitor.objects.all().order_by('-last_visit')[:25]
    recent_applications = JobApplication.objects.select_related('target_vacancy', 'target_track').all().order_by('-created_at')[:8]
    
    context = {
        'title': 'Сводная аналитика посещаемости и воронки соискателей «Очаково»',
        'total_visitors': total_visitors,
        'total_page_views': total_page_views,
        'sources_data': sources_data,
        'devices_data': devices_data,
        'funnel_stages': funnel_stages,
        'recent_visitors': recent_visitors,
        'recent_applications': recent_applications,
        'played_count': played_count,
        'completed_count': completed_count,
        'applied_count': applied_count,
        'approved_count': approved_count,
        'conversion_rate': round(applied_count / max(1, total_visitors) * 100, 1),
    }
    return render(request, 'admin/analytics_dashboard.html', context)


@staff_member_required(login_url='/admin/login/')
def admin_analytics_export_csv(request):
    """
    Экспорт полного реестра всех посетителей сайта в формате CSV для Excel.
    """
    from .models import SiteVisitor
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="ochakovo_visitors_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
    response.write('﻿')  # UTF-8 BOM для корректного отображения кириллицы в Excel
    
    writer = csv.writer(response)
    writer.writerow([
        'ID Сессии',
        'Пользователь / VK',
        'ID ВКонтакте',
        'Устройство',
        'Браузер и ОС',
        'IP-адрес',
        'Канал входа',
        'Страница входа',
        'Последняя страница',
        'Источник (Referer)',
        'Просмотров страниц',
        'Запуск симулятора',
        'Успех смены',
        'Баллы (XP)',
        'Подал заявку',
        'Первый визит',
        'Последняя активность',
    ])
    
    for v in SiteVisitor.objects.all().order_by('-last_visit'):
        writer.writerow([
            v.session_key,
            v.vk_name or 'Гость',
            v.vk_user_id,
            v.get_device_type_display(),
            v.browser_os,
            v.ip_address,
            v.get_source_display(),
            v.landing_page,
            v.last_page,
            v.referrer,
            v.page_views_count,
            'Да' if v.has_played_game else 'Нет',
            'Да' if v.has_completed_shift else 'Нет',
            v.last_game_score if v.last_game_score is not None else '—',
            'Да' if v.has_applied else 'Нет',
            v.first_visit.strftime('%d.%m.%Y %H:%M'),
            v.last_visit.strftime('%d.%m.%Y %H:%M'),
        ])
    
    return response

