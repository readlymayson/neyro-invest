# Инициализация системы

## Обзор

Система использует надежную инициализацию компонентов с обработкой ошибок. Все компоненты инициализируются независимо, и система продолжает работу даже при частичных ошибках.

## Процесс инициализации

### 1. Инициализация провайдера данных

```python
try:
    await self.data_provider.initialize()
    logger.info("✅ Провайдер данных инициализирован")
except Exception as e:
    error_msg = f"Ошибка инициализации провайдера данных: {e}"
    logger.error(error_msg)
    initialization_errors.append(error_msg)
```

**Что инициализируется:**
- Подключение к источникам данных
- Загрузка исторических данных
- Настройка провайдера новостей (если включен)

### 2. Инициализация менеджера нейросетей

```python
try:
    await self.network_manager.initialize()
    logger.info("✅ Менеджер нейросетей инициализирован")
except Exception as e:
    error_msg = f"Ошибка инициализации менеджера нейросетей: {e}"
    logger.error(error_msg)
    initialization_errors.append(error_msg)
```

**Что инициализируется:**
- Инициализация всех моделей (XGBoost, DeepSeek)
- Загрузка обученных моделей (если есть)
- Настройка API для DeepSeek (если используется)

### 3. Инициализация торгового движка

```python
try:
    await self.trading_engine.initialize()
    logger.info("✅ Торговый движок инициализирован")
    
    # Проверка успешной инициализации брокера для T-Bank
    if self.trading_engine.broker_type in ['tinkoff', 'tbank']:
        if not hasattr(self.trading_engine, 'tbank_broker') or not self.trading_engine.tbank_broker:
            warning_msg = "T-Bank брокер не инициализирован, будет использован режим paper trading"
            logger.warning(warning_msg)
            initialization_errors.append(warning_msg)
except Exception as e:
    error_msg = f"Ошибка инициализации торгового движка: {e}"
    logger.error(error_msg)
    initialization_errors.append(error_msg)
```

**Что инициализируется:**
- Подключение к брокеру (T-Bank, Paper Trading)
- Проверка доступности API
- Настройка торговых параметров

### 4. Установка списка символов

```python
symbols = self.config['data'].get('symbols', [])
if symbols:
    self.trading_engine.set_symbols(symbols)
else:
    warning_msg = "Список символов пуст в конфигурации"
    logger.warning(warning_msg)
    initialization_errors.append(warning_msg)
```

**Что проверяется:**
- Наличие символов в конфигурации
- Установка символов в торговый движок

### 5. Инициализация менеджера портфеля

```python
try:
    await self.portfolio_manager.initialize()
    logger.info("✅ Менеджер портфеля инициализирован")
except Exception as e:
    error_msg = f"Ошибка инициализации менеджера портфеля: {e}"
    logger.error(error_msg)
    initialization_errors.append(error_msg)
```

**Что инициализируется:**
- Загрузка начального капитала
- Настройка параметров риска
- Инициализация структуры портфеля

### 6. Синхронизация с T-Bank

```python
if hasattr(self.trading_engine, 'tbank_broker') and self.trading_engine.tbank_broker:
    self.portfolio_manager.set_tbank_broker(self.trading_engine.tbank_broker)
    # Синхронизация с T-Bank при инициализации
    try:
        sync_result = await self.portfolio_manager.sync_with_tbank()
        if not sync_result:
            warning_msg = "Не удалось синхронизироваться с T-Bank при инициализации"
            logger.warning(warning_msg)
            initialization_errors.append(warning_msg)
    except Exception as e:
        warning_msg = f"Ошибка синхронизации с T-Bank: {e}"
        logger.warning(warning_msg)
        initialization_errors.append(warning_msg)
```

**Что синхронизируется:**
- Баланс счета
- Текущие позиции
- История операций

## Обработка ошибок

### Сбор ошибок

Все ошибки и предупреждения собираются в список `initialization_errors`:

```python
initialization_errors = []
```

### Итоговый отчет

После инициализации всех компонентов система выводит итоговый отчет:

```python
if initialization_errors:
    logger.warning(f"Инициализация завершена с предупреждениями: {len(initialization_errors)} проблем")
    for error in initialization_errors:
        logger.warning(f"  - {error}")
else:
    logger.info("✅ Все компоненты успешно инициализированы")
```

## Типы ошибок

### Критические ошибки (ERROR)
- Ошибки инициализации основных компонентов
- Отсутствие обязательных конфигураций
- Недоступность критических API

### Предупреждения (WARNING)
- Неудачная синхронизация с T-Bank (система продолжит работу в paper режиме)
- Отсутствие символов в конфигурации
- Отсутствие API ключей (система будет работать без соответствующих функций)

## Поведение системы при ошибках

### Частичная инициализация

Система продолжает работу даже при частичных ошибках:

- ✅ **Провайдер данных не инициализирован** → Система не сможет обновлять данные, но может работать с существующими
- ✅ **Менеджер нейросетей не инициализирован** → Торговля будет работать без анализа нейросетями
- ✅ **T-Bank брокер не инициализирован** → Система автоматически переключится на paper trading
- ✅ **Менеджер портфеля не инициализирован** → Торговля будет работать с ограниченной функциональностью

### Автоматические fallback'и

- **T-Bank недоступен** → Paper Trading
- **DeepSeek API недоступен** → Работа только с XGBoost
- **Новостной провайдер недоступен** → Работа без новостных данных

## Рекомендации

### При запуске проверьте:

1. **Статус инициализации:**
   ```
   neyro-invest> status
   ```

2. **Логи инициализации:**
   - Проверьте файл `logs/investment_system.log`
   - Ищите сообщения с `✅` для успешной инициализации
   - Ищите сообщения с `❌` или `⚠️` для проблем

3. **Критичные компоненты:**
   - Провайдер данных должен быть инициализирован
   - Минимум одна нейросеть должна быть обучена
   - Торговый движок должен быть инициализирован (даже в paper режиме)

### Типичные проблемы

#### T-Bank не инициализирован
**Причина:** Отсутствует или неверный токен
**Решение:** 
- Проверьте переменную окружения `TINKOFF_TOKEN`
- Проверьте настройки в `config/main.yaml`
- Система автоматически использует paper trading

#### DeepSeek не инициализирован
**Причина:** Отсутствует API ключ
**Решение:**
- Проверьте переменную окружения `DEEPSEEK_API_KEY`
- Система продолжит работу только с XGBoost

#### Нет символов в конфигурации
**Причина:** Пустой список `symbols` в конфигурации
**Решение:**
- Добавьте символы в `config/main.yaml`
- Например: `symbols: [SBER, GAZP, LKOH]`

