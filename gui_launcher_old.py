#!/usr/bin/env python3
"""
Launcher для графического интерфейса системы нейросетевых инвестиций
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# Добавление корневой директории проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.gui.main_window import MainWindow
    from loguru import logger
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def check_dependencies():
    """
    Проверка наличия необходимых зависимостей
    
    Returns:
        bool: True если все зависимости установлены
    """
    required_packages = [
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'loguru',
        'yaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'matplotlib':
                import matplotlib
            elif package == 'numpy':
                import numpy
            elif package == 'pandas':
                import pandas
            elif package == 'loguru':
                import loguru
            elif package == 'yaml':
                import yaml
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Отсутствуют следующие зависимости:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nУстановите их командой:")
        print("pip install -r requirements_gui_minimal.txt")
        return False
    
    return True


def setup_logging():
    """
    Настройка логирования для GUI приложения
    """
    try:
        # Создание директории для логов
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Настройка loguru
        logger.remove()  # Удаление стандартного обработчика
        
        # Добавление обработчика для файла
        logger.add(
            logs_dir / "gui_application.log",
            rotation="10 MB",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}",
            encoding="utf-8"
        )
        
        # Добавление обработчика для консоли (только для отладки)
        logger.add(
            sys.stderr,
            level="WARNING",
            format="{time:HH:mm:ss} | {level} | {message}"
        )
        
        logger.info("Логирование настроено")
        
    except Exception as e:
        print(f"Ошибка настройки логирования: {e}")


def check_config_files():
    """
    Проверка наличия файлов конфигурации
    
    Returns:
        bool: True если основные файлы конфигурации найдены
    """
    try:
        config_dir = project_root / "config"
        
        if not config_dir.exists():
            print("Директория config не найдена")
            return False
        
        main_config = config_dir / "main.yaml"
        if not main_config.exists():
            print("Основной файл конфигурации config/main.yaml не найден")
            return False
        
        logger.info("Файлы конфигурации найдены")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка проверки файлов конфигурации: {e}")
        return False


def create_directories():
    """
    Создание необходимых директорий
    """
    try:
        directories = [
            "logs",
            "data",
            "models"
        ]
        
        for dir_name in directories:
            dir_path = project_root / dir_name
            dir_path.mkdir(exist_ok=True)
            logger.debug(f"Директория {dir_name} создана/проверена")
        
        logger.info("Все необходимые директории созданы")
        
    except Exception as e:
        logger.error(f"Ошибка создания директорий: {e}")


def show_startup_info():
    """
    Показ информации о запуске
    """
    startup_info = f"""
╔══════════════════════════════════════════════════════════════╗
║              Нейросетевая система инвестиций                 ║
║                     Версия 1.0.0                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Графический интерфейс для управления системой              ║
║  автоматической торговли с использованием нейронных сетей   ║
║                                                              ║
║  Возможности:                                                ║
║  • Мониторинг портфеля в реальном времени                   ║
║  • Управление торговыми стратегиями                         ║
║  • Настройка нейросетевых моделей                           ║
║  • Анализ рисков и производительности                       ║
║  • Просмотр логов системы                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Запуск приложения...
    """
    
    print(startup_info)
    logger.info("Запуск GUI приложения")


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Обработчик необработанных исключений
    
    Args:
        exc_type: Тип исключения
        exc_value: Значение исключения
        exc_traceback: Трассировка исключения
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Игнорируем KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.error(
        "Необработанное исключение",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Показ сообщения пользователю
    try:
        root = tk.Tk()
        root.withdraw()  # Скрыть главное окно
        
        error_message = f"""
Произошла критическая ошибка в приложении:

{exc_type.__name__}: {exc_value}

Подробности сохранены в файле логов.
Приложение будет закрыто.
        """
        
        messagebox.showerror("Критическая ошибка", error_message)
        root.destroy()
        
    except Exception:
        # Если не удается показать GUI сообщение, выводим в консоль
        print(f"Критическая ошибка: {exc_type.__name__}: {exc_value}")


def main():
    """
    Главная функция запуска приложения
    """
    try:
        # Показ информации о запуске
        show_startup_info()
        
        # Проверка зависимостей
        if not check_dependencies():
            input("Нажмите Enter для выхода...")
            return 1
        
        # Настройка логирования
        setup_logging()
        
        # Установка обработчика исключений
        sys.excepthook = handle_exception
        
        # Создание необходимых директорий
        create_directories()
        
        # Проверка файлов конфигурации
        if not check_config_files():
            logger.warning("Некоторые файлы конфигурации отсутствуют")
            print("Предупреждение: Некоторые файлы конфигурации отсутствуют")
            print("Приложение может работать некорректно")
        
        # Создание и запуск главного окна
        logger.info("Создание главного окна приложения")
        main_window = MainWindow()
        
        logger.info("Запуск главного цикла приложения")
        main_window.run()
        
        logger.info("Приложение завершено")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Приложение прервано пользователем")
        print("\nПриложение прервано пользователем")
        return 0
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        print(f"Критическая ошибка при запуске: {e}")
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Ошибка запуска",
                f"Не удалось запустить приложение:\n\n{e}\n\nПроверьте логи для получения подробной информации."
            )
            root.destroy()
        except Exception:
            pass
        
        return 1


if __name__ == "__main__":
    # Проверка версии Python
    if sys.version_info < (3, 8):
        print("Ошибка: Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        sys.exit(1)
    
    # Запуск приложения
    exit_code = main()
    sys.exit(exit_code)
