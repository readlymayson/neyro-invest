# Информация о вашем T-Bank Sandbox счете

## 📊 Данные счета

**Account ID:** `24fdd4b3-aba2-4410-ae91-d57a8190909b`

**Статус:** ✅ Активен  
**Создан:** 22 октября 2025  
**Начальный капитал:** 1,000,000 ₽  
**Режим:** Sandbox (песочница)

---

## ✅ Ответ на ваш вопрос

### Будет ли работать этот ID в будущем?

**ДА!** Этот счет будет работать и **не будет создавать новые** при каждом запуске, потому что:

1. ✅ ID сохранен в конфигурации `config/test_config.yaml`
2. ✅ Брокер проверяет: если `account_id` указан - использует существующий
3. ✅ Только если `account_id: null` - создает новый

### Как это работает (код из `tbank_broker.py`):

```python
async def _setup_sandbox_account(self, client):
    if not self.account_id:
        # Создание НОВОГО счета (только если account_id не указан)
        response = await client.sandbox.open_sandbox_account()
        self.account_id = response.account_id
        logger.info(f"Создан новый sandbox счет: {self.account_id}")
        
        # Пополнение счета
        await client.sandbox.sandbox_pay_in(...)
    else:
        # Используется СУЩЕСТВУЮЩИЙ счет
        logger.info(f"Используется существующий sandbox счет: {self.account_id}")
```

---

## ⏰ Срок хранения счета

**Важно!** Счета в песочнице T-Bank хранятся **3 месяца** с даты последнего использования.

### Что это значит:
- ✅ Если вы используете систему регулярно - счет будет жить
- ⚠️ Если не используете 3 месяца - счет удалится автоматически
- 🔄 При удалении - просто установите `account_id: null` в конфиге

### Рекомендация:
Запускайте систему хотя бы раз в месяц для сохранения счета.

---

## 🔧 Конфигурация

Ваш счет уже настроен в файле `config/test_config.yaml`:

```yaml
trading:
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}
      sandbox: true
      account_id: "24fdd4b3-aba2-4410-ae91-d57a8190909b"  # ← Ваш счет!
```

### Что означает каждый параметр:

| Параметр | Значение | Описание |
|----------|----------|----------|
| `token` | Из .env | Ваш API токен T-Bank |
| `sandbox` | `true` | Режим песочницы (не реальные деньги) |
| `account_id` | Ваш ID | Конкретный счет (не создает новые) |

---

## 🎯 Использование

### При каждом запуске система будет:

1. ✅ Подключаться к вашему счету `24fdd4b3-aba2-4410-ae91-d57a8190909b`
2. ✅ Использовать текущий баланс и позиции
3. ✅ Не создавать новые счета
4. ✅ Сохранять историю операций

### Проверка счета:

```python
from src.trading.tbank_broker import TBankBroker
import asyncio
import os

async def check_account():
    broker = TBankBroker(
        token=os.getenv('TINKOFF_TOKEN'),
        sandbox=True,
        account_id="24fdd4b3-aba2-4410-ae91-d57a8190909b"
    )
    await broker.initialize()
    
    portfolio = await broker.get_portfolio()
    print(f"Account ID: {broker.account_id}")
    print(f"Balance: {portfolio['total_amount']} ₽")

asyncio.run(check_account())
```

---

## 🔄 Если счет удалился (через 3 месяца)

### Признаки:
- Ошибка "Account not found"
- Пустой портфель после долгого перерыва

### Решение (2 варианта):

**Вариант 1: Создать новый счет**
```yaml
# В config/test_config.yaml измените:
account_id: null  # Создаст новый при следующем запуске
```

**Вариант 2: Через код**
```python
# Закрыть старый и создать новый
await broker.close_sandbox_account()  # Если старый еще жив
# Установить account_id: null в конфиге
# Запустить систему - создастся новый
```

---

## 💰 Текущий статус счета

По данным из вашего теста:

```
Account ID: 24fdd4b3-aba2-4410-ae91-d57a8190909b
Режим: sandbox
Инструментов загружено: 1929
Общая стоимость: 0.00 ₽ (в акциях)
Позиций: 1 (наличные)
Баланс: 1,000,000.00 ₽ (в рублях)
```

### Расшифровка:
- ✅ Счет активен и работает
- ✅ 1 млн рублей доступен для торговли
- ✅ Нет открытых позиций (все в наличных)
- ✅ 1929 инструментов доступны для торговли

---

## 📋 Важные команды

### Проверить счет:
```cmd
python examples/tbank_sandbox_test.py
```

### Запустить торговлю с этим счетом:
```cmd
python run.py --config config/test_config.yaml
```

### Посмотреть операции:
```python
operations = await broker.get_operations()
for op in operations:
    print(f"{op['date']}: {op['type']} - {op['payment']} ₽")
```

---

## ✅ Резюме

### Ваш вопрос: "Будет ли работать брокер по этому ID в будущем?"

**ОТВЕТ: ДА! ✅**

- ✅ ID сохранен в конфигурации
- ✅ Система будет использовать именно этот счет
- ✅ Новые счета **НЕ БУДУТ** создаваться
- ✅ Все операции и баланс сохраняются
- ⏰ Счет живет 3 месяца (при регулярном использовании - неограниченно)

---

## 🔗 Полезные ссылки

- **Документация T-Bank Sandbox:** https://developer.tbank.ru/invest/intro/developer/sandbox
- **Полное руководство:** [TBANK_SANDBOX_SETUP.md](TBANK_SANDBOX_SETUP.md)
- **Конфигурация:** [../config/test_config.yaml](../config/test_config.yaml)

---

*Создано: 22 октября 2025*  
*ID счета: 24fdd4b3-aba2-4410-ae91-d57a8190909b*  
*Статус: ✅ Активен и настроен*

