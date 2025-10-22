#!/bin/bash

# GUI Системы нейросетевых инвестиций
# Скрипт запуска для Linux/macOS

echo ""
echo "========================================"
echo "   GUI СИСТЕМЫ НЕЙРОСЕТЕВЫХ ИНВЕСТИЦИЙ"
echo "========================================"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.8+"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Активация виртуального окружения если есть
if [ -f "venv/bin/activate" ]; then
    echo "🔧 Активация виртуального окружения..."
    source venv/bin/activate
    echo "✅ Виртуальное окружение активировано"
else
    echo "⚠️  Виртуальное окружение не найдено, используем системный Python"
fi

# Установка зависимостей
echo ""
echo "📦 Проверка и установка зависимостей..."

if ! python3 -c "import tkinter, matplotlib, pandas, numpy, loguru, yaml" 2>/dev/null; then
    echo "📥 Установка зависимостей..."
    if [ -f "requirements_gui_minimal.txt" ]; then
        pip install -r requirements_gui_minimal.txt --quiet
    else
        pip install matplotlib pandas numpy loguru pyyaml --quiet
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка установки зависимостей"
        exit 1
    fi
    echo "✅ Зависимости установлены"
else
    echo "✅ Все зависимости уже установлены"
fi

# Запуск GUI
echo ""
echo "🖥️  Запуск графического интерфейса..."
echo "========================================"
echo ""

python3 gui_launcher_new.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Ошибка запуска GUI"
    echo "Проверьте логи выше для диагностики"
    exit 1
fi

echo ""
echo "✅ GUI завершен"
