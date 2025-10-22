# Инструкция по настройке и запуску системы нейросетевых инвестиций

## Системные требования

- Python 3.8+
- 8GB RAM (рекомендуется 16GB)
- 10GB свободного места на диске
- Стабильное интернет-соединение

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd neyro-invest
```

### 2. Создание виртуального окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Создание необходимых директорий

```bash
mkdir -p logs models data config
```

## Настройка

### 1. Конфигурация системы

Отредактируйте файл `config/main.yaml`:

```yaml
# Настройки данных
data:
  symbols: [SBER, GAZP, LKOH, NVTK]  # Российские акции
  update_interval: 60  # Обновление каждую минуту

# Настройки торговли
trading:
  broker: paper  # Начните с бумажной торговли
  signal_threshold: 0.6

# Настройки портфеля
portfolio:
  initial_capital: 1000000  # 1 млн рублей
  max_risk_per_trade: 0.02  # 2% риска на сделку
```

### 2. Настройка логирования

Создайте директорию для логов:

```bash
mkdir -p logs
```

Система автоматически создаст файлы логов в директории `logs/`.

## Первый запуск

### 1. Обучение моделей

Перед началом торговли необходимо обучить нейросети:

```bash
python examples/training_models.py --mode train
```

Этот процесс может занять 10-30 минут в зависимости от вашего оборудования.

### 2. Бэктестинг

Проверьте работу системы на исторических данных:

```bash
python examples/backtesting.py
```

### 3. Запуск системы

После успешного обучения и бэктестинга запустите систему:

```bash
python examples/basic_usage.py
```

## Мониторинг системы

### 1. Логи

Проверяйте логи для отслеживания работы системы:

```bash
# Основные логи
tail -f logs/investment_system.log

# Логи торговли
tail -f logs/trading.log

# Логи нейросетей
tail -f logs/neural_networks.log
```

### 2. Статус системы

Система выводит статус каждые несколько минут:

```
2024-01-15 10:30:00 | INFO | Система инвестиций: Портфель обновлен
2024-01-15 10:30:01 | INFO | Система инвестиций: Получено 3 торговых сигнала
2024-01-15 10:30:02 | INFO | Система инвестиций: Выполнено 1 торговых операций
```

## Настройка реальной торговли

### 1. Получение API ключей

Для торговли с реальными брокерами получите API ключи:

- **Tinkoff**: https://www.tinkoff.ru/invest/sandbox/
- **Сбербанк**: https://www.sberbank.com/ru/person/investments/trading/brokerage-services

### 2. Обновление конфигурации

```yaml
trading:
  broker: tinkoff  # или sber
  broker_settings:
    tinkoff:
      token: "your_tinkoff_token"
      sandbox: true  # Начните с sandbox
```

### 3. Перезапуск системы

```bash
python examples/basic_usage.py
```

## Устранение неполадок

### Частые проблемы

#### 1. Ошибка "Недостаточно данных"

```
ERROR | Недостаточно данных для создания последовательностей
```

**Решение**: Увеличьте `history_days` в конфигурации или добавьте больше символов.

#### 2. Ошибка подключения к API

```
ERROR | Ошибка получения данных для SBER: Connection timeout
```

**Решение**: Проверьте интернет-соединение и лимиты API.

#### 3. Ошибка памяти при обучении

```
ERROR | Out of memory during model training
```

**Решение**: Уменьшите `batch_size` или `epochs` в конфигурации моделей.

#### 4. Модели не обучаются

```
WARNING | Модель lstm_predictor не обучена, пропускаем
```

**Решение**: Проверьте логи обучения и убедитесь в достаточности данных.

### Отладка

#### 1. Включение подробного логирования

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

#### 2. Проверка статуса компонентов

```python
from src.core.investment_system import InvestmentSystem

system = InvestmentSystem("config/main.yaml")
status = system.get_system_status()
print(status)
```

#### 3. Тестирование отдельных компонентов

```python
# Тестирование провайдера данных
from src.data.data_provider import DataProvider
data_provider = DataProvider(config['data'])
await data_provider.initialize()
data = await data_provider.get_latest_data()
print(data)
```

## Оптимизация производительности

### 1. Настройка параметров моделей

Для быстрого тестирования:

```yaml
neural_networks:
  models:
    - name: lstm_predictor
      epochs: 10  # Уменьшите для быстрого обучения
      batch_size: 64  # Увеличьте если есть память
```

### 2. Ограничение количества символов

```yaml
data:
  symbols: [SBER, GAZP]  # Начните с 2-3 символов
```

### 3. Увеличение интервалов обновления

```yaml
data:
  update_interval: 300  # 5 минут вместо 1 минуты
neural_networks:
  analysis_interval: 600  # 10 минут
```

## Безопасность

### 1. Защита API ключей

Никогда не коммитьте API ключи в репозиторий:

```bash
# Добавьте в .gitignore
config/secrets.yaml
*.key
.env
```

### 2. Использование переменных окружения

```bash
export TINKOFF_TOKEN="your_token"
export SBER_TOKEN="your_token"
```

```yaml
trading:
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}
```

### 3. Начните с sandbox

Всегда тестируйте с sandbox режимом перед реальной торговлей.

## Поддержка

При возникновении проблем:

1. Проверьте логи системы
2. Убедитесь в правильности конфигурации
3. Проверьте системные требования
4. Создайте issue в репозитории с описанием проблемы

## Обновления

Для обновления системы:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

Переобучите модели после обновления:

```bash
python examples/training_models.py --mode train
```

