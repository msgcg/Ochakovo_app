import uuid

from django.db import models

from django.utils import timezone





class InternshipTrack(models.Model):

    """Карьерные направления практики и стажировок в Очаково"""

    slug = models.SlugField(max_length=60, unique=True, verbose_name="Слаг направления")

    title = models.CharField(max_length=150, verbose_name="Название трека")

    short_desc = models.CharField(max_length=300, verbose_name="Краткое описание")

    icon_name = models.CharField(max_length=60, default="sparkles", verbose_name="Имя иконки Lucide")

    accent_color = models.CharField(max_length=30, default="#D50032", verbose_name="Цвет акцента")

    mentor_name = models.CharField(max_length=100, default="Михалыч", verbose_name="Имя наставника")

    mentor_title = models.CharField(max_length=150, default="Главный технолог-квасовар", verbose_name="Должность наставника")

    mentor_avatar = models.CharField(max_length=150, default="mentor_brewer.jpg", verbose_name="Аватар наставника")

    order = models.PositiveIntegerField(default=0, verbose_name="Порядок вывода")



    class Meta:

        verbose_name = "Карьерный трек"

        verbose_name_plural = "Карьерные треки"

        ordering = ['order', 'id']



    def __str__(self):

        return self.title





class Vacancy(models.Model):

    """Реальные сезонные вакансии и оплачиваемые стажировки (пик: март - сентябрь)"""

    title = models.CharField(max_length=200, verbose_name="Название вакансии")

    slug = models.SlugField(max_length=200, unique=True, verbose_name="Слаг вакансии")

    track = models.ForeignKey(InternshipTrack, on_delete=models.SET_NULL, null=True, blank=True, related_name="vacancies", verbose_name="Трек")

    department = models.CharField(max_length=150, verbose_name="Подразделение / Цех")

    city = models.CharField(max_length=100, default="Москва", verbose_name="Город")

    address = models.CharField(max_length=250, default="ул. Рябиновая, д. 44 (м. Озёрная / Кунцевская)", verbose_name="Адрес площадки")

    salary_min = models.PositiveIntegerField(verbose_name="Зарплата от (₽)", default=65000)

    salary_max = models.PositiveIntegerField(verbose_name="Зарплата до (₽)", default=95000)

    salary_text = models.CharField(max_length=100, verbose_name="Отображение зарплаты", default="от 75 000 до 105 000 ₽")

    experience_level = models.CharField(max_length=100, default="Без опыта / Студенты", verbose_name="Требуемый опыт")

    schedule = models.CharField(max_length=100, default="Сменный 2/2 (дневные/ночные)", verbose_name="График работы")



    # Сезонные преимущества

    is_seasonal_peak = models.BooleanField(default=True, verbose_name="Пик сезона (март-сентябрь)")

    is_student_friendly = models.BooleanField(default=True, verbose_name="Оплачиваемая практика для студентов")

    has_dormitory = models.BooleanField(default=True, verbose_name="Общежитие в Москве рядом с работой")

    has_meal_compensation = models.BooleanField(default=True, verbose_name="Компенсация питания в столовой")



    description = models.TextField(verbose_name="Описание роли и смыслов работы")

    responsibilities = models.TextField(verbose_name="Обязанности (через перенос строки)")

    requirements = models.TextField(verbose_name="Требования к кандидату")

    benefits = models.TextField(verbose_name="Условия и бонусы")



    hh_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на hh.ru")

    is_active = models.BooleanField(default=True, verbose_name="Активна")

    order = models.PositiveIntegerField(default=0, verbose_name="Порядок вывода")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")



    class Meta:

        verbose_name = "Вакансия"

        verbose_name_plural = "Вакансии"

        ordering = ['order', '-id']



    def __str__(self):

        return f"{self.title} ({self.city})"



    def get_responsibilities_list(self):

        return [r.strip() for r in self.responsibilities.split('\n') if r.strip()]



    def get_requirements_list(self):

        return [r.strip() for r in self.requirements.split('\n') if r.strip()]



    def get_benefits_list(self):

        return [r.strip() for r in self.benefits.split('\n') if r.strip()]



    @property

    def matched_scenario(self):

        """Возвращает связанный игровой сценарий через regex-сопоставление"""

        from careers.services.scenario_matcher import match_game_scenario

        track_slug = self.track.slug if self.track else ''

        return match_game_scenario(self.title, self.description, track_slug)





class GameScenario(models.Model):

    """Игровой интерактивный инцидент в симуляторе завода Очаково"""

    slug = models.SlugField(max_length=100, unique=True, verbose_name="Слаг сценария")

    title = models.CharField(max_length=200, verbose_name="Название сценария")

    track = models.ForeignKey(InternshipTrack, on_delete=models.CASCADE, related_name="scenarios", verbose_name="Трек")

    target_vacancy = models.ForeignKey(Vacancy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Целевая вакансия")



    mentor_name = models.CharField(max_length=100, verbose_name="Имя наставника")

    mentor_role = models.CharField(max_length=150, verbose_name="Роль наставника")

    mentor_avatar = models.CharField(max_length=150, default="mentor_brewer.jpg", verbose_name="Файл аватара")

    workshop_name = models.CharField(max_length=150, default="Цех брожения и фильтрации", verbose_name="Название цеха")

    difficulty = models.CharField(max_length=50, default="Стажёр", verbose_name="Уровень сложности")

    time_limit_sec = models.PositiveIntegerField(default=35, verbose_name="Таймер на решение (сек)")

    bg_image = models.CharField(max_length=150, default="ochakovo_hero_banner.jpg", verbose_name="Фон цеха")



    # Стартовые параметры датчиков цеха

    initial_temperature = models.FloatField(default=28.5, verbose_name="Начальная температура (°C)")

    target_temp_min = models.FloatField(default=24.0, verbose_name="Мин. целевая темп-ра (°C)")

    target_temp_max = models.FloatField(default=26.5, verbose_name="Макс. целевая темп-ра (°C)")



    initial_brix = models.FloatField(default=8.4, verbose_name="Плотность затора (°Brix)")

    target_brix_min = models.FloatField(default=7.0, verbose_name="Мин. целевой Brix")

    target_brix_max = models.FloatField(default=7.6, verbose_name="Макс. целевой Brix")



    initial_line_speed = models.PositiveIntegerField(default=28000, verbose_name="Скорость конвейера (бут/ч)")

    initial_purity = models.PositiveIntegerField(default=92, verbose_name="Чистота контура CIP (%)")

    initial_balance = models.PositiveIntegerField(default=45, verbose_name="Баланс брожения: дрожжи/лакто (0-100)")



    description = models.TextField(verbose_name="Описание вводной ситуации")

    order = models.PositiveIntegerField(default=0, verbose_name="Порядок вывода")



    class Meta:

        verbose_name = "Игровой сценарий"

        verbose_name_plural = "Игровые сценарии"

        ordering = ['order', 'id']



    def __str__(self):

        return f"{self.title} ({self.mentor_name})"





class ScenarioNode(models.Model):

    """Узел диалогового графа инцидента"""

    scenario = models.ForeignKey(GameScenario, on_delete=models.CASCADE, related_name="nodes", verbose_name="Сценарий")

    node_id = models.CharField(max_length=60, verbose_name="ID узла")

    speaker_name = models.CharField(max_length=100, verbose_name="Говорящий")

    speaker_role = models.CharField(max_length=150, verbose_name="Роль говорящего")

    speaker_mood = models.CharField(

        max_length=30,

        choices=[

            ('normal', 'Рабочий'),

            ('concerned', 'Обеспокоенный'),

            ('critical', 'Тревожный / Критический'),

            ('happy', 'Довольный'),

            ('impressed', 'Восхищенный')

        ],

        default='normal',

        verbose_name="Эмоция"

    )

    dialogue_text = models.TextField(verbose_name="Реплика наставника / диспетчера")

    narrative_context = models.TextField(blank=True, verbose_name="Показания датчиков и обстановка")

    is_terminal = models.BooleanField(default=False, verbose_name="Финальный узел")

    is_success = models.BooleanField(default=False, verbose_name="Успешное завершение смены")

    final_verdict = models.TextField(blank=True, verbose_name="Итоговый разбор и производственный вывод")



    class Meta:

        verbose_name = "Узел сценария"

        verbose_name_plural = "Узлы сценариев"

        unique_together = ('scenario', 'node_id')



    def __str__(self):

        return f"{self.scenario.slug} -> {self.node_id}"





class ScenarioChoice(models.Model):

    """Вариант тактического действия или решения стажёра"""

    node = models.ForeignKey(ScenarioNode, on_delete=models.CASCADE, related_name="choices", verbose_name="Исходный узел")

    choice_text = models.CharField(max_length=250, verbose_name="Текст решения")

    tactical_hint = models.CharField(max_length=250, blank=True, verbose_name="Тактическая подсказка")

    equipment_code = models.CharField(max_length=50, blank=True, verbose_name="Код оборудования (drag&drop)")

    next_node_id = models.CharField(max_length=60, verbose_name="ID следующего узла")



    score_delta = models.IntegerField(default=15, verbose_name="Изменение очков")

    temp_delta = models.FloatField(default=0.0, verbose_name="Дельта температуры (°C)")

    brix_delta = models.FloatField(default=0.0, verbose_name="Дельта Brix")

    line_speed_delta = models.IntegerField(default=0, verbose_name="Дельта скорости конвейера")

    purity_delta = models.IntegerField(default=0, verbose_name="Дельта чистоты CIP")

    balance_delta = models.IntegerField(default=0, verbose_name="Дельта баланса брожения")



    mentor_quick_reaction = models.CharField(max_length=200, blank=True, verbose_name="Мгновенная реакция наставника")

    order = models.PositiveIntegerField(default=0, verbose_name="Порядок кнопки")



    class Meta:

        verbose_name = "Вариант действия"

        verbose_name_plural = "Варианты действий"

        ordering = ['order', 'id']



    def __str__(self):

        return f"{self.node.node_id} -> {self.choice_text[:40]}"





class GameSession(models.Model):

    """Живая игровая сессия кандидата в симуляторе завода"""

    session_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    scenario = models.ForeignKey(GameScenario, on_delete=models.CASCADE, verbose_name="Сценарий")

    current_node_id = models.CharField(max_length=60, default="start", verbose_name="Текущий узел")



    score = models.IntegerField(default=50, verbose_name="Текущие очки мастерства")

    temperature = models.FloatField(default=28.5, verbose_name="Текущая температура")

    brix = models.FloatField(default=8.4, verbose_name="Текущий Brix")

    line_speed = models.PositiveIntegerField(default=28000, verbose_name="Скорость конвейера")

    purity = models.PositiveIntegerField(default=92, verbose_name="Чистота CIP")

    balance = models.PositiveIntegerField(default=45, verbose_name="Баланс брожения")



    turns_count = models.PositiveIntegerField(default=0, verbose_name="Количество шагов")

    status = models.CharField(

        max_length=30,

        choices=[

            ('active', 'В процессе'),

            ('completed', 'Успешно завершена'),

            ('failed', 'Смена сорвана')

        ],

        default='active',

        verbose_name="Статус смены"

    )

    dialogue_history = models.JSONField(default=list, verbose_name="История реплик и действий")

    feedback_text = models.TextField(blank=True, verbose_name="Разбор наставника")



    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Начало смены")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Последнее действие")



    class Meta:

        verbose_name = "Игровая сессия"

        verbose_name_plural = "Игровые сессии"

        ordering = ['-created_at']



    def __str__(self):

        return f"Сессия {self.session_uuid} ({self.scenario.title})"





class JobApplication(models.Model):

    """Отклик студента / выпускника на оплачиваемую практику или вакансию"""

    full_name = models.CharField(max_length=150, verbose_name="ФИО соискателя")

    phone = models.CharField(max_length=30, verbose_name="Номер телефона")

    email = models.EmailField(verbose_name="Email")

    telegram = models.CharField(max_length=100, blank=True, verbose_name="Ник Telegram")

    university = models.CharField(max_length=200, verbose_name="ВУЗ / Колледж")

    study_field = models.CharField(max_length=150, verbose_name="Специальность / факультет")

    course_or_status = models.CharField(max_length=80, verbose_name="Курс / статус", default="3 курс")



    target_track = models.ForeignKey(InternshipTrack, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Интересующий трек")

    target_vacancy = models.ForeignKey(Vacancy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Выбранная вакансия")

    game_session = models.ForeignKey(GameSession, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сессия в симуляторе")

    game_score = models.IntegerField(null=True, blank=True, verbose_name="Баллы в симуляторе")



    cover_letter = models.TextField(blank=True, verbose_name="О себе / мотивация")

    completed_cases = models.JSONField(default=list, blank=True, verbose_name="Пройденные кейсы и оценки")

    hh_response_url = models.URLField(blank=True, null=True, verbose_name="Ссылка отклика на hh.ru")

    vk_url = models.CharField(max_length=255, blank=True, verbose_name="Профиль ВКонтакте")

    source = models.CharField(

        max_length=50,

        default='site',

        choices=[

            ('site', 'Сайт практики'),

            ('stand_qr', 'Стенд / QR-код'),

            ('vk', 'Вход ВКонтакте'),

            ('simulator', 'Симулятор цеха')

        ],

        verbose_name="Источник воронки"

    )

    cumulative_score = models.IntegerField(default=50, verbose_name="Суммарный скор (XP)")

    recommended_role = models.CharField(max_length=150, blank=True, verbose_name="Рекомендованная должность")

    internship_reduction = models.CharField(max_length=100, blank=True, verbose_name="Бонус стажировки")

    status = models.CharField(

        max_length=40,

        choices=[

            ('new', 'Новая заявка'),

            ('screening', 'На рассмотрении HR'),

            ('interview', 'Назначено собеседование'),

            ('practice_approved', 'Принят на оплачиваемую практику')

        ],

        default='new',

        verbose_name="Статус отклика"

    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подачи")



    class Meta:

        verbose_name = "Заявка на практику"

        verbose_name_plural = "Заявки на практику"

        ordering = ['-created_at']



    def __str__(self):

        return f"{self.full_name} — {self.university} ({self.target_vacancy or self.target_track or 'Общая'})"





class StoryMilestone(models.Model):

    """Вехи истории Очаково с 1978 по 2026 год"""

    year = models.CharField(max_length=20, verbose_name="Год / Период")

    badge = models.CharField(max_length=60, default="История вкуса", verbose_name="Бейдж вехи")

    title = models.CharField(max_length=200, verbose_name="Заголовок события")

    description = models.TextField(verbose_name="Подробное описание")

    icon_name = models.CharField(max_length=60, default="flag", verbose_name="Иконка Lucide")

    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")



    class Meta:

        verbose_name = "Веха истории"

        verbose_name_plural = "Вехи истории"

        ordering = ['order', 'id']



    def __str__(self):

        return f"{self.year} — {self.title}"





class CompanyPerk(models.Model):

    """Преимущества и условия работы для молодёжи в Очаково"""

    title = models.CharField(max_length=150, verbose_name="Заголовок преимущества")

    short_desc = models.TextField(verbose_name="Описание")

    icon_name = models.CharField(max_length=60, default="check-circle", verbose_name="Иконка Lucide")

    tag = models.CharField(max_length=60, default="Условия", verbose_name="Метка")

    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")



    class Meta:

        verbose_name = "Преимущество работодателя"

        verbose_name_plural = "Преимущества работодателя"

        ordering = ['order', 'id']



    def __str__(self):

        return self.title





class AIConfig(models.Model):

    """Единая конфигурация ИИ-наставника комбината Очаково (задается владельцем)"""

    gigachat_auth_key = models.CharField(

        max_length=500,

        blank=True,

        verbose_name="GigaChat Auth Key (Base64)",

        help_text="Готовый Base64 ключ авторизации Сбер Studio Salute"

    )

    gigachat_client_id = models.CharField(

        max_length=150,

        blank=True,

        verbose_name="GigaChat Client ID",

        help_text="Идентификатор клиента из Studio Salute"

    )

    gigachat_client_secret = models.CharField(

        max_length=150,

        blank=True,

        verbose_name="GigaChat Client Secret",

        help_text="Секретный ключ клиента из Studio Salute"

    )

    gigachat_model = models.CharField(

        max_length=60,

        default="GigaChat-Max",

        verbose_name="Модель GigaChat",

        help_text="Например: GigaChat-Max или GigaChat"

    )

    gigachat_scope = models.CharField(

        max_length=60,

        default="GIGACHAT_API_PERS",

        verbose_name="Scope API",

        help_text="GIGACHAT_API_PERS (для физлиц) или GIGACHAT_API_CORP"

    )

    is_active = models.BooleanField(

        default=True,

        verbose_name="Использовать онлайн ИИ",

        help_text="Если выключено или ключи не заданы, симулятор использует встроенный офлайн-движок"

    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")



    class Meta:

        verbose_name = "Настройки ИИ-наставника (единый ключ)"

        verbose_name_plural = "Настройки ИИ-наставника (единый ключ)"



    def __str__(self):

        status = "онлайн" if self.is_active else "офлайн"

        return f"Конфигурация ИИ Очаково ({status})"


class SiteVisitor(models.Model):
    """Журнал и статистика посещений всех пользователей сайта «Очаково»"""
    session_key = models.CharField(max_length=64, unique=True, verbose_name="Ключ сессии")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP-адрес")
    device_type = models.CharField(
        max_length=30,
        choices=[
            ('desktop', '🖥️ Компьютер (ПК)'),
            ('mobile', '📱 Смартфон'),
            ('tablet', '📟 Планшет'),
            ('bot', '🤖 Бот / Индексатор'),
        ],
        default='desktop',
        verbose_name="Тип устройства"
    )
    browser_os = models.CharField(max_length=150, blank=True, verbose_name="Браузер и ОС")
    user_agent = models.CharField(max_length=400, blank=True, verbose_name="User-Agent")
    landing_page = models.CharField(max_length=255, default="/", verbose_name="Страница входа")
    last_page = models.CharField(max_length=255, default="/", verbose_name="Последняя страница")
    referrer = models.CharField(max_length=500, blank=True, verbose_name="Источник перехода (Referer)")
    source = models.CharField(
        max_length=50,
        choices=[
            ('site', '💻 Прямой заход / Сайт'),
            ('stand_qr', '📱 Стенд / QR-код'),
            ('vk', '🌐 ВКонтакте'),
            ('simulator', '🎮 Симулятор цеха'),
            ('hh', '💼 HeadHunter'),
        ],
        default='site',
        verbose_name="Канал перехода"
    )
    vk_user_id = models.CharField(max_length=100, blank=True, verbose_name="ID ВКонтакте")
    vk_name = models.CharField(max_length=200, blank=True, verbose_name="Имя пользователя VK")
    page_views_count = models.PositiveIntegerField(default=1, verbose_name="Просмотров страниц")
    has_played_game = models.BooleanField(default=False, verbose_name="Запускал симулятор")
    has_completed_shift = models.BooleanField(default=False, verbose_name="Успешно завершил смену")
    has_applied = models.BooleanField(default=False, verbose_name="Подал заявку")
    last_game_score = models.IntegerField(null=True, blank=True, verbose_name="Баллы симулятора (XP)")
    first_visit = models.DateTimeField(auto_now_add=True, verbose_name="Первый визит")
    last_visit = models.DateTimeField(auto_now=True, verbose_name="Последняя активность")

    class Meta:
        verbose_name = "Посетитель сайта"
        verbose_name_plural = "Посетители сайта (Статистика)"
        ordering = ['-last_visit']

    def __str__(self):
        name = self.vk_name or (f"Гость {self.session_key[:8]}" if self.session_key else "Посетитель")
        return f"{name} ({self.get_device_type_display()}, {self.get_source_display()})"

