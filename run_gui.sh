#!/bin/bash

# Скрипт запуска GUI для системы нейросетевых инвестиций

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Нейросетевая система инвестиций                 ║"
echo "║                     Запуск GUI                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python 3 не найден в системе"
    echo "Установите Python 3.8 или выше"
    exit 1
fi

# Проверка версии Python
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Ошибка: Требуется Python $required_version или выше"
    echo "Текущая версия: $python_version"
    exit 1
fi

# Создание виртуального окружения если не существует
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "Проверка и установка зависимостей..."
if ! pip install -r requirements_gui_minimal.txt --quiet; then
    echo "Попытка установки с основным файлом зависимостей..."
    pip install -r requirements_gui.txt --quiet
fi

# Запуск GUI приложения
echo
echo "Запуск графического интерфейса..."
echo
python3 gui_launcher.py

# Деактивация виртуального окружения
deactivate

echo
echo "Приложение завершено."
