"""
Тестовый скрипт для проверки ограничений размера позиций.
"""

import asyncio
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.data.data_provider import DataProvider
from src.neural_networks.network_manager import NetworkManager
from src.portfolio.portfolio_manager import PortfolioManager, Position, Transaction, TransactionType
from src.trading.trading_engine import TradingEngine
from src.utils.config_manager import ConfigManager
from loguru import logger

async def test_position_limits():
    """
    Тестирование ограничений размера позиций.
    """
    logger.info("🚀 Запуск теста ограничений размера позиций")

    try:
        # 1. Загрузка конфигурации
        config_manager = ConfigManager("config/main.yaml")
        config = config_manager.get_config()
        
        # 2. Инициализация провайдера данных
        data_provider = DataProvider(config['data'])
        await data_provider.initialize()
        
        # 3. Инициализация менеджера портфеля
        portfolio_manager = PortfolioManager(config['portfolio'])
        await portfolio_manager.initialize()

        # 4. Создание тестового портфеля с большой позицией
        logger.info("📝 Создание тестового портфеля с большой позицией")
        
        # Добавляем большую позицию (50% от капитала)
        large_transaction = Transaction(
            id="large_txn", 
            symbol="SBER", 
            type=TransactionType.BUY, 
            quantity=500000,  # 500,000 акций по ~200₽ = 100,000,000₽ (100% капитала)
            price=200.0, 
            commission=0.0, 
            timestamp=datetime.now() - timedelta(days=1)
        )
        portfolio_manager.transactions.append(large_transaction)
        portfolio_manager.cash_balance = 1_000_000 - (500000 * 200.0)  # Остается 0₽
        await portfolio_manager.update_portfolio()
        
        logger.info(f"Тестовый портфель создан:")
        if portfolio_manager.current_metrics:
            logger.info(f"  - Общая стоимость: {portfolio_manager.current_metrics.total_value:.2f} ₽")
            logger.info(f"  - Денежные средства: {portfolio_manager.current_metrics.cash_balance:.2f} ₽")
            logger.info(f"  - Инвестированная стоимость: {portfolio_manager.current_metrics.invested_value:.2f} ₽")
            logger.info(f"  - Количество позиций: {len(portfolio_manager.positions)}")

        # 5. Инициализация торгового движка
        trading_engine = TradingEngine(config['trading'])
        trading_engine.portfolio_manager = portfolio_manager
        trading_engine.data_provider = data_provider
        
        # 6. Тестирование ограничений
        logger.info("🔍 Тестирование ограничений размера позиций")
        
        # Создаем тестовый сигнал на покупку
        from src.trading.trading_engine import TradingSignal
        test_signal = TradingSignal(
            symbol="GAZP",
            signal="BUY",
            confidence=0.8,
            timestamp=datetime.now(),
            source="test"
        )
        
        # Тестируем расчет размера позиции
        position_size = await trading_engine._calculate_position_size(test_signal)
        
        logger.info(f"✅ Результат тестирования:")
        logger.info(f"  - Запрошенный размер позиции для GAZP: {position_size}")
        logger.info(f"  - Максимальный размер позиции: {portfolio_manager.current_metrics.total_value * 0.1:.2f} ₽ (10%)")
        logger.info(f"  - Текущее общее воздействие: {portfolio_manager.current_metrics.invested_value:.2f} ₽")
        logger.info(f"  - Максимальное общее воздействие: {portfolio_manager.current_metrics.total_value * 0.8:.2f} ₽ (80%)")
        
        # Проверяем, что ограничения работают
        if position_size == 0:
            logger.info("✅ Ограничения работают корректно - позиция заблокирована")
        else:
            logger.warning("⚠️ Ограничения не сработали - позиция разрешена")
        
        # 7. Тестирование с меньшим портфелем
        logger.info("🔄 Тестирование с меньшим портфелем")
        
        # Создаем новый портфель с меньшими позициями
        portfolio_manager2 = PortfolioManager(config['portfolio'])
        await portfolio_manager2.initialize()
        
        # Добавляем небольшую позицию (5% от капитала)
        small_transaction = Transaction(
            id="small_txn", 
            symbol="SBER", 
            type=TransactionType.BUY, 
            quantity=2500,  # 2,500 акций по ~200₽ = 500,000₽ (50% капитала)
            price=200.0, 
            commission=0.0, 
            timestamp=datetime.now() - timedelta(days=1)
        )
        portfolio_manager2.transactions.append(small_transaction)
        portfolio_manager2.cash_balance = 1_000_000 - (2500 * 200.0)  # Остается 500,000₽
        await portfolio_manager2.update_portfolio()
        
        # Обновляем торговый движок
        trading_engine.portfolio_manager = portfolio_manager2
        
        # Тестируем снова
        position_size2 = await trading_engine._calculate_position_size(test_signal)
        
        logger.info(f"✅ Результат тестирования с меньшим портфелем:")
        logger.info(f"  - Запрошенный размер позиции для GAZP: {position_size2}")
        logger.info(f"  - Текущее общее воздействие: {portfolio_manager2.current_metrics.invested_value:.2f} ₽")
        
        if position_size2 > 0:
            logger.info("✅ Ограничения работают корректно - позиция разрешена")
        else:
            logger.warning("⚠️ Позиция заблокирована даже при наличии свободных средств")
        
        logger.info("🎉 Тест ограничений размера позиций завершен успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка в тесте ограничений размера позиций: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_position_limits())
