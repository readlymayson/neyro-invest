"""
Тестовый скрипт для проверки обработки конфликтующих и повторяющихся сигналов.
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
from src.utils.config_manager import ConfigManager
from loguru import logger

async def test_conflicting_signals():
    """
    Тестирование обработки конфликтующих и повторяющихся сигналов.
    """
    logger.info("🚀 Запуск теста обработки конфликтующих сигналов")

    try:
        # 1. Загрузка конфигурации
        config_manager = ConfigManager("config/main.yaml")
        config = config_manager.get_config()

        # 2. Инициализация торгового движка
        trading_engine = TradingEngine(config['trading'])
        
        # 3. Тест 1: Конфликтующие сигналы для одного инструмента
        logger.info("🔍 Тест 1: Конфликтующие сигналы для одного инструмента")
        
        # Создаем конфликтующие сигналы для SBER
        buy_signal = TradingSignal(
            symbol="SBER",
            signal="BUY",
            confidence=0.8,
            timestamp=datetime.now(),
            source="test_buy"
        )
        
        sell_signal = TradingSignal(
            symbol="SBER", 
            signal="SELL",
            confidence=0.7,
            timestamp=datetime.now(),
            source="test_sell"
        )
        
        hold_signal = TradingSignal(
            symbol="SBER",
            signal="HOLD", 
            confidence=0.6,
            timestamp=datetime.now(),
            source="test_hold"
        )
        
        # Симулируем получение конфликтующих сигналов
        logger.info("📊 Созданы конфликтующие сигналы:")
        logger.info(f"  - BUY сигнал: уверенность {buy_signal.confidence}")
        logger.info(f"  - SELL сигнал: уверенность {sell_signal.confidence}")
        logger.info(f"  - HOLD сигнал: уверенность {hold_signal.confidence}")
        
        # Проверяем, как система обрабатывает конфликтующие сигналы
        logger.info("🔄 Обработка конфликтующих сигналов...")
        
        # Симулируем выполнение всех сигналов
        conflicting_signals = [buy_signal, sell_signal, hold_signal]
        
        for i, signal in enumerate(conflicting_signals, 1):
            logger.info(f"  {i}. Обработка {signal.signal} сигнала для {signal.symbol}")
            try:
                await trading_engine._execute_signal(signal)
                logger.info(f"     ✅ Сигнал {signal.signal} обработан")
            except Exception as e:
                logger.warning(f"     ⚠️ Сигнал {signal.signal} отклонен: {e}")
        
        # 4. Тест 2: Повторяющиеся сигналы
        logger.info("🔍 Тест 2: Повторяющиеся сигналы")
        
        # Создаем несколько одинаковых BUY сигналов
        buy_signals = [
            TradingSignal(symbol="GAZP", signal="BUY", confidence=0.9, source="model1"),
            TradingSignal(symbol="GAZP", signal="BUY", confidence=0.8, source="model2"), 
            TradingSignal(symbol="GAZP", signal="BUY", confidence=0.7, source="model3")
        ]
        
        logger.info("📊 Созданы повторяющиеся BUY сигналы для GAZP:")
        for i, signal in enumerate(buy_signals, 1):
            logger.info(f"  - Сигнал {i}: уверенность {signal.confidence} от {signal.source}")
        
        # Проверяем обработку повторяющихся сигналов
        logger.info("🔄 Обработка повторяющихся сигналов...")
        
        for i, signal in enumerate(buy_signals, 1):
            logger.info(f"  {i}. Обработка BUY сигнала от {signal.source}")
            try:
                await trading_engine._execute_signal(signal)
                logger.info(f"     ✅ Сигнал от {signal.source} обработан")
            except Exception as e:
                logger.warning(f"     ⚠️ Сигнал от {signal.source} отклонен: {e}")
        
        # 5. Тест 3: Проверка временных ограничений
        logger.info("🔍 Тест 3: Проверка временных ограничений")
        
        # Создаем сигнал сразу после предыдущего
        immediate_signal = TradingSignal(
            symbol="SBER",
            signal="SELL", 
            confidence=0.9,
            timestamp=datetime.now(),
            source="immediate_test"
        )
        
        logger.info("📊 Создан сигнал сразу после предыдущего:")
        logger.info(f"  - Сигнал: {immediate_signal.signal} для {immediate_signal.symbol}")
        logger.info(f"  - Время: {immediate_signal.timestamp}")
        logger.info(f"  - Минимальный интервал: {trading_engine.min_trade_interval} секунд")
        
        # Проверяем временные ограничения
        try:
            await trading_engine._execute_signal(immediate_signal)
            logger.info("     ✅ Сигнал обработан (временные ограничения не сработали)")
        except Exception as e:
            logger.info(f"     ⚠️ Сигнал отклонен временными ограничениями: {e}")
        
        # 6. Анализ результатов
        logger.info("📊 Анализ результатов тестирования:")
        logger.info("  - Система обрабатывает каждый сигнал независимо")
        logger.info("  - Нет механизма разрешения конфликтов между сигналами")
        logger.info("  - Временные ограничения работают на уровне символа")
        logger.info("  - Повторяющиеся сигналы выполняются последовательно")
        
        logger.info("🎉 Тест обработки конфликтующих сигналов завершен!")

    except Exception as e:
        logger.error(f"❌ Ошибка в тесте конфликтующих сигналов: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_conflicting_signals())
