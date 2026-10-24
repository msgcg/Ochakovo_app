from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.http import HttpResponse
import csv
from datetime import datetime
from .models import (
    AIConfig,
    InternshipTrack,
    Vacancy,
    GameScenario,
    ScenarioNode,
    ScenarioChoice,
    GameSession,
    JobApplication,
    StoryMilestone,
    CompanyPerk,
    SiteVisitor,
)

# Настройка заголовков панели администратора на русском языке
admin.site.site_header = "АО МПБК «Очаково» — Управление Карьерой и Симулятором"
admin.site.site_title = "Очаково HR Воронка"
admin.site.index_title = "Панель управления соискателями, практикой и игровыми сменами"


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    """
    Полноценное меню информации о кандидатах, соискателях со стендов и выпускниках:
    отображает ФИО, контакты, соцсети (VK), общий скор (XP), рекомендованную должность и статус.
    """
    list_display = (
        'candidate_name',
        'contact_links',
        'score_badge',
        'recommended_position',
        'funnel_source',
        'status_badge',
        'created_at_fmt',
    )
    list_filter = ('status', 'source', 'target_track', 'created_at')
    search_fields = ('full_name', 'phone', 'email', 'telegram', 'university', 'study_field', 'vk_url')
    readonly_fields = ('created_at', 'game_session')
    ordering = ('-created_at',)
    list_per_page = 25

    fieldsets = (
        ("👤 Личные данные соискателя", {
            "fields": (
                "full_name",
                ("phone", "telegram", "email"),
                "vk_url",
                ("university", "study_field", "course_or_status"),
            )
        }),
        ("🎯 Карьерные успехи и скоринг", {
            "fields": (
                ("game_score", "cumulative_score"),
                ("recommended_role", "internship_reduction"),
                "target_track",
                "target_vacancy",
                "completed_cases",
                "game_session",
            )
        }),
        ("📋 Статус заявки и источник", {
            "fields": (
                ("status", "source"),
                "hh_response_url",
                "cover_letter",
                "created_at",
            )
        }),
    )

    actions = [
        'approve_practice_action',
        'invite_interview_action',
        'move_to_screening_action',
        'export_as_csv_action'
    ]

    @admin.display(description="Кандидат / ВУЗ")
    def candidate_name(self, obj):
        uni = obj.university or "ВУЗ не указан"
        return format_html(
            '<div style="font-weight: 800; font-size: 0.95rem; color: #0F172A;">{}</div>'
            '<div style="font-size: 0.78rem; color: #64748B;">{}</div>',
            obj.full_name,
            uni
        )

    @admin.display(description="Контакты / VK")
    def contact_links(self, obj):
        links = []
        if obj.phone:
            links.append(f'<span style="font-weight:700;">📞 {obj.phone}</span>')
        if obj.telegram:
            tg = obj.telegram.lstrip('@')
            links.append(f'<a href="https://t.me/{tg}" target="_blank" style="color:#0284C7; font-weight:700;">✈️ @{tg}</a>')
        if obj.vk_url:
            vk_display = obj.vk_url.replace("https://vk.com/", "@")
            links.append(f'<a href="{obj.vk_url}" target="_blank" style="color:#0077FF; font-weight:700;">🌐 {vk_display}</a>')
        elif obj.email:
            links.append(f'<span style="color:#64748B;">✉️ {obj.email}</span>')
        return mark_safe("<br>".join(links)) if links else "—"

    @admin.display(description="Скор (XP)", ordering='cumulative_score')
    def score_badge(self, obj):
        score = obj.cumulative_score or obj.game_score or 50
        if score >= 200:
            bg, color, label = "#DCFCE7", "#166534", "Высший разряд"
        elif score >= 100:
            bg, color, label = "#E0F2FE", "#0369A1", "2-й разряд"
        else:
            bg, color, label = "#FEF3C7", "#92400E", "Стажёр"
        
        return format_html(
            '<div style="background:{}; color:{}; border:1.5px solid #1E293B; border-radius:8px; padding:3px 8px; text-align:center; font-weight:900; display:inline-block;">'
            '{} XP<div style="font-size:0.68rem; font-weight:800;">{}</div>'
            '</div>',
            bg, color, score, label
        )

    @admin.display(description="Рекомендация должности")
    def recommended_position(self, obj):
        role = obj.recommended_role or (obj.target_vacancy.title if obj.target_vacancy else "Мастер цеха")
        bonus = obj.internship_reduction or "Сокращение стажировки -50%"
        return format_html(
            '<div style="font-weight:800; color:#0F172A; font-size:0.85rem;">{}</div>'
            '<span style="background:#FEF9C3; color:#854D0E; font-size:0.7rem; font-weight:800; padding:1px 6px; border-radius:4px; border:1px solid #CA8A04;">{}</span>',
            role, bonus
        )

    @admin.display(description="Источник")
    def funnel_source(self, obj):
        mapping = {
            'stand_qr': ('#FEF3C7', '#B45309', '📱 Стенд / QR'),
            'vk': ('#EFF6FF', '#1D4ED8', '🌐 ВКонтакте'),
            'simulator': ('#F0FDF4', '#15803D', '🎮 Симулятор цеха'),
            'site': ('#F1F5F9', '#334155', '💻 Сайт практики'),
        }
        bg, color, text = mapping.get(obj.source, ('#F1F5F9', '#334155', obj.source or 'Сайт'))
        return format_html(
            '<span style="background:{}; color:{}; font-weight:800; font-size:0.75rem; padding:3px 8px; border-radius:6px; border:1px solid #CBD5E1;">{}</span>',
            bg, color, text
        )

    @admin.display(description="Статус отклика", ordering='status')
    def status_badge(self, obj):
        status_map = {
            'new': ('#FEF3C7', '#92400E', '🟡 Новая заявка'),
            'screening': ('#E0F2FE', '#0369A1', '🔵 Рассмотрение HR'),
            'interview': ('#F3E8FF', '#6B21A8', '🟣 Собеседование'),
            'practice_approved': ('#DCFCE7', '#15803D', '🟢 Практика одобрена'),
        }
        bg, color, label = status_map.get(obj.status, ('#F1F5F9', '#334155', obj.status))
        return format_html(
            '<span style="background:{}; color:{}; font-weight:900; font-size:0.75rem; padding:4px 8px; border-radius:6px; border:1.5px solid #1E293B;">{}</span>',
            bg, color, label
        )

    @admin.display(description="Дата подачи", ordering='created_at')
    def created_at_fmt(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    @admin.action(description="🟢 Одобрить на оплачиваемую практику (сокращение срока на 50%%)")
    def approve_practice_action(self, request, queryset):
        updated = queryset.update(status='practice_approved', internship_reduction='Сокращение стажировки на 50%')
        self.message_user(request, f"Одобрено кандидатов на практику: {updated}. Сформированы персональные офферы.")

    @admin.action(description="🟣 Пригласить на собеседование на завод «Очаково»")
    def invite_interview_action(self, request, queryset):
        updated = queryset.update(status='interview')
        self.message_user(request, f"Назначено собеседование для кандидатов: {updated}.")

    @admin.action(description="🔵 Перевести на рассмотрение HR")
    def move_to_screening_action(self, request, queryset):
        updated = queryset.update(status='screening')
        self.message_user(request, f"Переведено на рассмотрение: {updated}.")

    @admin.action(description="📥 Выгрузить список соискателей в CSV для HR")
    def export_as_csv_action(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="ochakovo_candidates_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
        response.write('﻿')  # BOM для правильного открытия в Excel на русском
        writer = csv.writer(response)
        writer.writerow(['ФИО', 'Телефон', 'Email', 'Telegram', 'VK Ссылка', 'ВУЗ', 'Специальность', 'Баллы (XP)', 'Рекомендованная должность', 'Бонус', 'Источник', 'Статус', 'Дата'])
        for app in queryset:
            writer.writerow([
                app.full_name,
                app.phone,
                app.email,
                app.telegram,
                app.vk_url,
                app.university,
                app.study_field,
                app.cumulative_score or app.game_score,
                app.recommended_role,
                app.internship_reduction,
                app.source,
                app.get_status_display(),
                app.created_at.strftime("%d.%m.%Y %H:%M")
            ])
        return response


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """
    Игровые смены симулятора: отображение прогресса кандидата, телеметрии датчиков и решений
    """
    list_display = ('scenario_title', 'score_pill', 'telemetry_hud', 'status_badge', 'turns_count', 'created_at_fmt')
    list_filter = ('status', 'scenario', 'created_at')
    readonly_fields = ('session_uuid', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    @admin.display(description="Цех / Сценарий")
    def scenario_title(self, obj):
        return format_html(
            '<div style="font-weight:800; color:#0F172A;">{}</div>'
            '<div style="font-size:0.75rem; color:#64748B;">Наставник: {}</div>',
            obj.scenario.title,
            obj.scenario.mentor_name
        )

    @admin.display(description="Очки смены")
    def score_pill(self, obj):
        color = "#16A34A" if obj.score >= 80 else ("#D97706" if obj.score >= 50 else "#DC2626")
        return format_html(
            '<span style="font-weight:900; font-size:0.95rem; color:{};">{} XP</span>',
            color, obj.score
        )

    @admin.display(description="Телеметрия цеха")
    def telemetry_hud(self, obj):
        return format_html(
            '<span style="font-size:0.8rem; font-weight:700;">🌡️ {}°C &nbsp;|&nbsp; 🍯 {}°Bx &nbsp;|&nbsp; ⚡ {} б/ч</span>',
            obj.temperature, obj.brix, obj.line_speed
        )

    @admin.display(description="Статус")
    def status_badge(self, obj):
        colors = {
            'completed': ('#DCFCE7', '#166534', 'Партия спасена'),
            'active': ('#FEF3C7', '#92400E', 'В процессе смены'),
            'failed': ('#FEE2E2', '#991B1B', 'Срыв смены'),
        }
        bg, color, text = colors.get(obj.status, ('#F1F5F9', '#334155', obj.status))
        return format_html(
            '<span style="background:{}; color:{}; font-weight:800; padding:3px 8px; border-radius:6px; border:1px solid #CBD5E1;">{}</span>',
            bg, color, text
        )

    @admin.display(description="Дата")
    def created_at_fmt(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'department', 'salary_text', 'is_seasonal_peak', 'is_student_friendly', 'is_active')
    list_filter = ('city', 'department', 'is_seasonal_peak', 'is_student_friendly', 'is_active')
    search_fields = ('title', 'description', 'requirements')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(InternshipTrack)
class InternshipTrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'mentor_name', 'accent_color', 'order')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'mentor_name')


class ScenarioChoiceInline(admin.TabularInline):
    model = ScenarioChoice
    extra = 1


@admin.register(ScenarioNode)
class ScenarioNodeAdmin(admin.ModelAdmin):
    list_display = ('scenario', 'node_id', 'speaker_name', 'speaker_mood', 'is_terminal', 'is_success')
    list_filter = ('scenario', 'speaker_mood', 'is_terminal', 'is_success')
    search_fields = ('node_id', 'dialogue_text', 'narrative_context')
    inlines = [ScenarioChoiceInline]


@admin.register(GameScenario)
class GameScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', 'track', 'difficulty', 'mentor_name', 'initial_temperature', 'initial_brix', 'order')
    list_filter = ('track', 'difficulty')
    search_fields = ('title', 'mentor_name', 'description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(StoryMilestone)
class StoryMilestoneAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'badge', 'order')
    ordering = ('order',)


@admin.register(CompanyPerk)
class CompanyPerkAdmin(admin.ModelAdmin):
    list_display = ('title', 'tag', 'order')
    ordering = ('order',)


@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'gigachat_model', 'gigachat_scope', 'is_active', 'updated_at')
    fieldsets = (
        ('Настройка нейросети GigaChat', {
            'description': 'Единый корпоративный ключ API Salute / GigaChat. Настраивается владельцем платформы.',
            'fields': ('is_active', 'gigachat_auth_key', 'gigachat_client_id', 'gigachat_client_secret', 'gigachat_model', 'gigachat_scope')
        }),
    )

    def has_add_permission(self, request):
        return AIConfig.objects.count() == 0


@admin.register(SiteVisitor)
class SiteVisitorAdmin(admin.ModelAdmin):
    """
    Журнал активности и статистика всех пользователей, заходивших на сайт Очаково:
    типы устройств, каналы переходов (стенды/QR, VK ID, сайт), глубина просмотра,
    результаты в симуляторе и статус конверсии в соискатели.
    """
    change_list_template = "admin/careers/sitevisitor/change_list.html"

    list_display = (
        'visitor_identity',
        'device_badge',
        'source_badge',
        'activity_badge',
        'conversion_status',
        'entry_and_last_page',
        'first_visit_fmt',
        'last_visit_fmt',
    )
    list_filter = (
        'source',
        'device_type',
        'has_played_game',
        'has_completed_shift',
        'has_applied',
        'last_visit',
        'first_visit',
    )
    search_fields = (
        'session_key',
        'vk_name',
        'vk_user_id',
        'ip_address',
        'landing_page',
        'last_page',
        'user_agent',
    )
    readonly_fields = (
        'session_key',
        'ip_address',
        'device_type',
        'browser_os',
        'user_agent',
        'landing_page',
        'last_page',
        'referrer',
        'source',
        'vk_user_id',
        'vk_name',
        'page_views_count',
        'has_played_game',
        'has_completed_shift',
        'has_applied',
        'last_game_score',
        'first_visit',
        'last_visit',
    )
    ordering = ('-last_visit',)
    list_per_page = 30
    actions = ['export_as_csv_action']

    @admin.display(description="Пользователь / Устройство")
    def visitor_identity(self, obj):
        if obj.vk_name:
            return format_html(
                '<div style="font-weight: 800; font-size: 0.92rem; color: #0F172A;">🌐 {}</div>'
                '<div style="font-size: 0.74rem; color: #0284C7; font-weight: 700;">VK ID: {} &nbsp;|&nbsp; {}</div>',
                obj.vk_name,
                obj.vk_user_id or '—',
                obj.browser_os or 'Браузер'
            )
        return format_html(
            '<div style="font-weight: 800; font-size: 0.92rem; color: #0F172A;">👤 Гость <span style="font-family: monospace; font-size: 0.8rem; background: #E2E8F0; padding: 1px 5px; border-radius: 4px;">{}</span></div>'
            '<div style="font-size: 0.74rem; color: #64748B;">IP: {} &nbsp;|&nbsp; {}</div>',
            obj.session_key[:8] if obj.session_key else 'anon',
            obj.ip_address or 'локально',
            obj.browser_os or 'Браузер'
        )

    @admin.display(description="Устройство", ordering='device_type')
    def device_badge(self, obj):
        mapping = {
            'mobile': ('#E0F2FE', '#0369A1', '📱 Смартфон'),
            'desktop': ('#F1F5F9', '#334155', '🖥️ ПК / Ноутбук'),
            'tablet': ('#F3E8FF', '#6B21A8', '📟 Планшет'),
            'bot': ('#FEE2E2', '#991B1B', '🤖 Бот'),
        }
        bg, color, text = mapping.get(obj.device_type, ('#F1F5F9', '#334155', obj.device_type))
        return format_html(
            '<span style="background:{}; color:{}; font-weight:800; font-size:0.75rem; padding:3px 8px; border-radius:6px; border:1px solid #CBD5E1; white-space:nowrap;">{}</span>',
            bg, color, text
        )

    @admin.display(description="Канал входа", ordering='source')
    def source_badge(self, obj):
        mapping = {
            'stand_qr': ('#FEF3C7', '#B45309', '📱 Стенд / QR-код'),
            'vk': ('#EFF6FF', '#1D4ED8', '🌐 ВКонтакте'),
            'site': ('#F8FAFC', '#0F172A', '💻 Сайт практики'),
            'hh': ('#FEE2E2', '#DC2626', '💼 HeadHunter'),
            'simulator': ('#DCFCE7', '#15803D', '🎮 Симулятор цеха'),
        }
        bg, color, text = mapping.get(obj.source, ('#F1F5F9', '#334155', obj.get_source_display()))
        return format_html(
            '<span style="background:{}; color:{}; font-weight:800; font-size:0.75rem; padding:3px 8px; border-radius:6px; border:1.5px solid #1E293B; white-space:nowrap;">{}</span>',
            bg, color, text
        )

    @admin.display(description="Активность на сайте")
    def activity_badge(self, obj):
        items = []
        items.append(f'<span style="font-weight:700; color:#475569;">👁️ {obj.page_views_count} просм.</span>')
        if obj.has_played_game:
            score_txt = f"{obj.last_game_score} XP" if obj.last_game_score is not None else "в цеху"
            if obj.has_completed_shift:
                items.append(f'<span style="background:#DCFCE7; color:#15803D; font-weight:800; font-size:0.72rem; padding:2px 6px; border-radius:4px; border:1px solid #86EFAC;">🏆 Смена: {score_txt}</span>')
            else:
                items.append(f'<span style="background:#FEF3C7; color:#92400E; font-weight:800; font-size:0.72rem; padding:2px 6px; border-radius:4px; border:1px solid #FDE68A;">🎮 Играл: {score_txt}</span>')
        return mark_safe(" &nbsp;".join(items))

    @admin.display(description="Статус воронки", ordering='has_applied')
    def conversion_status(self, obj):
        if obj.has_applied:
            bg, color, border, label = '#DCFCE7', '#166534', '#16A34A', '🟢 Заявка подана'
        elif obj.has_completed_shift:
            bg, color, border, label = '#FEF9C3', '#854D0E', '#EAB308', '🟡 Смена защищена'
        elif obj.has_played_game:
            bg, color, border, label = '#E0F2FE', '#0369A1', '#7DD3FC', '🔵 Играл в цеху'
        else:
            bg, color, border, label = '#F1F5F9', '#64748B', '#CBD5E1', '⚪ Знакомился с сайтом'

        return format_html(
            '<span style="background:{}; color:{}; border:1.5px solid {}; font-weight:800; font-size:0.75rem; padding:3px 8px; border-radius:6px; white-space:nowrap;">{}</span>',
            bg, color, border, label
        )

    @admin.display(description="Вход → Последняя страница")
    def entry_and_last_page(self, obj):
        return format_html(
            '<div style="font-size:0.78rem; color:#475569;"><span style="color:#64748B;">Вход:</span> <b>{}</b></div>'
            '<div style="font-size:0.78rem; color:#0F172A;"><span style="color:#64748B;">Сейчас:</span> <b>{}</b></div>',
            obj.landing_page[:28],
            obj.last_page[:28]
        )

    @admin.display(description="Первый визит", ordering='first_visit')
    def first_visit_fmt(self, obj):
        return obj.first_visit.strftime("%d.%m.%Y %H:%M")

    @admin.display(description="Последняя активность", ordering='last_visit')
    def last_visit_fmt(self, obj):
        return obj.last_visit.strftime("%d.%m.%Y %H:%M")

    @admin.action(description="📥 Выгрузить выбранных посетителей в CSV")
    def export_as_csv_action(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="ochakovo_selected_visitors_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
        response.write('﻿')
        writer = csv.writer(response)
        writer.writerow([
            'ID Сессии', 'Пользователь / VK', 'ID VK', 'Устройство', 'Браузер и ОС',
            'IP-адрес', 'Канал входа', 'Страница входа', 'Последняя страница',
            'Просмотров', 'Запуск симулятора', 'Успех смены', 'Баллы (XP)', 'Подал заявку',
            'Первый визит', 'Последняя активность'
        ])
        for v in queryset:
            writer.writerow([
                v.session_key,
                v.vk_name or 'Гость',
                v.vk_user_id,
                v.get_device_type_display(),
                v.browser_os,
                v.ip_address,
                v.get_source_display(),
                v.landing_page,
                v.last_page,
                v.page_views_count,
                'Да' if v.has_played_game else 'Нет',
                'Да' if v.has_completed_shift else 'Нет',
                v.last_game_score if v.last_game_score is not None else '—',
                'Да' if v.has_applied else 'Нет',
                v.first_visit.strftime('%d.%m.%Y %H:%M'),
                v.last_visit.strftime('%d.%m.%Y %H:%M'),
            ])
        return response

