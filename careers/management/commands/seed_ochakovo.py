from django.core.management.base import BaseCommand
from careers.models import (
    InternshipTrack,
    Vacancy,
    GameScenario,
    ScenarioNode,
    ScenarioChoice,
    StoryMilestone,
    CompanyPerk,
)


class Command(BaseCommand):
    help = "Наполняет базу данных реальными вакансиями Очаково, сценариями симулятора и вехами истории"

    def handle(self, *args, **options):
        self.stdout.write("Начало наполнения базы данных Очаково...")

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

        # 2. РЕАЛЬНЫЕ ВАКАНСИИ СЕЗОНА
        vacancies_data = [
            {
                'title': 'Мастер - технолог производства кваса и напитков',
                'slug': 'master-tehnolog-proizvodstva',
                'track': tracks['brewing'],
                'department': 'Бродильно-лагерный цех',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44 (м. Озёрная)',
                'hh_url': 'https://hh.ru/vacancy/107211997',
                'salary_min': 85000,
                'salary_max': 120000,
                'salary_text': 'от 85 000 до 120 000 ₽',
                'experience_level': 'Без опыта / Студенты профильных вузов',
                'schedule': 'Сменный 2/2 (день/ночь)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Приглашаем студентов старших курсов и выпускников пищевых и биотехнологических факультетов на оплачиваемую практику с возможностью трудоустройства на постоянной основе. Вы будете управлять процессами приготовления натурального квасного сусла, контролировать двойное брожение в ЦКТ и работать с чистыми культурами дрожжей.',
                'responsibilities': (
                    'Контроль технологических параметров брожения сусла (температура, плотность Brix, кислотность)\n'
                    'Внесение чистых культур закваски натурального брожения Очаково\n'
                    'Управление клапанами хладоносителя и перекачкой сусла через SCADA\n'
                    'Органолептическая оценка полуфабриката перед передачей на сепарацию и фильтрацию\n'
                    'Ведение производственного журнала смены в электронной системе'
                ),
                'requirements': (
                    'Профильное образование (биотехнология, пищевые производства, бродильные производства) или студенты 3-4 курсов\n'
                    'Понимание биохимии ферментации и санитарно-гигиенических норм\n'
                    'Внимательность к показаниям датчиков и ответственность'
                ),
                'benefits': (
                    'Официальное трудоустройство в штат с первого дня по ТК РФ\n'
                    'Заработная плата 2 раза в месяц без задержек + премии за перевыполнение плана смены\n'
                    'Бесплатное проживание в корпоративном общежитии в Москве рядом с заводом\n'
                    'Компенсация горячего питания в производственной столовой\n'
                    'Индивидуальный наставник — мастер высшей категории на весь период практики\n'
                    'Оформление всех документов и отчетов по практике для университета'
                ),
                'order': 1
            },
            {
                'title': 'Оператор - наладчик на линии розлива Krones',
                'slug': 'operator-naladchik-linii-rozliva',
                'track': tracks['automation'],
                'department': 'Цех розлива и упаковки готовой продукции',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/98465520',
                'salary_min': 80000,
                'salary_max': 110000,
                'salary_text': 'от 80 000 до 110 000 ₽',
                'experience_level': 'Без опыта (обучение на месте)',
                'schedule': 'Сменный 2/2',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Работа на новейших роботизированных немецких линиях розлива Krones и KHS. Идеальный старт для студентов инженерных специальностей, желающих получить практический опыт работы со сложными мехатронными комплексами и промышленной автоматикой.',
                'responsibilities': (
                    'Управление автоматическим триблоком розлива, укупорки и этикетирования\n'
                    'Контроль бесперебойной подачи бутылок, банок и упаковочных материалов\n'
                    'Оперативная переналадка линии при смене формата тары (0.5л, 1л, 1.5л, 2л)\n'
                    'Мониторинг параметров давления углекислого газа и уровня налива\n'
                    'Участие в планово-предупредительном техобслуживании и CIP-мойке'
                ),
                'requirements': (
                    'Технический склад ума, интерес к механике и автоматике\n'
                    'Студенты инженерных, механических, энергетических факультетов\n'
                    'Готовность к активной сменной работе на динамичном конвейере'
                ),
                'benefits': (
                    'Полный социальный пакет и белая зарплата от 80 000 ₽\n'
                    'Обучение на рабочем месте опытными инженерами Krones\n'
                    'Комфортное общежитие в Москве для иногородних практикантов\n'
                    'Бесплатная спецодежда и регулярные медосмотры за счет компании'
                ),
                'order': 2
            },
            {
                'title': 'Инженер-химик / Микробиолог лаборатории качества',
                'slug': 'inzhener-himik-laboratoriya',
                'track': tracks['lab'],
                'department': 'Центральная аналитическая лаборатория ОТК',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/106316381',
                'salary_min': 75000,
                'salary_max': 100000,
                'salary_text': 'от 75 000 до 100 000 ₽',
                'experience_level': 'Студенты химико-биологических направлений',
                'schedule': 'Сменный 2/2 (дневные смены)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Очаково выпускает только 100% натуральные напитки без химических консервантов. Это означает высочайшие требования к чистоте микробиологической среды и постоянный аналитический контроль на каждом этапе — от солода до укупоренной бутылки.',
                'responsibilities': (
                    'Отбор проб сусла, закваски и готовых напитков на всех стадиях производства\n'
                    'Проведение физико-химических экспресс-анализов (плотность, pH, кислотность, CO2)\n'
                    'Микробиологический посев и микроскопия культур дрожжей и лактобактерий\n'
                    'Оформление паспортов качества партий в лабораторной информационной системе LIMS'
                ),
                'requirements': (
                    'Студенты профильных факультетов (химия, биохимия, микробиология, биотехнология)\n'
                    'Навыки работы с лабораторным оборудованием (pH-метры, спектрофотометры, микроскопы)\n'
                    'Аккуратность, педантичность и внимание к чистоте экспериментов'
                ),
                'benefits': (
                    'Уникальный опыт работы в одной из самых оснащенных пищевых лабораторий страны\n'
                    'Возможность сбора реальных практических данных для курсовых и дипломных работ\n'
                    'Официальная оплачиваемая практика с первого дня\n'
                    'Корпоративная столовая и комфортные условия труда'
                ),
                'order': 3
            },
            {
                'title': 'Инженер по автоматизации / Инженер КИПиА',
                'slug': 'inzhener-avtomatizacii-kipia',
                'track': tracks['automation'],
                'department': 'Служба главного прибориста и АСУ ТП',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/107678720',
                'salary_min': 95000,
                'salary_max': 135000,
                'salary_text': 'от 95 000 до 135 000 ₽',
                'experience_level': 'Начальный опыт / Выпускники бакалавриата',
                'schedule': 'График 5/2 или 2/2',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Обслуживание промышленных контроллеров Siemens, датчиков температуры, давления, расходомеров Endress+Hauser и систем диспетчеризации цехов брожения и розлива.',
                'responsibilities': (
                    'Диагностика и наладка контрольно-измерительных приборов и датчиков\n'
                    'Калибровка расходомеров, датчиков давления CO2 и термометров сопротивления\n'
                    'Поиск и устранение сбоев в шкафах управления PLC Siemens S7\n'
                    'Участие в проектах модернизации и цифровизации производственных участков'
                ),
                'requirements': (
                    'Высшее или неоконченное высшее образование (АСУ ТП, мехатроника, электроника, робототехника)\n'
                    'Базовые знания схемотехники, интерфейсов RS-485, Profinet, Modbus\n'
                    'Умение читать электрические схемы и техническую документацию'
                ),
                'benefits': (
                    'Высокая заработная плата от 95 000 ₽ с перспективой роста\n'
                    'Работа со сложнейшим парком современного промышленного оборудования\n'
                    'Проживание в корпоративном общежитии в Москве\n'
                    'ДМС со стоматологией после окончания стажировки'
                ),
                'order': 4
            },
            {
                'title': 'Менеджер по складской логистике WMS',
                'slug': 'menedzher-skladskoj-logistiki-wms',
                'track': tracks['logistics'],
                'department': 'Логистический комплекс готовой продукции',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/106795271',
                'salary_min': 75000,
                'salary_max': 105000,
                'salary_text': 'от 75 000 до 105 000 ₽',
                'experience_level': 'Без опыта / Студенты',
                'schedule': 'Сменный 2/2',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': True,
                'has_meal_compensation': True,
                'description': 'Летний сезон — время пиковой отгрузки: сотни фур ежедневно отправляются во все регионы России. Мы ищем энергичных координаторов в службу складской логистики.',
                'responsibilities': (
                    'Координация работы смены с помощью WMS-системы и терминалов ТСД\n'
                    'Контроль комплектации заказов дистрибьюторов и торговых сетей\n'
                    'Управление потоками погрузчиков на пандусах отгрузки\n'
                    'Оформление товарно-транспортных накладных в 1С:ERP'
                ),
                'requirements': (
                    'Уверенный пользователь ПК, внимательность, собранность\n'
                    'Студенты логистических, экономических или технических специальностей\n'
                    'Умение работать в команде при высоком темпе операций'
                ),
                'benefits': (
                    'Достойный стабильный заработок и премии в сезон пиковой нагрузки\n'
                    'Бесплатное проживание в Москве рядом с работой\n'
                    'Опыт управления крупным распределительным складским хабом'
                ),
                'order': 5
            },
            {
                'title': 'Трейд-маркетолог молодежных линеек напитков',
                'slug': 'trejd-marketolog-napitkov',
                'track': tracks['marketing'],
                'department': 'Департамент маркетинга и развития брендов',
                'city': 'Москва',
                'address': 'ул. Рябиновая, д. 44',
                'hh_url': 'https://hh.ru/vacancy/106723644',
                'salary_min': 90000,
                'salary_max': 130000,
                'salary_text': 'от 90 000 до 130 000 ₽',
                'experience_level': 'Студенты старших курсов / Выпускники',
                'schedule': 'График 5/2 (гибкое начало дня)',
                'is_seasonal_peak': True,
                'is_student_friendly': True,
                'has_dormitory': False,
                'has_meal_compensation': True,
                'description': 'Продвижение безалкогольных хитов CoolCola, Fancy, Street и новых вкусов кваса в летний сезон. Разработка креативных промо-кампаний, работа с фестивалями и инфлюенсерами.',
                'responsibilities': (
                    'Разработка сезонных BTL и трейд-активностей в федеральных сетях\n'
                    'Координация промо-команд на городских мероприятиях и фестивалях Москвы\n'
                    'Анализ динамики продаж категорий и потребительских предпочтений молодёжи\n'
                    'Участие в тестировании новых вкусов и концептов упаковки'
                ),
                'requirements': (
                    'Высшее образование или студенты 4 курса / магистратуры (маркетинг, реклама, PR, менеджмент)\n'
                    'Креативное мышление, понимание молодежных трендов и мемов\n'
                    'Навыки анализа данных и презентации идей'
                ),
                'benefits': (
                    'Работа с культовыми федеральными брендами напитков\n'
                    'Уютный офис, бесплатный кофе и корпоративная столовая\n'
                    'Реальная возможность реализовать собственные смелые рекламные кампании'
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

        # 3. ИГРОВЫЕ СЦЕНАРИИ
        # 3. ИГРОВЫЕ СЦЕНАРИИ (ПРОСТЫЕ, ИГРОВЫЕ, С ЮМОРОМ И МАСКОТАМИ)
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
                'bg_image': 'vn_bg/bg_brewhouse.jpg',
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
                'workshop_name': 'Цех брожения и созревания кваса (ЦКТ №7)',
                'difficulty': 'Стажёр',
                'time_limit_sec': 45,
                'bg_image': 'vn_bg/bg_brewhouse.jpg',
                'initial_temperature': 28.5,
                'target_temp_min': 24.0,
                'target_temp_max': 26.0,
                'initial_brix': 8.4,
                'target_brix_min': 7.0,
                'target_brix_max': 7.6,
                'initial_line_speed': 28000,
                'initial_purity': 92,
                'initial_balance': 45,
                'description': 'Классический инцидент брожения: балансируем терморежим сусла и спасаем партию легендарного напитка.',
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
                'bg_image': 'vn_bg/bg_bottling_line.jpg',
                'initial_temperature': 22.0,
                'target_temp_min': 20.0,
                'target_temp_max': 24.0,
                'initial_brix': 7.2,
                'target_brix_min': 7.0,
                'target_brix_max': 7.5,
                'initial_line_speed': 35000,
                'initial_purity': 95,
                'initial_balance': 50,
                'description': 'На скорости 35 000 банок в час робот-манипулятор замер из-за перекоса одной банки. Линия пищит, фуры у ворот ждут! Поправь банку и верни конвейер к жизни.',
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
                'workshop_name': 'Высокоскоростной цех розлива №2',
                'difficulty': 'Специалист',
                'time_limit_sec': 40,
                'bg_image': 'vn_bg/bg_bottling_line.jpg',
                'initial_temperature': 22.0,
                'target_temp_min': 20.0,
                'target_temp_max': 24.0,
                'initial_brix': 7.2,
                'target_brix_min': 7.0,
                'target_brix_max': 7.5,
                'initial_line_speed': 34000,
                'initial_purity': 95,
                'initial_balance': 50,
                'description': 'Оптический датчик зафиксировал перекос упаковки. Перехвати управление и восстанови темп.',
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
                'workshop_name': 'Лаборатория качества и дегустационный зал',
                'difficulty': 'Стажёр',
                'time_limit_sec': 45,
                'bg_image': 'vn_bg/bg_laboratory.jpg',
                'initial_temperature': 24.5,
                'target_temp_min': 24.0,
                'target_temp_max': 25.5,
                'initial_brix': 7.4,
                'target_brix_min': 7.0,
                'target_brix_max': 7.6,
                'initial_line_speed': 25000,
                'initial_purity': 99,
                'initial_balance': 85,
                'description': 'В столовой завода спор века: стажёр принёс кефир на обед! Докажи превосходство резкого белого кваса с хреном через органолептическую пробу и спаси гастрономический канон.',
                'order': 5
            },
            {
                'slug': 'warehouse-drift',
                'title': 'Форсаж на электрокаре: Пик отгрузки',
                'track': tracks['logistics'],
                'target_vacancy': vacancies.get('trejd-marketolog-napitkov'),
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
                'description': 'У ворот 40 фур ждут квас в 30-градусную жару. Доставь паллету напитков к рампе на электрокаре быстро, аккуратно и без дрифта на поворотах!',
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
                'workshop_name': 'Креативный хаб и музей Очаково',
                'difficulty': 'Креатор',
                'time_limit_sec': 45,
                'bg_image': 'vn_bg/bg_rnd_lab.jpg',
                'initial_temperature': 22.0,
                'target_temp_min': 20.0,
                'target_temp_max': 24.0,
                'initial_brix': 7.5,
                'target_brix_min': 7.2,
                'target_brix_max': 7.8,
                'initial_line_speed': 30000,
                'initial_purity': 98,
                'initial_balance': 90,
                'description': 'Ищем архивный рецепт 1978 года к Олимпиаде-80 для запуска вирусного молодёжного дропа кваса в ретро-банке.',
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

        self.stdout.write(self.style.SUCCESS("База данных Очаково успешно наполнена всеми необходимыми данными!"))
