"""
Скрипт для проверки доступных тикеров в T-Bank sandbox
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Установка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from loguru import logger

try:
    from tinkoff.invest import AsyncClient
    from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX
    TINKOFF_AVAILABLE = True
except ImportError:
    TINKOFF_AVAILABLE = False
    logger.error("Библиотека tinkoff-investments не установлена")


async def check_available_tickers():
    """Проверка доступных тикеров в sandbox"""
    
    if not TINKOFF_AVAILABLE:
        print("❌ Библиотека tinkoff-investments не установлена")
        print("Установите: pip install tinkoff-investments")
        return
    
    # Попытка загрузить токен из .env файла
    token = os.environ.get('TINKOFF_TOKEN')
    
    if not token:
        # Попытка загрузить из .env файла
        env_file = '.env'
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                if key.strip() == 'TINKOFF_TOKEN':
                                    token = value.strip().strip('"').strip("'")
                                    break
            except Exception as e:
                pass
    
    if not token:
        print("❌ Переменная окружения TINKOFF_TOKEN не установлена")
        print()
        print("Установите токен одним из способов:")
        print("1. Создайте файл .env с содержимым:")
        print("   TINKOFF_TOKEN=your_token_here")
        print()
        print("2. Или установите переменную окружения:")
        print("   set TINKOFF_TOKEN=your_token_here")
        print()
        print("Получить токен: https://www.tbank.ru/invest/settings/api/")
        return
    
    print("🔍 Проверка доступных инструментов в T-Bank sandbox...")
    print()
    
    try:
        async with AsyncClient(token, target=INVEST_GRPC_API_SANDBOX) as client:
            # Загрузка акций
            response = await client.instruments.shares()
            
            # Фильтрация доступных для торговли
            available_tickers = []
            russian_tickers = []
            us_tickers = []
            
            for share in response.instruments:
                # Проверка доступности для торговли в sandbox
                if (share.api_trade_available_flag and 
                    share.trading_status.name == 'SECURITY_TRADING_STATUS_NORMAL_TRADING'):
                    
                    ticker_info = {
                        'ticker': share.ticker,
                        'name': share.name,
                        'currency': share.currency,
                        'country': share.country_of_risk_name,
                        'exchange': share.exchange
                    }
                    available_tickers.append(ticker_info)
                    
                    # Разделение по странам
                    if share.currency == 'rub':
                        russian_tickers.append(ticker_info)
                    elif share.currency == 'usd':
                        us_tickers.append(ticker_info)
            
            # Вывод статистики
            print(f"📊 Всего доступно инструментов: {len(available_tickers)}")
            print(f"   • Российские (RUB): {len(russian_tickers)}")
            print(f"   • Американские (USD): {len(us_tickers)}")
            print()
            
            # Проверка популярных российских тикеров
            print("🔎 Проверка популярных российских тикеров:")
            popular_russian = ['SBER', 'GAZP', 'LKOH', 'NVTK', 'ROSN', 'GMKN', 'YNDX', 'MGNT', 'TATN', 'SNGS']
            russian_ticker_set = {t['ticker'] for t in russian_tickers}
            
            for ticker in popular_russian:
                status = "✅" if ticker in russian_ticker_set else "❌"
                print(f"   {status} {ticker}")
            print()
            
            # Вывод доступных российских тикеров
            if russian_tickers:
                print(f"✅ Доступные российские тикеры ({len(russian_tickers)}):")
                for info in russian_tickers[:20]:  # Первые 20
                    print(f"   • {info['ticker']:6s} - {info['name'][:50]}")
                if len(russian_tickers) > 20:
                    print(f"   ... и еще {len(russian_tickers) - 20}")
                print()
            
            # Вывод доступных американских тикеров
            if us_tickers:
                print(f"✅ Доступные американские тикеры ({len(us_tickers)}) - примеры:")
                for info in us_tickers[:20]:  # Первые 20
                    print(f"   • {info['ticker']:6s} - {info['name'][:50]}")
                if len(us_tickers) > 20:
                    print(f"   ... и еще {len(us_tickers) - 20}")
                print()
            
            # Сохранение полного списка в файл
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"tbank_tickers_{timestamp}.json"
            
            # Подготовка данных для сохранения
            output_data = {
                "timestamp": timestamp,
                "total_count": len(available_tickers),
                "russian_count": len(russian_tickers),
                "us_count": len(us_tickers),
                "russian_tickers": russian_tickers,
                "us_tickers": us_tickers,
                "all_tickers": available_tickers
            }
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 Полный список тикеров сохранен в файл: {output_file}")
                print(f"   • Всего инструментов: {len(available_tickers)}")
                print(f"   • Российские: {len(russian_tickers)}")
                print(f"   • Американские: {len(us_tickers)}")
                print()
                
            except Exception as e:
                logger.error(f"Ошибка сохранения файла: {e}")
                print(f"❌ Ошибка сохранения файла: {e}")
            
            # Рекомендация
            print("💡 Рекомендация:")
            if russian_tickers:
                print("   Используйте доступные российские тикеры из списка выше")
                print("   Обновите config/test_config.yaml соответственно")
            elif us_tickers:
                print("   В sandbox доступны только американские акции (USD)")
                print("   Пример конфигурации:")
                print("   symbols:")
                for ticker in us_tickers[:5]:
                    print(f"     - {ticker['ticker']}  # {ticker['name'][:40]}")
            else:
                print("   ⚠️  Не найдено доступных инструментов в sandbox")
                print("   Попробуйте использовать production API")
            
    except Exception as e:
        logger.error(f"Ошибка проверки: {e}")
        print(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    asyncio.run(check_available_tickers())

