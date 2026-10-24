from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from careers import views as careers_views

urlpatterns = [
    path('admin/analytics/', careers_views.admin_analytics_dashboard_view, name='admin_analytics_dashboard'),
    path('admin/analytics/export-csv/', careers_views.admin_analytics_export_csv, name='admin_analytics_export_csv'),
    path('admin/', admin.site.urls),
    path('', include('careers.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
