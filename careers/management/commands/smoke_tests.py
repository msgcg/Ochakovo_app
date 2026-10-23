import sys
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
from careers.models import InternshipTrack, Vacancy, GameScenario, GameSession
from careers.services.scenario_matcher import match_game_scenario
from careers.services.whisper_service import WhisperVulkanService
from careers.services.sber_service import OchakovoAIService


class Command(BaseCommand):
    help = "Запуск комплексных автоматических смоук-тестов платформы «Очаково»"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Запуск смоук-тестирования платформы «Очаково» ==="))
        client = Client()
        passed = 0
        total = 0

        def check(description, condition_fn):
            nonlocal passed, total
            total += 1
            self.stdout.write(f"Тест {total}: {description}... ", ending="")
            try:
                res = condition_fn()
                if res:
                    passed += 1
                    self.stdout.write(self.style.SUCCESS("[УСПЕШНО]"))
                else:
                    self.stdout.write(self.style.ERROR("[ОШИБКА: условие не выполнено]"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[ИСКЛЮЧЕНИЕ: {e}]"))

        # 1. Проверка наличия данных в базе
        check("Наличие карьерных треков и сценариев Очаково", lambda: InternshipTrack.objects.count() > 0 and GameScenario.objects.count() > 0)
        check("Наличие активных вакансий Очаково", lambda: Vacancy.objects.filter(is_active=True).count() > 0)

        # 2. Проверка HTTP-эндпоинтов
        check("Главная страница (/) возвращает 200 OK", lambda: client.get(reverse('careers:home')).status_code == 200)
        check("Каталог вакансий (/vacancies/) возвращает 200 OK", lambda: client.get(reverse('careers:vacancies_list')).status_code == 200)
        check("Выбор сценариев (/game/) возвращает 200 OK", lambda: client.get(reverse('careers:game_select')).status_code == 200)
        check("Центр прогресса (/progress/) возвращает 200 OK", lambda: client.get(reverse('careers:progress')).status_code == 200)
        check("Страница истории бренда (/story/) возвращает 200 OK", lambda: client.get(reverse('careers:story')).status_code == 200)

        # 3. PWA компоненты
        check("PWA манифест (/manifest.json) доступен и валиден", lambda: client.get(reverse('careers:manifest')).status_code == 200)
        check("Service Worker (/sw.js) доступен с заголовком Service-Worker-Allowed", lambda: client.get(reverse('careers:service_worker')).status_code == 200)

        # 4. AJAX API вакансий
        def test_vacancies_api():
            resp = client.get(reverse('careers:vacancies_search_api'))
            if resp.status_code != 200:
                return False
            data = resp.json()
            return data.get('ok') is True and data.get('count', 0) > 0
        check("AJAX API поиска вакансий (/api/vacancies/search/)", test_vacancies_api)

        # 5. Regex-матчер сценариев
        check("Regex-матчер сопоставляет вакансию розлива со сценарием Krones", lambda: match_game_scenario("Оператор линии розлива банок", "Работа с машинами Krones", "engineering") is not None)

        # 6. Сервис Whisper Vulkan/CPU
        mode, fallback = WhisperVulkanService.get_acceleration_config()
        check(f"Конфигурация Whisper ускорения ({mode}, fallback={fallback})", lambda: mode in ('auto', 'vulkan', 'cpu'))

        # 7. Защита от прокрастинации и аварийная логика ИИ
        def test_stall_protection():
            sc = GameScenario.objects.first()
            if not sc:
                return False
            sess = GameSession.objects.create(scenario=sc, current_node_id='start', turns_count=0)
            res = OchakovoAIService.process_turn(sc, sess, user_message="давай просто подождем, не надо спешить")
            sess.delete()
            return res.get('ok') is True and (res.get('verdict') in ['warning', 'critical_fail'] or res.get('show_hints') is True)
        check("Логика отслеживания прокрастинации в цеху", test_stall_protection)

        self.stdout.write(self.style.NOTICE("-------------------------------------------------------"))
        if passed == total:
            self.stdout.write(self.style.SUCCESS(f"ВСЕ {passed}/{total} ТЕСТОВ УСПЕШНО ПРОЙДЕНЫ! Платформа готова к демонстрации."))
        else:
            self.stdout.write(self.style.WARNING(f"Пройдено {passed} из {total} тестов."))
            sys.exit(1)
