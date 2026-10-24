from .models import InternshipTrack, Vacancy, GameScenario

def pluralize_ru(n, one, two, five):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {one}"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} {two}"
    else:
        return f"{n} {five}"

def ochakovo_context(request):
    """Глобальный контекст бренда Очаково для всех страниц и админки"""
    total_cases = GameScenario.objects.count()
    
    try:
        from .models import SiteVisitor, GameSession, JobApplication
        total_v = SiteVisitor.objects.count()
        qr_v = SiteVisitor.objects.filter(source='stand_qr').count()
        vk_v = SiteVisitor.objects.filter(source='vk').count()
        played_v = SiteVisitor.objects.filter(has_played_game=True).count()
        completed_v = SiteVisitor.objects.filter(has_completed_shift=True).count()
        applied_v = JobApplication.objects.count()
        approved_v = JobApplication.objects.filter(status='practice_approved').count()
        conversion = round((applied_v / total_v * 100), 1) if total_v > 0 else 0
        v_stats = {
            'total_visitors': total_v,
            'qr_visitors': qr_v,
            'vk_visitors': vk_v,
            'played_count': played_v,
            'completed_count': completed_v,
            'applied_count': applied_v,
            'approved_count': approved_v,
            'conversion_rate': conversion,
            'sessions_count': GameSession.objects.count(),
        }
    except Exception:
        v_stats = {
            'total_visitors': 0,
            'qr_visitors': 0,
            'vk_visitors': 0,
            'played_count': 0,
            'completed_count': 0,
            'applied_count': 0,
            'approved_count': 0,
            'conversion_rate': 0,
            'sessions_count': 0,
        }
    return {
        'brand_name': 'Очаково',
        'brand_year': '1978',
        'brand_slogan': 'Всё по-настоящему • 100% натурально',
        'brand_color_primary': '#D50032',
        'brand_color_dark': '#12161A',
        'season_months': 'Март — Сентябрь 2026',
        'season_title': 'Пик сезона напитков 2026',
        'season_badge': 'Оплачиваемая практика & Карьерный старт',
        'tracks_nav': InternshipTrack.objects.all().order_by('order'),
        'total_active_vacancies': Vacancy.objects.filter(is_active=True).count(),
        'total_cases_count': total_cases,
        'total_scenarios_count': total_cases,
        'total_cases_label': pluralize_ru(total_cases, 'кейс', 'кейса', 'кейсов'),
        'total_shifts_label': pluralize_ru(total_cases, 'смена', 'смены', 'смен'),
        'total_workshops_label': pluralize_ru(total_cases, 'цех', 'цеха', 'цехов'),
        'max_possible_score': total_cases * 100,
        'visitor_stats': v_stats,
        'contacts': {
            'phone': '+7 (495) 785-39-30',
            'phone_ext': 'доб. 1155, 2107',
            'mobile_1': '+7 (903) 153-77-40',
            'mobile_2': '+7 (903) 256-33-97',
            'telegram': 'https://t.me/ochakovo_official',
            'vk': 'https://vk.com/ochakovo',
            'email': 'rabota@ochakovo.ru',
            'address': 'г. Москва, ул. Рябиновая, д. 44 (м. Озёрная / Кунцевская)',
            'site': 'https://ochakovo.ru/'
        }
    }
