#!/usr/bin/env python3
"""
Главный файл запуска системы нейросетевых инвестиций
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger

# Настройка кодировки для Windows
if sys.platform == "win32":
    import codecs
    import io
    # Создаем новые потоки с правильной кодировкой
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Добавление корневой директории в путь
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

# Загрузка переменных окружения из .env файла
try:
    from dotenv import load_dotenv
    env_path = root_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Переменные окружения загружены из {env_path}")
    else:
        print("Файл .env не найден, используются системные переменные окружения")
except ImportError:
    print("python-dotenv не установлен, используются только системные переменные окружения")

from src.core.investment_system import InvestmentSystem
from src.utils.config_selector import ConfigSelector


def setup_logging(config_path: str = "config/main.yaml"):
    """
    Настройка логирования
    """
    try:
        # Создание директории логов
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Удаление старых обработчиков
        logger.remove()
        
        # Настройка консольного вывода
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # Настройка файлового вывода
        logger.add(
            logs_dir / "investment_system.log",
            rotation="1 day",
            retention="30 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            encoding="utf-8"
        )
        
        # Настройка отдельных логов для компонентов
        logger.add(
            logs_dir / "trading.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "trading" in record["name"].lower(),
            encoding="utf-8"
        )
        
        logger.add(
            logs_dir / "neural_networks.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "neural" in record["name"].lower(),
            encoding="utf-8"
        )
        
        logger.info("Логирование настроено")
        
    except Exception as e:
        print(f"Ошибка настройки логирования: {e}")


def check_environment():
    """
    Проверка окружения
    """
    logger.info("Проверка окружения...")
    
    # Проверка Python версии
    if sys.version_info < (3, 8):
        logger.error("Требуется Python 3.8 или выше")
        return False
    
    # Проверка необходимых директорий
    required_dirs = ["logs", "models", "data", "config"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Создана директория: {dir_name}")
    
    # Проверка конфигурации
    config_path = Path("config/main.yaml")
    if not config_path.exists():
        logger.error(f"Файл конфигурации не найден: {config_path}")
        logger.info("Скопируйте пример конфигурации: cp config/examples/beginners.yaml config/main.yaml")
        return False
    
    # Проверка переменных окружения
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_key:
        logger.warning("Переменная DEEPSEEK_API_KEY не установлена")
        logger.info("Установите API ключ: set DEEPSEEK_API_KEY=your_key (Windows) или export DEEPSEEK_API_KEY=your_key (Linux/Mac)")
    
    logger.info("Проверка окружения завершена")
    return True


async def run_training_mode(config_path: str):
    """
    Режим обучения моделей
    """
    logger.info("🚀 Запуск в режиме обучения моделей")
    
    try:
        # Инициализация системы
        system = InvestmentSystem(config_path)
        
        # Инициализация компонентов
        await system._initialize_components()
        
        # Обучение моделей
        logger.info("Начало обучения нейросетей...")
        historical_data = await system.data_provider.get_latest_data()
        await system.network_manager.train_models(historical_data)
        
        logger.info("✅ Обучение завершено успешно!")
        
        # Тестирование моделей
        logger.info("Тестирование обученных моделей...")
        test_results = await system.network_manager.analyze(historical_data)
        
        logger.info("Результаты тестирования:")
        ensemble_pred = test_results.get('ensemble_prediction', {})
        logger.info(f"Ансамблевое предсказание: {ensemble_pred}")
        
    except Exception as e:
        logger.error(f"Ошибка в режиме обучения: {e}")
        raise


async def run_trading_mode(config_path: str):
    """
    Режим торговли
    """
    logger.info("💰 Запуск в режиме торговли")
    
    try:
        # Инициализация системы
        system = InvestmentSystem(config_path)
        
        # Запуск торговой системы
        await system.start_trading()
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка в режиме торговли: {e}")
        raise


async def run_backtest_mode(config_path: str, start_date: str, end_date: str):
    """
    Режим бэктестинга
    """
    logger.info("📊 Запуск в режиме бэктестинга")
    
    try:
        from examples.backtesting import BacktestEngine
        
        # Создание движка бэктестинга
        backtest_engine = BacktestEngine(config_path)
        await backtest_engine.initialize()
        
        # Парсинг дат
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Запуск бэктестинга
        await backtest_engine.run_backtest(start_dt, end_dt, train_period_days=365)
        
        logger.info("✅ Бэктестинг завершен!")
        
    except Exception as e:
        logger.error(f"Ошибка в режиме бэктестинга: {e}")
        raise


def show_status():
    """
    Показать статус системы
    """
    try:
        from src.utils.config_manager import ConfigManager
        
        config_manager = ConfigManager("config/main.yaml")
        config = config_manager.get_config()
        
        print("\n" + "="*60)
        print("📈 СТАТУС СИСТЕМЫ НЕЙРОСЕТЕВЫХ ИНВЕСТИЦИЙ")
        print("="*60)
        
        # Информация о конфигурации
        print(f"📊 Символы для торговли: {', '.join(config['data']['symbols'])}")
        print(f"🔄 Интервал обновления: {config['data']['update_interval']} сек")
        print(f"💰 Начальный капитал: {config['portfolio']['initial_capital']:,} руб")
        print(f"📈 Максимум позиций: {config['trading']['max_positions']}")
        print(f"🎯 Порог сигналов: {config['trading']['signal_threshold']}")
        
        # Информация о моделях
        models = config['neural_networks']['models']
        enabled_models = [m for m in models if m.get('enabled', True)]
        print(f"🧠 Активных моделей: {len(enabled_models)}")
        
        for model in enabled_models:
            print(f"  • {model['name']} ({model['type']}) - вес {model['weight']}")
        
        # Информация о брокере
        broker = config['trading']['broker']
        print(f"🏦 Брокер: {broker}")
        
        # Проверка переменных окружения
        print("\n🔑 Переменные окружения:")
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        print(f"  • DEEPSEEK_API_KEY: {'✅ Установлен' if deepseek_key else '❌ Не установлен'}")
        
        tinkoff_token = os.getenv('TINKOFF_TOKEN')
        print(f"  • TINKOFF_TOKEN: {'✅ Установлен' if tinkoff_token else '❌ Не установлен'}")
        
        print("\n📁 Файлы:")
        files_to_check = [
            "config/main.yaml",
            "logs/investment_system.log",
            "models/",
            "data/"
        ]
        
        for file_path in files_to_check:
            path = Path(file_path)
            status = "✅" if path.exists() else "❌"
            print(f"  • {file_path}: {status}")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")


def main():
    """
    Главная функция
    """
    parser = argparse.ArgumentParser(
        description="Система нейросетевых инвестиций на российском рынке",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python run.py                    # Интерактивный выбор конфигурации и запуск торговли
  python run.py --select-config    # Выбор конфигурации
  python run.py --mode train       # Обучение моделей
  python run.py --mode backtest --start 2023-01-01 --end 2023-12-31  # Бэктестинг
  python run.py --status           # Показать статус системы
  python run.py --config config/aggressive_trading.yaml  # Использовать конкретную конфигурацию
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['trading', 'train', 'backtest'],
        default='trading',
        help='Режим работы (по умолчанию: trading)'
    )
    
    parser.add_argument(
        '--config',
        default=None,
        help='Путь к конфигурационному файлу (если не указан, будет предложен выбор)'
    )
    
    parser.add_argument(
        '--start',
        help='Дата начала бэктестинга (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end',
        help='Дата окончания бэктестинга (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Показать статус системы'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Проверить конфигурацию'
    )
    
    parser.add_argument(
        '--select-config',
        action='store_true',
        help='Интерактивный выбор конфигурации'
    )
    
    args = parser.parse_args()
    
    # Интерактивный выбор конфигурации
    if args.select_config or not args.config:
        # Используем тестовую конфигурацию по умолчанию для быстрого старта
        if not args.select_config and not args.config:
            print("✅ Используется тестовая конфигурация по умолчанию (быстрый режим)")
            print("   Для выбора другой конфигурации используйте: python run.py --select-config")
            args.config = "config/test_config.yaml"
        else:
            selector = ConfigSelector()
            selected_config = selector.select_config()
            if selected_config:
                args.config = selected_config
            else:
                print("❌ Конфигурация не выбрана. Использую тестовую конфигурацию.")
                args.config = "config/test_config.yaml"
    
    # Настройка логирования
    setup_logging(args.config)
    
    # Показать статус
    if args.status:
        show_status()
        return
    
    # Валидация конфигурации
    if args.validate:
        logger.info("Проверка конфигурации...")
        try:
            from scripts.validate_config import validate_config
            is_valid = validate_config(args.config)
            if is_valid:
                logger.info("✅ Конфигурация корректна")
            else:
                logger.error("❌ Конфигурация содержит ошибки")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Ошибка валидации: {e}")
            sys.exit(1)
    
    # Проверка окружения
    if not check_environment():
        logger.error("❌ Проверка окружения не пройдена")
        sys.exit(1)
    
    # Выбор режима работы
    try:
        if args.mode == 'train':
            asyncio.run(run_training_mode(args.config))
        elif args.mode == 'backtest':
            if not args.start or not args.end:
                logger.error("Для бэктестинга необходимо указать --start и --end")
                sys.exit(1)
            asyncio.run(run_backtest_mode(args.config, args.start, args.end))
        else:  # trading
            asyncio.run(run_trading_mode(args.config))
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
