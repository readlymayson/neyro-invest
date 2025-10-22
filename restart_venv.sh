#!/bin/bash

# Скрипт перезапуска виртуального окружения для Linux/macOS

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Перезапуск виртуального окружения              ║"
echo "║                     Система инвестиций                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Ошибка: Python 3 не найден в системе"
    echo "Установите Python 3.8 или выше"
    exit 1
fi

# Проверка версии Python
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Ошибка: Требуется Python $required_version или выше"
    echo "Текущая версия: $python_version"
    exit 1
fi

echo "✅ Python $python_version найден"
echo

# Запуск Python скрипта
python3 restart_venv.py

# Проверка результата
if [ $? -eq 0 ]; then
    echo
    echo "🎉 Перезапуск завершен успешно!"
    echo
    echo "Теперь можно запустить GUI:"
    echo "  ./run_gui.sh"
    echo "  или"
    echo "  python3 gui_launcher_simple.py"
else
    echo
    echo "❌ Произошли ошибки при перезапуске"
    echo "Проверьте сообщения выше для диагностики"
    exit 1
fi
