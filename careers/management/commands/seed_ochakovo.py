from django.core.management.base import BaseCommand
from careers.models import (
    InternshipTrack,
    Vacancy,
    GameScenario,
    ScenarioNode,
    ScenarioChoice,
    StoryMilestone,
    CompanyPerk,
    SiteVisitor,
    AIConfig,
)


class Command(BaseCommand):
    help = "Наполняет базу данных реальными вакансиями Очаково, сценариями симулятора и вехами истории"

    def handle(self, *args, **options):
        self.stdout.write("Начало наполнения базы данных Очаково...")
        # 0. ГАРАНТИРОВАННОЕ СОЗДАНИЕ СУПЕРПОЛЬЗОВАТЕЛЯ admin / ochakovo2026
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user, created = User.objects.get_or_create(username='admin')
        admin_user.set_password('ochakovo2026')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        if not admin_user.email:
            admin_user.email = 'admin@ochakovo.ru'
        admin_user.save()
        if created:
            self.stdout.write(self.style.SUCCESS("[OK] Создан суперпользователь: admin (пароль: ochakovo2026)"))
        else:
            self.stdout.write(self.style.SUCCESS("[OK] Обновлен суперпользователь: admin (пароль: ochakovo2026)"))

        # 1. КАРЬЕРНЫЕ ТРЕКИ
        tracks_data = [
            {
                'slug': 'brewing',
                'title': 'Бродильное производство & Квасоварение',
                'short_desc': 'Сердце комбината: работа с суслом, чистыми культурами закваски Очаково, ЦКТ и биохимией живого брожения.',
                'icon_name': 'sparkles',
                'accent_color': '#D50032',
                'mentor_name': 'Михалыч',
                'mentor_title': 'Главный технолог-квасовар (стаж 20 лет)',
                'mentor_avatar': 'mentor_brewer.jpg',
                'order': 1
            },
            {
                'slug': 'automation',
                'title': 'Автоматизация & Линии розлива',
                'short_desc': 'Высокоскоростная робототехника Krones, КИПиА, манипуляторы, системы SCADA и конвейеры до 50 000 бут/час.',
                'icon_name': 'cpu',
                'accent_color': '#0284c7',
                'mentor_name': 'Анна',
                'mentor_title': 'Ведущий инженер АСУ ТП и робототехники',
                'mentor_avatar': 'mentor_engineer.jpg',
                'order': 2
            },
            {
                'slug': 'lab',
                'title': 'Контроль качества & Лаборатория',
                'short_desc': 'Микробиологические экспресс-тесты, хроматография, сенсорный и органолептический анализ натуральности сырья.',
                'icon_name': 'flask-conical',
                'accent_color': '#10b981',
                'mentor_name': 'Елена',
                'mentor_title': 'Руководитель лаборатории микробиологии',
                'mentor_avatar': 'mentor_lab.jpg',
                'order': 3
            },
            {
                'slug': 'logistics',
                'title': 'Складская логистика WMS & Хаб',
                'short_desc': 'Управление интеллектуальным складом класса А, логистика 500+ фур в сутки в разгар летнего пика продаж.',
                'icon_name': 'truck',
                'accent_color': '#f59e0b',
                'mentor_name': 'Роман',
                'mentor_title': 'Диспетчер логистического комплекса WMS',
                'mentor_avatar': 'mentor_logistics.jpg',
                'order': 4
            },
            {
                'slug': 'marketing',
                'title': 'Маркетинг & Бренд-стратегия',
                'short_desc': 'Продвижение молодежных линеек CoolCola, Fancy, Street, создание новых дропов кваса и digital-кампаний.',
                'icon_name': 'megaphone',
                'accent_color': '#8b5cf6',
                'mentor_name': 'Артём',
                'mentor_title': 'Бренд-стратег молодежных напитков',
                'mentor_avatar': 'mentor_marketing.jpg',
                'order': 5
            }
        ]

        tracks = {}
        for td in tracks_data:
            t, _ = InternshipTrack.objects.update_or_create(slug=td['slug'], defaults=td)
            tracks[td['slug']] = t

        self.stdout.write(f"Создано/обновлено карьерных треков: {len(tracks)}")

        # 2. РЕАЛЬНЫЕ ВАКАНСИИ СЕЗОНА ИЗ ОФИЦИАЛЬНОГО БРЕНДБУКА ПРАКТИКИ ОЧАКОВО
        vacancies_data = [
            {
                'title': 'Оператор варочного цеха (сырье, сусло, закваска)',
                'slug': 'master-tehnolog-proizvodstva',
                'track': tracks['brewing'],
                'department': 'Технологический цех',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44 (м. Озёрная)',
                'hh_url': 'https://hh.ru/vacancy/107211997',
                'salary_min': 70000,
                'salary_max': 95000,
                'salary_text': 'от 70 000 ₽ до вычета налога',
                'experience_level': 'Без опыта / Студенты профильных вузов',
                'schedule': 'Сменный 2/2 (день-ночь-отсыпной-выходной: с 8:00 до 20:00 и с 20:00 до 8:00)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Оплачиваемая практика в технологическом цехе завода Очаково (с начала марта/апреля по июль/август). Работа в цехе варки, работа с сырьем (сахар, сироп, сусло, натуральная закваска двойного брожения), контроль ферментации в ЦКТ. Официальное трудоустройство по срочному договору ТК РФ с возможностью перехода на постоянную работу.',
                'responsibilities': (
                    'Работа в цехе варки напитков, контроль рецептуры и загрузки натурального сырья\n'
                    'Контроль технологических параметров брожения сусла (температура, плотность Brix, кислотность)\n'
                    'Внесение чистых культур закваски натурального брожения штамма 1978\n'
                    'Управление клапанами охлаждающей рубашки ЦКТ и перекачкой через SCADA\n'
                    'Органолептическая оценка полуфабриката перед передачей на сепарацию'
                ),
                'requirements': (
                    'Студенты профильных факультетов (пищевые технологии, биотехнология, бродильные производства)\n'
                    'Понимание биохимии ферментации и санитарно-гигиенических норм\n'
                    'Внимательность к показаниям датчиков и ответственность'
                ),
                'benefits': (
                    'Официальное трудоустройство по ТК РФ с первого дня практики\n'
                    'Заработная плата от 70 000 ₽ (с ночными сменами больше) без задержек\n'
                    'Спецодежда и регулярный медосмотр полностью за счет завода\n'
                    'Питание в производственной столовой по льготной цене\n'
                    '50% оплаты проживания в общежитии компании\n'
                    'Скидка на всю продукцию комбината Очаково\n'
                    'Оформление всех документов и отчетов по практике для ВУЗа/колледжа'
                ),
                'order': 1
            },
            {
                'title': 'Оператор линии розлива (Krones, выдув, этикетка)',
                'slug': 'operator-naladchik-linii-rozliva',
                'track': tracks['automation'],
                'department': 'Цех розлива напитков',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/98465520',
                'salary_min': 70000,
                'salary_max': 95000,
                'salary_text': 'от 70 000 ₽ до вычета налога',
                'experience_level': 'Без опыта (обучение на месте)',
                'schedule': 'Сменный с ночными и дневными сменами (с 8:00 до 20:00 или с 20:00 до 8:00)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Оплачиваемая практика в высокоскоростном цехе розлива комбината Очаково. Работа на оборудовании Krones: этикетировочные автоматы, упаковочные машины, выдувные агрегаты, роботы-паллетайзеры, замена комплектующих и переналадка узлов.',
                'responsibilities': (
                    'Работа на скоростных машинах линии розлива (этикетка, упаковка, выдувная машина, паллет)\n'
                    'Контроль бесперебойной подачи бутылок, банок и упаковочных материалов\n'
                    'Своевременная замена комплектующих и расходных материалов узлов линии\n'
                    'Мониторинг давления CO2, герметичности укупорки и уровня налива\n'
                    'Участие в технологической CIP-мойке и санитарной обработке контуров'
                ),
                'requirements': (
                    'Технический склад ума, интерес к механике и промышленной робототехнике\n'
                    'Студенты инженерных, механических, энергетических факультетов и колледжей\n'
                    'Готовность к активной сменной работе на динамичном конвейере'
                ),
                'benefits': (
                    'Официальное трудоустройство по срочному договору ТК РФ с переводом в штат\n'
                    'Заработная плата от 70 000 ₽ до вычета налога (с ночными сменами больше)\n'
                    'Бесплатная спецодежда и медосмотр за наш счет\n'
                    'Горячее питание в столовой по льготной цене\n'
                    '50% компенсации проживания в общежитии завода в Москве\n'
                    'Скидка на всю продукцию комбината (квас, CoolCola, соки)'
                ),
                'order': 2
            },
            {
                'title': 'Лаборант экспресс-анализа качества',
                'slug': 'inzhener-himik-laboratoriya',
                'track': tracks['lab'],
                'department': 'Лаборатория',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/106316381',
                'salary_min': 60000,
                'salary_max': 85000,
                'salary_text': 'от 60 000 ₽ до вычета налога (с ночью больше)',
                'experience_level': 'Студенты химико-биологических направлений',
                'schedule': 'График 2/2 дневные смены с 8:00 до 20:00 или 2/2 с ночными сменами (день-ночь-отсыпной-выходной)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Оплачиваемая практика в центральной аналитической лаборатории Очаково. Взятие проб, микробиологический посев, экспресс-контроль физико-химических показателей натуральности напитков (pH, титруемая кислотность, сухие вещества Brix).',
                'responsibilities': (
                    'Взятие проб сусла, закваски и готовой продукции на линии розлива и из ЦКТ\n'
                    'Проведение экспресс-анализов качества: pH-метрия, титрование, замер плотности Brix\n'
                    'Контроль микробиологической чистоты и отсутствия посторонней микрофлоры\n'
                    'Оформление протоколов анализов и паспортов качества партий'
                ),
                'requirements': (
                    'Студенты профильных факультетов (химия, биохимия, микробиология, биотехнология)\n'
                    'Навыки работы с лабораторной посудой и измерительными приборами\n'
                    'Педантичность, аккуратность и соблюдение стандартов стерильности'
                ),
                'benefits': (
                    'Официальный срочный трудовой договор по ТК РФ с перспективой перехода на постоянную должность\n'
                    'Заработная плата от 60 000 ₽ (с ночными сменами больше)\n'
                    'Предоставляем спецодежду (лабораторные халаты, СИЗ) и медосмотр за счет компании\n'
                    'Питание в столовой по льготной цене, 50% оплаты за общежитие, скидка на напитки'
                ),
                'order': 3
            },
            {
                'title': 'Оператор склада с ТТН (WMS-комплекс)',
                'slug': 'menedzher-skladskoj-logistiki-wms',
                'track': tracks['logistics'],
                'department': 'Складской комплекс',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/106795271',
                'salary_min': 60000,
                'salary_max': 82000,
                'salary_text': 'от 60 000 ₽ до вычета налога (с ночью больше)',
                'experience_level': 'Без опыта / Студенты',
                'schedule': 'График 2/2 дневные смены с 8:00 до 20:00 или 2/2 с ночными сменами (с 8:00 до 20:00 и с 20:00 до 8:00)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Оплачиваемая практика в складском комплексе комбината Очаково. Работа с программой складского учета WMS, оформление товарно-транспортных накладных (ТТН), работа с документацией и координация отгрузок фур в летний пик сезона.',
                'responsibilities': (
                    'Работа в автоматизированной системе WMS и ведение первичной складской документации\n'
                    'Оформление товарно-транспортных накладных (ТТН) для водителей фур\n'
                    'Контроль комплектации заказов по спецификациям торговых сетей\n'
                    'Взаимодействие с диспетчерами, кладовщиками и водителями электрокаров'
                ),
                'requirements': (
                    'Уверенное владение ПК, внимательность при работе с номерами партий и накладными\n'
                    'Студенты логистических, экономических или технических специальностей\n'
                    'Умение быстро ориентироваться в динамичной складской обстановке'
                ),
                'benefits': (
                    'Официальное трудоустройство по ТК РФ, стаж с первого дня\n'
                    'Заработная плата от 60 000 ₽ до вычета налога (с ночными сменами больше)\n'
                    'Спецодежда и медосмотр за счет завода, питание по льготной цене\n'
                    '50% оплаты за проживание в общежитии, корпоративная скидка на продукцию'
                ),
                'order': 4
            },
            {
                'title': 'Кладовщик (управление комплектовщиками)',
                'slug': 'kladovshik-upravlenie',
                'track': tracks['logistics'],
                'department': 'Складской комплекс',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/106795271',
                'salary_min': 56000,
                'salary_max': 75000,
                'salary_text': 'от 56 000 ₽ до вычета налога (с ночью больше)',
                'experience_level': 'Без опыта / Студенты',
                'schedule': 'График 2/2 дневные смены с 8:00 до 20:00 или 2/2 с ночными сменами (с 8:00 до 20:00 и с 20:00 до 8:00)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Оплачиваемая практика в складском логистическом комплексе завода Очаково. Работа с накладными, управление комплектовщиками, контроль размещения паллет готовой продукции на электрокарах и стеллажах.',
                'responsibilities': (
                    'Работа с накладными и контроль физического перемещения грузов\n'
                    'Управление сменой комплектовщиков, распределение задач по сборке заказов\n'
                    'Контроль безопасного движения электропогрузчиков и электрокаров\n'
                    'Проведение инвентаризаций и контроль остатков готовой продукции'
                ),
                'requirements': (
                    'Ответственность, организаторские способности, активность\n'
                    'Студенты любых направлений, желающие освоить складскую логистику\n'
                    'Готовность к сменной работе на современном автоматизированном складе'
                ),
                'benefits': (
                    'Официальное оформление по ТК РФ, стабильная белая зарплата от 56 000 ₽\n'
                    'Бесплатная спецодежда и медосмотр, питание в столовой по льготной цене\n'
                    '50% оплаты проживания в общежитии компании, скидка на напитки комбината'
                ),
                'order': 5
            },
            {
                'title': 'Купажист / Разработчик новых вкусов (R&D)',
                'slug': 'trejd-marketolog-napitkov',
                'track': tracks['marketing'],
                'department': 'Инновационный центр R&D',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/106723644',
                'salary_min': 75000,
                'salary_max': 110000,
                'salary_text': 'от 75 000 до 110 000 ₽',
                'experience_level': 'Студенты старших курсов / Выпускники',
                'schedule': 'График 5/2 (гибкое начало дня с 9:00 до 18:00)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Творческая практика по созданию новых напитков, разработке вкусовых профилей молодежных линеек CoolCola, Fancy, Street и архивных рецептов кваса Олимпиады-80. Органолептический анализ, подбор натуральных экстрактов и дизайн презентационных образцов.',
                'responsibilities': (
                    'Лабораторное купажирование сиропов, соков и натуральных экстрактов\n'
                    'Проведение слепых дегустационных панелей и сенсорный анализ напитков\n'
                    'Поиск и воссоздание архивных рецептур традиционного кваса комбината\n'
                    'Участие в тестировании потребительских предпочтений и дизайна упаковки'
                ),
                'requirements': (
                    'Студенты пищевых, биотехнологических или маркетинговых факультетов\n'
                    'Тонкое обоняние и вкус, интерес к индустрии безалкогольных напитков\n'
                    'Креативность, инициативность и стремление создавать инновационные продукты'
                ),
                'benefits': (
                    'Официальное трудоустройство по ТК РФ, оклад от 75 000 ₽\n'
                    'Работа в современной инновационной R&D лаборатории завода\n'
                    'Льготное питание в столовой, компенсация общежития, скидки на продукцию'
                ),
                'order': 6
            },
            {
                'title': 'Оператор линии розлива (Краснодарский филиал)',
                'slug': 'operator-linii-krasnodar',
                'track': tracks['automation'],
                'department': 'Производственный комплекс Краснодар',
                'city': 'Краснодар',
                'address': 'г. Краснодар, ул. Тополиная, д. 4',
                'hh_url': 'https://hh.ru/vacancy/107618804',
                'salary_min': 65000,
                'salary_max': 90000,
                'salary_text': 'от 65 000 до 90 000 ₽',
                'experience_level': 'Без опыта / Студенты',
                'schedule': 'Сменный 2/2',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': False,
                'has_meal_compensation': True,
                'description': 'Сезонный набор на южную производственную площадку «Очаково» в Краснодаре. Обслуживание современных автоматических линий фасовки кваса и безалкогольных напитков.',
                'responsibilities': (
                    'Контроль за ходом технологического процесса розлива\n'
                    'Проверка качества укупорки и наклейки этикетки\n'
                    'Устранение мелких технологических задержек на конвейере'
                ),
                'requirements': (
                    'Ответственность, исполнительность, желание работать на современном заводе'
                ),
                'benefits': (
                    'Официальное оформление по ТК РФ, полный соцпакет, питание'
                ),
                'order': 7
            }
        ]

        vacancies = {}
        for vd in vacancies_data:
            v, _ = Vacancy.objects.update_or_create(slug=vd['slug'], defaults=vd)
            vacancies[vd['slug']] = v

        self.stdout.write(f"Создано/обновлено вакансий: {len(vacancies)}")

        # 3. ИГРОВЫЕ СЦЕНАРИИ (7 УНИКАЛЬНЫХ СЦЕНАРИЕВ С НЕПОВТОРИМЫМИ ФОНАМИ ЦЕХОВ И ВАКАНСИЯМИ)
        scenarios_data = [
            {
                'slug': 'brew-yeast-flex',
                'title': 'Дрожжевой флекс в ЦКТ №7',
                'track': tracks['brewing'],
                'target_vacancy': vacancies.get('master-tehnolog-proizvodstva'),
                'mentor_name': 'Михалыч',
                'mentor_role': 'Главный технолог-квасовар завода',
                'mentor_avatar': 'mentor_brewer.jpg',
                'workshop_name': 'Цех брожения и созревания кваса (ЦКТ №7)',
                'difficulty': 'Стажёр',
                'time_limit_sec': 45,
                'bg_image': 'vn_bg/bg_brewhouse_cct.jpg',
                'initial_temperature': 28.5,
                'target_temp_min': 24.0,
                'target_temp_max': 26.0,
                'initial_brix': 8.4,
                'target_brix_min': 7.0,
                'target_brix_max': 7.6,
                'initial_line_speed': 28000,
                'initial_purity': 92,
                'initial_balance': 45,
                'description': 'В жаркий полдень дрожжи в танке брожения устроили рейв и разогрели сусло до 28.5°C! Охлади рубашку ЦКТ и внеси легендарную закваску 1978, пока квас не улетел в космос!',
                'order': 1
            },
            {
                'slug': 'brew-double-fermentation',
                'title': 'Битва за сусло: Тонкости двойного брожения',
                'track': tracks['brewing'],
                'target_vacancy': vacancies.get('master-tehnolog-proizvodstva'),
                'mentor_name': 'Михалыч',
                'mentor_role': 'Главный технолог-квасовар завода',
                'mentor_avatar': 'mentor_brewer.jpg',
                'workshop_name': 'Варочный цех приготовления сусла',
                'difficulty': 'Стажёр',
                'time_limit_sec': 45,
                'bg_image': 'vn_bg/bg_brewhouse_kettles.jpg',
                'initial_temperature': 28.5,
                'target_temp_min': 24.0,
                'target_temp_max': 26.0,
                'initial_brix': 8.4,
                'target_brix_min': 7.0,
                'target_brix_max': 7.6,
                'initial_line_speed': 28000,
                'initial_purity': 92,
                'initial_balance': 45,
                'description': 'Классический инцидент варки и брожения: балансируем терморежим сусла в затирочном котле и спасаем партию легендарного напитка.',
                'order': 2
            },
            {
                'slug': 'krones-robot-tilt',
                'title': 'Роботы Krones в тильте',
                'track': tracks['automation'],
                'target_vacancy': vacancies.get('operator-naladchik-linii-rozliva'),
                'mentor_name': 'Анна',
                'mentor_role': 'Ведущий инженер АСУ ТП и робототехники',
                'mentor_avatar': 'mentor_engineer.jpg',
                'workshop_name': 'Высокоскоростной цех розлива CoolCola и кваса',
                'difficulty': 'Практикант',
                'time_limit_sec': 40,
                'bg_image': 'vn_bg/bg_bottling_robot.jpg',
                'initial_temperature': 22.0,
                'target_temp_min': 20.0,
                'target_temp_max': 24.0,
                'initial_brix': 7.2,
                'target_brix_min': 7.0,
                'target_brix_max': 7.5,
                'initial_line_speed': 35000,
                'initial_purity': 95,
                'initial_balance': 50,
                'description': 'На скорости 35 000 банок в час робот-манипулятор Krones замер из-за перекоса банки. Линия пищит, фуры у ворот ждут! Поправь захват и верни конвейер к жизни.',
                'order': 3
            },
            {
                'slug': 'bot-line-glitch',
                'title': 'Сбой робота-укладчика на конвейере',
                'track': tracks['automation'],
                'target_vacancy': vacancies.get('operator-naladchik-linii-rozliva'),
                'mentor_name': 'Анна',
                'mentor_role': 'Ведущий инженер АСУ ТП и робототехники',
                'mentor_avatar': 'mentor_engineer.jpg',
                'workshop_name': 'Скоростная линия розлива №2',
                'difficulty': 'Специалист',
                'time_limit_sec': 40,
                'bg_image': 'vn_bg/bg_bottling_conveyor.jpg',
                'initial_temperature': 22.0,
                'target_temp_min': 20.0,
                'target_temp_max': 24.0,
                'initial_brix': 7.2,
                'target_brix_min': 7.0,
                'target_brix_max': 7.5,
                'initial_line_speed': 34000,
                'initial_purity': 95,
                'initial_balance': 50,
                'description': 'Оптический датчик зафиксировал перекос упаковки на скоростном конвейере налива. Перехвати управление и восстанови темп потока.',
                'order': 4
            },
            {
                'slug': 'okroshka-detective',
                'title': 'Окрошечный детектив: Квас против Кефира',
                'track': tracks['lab'],
                'target_vacancy': vacancies.get('inzhener-himik-laboratoriya'),
                'mentor_name': 'Елена',
                'mentor_role': 'Руководитель лаборатории микробиологии',
                'mentor_avatar': 'mentor_lab.jpg',
                'workshop_name': 'Лаборатория экспресс-анализа качества',
                'difficulty': 'Стажёр',
                'time_limit_sec': 45,
                'bg_image': 'vn_bg/bg_laboratory_titration.jpg',
                'initial_temperature': 24.5,
                'target_temp_min': 24.0,
                'target_temp_max': 25.5,
                'initial_brix': 7.4,
                'target_brix_min': 7.0,
                'target_brix_max': 7.6,
                'initial_line_speed': 25000,
                'initial_purity': 99,
                'initial_balance': 85,
                'description': 'В лаборатории спор века: стажёр принёс кефир на обед! Докажи превосходство резкого белого кваса с хреном через титрование кислотности и спаси канон.',
                'order': 5
            },
            {
                'slug': 'warehouse-drift',
                'title': 'Форсаж на электрокаре: Пик отгрузки',
                'track': tracks['logistics'],
                'target_vacancy': vacancies.get('menedzher-skladskoj-logistiki-wms'),
                'mentor_name': 'Роман',
                'mentor_role': 'Диспетчер логистического комплекса WMS',
                'mentor_avatar': 'mentor_logistics.jpg',
                'workshop_name': 'Интеллектуальный логистический хаб WMS',
                'difficulty': 'Драйвер смены',
                'time_limit_sec': 35,
                'bg_image': 'vn_bg/bg_warehouse.png',
                'initial_temperature': 20.0,
                'target_temp_min': 18.0,
                'target_temp_max': 22.0,
                'initial_brix': 7.2,
                'target_brix_min': 7.0,
                'target_brix_max': 7.5,
                'initial_line_speed': 32000,
                'initial_purity': 96,
                'initial_balance': 70,
                'description': 'У ворот 40 фур ждут квас и CoolCola в 30-градусную жару. Оформи ТТН и доставь паллету напитков к рампе на электрокаре без дрифта на поворотах!',
                'order': 6
            },
            {
                'slug': 'secret-drop-1978',
                'title': 'Секретный дроп 1978: Рецепт Олимпиады',
                'track': tracks['marketing'],
                'target_vacancy': vacancies.get('trejd-marketolog-napitkov'),
                'mentor_name': 'Артём',
                'mentor_role': 'Бренд-стратег молодежных напитков',
                'mentor_avatar': 'mentor_marketing.jpg',
                'workshop_name': 'Инновационный R&D центр и дегустационный зал',
                'difficulty': 'Креатор',
                'time_limit_sec': 45,
                'bg_image': 'vn_bg/bg_rnd_tasting.jpg',
                'initial_temperature': 22.0,
                'target_temp_min': 20.0,
                'target_temp_max': 24.0,
                'initial_brix': 7.5,
                'target_brix_min': 7.2,
                'target_brix_max': 7.8,
                'initial_line_speed': 30000,
                'initial_purity': 98,
                'initial_balance': 90,
                'description': 'Ищем архивный рецепт 1978 года к Олимпиаде-80 для запуска вирусного молодёжного дропа кваса и натуральной колы в ретро-банке.',
                'order': 7
            }
        ]

        scenarios = {}
        for sd in scenarios_data:
            sc, _ = GameScenario.objects.update_or_create(slug=sd['slug'], defaults=sd)
            scenarios[sd['slug']] = sc

        self.stdout.write(f"Создано/обновлено игровых сценариев: {len(scenarios)}")

        # 4. ДИАЛОГОВЫЕ ГРАФЫ СЦЕНАРИЕВ
        # Общая функция заполнения брожения для brew-yeast-flex и brew-double-fermentation
        for b_slug in ['brew-yeast-flex', 'brew-double-fermentation']:
            sc_brew = scenarios.get(b_slug)
            if sc_brew:
                ScenarioNode.objects.filter(scenario=sc_brew).delete()

                nb_start = ScenarioNode.objects.create(
                    scenario=sc_brew,
                    node_id='start',
                    speaker_name='Михалыч',
                    speaker_role='Главный технолог-квасовар',
                    speaker_mood='concerned',
                    dialogue_text='Здорово, стажёр! В цеху жара +30°C, дрожжи в седьмом танке поймали вайб и устроили дикий рейв! Температура уже 28.5°C, если не охладим рубашку — сусло сбежит прямо в Москву-реку! Что делаем первым делом?',
                    narrative_context='Датчик ЦКТ №7: Температура 28.5°C (критическая зона выше 27°C). Контур рубашки охлаждения закрыт.'
                )

                nb_cooling = ScenarioNode.objects.create(
                    scenario=sc_brew,
                    node_id='cooling_opened',
                    speaker_name='Михалыч',
                    speaker_role='Главный технолог-квасовар',
                    speaker_mood='happy',
                    dialogue_text='Красавчик! Ледяной гликоль пошёл по рубашке танка, температура плавно съехала на комфортные 25.5°C. Дрожжи успокоились, пора внести чистую закваску 1978 для фирменного вкуса. Действуй!',
                    narrative_context='Датчики ЦКТ: Температура 25.5°C (норма). Плотность затора 8.0 °Brix. Закваска готова к внесению.'
                )

                nb_success = ScenarioNode.objects.create(
                    scenario=sc_brew,
                    node_id='success_shift',
                    speaker_name='Михалыч',
                    speaker_role='Главный технолог-квасовар',
                    speaker_mood='impressed',
                    dialogue_text='Вот это работа, вот это хватка! Закваска 1978 внесена, пена стойкая, рубиновый цвет играет, аромат ржаной корочки! Смену закрываем с отличием, пишу рекомендацию на оплачиваемую практику в Очаково!',
                    narrative_context='Партия кваса (300 тонн) спасена. Золотой стандарт качества Очаково подтвержден.',
                    is_terminal=True,
                    is_success=True,
                    final_verdict='Смена успешно завершена: своевременное охлаждение и баланс закваски спасли партию.'
                )

                nb_fail = ScenarioNode.objects.create(
                    scenario=sc_brew,
                    node_id='fail_spoiled',
                    speaker_name='Михалыч',
                    speaker_role='Главный технолог-квасовар',
                    speaker_mood='critical',
                    dialogue_text='Эх, зазевались... Температура перевалила за 31°C, закваска погибла, сусло закисло! Ничего, это учебный тренажёр: жми рестарт и охлаждай рубашку сразу!',
                    narrative_context='Перегрев сусла. Регламент нарушен.',
                    is_terminal=True,
                    is_success=False,
                    final_verdict='Срыв регламента брожения из-за промедления с охлаждением.'
                )

                ScenarioChoice.objects.create(
                    node=nb_start,
                    choice_text='Открыть клапан охлаждения гликолем (-3°C)',
                    tactical_hint='Плавное охлаждение опустит температуру до идеальных 25.5°C',
                    equipment_code='valve_cooling',
                    next_node_id='cooling_opened',
                    score_delta=30,
                    temp_delta=-3.0,
                    brix_delta=-0.3,
                    mentor_quick_reaction='Отличная реакция, гликоль пошёл в контур!',
                    order=1
                )
                ScenarioChoice.objects.create(
                    node=nb_start,
                    choice_text='Спросить совет Михалыча',
                    tactical_hint='Михалыч подскажет открыть клапан охлаждения',
                    equipment_code='intercom_radio',
                    next_node_id='cooling_opened',
                    score_delta=15,
                    temp_delta=-2.5,
                    brix_delta=-0.2,
                    mentor_quick_reaction='Совет прост: охлаждай рубашку, пока дрожжи не закипели!',
                    order=2
                )
                ScenarioChoice.objects.create(
                    node=nb_start,
                    choice_text='Подождать полчаса и посмотреть, что будет',
                    tactical_hint='В жару промедление погубит закваску',
                    equipment_code='',
                    next_node_id='fail_spoiled',
                    score_delta=-35,
                    temp_delta=3.5,
                    mentor_quick_reaction='Ждать нельзя, сусло греется!',
                    order=3
                )

                ScenarioChoice.objects.create(
                    node=nb_cooling,
                    choice_text='Внести дозатором закваску «Очаково 1978» и снять пробу',
                    tactical_hint='Внесение штамма дрожжей и лактобактерий завершит брожение',
                    equipment_code='starter_culture',
                    next_node_id='success_shift',
                    score_delta=35,
                    temp_delta=-0.2,
                    brix_delta=-0.5,
                    mentor_quick_reaction='В десяточку! Закваска легла идеально!',
                    order=1
                )

        # Сценарий: Роботы Krones в тильте
        for r_slug in ['krones-robot-tilt', 'bot-line-glitch']:
            sc_rob = scenarios.get(r_slug)
            if sc_rob:
                ScenarioNode.objects.filter(scenario=sc_rob).delete()

                nr_start = ScenarioNode.objects.create(
                    scenario=sc_rob,
                    node_id='start',
                    speaker_name='Анна',
                    speaker_role='Ведущий инженер АСУ ТП и робототехники',
                    speaker_mood='concerned',
                    dialogue_text='Стажёр, тревога на конвейере! Робот Krones на упаковке банок CoolCola словил тильт: одна банка встала на ребро, и оптический датчик заблокировал ход. Скорость упала с 35 000 до нуля, фуры на погрузке сигналят! Спасай смену!',
                    narrative_context='Линия упаковки №2: Конвейер остановлен фотоэлементом B4.'
                )

                nr_success = ScenarioNode.objects.create(
                    scenario=sc_rob,
                    node_id='success_shift',
                    speaker_name='Анна',
                    speaker_role='Ведущий инженер АСУ ТП и робототехники',
                    speaker_mood='happy',
                    dialogue_text='Виртуозно! Банку-бунтаря поправили, сдули соринку с датчика и запустили конвейер. Линия с визгом радости полетела на 35 000 банок в час! Роботы Krones уважают стажёров с прямыми руками!',
                    narrative_context='Конвейер разогнан на полную мощность. Задержка ликвидирована.',
                    is_terminal=True,
                    is_success=True,
                    final_verdict='Быстрое и безопасное устранение затора спасло план выпуска смены.'
                )

                ScenarioChoice.objects.create(
                    node=nr_start,
                    choice_text='Аккуратно поправить банку на направляющей конвейера',
                    tactical_hint='Простое действие освободит ход и датчик',
                    equipment_code='',
                    next_node_id='success_shift',
                    score_delta=35,
                    line_speed_delta=35000,
                    mentor_quick_reaction='Точно в яблочко! Банка на месте!',
                    order=1
                )
                ScenarioChoice.objects.create(
                    node=nr_start,
                    choice_text='Продуть фотодатчик Krones сжатым воздухом и нажать рестарт',
                    tactical_hint='Сброс оптической ошибки снимет блокировку',
                    equipment_code='cip_wash',
                    next_node_id='success_shift',
                    score_delta=30,
                    line_speed_delta=35000,
                    mentor_quick_reaction='Датчик чист, автоматика поехала!',
                    order=2
                )
                ScenarioChoice.objects.create(
                    node=nr_start,
                    choice_text='Нажать аварийный стоп и вызвать главного инженера',
                    tactical_hint='Безопасно, но вызывает задержку',
                    equipment_code='emergency_stop',
                    next_node_id='success_shift',
                    score_delta=20,
                    line_speed_delta=20000,
                    mentor_quick_reaction='Осторожность одобряю, линию запустили!',
                    order=3
                )

        # Сценарий: Окрошечный детектив (Квас против Кефира)
        sc_okr = scenarios.get('okroshka-detective')
        if sc_okr:
            ScenarioNode.objects.filter(scenario=sc_okr).delete()

            no_start = ScenarioNode.objects.create(
                scenario=sc_okr,
                node_id='start',
                speaker_name='Елена',
                speaker_role='Руководитель лаборатории качества',
                speaker_mood='concerned',
                dialogue_text='Внимание, детектив в заводской столовой! Практикант принёс пакет кефира и пытается накормить бригаду квасоваров! Срочно проводим органолептическую пробу настоящего резкого белого кваса с хреном и доказываем, что квас — это база!',
                narrative_context='Лаборатория сенсорного анализа: образцы белого кваса с хреном на столе.'
            )

            no_success = ScenarioNode.objects.create(
                scenario=sc_okr,
                node_id='success_shift',
                speaker_name='Елена',
                speaker_role='Руководитель лаборатории качества',
                speaker_mood='happy',
                dialogue_text='Безоговорочная победа канона! Органолептика показала 10 баллов из 10: ядрёный, освежающий, с тонким ароматом хрена и ржаного солода. Вся смена аплодирует стоя, кефир отправлен в отставку!',
                narrative_context='Кулинарный спор закрыт в пользу традиций Очаково.',
                is_terminal=True,
                is_success=True,
                final_verdict='Экспертная органолептическая проба подтвердила лидерство кваса Очаково.'
            )

            ScenarioChoice.objects.create(
                node=no_start,
                choice_text='Снять органолептическую пробу белого кваса с хреном',
                tactical_hint='Живой вкус и аромат убедят любого спорщика',
                equipment_code='tasting_mug',
                next_node_id='success_shift',
                score_delta=35,
                purity_delta=5,
                mentor_quick_reaction='Вот это вкус! Никакой кефир рядом не стоял!',
                order=1
            )
            ScenarioChoice.objects.create(
                node=no_start,
                choice_text='Замерить кислотность и свежесть на pH-метре',
                tactical_hint='Научное доказательство идеального баланса',
                equipment_code='ph_meter',
                next_node_id='success_shift',
                score_delta=30,
                purity_delta=5,
                mentor_quick_reaction='Приборы подтверждают: ГОСТ совершенен!',
                order=2
            )

        # Сценарий: Форсаж на электрокаре
        sc_drift = scenarios.get('warehouse-drift')
        if sc_drift:
            ScenarioNode.objects.filter(scenario=sc_drift).delete()

            nd_start = ScenarioNode.objects.create(
                scenario=sc_drift,
                node_id='start',
                speaker_name='Роман',
                speaker_role='Диспетчер логистического комплекса WMS',
                speaker_mood='concerned',
                dialogue_text='На часах 13:00, у рампы 40 фур ждут партию кваса и CoolCola на жаре! Садись на электрокар, твоя задача — доставить паллету до рампы №14 без заносов и потерь. Погнали!',
                narrative_context='Склад готовой продукции класса А. Паллета 600 кг.'
            )

            nd_success = ScenarioNode.objects.create(
                scenario=sc_drift,
                node_id='success_shift',
                speaker_name='Роман',
                speaker_role='Диспетчер логистического комплекса WMS',
                speaker_mood='happy',
                dialogue_text='Мастерское вождение! Паллета доставлена плавно, штрихкод пробит терминалом WMS за 3 секунды, фура уже выезжает на МКАД. В сезон такие водители на вес золота!',
                narrative_context='Отгрузка выполнена с опережением графика.',
                is_terminal=True,
                is_success=True,
                final_verdict='Идеальная складская логистика и аккуратность сохранили груз.'
            )

            ScenarioChoice.objects.create(
                node=nd_start,
                choice_text='Плавно набрать ход электрокара по ровной колее до рампы',
                tactical_hint='Плавный ход гарантирует устойчивость паллеты',
                equipment_code='',
                next_node_id='success_shift',
                score_delta=35,
                line_speed_delta=3000,
                mentor_quick_reaction='Красиво идёшь, паллета как влитая!',
                order=1
            )
            ScenarioChoice.objects.create(
                node=nd_start,
                choice_text='Проверить стретч-пленку и отсканировать штрихкод в WMS',
                tactical_hint='Контроль фиксации исключит падение банок',
                equipment_code='',
                next_node_id='success_shift',
                score_delta=30,
                line_speed_delta=2000,
                mentor_quick_reaction='Педантичность в логистике — залог успеха!',
                order=2
            )

        # Сценарий: Секретный дроп 1978
        sc_drop = scenarios.get('secret-drop-1978')
        if sc_drop:
            ScenarioNode.objects.filter(scenario=sc_drop).delete()

            ns_start = ScenarioNode.objects.create(
                scenario=sc_drop,
                node_id='start',
                speaker_name='Артём',
                speaker_role='Бренд-стратег молодежных напитков',
                speaker_mood='concerned',
                dialogue_text='Привет! К летнему сезону мы готовим лимитированный дроп кваса в ретро-банке. Ищем в архивах комбината рецепт напитков Олимпиады-80. Что выберем для основы рецепта?',
                narrative_context='Архив комбината: картотека рецептур 1978-1980 гг.'
            )

            ns_success = ScenarioNode.objects.create(
                scenario=sc_drop,
                node_id='success_shift',
                speaker_name='Артём',
                speaker_role='Бренд-стратег молодежных напитков',
                speaker_mood='happy',
                dialogue_text='Бинго! Золотая пропорция томлёного ржаного солода найдена! Запускаем дроп, снимаем танцующую банку кваса для соцсетей — этот релиз станет главным трендом лета!',
                narrative_context='Концепт ретро-дропа утвержден к серийному выпуску.',
                is_terminal=True,
                is_success=True,
                final_verdict='Творческий подход и уважение к истории бренда создали хит сезона.'
            )

            ScenarioChoice.objects.create(
                node=ns_start,
                choice_text='Открыть архивный журнал 1978 года с томлёным ржаным солодом',
                tactical_hint='Аутентичный рецепт Олимпиады-80 — стопроцентный хит',
                equipment_code='',
                next_node_id='success_shift',
                score_delta=35,
                mentor_quick_reaction='То что надо, ретро-канон возвращается!',
                order=1
            )
            ScenarioChoice.objects.create(
                node=ns_start,
                choice_text='Запустить вирусный челлендж с танцующей банкой кваса',
                tactical_hint='Молодежный тренд обеспечит миллионы просмотров',
                equipment_code='',
                next_node_id='success_shift',
                score_delta=30,
                mentor_quick_reaction='Трек качает, банка танцует — летим в топ!',
                order=2
            )

        # 5. ИСТОРИЧЕСКИЕ ВЕХИ
        milestones_data = [
            {
                'year': '1978',
                'badge': 'Рождение легенды',
                'title': 'Строительство Московского комбината к Олимпиаде-80',
                'description': 'Комбинат строился по специальному правительственному решению для обеспечения гостей и участников московских Олимпийских игр безалкогольными напитками высочайшего качества.',
                'icon_name': 'flag',
                'order': 1
            },
            {
                'year': '1980',
                'badge': 'Олимпийский старт',
                'title': 'Первая продукция для гостей со всего мира',
                'description': 'Выпуск знаменитого пива «Столичное», легендарных лимонадов и натуральных квасов. Безупречное качество напитков стало визитной карточкой столицы.',
                'icon_name': 'award',
                'order': 2
            },
            {
                'year': '1994',
                'badge': 'Революция кваса',
                'title': 'Возрождение классического двойного брожения',
                'description': 'Технологи Очаково первыми в современной России возродили старинную технологию одновременного дрожжевого и молочнокислого брожения в промышленном масштабе.',
                'icon_name': 'sparkles',
                'order': 3
            },
            {
                'year': '2000-е',
                'badge': 'Федеральный масштаб',
                'title': 'Открытие мега-заводов в регионах России',
                'description': 'Запуск суперсовременных филиалов в Краснодаре, Пензе и Тюмени. Собственные солодовни в Липецкой и Воронежской областях с чистейшим зерном.',
                'icon_name': 'globe',
                'order': 4
            },
            {
                'year': '2022',
                'badge': 'Импортозамещение',
                'title': 'Триумф молодежных линеек CoolCola, Fancy, Street',
                'description': 'В рекордные сроки Очаково разработало и запустило отечественные напитки на натуральных эфирных маслах и соках, завоевавшие доверие десятков миллионов потребителей.',
                'icon_name': 'zap',
                'order': 5
            },
            {
                'year': '2026',
                'badge': 'Индустрия 4.0',
                'title': 'Сезон высоких технологий и оплачиваемой практики',
                'description': 'Внедрение машинного зрения, роботов-манипуляторов и масштабная программа привлечения студентов и выпускников на оплачиваемые стажировки.',
                'icon_name': 'cpu',
                'order': 6
            }
        ]

        for md in milestones_data:
            StoryMilestone.objects.update_or_create(year=md['year'], defaults=md)

        # 6. ПРЕИМУЩЕСТВА РАБОТОДАТЕЛЯ
        perks_data = [
            {
                'title': 'Оплата с первого дня и оформление по ТК РФ',
                'short_desc': 'Никаких неоплачиваемых стажировок: официальный трудовой договор, стаж в трудовую книжку и белая заработная плата 2 раза в месяц.',
                'icon_name': 'file-check',
                'tag': 'Стабильность',
                'order': 1
            },
            {
                'title': 'Бесплатное общежитие в Москве',
                'short_desc': 'Для студентов из регионов и других городов предоставляется комфортное общежитие компании в шаговой доступности от завода.',
                'icon_name': 'home',
                'tag': 'Жильё',
                'order': 2
            },
            {
                'title': 'Компенсация горячего питания',
                'short_desc': 'Вкусные сытные комплексные обеды в собственной корпоративной столовой комбината с существенной скидкой от компании.',
                'icon_name': 'utensils',
                'tag': 'Питание',
                'order': 3
            },
            {
                'title': 'Договор и зачет практики в любом ВУЗе',
                'short_desc': 'Подписываем официальные договоры о производственной и преддипломной практике со всеми ведущими университетами и колледжами страны.',
                'icon_name': 'graduation-cap',
                'tag': 'Обучение',
                'order': 4
            },
            {
                'title': 'Личный наставник — мастер завода',
                'short_desc': 'Каждый стажёр работает в паре с опытным бригадиром или ведущим технологом, готовым научить тонкостям профессии с нуля.',
                'icon_name': 'users',
                'tag': 'Наставничество',
                'order': 5
            },
            {
                'title': 'Скидки на продукцию и мероприятия',
                'short_desc': 'Корпоративные скидки в фирменных магазинах, бесплатные экскурсии в музей традиционных напитков и путевки в ведомственные санатории.',
                'icon_name': 'tag',
                'tag': 'Бонусы',
                'order': 6
            }
        ]

        for pd in perks_data:
            CompanyPerk.objects.update_or_create(title=pd['title'], defaults=pd)

        # 6. ОНЛАЙН-СИНХРОНИЗАЦИЯ АКТУАЛЬНЫХ ВАКАНСИЙ С ОФИЦИАЛЬНОГО САЙТА OCHAKOVO.RU
        try:
            self.stdout.write("Проверка и синхронизация официальных вакансий с ochakovo.ru/rabota/...")
            from careers.services.vacancy_crawler import sync_vacancies_to_database
            sync_res = sync_vacancies_to_database(force_refresh=False)
            self.stdout.write(f"Синхронизировано {sync_res['total_fetched']} официальных вакансий с сайта завода.")
        except Exception as e:
            self.stdout.write(f"Офлайн-режим: используются локальные базовые вакансии ({e})")

        
        
        # 6. НАСТРОЙКИ ИИ-НАСТАВНИКА (GigaChat API) ИЗ .ENV
        AIConfig.objects.update_or_create(
            id=1,
            defaults={
                'gigachat_auth_key': 'MDFhMDcyMTUtY2Y2Ni03ZWMyLWJmNDktZTYwMmYxZjgzM2E2OmZjZTBhMGIwLWExZDEtNGMwYi05YmYyLTY2M2E0MGEzMGVmYw==',
                'gigachat_client_id': '01a07215-cf66-7ec2-bf49-e602f1f833a6',
                'gigachat_client_secret': 'fce0a0b0-a1d1-4c0b-9bf2-663a40a30efc',
                'gigachat_scope': 'GIGACHAT_API_PERS',
                'gigachat_model': 'GigaChat-Max',
                'is_active': True,
            }
        )
        self.stdout.write("Настройки ИИ-наставника (GigaChat API) успешно инициализированы.")

        # 7. ИНИЦИАЛИЗАЦИЯ ДЕМОНСТРАЦИОННОЙ СТАТИСТИКИ ПОСЕТИТЕЛЕЙ (Стенды, QR, VK, Сайт)
        if SiteVisitor.objects.count() == 0:
            import uuid
            from django.utils import timezone
            now = timezone.now()
            sample_visitors = [
                {
                    'session_key': 'stand_qr_visitor_01',
                    'ip_address': '195.208.44.12',
                    'device_type': 'mobile',
                    'browser_os': 'Safari (iOS 17.4)',
                    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1',
                    'landing_page': '/?source=stand_qr',
                    'last_page': '/game/krones-robot-tilt/',
                    'referrer': 'https://ochakovo.ru/mosprom2026/qr',
                    'source': 'stand_qr',
                    'vk_name': 'Максим Васильев',
                    'vk_user_id': 'id49201948',
                    'page_views_count': 6,
                    'has_played_game': True,
                    'has_completed_shift': True,
                    'has_applied': True,
                    'last_game_score': 95,
                },
                {
                    'session_key': 'stand_qr_visitor_02',
                    'ip_address': '178.62.190.55',
                    'device_type': 'mobile',
                    'browser_os': 'Chrome (Android 14)',
                    'user_agent': 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 Chrome/122.0.0.0 Mobile Safari/537.36',
                    'landing_page': '/?source=stand_qr',
                    'last_page': '/vacancies/master-tehnolog-proizvodstva/',
                    'referrer': 'https://ochakovo.ru/stand',
                    'source': 'stand_qr',
                    'vk_name': 'Анна Соколова',
                    'vk_user_id': 'id81230491',
                    'page_views_count': 4,
                    'has_played_game': True,
                    'has_completed_shift': True,
                    'has_applied': True,
                    'last_game_score': 100,
                },
                {
                    'session_key': 'vk_candidate_visitor_03',
                    'ip_address': '94.25.174.88',
                    'device_type': 'desktop',
                    'browser_os': 'Яндекс.Браузер (Windows)',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 YaBrowser/24.1.0.0 Safari/537.36',
                    'landing_page': '/auth/vk/login/',
                    'last_page': '/progress/',
                    'referrer': 'https://vk.com/ochakovo_career',
                    'source': 'vk',
                    'vk_name': 'Дмитрий Кузнецов',
                    'vk_user_id': 'id18492011',
                    'page_views_count': 9,
                    'has_played_game': True,
                    'has_completed_shift': True,
                    'has_applied': True,
                    'last_game_score': 90,
                },
                {
                    'session_key': 'direct_desktop_visitor_04',
                    'ip_address': '212.45.12.80',
                    'device_type': 'desktop',
                    'browser_os': 'Chrome (Windows)',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
                    'landing_page': '/',
                    'last_page': '/game/brew-yeast-flex/',
                    'referrer': 'https://yandex.ru/search/',
                    'source': 'site',
                    'vk_name': '',
                    'vk_user_id': '',
                    'page_views_count': 5,
                    'has_played_game': True,
                    'has_completed_shift': False,
                    'has_applied': False,
                    'last_game_score': 65,
                },
                {
                    'session_key': 'mobile_site_visitor_05',
                    'ip_address': '85.140.2.14',
                    'device_type': 'mobile',
                    'browser_os': 'Safari (iOS 16.5)',
                    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1',
                    'landing_page': '/vacancies/',
                    'last_page': '/vacancies/inzhener-avtomatizacii-krones/',
                    'referrer': '',
                    'source': 'site',
                    'vk_name': '',
                    'vk_user_id': '',
                    'page_views_count': 3,
                    'has_played_game': False,
                    'has_completed_shift': False,
                    'has_applied': False,
                    'last_game_score': None,
                },
            ]
            for sv in sample_visitors:
                SiteVisitor.objects.update_or_create(session_key=sv['session_key'], defaults=sv)
            self.stdout.write(f"Инициализирована демонстрационная статистика посетителей ({len(sample_visitors)} записей)")

        self.stdout.write(self.style.SUCCESS("База данных Очаково успешно наполнена всеми необходимыми данными!"))
