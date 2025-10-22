# Быстрый старт с T-Bank Sandbox

Краткая инструкция по настройке и запуску системы с песочницей T-Bank.

## 🚀 За 5 минут

### 1. Получите токен T-Bank

1. Откройте https://www.tbank.ru/invest/settings/api/
2. Создайте новый токен "Для торговли"
3. Скопируйте токен (показывается только один раз!)

### 2. Настройте переменные окружения

Создайте файл `.env` в корне проекта:

```bash
TINKOFF_TOKEN=t.ваш_токен_здесь
TINKOFF_SANDBOX=true
```

### 3. Установите зависимости

```bash
pip install tinkoff-investments
```

Или установите все зависимости:

```bash
pip install -r requirements.txt
```

### 4. Запустите тест

```bash
python examples/tbank_sandbox_test.py
```

Если все настроено правильно, вы увидите:
- ✅ Информацию о провайдере данных
- ✅ Текущую цену SBER
- ✅ Исторические данные
- ✅ Стакан заявок
- ✅ Информацию о портфеле

## 📊 Использование в торговой системе

### Настройка конфигурации

Отредактируйте `config/test_config.yaml`:

```yaml
trading:
  broker: tinkoff  # Используем T-Bank
  
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}  # Из .env файла
      sandbox: true            # Песочница
      account_id: null         # Создастся автоматически
```

### Запуск системы

```bash
python run.py --config config/test_config.yaml
```

Или через GUI:

```bash
python gui_launcher.py
```

В GUI выберите:
- **Брокер:** Tinkoff
- **Режим:** Sandbox
- **Токен:** Вставьте ваш токен

## 🧪 Что происходит в песочнице?

- ✅ Создается виртуальный счет с 1,000,000 ₽
- ✅ Реальные рыночные данные
- ✅ Тестовые сделки без риска
- ✅ Комиссия 0.05% (как и в реале)
- ❌ Нет реальных денег
- ❌ Нет дивидендов/купонов

## 📖 Подробная документация

Полная документация: **[docs/TBANK_SANDBOX_SETUP.md](docs/TBANK_SANDBOX_SETUP.md)**

Включает:
- Подробную настройку
- Примеры кода
- Особенности песочницы
- Переход на production
- Решение проблем

## ⚠️ Важно

**Для реальной торговли:**

1. Тщательно протестируйте в песочнице
2. Измените `sandbox: false` в конфигурации
3. Начните с малых сумм
4. Установите консервативные параметры

**Никогда не используйте production без тестирования!**

## 🆘 Проблемы?

### Ошибка: "T-Bank брокер недоступен"

```bash
pip install tinkoff-investments
```

### Ошибка: "Токен не указан"

Проверьте файл `.env`:
```bash
TINKOFF_TOKEN=t.ваш_токен
```

### Другие проблемы

См. раздел "Устранение проблем" в [docs/TBANK_SANDBOX_SETUP.md](docs/TBANK_SANDBOX_SETUP.md)

## 🔗 Полезные ссылки

- 📚 **Документация T-Bank API:** https://developer.tbank.ru/invest/
- 🔑 **Получить токен:** https://www.tbank.ru/invest/settings/api/
- 🧪 **Песочница:** https://developer.tbank.ru/invest/intro/developer/sandbox

---

**Готово к тестированию!** 🎉

