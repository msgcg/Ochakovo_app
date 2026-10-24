from ..models import Vacancy, GameScenario, InternshipTrack


REALITY_CHECK_TEXT = {
    "title": "ПРОИЗВОДСТВЕННАЯ РЕАЛЬНОСТЬ «ОЧАКОВО»",
    "badge": "ИНСАЙТ ОТ НАСТАВНИКА",
    "reality": "В реальной жизни всё устроено строже и сложнее, чем в симуляторе. На комбинате гудят многотонные автоматические линии, дрожжи капризны к миллидолям температуры, а за каждый вентиль и пробу сусла отвечает живой инженер.",
    "opportunity": "Но именно поэтому на комбинате «Очаково» так интересно и прибыльно: реальный инженерный драйв, оплачиваемая практика с 1-го дня (от 65 000 до 110 000 ₽), общежитие в Москве рядом с заводом, официальный стаж и прямой путь до начальника цеха!"
}


def calculate_cumulative_profile(session_data, current_scenario=None, current_score=95):
    """
    Рассчитывает суммарные карьерные успехи соискателя по всем пройденным сменам завода:
    - Суммарный XP (очки опыта)
    - Пройденные цеха и подтвержденные навыки
    - Квалификационный разряд
    - Персональные рекомендации вакансий с бонусами стажировки
    """
    # Сбор данных из сессии
    completed_slugs = set()
    total_xp = int(current_score)
    
    saved_progress = session_data.get('saved_cases_progress', {})
    if isinstance(saved_progress, dict):
        for slug, data in saved_progress.items():
            completed_slugs.add(slug)
            if isinstance(data, dict):
                total_xp += int(data.get('score', 80))
            elif isinstance(data, (int, float)):
                total_xp += int(data)

    if current_scenario:
        completed_slugs.add(current_scenario.slug)

    cases_count = max(len(completed_slugs), 1)

    # Определение квалификационного разряда по суммарным баллам
    if total_xp >= 300:
        rank = "Инженер-наставник кадрового резерва (Высший разряд)"
        bonus_badge = "Сокращение стажировки на 70% + прямой оффер"
    elif total_xp >= 200:
        rank = "Мастер смены 3-го производственного разряда"
        bonus_badge = "Сокращение стажировки на 50% + надбавка"
    elif total_xp >= 100:
        rank = "Техник-практикант 2-го разряда"
        bonus_badge = "Сокращение стажировки на 30%"
    else:
        rank = "Стажёр-испытатель 1-го разряда"
        bonus_badge = "Гарантированная оплачиваемая практика"

    # Подбор лучших вакансий по суммарным достижениям
    all_vacancies = list(Vacancy.objects.filter(is_active=True).order_by('-salary_max', 'order'))
    
    # Категоризация по доминирующим навыкам
    has_brewing = any('brew' in s or 'yeast' in s or 'hop' in s for s in completed_slugs)
    has_bottling = any('bottling' in s or 'krones' in s or 'pallet' in s for s in completed_slugs)
    has_lab = any('cip' in s or 'lab' in s or 'kvass' in s for s in completed_slugs)

    recommendations = []
    
    # Приоритет вакансий
    for vac in all_vacancies:
        title_lower = vac.title.lower()
        match_score = 80
        reason = ""
        bonuses = bonus_badge

        if has_brewing and ('технолог' in title_lower or 'вар' in title_lower or 'брожен' in title_lower):
            match_score = 98 if total_xp > 150 else 92
            reason = f"По сумме успехов брожения и термоконтроля ({total_xp} XP) — рекомендован прямой допуск в цех квасоварения."
            bonuses = "Сокращение стажировки на 50% + премия за смену"
        elif has_bottling and ('механик' in title_lower or 'наладчик' in title_lower or 'розлив' in title_lower or 'оператор' in title_lower):
            match_score = 96 if total_xp > 150 else 90
            reason = f"По сумме успехов на конвейере и оборудовании ({total_xp} XP) — высокий приоритет на линии Krones."
            bonuses = "Персональный наставник + ускоренная сдача на разряд"
        elif has_lab and ('микробиолог' in title_lower or 'лаборант' in title_lower or 'контролер' in title_lower or 'качества' in title_lower):
            match_score = 94 if total_xp > 120 else 88
            reason = f"По суммарным навыкам санитизации и лабораторного анализа ({total_xp} XP) — готовность к контролю стандартов."
            bonuses = "Допуск к испытаниям новых авторских сортов"
        elif total_xp >= 200 and ('начальник' in title_lower or 'мастер' in title_lower or 'ведущий' in title_lower):
            match_score = 95
            reason = f"Высокий общий карьерный балл ({total_xp} XP по комбинату) — рекомендация в кадровый резерв руководства."
            bonuses = "Прямой оффер с окладом от 90 000 ₽"
        else:
            match_score = min(85 + (total_xp // 30), 91)
            reason = f"Уверенная производственная база завода «Очаково» ({total_xp} XP)."

        recommendations.append({
            'vacancy': vac,
            'title': vac.title,
            'slug': vac.slug,
            'salary_text': vac.salary_text or "от 70 000 ₽",
            'city': vac.city or "Москва",
            'match_score': match_score,
            'bonus_badge': bonuses,
            'reason': reason,
            'hh_url': vac.hh_url or f"https://hh.ru/search/vacancy?text={vac.title}"
        })

    # Сортируем по проценту соответствия
    recommendations.sort(key=lambda r: r['match_score'], reverse=True)
    top_recommendations = recommendations[:3]

    return {
        'total_xp': total_xp,
        'cases_count': cases_count,
        'rank': rank,
        'bonus_badge': bonus_badge,
        'reality_check': REALITY_CHECK_TEXT,
        'top_recommendations': top_recommendations,
        'all_recommendations': recommendations[:6]
    }
