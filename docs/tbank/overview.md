# T-Bank (Tinkoff Invest API) - Документация

## 📚 Полный список документации

### Для начинающих

1. **[QUICK_START_TBANK.md](../QUICK_START_TBANK.md)** - Быстрый старт за 5 минут ⭐
2. **[INSTALL_TBANK.md](../INSTALL_TBANK.md)** - Подробная инструкция по установке

### Подробная документация

3. **[TBANK_SANDBOX_SETUP.md](TBANK_SANDBOX_SETUP.md)** - Полное руководство по песочнице (60+ страниц) 📖

### Техническая документация

4. **[TBANK_INTEGRATION_SUMMARY.md](../TBANK_INTEGRATION_SUMMARY.md)** - Технический обзор интеграции

### Примеры

5. **[examples/tbank_sandbox_test.py](../examples/tbank_sandbox_test.py)** - Тестовый скрипт
6. **[examples/README.md](../examples/README.md)** - Описание примеров

---

## 🚀 Рекомендуемый путь обучения

### Шаг 1: Установка (5 минут)

Прочитайте: **[INSTALL_TBANK.md](../INSTALL_TBANK.md)**

Сделайте:
```bash
pip install tinkoff-investments
echo "TINKOFF_TOKEN=t.ваш_токен" > .env
python examples/tbank_sandbox_test.py
```

### Шаг 2: Быстрый старт (10 минут)

Прочитайте: **[QUICK_START_TBANK.md](../QUICK_START_TBANK.md)**

Сделайте:
```bash
# Настройте config/test_config.yaml
python run.py --config config/test_config.yaml
```

### Шаг 3: Изучение песочницы (30 минут)

Прочитайте: **[TBANK_SANDBOX_SETUP.md](TBANK_SANDBOX_SETUP.md)**

Разделы для изучения:
- Особенности песочницы
- Примеры использования
- Устранение проблем

### Шаг 4: Практика (1-2 часа)

Изучите и запустите примеры:
- `examples/tbank_sandbox_test.py`
- Создайте свои примеры
- Протестируйте разные стратегии

### Шаг 5: Переход на production (когда готовы)

Прочитайте раздел "Переход на production" в **[TBANK_SANDBOX_SETUP.md](TBANK_SANDBOX_SETUP.md)**

**⚠️ ВАЖНО:** Не переходите на production без тщательного тестирования!

---

## 📖 Содержание документов

### QUICK_START_TBANK.md

Краткое руководство для быстрого старта:
- ✅ Получение токена
- ✅ Настройка за 5 минут
- ✅ Первый запуск
- ✅ Проверка работоспособности

**Для кого:** Новички, которые хотят быстро начать

### INSTALL_TBANK.md

Подробная инструкция по установке:
- ✅ Установка для Windows/Linux/macOS
- ✅ Проверка установки
- ✅ Устранение проблем
- ✅ Системные требования

**Для кого:** Все пользователи

### TBANK_SANDBOX_SETUP.md

Полное руководство по песочнице:
- ✅ Введение в песочницу
- ✅ Получение и настройка токена
- ✅ Особенности и ограничения песочницы
- ✅ Использование в коде (множество примеров)
- ✅ Переход на production
- ✅ Подробное устранение проблем
- ✅ FAQ

**Для кого:** Все, кто хочет полностью разобраться

### TBANK_INTEGRATION_SUMMARY.md

Технический обзор интеграции:
- ✅ Что было реализовано
- ✅ Архитектура решения
- ✅ API endpoints
- ✅ Основные классы
- ✅ Changelog

**Для кого:** Разработчики, технические специалисты

---

## 🎯 Быстрые ссылки

### Получение токена

🔑 https://www.tbank.ru/invest/settings/api/

### Официальная документация

📚 https://developer.tbank.ru/invest/

### Песочница

🧪 https://developer.tbank.ru/invest/intro/developer/sandbox

### Библиотека на GitHub

💻 https://github.com/Tinkoff/invest-python

### Telegram канал разработчиков

💬 https://t.me/tinkoffinvestopenapi

---

## 🔧 Быстрые команды

### Тестирование

```bash
# Полный тест песочницы
python examples/tbank_sandbox_test.py

# Или через батник (Windows)
test_tbank_sandbox.bat

# Или через shell (Linux/macOS)
./test_tbank_sandbox.sh
```

### Запуск системы

```bash
# С тестовой конфигурацией
python run.py --config config/test_config.yaml

# С выбором конфигурации
python run.py --select-config

# Через GUI
python gui_launcher.py
```

### Проверка статуса

```bash
# Проверка установки библиотеки
python -c "import tinkoff.invest; print('✅ OK')"

# Проверка токена
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TINKOFF_TOKEN')[:10] if os.getenv('TINKOFF_TOKEN') else 'Not found')"
```

---

## ❓ Частые вопросы

### Q: Где взять токен?

**A:** https://www.tbank.ru/invest/settings/api/ - создайте новый токен

### Q: Токен бесплатный?

**A:** Да, создание токена бесплатно

### Q: Песочница бесплатная?

**A:** Да, полностью бесплатная для тестирования

### Q: Можно ли потерять деньги в песочнице?

**A:** Нет, в песочнице виртуальные деньги

### Q: Как перейти на реальную торговлю?

**A:** Измените `sandbox: false` в конфигурации. **НО СНАЧАЛА ПРОТЕСТИРУЙТЕ В ПЕСОЧНИЦЕ!**

### Q: Сколько хранятся счета в песочнице?

**A:** 3 месяца с даты последнего использования

### Q: Можно ли иметь несколько счетов в песочнице?

**A:** Да, неограниченное количество

### Q: Какая комиссия в песочнице?

**A:** 0.05% от объема сделки (фиксированная)

### Q: Какая комиссия в production?

**A:** Зависит от вашего тарифа в T-Bank Инвестициях

### Q: Что делать если токен не работает?

**A:** 
1. Проверьте, что скопировали полностью
2. Создайте новый токен
3. Убедитесь, что токен для торговли, а не только для чтения

---

## 🆘 Получение помощи

### 1. Проверьте документацию

- [TBANK_SANDBOX_SETUP.md](TBANK_SANDBOX_SETUP.md) - раздел "Устранение проблем"
- [INSTALL_TBANK.md](../INSTALL_TBANK.md) - раздел "Устранение проблем"

### 2. Проверьте логи

Логи находятся в папке `logs/`:
- `investment_system.log` - основные логи
- `trading.log` - торговые операции

### 3. Запустите тест с DEBUG

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Затем запустите тест
```

### 4. Официальная поддержка T-Bank

- Telegram: https://t.me/tinkoffinvestopenapi
- Документация: https://developer.tbank.ru/invest/

---

## 📊 Примеры кода

### Минимальный пример

```python
from src.data.tbank_data_provider import TBankDataProvider
import asyncio
import os

async def main():
    token = os.getenv('TINKOFF_TOKEN')
    provider = TBankDataProvider(token=token, sandbox=True)
    await provider.initialize()
    
    price = await provider.get_current_price('SBER')
    print(f"SBER: {price} ₽")

asyncio.run(main())
```

### С брокером

```python
from src.trading.tbank_broker import TBankBroker
import asyncio
import os

async def main():
    token = os.getenv('TINKOFF_TOKEN')
    broker = TBankBroker(token=token, sandbox=True)
    await broker.initialize()
    
    # Получение портфеля
    portfolio = await broker.get_portfolio()
    print(f"Портфель: {portfolio['total_amount']:.2f} ₽")
    
    # Размещение ордера
    order = await broker.place_order(
        ticker='SBER',
        quantity=1,
        direction='buy',
        order_type='market'
    )
    print(f"Ордер: {order}")

asyncio.run(main())
```

### Полная интеграция

```python
from src.core.investment_system import InvestmentSystem
import asyncio

async def main():
    # Система автоматически подключится к T-Bank
    # если в конфигурации указан broker: tinkoff
    system = InvestmentSystem(config_path='config/test_config.yaml')
    await system.initialize()
    await system.start()

asyncio.run(main())
```

Больше примеров: [examples/](../examples/)

---

## 🎓 Обучающие материалы

### Видео (если есть)

*Раздел для будущих видео-туториалов*

### Статьи

- [TBANK_SANDBOX_SETUP.md](TBANK_SANDBOX_SETUP.md) - Основная статья
- [Официальная документация T-Bank](https://developer.tbank.ru/invest/)

### Примеры стратегий

*Раздел для будущих примеров торговых стратегий*

---

## 📈 Что дальше?

### После освоения основ

1. **Изучите продвинутые возможности:**
   - Лимитные ордера
   - Стоп-ордера
   - Стримы данных
   - Портфельные метрики

2. **Оптимизируйте стратегию:**
   - Бэктестинг
   - Оптимизация параметров
   - Анализ рисков

3. **Подготовьтесь к production:**
   - Тестируйте в песочнице минимум месяц
   - Проверьте все сценарии
   - Настройте риск-менеджмент
   - Начните с малых сумм

---

## ✅ Чеклист готовности к production

Перед переходом на реальную торговлю убедитесь:

- [ ] Протестировано в песочнице минимум 1 месяц
- [ ] Стратегия показывает стабильную прибыль
- [ ] Понимаете каждую строку кода
- [ ] Настроен риск-менеджмент
- [ ] Установлены стоп-лоссы
- [ ] Настроено логирование
- [ ] Настроены уведомления
- [ ] Есть план действий при сбоях
- [ ] Готовы к потерям
- [ ] Начинаете с малых сумм

**Если хоть один пункт не выполнен - продолжайте тестировать в песочнице!**

---

*Последнее обновление: 22 октября 2025*


