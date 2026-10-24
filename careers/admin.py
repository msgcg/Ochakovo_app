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
