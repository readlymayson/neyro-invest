"""
Launcher для веб-интерфейса EFrolovDev-Invest
Запускает FastAPI приложение с веб-GUI
"""

import sys
import os
from pathlib import Path
from loguru import logger
import subprocess
import webbrowser
import time

# Настройка логирования
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    log_dir / "web_launcher.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
)


def check_dependencies():
    """Проверка установленных зависимостей"""
    logger.info("Проверка зависимостей...")
    
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydantic': 'Pydantic',
        'loguru': 'Loguru',
        'yaml': 'PyYAML'
    }
    
    missing_packages = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            logger.debug(f"  + {name} установлен")
        except ImportError:
            logger.warning(f"  - {name} НЕ установлен")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Отсутствуют пакеты: {', '.join(missing_packages)}")
        logger.info("Установите зависимости: pip install -r requirements.txt")
        return False
    
    logger.info("+ Все зависимости установлены")
    return True


def setup_environment():
    """Настройка окружения"""
    logger.info("Настройка окружения...")
    
    # Добавление путей
    root_dir = Path(__file__).parent
    sys.path.insert(0, str(root_dir))
    
    # Проверка переменных окружения
    env_file = root_dir / ".env"
    if env_file.exists():
        logger.info(f"Найден файл окружения: {env_file}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            logger.info("+ Переменные окружения загружены")
        except ImportError:
            logger.warning("python-dotenv не установлен, пропускаем загрузку .env")
    else:
        logger.warning(f"Файл окружения не найден: {env_file}")
    
    # Создание необходимых директорий
    for dir_name in ["logs", "data", "config", "models"]:
        dir_path = root_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        logger.debug(f"  + Директория: {dir_path}")
    
    logger.info("+ Окружение настроено")


def main():
    """Главная функция запуска веб-GUI"""
    print("\n" + "=" * 70)
    print("    EFrolovDev-Invest - Web GUI Launcher")
    print("    Запуск веб-интерфейса")
    print("=" * 70)
    
    logger.info("=" * 70)
    logger.info("Запуск Web GUI Launcher")
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Рабочая директория: {Path.cwd()}")
    logger.info("=" * 70)
    
    try:
        # Проверка зависимостей
        if not check_dependencies():
            print("\n" + "!" * 70)
            print("ОШИБКА: Не все зависимости установлены!")
            print("!" * 70)
            print("\nУстановите зависимости:")
            print("  pip install fastapi uvicorn[standard] pydantic loguru pyyaml")
            print("\nили используйте:")
            print("  pip install -r requirements.txt")
            input("\nНажмите Enter для выхода...")
            return 1
        
        # Настройка окружения
        setup_environment()
        
        # Параметры запуска
        host = os.getenv("WEB_GUI_HOST", "127.0.0.1")
        port = int(os.getenv("WEB_GUI_PORT", "8001"))
        
        print("\n" + "=" * 70)
        print("ЗАПУСК ВЕБ-СЕРВЕРА")
        print("=" * 70)
        print(f"\n  Адрес: http://{host}:{port}")
        print(f"  API Docs: http://{host}:{port}/docs")
        print(f"  Redoc: http://{host}:{port}/redoc")
        print("\n" + "-" * 70)
        print("  Для остановки нажмите Ctrl+C")
        print("=" * 70 + "\n")
        
        logger.info(f"Запуск сервера на {host}:{port}")
        
        # Открытие браузера через 2 секунды
        def open_browser():
            time.sleep(2)
            url = f"http://{host}:{port}"
            logger.info(f"Открытие браузера: {url}")
            webbrowser.open(url)
        
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Запуск uvicorn
        import uvicorn
        from src.gui.web_app import app
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        logger.info("Веб-сервер остановлен")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠ Прервано пользователем (Ctrl+C)")
        logger.warning("Программа прервана пользователем (Ctrl+C)")
        return 130
        
    except Exception as e:
        print("\n" + "!" * 70)
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("!" * 70)
        
        import traceback
        print("\nПодробности ошибки:")
        print(traceback.format_exc())
        
        logger.error("=" * 70)
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error("=" * 70)
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        print("\nЛоги сохранены в: logs/web_launcher.log")
        print("\nДля решения проблемы:")
        print("  1. Проверьте логи: logs/web_launcher.log")
        print("  2. Убедитесь, что все зависимости установлены")
        print("  3. Проверьте структуру проекта")
        print("  4. Обратитесь к документации: docs/gui/quick-start.md")
        
        input("\nНажмите Enter для выхода...")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

