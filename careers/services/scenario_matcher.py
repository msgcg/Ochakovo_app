import re
from typing import Optional, Dict, Any


# Регулярные выражения для сопоставления вакансий завода «Очаково» с игровыми сценариями симулятора
SCENARIO_RULES = [
    {
        'slug': 'okroshka-detective',
        'title': 'Окрошечный детектив: Квас против Кефира',
        'mentor_name': 'Елена',
        'mentor_role': 'Руководитель лаборатории микробиологии',
        'badge': 'Лаборатория и ОТК',
        'btn_text': 'Пройти тест в лаборатории качества',
        'track_slug': 'lab',
        'regex': re.compile(
            r'(?:химик\w*|лаборант\w*|лаборатор\w*|микробиолог\w*|отк\b|титрован\w*|контрол\w*\s+качеств\w*|инженер[- ]химик)',
            re.IGNORECASE
        )
    },
    {
        'slug': 'brew-yeast-flex',
        'title': 'Дрожжевой флекс в ЦКТ №7',
        'mentor_name': 'Михалыч',
        'mentor_role': 'Главный пивовар-технолог',
        'badge': 'Бродильное отделение',
        'btn_text': 'Пройти смену в варочном цехе',
        'track_slug': 'brewing',
        'regex': re.compile(
            r'(?:квасовар\w*|пивовар\w*|брожен\w*|варочн\w*|(?<!с)варщик\w*|затор\w*|сусл\w*|солод\w*|купаж\w*|дрожж\w*|фильтрац\w*|мастер\s*[-–]\s*технолог|технолог\w*\s+(?:пив|квас|напит|производств))',
            re.IGNORECASE
        )
    },
    {
        'slug': 'krones-robot-tilt',
        'title': 'Роботы Krones в тильте',
        'mentor_name': 'Анна',
        'mentor_role': 'Ведущий инженер розлива',
        'badge': 'Линия розлива Krones',
        'btn_text': 'Устранить аварию на линии розлива',
        'track_slug': 'automation',
        'regex': re.compile(
            r'(?:розлив\w*|линия\s+розлив\w*|наладчик\w*|krones|khs|упаков\w*|фасов\w*|кипиа|автоматиз\w*|стан(?:ок|ков)\b|механик\w*|электромонтер\w*|электроник\w*|инженер[- ]электрик|инженер[- ]конструктор|инженер\s+по\s+автоматизации|главный\s+энергетик)',
            re.IGNORECASE
        )
    },
    {
        'slug': 'warehouse-drift',
        'title': 'Форсаж на электрокаре: Пик отгрузки',
        'mentor_name': 'Роман',
        'mentor_role': 'Начальник логистического комплекса WMS',
        'badge': 'Складской комплекс WMS',
        'btn_text': 'Пройти тест-драйв в логистическом хабе',
        'track_slug': 'logistics',
        'regex': re.compile(
            r'(?:склад\w*|логист\w*|погрузчик\w*|электрокар\w*|штабелер\w*|комплектовщик\w*|кладовщик\w*|wms\b|отгрузк\w*|паллет\w*)',
            re.IGNORECASE
        )
    },
    {
        'slug': 'secret-drop-1978',
        'title': 'Секретный дроп 1978: Рецепт Олимпиады',
        'mentor_name': 'Артём',
        'mentor_role': 'Бренд-стратег и креативный продюсер',
        'badge': 'Креативный хаб / бренд',
        'btn_text': 'Создать концепт в дизайн-хабе',
        'track_slug': 'marketing',
        'regex': re.compile(
            r'(?:маркетолог\w*|smm\b|бренд\w*|дизайн\w*|копирайтер\w*|pr\b|креатив\w*|таргетолог\w*|контент\w*)',
            re.IGNORECASE
        )
    }
]


def match_game_scenario(title: str, description: str = "", track_slug: str = "") -> Optional[Dict[str, Any]]:
    """
    Анализирует наименование, описание и трек вакансии с помощью регулярных выражений (regex).
    Если для вакансии предусмотрен игровой сценарий, возвращает словарь с параметрами сценария.
    """
    text_to_check = f"{title} {description}".strip()
    
    # 1. Поиск точного совпадения по регулярным выражениям
    for rule in SCENARIO_RULES:
        if rule['regex'].search(text_to_check):
            from careers.models import GameScenario
            scenario_obj = GameScenario.objects.filter(slug=rule['slug']).first()
            if not scenario_obj:
                scenario_obj = GameScenario.objects.filter(slug=rule['slug'].replace('-', '_')).first()
            
            slug_to_use = scenario_obj.slug if scenario_obj else rule['slug']
            scenario_id = scenario_obj.id if scenario_obj else 1
            mentor_name = scenario_obj.mentor_name if scenario_obj else rule['mentor_name']
            mentor_role = scenario_obj.mentor_role if scenario_obj else rule['mentor_role']
            scenario_title = scenario_obj.title if scenario_obj else rule['title']
            
            return {
                'has_scenario': True,
                'scenario_id': scenario_id,
                'scenario_slug': slug_to_use,
                'scenario_title': scenario_title,
                'mentor_name': mentor_name,
                'mentor_role': mentor_role,
                'badge': rule['badge'],
                'btn_text': rule['btn_text'],
                'track_slug': rule['track_slug'],
            }

    # 2. Если по regex в тексте совпадения нет, но указан соответствующий трек
    if track_slug:
        for rule in SCENARIO_RULES:
            if rule['track_slug'] == track_slug:
                from careers.models import GameScenario
                scenario_obj = GameScenario.objects.filter(slug=rule['slug']).first()
                if not scenario_obj:
                    scenario_obj = GameScenario.objects.filter(slug=rule['slug'].replace('-', '_')).first()
                if scenario_obj:
                    return {
                        'has_scenario': True,
                        'scenario_id': scenario_obj.id,
                        'scenario_slug': scenario_obj.slug,
                        'scenario_title': scenario_obj.title,
                        'mentor_name': scenario_obj.mentor_name,
                        'mentor_role': scenario_obj.mentor_role,
                        'badge': rule['badge'],
                        'btn_text': rule['btn_text'],
                        'track_slug': rule['track_slug'],
                    }

    return None
