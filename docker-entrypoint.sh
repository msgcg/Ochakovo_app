#!/bin/sh
set -e

echo "=== Запуск симулятора «Очаково: Мастерская Вкуса» в Linux-контейнере ==="

# Безопасность: гарантированное отсутствие предустановленных ключей и .env файлов
rm -f /app/.env /app/.env.local /app/.env.production 2>/dev/null || true

# Директива FRESH_DB: принудительный сброс ТОЛЬКО при явном указании FRESH_DB=1 или RESET_DB=1
if [ "$FRESH_DB" = "1" ] || [ "$RESET_DB" = "1" ]; then
    echo "Активирована директива FRESH_DB=1: очистка базы данных и восстановление чистой эталонной БД..."
    rm -f /app/db.sqlite3 /app/db.sqlite3-journal /app/db.sqlite3-wal 2>/dev/null || true
    if [ -f "/app/db.sqlite3.clean" ]; then
        cp /app/db.sqlite3.clean /app/db.sqlite3
        echo "База данных восстановлена из эталонного образа."
    fi
elif [ ! -f "/app/db.sqlite3" ] && [ -f "/app/db.sqlite3.clean" ]; then
    echo "Инициализация базы данных из чистого эталона сборки образа..."
    cp /app/db.sqlite3.clean /app/db.sqlite3
fi

# Применение миграций базы данных
echo "Применение миграций Django..."
python manage.py migrate --noinput

# Проверка наличия данных в базе (если база абсолютно пуста — засеиваем эталонные данные Очаково)
echo "Проверка наличия вакансий, карьерных треков и сценариев Очаково..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ochakovo_project.settings')
django.setup()
from careers.models import Vacancy, GameScenario, InternshipTrack
if not Vacancy.objects.exists() or not GameScenario.objects.exists():
    print('Справочники Очаково пусты. Запуск инициализации сценариев и вакансий...')
    from django.core.management import call_command
    call_command('seed_ochakovo')
    print('Данные успешно инициализированы.')
else:
    print(f'Обнаружено {Vacancy.objects.count()} вакансий, {GameScenario.objects.count()} сценариев и {InternshipTrack.objects.count()} карьерных треков. База готова.')
"

# Диагностика и проверка доступности аппаратного ускорения Vulkan GPU
echo "=== Диагностика среды Vulkan и GPU ==="
if command -v vulkaninfo >/dev/null 2>&1; then
    vulkaninfo --summary 2>/dev/null | grep -E "deviceName|driverVersion|apiVersion" || echo "Vulkan: среда готова, устройство ожидает передачи хост-GPU."
else
    echo "Утилита vulkaninfo не найдена (будет использован автоматический fallback на CPU)."
fi

# Проверка готовности бортового модуля Whisper GGML
if [ -x "/usr/local/bin/whisper-cli" ] || command -v whisper-cli >/dev/null 2>&1; then
    python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ochakovo_project.settings')
django.setup()
from careers.services.whisper_service import WhisperVulkanService
bin_path = WhisperVulkanService.get_bin_path()
model_path = WhisperVulkanService.get_model_path()
avail = WhisperVulkanService.is_available()
mode, fallback = WhisperVulkanService.get_acceleration_config()
print(f'Бортовой модуль Whisper GGML: готов={avail} [бинарник: {bin_path}, модель: {model_path}, режим: {mode}, fallback_cpu: {fallback}]')
"
else
    echo "Бортовой модуль Whisper: автономное распознавание отключено, используется Web Speech API браузера."
fi

# Сборка статических файлов
echo "Сборка статических файлов..."
python manage.py collectstatic --noinput --clear || true

echo "Сервер «Очаково» готов к работе на порту 8000."
exec "$@"
