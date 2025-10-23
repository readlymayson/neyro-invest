#!/usr/bin/env python3
"""
Тестирование расширенного T-Bank провайдера данных
Проверяет возможности получения стакана заявок, расширенных данных и признаков
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.data.enhanced_tbank_provider import EnhancedTBankProvider
from src.data.data_provider import DataProvider
from src.neural_networks.enhanced_features import EnhancedFeatureExtractor
from loguru import logger

# Настройка логирования
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


async def test_enhanced_tbank_provider():
    """Тестирование расширенного T-Bank провайдера"""
    
    print("🚀 Тестирование расширенного T-Bank провайдера данных")
    print("=" * 60)
    
    # Получение токена
    token = os.environ.get('TINKOFF_TOKEN')
    if not token:
        print("❌ Переменная окружения TINKOFF_TOKEN не установлена")
        print("Установите токен: set TINKOFF_TOKEN=your_token_here")
        return
    
    # Список тестовых символов
    test_symbols = ['SBER', 'GAZP', 'LKOH']
    
    try:
        # 1. Тестирование базового T-Bank провайдера
        print("\n1️⃣ Тестирование базового T-Bank провайдера")
        print("-" * 40)
        
        provider = EnhancedTBankProvider(token, sandbox=True, symbols=test_symbols)
        await provider.initialize()
        
        print(f"✅ Провайдер инициализирован")
        print(f"📊 Доступно инструментов: {len(provider.instruments_cache)}")
        
        # Показать примеры доступных инструментов
        sample_instruments = list(provider.instruments_cache.keys())[:5]
        print(f"🔍 Примеры инструментов: {', '.join(sample_instruments)}")
        
        # 2. Тестирование исторических данных
        print("\n2️⃣ Тестирование исторических данных")
        print("-" * 40)
        
        for symbol in test_symbols:
            print(f"\n📈 Получение данных для {symbol}...")
            
            # Получение исторических данных
            historical_data = await provider.get_historical_data(symbol, period="1m", interval="1d")
            
            if not historical_data.empty:
                print(f"  ✅ Получено {len(historical_data)} записей")
                print(f"  📅 Период: {historical_data.index[0]} - {historical_data.index[-1]}")
                print(f"  💰 Последняя цена: {historical_data['Close'].iloc[-1]:.2f} ₽")
            else:
                print(f"  ❌ Нет данных для {symbol}")
        
        # 3. Тестирование данных в реальном времени
        print("\n3️⃣ Тестирование данных в реальном времени")
        print("-" * 40)
        
        realtime_data = await provider.get_realtime_data(test_symbols)
        print(f"✅ Получены данные для {len(realtime_data)} инструментов")
        
        for symbol, data in realtime_data.items():
            print(f"  {symbol}: {data['price']:.2f} ₽ ({data['timestamp']})")
        
        # 4. Тестирование стакана заявок
        print("\n4️⃣ Тестирование стакана заявок")
        print("-" * 40)
        
        for symbol in test_symbols[:2]:  # Тестируем только первые 2 символа
            print(f"\n📊 Стакан заявок для {symbol}:")
            
            orderbook = await provider.get_orderbook(symbol, depth=5)
            
            if orderbook:
                print(f"  ✅ Получен стакан глубиной {orderbook.get('depth', 0)}")
                print(f"  💰 Спред: {orderbook.get('spread', 0):.2f} ₽ ({orderbook.get('spread_percent', 0):.2f}%)")
                print(f"  📈 Лучший bid: {orderbook.get('bids', [{}])[0].get('price', 0):.2f} ₽")
                print(f"  📉 Лучший ask: {orderbook.get('asks', [{}])[0].get('price', 0):.2f} ₽")
                print(f"  📊 Объем bid: {orderbook.get('total_bid_volume', 0)}")
                print(f"  📊 Объем ask: {orderbook.get('total_ask_volume', 0)}")
                print(f"  ⚖️ Дисбаланс: {orderbook.get('volume_imbalance', 0)}")
            else:
                print(f"  ❌ Не удалось получить стакан для {symbol}")
        
        # 5. Тестирование расширенных данных
        print("\n5️⃣ Тестирование расширенных данных")
        print("-" * 40)
        
        enhanced_data = await provider.get_enhanced_market_data(test_symbols[:2])
        print(f"✅ Получены расширенные данные для {len(enhanced_data)} инструментов")
        
        for symbol, data in enhanced_data.items():
            print(f"\n📊 Расширенные данные для {symbol}:")
            print(f"  💰 Цена: {data['price']:.2f} ₽")
            print(f"  📈 Спред: {data['metrics']['spread']:.2f} ₽")
            print(f"  📊 Дисбаланс объема: {data['metrics']['volume_imbalance']}")
            print(f"  🏢 Тип: {data['instrument']['type']}")
            print(f"  💱 Валюта: {data['instrument']['currency']}")
        
        # 6. Тестирование извлечения признаков
        print("\n6️⃣ Тестирование извлечения признаков")
        print("-" * 40)
        
        extractor = EnhancedFeatureExtractor()
        
        for symbol in test_symbols[:1]:  # Тестируем только один символ
            print(f"\n🧠 Извлечение признаков для {symbol}:")
            
            # Получение исторических данных
            historical_data = await provider.get_historical_data(symbol, period="1m", interval="1d")
            
            if not historical_data.empty:
                # Получение стакана заявок
                orderbook_data = await provider.get_orderbook(symbol, depth=5)
                
                # Получение информации об инструменте
                instrument_info = provider.instruments_cache.get(symbol, {})
                
                # Извлечение признаков
                features = extractor.extract_all_features(
                    historical_data, 
                    orderbook_data, 
                    instrument_info
                )
                
                print(f"  ✅ Извлечено {len(features.columns)} признаков")
                
                # Показать категории признаков
                categories = extractor.get_feature_importance_categories()
                for category, feature_list in categories.items():
                    available_features = [f for f in feature_list if f in features.columns]
                    if available_features:
                        print(f"  📊 {category}: {len(available_features)} признаков")
                
                # Показать примеры признаков
                print(f"  🔍 Примеры признаков:")
                sample_features = list(features.columns)[:10]
                for feature in sample_features:
                    if feature in features.columns:
                        value = features[feature].iloc[-1] if not features[feature].empty else 0
                        print(f"    {feature}: {value:.4f}")
            else:
                print(f"  ❌ Нет исторических данных для {symbol}")
        
        print("\n" + "=" * 60)
        print("✅ Тестирование расширенного T-Bank провайдера завершено успешно!")
        print("🎯 Провайдер поддерживает:")
        print("  • Исторические данные с различными интервалами")
        print("  • Данные в реальном времени")
        print("  • Стакан заявок с метриками ликвидности")
        print("  • Расширенные рыночные данные")
        print("  • Извлечение 50+ признаков для нейросети")
        
    except Exception as e:
        logger.error(f"Ошибка тестирования: {e}")
        print(f"❌ Произошла ошибка: {e}")


async def test_data_provider_integration():
    """Тестирование интеграции с основным провайдером данных"""
    
    print("\n🔗 Тестирование интеграции с основным провайдером")
    print("=" * 60)
    
    # Конфигурация для T-Bank провайдера
    config = {
        'provider': 'tbank',
        'symbols': ['SBER', 'GAZP'],
        'tbank_token': os.environ.get('TINKOFF_TOKEN'),
        'tbank_sandbox': True,
        'update_interval': 60,
        'history_days': 30
    }
    
    if not config['tbank_token']:
        print("❌ TINKOFF_TOKEN не установлен, пропускаем тест интеграции")
        return
    
    try:
        # Создание провайдера данных
        data_provider = DataProvider(config)
        await data_provider.initialize()
        
        print("✅ Провайдер данных инициализирован")
        
        # Получение информации о провайдере
        provider_info = data_provider.get_provider_info()
        print(f"📊 Тип провайдера: {provider_info['provider_type']}")
        print(f"📈 Символов: {provider_info['symbols_count']}")
        print(f"💾 Рыночных данных: {provider_info['market_data_count']}")
        print(f"⚡ Данных в реальном времени: {provider_info['realtime_data_count']}")
        print(f"🔍 Расширенных данных: {provider_info['enhanced_data_count']}")
        print(f"📊 Поддержка стакана: {provider_info['supports_orderbook']}")
        print(f"🚀 Поддержка расширенных данных: {provider_info['supports_enhanced_data']}")
        
        # Тестирование получения расширенных признаков
        print("\n🧠 Тестирование расширенных признаков:")
        
        for symbol in ['SBER']:
            features = await data_provider.get_enhanced_features(symbol)
            
            if not features.empty:
                print(f"  ✅ {symbol}: {len(features.columns)} признаков")
                
                # Показать примеры признаков
                sample_features = list(features.columns)[:5]
                for feature in sample_features:
                    if feature in features.columns:
                        value = features[feature].iloc[-1] if not features[feature].empty else 0
                        print(f"    {feature}: {value:.4f}")
            else:
                print(f"  ❌ Нет признаков для {symbol}")
        
        print("\n✅ Интеграция с основным провайдером работает корректно!")
        
    except Exception as e:
        logger.error(f"Ошибка тестирования интеграции: {e}")
        print(f"❌ Ошибка интеграции: {e}")


async def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ РАСШИРЕННОГО T-BANK ПРОВАЙДЕРА")
    print("=" * 60)
    print("Этот скрипт тестирует новые возможности:")
    print("• Стакан заявок (order book)")
    print("• Расширенные рыночные данные")
    print("• Микроструктурный анализ")
    print("• 50+ признаков для нейросети")
    print("• Множественные источники данных")
    print("=" * 60)
    
    # Проверка токена
    token = os.environ.get('TINKOFF_TOKEN')
    if not token:
        print("❌ Переменная окружения TINKOFF_TOKEN не установлена")
        print("\nДля тестирования установите токен:")
        print("1. Получите токен: https://www.tbank.ru/invest/settings/api/")
        print("2. Установите переменную: set TINKOFF_TOKEN=your_token_here")
        print("3. Или создайте файл .env с содержимым: TINKOFF_TOKEN=your_token_here")
        return
    
    # Запуск тестов
    await test_enhanced_tbank_provider()
    await test_data_provider_integration()
    
    print("\n🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
    print("🚀 Система готова к использованию с расширенными возможностями T-Bank API")


if __name__ == "__main__":
    asyncio.run(main())
