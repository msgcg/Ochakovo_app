import re
import html
import requests

def parse_vk_public_profile(query_or_url: str) -> dict:
    """
    Бесплатный быстрый парсер открытых профилей ВКонтакте без использования OAuth 2.0 и API-ключей.
    Подтягивает Имя, Фамилию, реальную аватарку, ID и статус прямо из веб-страницы.
    """
    raw = (query_or_url or '').strip()
    if not raw:
        return _build_fallback_profile('Стажёр', 'Очаково')

    # Очищаем входные данные: ссылки, @, лишние слэши и параметры
    clean = re.sub(r'^https?://', '', raw, flags=re.IGNORECASE)
    clean = re.sub(r'^(m\.)?vk\.(com|ru)/', '', clean, flags=re.IGNORECASE)
    clean = clean.lstrip('@').split('?')[0].split('/')[0].strip()

    if not clean:
        clean = 'candidate'

    # Подготавливаем запрос с заголовками бота (VK отдает полные OpenGraph метатеги без редиректа на логин)
    target_url = f"https://vk.com/{clean}"
    headers = {
        'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        resp = requests.get(target_url, headers=headers, timeout=6)
        if resp.status_code == 200 and resp.text:
            text = resp.text
            # Коррекция кодировки если страница в windows-1251
            if 'windows-1251' in text[:1200].lower():
                resp.encoding = 'windows-1251'
                text = resp.text

            # 1. Извлечение имени и фамилии
            name = None
            og_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', text)
            if og_title:
                name = og_title.group(1)
            else:
                h1_name = re.search(r'<h1\s+class=["\']page_name["\'][^>]*>([^<]+)</h1>', text)
                if h1_name:
                    name = h1_name.group(1)
                else:
                    title_tag = re.search(r'<title>([^<]+)</title>', text)
                    if title_tag:
                        name = title_tag.group(1)

            if name:
                name = html.unescape(name)
                # Очищаем суффиксы VK
                name = re.sub(r'\s*\|\s*(ВКонтакте|VK).*$', '', name, flags=re.IGNORECASE).strip()
                parts = [p for p in name.split() if p]
                first_name = parts[0] if parts else clean.capitalize()
                last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
            else:
                first_name = clean.capitalize()
                last_name = ''

            # 2. Извлечение аватара пользователя
            avatar = ''
            og_img = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', text)
            if og_img:
                avatar = html.unescape(og_img.group(1)).strip()
            else:
                avatar_img = re.search(r'class=["\'](pp_photo|page_avatar_img)["\'][^>]+src=["\']([^"\']+)["\']', text)
                if avatar_img:
                    avatar = html.unescape(avatar_img.group(2)).strip()

            if not avatar or 'camera_' in avatar:
                avatar = '/static/img/avatar_student_boy.jpg'

            # 3. Извлечение ID пользователя
            uid_match = re.search(r'"user_id":\s*(\d+)', text)
            if uid_match:
                user_id = uid_match.group(1)
            elif clean.lower().startswith('id') and clean[2:].isdigit():
                user_id = clean[2:]
            elif clean.isdigit():
                user_id = clean
            else:
                user_id = str(abs(hash(clean)) % 100000000)

            # 4. Извлечение описания / статуса
            status = ''
            og_desc = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', text)
            if og_desc:
                status = html.unescape(og_desc.group(1)).strip()

            return {
                'id': user_id,
                'username': clean,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f"{first_name} {last_name}".strip(),
                'avatar': avatar,
                'city': 'Москва',
                'university': 'МГУТУ им. К.Г. Разумовского',
                'study_field': 'Технология бродильных производств и виноделие',
                'status': status,
                'profile_url': f"https://vk.com/{clean}",
                'is_demo': False,
                'parsed': True
            }
    except Exception as exc:
        print(f"[VK Public Scraper] Error scraping {target_url}: {exc}")

    # Надежный фоллбэк на основе переданного имени/юзернейма
    clean_title = clean.capitalize()
    return _build_fallback_profile(clean_title, '', username=clean)


def _build_fallback_profile(first_name: str, last_name: str = '', username: str = 'intern') -> dict:
    return {
        'id': str(abs(hash(username)) % 100000000),
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'full_name': f"{first_name} {last_name}".strip(),
        'avatar': '/static/img/avatar_student_boy.jpg',
        'city': 'Москва',
        'university': 'МГУТУ им. К.Г. Разумовского',
        'study_field': 'Технология бродильных производств и виноделие',
        'status': 'Стажёр-технолог завода «Очаково» 2026',
        'profile_url': f"https://vk.com/{username}",
        'is_demo': True,
        'parsed': False
    }
