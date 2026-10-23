from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('game/', views.game_select_view, name='game_select'),
    path('game/<slug:scenario_slug>/', views.game_play_view, name='game_play'),
    
    # API endpoints
    path('api/game/action/', views.game_action_api, name='game_action_api'),
    path('api/game/credentials/', views.game_credentials_api, name='game_credentials_api'),
    path('api/game/tts/', views.game_tts_api, name='game_tts_api'),
    path('api/game/stt/', views.game_stt_api, name='game_stt_api'),
    path('api/candidate/apply/', views.apply_candidate_api, name='apply_candidate_api'),
    path('api/candidate/progress/', views.candidate_progress_api, name='candidate_progress_api'),
    path('api/vacancies/search/', views.vacancies_search_api, name='vacancies_search_api'),
    path('api/vacancies/sync/', views.vacancies_sync_api, name='vacancies_sync_api'),
    
    # Vacancies, Progress & Story
    path('progress/', views.candidate_progress_view, name='progress'),
    path('vacancies/', views.vacancies_list_view, name='vacancies_list'),
    path('vacancies/<slug:slug>/', views.vacancy_detail_view, name='vacancy_detail'),
    path('story/', views.story_view, name='story'),
    
    # PWA service files
    path('offline/', views.offline_view, name='offline'),
    path('manifest.json', views.manifest_view, name='manifest'),
    path('sw.js', views.service_worker_view, name='service_worker'),
]
