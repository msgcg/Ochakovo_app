import re
import requests
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from django.core.cache import cache
from django.utils.text import slugify

from .scenario_matcher import match_game_scenario

logger = logging.getLogger(__name__)

OFFICIAL_CAREERS_URL = "https://ochakovo.ru/rabota/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OchakovoCareers/2.0"
CACHE_KEY = "ochakovo_official_vacancies_cache_v2"
CACHE_TIMEOUT = 3600  # 1 час в кэше


def classify_track_slug(title: str, description: str = "") -> str:
    """Определение карьерного трека на основе ключевых слов в названии позиции"""
    text = f"{title} {description}".lower()
    
    if re.search(r'(?:химик|лаборант|лаборатор|микробиолог|отк\b|качества|экспертиз)', text):
        return 'lab'
    if re.search(r'(?:квасовар|пивовар|брожен|варочн|варщик|солод|купаж|дрожж|фильтрац|мастер.*технолог|технолог.*производств)', text):
        return 'brewing'
    if re.search(r'(?:розлив|наладчик|krones|khs|упаков|фасов|кипиа|автоматиз|станок|станков|механик|электромонтер|электроник|инженер|энергетик)', text):
        return 'automation'
    if re.search(r'(?:склад|логист|wms|комплектов|погрузчик|кладовщик|водитель|грузчик)', text):
        return 'logistics'
    if re.search(r'(?:маркетинг|бренд|реклам|продаж|мерчендайзер|торговый|супервайзер|экскурсовод|hr|персонал|экономист|бухгалтер|юрист)', text):
        return 'marketing'
    
    return 'automation'


def estimate_salary_text(title: str, city: str) -> str:
    """Оценка вилки заработной платы для отображения на карточке"""
    t = title.lower()
    is_capital = (city == 'Москва')
    
    if 'главный' in t or 'руководитель' in t or 'директор' in t:
        return 'от 120 000 до 190 000 ₽' if is_capital else 'от 95 000 до 150 000 ₽'
    if 'ведущий' in t or 'инженер' in t or 'технолог' in t or 'химик' in t:
        return 'от 85 000 до 125 000 ₽' if is_capital else 'от 70 000 до 95 000 ₽'
    if 'наладчик' in t or 'оператор' in t or 'механик' in t or 'электромонтер' in t:
        return 'от 75 000 до 105 000 ₽' if is_capital else 'от 60 000 до 85 000 ₽'
    if 'водитель' in t or 'погрузчик' in t or 'склад' in t:
        return 'от 70 000 до 95 000 ₽' if is_capital else 'от 55 000 до 75 000 ₽'
    
    return 'от 65 000 до 90 000 ₽' if is_capital else 'от 50 000 до 70 000 ₽'


def fetch_official_vacancies(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Автоматическая выгрузка актуальных вакансий напрямую с официального портала «Очаково» (ochakovo.ru/rabota/).
    Включает кэширование, классификацию по трекам и сопоставление с игровым симулятором через regex.
    """
    if not force_refresh:
        cached_data = cache.get(CACHE_KEY)
        if cached_data:
            return cached_data

    vacancies: List[Dict[str, Any]] = []
    sync_status = "live"
    error_message = None

    try:
        response = requests.get(
            OFFICIAL_CAREERS_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        response.encoding = 'utf-8'
        html = response.text

        # Извлечение карточек вакансий
        links = re.findall(r'<a\s+[^>]*href=\"([^\"]*hh\.ru/vacancy/(\d+))\"[^>]*>(.*?)</a>', html, re.DOTALL)
        
        for hh_url, vid, content in links:
            h3s = re.findall(r'<h3>(.*?)</h3>', content, re.DOTALL)
            if len(h3s) >= 2:
                title = re.sub(r'\s+', ' ', h3s[0]).strip()
                city = re.sub(r'\s+', ' ', h3s[1]).strip()
            elif len(h3s) == 1:
                title = re.sub(r'\s+', ' ', h3s[0]).strip()
                city = "Москва"
            else:
                parts = [p.strip() for p in re.sub(r'<[^>]+>', '|', content).split('|') if p.strip()]
                title = parts[0] if parts else "Специалист производства"
                city = parts[1] if len(parts) > 1 else "Москва"

            track_slug = classify_track_slug(title)
            salary_text = estimate_salary_text(title, city)
            scenario_match = match_game_scenario(title=title, track_slug=track_slug)

            vacancies.append({
                'external_id': vid,
                'slug': f"hh-{vid}",
                'title': title,
                'city': city,
                'track_slug': track_slug,
                'salary_text': salary_text,
                'hh_url': hh_url,
                'source': 'Официальный портал ochakovo.ru',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': (city == 'Москва'),
                'matched_scenario': scenario_match,
                'schedule': 'Сменный 2/2 или гибкий для студентов',
                'experience_level': 'Без опыта / Стажёр / Студент',
                'description': f'Официальная вакансия предприятия «Очаково» в городе {city}. Приглашаем студентов и выпускников на оплачиваемую работу и производственную практику в пик сезона.'
            })

    except Exception as e:
        logger.warning(f"Ошибка при выгрузке вакансий с ochakovo.ru: {e}")
        sync_status = "fallback"
        error_message = str(e)

    result = {
        'status': sync_status,
        'vacancies': vacancies,
        'total_count': len(vacancies),
        'synced_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
        'source_url': OFFICIAL_CAREERS_URL,
        'error': error_message
    }

    if vacancies:
        cache.set(CACHE_KEY, result, CACHE_TIMEOUT)

    return result


def sync_vacancies_to_database(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Синхронизирует актуальные вакансии с официального сайта ochakovo.ru
    в локальную базу данных Django для полноценной офлайн-работы и быстрой выборки.
    """
    from careers.models import Vacancy, InternshipTrack

    feed = fetch_official_vacancies(force_refresh=force_refresh)
    items = feed.get('vacancies', [])
    created_count = 0
    updated_count = 0

    tracks = {t.slug: t for t in InternshipTrack.objects.all()}

    for item in items:
        track = tracks.get(item['track_slug']) or tracks.get('automation')
        if not track:
            continue

        slug = item['slug']
        title = item['title']
        city = item['city']
        hh_url = item['hh_url']

        vac, created = Vacancy.objects.update_or_create(
            slug=slug,
            defaults={
                'title': title,
                'city': city,
                'track': track,
                'salary_text': item['salary_text'],
                'hh_url': hh_url,
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': item['has_dormitory'],
                'has_meal_compensation': True,
                'schedule': item['schedule'],
                'experience_level': item['experience_level'],
                'description': item['description'],
                'responsibilities': '• Выполнение производственных задач смены\n• Соблюдение стандартов пищевой безопасности ХАССП\n• Контроль параметров технологического процесса',
                'requirements': '• Студент или выпускник колледжа/ВУЗа\n• Внимательность, ответственность, желание развиваться в индустрии напитков\n• Готовность к активной работе в пик сезона',
                'benefits': '• Официальное трудоустройство по ТК РФ\n• Бесплатное общежитие в Москве рядом с заводом\n• Дотация на горячее питание в корпоративной столовой\n• Фирменная спецодежда и регулярные дегустации новинок',
                'is_active': True,
            }
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

    return {
        'ok': True,
        'total_fetched': len(items),
        'created_count': created_count,
        'updated_count': updated_count,
        'synced_at': feed['synced_at'],
        'status': feed['status']
    }
