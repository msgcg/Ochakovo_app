from django.contrib import admin
from .models import (
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


@admin.register(InternshipTrack)
class InternshipTrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'mentor_name', 'accent_color', 'order')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'mentor_name')


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'department', 'salary_text', 'is_seasonal_peak', 'is_student_friendly', 'is_active')
    list_filter = ('city', 'department', 'is_seasonal_peak', 'is_student_friendly', 'is_active')
    search_fields = ('title', 'description', 'requirements')
    prepopulated_fields = {'slug': ('title',)}


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


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('session_uuid', 'scenario', 'current_node_id', 'score', 'temperature', 'status', 'created_at')
    list_filter = ('status', 'scenario')
    readonly_fields = ('session_uuid', 'created_at', 'updated_at')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'university', 'target_track', 'target_vacancy', 'game_score', 'status', 'created_at')
    list_filter = ('status', 'target_track', 'university')
    search_fields = ('full_name', 'phone', 'email', 'university', 'study_field')
    readonly_fields = ('created_at',)


@admin.register(StoryMilestone)
class StoryMilestoneAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'badge', 'order')
    ordering = ('order',)


@admin.register(CompanyPerk)
class CompanyPerkAdmin(admin.ModelAdmin):
    list_display = ('title', 'tag', 'order')
    ordering = ('order',)
