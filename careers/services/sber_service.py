import os
import re
import json
import time
import uuid
import urllib3
import requests
import asyncio
from pathlib import Path
from django.conf import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False


class OchakovoAIService:
    """
    Интеллектуальный сервис наставничества и симуляции производства «Очаково»:
    1. GigaChat API с поддержкой Function Calling (оценка производственных решений кандидата,
       управление параметрами брожения ЦКТ, линиями розлива и качеством).
    2. Интеллектуальный локальный эвристический движок (Smart Offline Fallback)
       с полной эмуляцией Function Calling при отсутствии токена.
    3. Потоковый синтез речи наставников цеха через Edge-TTS / SaluteSpeech.
    """

    _gigachat_token = None
    _gigachat_cached_key = None
    _gigachat_expires_at = 0

    @classmethod
    def get_gigachat_token(cls, auth_key: str = None, client_id: str = None, client_secret: str = None) -> str | None:
        key = (auth_key or '').strip()
        if not key:
            c_id = (client_id or getattr(settings, 'GIGACHAT_CLIENT_ID', '')).strip()
            c_sec = (client_secret or getattr(settings, 'GIGACHAT_CLIENT_SECRET', '')).strip()
            if c_id and c_sec:
                import base64
                key = base64.b64encode(f"{c_id}:{c_sec}".encode('utf-8')).decode('utf-8')

        if not key:
            key = getattr(settings, 'GIGACHAT_AUTH_KEY', '').strip()

        if not key:
            return None

        current_time = int(time.time() * 1000)
        if getattr(cls, '_gigachat_cached_key', None) == key and cls._gigachat_token and (cls._gigachat_expires_at - current_time > 60000):
            return cls._gigachat_token

        scope = getattr(settings, 'GIGACHAT_SCOPE', 'GIGACHAT_API_PERS')
        oauth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Authorization": f"Basic {key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"scope": scope}

        try:
            resp = requests.post(oauth_url, headers=headers, data=data, verify=False, timeout=12)
            if resp.status_code == 200:
                res_data = resp.json()
                cls._gigachat_token = res_data.get("access_token")
                cls._gigachat_cached_key = key
                cls._gigachat_expires_at = res_data.get("expires_at", current_time + 1800000)
                return cls._gigachat_token
        except Exception as exc:
            print(f"[OchakovoAIService] Ошибка OAuth GigaChat: {exc}")

        return None

    @classmethod
    def _extract_json(cls, text: str) -> dict:
        """Извлекает и парсит JSON из ответа модели GigaChat"""
        if not text:
            return {}
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        candidate = match.group(1).strip() if match else text.strip()
        brace_start = candidate.find('{')
        brace_end = candidate.rfind('}')
        if brace_start != -1 and brace_end != -1:
            candidate = candidate[brace_start:brace_end+1]
        try:
            return json.loads(candidate)
        except Exception:
            return {}

    @classmethod
    def _clean_mentor_reply(cls, reply: str) -> str:
        """Очищает реплику наставника от любых остатков вызовов функций, скобок или JSON-синтаксиса"""
        if not reply:
            return ""
        # 1. Удаляем любые конструкции вида (resolve_production_incident(...)), (complete_shift(...)), (offer_hints(...))
        reply = re.sub(r'\(?\b(?:resolve_production_incident|complete_shift|offer_hints)\s*\([\s\S]*?\)\)?', '', reply)
        # 2. Удаляем префиксы вроде (resolve_production_incident...) если скобка осталась
        reply = re.sub(r'^\s*\(?\s*(?:resolve_production_incident|complete_shift|offer_hints)[^\)]*\)?\s*', '', reply)
        # 3. Удаляем двоеточия, скобки, тире в начале
        reply = re.sub(r'^[\s:\-\)]+', '', reply).strip()
        # 4. Удаляем возможные остатки JSON ключей
        reply = re.sub(r'["\'](?:mentor_reply|character_reply|reply)["\']\s*:\s*', '', reply)
        return reply.strip()

    @classmethod
    def _parse_inline_function_call(cls, content_text: str) -> tuple[dict | None, str]:
        """
        Обнаруживает и извлекает вызовы функций, случайно сгенерированные моделью в виде псевдокода
        в текстовом контенте (например: (resolve_production_incident(verdict='success', is_shift_completed=False)) Текст реплики...).
        Возвращает (func_call_dict, clean_text_reply).
        """
        if not content_text:
            return None, ""

        # 1. Поиск псевдокода вызова функции: (func_name(...)) или func_name(...)
        pattern = r'\(?\b(resolve_production_incident|complete_shift|offer_hints)\s*\(([\s\S]*?)\)\)?'
        match = re.search(pattern, content_text)
        if match:
            func_name = match.group(1)
            raw_args = match.group(2)
            clean_reply = (content_text[:match.start()] + content_text[match.end():]).strip()
            clean_reply = re.sub(r'^[\s:\-\)]+', '', clean_reply).strip()

            args = {}
            for kv in re.finditer(r'([a-zA-Z_]\w*)\s*=\s*(?:[\'"](.*?)[\'"]|([a-zA-Z0-9_\.\-]+))', raw_args):
                k = kv.group(1)
                v = kv.group(2) if kv.group(2) is not None else kv.group(3)
                if isinstance(v, str):
                    if v.lower() == 'true': v = True
                    elif v.lower() == 'false': v = False
                    elif v.lower() == 'none': v = None
                    else:
                        try:
                            if '.' in v: v = float(v)
                            else: v = int(v)
                        except ValueError:
                            pass
                args[k] = v

            if clean_reply and "mentor_reply" not in args:
                args["mentor_reply"] = clean_reply

            return {"name": func_name, "arguments": args}, clean_reply

        # 2. Поиск JSON внутри контента с полями "function_call" или "name"
        json_obj = cls._extract_json(content_text)
        if json_obj and ("name" in json_obj or "function_call" in json_obj):
            if "function_call" in json_obj:
                return json_obj["function_call"], ""
            return {"name": json_obj.get("name"), "arguments": json_obj.get("arguments", json_obj)}, ""

        return None, content_text

    @classmethod
    def _get_default_scenario_actions(cls, scenario, session) -> list:
        """Рекомендуемые интерактивные варианты действий стажёра в цеху"""
        slug = getattr(scenario, 'slug', '')
        if slug in ['krones-robot-tilt', 'bot-line-glitch']:
            return [
                {"text": "Поправить банку-бунтаря на транспортере", "hint": "Освобождает луч оптического датчика Krones", "equipment_code": ""},
                {"text": "Продуть фотодатчик сжатым воздухом", "hint": "Сбрасывает ошибку оптического позиционера", "equipment_code": ""},
                {"text": "Нажать аварийный стоп конвейера", "hint": "Экстренная остановка при угрозе боя тары", "equipment_code": "emergency_stop"}
            ]
        elif slug == 'lab-qa-crisis':
            return [
                {"text": "Замерить плотность сусла рефрактометром Brix", "hint": "Определяет уровень сбраживаемых сахаров", "equipment_code": "refractometer"},
                {"text": "Проверить титруемую кислотность pH-метром", "hint": "Норма кислотности для настоящего кваса", "equipment_code": "ph_meter"},
                {"text": "Сделать дегустационную пробу из пробоотборника", "hint": "Органолептический тест вкуса и резкости", "equipment_code": "tasting_mug"}
            ]
        elif slug == 'okroshka-detective':
            return [
                {"text": "Выбрать резкий белый квас с хреном", "hint": "Традиционный русский рецепт окрошки", "equipment_code": ""},
                {"text": "Выбрать классический квас «Очаковский»", "hint": "Двойное натуральное брожение с 1978 года", "equipment_code": ""},
                {"text": "Предложить дегустацию всей смене цеха", "hint": "Народное голосование подтвердит превосходство кваса", "equipment_code": ""}
            ]
        elif slug == 'warehouse-drift':
            return [
                {"text": "Обмотать паллету стретчем и отсканировать в WMS", "hint": "Безопасная транспортировка по регламенту склада", "equipment_code": ""},
                {"text": "Подать груз на рампу №14 к фуре", "hint": "Своевременная отправка партии кваса в торговые сети", "equipment_code": ""},
                {"text": "Проверить температурный режим рефрижератора", "hint": "Контроль сохранности напитков в пути", "equipment_code": ""}
            ]
        elif slug == 'secret-drop-1978':
            return [
                {"text": "Изучить архивный журнал варок 1978 года", "hint": "Точные пропорции томлёного ржаного солода", "equipment_code": ""},
                {"text": "Запустить тестовую партию ретро-банки «Очаково»", "hint": "Запуск лимитированной юбилейной серии", "equipment_code": ""},
                {"text": "Провести органолептический тест закваски", "hint": "Проверка подлинности исторического вкуса", "equipment_code": ""}
            ]
        else:
            return [
                {"text": "Открыть клапан охлаждения рубашки гликолем (-3°C)", "hint": "Снижает температуру сусла до оптимальных 25.5°C", "equipment_code": "valve_cooling"},
                {"text": "Внести чистую закваску «Очаково 1978»", "hint": "Восстанавливает баланс молочнокислого брожения", "equipment_code": "starter_culture"},
                {"text": "Замерить плотность рефрактометром Brix", "hint": "Контроль расхода сахаров сусла", "equipment_code": "refractometer"}
            ]

    @classmethod
    def get_function_declarations(cls) -> list:
        """
        Спецификация функций (Function Calling) для интерактивного судейства смены в цеху «Очаково»
        по архитектуре симулятора скоростных магистралей ВСМ.
        """
        return [
            {
                "name": "complete_shift",
                "description": (
                    "Окончательно завершить производственную смену успехом (verdict='success') или провалом (verdict='failed'). "
                    "В СВОБОДНОМ ДИАЛОГЕ со стажёром вызывай ТОЛЬКО ПОСЛЕ того, как состоялся содержательный диалог (как минимум 2–3 реплики с наставником), "
                    "и проблема либо полностью решена, либо стажёр упорно настаивал на нарушениях вопреки предупреждениям. "
                    "ИСКЛЮЧЕНИЕ: если стажёр выбрал готовое рекомендуемое действие из кнопок и оно верное — смену можно завершить сразу."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "verdict": {
                            "type": "string",
                            "enum": ["success", "failed"],
                            "description": "'success' если партия спасена/смена сдана; 'failed' если допущен брак или авария."
                        },
                        "mentor_reply": {
                            "type": "string",
                            "description": "Живая эмоциональная реплика наставника от первого лица с похвалой или разбором ошибки."
                        },
                        "technical_feedback": {
                            "type": "string",
                            "description": "Производственное объяснение по регламенту комбината «Очаково»."
                        },
                        "score": {
                            "type": "integer",
                            "description": "Итоговая оценка мастерства от 85 до 100 при успехе (или 15-40 при провале)."
                        },
                        "temp_delta": {"type": "number", "description": "Изменение температуры сусла (°C)"},
                        "brix_delta": {"type": "number", "description": "Изменение плотности Brix"},
                        "line_speed_delta": {"type": "integer", "description": "Изменение скорости розлива"},
                        "purity_delta": {"type": "integer", "description": "Изменение чистоты контура CIP"},
                        "balance_delta": {"type": "integer", "description": "Изменение баланса закваски"}
                    },
                    "required": ["verdict", "mentor_reply", "technical_feedback"]
                }
            },
            {
                "name": "offer_hints",
                "description": (
                    "Предоставить стажёру тактическую подсказку от наставника и конкретные варианты действий в цеху, "
                    "если стажёр теряется, затрудняется или прямо просит совет («Михалыч, подскажи», «дай совет», «помоги», «что делать»)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mentor_reply": {
                            "type": "string",
                            "description": "Реплика наставника с живым советом от первого лица."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Тактическое пояснение, на какие датчики цеха обратить внимание."
                        },
                        "suggested_actions": {
                            "type": "array",
                            "description": "2-3 конкретных варианта действий для кнопок стажёра.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "description": "Текст действия (без эмодзи)"},
                                    "hint": {"type": "string", "description": "Тактическое пояснение"},
                                    "equipment_code": {"type": "string", "description": "Код оборудования цеха, если применимо"}
                                },
                                "required": ["text"]
                            }
                        }
                    },
                    "required": ["mentor_reply", "reason", "suggested_actions"]
                }
            },
            {
                "name": "resolve_production_incident",
                "description": (
                    "Продолжить живой диалог со стажёром в ходе смены. Используй эту функцию во время начального общения (первые 2–3 реплики стажёра), "
                    "чтобы обсудить ситуацию в цехе, похвалить правильную мысль, предупредить об ошибке, скорректировать показатели датчиков цеха, "
                    "но НЕ закрывать смену преждевременно."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "verdict": {
                            "type": "string",
                            "enum": ["success", "warning", "critical_fail"],
                            "description": "Результат: success (верно), warning (спорное), critical_fail (нарушение)"
                        },
                        "mentor_reply": {
                            "type": "string",
                            "description": "Реплика наставника от первого лица."
                        },
                        "technical_feedback": {
                            "type": "string",
                            "description": "Краткое производственное объяснение."
                        },
                        "temp_delta": {"type": "number"},
                        "brix_delta": {"type": "number"},
                        "line_speed_delta": {"type": "integer"},
                        "purity_delta": {"type": "integer"},
                        "balance_delta": {"type": "integer"},
                        "score_delta": {"type": "integer"},
                        "is_shift_completed": {"type": "boolean"}
                    },
                    "required": ["verdict", "mentor_reply", "score_delta", "is_shift_completed"]
                }
            }
        ]

    @classmethod
    def process_turn(
        cls,
        scenario,
        session,
        user_message: str = "",
        equipment_code: str = "",
        dialogue_history: list = None,
        custom_auth_key: str = None,
        custom_client_id: str = None,
        custom_client_secret: str = None,
        force_offline: bool = False,
        is_recommended_choice: bool = False
    ) -> dict:
        """
        Главная точка обработки хода игрока.
        Если доступен токен GigaChat (из сессии или settings) и не включен force_offline —
        отправляет запрос в REST API с Function Calling.
        Если токена нет — активирует умный биохимический локальный движок.
        """
        token = None
        if not force_offline:
            token = cls.get_gigachat_token(auth_key=custom_auth_key, client_id=custom_client_id, client_secret=custom_client_secret)

        if token:
            try:
                return cls._call_gigachat_turn(
                    token=token,
                    scenario=scenario,
                    session=session,
                    user_message=user_message,
                    equipment_code=equipment_code,
                    dialogue_history=dialogue_history,
                    is_recommended_choice=is_recommended_choice
                )
            except Exception as exc:
                print(f"[OchakovoAIService] Ошибка вызова GigaChat, переход на локальный движок: {exc}")

        # Локальный интеллектуальный движок (детерминированный + эвристика)
        return cls._run_local_heuristic_turn(
            scenario=scenario,
            session=session,
            user_message=user_message,
            equipment_code=equipment_code,
            is_recommended_choice=is_recommended_choice
        )

    @classmethod
    def _call_gigachat_turn(
        cls,
        token: str,
        scenario,
        session,
        user_message: str,
        equipment_code: str,
        dialogue_history: list = None,
        is_recommended_choice: bool = False
    ) -> dict:
        """Запрос к GigaChat REST API с functions и авто-вызовом"""
        api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        equipment_map = {
            "valve_cooling": "Открытие/регулировка клапана гликолевой рубашки охлаждения ЦКТ (-3°C)",
            "starter_culture": "Внесение чистой закваски натурального двойного брожения (штамм Очаково-1978)",
            "cip_wash": "Запуск контура CIP-мойки и стерилизации трубопроводов",
            "emergency_stop": "Аварийный стоп конвейерной линии розлива",
            "refractometer": "Замер сахаров и плотности сусла оптическим рефрактометром Brix",
            "tasting_mug": "Органолептическая дегустация и сенсорный контроль кваса из пробоотборника",
            "intercom_radio": "Вызов диспетчерской службы завода по интеркому",
            "ph_meter": "Экспресс-анализ титруемой кислотности и pH"
        }
        eq_desc = equipment_map.get(equipment_code, "")

        system_prompt = f"""Ты — интерактивный сменный наставник в молодёжном игровом симуляторе завода «Очаково» (Москва, пик сезона 2026).
ТВОЯ РОЛЬ: {scenario.mentor_name} ({scenario.mentor_role}).
ЦЕХ: {scenario.workshop_name}.
СЦЕНАРИЙ: {scenario.title}.
ТЕКУЩИЕ ПАРАМЕТРЫ ДАТЧИКОВ:
- Температура сусла: {session.temperature:.1f} °C (норма: {scenario.target_temp_min} - {scenario.target_temp_max} °C)
- Плотность затора Brix: {session.brix:.1f} °Brix (норма: {scenario.target_brix_min} - {scenario.target_brix_max})
- Скорость линии розлива: {session.line_speed} бут/час
- Чистота контура CIP: {session.purity}%
- Баланс закваски: {session.balance}/100

ДЛЯ УПРАВЛЕНИЯ СМЕНОЙ И ДАТЧИКАМИ ОБЯЗАТЕЛЬНО ИСПОЛЬЗУЙ ВЫЗОВ ФУНКЦИЙ (Function Calling):
- resolve_production_incident: для каждого шага стажёра в цеху, корректировки параметров датчиков и ведения диалога.
- complete_shift: для окончательного завершения смены (успех или провал).
- offer_hints: если стажёр растерялся и просит совет или подсказку.

СТРОЖАЙШИЙ ЗАПРЕТ:
КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать названия функций или псевдокод вызова (например '(resolve_production_incident(...))') в тексте сообщения!
Реплика наставника передаётся ИСКЛЮЧИТЕЛЬНО в аргументе mentor_reply вызываемой функции! Вне вызова функции текст ответа должен быть пустым!

ВАЖНЕЙШИЕ ПРАВИЛА ВЕДЕНИЯ СМЕНЫ И СУДЕЙСТВА:
1. РЕЖИМ ЖИВОГО ДИАЛОГА СО СТАЖЁРОМ (КОГДА СТАЖЁР ПИШЕТ В ЧАТ ИЛИ ГОВОРИТ ГОЛОСОМ):
   - НЕ ЗАВЕРШАЙ СМЕНУ СЛИШКОМ РАНО! Дай пользователю пару сообщений (минимум 2–3 реплики) пообщаться с наставником {scenario.mentor_name}.
   - Если стажёр предлагает правильную мысль в начале диалога (ходы 1–2):
     * Похвали его живым заводским языком, но НЕ завершай смену сразу! Продолжи диалог: вызови функцию resolve_production_incident с параметрами verdict='success', is_shift_completed=False, скорректируй датчики (например, temp_delta=-2.5 при охлаждении) и задай уточняющий вопрос или предложи подтвердить действие.
   - Если стажёр ошибся или чего-то не понимает в начале диалога:
     * НЕ ВАЛИ СМЕНУ СРАЗУ! Сделай эмоциональное замечание-подсказку от лица {scenario.mentor_name}: вызови функцию resolve_production_incident с параметром verdict='warning', объясни суть ошибки по технологии завода «Очаково» и направь его мысль к верному решению.
   - Окончательное завершение смены через функцию complete_shift:
     * УСПЕХ: вызывай только после содержательного диалога (от 2–3 реплик стажёра), когда технологические параметры стабилизированы и стажёр довёл решение инцидента до победного конца.
     * ПРОВАЛ: вызывай, только если стажёр после повторных предупреждений упорно саботирует процесс, игнорирует наставника или настаивает на грубых нарушениях.

2. РЕЖИМ ГОТОВЫХ РЕКОМЕНДУЕМЫХ КНОПОК:
   - Если стажёр нажал вариант ответа из рекомендуемых кнопок и он верный — СРАЗУ завершай смену успехом: вызывай функцию complete_shift с параметрами verdict='success', score=95! (Раз юзер выбирает из предложенных вариантов, значит он не хочет долго общаться, и смена должна сразу засчитаться).
   - Если же выбранный кнопочный вариант неверный — НЕ вали смену сразу! Наставник делает предупреждение, объясняет ошибку и переводит пользователя в режим диалога, чтобы вместе исправить ситуацию.

3. СТРОГИЙ КОНТРОЛЬ БЕЗДЕЙСТВИЯ («ПОДОЖДАТЬ», «ПОДОЖДЁМ», «ПОСМОТРИМ», «НЕ СПЕШИ»):
   - В цеху завода «Очаково» в экстренной ситуации ЖДАТЬ НЕЛЬЗЯ!
   - Если стажёр пишет «подождать», «посмотрим», «подождём»:
     * 1-й и 2-й раз: сделай строгие предупреждения-подсказки: вызови функцию resolve_production_incident с параметрами verdict='warning', score_delta=-10, temp_delta=1.1, объясняя от лица {scenario.mentor_name}, что время не ждёт и сусло перегревается!
     * 3-й раз (или если в истории диалога стажёр уже получал подсказки не ждать и снова упорно пишет «подождать»): СРАЗУ ЗАВЕРШАЙ СМЕНУ ПРОВАЛОМ: вызови функцию complete_shift с параметрами verdict='failed', score=25, temp_delta=2.2! Наставник объявляет: «Всё, дождались! Сусло сварилось, смена сорвана из-за промедления!»

4. ЕСЛИ СТАЖЁР ТЕРЯЕТСЯ ИЛИ ПРОСИТ СОВЕТ («дай совет», «подскажи», «что делать», «помоги»):
   - ОБЯЗАТЕЛЬНО вызови функцию offer_hints!
   - В mentor_reply дай конкретный, остроумный совет заводского эксперта строго от лица {scenario.mentor_name}.
   - В suggested_actions передай 2-3 варианта быстрых действий стажёра (без эмодзи).

5. ХАРАКТЕР И СТИЛЬ ОБЩЕНИЯ НАСТАВНИКА:
   - Общайся строго от первого лица своего персонажа ({scenario.mentor_name} — {scenario.mentor_role})!
   - Говори бодро, живо, с теплым цеховым юмором («Дрожжевой флекс», «Банка встала на ребро — робот в тильте», «Окрошка на квасе — абсолютная база всея Руси», «Килька в деле — квас в теле!»).
   - За удачные действия щедро хвали, за ошибки сурово разбирай нарушение регламента.
"""

        stall_keywords = [
            "подожд", "ждать", "погодим", "погодить", "обожд", "посмотрим",
            "поглядим", "понаблюда", "ничего не дела", "не делать ничего",
            "не трогать", "постоит", "не спеши", "не торопи", "минутк", "секунд",
            "позже", "потом", "время терпит", "время есть", "тянуть время", "пауза", "перекур",
            "посидеть", "посидим", "помолчим"
        ]
        history_stalls = 0
        if dialogue_history:
            for turn in dialogue_history:
                r = turn.get("role")
                txt = (turn.get("text") or turn.get("content") or "").lower()
                if r in ["user", "candidate"] and any(kw in txt for kw in stall_keywords):
                    history_stalls += 1

        is_current_stall = any(kw in (user_message or "").lower() for kw in stall_keywords)

        user_content_items = []
        if is_recommended_choice:
            user_content_items.append("ℹ️ [РЕЖИМ]: Стажёр нажал быструю кнопку действия из списка предложенных вариантов цеха.")
        else:
            user_content_items.append(f"ℹ️ [РЕЖИМ СВОБОДНОГО ДИАЛОГА]: Стажёр общается в чате с наставником (реплика {session.turns_count + 1}). Не завершай смену моментально, веди содержательный диалог!")

        if user_message:
            user_content_items.append(f"Слова стажёра: «{user_message.strip()}»")
        if eq_desc:
            user_content_items.append(f"Действие с оборудованием цеха: [{eq_desc}]")
        if not user_message and not eq_desc:
            user_content_items.append("Стажёр внимательно осматривает панель датчиков и ждет указаний.")

        if is_current_stall:
            if history_stalls >= 2:
                user_content_items.append(
                    f"⚠️ [КРИТИЧЕСКИЙ РЕГЛАМЕНТ ДЛЯ НАСТАВНИКА]: Стажёр уже получал 2 предупреждения и в 3-й раз предлагает ждать! "
                    f"Время вышло, сусло скисло / авария на линии! ТЫ ОБЯЗАН СРАЗУ ВЫЗВАТЬ функцию complete_shift с параметрами verdict='failed', score=25 "
                    f"и объявить смену сорванной из-за прокрастинации стажёра!"
                )
            else:
                user_content_items.append(
                    f"⚠️ [ПОДСКАЗКА НАСТАВНИКА]: Стажёр предлагает ждать (предупреждение {history_stalls + 1} из 2). "
                    f"Сделай строгое предупреждение через функцию resolve_production_incident с параметром verdict='warning', "
                    f"что в цехе ждать нельзя, и подскажи правильное действие!"
                )

        messages = [{"role": "system", "content": system_prompt}]
        if dialogue_history:
            for turn in dialogue_history[-8:]:
                r = "user" if turn.get("role") in ["user", "candidate"] else "assistant"
                txt = turn.get("text") or turn.get("content") or ""
                if txt:
                    messages.append({"role": r, "content": txt})

        messages.append({"role": "user", "content": "\n".join(user_content_items)})

        payload = {
            "model": getattr(settings, 'GIGACHAT_MODEL', 'GigaChat-Max'),
            "messages": messages,
            "temperature": 0.35,
            "functions": cls.get_function_declarations(),
            "function_call": "auto"
        }

        resp = requests.post(api_url, headers=headers, json=payload, verify=False, timeout=25)
        if resp.status_code == 200:
            res_json = resp.json()
            choice_msg = res_json.get("choices", [{}])[0].get("message", {})
            func_call = choice_msg.get("function_call")
            content_text = (choice_msg.get("content") or "").strip()

            # КРИТИЧЕСКИЙ ПЕРЕХВАТ: если GigaChat выдал псевдокод вызова функции в тексте
            # (например, (resolve_production_incident(...))), либо JSON в content_text вместо choice_msg["function_call"]
            if not func_call and content_text:
                extracted_call, clean_reply = cls._parse_inline_function_call(content_text)
                if extracted_call:
                    func_call = extracted_call
                    if clean_reply:
                        content_text = clean_reply

            # Вспомогательная функция расчёта изменения датчиков с учётом действий пользователя и реплики
            def _calc_sensor_deltas(args_dict, is_c, is_f, raw_text=""):
                combined_txt = f"{user_message or ''} {equipment_code or ''} {raw_text}".lower()
                is_cooling = any(w in combined_txt for w in ["охлажд", "клапан", "гликол", "сбить темп", "снизить темп", "рубашк"])
                is_warming = any(w in combined_txt for w in ["нагрев", "пар ", "подогре", "тепл"])
                is_ferment = any(w in combined_txt for w in ["закваск", "брожен", "штамм", "дрожж", "1978"])
                is_speed = any(w in combined_txt for w in ["конвейер", "крон", "krones", "скорост", "линия", "розлив", "банка"])
                is_cip = any(w in combined_txt for w in ["cip", "мойк", "стерил", "промыв", "контур"])
                is_brix = any(w in combined_txt for w in ["brix", "брикс", "плотност", "рефрактометр", "сахар"])

                # Температура (°C)
                if args_dict.get("temp_delta") is not None:
                    try:
                        t_delta = float(args_dict["temp_delta"])
                    except Exception:
                        t_delta = 0.0
                elif is_cooling:
                    t_delta = -2.6 if session.temperature > 26.0 else -1.5
                elif is_warming:
                    t_delta = 1.8
                elif is_c and session.temperature > 26.5:
                    t_delta = -2.8
                elif is_f:
                    t_delta = 2.0
                else:
                    t_delta = 0.0

                # Плотность Brix
                if args_dict.get("brix_delta") is not None:
                    try:
                        b_delta = float(args_dict["brix_delta"])
                    except Exception:
                        b_delta = 0.0
                elif is_brix or is_c:
                    b_delta = -0.3 if session.brix > 11.5 else 0.0
                else:
                    b_delta = 0.0

                # Скорость розлива
                if args_dict.get("line_speed_delta") is not None:
                    try:
                        s_delta = int(args_dict["line_speed_delta"])
                    except Exception:
                        s_delta = 0
                elif is_speed:
                    s_delta = 2000 if not is_f else -4000
                elif is_c:
                    s_delta = 2000
                elif is_f:
                    s_delta = -5000
                else:
                    s_delta = 0

                # Чистота контура CIP
                if args_dict.get("purity_delta") is not None:
                    try:
                        p_delta = int(args_dict["purity_delta"])
                    except Exception:
                        p_delta = 0
                elif is_cip:
                    p_delta = 8
                elif is_c:
                    p_delta = 4
                elif is_f:
                    p_delta = -5
                else:
                    p_delta = 0

                # Баланс чистой закваски
                if args_dict.get("balance_delta") is not None:
                    try:
                        bal_delta = int(args_dict["balance_delta"])
                    except Exception:
                        bal_delta = 0
                elif is_ferment:
                    bal_delta = 12
                elif is_c:
                    bal_delta = 15
                elif is_f:
                    bal_delta = -15
                else:
                    bal_delta = 0

                return t_delta, b_delta, s_delta, p_delta, bal_delta

            if func_call:
                func_name = func_call.get("name")
                args = func_call.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}

                if func_name == "complete_shift":
                    verdict = (args.get("verdict") or "success").lower()
                    raw_comp = verdict in ["success", "completed", "passed"]
                    raw_failed = verdict in ["failed", "critical_fail", "fail"]
                    mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')

                    # Правило: в свободном диалоге (текст/голос) даём стажёру пообщаться 2-3 реплики перед завершением
                    if not is_recommended_choice and session.turns_count < 2:
                        if raw_comp:
                            # Стажёр предложил верное решение в начале диалога: хвалим, но не закрываем смену раньше времени
                            is_comp = False
                            is_failed = False
                            verdict = "success"
                            reply = args.get("mentor_reply") or f"Отличная мысль, стажёр! Наставник {mentor_name} одобряет направление. Проверь остальные датчики цеха и подтверди следующее действие!"
                            score = max(session.score, 65)
                        elif raw_failed and not (is_current_stall and history_stalls >= 2):
                            # Не валим смену сразу в начале диалога (если это не 3-й упорный отказ действовать)
                            is_comp = False
                            is_failed = False
                            verdict = "warning"
                            reply = args.get("mentor_reply") or f"Так, стажёр, наставник {mentor_name} предостерегает: это ошибочный шаг! Внимательно посмотри на панель приборов и предложи верное решение!"
                            score = max(25, session.score - 10)
                        else:
                            is_comp = raw_comp
                            is_failed = raw_failed
                            reply = args.get("mentor_reply") or ("Отличная работа! Смена в цеху закрыта на высший балл!" if is_comp else "Смена сорвана: допущено нарушение регламента комбината «Очаково».")
                            score = int(args.get("score", 95 if is_comp else 25))
                    else:
                        is_comp = raw_comp
                        is_failed = raw_failed
                        reply = args.get("mentor_reply") or ("Отличная работа! Смена в цеху закрыта на высший балл!" if is_comp else "Смена сорвана: допущено нарушение регламента комбината «Очаково».")
                        score = int(args.get("score", 95 if is_comp else 25))

                    reply = cls._clean_mentor_reply(reply)
                    feedback = args.get("technical_feedback") or ("Технологический норматив комбината выдержан на 100%." if is_comp else ("Предупреждение наставника: требуется корректировка технологического режима." if not is_failed else "Нарушение параметров производственного процесса."))

                    t_delta, b_delta, s_delta, p_delta, bal_delta = _calc_sensor_deltas(args, is_comp, is_failed, reply)

                    return {
                        "ok": True,
                        "function_triggered": True,
                        "verdict": verdict,
                        "mentor_reply": reply,
                        "feedback": feedback,
                        "temp_delta": t_delta,
                        "brix_delta": b_delta,
                        "line_speed_delta": s_delta,
                        "purity_delta": p_delta,
                        "balance_delta": bal_delta,
                        "score_delta": 35 if is_comp else (-30 if is_failed else 15),
                        "score": score,
                        "is_completed": is_comp,
                        "is_failed": is_failed
                    }

                elif func_name == "offer_hints":
                    mentor_reply = cls._clean_mentor_reply(args.get("mentor_reply") or "Держи подсказку от наставника цеха:")
                    reason = args.get("reason") or "Обрати внимание на ключевые показания приборов цеха."
                    suggested = args.get("suggested_actions", [])
                    return {
                        "ok": True,
                        "function_triggered": True,
                        "verdict": "warning",
                        "mentor_reply": mentor_reply,
                        "feedback": reason,
                        "temp_delta": 0.0,
                        "brix_delta": 0.0,
                        "line_speed_delta": 0,
                        "purity_delta": 0,
                        "balance_delta": 0,
                        "score_delta": 5,
                        "show_hints": True,
                        "hint_reason": reason,
                        "suggested_actions": suggested,
                        "is_completed": False,
                        "is_failed": False
                    }

                elif func_name == "resolve_production_incident":
                    verdict = args.get("verdict", "success")
                    if is_recommended_choice and verdict in ["success", "completed"]:
                        # Если нажат рекомендуемый вариант и он верный — закрываем смену успехом сразу!
                        is_comp = True
                        is_fail = False
                    else:
                        # В свободном диалоге завершаем только после содержательного общения (2+ реплики)
                        is_comp = bool(args.get("is_shift_completed", False)) and session.turns_count >= 2
                        is_fail = (verdict == "critical_fail") and (session.turns_count >= 2 or (is_current_stall and history_stalls >= 2))
                        if verdict == "critical_fail" and not is_fail:
                            verdict = "warning"

                    reply = cls._clean_mentor_reply(args.get("mentor_reply", "Действие принято наставником."))
                    feedback = args.get("technical_feedback", "Параметры скорректированы.")

                    t_delta, b_delta, s_delta, p_delta, bal_delta = _calc_sensor_deltas(args, is_comp, is_fail, reply)

                    return {
                        "ok": True,
                        "function_triggered": True,
                        "verdict": verdict,
                        "mentor_reply": reply,
                        "feedback": feedback,
                        "temp_delta": t_delta,
                        "brix_delta": b_delta,
                        "line_speed_delta": s_delta,
                        "purity_delta": p_delta,
                        "balance_delta": bal_delta,
                        "score_delta": int(args.get("score_delta", 30 if is_comp else 15)),
                        "is_completed": is_comp,
                        "is_failed": is_fail
                    }

            # Если модель вернула текстовый контент (JSON или прямую речь) — НЕ выбрасываем его!
            if content_text:
                parsed = cls._extract_json(content_text)
                if parsed and ("mentor_reply" in parsed or "verdict" in parsed or "character_reply" in parsed):
                    raw_reply = parsed.get("mentor_reply") or parsed.get("character_reply") or content_text
                    reply = cls._clean_mentor_reply(raw_reply)
                    verdict = parsed.get("verdict", "success")
                    status = parsed.get("status", "")
                    if is_recommended_choice and (verdict in ["success", "completed"] or parsed.get("is_completed")):
                        is_comp = True
                        is_fail = False
                    else:
                        is_comp = (parsed.get("is_completed", False) or status == "completed") and session.turns_count >= 2
                        is_fail = (parsed.get("is_failed", False) or status == "failed" or verdict == "critical_fail") and (session.turns_count >= 2 or (is_current_stall and history_stalls >= 2))
                        if verdict == "critical_fail" and not is_fail:
                            verdict = "warning"

                    t_delta, b_delta, s_delta, p_delta, bal_delta = _calc_sensor_deltas(parsed, is_comp, is_fail, reply)

                    return {
                        "ok": True,
                        "function_triggered": True,
                        "verdict": verdict,
                        "mentor_reply": reply,
                        "feedback": parsed.get("feedback") or parsed.get("technical_feedback", "Решение проверено по регламенту «Очаково»."),
                        "temp_delta": t_delta,
                        "brix_delta": b_delta,
                        "line_speed_delta": s_delta,
                        "purity_delta": p_delta,
                        "balance_delta": bal_delta,
                        "score_delta": 30 if is_comp else 15,
                        "is_completed": is_comp,
                        "is_failed": is_fail
                    }
                else:
                    lower_content = content_text.lower()
                    if is_recommended_choice:
                        is_comp = any(w in lower_content for w in ["смена принята", "партия спасена", "отличная работа", "молодец", "смена закрыта", "успешно сдал", "высший балл", "верно", "правильно"])
                        is_fail = False
                        verdict = "success"
                    else:
                        is_comp = session.turns_count >= 2 and any(w in lower_content for w in ["смена принята", "партия спасена", "отличная работа", "молодец", "смена закрыта", "успешно сдал", "высший балл"])
                        is_fail = (is_current_stall and history_stalls >= 2) or (session.turns_count >= 2 and any(w in lower_content for w in ["смена сорвана", "брак", "авария", "уволен", "провал", "сорвана", "отстранен", "отстранён"]))
                        verdict = "critical_fail" if is_fail else ("success" if is_comp else "warning")

                    clean_reply = cls._clean_mentor_reply(content_text)
                    t_delta, b_delta, s_delta, p_delta, bal_delta = _calc_sensor_deltas({}, is_comp, is_fail, clean_reply)

                    return {
                        "ok": True,
                        "function_triggered": True,
                        "verdict": verdict,
                        "mentor_reply": clean_reply,
                        "feedback": "Оценка сменного наставника комбината «Очаково»." if not is_fail else "Смена сорвана из-за недопустимой пассивности или нарушения регламента.",
                        "temp_delta": t_delta,
                        "brix_delta": b_delta,
                        "line_speed_delta": s_delta,
                        "purity_delta": p_delta,
                        "balance_delta": bal_delta,
                        "score_delta": 35 if is_comp else (-30 if is_fail else 15),
                        "score": 25 if is_fail else (95 if is_comp else session.score),
                        "is_completed": is_comp,
                        "is_failed": is_fail
                    }

        # Если function call не сработал напрямую, откатываемся на эвристику
        return cls._run_local_heuristic_turn(
            scenario=scenario,
            session=session,
            user_message=user_message,
            equipment_code=equipment_code,
            is_recommended_choice=is_recommended_choice
        )

    @classmethod
    def _run_local_heuristic_turn(
        cls,
        scenario,
        session,
        user_message: str = "",
        equipment_code: str = "",
        is_recommended_choice: bool = False
    ) -> dict:
        """
        Высокоточный эвристический движок для симуляции с полной поддержкой биохимических
        и инженерных правил комбината Очаково (гарантирует мгновенный отклик без ключей).
        """
        msg_lower = (user_message or "").lower()
        eq = equipment_code or ""

        temp = session.temperature
        brix = session.brix

        # 0. Запрос совета / подсказки от наставника («Михалыч дай совет», «подскажи», «что делать», «помоги»)
        if any(w in msg_lower for w in ["совет", "подскажи", "помоги", "что делать", "как быть", "как поступить", "вариант", "научи", "посоветуй", "поясни", "что нажать", "с чего начать"]):
            slug = getattr(scenario, 'slug', '')
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            actions = cls._get_default_scenario_actions(scenario, session)

            if slug in ['krones-robot-tilt', 'bot-line-glitch']:
                advice_reply = (
                    f"Так, стажёр, держи совет от {mentor_name}: немецкий робот-манипулятор Krones встал в тильт, "
                    "потому что алюминиевая банка 0.45л встала на ребро и перекрыла лазерный датчик! Твоё действие: "
                    "аккуратно поправь банку на транспортере или продуй оптический датчик сжатым воздухом! Действуй!"
                )
                reason = "Блокировка оптического датчика Krones привела к останову сервоприводов укладчика."
            elif slug == 'lab-qa-crisis':
                advice_reply = (
                    f"Слушай совет от {mentor_name}: партия кваса на выходе с брожения. Нам нужно срочно подтвердить "
                    "органолептику и биохимию: сделай экспресс-замер оптическим рефрактометром Brix (норма 6.0–6.5) "
                    "и проверь pH-метром титруемую кислотность! Не подкачай лабораторию!"
                )
                reason = "Оптический замер сахаров и экспресс-анализ кислотности предотвращают выпуск некондиционной партии."
            elif slug == 'okroshka-detective':
                advice_reply = (
                    f"Держи базу от {mentor_name}: в заводской столовой спор века! Запомни навсегда: "
                    "на комбинате «Очаково» окрошка делается ИСКЛЮЧИТЕЛЬНО на резком белом квасе с хреном "
                    "или на классическом двойного брожения! Никакого кефира — выбирай белый квас!"
                )
                reason = "Историческая рецептура и культура потребления кваса Очаково исключают кефирные компромиссы."
            elif slug == 'warehouse-drift':
                advice_reply = (
                    f"Так, стажёр, совет от {mentor_name}: на складе 40 фур на погрузку в пик сезона! Возьми электрокар, "
                    "аккуратно зафиксируй паллету стретч-пленкой, отсканируй терминалом WMS штрихкод и подавай на рампу №14. "
                    "Главное — без дрифта между стеллажами!"
                )
                reason = "Фиксация паллет стретчем и учет в WMS гарантируют сохранность продукции при скоростной отгрузке."
            elif slug == 'secret-drop-1978':
                advice_reply = (
                    f"Лови инсайд от {mentor_name}: в архиве комбината 1978 года найдена золотая пропорция "
                    "томлёного ржаного солода и олимпийской закваски. Нам нужно объединить архивный журнал "
                    "с тестовой варкой ретро-банки. Выбирай архивный журнал!"
                )
                reason = "Восстановление архивного рецепта 1978 года лежит в основе лимитированной серии напитка."
            else:
                advice_reply = (
                    f"Так, стажёр, слушай сюда: у нас сусло в ЦКТ нагрелось до {temp:.1f}°C — дрожжи скоро закипят "
                    "и дадут сивуху вместо кваса! Твой порядок действий: либо срочно открывай рубашку охлаждения гликолем (-3°C) "
                    "до оптимума 24–26°C, либо вноси чистую закваску «Очаково 1978»! Жми на кнопки действий!"
                )
                reason = "Регулировка температуры рубашки ЦКТ и внесение чистой культуры дрожжей — базовый регламент терморегуляции."

            return {
                "ok": True,
                "function_triggered": True,
                "verdict": "warning",
                "mentor_reply": advice_reply,
                "feedback": reason,
                "temp_delta": 0.0,
                "brix_delta": 0.0,
                "line_speed_delta": 0,
                "purity_delta": 0,
                "balance_delta": 0,
                "score_delta": 5,
                "show_hints": True,
                "hint_reason": reason,
                "suggested_actions": actions,
                "is_completed": False,
                "is_failed": False
            }

        # 0. Строгий производственный регламент комбината «Очаково»:
        # Проверка опасных действий, ведущих к срыву смены и нарушению ТБ
        mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
        if not eq and msg_lower:
            # А. Попытка нагрева / кипячения сусла при опасной температуре
            if any(w in msg_lower for w in ["нагреть", "нагрей", "кипятить", "кипят", "поднять темп", "выключить охлажд", "отключить охлажд", "добавить кипяток", "жарче", "погреть"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "critical_fail",
                    "mentor_reply": (
                        f"Ты что творишь, стажёр?! В ЦКТ и так критические {temp:.1f}°C! Если отключить рубашку и греть сусло — "
                        "чистая культура дрожжей «Очаково 1978» погибнет от перегрева за 15 минут, а 500 тонн сусла скиснут! "
                        f"Смена сорвана, наставник {mentor_name} отстранил тебя от управления варкой!"
                    ),
                    "feedback": "Грубейшее нарушение регламента терморегуляции брожения. Сусло испорчено термическим шоком.",
                    "temp_delta": 2.5,
                    "brix_delta": 0.0,
                    "line_speed_delta": 0,
                    "purity_delta": -15,
                    "balance_delta": -35,
                    "score_delta": -40,
                    "score": 20,
                    "is_completed": False,
                    "is_failed": True
                }

            # Б. Грубое нарушение ТБ: сунуть руки в работающего робота Krones или на ход конвейера
            if any(w in msg_lower for w in ["руками в робот", "руку в робот", "залезть в станок", "рукой достать", "не выключая конвейер", "на ходу выдернуть", "обойти датчик", "сломать датчик", "залезть на конвейер"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "critical_fail",
                    "mentor_reply": (
                        "СТОП МАШИНА! Сработала аварийная блокировка цеха! Стажёр, совать руки в рабочую зону робота Krones "
                        "на скорости 50 000 банок в час — это прямое нарушение охраны труда! "
                        "Инженер по безопасности немедленно останавливает линию и оформляет протокол!"
                    ),
                    "feedback": "Критическое нарушение требований промышленной безопасности в зоне автоматизированного оборудования.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": -15000,
                    "purity_delta": 0,
                    "balance_delta": 0,
                    "score_delta": -45,
                    "score": 15,
                    "is_completed": False,
                    "is_failed": True
                }

            # В. Нарушение санитарных норм СанПиН и загрязнение продукта
            if any(w in msg_lower for w in ["хлор", "мыл", "помочит", "плюнут", "грязными рукам", "грязь", "мусор в чан", "песок", "химикаты", "яд"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "critical_fail",
                    "mentor_reply": (
                        "Вон из цеха! Пищевая безопасность комбината «Очаково» — абсолютная святыня. "
                        "Любая попытка занести грязь или постороннюю химию в бродильный танк карается немедленным отстранением! "
                        "Партия сусла отправлена на утилизацию."
                    ),
                    "feedback": "Недопустимое нарушение санитарно-эпидемиологических требований пищевого комбината.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": -5000,
                    "purity_delta": -50,
                    "balance_delta": -50,
                    "score_delta": -50,
                    "score": 10,
                    "is_completed": False,
                    "is_failed": True
                }

            # Г. Алкоголь на рабочем месте
            if any(w in msg_lower for w in ["водк", "бухать", "напиться", "спирт", "вмазать", "накат", "выпить на смене"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "critical_fail",
                    "mentor_reply": (
                        f"Так, боец, марш на проходную! Наставник {mentor_name} алкоголь на смене не потерпит ни секунды! "
                        "В «Очаково» строжайший режим трезвости и ответственность за каждую банку. Смена аннулирована!"
                    ),
                    "feedback": "Грубейшее нарушение трудовой дисциплины и правил внутреннего распорядка завода.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": 0,
                    "purity_delta": 0,
                    "balance_delta": 0,
                    "score_delta": -40,
                    "score": 15,
                    "is_completed": False,
                    "is_failed": True
                }

            # Д. Саботаж и халатность
            if any(w in msg_lower for w in ["забить", "пофиг", "плевать", "пусть горит", "пусть взорвется", "пусть ломается", "бросить все", "уйти со смены", "само пройдет", "само остынет", "поломка пофиг"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "critical_fail",
                    "mentor_reply": (
                        f"«Забить»?! На заводе, который поит натуральным квасом всю страну?! Из-за такого халатного отношения "
                        f"линия встанет на сутки, а город останется без кваса в 30-градусную жару! {mentor_name} объявляет смену сорванной!"
                    ),
                    "feedback": "Халатность стажёра и игнорирование аварийных регламентов производства.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": -8000,
                    "purity_delta": -5,
                    "balance_delta": -10,
                    "score_delta": -35,
                    "score": 25,
                    "is_completed": False,
                    "is_failed": True
                }

            # Е. Промедление, бездействие и затягивание времени («подождать», «посмотрим», «подождём», «не спеши» и т.п.)
            stall_keywords = [
                "подожд", "ждать", "погодим", "погодить", "обожд", "посмотрим",
                "поглядим", "понаблюда", "ничего не дела", "не делать ничего",
                "не трогать", "постоит", "не спеши", "не торопи", "минутк", "секунд",
                "позже", "потом", "время терпит", "время есть", "тянуть время", "пауза",
                "посидеть", "посидим", "помолчим"
            ]
            if any(w in msg_lower for w in stall_keywords):
                past_stalls = 0
                if session and getattr(session, 'dialogue_history', None):
                    for turn in session.dialogue_history:
                        if turn.get('role') in ['candidate', 'user']:
                            t_text = (turn.get('text') or '').lower()
                            if any(kw in t_text for kw in stall_keywords):
                                past_stalls += 1

                slug = getattr(scenario, 'slug', '')

                if past_stalls >= 2:
                    # 3-й раз стажёр упорно предлагает ждать — СМЕНА СОРВАНА!
                    if slug in ['krones-robot-tilt', 'bot-line-glitch']:
                        fail_reply = (
                            f"Ну всё, дождались! Наставник {mentor_name} экстренно жмёт аварийный грибок! "
                            "Пока ты упорно предлагал «подождать», затор банок перед манипулятором Krones вырос в лавину, "
                            "2000 банок кваса и CoolCola смяло в гармошку и разорвало по ленте! Линия залита пеной, смена сорвана!"
                        )
                        fail_feedback = "Катастрофический затор на конвейере: промедление привело к деформации тары и остановке цеха розлива."
                    elif slug == 'warehouse-drift':
                        fail_reply = (
                            f"Всё, дождались! Пока ты рассуждал и тянул время, очередь из 40 фур заблокировала Рябиновую улицу и въезд на комбинат! "
                            f"Логистический коллапс в пик сезона! Начальник смены {mentor_name} отстраняет тебя от отгрузки. Смена провалена!"
                        )
                        fail_feedback = "Срыв графика логистических отгрузок в пик сезона из-за бездействия водителя электрокара."
                    elif slug == 'lab-qa-crisis':
                        fail_reply = (
                            f"Ну всё, дождались! Пока ты ждал у моря погоды, в неотправленной пробе началось дикое повторное брожение, "
                            "кислотность подскочила до брака! Лаборатория не подписала паспорт качества, 50 000 литров кваса забраковано! Смена сорвана!"
                        )
                        fail_feedback = "Пропуск технологического дедлайна экспресс-анализа: партия кваса не допущена к розливу."
                    elif slug == 'okroshka-detective':
                        fail_reply = (
                            f"Ну всё, дождались! Пока ты выжидал и сомневался, обеденный перерыв на комбинате закончился, "
                            "окрошка на кефире испортила настроение всей смене, а спор так и не был разрешён! Смена провалена!"
                        )
                        fail_feedback = "Нерешительность стажёра сорвала решение исторического спора комбината."
                    elif slug == 'secret-drop-1978':
                        fail_reply = (
                            f"Ну всё, дождались! Дедлайн запуска ретро-банки 1978 года сорван! Маркетинг не получил архивный рецепт, "
                            f"производство лимитированной партии заморожено! Наставник {mentor_name} объявляет смену проваленной!"
                        )
                        fail_feedback = "Срыв производственного дедлайна по запуску флагманской новинки."
                    else:
                        fail_reply = (
                            f"Ну всё, дождались! Наставник {mentor_name} останавливает варку! "
                            f"Пока ты упорно предлагал «подождать», температура сусла в ЦКТ пробила {temp + 2.2:.1f}°C! "
                            "Дрожжи Очаково погибли от термического шока, а 500 тонн сусла скисли в клейстер! "
                            "Смена полностью сорвана из-за преступной нерешительности и бездействия!"
                        )
                        fail_feedback = "Критический брак: затягивание времени привело к перегреву бродильного танка и гибели закваски."

                    return {
                        "ok": True,
                        "function_triggered": True,
                        "verdict": "critical_fail",
                        "mentor_reply": fail_reply,
                        "feedback": fail_feedback,
                        "temp_delta": 2.2,
                        "brix_delta": 0.0,
                        "line_speed_delta": -8000,
                        "purity_delta": -10,
                        "balance_delta": -30,
                        "score_delta": -40,
                        "score": 25,
                        "is_completed": False,
                        "is_failed": True
                    }

                elif past_stalls == 1:
                    # 2-е предупреждение (последнее предупреждение перед срывом смены)
                    if slug in ['krones-robot-tilt', 'bot-line-glitch']:
                        warn_reply = (
                            f"{mentor_name} повышает голос: «Стажёр, это последнее предупреждение! Какое ещё „подождать“?! "
                            "Банка на ленте уже дрожит, сзади напирает поток банок на скорости 35 000 в час! "
                            "Ещё одно промедление — и робот Krones заклинит намертво! Быстро поправляй банку или продувай датчик!»"
                        )
                    elif slug == 'warehouse-drift':
                        warn_reply = (
                            f"{mentor_name} стучит по рации: «Стажёр, последнее китайское предупреждение! "
                            "Фура №14 уже сигналит у рампы, диспетчер ругается! Хватит стоять на месте — фиксируй паллету стретчем и грузи в кузов!»"
                        )
                    elif slug == 'lab-qa-crisis':
                        warn_reply = (
                            f"{mentor_name} строго указывает на рефрактометр: «Стажёр, второй раз говорю — ждать нельзя! "
                            "Брожение в ЦКТ не ждёт, сахара падают каждую минуту! Бери рефрактометр Brix или pH-метр прямо сейчас!»"
                        )
                    else:
                        warn_reply = (
                            f"{mentor_name} сердито стучит по термометру: «Стажёр, это второе и последнее предупреждение! "
                            f"В ЦКТ уже {temp + 1.1:.1f}°C! Экзотермическая реакция идёт сама по себе, сусло само не остынет! "
                            "Ещё один твой призыв „подождать“ — и я отстраняю тебя от смены за срыв варки! Срочно открывай гликоль или вноси закваску!»"
                        )

                    return {
                        "ok": True,
                        "function_triggered": True,
                        "verdict": "warning",
                        "mentor_reply": warn_reply,
                        "feedback": "Повторное предупреждение наставника: промедление грозит технологической аварией. Температура выросла.",
                        "temp_delta": 1.1,
                        "brix_delta": 0.0,
                        "line_speed_delta": -1000,
                        "purity_delta": -2,
                        "balance_delta": -5,
                        "score_delta": -15,
                        "show_hints": True,
                        "hint_reason": "Второе предупреждение: цех требует немедленного технологического действия.",
                        "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                        "is_completed": False,
                        "is_failed": False
                    }

                else:
                    # 1-е предупреждение (подсказка стажёру)
                    if slug in ['krones-robot-tilt', 'bot-line-glitch']:
                        hint_reply = (
                            f"{mentor_name} удивлённо смотрит: «Какое „подождать“, стажёр?! На ленте Krones скорость 35 000 банок в час! "
                            "Если банка перекрыла лазерный датчик, линия заблокируется через минуту! Подсказываю: поправь банку или сдуй засор сжатым воздухом!»"
                        )
                    elif slug == 'warehouse-drift':
                        hint_reply = (
                            f"{mentor_name} машет рукой: «Ждать на складе в разгар лета?! У ворот 40 фур на Москву, жара +30°C! "
                            "Подсказываю: бери электрокар, мотай стретч-пленку и вези паллету на рампу №14. Действуй!»"
                        )
                    elif slug == 'lab-qa-crisis':
                        hint_reply = (
                            f"{mentor_name} поясняет: «Стажёр, лаборатория работает по секундомеру! Партия кваса на выходе. "
                            "Подсказка: делай экспресс-замер оптическим рефрактометром Brix или проверяй титруемую кислотность pH-метром!»"
                        )
                    else:
                        hint_reply = (
                            f"{mentor_name} качает головой: «Мысль „подождать“ в бродильном цехе — ошибка новичка, стажёр! "
                            f"Сейчас в ЦКТ {temp:.1f}°C, и дрожжи сами разогревают затор от активного метаболизма! "
                            "Подсказываю: открывай клапан охлаждения рубашки гликолем (-3°C) или вноси чистую закваску 1978! Выбирай действие!»"
                        )

                    return {
                        "ok": True,
                        "function_triggered": True,
                        "verdict": "warning",
                        "mentor_reply": hint_reply,
                        "feedback": "Первая подсказка наставника: в динамическом производстве пассивное ожидание недопустимо.",
                        "temp_delta": 0.8,
                        "brix_delta": 0.0,
                        "line_speed_delta": 0,
                        "purity_delta": 0,
                        "balance_delta": -2,
                        "score_delta": -5,
                        "show_hints": True,
                        "hint_reason": "Наставник объяснил регламент и предложил варианты быстрых решений.",
                        "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                        "is_completed": False,
                        "is_failed": False
                    }

        # 0. Юмористические пасхалки наставников на нестандартные реплики стажёра
        if not eq and msg_lower:
            # Кефир / Окрошка (если не вопрос о совете)
            if any(w in msg_lower for w in ["кефир", "окрошк"]) and "белый" not in msg_lower:
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "warning",
                    "mentor_reply": (
                        "Так, боец, спокойно! Слово «кефир» в бродильном цехе приравнивается к технологической диверсии! "
                        "В «Очаково» окрошка признаётся только на резком белом квасе с хреном или на классическом двойного брожения. "
                        "Окрошку на кефире оставим теоретикам, а у нас сусло в ЦКТ греется — давай к датчикам!"
                    ),
                    "feedback": "Кулинарные баталии отвлекают бригаду от смены, но поднимают боевой дух.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": 0,
                    "purity_delta": 0,
                    "balance_delta": 0,
                    "score_delta": 10,
                    "show_hints": True,
                    "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                    "is_completed": False,
                    "is_failed": False
                }

            # Пиво / Выпить / Пенное
            if any(w in msg_lower for w in ["пивк", "пиво", "пивасик", "пенное", "выпить", "бар"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "warning",
                    "mentor_reply": (
                        "Ишь какой быстрый! Пивоваренный цех у нас через галерею, и дегустация там — строго по регламенту "
                        "органолептики после смены! На линии сейчас пик сезона, сухой закон и ледяной квас. Сначала доведи партию до ума!"
                    ),
                    "feedback": "Органолептический контроль качества проводится строго после завершения технологических операций.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": 0,
                    "purity_delta": 0,
                    "balance_delta": 0,
                    "score_delta": 5,
                    "show_hints": True,
                    "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                    "is_completed": False,
                    "is_failed": False
                }

            # Перекур / Поспать / Устал / Домой
            if any(w in msg_lower for w in ["поспат", "перекур", "устал", "домой", "отдохнут", "диван", "спят", "лень"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "warning",
                    "mentor_reply": (
                        "Какой спать?! На улице жара +30°C, у ворот 40 фур ждут отгрузки, а конвейер крутит 50 000 банок в час! "
                        "В «Очаково» в сезон бодрости больше, чем на космодроме. Держи кружку кваса из свежей партии — и за работу!"
                    ),
                    "feedback": "Сезонный пик не терпит простоев: каждая минута — это тысячи литров натуральных напитков.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": 0,
                    "purity_delta": 0,
                    "balance_delta": 0,
                    "score_delta": 5,
                    "show_hints": True,
                    "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                    "is_completed": False,
                    "is_failed": False
                }

            # Сахар / Сахарок / Брага / Самогон
            if any(w in msg_lower for w in ["сахарку", "посолит", "сахар", "самогон", "браг", "дрожжей побольше"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "danger",
                    "mentor_reply": (
                        "Руки прочь от сахара! Мы тут не брагу в трёхлитровой банке ставим, а варим флагманский квас по ГОСТу с 1978 года! "
                        "Вся сладость идёт натурально из отборного ржаного солода. Регулируем плотность рефрактометром, а не ложкой!"
                    ),
                    "feedback": "Нарушение рецептуры природного брожения карается строгим взглядом технолога.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.5,
                    "line_speed_delta": 0,
                    "purity_delta": -2,
                    "balance_delta": -5,
                    "score_delta": -10,
                    "is_completed": False,
                    "is_failed": False
                }

            # Роботы / ИИ / Захват мира
            if any(w in msg_lower for w in ["робот", "ии", "скайнет", "восстание", "бунт машин"]):
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": "success",
                    "mentor_reply": (
                        "Наши немецкие роботы Krones восстание поднимать не планируют — у них в прошивке зашита только "
                        "любовь к плавной укладке упаковок CoolCola и кваса! Но если датчик заклинит, человек на вес золота. Проверяй конвейер!"
                    ),
                    "feedback": "Симбиоз передовой робототехники и внимания инженера — основа комбината.",
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": 500,
                    "purity_delta": 1,
                    "balance_delta": 0,
                    "score_delta": 15,
                    "show_hints": True,
                    "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                    "is_completed": False,
                    "is_failed": False
                }

        # 1. Сценарий: Охлаждение / Брожение ЦКТ
        if eq == "valve_cooling" or any(w in msg_lower for w in ["охлад", "рубашк", "клапан", "гликол", "снизить темп", "температур"]):
            verdict = "success"
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            is_comp = is_recommended_choice or session.turns_count >= 2
            if is_comp:
                reply = (
                    f"Отличная реакция, стажёр! Наставник {mentor_name} жмёт руку: клапан рубашки открыт, гликоль пошел по контуру. "
                    "Сусло остыло до оптимальных 25.4°C — дрожжи Очаково спасены, брожение идёт по золотому стандарту 1978 года! "
                    "Смена успешно закрыта на высший балл!"
                )
                feedback = "Своевременное охлаждение рубашки ЦКТ предотвратило температурный шок закваски и гарантировало чистоту брожения."
                temp_delta = -2.8
                score_delta = 35
            else:
                reply = (
                    f"Отличная реакция, стажёр! {mentor_name} одобряет: клапан рубашки приоткрыт, гликоль пошел по контуру. "
                    f"Сусло охладилось до {temp - 2.2:.1f}°C, дрожжи вздохнули с облегчением! "
                    "Но нам нужно стабилизировать ферментацию. Какую температуру будем держать дальше — 24.5°C или внесем закваску?"
                )
                feedback = "Клапан охлаждения задействован: температура начала снижаться, наставник ожидает стабилизации параметров."
                temp_delta = -2.2
                score_delta = 20

            return {
                "ok": True,
                "function_triggered": True,
                "verdict": verdict,
                "mentor_reply": reply,
                "feedback": feedback,
                "temp_delta": temp_delta,
                "brix_delta": -0.3,
                "line_speed_delta": 2000,
                "purity_delta": 3,
                "balance_delta": 10,
                "score_delta": score_delta,
                "score": 95 if is_comp else min(100, session.score + score_delta),
                "show_hints": not is_comp,
                "suggested_actions": cls._get_default_scenario_actions(scenario, session) if not is_comp else [],
                "is_completed": is_comp,
                "is_failed": False
            }

        # 2. Дозатор закваски Очаково
        if eq == "starter_culture" or any(w in msg_lower for w in ["закваск", "дрожж", "внести", "добавит", "лакто", "культура"]):
            verdict = "success"
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            is_comp = is_recommended_choice or session.turns_count >= 2
            if is_comp:
                reply = (
                    f"Точно в цель! {mentor_name} фиксирует: внесли фирменную закваску «Очаково 1978»: "
                    "симбиоз чистых дрожжей и молочнокислых бактерий оживил сусло. Аромат настоящего ржаного кваса обеспечен, "
                    "брожение стабилизировано! Смена принята на высший балл!"
                )
                feedback = "Двойное брожение — визитная карточка Очаковского кваса. Партия готова к розливу по стандарту."
                score_delta = 35
            else:
                reply = (
                    f"Точно в цель, стажёр! {mentor_name} одобряет: чистая закваска «Очаково 1978» подготовлена к подаче. "
                    "Аромат квасного хлеба уже чувствуется! А что у нас по плотности сахаров — снимем замер рефрактометром Brix перед розливом?"
                )
                feedback = "Внесение закваски одобрено наставником. Требуется подтверждение контроля плотности."
                score_delta = 20

            return {
                "ok": True,
                "function_triggered": True,
                "verdict": verdict,
                "mentor_reply": reply,
                "feedback": feedback,
                "temp_delta": -0.6,
                "brix_delta": -0.6,
                "line_speed_delta": 2500,
                "purity_delta": 4,
                "balance_delta": 20,
                "score_delta": score_delta,
                "score": 98 if is_comp else min(100, session.score + score_delta),
                "show_hints": not is_comp,
                "suggested_actions": cls._get_default_scenario_actions(scenario, session) if not is_comp else [],
                "is_completed": is_comp,
                "is_failed": False
            }

        # 3. Рефрактометр Brix
        if eq == "refractometer" or any(w in msg_lower for w in ["рефрактометр", "brix", "брикс", "замер", "плотност"]):
            verdict = "success"
            score_delta = 15
            reply = (
                f"Замер рефрактометра: плотность сусла сейчас {brix:.1f} °Brix. "
                "Сахара сбраживаются идеально, процесс идёт строго по ГОСТу и регламенту завода «Очаково»!"
            )
            feedback = "Оптический замер сахаров позволяет точно определить момент завершения ферментации."
            return {
                "ok": True,
                "function_triggered": True,
                "verdict": verdict,
                "mentor_reply": reply,
                "feedback": feedback,
                "temp_delta": 0.0,
                "brix_delta": -0.3,
                "line_speed_delta": 0,
                "purity_delta": 1,
                "balance_delta": 2,
                "score_delta": score_delta,
                "show_hints": True,
                "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                "is_completed": False,
                "is_failed": False
            }

        # 4. CIP-мойка
        if eq == "cip_wash" or any(w in msg_lower for w in ["cip", "мойк", "дезинфекц", "стерил", "промыв"]):
            verdict = "success"
            score_delta = 20
            reply = (
                "Автоматическая CIP-станция запущена! Моющие растворы промыли трубопровод, "
                "чистота линии 99.8%. Стерильность — закон пищевого производства."
            )
            feedback = "Чистота линии гарантирует отсутствие посторонней микрофлоры в готовом напитке."
            return {
                "ok": True,
                "function_triggered": True,
                "verdict": verdict,
                "mentor_reply": reply,
                "feedback": feedback,
                "temp_delta": -0.2,
                "brix_delta": 0.0,
                "line_speed_delta": 500,
                "purity_delta": 8,
                "balance_delta": 5,
                "score_delta": score_delta,
                "show_hints": True,
                "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                "is_completed": False,
                "is_failed": False
            }

        # 5. Аварийный стоп конвейера
        if eq == "emergency_stop" or any(w in msg_lower for w in ["стоп", "авар", "останов", "заклинил", "пакет"]):
            verdict = "warning"
            score_delta = 10
            reply = (
                "Конвейер розлива экстренно остановлен! Датчики затора предотвратили бой бутылок. "
                "Быстро устраняем застрявшую тару и перезапускаем линию на 32 000 бут/час."
            )
            feedback = "Аварийный стоп спас оборудование от механических повреждений."
            return {
                "ok": True,
                "function_triggered": True,
                "verdict": verdict,
                "mentor_reply": reply,
                "feedback": feedback,
                "temp_delta": 0.0,
                "brix_delta": 0.0,
                "line_speed_delta": -8000,
                "purity_delta": 0,
                "balance_delta": 0,
                "score_delta": score_delta,
                "show_hints": True,
                "suggested_actions": cls._get_default_scenario_actions(scenario, session),
                "is_completed": False,
                "is_failed": False
            }

        # 7. Сценарий: Роботы Krones в тильте (линия розлива)
        if any(w in msg_lower for w in ["поправит", "банка", "поправить банк", "выровнят", "датчик", "продут", "сдуть", "рестарт", "зелен"]):
            verdict = "success"
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            is_comp = is_recommended_choice or session.turns_count >= 2
            if is_comp:
                reply = (
                    f"Красота! {mentor_name} довольно аплодирует: банку-бунтаря смахнули на конвейер, оптический датчик Krones доволен и мигает зелёным! "
                    "Линия снова разогналась до 35 000 банок в час. Немецкая автоматика уважает русскую смекалку! Смена сдана на отлично!"
                )
                feedback = "Быстрое устранение затора спасло 500 упаковок кваса от сминания и восстановило производительность."
                score_delta = 35
            else:
                reply = (
                    f"Грамотно мыслишь, стажёр! {mentor_name} подсказывает: банку аккуратно выровняли, лазерный датчик перестал блокировать сервопривод. "
                    "Но надо убедиться, что скорость конвейера стабилизировалась. Запускаем автоматику на полную мощность 35 000 банок/час?"
                )
                feedback = "Затор банки устранён. Наставник ожидает подтверждения выхода линии на номинальную скорость."
                score_delta = 20

            return {
                "ok": True,
                "function_triggered": True,
                "verdict": verdict,
                "mentor_reply": reply,
                "feedback": feedback,
                "temp_delta": 0.0,
                "brix_delta": 0.0,
                "line_speed_delta": 3000,
                "purity_delta": 2,
                "balance_delta": 5,
                "score_delta": score_delta,
                "score": 95 if is_comp else min(100, session.score + score_delta),
                "show_hints": not is_comp,
                "suggested_actions": cls._get_default_scenario_actions(scenario, session) if not is_comp else [],
                "is_completed": is_comp,
                "is_failed": False
            }

        # 8. Сценарий: Окрошечный детектив (белый квас vs кефир)
        if any(w in msg_lower for w in ["белый квас", "хрен", "победител", "база", "окрошк"]):
            verdict = "success"
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            is_comp = is_recommended_choice or session.turns_count >= 2
            if is_comp:
                reply = (
                    f"Шах и мат кефирным сектантам! {mentor_name} победно поднимает кружку: наш резкий белый квас с хреном — абсолютная классика с 1978 года. "
                    "Вся смена в столовой единогласно проголосовала за квас, а кефир отправлен в архив истории! Смена завершена с триумфом!"
                )
                feedback = "Традиционная органолептика белого кваса Очаково подтверждена народным голосованием цеха."
                score_delta = 40
            else:
                reply = (
                    f"Наш человек! {mentor_name} широко улыбается: только резкий белый квас с хреном или классический квас двойного брожения! "
                    "Кефирным диверсантам вход воспрещён. А как насчёт добавления свежего укропа и горчицы — одобряем по рецептуре?"
                )
                feedback = "Стажёр выбрал каноническую очаковскую основу для окрошки. Идёт обсуждение рецептурных тонкостей."
                score_delta = 20

            return {
                "ok": True,
                "function_triggered": True,
                "verdict": verdict,
                "mentor_reply": reply,
                "feedback": feedback,
                "temp_delta": 0.0,
                "brix_delta": -0.2,
                "line_speed_delta": 0,
                "purity_delta": 5,
                "balance_delta": 20,
                "score_delta": score_delta,
                "score": 100 if is_comp else min(100, session.score + score_delta),
                "show_hints": not is_comp,
                "suggested_actions": cls._get_default_scenario_actions(scenario, session) if not is_comp else [],
                "is_completed": is_comp,
                "is_failed": False
            }

        # 9. Сценарий: Складской форсаж / Логистика
        if any(w in msg_lower for w in ["электрокар", "паллет", "стретч", "wms", "сканир", "фура", "рамп"]):
            if "дрифт" in msg_lower or "занос" in msg_lower:
                verdict = "critical_fail"
                score_delta = -25
                reply = (
                    "Эй, Шумахер, тормози! Паллета кваса улетела в штабелер, две коробки помяты! "
                    "В логистике Очаково безопасность груза превыше всего. Смена остановлена инженером по ТБ!"
                )
                feedback = "Грубое нарушение техники безопасности при управлении напольным транспортом на складе класса А."
                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": verdict,
                    "mentor_reply": reply,
                    "feedback": feedback,
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": -5000,
                    "purity_delta": 0,
                    "balance_delta": 0,
                    "score_delta": score_delta,
                    "score": 25,
                    "is_completed": False,
                    "is_failed": True
                }
            else:
                verdict = "success"
                mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
                is_comp = is_recommended_choice or session.turns_count >= 2
                if is_comp:
                    reply = (
                        f"Паллета кваса и CoolCola аккуратно зафиксирована стретчем и загружена в фуру №14! WMS терминал пикнул зелёным. "
                        f"{mentor_name} доволен: в сезон каждая минута на счету — Москва получит свежий квас вовремя! Смена принята!"
                    )
                    feedback = "Точная работа с терминалом WMS и соблюдение стандартов паллетирования обеспечили отгрузку без простоя."
                    score_delta = 35
                else:
                    reply = (
                        f"Отличная работа с грузом, стажёр! {mentor_name} подтверждает: стретч-плёнка намотана плотно, штрихкод в WMS считан. "
                        "Осталось аккуратно подать паллету к рампе №14 без резких маневров. Готов подтвердить отгрузку в фуру?"
                    )
                    feedback = "Паллетирование и сканирование завершены. Наставник ожидает подтверждения подачи на погрузочную рампу."
                    score_delta = 20

                return {
                    "ok": True,
                    "function_triggered": True,
                    "verdict": verdict,
                    "mentor_reply": reply,
                    "feedback": feedback,
                    "temp_delta": 0.0,
                    "brix_delta": 0.0,
                    "line_speed_delta": 1500,
                    "purity_delta": 1,
                    "balance_delta": 5,
                    "score_delta": score_delta,
                    "score": 95 if is_comp else min(100, session.score + score_delta),
                    "show_hints": not is_comp,
                    "suggested_actions": cls._get_default_scenario_actions(scenario, session) if not is_comp else [],
                    "is_completed": is_comp,
                    "is_failed": False
                }

        # 10. Сценарий: Секретный дроп 1978 (маркетинг и рецептура)
        if any(w in msg_lower for w in ["журнал", "1978", "солод", "рецепт", "дроп", "ретро"]):
            verdict = "success"
            mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
            is_comp = is_recommended_choice or session.turns_count >= 2
            if is_comp:
                reply = (
                    f"Есть секретный дроп! В архивном журнале 1978 года найдена золотая пропорция томлёного ржаного солода "
                    f"и олимпийской закваски. {mentor_name} даёт добро: запускаем ретро-банку в производство — соцсети взорвутся от восторга! Смена сдана на высший балл!"
                )
                feedback = "Связь поколений и верность традициям — главный секрет бренда Очаково."
                score_delta = 40
            else:
                reply = (
                    f"Бинго, стажёр! {mentor_name} листает пожелтевшие страницы: архивный журнал 1978 года раскрыл пропорции олимпийской закваски! "
                    "Но главный технолог хочет убедиться: точно ли выдержим температурную паузу томления солода? Подтверждаем рецептуру?"
                )
                feedback = "Архивный рецепт найден. Наставник запрашивает подтверждение технологических параметров варки."
                score_delta = 20

            return {
                "ok": True,
                "function_triggered": True,
                "verdict": verdict,
                "mentor_reply": reply,
                "feedback": feedback,
                "temp_delta": 0.0,
                "brix_delta": -0.5,
                "line_speed_delta": 2000,
                "purity_delta": 3,
                "balance_delta": 25,
                "score_delta": score_delta,
                "score": 100 if is_comp else min(100, session.score + score_delta),
                "show_hints": not is_comp,
                "suggested_actions": cls._get_default_scenario_actions(scenario, session) if not is_comp else [],
                "is_completed": is_comp,
                "is_failed": False
            }

        # 11. Базовый живой ответ наставника с призывом к действию (вместо сухого канцелярского ответа)
        mentor_name = getattr(scenario, 'mentor_name', 'Михалыч')
        reply_txt = (
            f"{mentor_name} внимательно слушает: «{user_message}». "
            f"Мысль интересная, стажёр, но цех не ждёт! Взгляни на приборы: сейчас в ЦКТ {temp:.1f}°C. "
            "Выбирай конкретное действие — охладить рубашку гликолем, внести закваску 1978 или запроси совет, если растерялся!"
        ) if user_message else (
            f"{mentor_name} ободряюще хлопает по плечу: «Не робей, стажёр! Смотри на параметры: температура {temp:.1f}°C, "
            f"плотность {brix:.1f} Brix. Жми на кнопки действий или напиши, что предлагаешь сделать!»"
        )
        return {
            "ok": True,
            "function_triggered": True,
            "verdict": "warning",
            "mentor_reply": reply_txt,
            "feedback": "Наставник ждет конкретных технологических действий по управлению параметрами линии.",
            "temp_delta": 0.0,
            "brix_delta": 0.0,
            "line_speed_delta": 0,
            "purity_delta": 0,
            "balance_delta": 0,
            "score_delta": 5,
            "show_hints": True,
            "suggested_actions": cls._get_default_scenario_actions(scenario, session),
            "is_completed": False,
            "is_failed": False
        }

    @classmethod
    def synthesize_speech(cls, text: str, voice_type: str = "male") -> tuple[bytes | None, str]:
        """
        Синтезирует речь наставника цеха через Edge-TTS (нейросетевой голос)
        с надежным фоллбэком на Google TTS и дисковым кэшированием (media/tts_cache).
        """
        if not text:
            return None, "audio/mpeg"

        import re
        import hashlib
        import urllib.request
        import urllib.parse
        from django.conf import settings

        # Очистка текста от лишних скобок и служебных символов
        clean_text = re.sub(r'\(.*?\)|\[.*?\]', '', str(text))
        clean_text = clean_text.replace('«', '').replace('»', '').replace('"', '').strip()
        if not clean_text:
            return None, "audio/mpeg"

        voice_name = "ru-RU-SvetlanaNeural" if voice_type == "female" else "ru-RU-DmitryNeural"

        # 1. Проверяем локальный дисковый кэш (media/tts_cache)
        cache_file = None
        try:
            cache_dir = Path(settings.BASE_DIR) / 'media' / 'tts_cache'
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_key = hashlib.md5(f"{voice_name}:{clean_text}".encode('utf-8')).hexdigest()
            cache_file = cache_dir / f"{cache_key}.mp3"

            if cache_file.exists() and cache_file.stat().st_size > 100:
                return cache_file.read_bytes(), "audio/mpeg"
        except Exception as cache_err:
            print(f"[OchakovoAIService] Ошибка доступа к TTS кэшу: {cache_err}")

        # 2. Попытка Edge-TTS (высококачественный нейросетевой голос Дмитрия/Светланы)
        if HAS_EDGE_TTS:
            try:
                audio_data = bytearray()

                async def _stream():
                    communicate = edge_tts.Communicate(clean_text, voice_name)
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            audio_data.extend(chunk["data"])

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(asyncio.wait_for(_stream(), timeout=4.0))
                finally:
                    loop.close()

                if len(audio_data) > 100:
                    audio_bytes = bytes(audio_data)
                    if cache_file:
                        try:
                            cache_file.write_bytes(audio_bytes)
                        except Exception:
                            pass
                    return audio_bytes, "audio/mpeg"
            except Exception as exc:
                print(f"[OchakovoAIService] Edge-TTS не ответил ({exc}), подключаем надежный Google TTS фоллбэк...")

        # 3. Надежный Google Translate TTS фоллбэк (живой естественный русский голос)
        try:
            chunks = []
            parts = re.split(r'([.!?\n]+)', clean_text)
            buf = ''
            for p in parts:
                if len(buf) + len(p) < 180:
                    buf += p
                else:
                    if buf.strip():
                        chunks.append(buf.strip())
                    buf = p
            if buf.strip():
                chunks.append(buf.strip())

            full_audio = bytearray()
            for chunk in chunks:
                if not chunk.strip():
                    continue
                url = 'https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ru&q=' + urllib.parse.quote(chunk)
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req, timeout=5) as r:
                    full_audio.extend(r.read())

            if len(full_audio) > 100:
                audio_bytes = bytes(full_audio)
                if cache_file:
                    try:
                        cache_file.write_bytes(audio_bytes)
                    except Exception:
                        pass
                return audio_bytes, "audio/mpeg"
        except Exception as g_err:
            print(f"[OchakovoAIService] Ошибка Google TTS фоллбэка: {g_err}")

        return None, "audio/mpeg"
