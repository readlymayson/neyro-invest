# Настройка песочницы T-Bank (Tinkoff Invest API)

## Содержание

1. [Введение](#введение)
2. [Получение API токена](#получение-api-токена)
3. [Настройка окружения](#настройка-окружения)
4. [Конфигурация системы](#конфигурация-системы)
5. [Особенности песочницы](#особенности-песочницы)
6. [Использование в коде](#использование-в-коде)
7. [Примеры использования](#примеры-использования)
8. [Переход на production](#переход-на-production)
9. [Устранение проблем](#устранение-проблем)

---

## Введение

T-Bank (ранее Tinkoff) предоставляет песочницу (sandbox) для безопасного тестирования торговых роботов без риска для реальных средств.

**Документация T-Bank:** https://developer.tbank.ru/invest/intro/developer/sandbox

### Преимущества песочницы

- ✅ Бесплатное тестирование без рисков
- ✅ Полный доступ ко всем инструментам (включая для квалифицированных инвесторов)
- ✅ Виртуальные счета с тестовым капиталом
- ✅ Маржинальная торговля с плечом 2
- ✅ Реалистичные рыночные данные

### Ограничения песочницы

- ❌ Нет начисления дивидендов и купонов
- ❌ Упрощенный алгоритм исполнения ордеров
- ❌ Налоги не рассчитываются
- ❌ Счета хранятся 3 месяца с даты последнего использования

---

## Получение API токена

### Шаг 1: Регистрация в T-Bank Инвестициях

1. Откройте приложение T-Bank или сайт: https://www.tbank.ru/invest/
2. Зарегистрируйтесь или войдите в аккаунт
3. Откройте брокерский счет (если еще не открыт)

### Шаг 2: Получение токена

1. Перейдите в настройки API: https://www.tbank.ru/invest/settings/api/
2. Создайте новый токен:
   - Выберите тип токена: **"Для торговли"** или **"Только для чтения"** (для тестирования подойдет "Для торговли")
   - Нажмите "Выпустить токен"
3. **ВАЖНО:** Сохраните токен в безопасном месте! Он показывается только один раз.

### Шаг 3: Токен для песочницы

Для работы с песочницей используется тот же токен, что и для production. Режим работы (sandbox/production) определяется параметрами подключения в коде.

---

## Настройка окружения

### Установка зависимостей

```bash
# Установка библиотеки T-Bank Invest API
pip install tinkoff-investments

# Или установка всех зависимостей проекта
pip install -r requirements.txt
```

### Настройка переменных окружения

Создайте файл `.env` в корне проекта (или отредактируйте `environment.env`):

```bash
# T-Bank (Tinkoff) Invest API токен
TINKOFF_TOKEN=t.ваш_токен_здесь

# Режим песочницы (true для тестирования)
TINKOFF_SANDBOX=true

# ID счета (опционально, будет создан автоматически)
TINKOFF_ACCOUNT_ID=
```

---

## Конфигурация системы

### Настройка в YAML конфигурации

Откройте файл конфигурации (например, `config/test_config.yaml`):

```yaml
# Настройки торговли
trading:
  broker: tinkoff  # Использовать T-Bank брокер
  signal_threshold: 0.5
  max_positions: 5
  position_size: 0.05
  
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}  # Токен из переменной окружения
      sandbox: true            # ВАЖНО: true для песочницы
      account_id: null         # Будет создан автоматически
```

### Параметры конфигурации

| Параметр | Описание | Значения |
|----------|----------|----------|
| `broker` | Тип брокера | `tinkoff` или `tbank` |
| `token` | API токен | Строка или `${TINKOFF_TOKEN}` |
| `sandbox` | Режим песочницы | `true` (тест) / `false` (prod) |
| `account_id` | ID счета | `null` (создать) или конкретный ID |

---

## Особенности песочницы

### Работа со счетами

**Создание счета:**
- Счет создается автоматически при первом запуске
- Пополняется на 1,000,000 RUB по умолчанию
- Хранится 3 месяца с даты последнего использования

**Управление счетами:**
```python
from src.trading.tbank_broker import TBankBroker

# Создание брокера
broker = TBankBroker(token="your_token", sandbox=True)
await broker.initialize()  # Автоматически создаст счет

# ID созданного счета
print(f"Account ID: {broker.account_id}")
```

### Торговля в песочнице

**Исполнение ордеров:**
- **Рыночные ордеры:** Исполняются по цене последней сделки (last price)
- **Лимитные ордеры:** Исполняются, если есть встречное предложение хотя бы на 1 лот
- Ордеры не влияют на рынок (не участвуют в формировании стакана)
- Неисполненные ордеры отменяются после закрытия торговой сессии

**Комиссия:**
- 0.05% от объема сделки (независимо от инструмента)

**Маржинальная торговля:**
- Плечо 2 для всех инструментов (покупка и продажа)
- Пример: при балансе 1,000,000 ₽ можно купить активов на 2,000,000 ₽

**Фьючерсы:**
- При покупке списывается полная стоимость (не ГО)
- Вариационная маржа НЕ рассчитывается

---

## Использование в коде

### Базовый пример

```python
from src.trading.tbank_broker import TBankBroker
from src.data.tbank_data_provider import TBankDataProvider
import asyncio

async def main():
    # Получение токена из переменной окружения
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('TINKOFF_TOKEN')
    
    # Создание брокера
    broker = TBankBroker(token=token, sandbox=True)
    await broker.initialize()
    
    # Создание провайдера данных
    data_provider = TBankDataProvider(token=token, sandbox=True)
    await data_provider.initialize()
    
    # Получение текущей цены
    price = await data_provider.get_current_price('SBER')
    print(f"Текущая цена SBER: {price} ₽")
    
    # Размещение ордера
    order = await broker.place_order(
        ticker='SBER',
        quantity=10,  # 10 лотов
        direction='buy',
        order_type='market'
    )
    print(f"Ордер размещен: {order}")
    
    # Получение портфеля
    portfolio = await broker.get_portfolio()
    print(f"Портфель: {portfolio}")

if __name__ == '__main__':
    asyncio.run(main())
```

### Интеграция с торговой системой

```python
from src.core.investment_system import InvestmentSystem
import asyncio

async def main():
    # Создание системы с конфигурацией
    system = InvestmentSystem(config_path='config/test_config.yaml')
    
    # Инициализация (брокер настроится автоматически)
    await system.initialize()
    
    # Запуск торговли
    await system.start()

if __name__ == '__main__':
    asyncio.run(main())
```

---

## Примеры использования

### Пример 1: Получение исторических данных

```python
from src.data.tbank_data_provider import TBankDataProvider
import asyncio
import os

async def get_historical_data():
    token = os.getenv('TINKOFF_TOKEN')
    provider = TBankDataProvider(token=token, sandbox=True)
    await provider.initialize()
    
    # Получение данных за год
    data = await provider.get_historical_data(
        ticker='SBER',
        period='1y',
        interval='day'
    )
    
    print(f"Получено {len(data)} свечей")
    print(data.head())

asyncio.run(get_historical_data())
```

### Пример 2: Получение стакана заявок

```python
async def get_orderbook():
    token = os.getenv('TINKOFF_TOKEN')
    provider = TBankDataProvider(token=token, sandbox=True)
    await provider.initialize()
    
    # Получение стакана
    orderbook = await provider.get_orderbook(
        ticker='SBER',
        depth=10
    )
    
    print("Bid (покупка):")
    for bid in orderbook['bids'][:5]:
        print(f"  {bid['price']} ₽ x {bid['quantity']}")
    
    print("\nAsk (продажа):")
    for ask in orderbook['asks'][:5]:
        print(f"  {ask['price']} ₽ x {ask['quantity']}")

asyncio.run(get_orderbook())
```

### Пример 3: Размещение лимитного ордера

```python
async def place_limit_order():
    token = os.getenv('TINKOFF_TOKEN')
    broker = TBankBroker(token=token, sandbox=True)
    await broker.initialize()
    
    # Лимитный ордер на покупку
    order = await broker.place_order(
        ticker='SBER',
        quantity=5,
        direction='buy',
        order_type='limit',
        price=250.0  # Цена в рублях
    )
    
    print(f"Лимитный ордер размещен: {order}")
    
    # Проверка статуса ордера
    state = await broker.get_order_state(order['order_id'])
    print(f"Статус ордера: {state}")

asyncio.run(place_limit_order())
```

### Пример 4: Получение операций

```python
from datetime import datetime, timedelta

async def get_operations():
    token = os.getenv('TINKOFF_TOKEN')
    broker = TBankBroker(token=token, sandbox=True)
    await broker.initialize()
    
    # Операции за последние 30 дней
    operations = await broker.get_operations(
        from_date=datetime.now() - timedelta(days=30),
        to_date=datetime.now()
    )
    
    print(f"Найдено операций: {len(operations)}")
    for op in operations:
        print(f"{op['date']}: {op['type']} - {op['payment']} ₽")

asyncio.run(get_operations())
```

---

## Переход на production

### Шаг 1: Проверка готовности

Перед переходом на реальную торговлю убедитесь:

- ✅ Система стабильно работает в песочнице
- ✅ Стратегия показывает положительные результаты
- ✅ Риск-менеджмент настроен корректно
- ✅ Логирование работает и записывает все операции
- ✅ Вы понимаете, как работает каждая часть системы

### Шаг 2: Изменение конфигурации

В файле `.env`:
```bash
# Переключение на production
TINKOFF_SANDBOX=false
```

В YAML конфигурации:
```yaml
trading:
  broker: tinkoff
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}
      sandbox: false  # ВАЖНО: false для реальной торговли
      account_id: "ваш_реальный_account_id"  # Опционально
```

### Шаг 3: Тестовый запуск

1. Начните с малых сумм
2. Установите консервативные параметры:
   - Низкий `position_size` (например, 0.01 - 1%)
   - Высокий `signal_threshold` (например, 0.8)
   - Малое количество `max_positions` (например, 2-3)

### Шаг 4: Мониторинг

- Внимательно следите за логами
- Проверяйте каждую сделку
- Регулярно просматривайте портфель
- Анализируйте производительность

---

## Устранение проблем

### Ошибка: "T-Bank брокер недоступен"

**Причина:** Не установлена библиотека `tinkoff-investments`

**Решение:**
```bash
pip install tinkoff-investments
```

### Ошибка: "T-Bank токен не указан в конфигурации"

**Причина:** Токен не передан или не загружен из переменной окружения

**Решение:**
1. Проверьте файл `.env`:
   ```bash
   TINKOFF_TOKEN=t.ваш_токен
   ```
2. Убедитесь, что используется `${TINKOFF_TOKEN}` в YAML
3. Перезапустите приложение

### Ошибка: "FIGI не найден для тикера"

**Причина:** Тикер не найден в списке инструментов T-Bank

**Решение:**
1. Проверьте правильность написания тикера
2. Используйте поиск инструментов:
   ```python
   provider = TBankDataProvider(token=token, sandbox=True)
   await provider.initialize()
   results = await provider.search_instrument('СБЕР')
   print(results)
   ```

### Ошибка: "Количество лотов меньше 1"

**Причина:** Рассчитанное количество акций меньше 1 лота

**Решение:**
1. Увеличьте `position_size` в конфигурации
2. Увеличьте `initial_capital` для тестов
3. Выбирайте более дешевые инструменты

### Счет не найден

**Причина:** Счет в песочнице был удален (хранится 3 месяца)

**Решение:**
1. Установите `account_id: null` в конфигурации
2. Перезапустите систему - счет создастся автоматически

### Медленное выполнение запросов

**Причина:** Сетевые задержки или ограничения API

**Решение:**
1. Используйте кэширование данных
2. Увеличьте интервалы обновления
3. Используйте batch-запросы где возможно
4. Рассмотрите использование websocket-стримов для real-time данных

---

## Полезные ссылки

- **Документация T-Bank Invest API:** https://developer.tbank.ru/invest/
- **Песочница:** https://developer.tbank.ru/invest/intro/developer/sandbox
- **Получение токена:** https://www.tbank.ru/invest/settings/api/
- **GitHub библиотеки:** https://github.com/Tinkoff/invest-python
- **Telegram-канал разработчиков:** https://t.me/tinkoffinvestopenapi

---

## Заключение

Песочница T-Bank - это безопасная среда для тестирования торговых стратегий. Используйте её для:

1. **Разработки:** Отладка логики торговой системы
2. **Тестирования:** Проверка стратегий на исторических и текущих данных
3. **Обучения:** Изучение API без рисков

**Важно:** Никогда не переходите на production без тщательного тестирования в песочнице!

---

*Документация обновлена: 2025-10-22*


