# T-Bank API - Шпаргалка

## 🚀 Быстрый старт (3 команды)

```bash
pip install tinkoff-investments
echo "TINKOFF_TOKEN=t.ваш_токен" > .env
python examples/tbank_sandbox_test.py
```

## 🔑 Получение токена

**URL:** https://www.tbank.ru/invest/settings/api/

1. Войти в T-Bank Инвестиции
2. Настройки → API
3. "Выпустить токен"
4. Скопировать (показывается один раз!)

## 📝 Настройка .env

```bash
TINKOFF_TOKEN=t.ваш_токен_здесь
TINKOFF_SANDBOX=true
```

## ⚙️ Конфигурация (YAML)

```yaml
trading:
  broker: tinkoff
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}
      sandbox: true          # false для реальной торговли
      account_id: null       # Создастся автоматически
```

## 💻 Код: Провайдер данных

```python
from src.data.tbank_data_provider import TBankDataProvider
import asyncio, os

async def main():
    provider = TBankDataProvider(
        token=os.getenv('TINKOFF_TOKEN'),
        sandbox=True
    )
    await provider.initialize()
    
    # Текущая цена
    price = await provider.get_current_price('SBER')
    
    # Исторические данные
    data = await provider.get_historical_data(
        ticker='SBER',
        period='1mo',    # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y
        interval='day'   # 1min, 5min, 15min, hour, day
    )
    
    # Стакан заявок
    orderbook = await provider.get_orderbook('SBER', depth=10)

asyncio.run(main())
```

## 💼 Код: Брокер

```python
from src.trading.tbank_broker import TBankBroker
import asyncio, os

async def main():
    broker = TBankBroker(
        token=os.getenv('TINKOFF_TOKEN'),
        sandbox=True
    )
    await broker.initialize()
    
    # Портфель
    portfolio = await broker.get_portfolio()
    
    # Размещение ордера
    order = await broker.place_order(
        ticker='SBER',
        quantity=1,             # Лоты
        direction='buy',        # 'buy' или 'sell'
        order_type='market',    # 'market' или 'limit'
        price=250.0             # Только для limit
    )
    
    # Статус ордера
    state = await broker.get_order_state(order['order_id'])
    
    # Отмена ордера
    await broker.cancel_order(order['order_id'])

asyncio.run(main())
```

## 🎯 Запуск системы

```bash
# С конфигурацией
python run.py --config config/test_config.yaml

# Выбор конфигурации
python run.py --select-config

# GUI
python gui_launcher.py
```

## 🧪 Тестирование

```bash
# Полный тест
python examples/tbank_sandbox_test.py

# Windows
test_tbank_sandbox.bat

# Linux/macOS
./test_tbank_sandbox.sh
```

## ✅ Проверки

```bash
# Библиотека установлена?
python -c "import tinkoff.invest; print('✅ OK')"

# Токен настроен?
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TINKOFF_TOKEN')[:10] if os.getenv('TINKOFF_TOKEN') else '❌')"
```

## 📊 Особенности песочницы

| Параметр | Значение |
|----------|----------|
| Начальный капитал | 1,000,000 ₽ |
| Комиссия | 0.05% фиксированная |
| Плечо | 2 (все инструменты) |
| Срок хранения счета | 3 месяца |
| Дивиденды | ❌ Нет |
| Купоны | ❌ Нет |
| Налоги | ❌ Нет |

## 🔧 Основные методы

### TBankDataProvider

| Метод | Описание |
|-------|----------|
| `initialize()` | Инициализация, загрузка инструментов |
| `get_current_price(ticker)` | Текущая цена |
| `get_historical_data(ticker, period, interval)` | История (свечи) |
| `get_realtime_data(tickers)` | Real-time данные |
| `get_orderbook(ticker, depth)` | Стакан заявок |
| `search_instrument(query)` | Поиск инструментов |

### TBankBroker

| Метод | Описание |
|-------|----------|
| `initialize()` | Инициализация, создание счета |
| `place_order(...)` | Размещение ордера |
| `cancel_order(order_id)` | Отмена ордера |
| `get_order_state(order_id)` | Статус ордера |
| `get_portfolio()` | Получение портфеля |
| `get_operations(from, to)` | История операций |
| `close_sandbox_account()` | Закрытие sandbox счета |

## ⚠️ Частые ошибки

| Ошибка | Решение |
|--------|---------|
| "No module named 'tinkoff'" | `pip install tinkoff-investments` |
| "Token not found" | Проверить `.env` файл |
| "Invalid token" | Создать новый токен |
| "FIGI not found" | Проверить тикер (должен быть верным) |
| "Lots < 1" | Увеличить `position_size` |

## 🔗 Быстрые ссылки

| Ресурс | URL |
|--------|-----|
| Получить токен | https://www.tbank.ru/invest/settings/api/ |
| Документация API | https://developer.tbank.ru/invest/ |
| Песочница | https://developer.tbank.ru/invest/intro/developer/sandbox |
| Telegram | https://t.me/tinkoffinvestopenapi |
| GitHub | https://github.com/Tinkoff/invest-python |

## 📚 Документация проекта

| Документ | Описание |
|----------|----------|
| [START_HERE_TBANK.md](START_HERE_TBANK.md) | С чего начать |
| [QUICK_START_TBANK.md](QUICK_START_TBANK.md) | Быстрый старт (5 мин) |
| [INSTALL_TBANK.md](INSTALL_TBANK.md) | Установка |
| [docs/TBANK_SANDBOX_SETUP.md](docs/TBANK_SANDBOX_SETUP.md) | Полное руководство |

## 🎯 Переход на production

```yaml
# В конфигурации измените:
trading:
  broker_settings:
    tinkoff:
      sandbox: false  # ⚠️ Реальные деньги!
```

**⚠️ НЕ ПЕРЕХОДИТЕ БЕЗ ТЕСТИРОВАНИЯ!**

Чеклист:
- [ ] Протестировано в sandbox ≥ 1 месяц
- [ ] Стратегия прибыльная
- [ ] Понимаете весь код
- [ ] Настроен риск-менеджмент
- [ ] Готовы к потерям
- [ ] Начинаете с малых сумм

## 💡 Полезные команды

```bash
# Установка всего
pip install -r requirements.txt

# Проверка конфигурации
python scripts/validate_config.py config/test_config.yaml

# Смена конфигурации
python change_config.py

# Статус системы
python run.py --status
```

---

**Создано:** 22.10.2025  
**Версия:** 1.0.0  
**Полная документация:** [docs/TBANK_SANDBOX_SETUP.md](docs/TBANK_SANDBOX_SETUP.md)

