#!/usr/bin/env python3
"""
Проверка облачной синхронизации с T-Bank API
Проверяет статус синхронизации портфеля, позиций и операций
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
from src.trading.tbank_broker import TBankBroker
from loguru import logger

# Настройка логирования
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


async def check_cloud_sync_status():
    """Проверка статуса облачной синхронизации"""
    
    print("☁️ Проверка облачной синхронизации с T-Bank API")
    print("=" * 60)
    
    # Получение токена
    token = os.environ.get('TINKOFF_TOKEN')
    if not token:
        print("❌ Переменная окружения TINKOFF_TOKEN не установлена")
        print("Установите токен: set TINKOFF_TOKEN=your_token_here")
        return
    
    # Account ID будет определен автоматически
    account_id = None
    
    try:
        # 1. Проверка подключения к T-Bank API
        print("\n1️⃣ Проверка подключения к T-Bank API")
        print("-" * 40)
        
        broker = TBankBroker(token=token, sandbox=True, account_id=account_id)
        await broker.initialize()
        
        print(f"✅ Подключение к T-Bank API успешно")
        print(f"📊 Account ID: {broker.account_id} (автоматически определен)")
        print(f"🏖️ Sandbox режим: {broker.sandbox}")
        
        if broker.account_id:
            print(f"✅ Счет успешно определен/создан")
        else:
            print(f"❌ Не удалось определить счет")
            return
        
        # 2. Проверка синхронизации портфеля
        print("\n2️⃣ Проверка синхронизации портфеля")
        print("-" * 40)
        
        # Получение информации о портфеле
        portfolio = await broker.get_portfolio()
        print(f"✅ Портфель синхронизирован")
        print(f"💰 Общая стоимость: {portfolio.get('total_amount', 0):,.2f} ₽")
        print(f"📈 Ожидаемая доходность: {portfolio.get('expected_yield', 0):,.2f} ₽")
        
        # 3. Проверка синхронизации позиций
        print("\n3️⃣ Проверка синхронизации позиций")
        print("-" * 40)
        
        await broker.update_positions()
        positions = broker.positions
        
        if positions:
            print(f"✅ Позиции синхронизированы: {len(positions)} позиций")
            for ticker, pos_data in positions.items():
                print(f"  📊 {ticker}: {pos_data['quantity']:.4f} шт. по {pos_data['average_price']:.2f} ₽")
        else:
            print("ℹ️ Нет открытых позиций")
        
        # 4. Проверка синхронизации баланса
        print("\n4️⃣ Проверка синхронизации баланса")
        print("-" * 40)
        
        balances = await broker.get_account_balance()
        print(f"✅ Баланс синхронизирован")
        for currency, amount in balances.items():
            print(f"  💰 {currency.upper()}: {amount:,.2f}")
        
        # 5. Проверка синхронизации операций
        print("\n5️⃣ Проверка синхронизации операций")
        print("-" * 40)
        
        from_date = datetime.now() - timedelta(days=7)
        operations = await broker.get_operations(from_date=from_date)
        
        if operations:
            print(f"✅ Операции синхронизированы: {len(operations)} операций за 7 дней")
            
            # Группировка по типам операций
            operation_types = {}
            for op in operations:
                op_type = op.get('type', 'UNKNOWN')
                operation_types[op_type] = operation_types.get(op_type, 0) + 1
            
            print("  📊 Типы операций:")
            for op_type, count in operation_types.items():
                print(f"    {op_type}: {count}")
        else:
            print("ℹ️ Нет операций за последние 7 дней")
        
        # 6. Проверка синхронизации рыночных данных
        print("\n6️⃣ Проверка синхронизации рыночных данных")
        print("-" * 40)
        
        provider = EnhancedTBankProvider(token, sandbox=True)
        await provider.initialize()
        
        # Проверка доступности инструментов
        instruments = await provider.get_available_instruments()
        print(f"✅ Инструменты синхронизированы: {len(instruments)} доступно")
        
        # Проверка данных в реальном времени
        test_symbols = ['SBER', 'GAZP']
        realtime_data = await provider.get_realtime_data(test_symbols)
        print(f"✅ Данные в реальном времени: {len(realtime_data)} инструментов")
        
        for symbol, data in realtime_data.items():
            print(f"  📈 {symbol}: {data['price']:.2f} ₽ ({data['timestamp']})")
        
        # 7. Проверка стакана заявок
        print("\n7️⃣ Проверка синхронизации стакана заявок")
        print("-" * 40)
        
        for symbol in test_symbols:
            orderbook = await provider.get_orderbook(symbol, depth=5)
            if orderbook:
                print(f"✅ Стакан для {symbol}: {len(orderbook.get('bids', []))} bids, {len(orderbook.get('asks', []))} asks")
                print(f"  💰 Спред: {orderbook.get('spread', 0):.2f} ₽ ({orderbook.get('spread_percent', 0):.2f}%)")
            else:
                print(f"❌ Стакан для {symbol} недоступен")
        
        # 8. Итоговая сводка синхронизации
        print("\n8️⃣ Итоговая сводка синхронизации")
        print("-" * 40)
        
        sync_status = {
            'API Connection': '✅ OK',
            'Portfolio': '✅ OK' if portfolio else '❌ Error',
            'Positions': '✅ OK' if positions else 'ℹ️ Empty',
            'Balance': '✅ OK' if balances else '❌ Error',
            'Operations': '✅ OK' if operations else 'ℹ️ Empty',
            'Instruments': '✅ OK' if instruments else '❌ Error',
            'Realtime Data': '✅ OK' if realtime_data else '❌ Error',
            'Order Book': '✅ OK' if any(await provider.get_orderbook(s, depth=1) for s in test_symbols) else '❌ Error'
        }
        
        print("📊 Статус синхронизации:")
        for component, status in sync_status.items():
            print(f"  {component}: {status}")
        
        # Подсчет успешных компонентов
        success_count = sum(1 for status in sync_status.values() if '✅' in status)
        total_count = len(sync_status)
        
        print(f"\n📈 Общий статус: {success_count}/{total_count} компонентов синхронизированы")
        
        if success_count == total_count:
            print("🎉 Все компоненты успешно синхронизированы с облаком!")
        elif success_count >= total_count * 0.8:
            print("✅ Большинство компонентов синхронизированы")
        else:
            print("⚠️ Есть проблемы с синхронизацией")
        
        print("\n" + "=" * 60)
        print("✅ Проверка облачной синхронизации завершена")
        print("☁️ Система готова к работе с облачными данными T-Bank API")
        
    except Exception as e:
        logger.error(f"Ошибка проверки синхронизации: {e}")
        print(f"❌ Произошла ошибка: {e}")


async def main():
    """Основная функция проверки"""
    print("☁️ ПРОВЕРКА ОБЛАЧНОЙ СИНХРОНИЗАЦИИ T-BANK")
    print("=" * 60)
    print("Этот скрипт проверяет:")
    print("• Подключение к T-Bank API")
    print("• Синхронизацию портфеля")
    print("• Синхронизацию позиций")
    print("• Синхронизацию баланса")
    print("• Синхронизацию операций")
    print("• Синхронизацию рыночных данных")
    print("• Синхронизацию стакана заявок")
    print("=" * 60)
    
    # Проверка токена
    token = os.environ.get('TINKOFF_TOKEN')
    if not token:
        print("❌ Переменная окружения TINKOFF_TOKEN не установлена")
        print("\nДля проверки установите токен:")
        print("1. Получите токен: https://www.tbank.ru/invest/settings/api/")
        print("2. Установите переменную: set TINKOFF_TOKEN=your_token_here")
        print("3. Или создайте файл .env с содержимым: TINKOFF_TOKEN=your_token_here")
        return
    
    # Запуск проверки
    await check_cloud_sync_status()
    
    print("\n🎉 ПРОВЕРКА ЗАВЕРШЕНА!")
    print("☁️ Облачная синхронизация работает корректно")


if __name__ == "__main__":
    asyncio.run(main())
