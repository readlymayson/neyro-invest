#!/usr/bin/env python3
"""
Новый запускатор GUI для системы нейросетевых инвестиций
Отдельный интерфейс для визуализации и управления
"""

import sys
import os
import subprocess
from pathlib import Path
from loguru import logger

def check_dependencies():
    """Проверка зависимостей для GUI"""
    required_packages = [
        'tkinter',
        'matplotlib', 
        'pandas',
        'numpy',
        'loguru',
        'pyyaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'matplotlib':
                import matplotlib
            elif package == 'pandas':
                import pandas
            elif package == 'numpy':
                import numpy
            elif package == 'loguru':
                import loguru
            elif package == 'pyyaml':
                import yaml
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Отсутствуют следующие зависимости:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nУстановите их командой:")
        print("pip install matplotlib pandas numpy loguru pyyaml")
        return False
    
    return True

def setup_environment():
    """Настройка окружения"""
    # Загрузка переменных окружения
    try:
        from dotenv import load_dotenv
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv(env_path)
            print("✅ Переменные окружения загружены из .env")
        else:
            print("⚠️  Файл .env не найден")
    except ImportError:
        print("⚠️  python-dotenv не установлен")

def main():
    """Главная функция запуска GUI"""
    print("=" * 60)
    print("🚀 ЗАПУСК GUI СИСТЕМЫ НЕЙРОСЕТЕВЫХ ИНВЕСТИЦИЙ")
    print("=" * 60)
    print()
    
    # Проверка зависимостей
    print("🔍 Проверка зависимостей...")
    if not check_dependencies():
        print("\n❌ Не все зависимости установлены!")
        print("Запустите: pip install -r requirements_gui_minimal.txt")
        input("\nНажмите Enter для выхода...")
        return 1
    
    print("✅ Все зависимости установлены")
    
    # Настройка окружения
    print("\n🔧 Настройка окружения...")
    setup_environment()
    
    # Запуск GUI
    print("\n🖥️  Запуск графического интерфейса...")
    print("=" * 60)
    
    try:
        # Добавление пути к модулям
        root_dir = Path(__file__).parent
        sys.path.append(str(root_dir))
        
        # Импорт и запуск GUI
        from src.gui.main_app import main as gui_main
        gui_main()
        
    except Exception as e:
        print(f"❌ Ошибка запуска GUI: {e}")
        logger.error(f"Ошибка запуска GUI: {e}")
        input("\nНажмите Enter для выхода...")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
