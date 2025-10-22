#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "    🚀 NEYRO-INVEST WEB GUI"
echo "    Запуск веб-интерфейса"
echo "============================================================"
echo

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python не найден!${NC}"
    echo
    echo "Установите Python 3.11+ с https://www.python.org/"
    exit 1
fi

# Активация виртуального окружения если есть
if [ -f "venv/bin/activate" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
fi

# Запуск веб-GUI
echo
echo "Запуск веб-сервера..."
echo
python3 web_launcher.py

