#!/usr/bin/env bash
# Очаково: Мастерская вкуса — Запуск для Linux / macOS
set -e

echo "========================================================================"
echo "   ОЧАКОВО: МАСТЕРСКАЯ НАТУРАЛЬНОГО ВКУСА"
echo "   Запуск в пару кликов..."
echo "========================================================================"

if command -v python3 &>/dev/null; then
    python3 run.py
elif command -v python &>/dev/null; then
    python run.py
else
    echo "Python 3 не найден в системе. Установите Python 3."
    exit 1
fi
