# Примеры использования

Эта папка содержит примеры кода для различных сценариев использования системы.

## Доступные примеры

### 📊 Основные примеры

- **`basic_usage.py`** - Базовый пример использования системы
- **`training_models.py`** - Пример обучения нейросетевых моделей
- **`backtesting.py`** - Пример бэктестинга торговых стратегий

### 🏦 T-Bank (Tinkoff Invest API)

- **`tbank_sandbox_test.py`** 🆕 - Тестирование песочницы T-Bank API

## Как использовать

### Базовый пример

```bash
python examples/basic_usage.py
```

### Обучение моделей

```bash
python examples/training_models.py
```

### Бэктестинг

```bash
python examples/backtesting.py
```

### Тестирование T-Bank Sandbox

```bash
# Убедитесь, что установили токен в .env файл
python examples/tbank_sandbox_test.py

# Или используйте батник (Windows)
test_tbank_sandbox.bat

# Или shell скрипт (Linux/macOS)
./test_tbank_sandbox.sh
```

## Перед запуском

### Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# DeepSeek API ключ
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# T-Bank API токен
TINKOFF_TOKEN=t.ваш_токен_здесь
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

Для T-Bank интеграции также нужно:

```bash
pip install tinkoff-investments
```

## Документация

- **T-Bank Sandbox:** [../docs/TBANK_SANDBOX_SETUP.md](../docs/TBANK_SANDBOX_SETUP.md)
- **Быстрый старт T-Bank:** [../QUICK_START_TBANK.md](../QUICK_START_TBANK.md)
- **Конфигурация:** [../docs/CONFIG_GUIDE.md](../docs/CONFIG_GUIDE.md)
- **DeepSeek Setup:** [../docs/DEEPSEEK_SETUP.md](../docs/DEEPSEEK_SETUP.md)

## Создание своих примеров

Вы можете создавать свои примеры на основе существующих. Основная структура:

```python
import asyncio
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Импорты из проекта
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.investment_system import InvestmentSystem

async def main():
    # Ваш код здесь
    pass

if __name__ == '__main__':
    asyncio.run(main())
```

## Помощь

Если у вас возникли проблемы, см.:
- [../РЕШЕНИЕ_ПРОБЛЕМ.md](../РЕШЕНИЕ_ПРОБЛЕМ.md)
- [../docs/TBANK_SANDBOX_SETUP.md](../docs/TBANK_SANDBOX_SETUP.md) (раздел "Устранение проблем")


