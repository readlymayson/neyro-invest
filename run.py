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
from src.utils.interactive_console import start_interactive_console


def setup_logging(config_path: str = "config/main.yaml"):
    """
    Настройка логирования с созданием уникальных файлов для каждой сессии
    """
    try:
        from datetime import datetime
        
        # Создание директории логов
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Создание поддиректории для текущей сессии
        session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = logs_dir / f"session_{session_timestamp}"
        session_dir.mkdir(exist_ok=True)
        
        # Удаление старых обработчиков
        logger.remove()
        
        # Настройка консольного вывода
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # Настройка основного файла логов для сессии
        logger.add(
            session_dir / "investment_system.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            encoding="utf-8"
        )
        
        # Настройка отдельных логов для компонентов
        logger.add(
            session_dir / "trading.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "trading" in record["name"].lower(),
            encoding="utf-8"
        )
        
        logger.add(
            session_dir / "neural_networks.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "neural" in record["name"].lower(),
            encoding="utf-8"
        )
        
        # Настройка логов для GUI приложения
        logger.add(
            session_dir / "gui_application.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "gui" in record["name"].lower() or "web" in record["name"].lower(),
            encoding="utf-8"
        )
        
        # Настройка логов для бэктестинга
        logger.add(
            session_dir / "backtesting.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "backtest" in record["name"].lower(),
            encoding="utf-8"
        )
        
        # Настройка логов для веб-запуска
        logger.add(
            session_dir / "web_launcher.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "web_launcher" in record["name"].lower(),
            encoding="utf-8"
        )
        
        logger.info(f"Логирование настроено для сессии {session_timestamp}")
        logger.info(f"Файлы логов сохраняются в: {session_dir}")
        
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
        
        # Проверяем, нужно ли использовать новостные данные при обучении
        news_config = system.config.get('data', {}).get('news', {})
        include_news_in_training = news_config.get('include_news_in_training', False)
        
        if include_news_in_training:
            # При обучении используем новостные данные расширенного периода (training_news_days)
            news_data = historical_data.get('news_training', {}) or historical_data.get('news', {})
            if news_data:
                logger.info(f"Новостные данные включены в обучение для {len(news_data)} символов (расширенный период)")
            else:
                logger.warning("Новостные данные для обучения недоступны, обучение продолжится без новостей")
            await system.network_manager.train_models(historical_data, news_data=news_data)
        else:
            # При обучении новостные данные НЕ используются - только исторические данные за 1 год
            logger.info("Обучение на исторических данных без новостей (новости используются только при анализе)")
            await system.network_manager.train_models(historical_data)
        
        logger.info("✅ Обучение завершено успешно!")
        
        # Тестирование моделей
        logger.info("Тестирование обученных моделей...")
        
        # При анализе используются новостные данные за 2 недели для актуальности выводов
        news_data = historical_data.get('news', {})
        if news_data:
            logger.info(f"Новостные данные включены в анализ для {len(news_data)} символов (сводки за 2 недели)")
        else:
            logger.info("Новостные данные не доступны для анализа")
        
        test_results = await system.network_manager.analyze(historical_data, system.portfolio_manager, news_data=news_data)
        
        # Экспорт сигналов после тестирования
        await system._export_signals_data()
        
        logger.info("Результаты тестирования:")
        ensemble_pred = test_results.get('ensemble_prediction', {})
        logger.info(f"Ансамблевое предсказание: {ensemble_pred}")
        
    except Exception as e:
        logger.error(f"Ошибка в режиме обучения: {e}")
        raise


async def run_interactive_mode(config_path: str):
    """
    Интерактивный режим с командами
    """
    logger.info("🎮 Запуск в интерактивном режиме")
    
    try:
        # Инициализация системы
        system = InvestmentSystem(config_path)
        
        # Инициализация компонентов для интерактивного режима
        await system.initialize_components()
        
        await start_interactive_console(
            system=system,
            portfolio=system.portfolio_manager
        )
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка в интерактивном режиме: {e}")
        raise

async def run_auto_mode(config_path: str):
    """
    Автоматический режим торговли с интерактивной консолью
    """
    logger.info("🤖 Запуск в автоматическом режиме торговли")
    
    try:
        # Инициализация системы
        system = InvestmentSystem(config_path)
        
        # Запуск автоматической торговли в фоне
        trading_task = asyncio.create_task(system.start_trading())
        
        # Запуск интерактивной консоли параллельно
        console_task = asyncio.create_task(
            start_interactive_console(
                system=system,
                portfolio=system.portfolio_manager
            )
        )
        
        # Ожидание завершения любой из задач
        done, pending = await asyncio.wait(
            [trading_task, console_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Отмена оставшихся задач
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        await system.stop_trading()
    except Exception as e:
        logger.error(f"Ошибка в автоматическом режиме: {e}")
        await system.stop_trading()
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
  python run.py                    # Интерактивный режим с командами (по умолчанию)
  python run.py --mode auto        # Автоматическая торговля с консолью
  python run.py --select-config    # Выбор конфигурации
  python run.py --mode train       # Обучение моделей
  python run.py --mode backtest --start 2023-01-01 --end 2023-12-31  # Бэктестинг
  python run.py --status           # Показать статус системы
  python run.py --config config/aggressive_trading.yaml  # Использовать конкретную конфигурацию
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['train', 'backtest', 'auto'],
        default=None,
        help='Режим работы (по умолчанию: интерактивный)'
    )
    
    parser.add_argument(
        '--config',
        default='config/main.yaml',
        help='Путь к конфигурационному файлу (по умолчанию: config/main.yaml)'
    )
    
    parser.add_argument(
        '--auto-account',
        action='store_true',
        help='Автоматическое определение счета (по умолчанию для T-Bank)'
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
    if args.select_config:
        selector = ConfigSelector()
        selected_config = selector.select_config()
        if selected_config:
            args.config = selected_config
        else:
            print("❌ Конфигурация не выбрана. Использую config/main.yaml по умолчанию.")
            args.config = "config/main.yaml"
    
    # Настройка логирования
    setup_logging(args.config)
    
    # Проверка T-Bank конфигурации
    if "tbank" in args.config.lower():
        print("🏦 T-Bank конфигурация обнаружена")
        print("☁️ Облачная синхронизация включена")
        print("🔄 Автоматическое определение счета включено")
        print("=" * 50)
        
        # Проверка токена T-Bank
        tbank_token = os.getenv('TINKOFF_TOKEN')
        if not tbank_token:
            print("❌ Переменная TINKOFF_TOKEN не установлена")
            print("Установите токен: set TINKOFF_TOKEN=your_token_here")
            print("Или создайте файл .env с содержимым: TINKOFF_TOKEN=your_token_here")
            sys.exit(1)
        else:
            print(f"✅ T-Bank токен найден: {tbank_token[:10]}...")
    
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
        elif args.mode == 'auto':
            asyncio.run(run_auto_mode(args.config))
        else:  # По умолчанию - интерактивный режим
            asyncio.run(run_interactive_mode(args.config))
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
