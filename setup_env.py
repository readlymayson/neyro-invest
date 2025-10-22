#!/usr/bin/env python3
"""
Скрипт для настройки переменных окружения из .env файла
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """
    Настройка переменных окружения
    """
    print("=" * 60)
    print("НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
    print("=" * 60)
    
    # Пути к файлам
    env_example = Path("environment.env")
    env_file = Path(".env")
    
    # Проверяем наличие файла-примера
    if not env_example.exists():
        print("ОШИБКА: Файл environment.env не найден!")
        return False
    
    # Копируем файл-пример в .env если его нет
    if not env_file.exists():
        try:
            shutil.copy2(env_example, env_file)
            print(f"СОЗДАН файл .env из {env_example}")
        except Exception as e:
            print(f"ОШИБКА создания .env файла: {e}")
            return False
    else:
        print("Файл .env уже существует")
    
    # Показываем содержимое .env файла
    print("\nСодержимое .env файла:")
    print("-" * 40)
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"ОШИБКА чтения .env файла: {e}")
        return False
    
    print("\nИНСТРУКЦИИ:")
    print("1. Откройте файл .env в текстовом редакторе")
    print("2. Замените 'your_deepseek_api_key_here' на ваш реальный API ключ DeepSeek")
    print("3. Замените 'your_tinkoff_token_here' на ваш реальный токен Tinkoff")
    print("4. Сохраните файл")
    print("\nПолучить API ключи:")
    print("- DeepSeek: https://platform.deepseek.com/")
    print("- Tinkoff Invest: https://www.tinkoff.ru/invest/settings/api/")
    
    return True

if __name__ == "__main__":
    setup_environment()
