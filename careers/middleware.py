import re
from django.utils import timezone
from .models import SiteVisitor


class VisitorTrackingMiddleware:
    """
    Автоматический журнал активности и статистика посещений всех пользователей сайта «Очаково».
    Фиксирует каналы переходов (сайт, стенды/QR, VK ID), типы устройств, глубину просмотра
    и прогресс в симуляторе завода.
    """

    EXCLUDED_PREFIXES = (
        '/static/',
        '/media/',
        '/favicon.ico',
        '/sw.js',
        '/manifest.json',
        '/robots.txt',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Исключаем статические ресурсы
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
            return self.get_response(request)

        # Не учитываем административную панель как посетительский просмотр
        if path.startswith('/admin/'):
            return self.get_response(request)

        # Гарантируем наличие сессии Django
        if not request.session.session_key:
            try:
                request.session.save()
            except Exception:
                pass

        session_key = request.session.session_key
        if session_key:
            try:
                self._record_visit(request, session_key, path)
            except Exception:
                # Middleware ни при каких обстоятельствах не должен блокировать выдачу страницы
                pass

        response = self.get_response(request)
        return response

    def _record_visit(self, request, session_key, path):
        # 1. Извлечение IP-адреса
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        # 2. Определение User-Agent, типа устройства и браузера
        ua = request.META.get('HTTP_USER_AGENT', '')
        ua_lower = ua.lower()

        if any(b in ua_lower for b in ('bot', 'crawler', 'spider', 'curl', 'wget', 'lighthouse')):
            device_type = 'bot'
        elif any(t in ua_lower for t in ('ipad', 'tablet', 'kindle', 'silk', 'playbook')):
            device_type = 'tablet'
        elif any(m in ua_lower for m in ('mobile', 'android', 'iphone', 'ipod', 'phone', 'harmonyos')):
            device_type = 'mobile'
        else:
            device_type = 'desktop'

        # Определение ОС и браузера
        os_name = "Неизвестная ОС"
        if "windows" in ua_lower:
            os_name = "Windows"
        elif "android" in ua_lower:
            os_name = "Android"
        elif "iphone" in ua_lower or "ipad" in ua_lower or "ios" in ua_lower:
            os_name = "iOS"
        elif "macintosh" in ua_lower or "mac os" in ua_lower:
            os_name = "macOS"
        elif "linux" in ua_lower:
            os_name = "Linux"

        browser_name = "Браузер"
        if "yabrowser" in ua_lower:
            browser_name = "Яндекс.Браузер"
        elif "edg" in ua_lower:
            browser_name = "Edge"
        elif "chrome" in ua_lower or "crios" in ua_lower:
            browser_name = "Chrome"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            browser_name = "Safari"
        elif "firefox" in ua_lower:
            browser_name = "Firefox"
        elif "opera" in ua_lower or "opr" in ua_lower:
            browser_name = "Opera"

        browser_os = f"{browser_name} ({os_name})"[:150]

        # 3. Определение источника перехода
        source = request.GET.get('source', '').strip().lower()
        if not source:
            source = request.GET.get('utm_source', '').strip().lower()
        if not source:
            source = request.session.get('lead_source', '')

        referrer = request.META.get('HTTP_REFERER', '')[:500]
        if not source:
            if 'vk.com' in referrer.lower():
                source = 'vk'
            elif 'hh.ru' in referrer.lower():
                source = 'hh'
            elif 'qr' in request.GET or 'stand' in request.GET:
                source = 'stand_qr'
            else:
                source = 'site'

        # Сохраняем источник в сессию для последующих шагов
        if source and source != 'site':
            request.session['lead_source'] = source

        # 4. Данные пользователя из VK ID, если есть
        vk_data = request.session.get('vk_user') or {}
        vk_id = str(vk_data.get('id') or request.session.get('vk_user_id') or '')[:100]
        vk_name = f"{vk_data.get('first_name', '')} {vk_data.get('last_name', '')}".strip()
        if not vk_name and vk_id:
            vk_name = f"VK ID {vk_id}"

        # 5. Создание или обновление записи в базе
        visitor, created = SiteVisitor.objects.get_or_create(
            session_key=session_key,
            defaults={
                'ip_address': ip,
                'device_type': device_type,
                'browser_os': browser_os,
                'user_agent': ua[:400],
                'landing_page': path[:255],
                'last_page': path[:255],
                'referrer': referrer,
                'source': source if source in dict(SiteVisitor._meta.get_field('source').choices) else 'site',
                'vk_user_id': vk_id,
                'vk_name': vk_name[:200],
                'page_views_count': 1,
            }
        )

        request.site_visitor = visitor

        if not created:
            update_fields = ['last_visit', 'page_views_count', 'last_page']
            visitor.page_views_count += 1
            visitor.last_page = path[:255]

            if source in ('stand_qr', 'vk', 'hh') and visitor.source == 'site':
                visitor.source = source
                update_fields.append('source')

            if vk_name and not visitor.vk_name:
                visitor.vk_name = vk_name[:200]
                update_fields.append('vk_name')

            if vk_id and not visitor.vk_user_id:
                visitor.vk_user_id = vk_id
                update_fields.append('vk_user_id')

            visitor.save(update_fields=update_fields)
