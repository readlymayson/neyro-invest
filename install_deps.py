#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для установки зависимостей проекта нейро-инвестиций
"""

import subprocess
import sys
import os

# Установка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def run_command(command):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {command}")
            return True
        else:
            print(f"✗ {command}")
            print(f"  Ошибка: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {command}")
        print(f"  Исключение: {e}")
        return False

def main():
    print("=" * 60)
    print("УСТАНОВКА ЗАВИСИМОСТЕЙ ДЛЯ ПРОЕКТА НЕЙРО-ИНВЕСТИЦИЙ")
    print("=" * 60)
    print()
    
    # Проверяем версию Python
    print(f"Python версия: {sys.version}")
    print()
    
    # Обновляем pip
    print("Обновление pip...")
    run_command("python -m pip install --upgrade pip")
    print()
    
    # Основные зависимости
    print("Установка основных зависимостей...")
    basic_deps = [
        "numpy>=1.21.0",
        "pandas>=1.3.0", 
        "scikit-learn>=1.0.0",
        "xgboost>=1.5.0"
    ]
    
    for dep in basic_deps:
        run_command(f"python -m pip install {dep}")
    print()
    
    # Зависимости для работы с данными
    print("Установка зависимостей для работы с данными...")
    data_deps = [
        "yfinance>=0.1.70",
        "requests>=2.27.0",
        "beautifulsoup4>=4.10.0",
        "lxml>=4.6.0"
    ]
    
    for dep in data_deps:
        run_command(f"python -m pip install {dep}")
    print()
    
    # Конфигурация
    print("Установка зависимостей для конфигурации...")
    config_deps = [
        "pyyaml>=6.0",
        "python-dotenv>=0.19.0"
    ]
    
    for dep in config_deps:
        run_command(f"python -m pip install {dep}")
    print()
    
    # Логирование и визуализация
    print("Установка зависимостей для логирования и визуализации...")
    viz_deps = [
        "loguru>=0.6.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0"
    ]
    
    for dep in viz_deps:
        run_command(f"python -m pip install {dep}")
    print()
    
    # База данных
    print("Установка зависимостей для базы данных...")
    run_command("python -m pip install sqlalchemy>=1.4.0")
    print()
    
    # Утилиты
    print("Установка утилит...")
    util_deps = [
        "schedule>=1.1.0",
        "python-dateutil>=2.8.0",
        "pytz>=2021.3"
    ]
    
    for dep in util_deps:
        run_command(f"python -m pip install {dep}")
    print()
    
    print("=" * 60)
    print("УСТАНОВКА ЗАВЕРШЕНА!")
    print("=" * 60)
    print()
    print("Примечания:")
    print("- PyTorch не установлен автоматически")
    print("- Для установки PyTorch: https://pytorch.org/get-started/locally/")
    print("- TA-Lib может потребовать Microsoft Visual C++ Build Tools")
    print()

if __name__ == "__main__":
    main()

