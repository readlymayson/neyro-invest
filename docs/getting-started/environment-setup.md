# Настройка переменных окружения через .env файл

## Обзор

Система нейросетевых инвестиций теперь поддерживает загрузку переменных окружения из файла `.env`. Это более удобный и безопасный способ управления конфигурацией.

## Быстрая настройка

### 1. Автоматическая настройка
```bash
python setup_env.py
```

Этот скрипт:
- Создаст файл `.env` из шаблона `environment.env`
- Покажет содержимое файла
- Даст инструкции по настройке

### 2. Ручная настройка

1. Скопируйте файл `environment.env` в `.env`:
   ```bash
   copy environment.env .env
   ```

2. Откройте файл `.env` в текстовом редакторе

3. Замените значения на реальные:
   ```env
   DEEPSEEK_API_KEY=sk-your-real-deepseek-key-here
   TINKOFF_TOKEN=your-real-tinkoff-token-here
   ```

## Структура .env файла

```env
# DeepSeek API ключ для анализа новостей и текста
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Tinkoff Invest API токен для торговли
TINKOFF_TOKEN=your_tinkoff_token_here

# Дополнительные настройки
LOG_LEVEL=INFO
DEBUG_MODE=false

# Настройки для разработки
DEVELOPMENT_MODE=true
```

## Получение API ключей

### DeepSeek API
1. Перейдите на https://platform.deepseek.com/
2. Зарегистрируйтесь или войдите в аккаунт
3. Создайте новый API ключ
4. Скопируйте ключ в файл `.env`

### Tinkoff Invest API
1. Перейдите на https://www.tinkoff.ru/invest/settings/api/
2. Войдите в свой аккаунт Tinkoff
3. Создайте токен для торговли
4. Скопируйте токен в файл `.env`

## Проверка настройки

После настройки `.env` файла проверьте статус системы:

```bash
python run.py --status
```

Вы должны увидеть:
```
🔑 Переменные окружения:
  • DEEPSEEK_API_KEY: ✅ Установлен
  • TINKOFF_TOKEN: ✅ Установлен
```

## Безопасность

⚠️ **ВАЖНО: Не добавляйте файл `.env` в систему контроля версий!**

Файл `.env` уже добавлен в `.gitignore` и не будет загружен в репозиторий.

## Устранение проблем

### Переменные не загружаются
1. Убедитесь, что файл `.env` находится в корневой директории проекта
2. Проверьте синтаксис файла (без пробелов вокруг `=`)
3. Перезапустите приложение

### Ошибки кодировки
Если возникают проблемы с кодировкой в Windows:
```bash
set PYTHONIOENCODING=utf-8
python run.py --status
```

## Альтернативные способы

Если `.env` файл не работает, можно использовать системные переменные окружения:

### Windows
```cmd
set DEEPSEEK_API_KEY=your_key_here
set TINKOFF_TOKEN=your_token_here
```

### Linux/Mac
```bash
export DEEPSEEK_API_KEY="your_key_here"
export TINKOFF_TOKEN="your_token_here"
```

## Дополнительные переменные

В файле `.env` можно настроить дополнительные параметры:

```env
# Уровень логирования
LOG_LEVEL=DEBUG

# Режим отладки
DEBUG_MODE=true

# Режим разработки
DEVELOPMENT_MODE=true
```

Эти переменные влияют на поведение системы и логирование.
