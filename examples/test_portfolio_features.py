"""
Тестирование интеграции портфельных признаков в нейросеть
"""

import asyncio
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.data.data_provider import DataProvider
from src.neural_networks.network_manager import NetworkManager
from src.portfolio.portfolio_manager import PortfolioManager
from src.neural_networks.portfolio_features import PortfolioFeatureExtractor
from src.utils.config_manager import ConfigManager
from loguru import logger


async def test_portfolio_features():
    """
    Тестирование портфельных признаков
    """
    try:
        logger.info("🧪 Начало тестирования портфельных признаков")
        
        # Загрузка конфигурации
        config_manager = ConfigManager("config/main.yaml")
        config = config_manager.get_config()
        
        # Инициализация менеджера портфеля
        portfolio_manager = PortfolioManager(config['portfolio'])
        await portfolio_manager.initialize()
        
        # Создание тестовых данных портфеля
        await create_test_portfolio_data(portfolio_manager)
        
        # Тестирование извлечения портфельных признаков
        logger.info("📊 Тестирование извлечения портфельных признаков")
        portfolio_extractor = PortfolioFeatureExtractor(config['neural_networks'].get('portfolio_features', {}))
        
        # Извлечение признаков для общего портфеля
        portfolio_features = portfolio_extractor.extract_portfolio_features(portfolio_manager)
        
        logger.info("✅ Портфельные признаки извлечены:")
        logger.info(f"  - Общая стоимость: {portfolio_features.total_value:,.2f} ₽")
        logger.info(f"  - P&L: {portfolio_features.total_pnl:,.2f} ₽ ({portfolio_features.total_pnl_percent:.2f}%)")
        logger.info(f"  - Количество позиций: {portfolio_features.position_count}")
        logger.info(f"  - Прибыльные позиции: {portfolio_features.winning_positions}")
        logger.info(f"  - Убыточные позиции: {portfolio_features.losing_positions}")
        logger.info(f"  - Коэффициент Шарпа: {portfolio_features.sharpe_ratio:.3f}")
        logger.info(f"  - Максимальная просадка: {portfolio_features.max_drawdown:.2f}%")
        logger.info(f"  - Волатильность: {portfolio_features.volatility:.2f}%")
        
        # Тестирование конвертации в DataFrame
        logger.info("📈 Тестирование конвертации в DataFrame")
        portfolio_df = portfolio_extractor.features_to_dataframe(portfolio_features)
        
        logger.info(f"✅ DataFrame создан: {portfolio_df.shape}")
        logger.info(f"  - Колонки: {list(portfolio_df.columns)}")
        
        # Тестирование признаков по символу
        logger.info("🎯 Тестирование признаков по символу")
        symbol_features = portfolio_extractor.extract_portfolio_features(portfolio_manager, "SBER")
        
        if symbol_features.symbol_features:
            logger.info("✅ Признаки по символу извлечены:")
            for symbol, features in symbol_features.symbol_features.items():
                logger.info(f"  {symbol}: {features}")
        
        # Тестирование интеграции с нейросетью
        logger.info("🧠 Тестирование интеграции с нейросетью")
        
        # Инициализация провайдера данных
        data_provider = DataProvider(config['data'])
        await data_provider.initialize()
        
        # Получение рыночных данных
        market_data = await data_provider.get_latest_data()
        
        # Инициализация менеджера нейросетей
        network_manager = NetworkManager(config['neural_networks'])
        await network_manager.initialize()
        
        # Анализ с портфельными данными
        logger.info("🔍 Анализ с портфельными данными")
        predictions = await network_manager.analyze(market_data, portfolio_manager)
        
        logger.info("✅ Анализ завершен:")
        logger.info(f"  - Проанализировано символов: {len(predictions.get('symbols_analyzed', []))}")
        logger.info(f"  - Использовано моделей: {len(predictions.get('models_used', []))}")
        
        # Вывод результатов анализа
        ensemble_predictions = predictions.get('ensemble_predictions', {})
        for symbol, prediction in ensemble_predictions.items():
            logger.info(f"  {symbol}: {prediction.get('signal', 'N/A')} (уверенность: {prediction.get('confidence', 0):.3f})")
        
        logger.info("🎉 Тестирование портфельных признаков завершено успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        raise


async def create_test_portfolio_data(portfolio_manager):
    """
    Создание тестовых данных портфеля
    """
    try:
        logger.info("📝 Создание тестовых данных портфеля")
        
        # Добавление тестовых транзакций
        from src.portfolio.portfolio_manager import Transaction, TransactionType
        from datetime import datetime, timedelta
        
        # Покупка SBER
        transaction1 = Transaction(
            id="test_1",
            symbol="SBER",
            type=TransactionType.BUY,
            quantity=100,
            price=200.0,
            commission=10.0,
            timestamp=datetime.now() - timedelta(days=30),
            notes="Тестовая покупка SBER"
        )
        await portfolio_manager.add_transaction({
            'id': transaction1.id,
            'symbol': transaction1.symbol,
            'side': transaction1.type.value,
            'quantity': transaction1.quantity,
            'price': transaction1.price,
            'commission': transaction1.commission,
            'timestamp': transaction1.timestamp,
            'notes': transaction1.notes
        })
        
        # Покупка GAZP
        transaction2 = Transaction(
            id="test_2",
            symbol="GAZP",
            type=TransactionType.BUY,
            quantity=50,
            price=150.0,
            commission=7.5,
            timestamp=datetime.now() - timedelta(days=20),
            notes="Тестовая покупка GAZP"
        )
        await portfolio_manager.add_transaction({
            'id': transaction2.id,
            'symbol': transaction2.symbol,
            'side': transaction2.type.value,
            'quantity': transaction2.quantity,
            'price': transaction2.price,
            'commission': transaction2.commission,
            'timestamp': transaction2.timestamp,
            'notes': transaction2.notes
        })
        
        # Продажа части SBER
        transaction3 = Transaction(
            id="test_3",
            symbol="SBER",
            type=TransactionType.SELL,
            quantity=30,
            price=220.0,
            commission=6.6,
            timestamp=datetime.now() - timedelta(days=10),
            notes="Тестовая продажа SBER"
        )
        await portfolio_manager.add_transaction({
            'id': transaction3.id,
            'symbol': transaction3.symbol,
            'side': transaction3.type.value,
            'quantity': transaction3.quantity,
            'price': transaction3.price,
            'commission': transaction3.commission,
            'timestamp': transaction3.timestamp,
            'notes': transaction3.notes
        })
        
        # Обновление портфеля
        await portfolio_manager.update_portfolio()
        
        logger.info("✅ Тестовые данные портфеля созданы")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания тестовых данных: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_portfolio_features())
