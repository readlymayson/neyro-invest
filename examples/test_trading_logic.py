"""
Тестовый скрипт для анализа логики торговли и причин отклонения сигналов.
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

from src.trading.trading_engine import TradingEngine, TradingSignal
from src.portfolio.portfolio_manager import PortfolioManager, Position, Transaction, TransactionType
from src.data.data_provider import DataProvider
from src.utils.config_manager import ConfigManager
from loguru import logger

async def test_trading_logic():
    """
    Тестирование логики торговли для выявления причин отклонения сигналов.
    """
    logger.info("🚀 Запуск теста логики торговли")

    try:
        # 1. Загрузка конфигурации
        config_manager = ConfigManager("config/main.yaml")
        config = config_manager.get_config()

        # 2. Инициализация компонентов
        data_provider = DataProvider(config['data'])
        await data_provider.initialize()
        
        portfolio_manager = PortfolioManager(config['portfolio'])
        await portfolio_manager.initialize()
        
        trading_engine = TradingEngine(config['trading'])
        trading_engine.set_components(data_provider, portfolio_manager)
        
        # 3. Создание тестового портфеля
        logger.info("📝 Создание тестового портфеля")
        
        # Добавляем позицию SBER
        sber_transaction = Transaction(
            id="sber_txn", 
            symbol="SBER", 
            type=TransactionType.BUY, 
            quantity=100, 
            price=200.0, 
            commission=0.0, 
            timestamp=datetime.now() - timedelta(days=1)
        )
        portfolio_manager.transactions.append(sber_transaction)
        portfolio_manager.cash_balance = 1_000_000 - (100 * 200.0)
        await portfolio_manager.update_portfolio()
        
        logger.info(f"Портфель создан:")
        logger.info(f"  - Денежные средства: {portfolio_manager.cash_balance:.2f} ₽")
        logger.info(f"  - Позиций: {len(portfolio_manager.positions)}")
        
        if portfolio_manager.positions:
            for symbol, pos in portfolio_manager.positions.items():
                logger.info(f"  - {symbol}: {pos.quantity} шт по {pos.average_price:.2f} ₽")
        
        # 4. Тест различных сигналов
        logger.info("🔍 Тест различных торговых сигналов")
        
        test_signals = [
            TradingSignal(symbol="SBER", signal="BUY", confidence=0.8, source="test"),
            TradingSignal(symbol="SBER", signal="SELL", confidence=0.7, source="test"),
            TradingSignal(symbol="GAZP", signal="BUY", confidence=0.9, source="test"),
            TradingSignal(symbol="GAZP", signal="SELL", confidence=0.6, source="test"),
            TradingSignal(symbol="LKOH", signal="BUY", confidence=0.8, source="test"),
            TradingSignal(symbol="LKOH", signal="SELL", confidence=0.5, source="test"),
        ]
        
        for i, signal in enumerate(test_signals, 1):
            logger.info(f"\n📊 Тест {i}: {signal.signal} для {signal.symbol}")
            
            # Проверка возможности продажи
            if signal.signal == 'SELL':
                can_sell = await trading_engine._can_sell(signal.symbol)
                logger.info(f"  - Можно продать: {can_sell}")
                
                if not can_sell:
                    # Проверяем причины
                    positions = portfolio_manager.positions
                    if signal.symbol not in positions:
                        logger.info(f"  - Причина: Нет позиции по {signal.symbol}")
                    else:
                        pos = positions[signal.symbol]
                        logger.info(f"  - Причина: Количество позиции {pos.quantity} <= 0")
            
            # Проверка размера позиции
            position_size = await trading_engine._calculate_position_size(signal)
            logger.info(f"  - Размер позиции: {position_size}")
            
            if position_size <= 0:
                logger.info(f"  - Причина отклонения: Размер позиции = 0")
                
                # Дополнительная диагностика
                if signal.signal == 'BUY':
                    portfolio_value = await portfolio_manager.get_portfolio_value()
                    logger.info(f"  - Стоимость портфеля: {portfolio_value:.2f} ₽")
                    logger.info(f"  - Денежные средства: {portfolio_manager.cash_balance:.2f} ₽")
                    
                    # Проверяем ограничения
                    if trading_engine.position_size_check:
                        current_invested = sum(pos.market_value for pos in portfolio_manager.positions.values())
                        max_allowed = portfolio_value * trading_engine.max_total_exposure
                        logger.info(f"  - Текущие инвестиции: {current_invested:.2f} ₽")
                        logger.info(f"  - Максимум разрешено: {max_allowed:.2f} ₽")
                        logger.info(f"  - Превышен лимит: {current_invested >= max_allowed}")
            
            # Попытка выполнения сигнала
            try:
                await trading_engine._execute_signal(signal)
                logger.info(f"  - ✅ Сигнал обработан")
            except Exception as e:
                logger.warning(f"  - ❌ Сигнал отклонен: {e}")
        
        # 5. Анализ результатов
        logger.info("\n📈 Анализ результатов:")
        logger.info("  - BUY сигналы для SBER: должны проходить (есть деньги)")
        logger.info("  - SELL сигналы для SBER: должны проходить (есть позиция)")
        logger.info("  - BUY сигналы для GAZP/LKOH: могут проходить (есть деньги)")
        logger.info("  - SELL сигналы для GAZP/LKOH: должны отклоняться (нет позиций)")
        
        # 6. Проверка временных ограничений
        logger.info("\n⏰ Тест временных ограничений")
        
        # Создаем сигнал сразу после предыдущего
        immediate_signal = TradingSignal(symbol="SBER", signal="BUY", confidence=0.9, source="immediate")
        
        logger.info(f"Минимальный интервал: {trading_engine.min_trade_interval} секунд")
        logger.info(f"Последняя сделка по SBER: {trading_engine.last_trade_time.get('SBER', 'Нет')}")
        
        try:
            await trading_engine._execute_signal(immediate_signal)
            logger.info("✅ Немедленный сигнал обработан")
        except Exception as e:
            logger.info(f"⚠️ Немедленный сигнал отклонен: {e}")
        
        logger.info("🎉 Тест логики торговли завершен!")

    except Exception as e:
        logger.error(f"❌ Ошибка в тесте логики торговли: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_trading_logic())
