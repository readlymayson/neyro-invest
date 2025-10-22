"""
Пример использования песочницы T-Bank (Tinkoff Invest API)
Этот скрипт демонстрирует основные возможности работы с песочницей
"""

import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

# Загрузка переменных окружения
load_dotenv()

# Добавление путей для импорта
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.tbank_data_provider import TBankDataProvider
from src.trading.tbank_broker import TBankBroker


async def test_data_provider():
    """Тест провайдера данных"""
    print("\n" + "="*80)
    print("ТЕСТ ПРОВАЙДЕРА ДАННЫХ T-BANK")
    print("="*80)
    
    token = os.getenv('TINKOFF_TOKEN')
    if not token:
        print("❌ ОШИБКА: Токен TINKOFF_TOKEN не найден в переменных окружения")
        print("   Создайте файл .env и добавьте: TINKOFF_TOKEN=ваш_токен")
        return
    
    try:
        # Создание провайдера
        provider = TBankDataProvider(token=token, sandbox=True)
        print("✅ Провайдер создан")
        
        # Инициализация
        await provider.initialize()
        print(f"✅ Провайдер инициализирован: {provider.get_status()}")
        
        # Поиск инструмента
        print("\n📊 Поиск инструмента 'SBER'...")
        instruments = await provider.search_instrument('SBER')
        if instruments:
            print(f"   Найдено инструментов: {len(instruments)}")
            for inst in instruments[:3]:
                print(f"   - {inst['ticker']}: {inst['name']} ({inst['figi']})")
        
        # Получение текущей цены
        print("\n💰 Получение текущей цены SBER...")
        price = await provider.get_current_price('SBER')
        print(f"   Текущая цена: {price:.2f} ₽")
        
        # Получение исторических данных
        print("\n📈 Получение исторических данных (последние 30 дней)...")
        data = await provider.get_historical_data('SBER', period='1mo', interval='day')
        if not data.empty:
            print(f"   Получено свечей: {len(data)}")
            print(f"   Последняя свеча:")
            last = data.iloc[-1]
            print(f"     Open: {last['Open']:.2f} ₽")
            print(f"     High: {last['High']:.2f} ₽")
            print(f"     Low:  {last['Low']:.2f} ₽")
            print(f"     Close: {last['Close']:.2f} ₽")
            print(f"     Volume: {int(last['Volume']):,}")
        
        # Получение стакана заявок
        print("\n📊 Получение стакана заявок...")
        orderbook = await provider.get_orderbook('SBER', depth=5)
        if orderbook:
            print("   BID (покупка):")
            for bid in orderbook['bids'][:5]:
                print(f"     {bid['price']:.2f} ₽ x {bid['quantity']}")
            print("   ASK (продажа):")
            for ask in orderbook['asks'][:5]:
                print(f"     {ask['price']:.2f} ₽ x {ask['quantity']}")
        
        print("\n✅ Тест провайдера данных завершен успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка в тесте провайдера: {e}")
        logger.exception(e)


async def test_broker():
    """Тест брокера"""
    print("\n" + "="*80)
    print("ТЕСТ БРОКЕРА T-BANK SANDBOX")
    print("="*80)
    
    token = os.getenv('TINKOFF_TOKEN')
    if not token:
        print("❌ ОШИБКА: Токен TINKOFF_TOKEN не найден в переменных окружения")
        return
    
    try:
        # Создание брокера
        broker = TBankBroker(token=token, sandbox=True)
        print("✅ Брокер создан")
        
        # Инициализация
        await broker.initialize()
        status = broker.get_status()
        print(f"✅ Брокер инициализирован:")
        print(f"   Режим: {status['mode']}")
        print(f"   Account ID: {status['account_id']}")
        print(f"   Инструментов загружено: {status['instruments_loaded']}")
        
        # Получение портфеля
        print("\n💼 Получение портфеля...")
        portfolio = await broker.get_portfolio()
        print(f"   Общая стоимость: {portfolio['total_amount']:.2f} ₽")
        print(f"   Ожидаемая доходность: {portfolio['expected_yield']:.2f} ₽")
        print(f"   Позиций: {len(portfolio['positions'])}")
        
        if portfolio['positions']:
            print("\n   Текущие позиции:")
            for pos in portfolio['positions'][:5]:
                print(f"     {pos['ticker']}: {pos['quantity']} шт @ {pos['average_price']:.2f} ₽")
        
        # Тестовое размещение рыночного ордера (ЗАКОММЕНТИРОВАНО для безопасности)
        # Раскомментируйте, если хотите протестировать размещение ордеров
        
        # print("\n📝 Размещение тестового ордера на покупку 1 лота SBER...")
        # order = await broker.place_order(
        #     ticker='SBER',
        #     quantity=1,
        #     direction='buy',
        #     order_type='market'
        # )
        # if order:
        #     print(f"✅ Ордер размещен:")
        #     print(f"   Order ID: {order['order_id']}")
        #     print(f"   Ticker: {order['ticker']}")
        #     print(f"   Direction: {order['direction']}")
        #     print(f"   Quantity: {order['quantity']}")
        #     print(f"   Status: {order['status']}")
        #     
        #     # Проверка статуса ордера
        #     await asyncio.sleep(2)  # Ждем исполнения
        #     state = await broker.get_order_state(order['order_id'])
        #     if state:
        #         print(f"\n   Статус ордера:")
        #         print(f"     Execution status: {state['execution_status']}")
        #         print(f"     Lots executed: {state['lots_executed']}")
        #         print(f"     Executed price: {state['executed_price']:.2f} ₽")
        
        # Получение операций
        print("\n📋 Получение последних операций...")
        from datetime import datetime, timedelta
        operations = await broker.get_operations(
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now()
        )
        print(f"   Найдено операций за последние 30 дней: {len(operations)}")
        
        if operations:
            print("\n   Последние операции:")
            for op in operations[-5:]:
                print(f"     {op['date']}: {op['type']} - {op['payment']:.2f} ₽")
        
        print("\n✅ Тест брокера завершен успешно!")
        
        # Закрытие счета (ЗАКОММЕНТИРОВАНО для безопасности)
        # print("\n🗑️  Закрытие sandbox счета...")
        # await broker.close_sandbox_account()
        # print("✅ Счет закрыт")
        
    except Exception as e:
        print(f"\n❌ Ошибка в тесте брокера: {e}")
        logger.exception(e)


async def main():
    """Главная функция"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "T-BANK SANDBOX TEST" + " "*39 + "║")
    print("║" + " "*15 + "Тестирование песочницы T-Bank API" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    
    # Проверка токена
    token = os.getenv('TINKOFF_TOKEN')
    if not token:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Токен TINKOFF_TOKEN не найден!")
        print("\nИнструкции по получению токена:")
        print("1. Перейдите на https://www.tbank.ru/invest/settings/api/")
        print("2. Создайте новый токен")
        print("3. Добавьте его в файл .env:")
        print("   TINKOFF_TOKEN=t.ваш_токен_здесь")
        print("\n📖 Подробная документация: docs/TBANK_SANDBOX_SETUP.md")
        return
    
    print(f"\n✅ Токен найден: {token[:10]}...{token[-5:]}")
    
    # Запуск тестов
    try:
        # Тест 1: Провайдер данных
        await test_data_provider()
        
        # Задержка между тестами
        await asyncio.sleep(2)
        
        # Тест 2: Брокер
        await test_broker()
        
        print("\n" + "="*80)
        print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
        print("="*80)
        print("\n📖 Для получения дополнительной информации см. docs/TBANK_SANDBOX_SETUP.md")
        print()
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ТЕСТЫ ЗАВЕРШЕНЫ С ОШИБКАМИ")
        print("="*80)
        print(f"\nОшибка: {e}")
        logger.exception(e)
        print("\n📖 См. документацию: docs/TBANK_SANDBOX_SETUP.md")
        print()


if __name__ == '__main__':
    # Настройка логирования
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="WARNING"  # Показываем только предупреждения и ошибки
    )
    
    # Запуск тестов
    asyncio.run(main())


