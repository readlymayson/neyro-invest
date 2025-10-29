# -*- coding: utf-8 -*-
"""
Пример интеграции новостных данных в систему нейросетевых инвестиций
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.data.news_data_provider import NewsDataProvider
from src.data.data_provider import DataProvider
from src.neural_networks.network_manager import NetworkManager
from src.core.investment_system import InvestmentSystem
from loguru import logger


async def test_news_provider():
    """
    Тестирование новостного провайдера
    """
    logger.info("🔍 Тестирование новостного провайдера")
    
    # Конфигурация новостного провайдера
    news_config = {
        'providers': [
            {
                'type': 'mock',
                'enabled': True
            }
        ],
        'cache_ttl': 300,
        'days_back': 14
    }
    
    # Создание провайдера
    news_provider = NewsDataProvider(news_config)
    
    # Тестирование получения новостей для символа
    symbol = 'SBER'
    news_summary = await news_provider.get_news_summary(symbol, days=14)
    
    logger.info(f"📰 Новости для {symbol}:")
    logger.info(f"  Всего новостей: {news_summary['total_news']}")
    logger.info(f"  Средняя тональность: {news_summary['avg_sentiment']:.3f}")
    logger.info(f"  Новостной тренд: {news_summary['recent_trend']}")
    logger.info(f"  Сводка: {news_summary['news_summary']}")
    
    # Тестирование получения новостей для всех символов
    symbols = ['SBER', 'GAZP', 'LKOH']
    all_news = await news_provider.get_all_symbols_news(symbols, days=14)
    
    logger.info(f"📊 Новости для {len(symbols)} символов:")
    for sym, news in all_news.items():
        logger.info(f"  {sym}: {news['total_news']} новостей, тональность: {news['avg_sentiment']:.3f}")


async def test_data_provider_with_news():
    """
    Тестирование провайдера данных с новостями
    """
    logger.info("🔍 Тестирование провайдера данных с новостями")
    
    # Конфигурация провайдера данных
    data_config = {
        'provider': 'russian',
        'symbols': ['SBER', 'GAZP', 'LKOH'],
        'update_interval': 60,
        'history_days': 365,
        'news': {
            'enabled': True,
            'providers': [
                {
                    'type': 'mock',
                    'enabled': True
                }
            ],
            'cache_ttl': 300,
            'days_back': 14
        }
    }
    
    # Создание провайдера
    data_provider = DataProvider(data_config)
    
    # Инициализация
    await data_provider.initialize()
    
    # Получение данных с новостями
    latest_data = await data_provider.get_latest_data()
    
    logger.info(f"📈 Данные получены:")
    logger.info(f"  Исторические данные: {len(latest_data['historical'])} символов")
    logger.info(f"  Данные в реальном времени: {len(latest_data['realtime'])} символов")
    logger.info(f"  Новостные данные: {len(latest_data['news'])} символов")
    
    # Показ новостных данных для первого символа
    if latest_data['news']:
        first_symbol = list(latest_data['news'].keys())[0]
        news_data = latest_data['news'][first_symbol]
        logger.info(f"📰 Новости для {first_symbol}:")
        logger.info(f"  Всего новостей: {news_data['total_news']}")
        logger.info(f"  Тональность: {news_data['avg_sentiment']:.3f}")
        logger.info(f"  Тренд: {news_data['recent_trend']}")


async def test_neural_networks_with_news():
    """
    Тестирование нейросетей с новостными данными
    """
    logger.info("🧠 Тестирование нейросетей с новостными данными")
    
    # Конфигурация нейросетей
    neural_config = {
        'models': [
            {
                'name': 'xgboost_enhanced',
                'type': 'xgboost',
                'enabled': True,
                'config': {
                    'n_estimators': 50,
                    'max_depth': 4,
                    'learning_rate': 0.1,
                    'random_state': 42
                }
            }
        ],
        'ensemble_method': 'weighted_average',
        'analysis_interval': 180
    }
    
    # Создание менеджера нейросетей
    network_manager = NetworkManager(neural_config)
    
    # Инициализация
    await network_manager.initialize()
    
    # Создание тестовых данных
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Генерация тестовых исторических данных
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    test_data = pd.DataFrame({
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(100, 200, len(dates)),
        'Low': np.random.uniform(100, 200, len(dates)),
        'Close': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.uniform(1000, 10000, len(dates))
    }, index=dates)
    
    # Тестовые новостные данные
    test_news_data = {
        'SBER': {
            'total_news': 5,
            'avg_sentiment': 0.3,
            'sentiment_confidence': 0.7,
            'positive_news': 3,
            'negative_news': 1,
            'neutral_news': 1,
            'recent_trend': 'positive',
            'news_summary': 'Преобладают позитивные новости о росте прибыли'
        }
    }
    
    # Обучение с новостными данными
    logger.info("🎓 Обучение модели с новостными данными...")
    training_data = {'historical': {'SBER': test_data}}
    await network_manager.train_models(training_data, news_data=test_news_data)
    
    # Анализ с новостными данными
    logger.info("🔍 Анализ с новостными данными...")
    analysis_data = {'historical': {'SBER': test_data.tail(10)}}
    results = await network_manager.analyze(analysis_data, news_data=test_news_data)
    
    logger.info(f"📊 Результаты анализа:")
    if 'ensemble_predictions' in results:
        for symbol, prediction in results['ensemble_predictions'].items():
            logger.info(f"  {symbol}: {prediction.get('signal', 'N/A')} "
                       f"(уверенность: {prediction.get('confidence', 0):.3f})")
            if 'news_summary' in prediction:
                logger.info(f"    Новости: {prediction['news_summary']['news_summary']}")


async def test_full_system():
    """
    Тестирование полной системы с новостными данными
    """
    logger.info("🚀 Тестирование полной системы с новостными данными")
    
    # Создание системы инвестиций
    system = InvestmentSystem("config/main.yaml")
    
    # Инициализация компонентов
    await system._initialize_components()
    
    # Получение данных
    latest_data = await system.data_provider.get_latest_data()
    
    logger.info(f"📊 Система инициализирована:")
    logger.info(f"  Символов: {len(system.data_provider.symbols)}")
    logger.info(f"  Исторических данных: {len(latest_data['historical'])}")
    logger.info(f"  Новостных данных: {len(latest_data.get('news', {}))}")
    
    # Обучение моделей с новостными данными
    news_data = latest_data.get('news', {})
    if news_data:
        logger.info("🎓 Обучение моделей с новостными данными...")
        await system.network_manager.train_models(latest_data, news_data=news_data)
        
        # Анализ с новостными данными
        logger.info("🔍 Анализ с новостными данными...")
        results = await system.network_manager.analyze(latest_data, system.portfolio_manager, news_data)
        
        logger.info(f"📈 Результаты анализа:")
        if 'ensemble_predictions' in results:
            for symbol, prediction in results['ensemble_predictions'].items():
                logger.info(f"  {symbol}: {prediction.get('signal', 'N/A')} "
                           f"(уверенность: {prediction.get('confidence', 0):.3f})")
                
                # Показ новостной информации
                if 'news_summary' in prediction:
                    news_summary = prediction['news_summary']
                    logger.info(f"    📰 Новости: {news_summary['total_news']} новостей, "
                               f"тональность: {news_summary['avg_sentiment']:.3f}")
    else:
        logger.warning("⚠️ Новостные данные недоступны")


async def main():
    """
    Основная функция для тестирования интеграции новостных данных
    """
    logger.info("🎯 Запуск тестирования интеграции новостных данных")
    
    try:
        # Тест 1: Новостной провайдер
        await test_news_provider()
        logger.info("✅ Тест новостного провайдера завершен")
        
        # Тест 2: Провайдер данных с новостями
        await test_data_provider_with_news()
        logger.info("✅ Тест провайдера данных с новостями завершен")
        
        # Тест 3: Нейросети с новостными данными
        await test_neural_networks_with_news()
        logger.info("✅ Тест нейросетей с новостными данными завершен")
        
        # Тест 4: Полная система
        await test_full_system()
        logger.info("✅ Тест полной системы завершен")
        
        logger.info("🎉 Все тесты успешно завершены!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тестах: {e}")
        raise


if __name__ == "__main__":
    # Настройка логирования
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    
    # Запуск тестов
    asyncio.run(main())
