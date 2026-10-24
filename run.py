#!/usr/bin/env python3
"""
ОЧАКОВО: МАСТЕРСКАЯ НАТУРАЛЬНОГО ВКУСА
Универсальный скрипт автозапуска «в пару кликов» карьерной платформы АО МПБК «Очаково».
"""

import os
import sys
import shutil
import subprocess
import webbrowser
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

BANNER = r"""
========================================================================
   ____   _____  _    _          _  __  ____   __      __ ____
  / __ \ / ____|| |  | |   /\   | |/ / / __ \  \ \    / // __ \
 | |  | || |     | |__| |  /  \  | ' / | |  | |  \ \  / /| |  | |
 | |  | || |     |  __  | / /\ \ |  <  | |  | |   \ \/ / | |  | |
 | |__| || |____ | |  | |/ ____ \| . \ | |__| |    \  /  | |__| |
  \____/  \_____||_|  |_/_/    \_|_|\_\ \____/      \/    \____/

   КАРЬЕРНАЯ PWA-ПЛАТФОРМА И СИМУЛЯТОР СМЕНЫ АО МПБК «ОЧАКОВО» 2026
========================================================================
"""

def main():
    print(BANNER)
    print(">>> Проверка и запуск приложения «Очаково»...")

    # 1. Проверяем наличие .env
    env_file = BASE_DIR / ".env"
    env_example = BASE_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        print(">>> Создание локального конфигурационного файла .env из .env.example...")
        shutil.copy(env_example, env_file)

    # 2. Определение интерпретатора Python в виртуальном окружении
    venv_dir = BASE_DIR / ".venv"
    if sys.platform == "win32":
        python_bin = venv_dir / "Scripts" / "python.exe"
    else:
        python_bin = venv_dir / "bin" / "python"

    if not python_bin.exists():
        print(">>> Виртуальное окружение не найдено. Создаём .venv...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        print(">>> Установка зависимостей в .venv...")
        subprocess.check_call([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([str(python_bin), "-m", "pip", "install", "-r", str(BASE_DIR / "requirements.txt")])
    else:
        print(f">>> Используется виртуальное окружение: {venv_dir}")

    # 3. Выполнение миграций базы данных
    print(">>> Применение миграций базы данных...")
    subprocess.check_call([str(python_bin), "manage.py", "migrate"])

    # 4. Наполнение базы данных реальными вакансиями Очаково и сценариями
    print(">>> Наполнение базы данных актуальными вакансиями сезона и сценариями...")
    subprocess.check_call([str(python_bin), "manage.py", "seed_ochakovo"])

    # 5. Сбор статических файлов
    print(">>> Сборка статических файлов для WhiteNoise...")
    subprocess.check_call([str(python_bin), "manage.py", "collectstatic", "--noinput"])

    # 6. Открытие браузера через 1.5 секунды
    url = "http://127.0.0.1:8080/"
    print(f"\n========================================================================")
    print(f"  ГОТОВО! Приложение запускается по адресу: {url}")
    print(f"  Браузер откроется автоматически через секунду.")
    print(f"  Для остановки нажмите Ctrl + C в этом окне.")
    print(f"========================================================================\n")

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # 7. Запуск Django Development Server
    subprocess.call([str(python_bin), "manage.py", "runserver", "127.0.0.1:8080"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n>>> Сервер остановлен пользователем.")
        sys.exit(0)
