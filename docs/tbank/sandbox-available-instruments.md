# Доступные инструменты в T-Bank Sandbox

## Проблема

При работе с T-Bank (Tinkoff) Invest API в режиме **sandbox** возникает ошибка:

```
ERROR 30079: Instrument is not available for trading
```

Это происходит потому, что **не все инструменты доступны для торговли в песочнице**.

## Причина

1. **Sandbox имеет ограниченный набор инструментов** по сравнению с production API
2. **Российские акции MOEX могут быть недоступны** в sandbox (SBER, GAZP, LKOH и т.д.)
3. **Статус инструмента** должен быть `SECURITY_TRADING_STATUS_NORMAL_TRADING`
4. **Флаг `api_trade_available_flag`** должен быть `true`

## Решение

### Вариант 1: Проверка доступных тикеров

Запустите скрипт для проверки доступных инструментов:

```bash
# Windows
check_tbank_tickers.bat

# Linux/Mac
python scripts/check_tbank_tickers.py
```

Скрипт покажет:
- ✅ Список всех доступных тикеров в sandbox
- ✅ Разделение на российские (RUB) и американские (USD)
- ✅ Проверку популярных тикеров
- 💡 Рекомендации по настройке

### Вариант 2: Использование американских акций

Если российские акции недоступны, используйте американские:

```yaml
# config/test_config.yaml
data:
  provider: russian  # Или tbank
  symbols:
    - AAPL   # Apple
    - MSFT   # Microsoft
    - GOOGL  # Alphabet (Google)
    - TSLA   # Tesla
    - AMZN   # Amazon
    - NVDA   # NVIDIA
    - META   # Meta (Facebook)
```

### Вариант 3: Переход на production API

Для работы с реальными российскими акциями используйте production API:

```yaml
# config/test_config.yaml
trading:
  broker: tinkoff
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}
      sandbox: false  # ⚠️ PRODUCTION режим!
      account_id: null
```

**⚠️ ВНИМАНИЕ:** В production режиме происходят реальные торговые операции!

## Автоматическая фильтрация

Система теперь **автоматически фильтрует недоступные инструменты**:

1. При инициализации брокера загружаются только доступные тикеры
2. При выполнении сигналов проверяется доступность инструмента
3. Недоступные инструменты пропускаются с предупреждением в логах

```python
# В логах вы увидите:
DEBUG | Инструмент SBER недоступен для торговли в T-Bank. Пропускаем сигнал.
```

## Методы для проверки

В коде доступны методы для проверки инструментов:

```python
# Проверка доступности тикера
if tbank_broker.is_ticker_available('AAPL'):
    print("AAPL доступна для торговли")

# Получение списка всех доступных тикеров
available = tbank_broker.get_available_tickers()
print(f"Доступно {len(available)} инструментов")
```

## Особенности Sandbox

**Sandbox T-Bank Invest API:**

- ✅ Виртуальные счета (хранятся 3 месяца)
- ✅ Бесплатное тестирование стратегий
- ✅ Упрощенный алгоритм исполнения
- ✅ Комиссия 0.05% от объема
- ❌ Ограниченный набор инструментов
- ❌ Не начисляются дивиденды и купоны
- ❌ Не все российские акции доступны

**Production API:**

- ✅ Все торгуемые инструменты MOEX
- ✅ Реальные дивиденды и купоны
- ✅ Реальный алгоритм исполнения
- ⚠️ Реальные деньги и риски!

## Проверка в коде

Система выполняет следующие проверки:

### 1. При инициализации брокера

```python
# src/trading/tbank_broker.py
if self.sandbox:
    # Для sandbox проверяем статус торговли
    if (share.api_trade_available_flag and 
        share.trading_status.name == 'SECURITY_TRADING_STATUS_NORMAL_TRADING'):
        self.instruments_cache[share.ticker] = share.figi
```

### 2. При размещении ордера

```python
# src/trading/tbank_broker.py
if not figi:
    logger.warning(
        f"Инструмент {ticker} недоступен для торговли в sandbox. "
        f"Доступно {len(self.instruments_cache)} инструментов."
    )
    return None
```

### 3. При выполнении сигнала

```python
# src/trading/trading_engine.py
if self.broker_type in ['tinkoff', 'tbank'] and self.tbank_broker:
    if not self.tbank_broker.is_ticker_available(signal.symbol):
        logger.debug(f"Инструмент {signal.symbol} недоступен. Пропускаем.")
        return
```

## Рекомендации

1. **Перед началом торговли** запустите `check_tbank_tickers.bat` для проверки доступных инструментов
2. **Обновите конфигурацию** с учетом доступных тикеров
3. **Для тестирования** используйте sandbox с американскими акциями
4. **Для реальной торговли** используйте production API с осторожностью
5. **Мониторьте логи** для отслеживания пропущенных инструментов

## Дополнительная информация

- [Официальная документация T-Bank Sandbox](https://developer.tbank.ru/invest/intro/developer/sandbox)
- [T-Bank Quick Start Guide](quick-start.md)
- [T-Bank Integration Overview](overview.md)

