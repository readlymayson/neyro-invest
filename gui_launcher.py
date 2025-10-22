#!/usr/bin/env python3
"""
Новый запускатор GUI для системы нейросетевых инвестиций
Отдельный интерфейс для визуализации и управления
"""

import sys
import os
import subprocess
import traceback
from pathlib import Path
from loguru import logger

# Настройка логирования в файл
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logger.add(
    log_dir / "gui_launcher.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
)

def check_dependencies():
    """Проверка зависимостей для GUI"""
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    print("=" * 60)
    
    required_packages = [
        ('tkinter', 'tkinter'),
        ('matplotlib', 'matplotlib'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('loguru', 'loguru'),
        ('pyyaml', 'yaml')
    ]
    
    missing_packages = []
    
    for display_name, import_name in required_packages:
        try:
            print(f"Проверка {display_name}...", end=" ")
            logger.debug(f"Проверка пакета: {display_name}")
            
            if import_name == 'tkinter':
                import tkinter
                print("✓ OK")
                logger.debug(f"✓ {display_name} найден")
            elif import_name == 'matplotlib':
                import matplotlib
                print(f"✓ OK (версия {matplotlib.__version__})")
                logger.debug(f"✓ {display_name} найден: {matplotlib.__version__}")
            elif import_name == 'pandas':
                import pandas
                print(f"✓ OK (версия {pandas.__version__})")
                logger.debug(f"✓ {display_name} найден: {pandas.__version__}")
            elif import_name == 'numpy':
                import numpy
                print(f"✓ OK (версия {numpy.__version__})")
                logger.debug(f"✓ {display_name} найден: {numpy.__version__}")
            elif import_name == 'loguru':
                import loguru
                print("✓ OK")
                logger.debug(f"✓ {display_name} найден")
            elif import_name == 'yaml':
                import yaml
                print("✓ OK")
                logger.debug(f"✓ {display_name} найден")
                
        except ImportError as e:
            print(f"✗ ОТСУТСТВУЕТ")
            logger.error(f"✗ {display_name} не найден: {e}")
            missing_packages.append(display_name)
        except Exception as e:
            print(f"✗ ОШИБКА: {e}")
            logger.error(f"Ошибка при проверке {display_name}: {e}")
            missing_packages.append(display_name)
    
    if missing_packages:
        print("\n" + "!" * 60)
        print("❌ ОТСУТСТВУЮТ СЛЕДУЮЩИЕ ЗАВИСИМОСТИ:")
        print("!" * 60)
        for package in missing_packages:
            print(f"  ✗ {package}")
        print("\nУстановите их командой:")
        print("  pip install matplotlib pandas numpy loguru pyyaml")
        print("\nИли используйте файл requirements:")
        print("  pip install -r requirements.txt")
        logger.error(f"Отсутствуют пакеты: {', '.join(missing_packages)}")
        return False
    
    print("\n✅ ВСЕ ЗАВИСИМОСТИ УСТАНОВЛЕНЫ")
    logger.info("Все зависимости проверены успешно")
    return True

def setup_environment():
    """Настройка окружения"""
    print("\n" + "=" * 60)
    print("НАСТРОЙКА ОКРУЖЕНИЯ")
    print("=" * 60)
    
    logger.info("Начало настройки окружения")
    
    # Загрузка переменных окружения
    try:
        print("Загрузка переменных окружения...", end=" ")
        logger.debug("Попытка загрузки python-dotenv")
        
        from dotenv import load_dotenv
        env_path = Path('.env')
        
        if env_path.exists():
            load_dotenv(env_path)
            print("✓ OK")
            logger.info(f"Переменные окружения загружены из {env_path}")
            
            # Проверка важных переменных
            tinkoff_token = os.getenv('TINKOFF_TOKEN')
            if tinkoff_token:
                print(f"  ✓ TINKOFF_TOKEN найден (длина: {len(tinkoff_token)})")
                logger.debug(f"TINKOFF_TOKEN найден (длина: {len(tinkoff_token)})")
            else:
                print("  ⚠ TINKOFF_TOKEN не найден")
                logger.warning("TINKOFF_TOKEN не найден в переменных окружения")
        else:
            print("⚠ Файл .env не найден")
            logger.warning(f"Файл .env не найден по пути: {env_path.absolute()}")
            
    except ImportError:
        print("⚠ python-dotenv не установлен")
        logger.warning("python-dotenv не установлен, пропускаем загрузку .env")
    except Exception as e:
        print(f"✗ ОШИБКА: {e}")
        logger.error(f"Ошибка при загрузке переменных окружения: {e}")
    
    # Проверка путей
    print("\nПроверка структуры проекта...")
    logger.debug("Проверка структуры директорий")
    
    important_dirs = ['src', 'src/gui', 'config', 'logs', 'data']
    for dir_name in important_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✓ {dir_name}/ найдена")
            logger.debug(f"Директория {dir_name} существует")
        else:
            print(f"  ✗ {dir_name}/ НЕ НАЙДЕНА")
            logger.warning(f"Директория {dir_name} не найдена")
            
            # Создание недостающих директорий
            if dir_name in ['logs', 'data']:
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"    → Создана директория {dir_name}/")
                    logger.info(f"Создана директория {dir_name}")
                except Exception as e:
                    print(f"    → Ошибка создания: {e}")
                    logger.error(f"Ошибка создания директории {dir_name}: {e}")
    
    # Проверка GUI модулей
    print("\nПроверка модулей GUI...")
    logger.debug("Проверка наличия GUI модулей")
    
    gui_modules = [
        'src/gui/__init__.py',
        'src/gui/main_app.py',
        'src/gui/main_window.py'
    ]
    
    for module in gui_modules:
        module_path = Path(module)
        if module_path.exists():
            print(f"  ✓ {module}")
            logger.debug(f"Модуль {module} найден")
        else:
            print(f"  ✗ {module} НЕ НАЙДЕН")
            logger.error(f"Модуль {module} не найден")
    
    print("\n✅ ОКРУЖЕНИЕ НАСТРОЕНО")
    logger.info("Настройка окружения завершена")

def main():
    """Главная функция запуска GUI"""
    print("\n" + "=" * 60)
    print("    NEYRO-INVEST - GUI LAUNCHER")
    print("    Запуск графического интерфейса")
    print("=" * 60)
    
    logger.info("=" * 60)
    logger.info("Запуск GUI launcher")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Рабочая директория: {Path.cwd()}")
    logger.info("=" * 60)
    
    try:
        # Проверка зависимостей
        if not check_dependencies():
            print("\n" + "!" * 60)
            print("❌ ОШИБКА: Не все зависимости установлены!")
            print("!" * 60)
            logger.error("Запуск прерван: отсутствуют зависимости")
            input("\nНажмите Enter для выхода...")
            return 1
        
        # Настройка окружения
        setup_environment()
        
        # Запуск GUI
        print("\n" + "=" * 60)
        print("ЗАПУСК ГРАФИЧЕСКОГО ИНТЕРФЕЙСА")
        print("=" * 60)
        logger.info("Начало запуска GUI приложения")
        
        # Добавление пути к модулям
        root_dir = Path(__file__).parent
        sys.path.insert(0, str(root_dir))
        
        print(f"\nДобавлен путь к модулям: {root_dir}")
        logger.info(f"Добавлен путь: {root_dir}")
        
        # Проверка импорта модулей
        print("\nИмпорт модулей GUI...")
        logger.debug("Попытка импорта src.gui.main_window")
        
        try:
            from src.gui.main_window import MainWindow
            print("  ✓ src.gui.main_window импортирован")
            logger.info("MainWindow импортирован успешно")
        except ImportError as e:
            print(f"  ✗ Ошибка импорта main_window: {e}")
            logger.error(f"Ошибка импорта MainWindow: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Пробуем альтернативный импорт
            print("\nПопытка альтернативного импорта (main_app)...")
            logger.debug("Попытка импорта src.gui.main_app")
            
            try:
                from src.gui.main_app import main as gui_main
                print("  ✓ src.gui.main_app импортирован")
                logger.info("main_app импортирован успешно")
                
                print("\nЗапуск GUI (main_app)...")
                logger.info("Запуск GUI через main_app")
                gui_main()
                return 0
                
            except ImportError as e2:
                print(f"  ✗ Ошибка импорта main_app: {e2}")
                logger.error(f"Ошибка импорта main_app: {e2}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
        
        # Запуск основного GUI через MainWindow
        print("\nИнициализация главного окна...")
        logger.info("Создание экземпляра MainWindow")
        
        try:
            window = MainWindow()
            print("✓ Главное окно создано")
            logger.info("MainWindow создан успешно")
            
            print("\nЗапуск главного цикла приложения...")
            print("=" * 60)
            logger.info("Запуск mainloop")
            
            window.run()
            
            print("\n" + "=" * 60)
            print("GUI ЗАКРЫТ")
            print("=" * 60)
            logger.info("GUI завершил работу нормально")
            
        except Exception as e:
            print(f"\n✗ Ошибка при создании/запуске MainWindow: {e}")
            logger.error(f"Ошибка при создании/запуске MainWindow: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
    except KeyboardInterrupt:
        print("\n\n⚠ Прервано пользователем (Ctrl+C)")
        logger.warning("Программа прервана пользователем (Ctrl+C)")
        return 130
        
    except Exception as e:
        print("\n" + "!" * 60)
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("!" * 60)
        print("\nПодробности ошибки:")
        print(traceback.format_exc())
        
        logger.error("=" * 60)
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error("=" * 60)
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        print("\nЛоги сохранены в: logs/gui_launcher.log")
        print("\nДля решения проблемы:")
        print("  1. Проверьте логи: logs/gui_launcher.log")
        print("  2. Убедитесь, что все зависимости установлены")
        print("  3. Проверьте структуру проекта")
        print("  4. Обратитесь к документации: docs/gui/quick-start.md")
        
        input("\nНажмите Enter для выхода...")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        logger.info(f"Программа завершена с кодом: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Необработанное исключение: {e}")
        logger.critical(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
