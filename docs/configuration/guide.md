# Руководство по настройке конфигурации main.yaml

## Обзор

Файл `config/main.yaml` является центральным конфигурационным файлом системы нейросетевых инвестиций. Он определяет все параметры работы системы: от получения данных до торговых стратегий.

## Структура конфигурации

### 1. Настройки данных (data)

```yaml
data:
  provider: yfinance          # Провайдер данных
  symbols:                    # Список отслеживаемых инструментов
    - SBER                    # Сбербанк
    - GAZP                    # Газпром
    - LKOH                    # Лукойл
    - NVTK                    # НОВАТЭК
    - ROSN                    # Роснефть
    - NLMK                    # НЛМК
    - MAGN                    # ММК
    - YNDX                    # Яндекс
  update_interval: 600        # Интервал обновления данных (секунды)
  history_days: 365          # Количество дней исторических данных
```

#### Параметры:

- **provider**: Провайдер данных (пока только `yfinance`)
- **symbols**: Список российских акций для анализа
  - Рекомендуется начать с 2-3 инструментов для тестирования
  - Полный список доступных тикеров: SBER, GAZP, LKOH, NVTK, ROSN, NLMK, MAGN, YNDX, MOEX, VTBR, ALRS, AFLT, SNGSP, MGNT, CHMF, RUAL, FIVE, OZON
- **update_interval**: 
  - 60 сек - для активной торговли
  - 300 сек (5 мин) - для среднесрочных стратегий
  - 600 сек (10 мин) - для долгосрочных стратегий
- **history_days**: Количество дней исторических данных для обучения
  - Минимум: 180 дней
  - Рекомендуется: 365 дней
  - Максимум: 1095 дней (3 года)

### 2. Настройки нейросетей (neural_networks)

```yaml
neural_networks:
  models:
    - name: lstm_predictor
      type: lstm
      weight: 0.3
      enabled: true
      sequence_length: 60
      lstm_units: [50, 50]
      dropout_rate: 0.2
      learning_rate: 0.001
      batch_size: 32
      epochs: 100
```

#### LSTM модель:

- **name**: Уникальное имя модели
- **type**: Тип модели (`lstm`)
- **weight**: Вес в ансамбле (0.0-1.0, сумма всех весов = 1.0)
- **enabled**: Включить/выключить модель
- **sequence_length**: Длина последовательности для анализа (рекомендуется 60)
- **lstm_units**: Количество нейронов в LSTM слоях `[первый_слой, второй_слой]`
- **dropout_rate**: Коэффициент дропаута для предотвращения переобучения (0.1-0.5)
- **learning_rate**: Скорость обучения (0.0001-0.01)
- **batch_size**: Размер батча для обучения (16, 32, 64)
- **epochs**: Количество эпох обучения (50-200)

```yaml
    - name: xgboost_classifier
      type: xgboost
      weight: 0.3
      enabled: true
      n_estimators: 100
      max_depth: 6
      learning_rate: 0.1
      subsample: 0.8
      colsample_bytree: 0.8
      buy_threshold: 0.05
      sell_threshold: -0.05
```

#### XGBoost модель:

- **n_estimators**: Количество деревьев (50-500)
- **max_depth**: Максимальная глубина дерева (3-10)
- **learning_rate**: Скорость обучения (0.01-0.3)
- **subsample**: Доля образцов для обучения (0.6-1.0)
- **colsample_bytree**: Доля признаков для дерева (0.6-1.0)
- **buy_threshold**: Порог для сигнала покупки (0.02-0.1)
- **sell_threshold**: Порог для сигнала продажи (-0.1 до -0.02)

#### DeepSeek модель:
- **name**: Уникальное имя модели
- **type**: Тип модели (`deepseek`)
- **weight**: Вес в ансамбле (0.0-1.0)
- **enabled**: Включить/выключить модель
- **model_name**: Название модели DeepSeek (`deepseek-chat`, `deepseek-coder`)
- **max_tokens**: Максимальное количество токенов (1000-8000)
- **temperature**: Температура генерации (0.1-1.0, меньше = более детерминированный)
- **analysis_window**: Размер окна для анализа в днях (30-100)

```yaml
    - name: deepseek_enhanced
      type: deepseek
      weight: 0.4
      enabled: true
      api_key: ${DEEPSEEK_API_KEY}  # API ключ DeepSeek
      base_url: "https://api.deepseek.com/v1"
      model_name: "deepseek-chat"
      max_tokens: 4000
      temperature: 0.3
      analysis_window: 30
      feature_importance_threshold: 0.1
```

### DeepSeek модель:

- **api_key**: API ключ DeepSeek (обязательно!)
- **base_url**: URL API (по умолчанию: https://api.deepseek.com/v1)
- **model_name**: Название модели (deepseek-chat)
- **max_tokens**: Максимальное количество токенов (1000-8000)
- **temperature**: Креативность ответов (0.1-0.9)
- **analysis_window**: Окно анализа в днях (10-90)
- **feature_importance_threshold**: Порог важности признаков (0.05-0.3)

```yaml
  # Интервалы анализа
  analysis_interval: 180      # Интервал анализа (секунды)
  signal_check_interval: 180  # Интервал проверки сигналов (секунды)
  
  # Управление передачей данных портфеля в нейросети при генерации сигналов
  enable_portfolio_features: true  # true - передавать портфельные данные, false - не передавать
  
  ensemble_method: weighted_average  # Метод ансамбля
```

#### Общие параметры нейросетей:

- **analysis_interval**: Интервал анализа данных нейросетями (секунды)
  - 60 сек - для высокочастотной торговли
  - 180 сек (3 мин) - стандартная частота
  - 300 сек (5 мин) - для стандартной торговли
  - 900 сек (15 мин) - для долгосрочных стратегий
- **signal_check_interval**: Интервал проверки торговых сигналов (секунды)
  - 180 сек (3 мин) - для активной торговли
  - 3600 сек (1 час) - для умеренной торговли
- **enable_portfolio_features**: Передача данных портфеля в нейросети при анализе
  - `true` - нейросети получают информацию о портфеле (позиции, P&L, распределение) для более точного анализа
  - `false` - нейросети работают только с рыночными данными без учета текущего портфеля
  - Рекомендуется: `true` для лучшей точности, `false` для независимого анализа каждого инструмента
- **ensemble_method**: Метод объединения предсказаний
  - `weighted_average` - взвешенное среднее (рекомендуется)
  - `majority_vote` - голосование большинством
  - `confidence_weighted` - взвешивание по уверенности

### 3. Настройки торговли (trading)

```yaml
trading:
  broker: paper               # Тип брокера
  signal_threshold: 0.6       # Порог уверенности сигналов
  signal_check_interval: 30   # Интервал проверки сигналов (секунды)
  max_positions: 10           # Максимальное количество позиций
  position_size: 0.1          # Размер позиции (% от капитала)
```

#### Параметры:

- **broker**: Тип брокера
  - `paper` - бумажная торговля (для тестирования)
  - `tinkoff` - Tinkoff Investments
  - `sber` - Сбербанк Инвестор
- **signal_threshold**: Минимальная уверенность для торгового сигнала (0.5-0.9)
  - 0.5 - более агрессивная торговля
  - 0.6 - сбалансированная торговля
  - 0.7+ - консервативная торговля
- **signal_check_interval**: Как часто проверять новые сигналы (секунды)
- **max_positions**: Максимальное количество одновременных позиций
- **position_size**: Размер каждой позиции как доля от капитала (0.05-0.2)

```yaml
  broker_settings:
    tinkoff:
      token: "your_tinkoff_token"
      sandbox: true
    sber:
      token: "your_sber_token"
      sandbox: true
```

#### Настройки брокеров:

- **token**: API токен брокера
- **sandbox**: Режим песочницы (true для тестирования, false для реальной торговли)

### 4. Настройки портфеля (portfolio)

```yaml
portfolio:
  initial_capital: 1000000    # Начальный капитал (рубли)
  max_risk_per_trade: 0.02    # Максимальный риск на сделку
  max_portfolio_risk: 0.1     # Максимальный риск портфеля
  update_interval: 300        # Интервал обновления портфеля (секунды)
  rebalance_threshold: 0.05   # Порог для ребалансировки
```

#### Параметры:

- **initial_capital**: Начальный капитал в рублях
  - Минимум: 100,000 руб
  - Рекомендуется: 1,000,000 руб
- **max_risk_per_trade**: Максимальный риск на одну сделку (0.01-0.05)
  - 0.01 (1%) - консервативно
  - 0.02 (2%) - сбалансированно
  - 0.05 (5%) - агрессивно
- **max_portfolio_risk**: Максимальный общий риск портфеля (0.05-0.2)
- **update_interval**: Как часто обновлять портфель (секунды)
- **rebalance_threshold**: Отклонение для запуска ребалансировки (0.03-0.1)

### 5. Настройки логирования (logging)

```yaml
logging:
  level: INFO                 # Уровень логирования
  file: logs/investment_system.log
  max_size: 10 MB
  retention: 30 days
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
```

#### Параметры:

- **level**: Уровень детализации логов
  - `DEBUG` - максимальная детализация
  - `INFO` - основная информация
  - `WARNING` - только предупреждения и ошибки
  - `ERROR` - только ошибки
- **file**: Путь к файлу логов
- **max_size**: Максимальный размер файла лога
- **retention**: Время хранения логов
- **format**: Формат записи в логах

### 6. Настройки уведомлений (notifications)

```yaml
notifications:
  enabled: false              # Включить уведомления
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your_email@gmail.com"
    password: "your_password"
    to_email: "notifications@example.com"
  telegram:
    bot_token: "your_telegram_bot_token"
    chat_id: "your_chat_id"
```

#### Параметры:

- **enabled**: Включить/выключить уведомления
- **email**: Настройки email уведомлений
  - **smtp_server**: SMTP сервер (Gmail: smtp.gmail.com, Yandex: smtp.yandex.ru)
  - **smtp_port**: Порт SMTP (Gmail: 587, Yandex: 587)
  - **username**: Email адрес
  - **password**: Пароль приложения (не основной пароль!)
  - **to_email**: Email для получения уведомлений
- **telegram**: Настройки Telegram уведомлений
  - **bot_token**: Токен Telegram бота
  - **chat_id**: ID чата для уведомлений

### 7. Настройки мониторинга (monitoring)

```yaml
monitoring:
  enabled: true               # Включить мониторинг
  web_interface:
    enabled: true             # Включить веб-интерфейс
    host: "localhost"         # Хост для веб-интерфейса
    port: 8080               # Порт для веб-интерфейса
  metrics:
    enabled: true             # Включить экспорт метрик
    export_interval: 60      # Интервал экспорта метрик (секунды)
```

## Примеры конфигураций

### Конфигурация для начинающих

```yaml
data:
  symbols: [SBER, GAZP]       # Только 2 акции
  update_interval: 900        # Обновление каждые 15 минут
  history_days: 180           # 6 месяцев истории

neural_networks:
  models:
    - name: lstm_simple
      type: lstm
      weight: 0.5
      enabled: true
      epochs: 50              # Меньше эпох для быстрого обучения
      batch_size: 64          # Больший батч
    - name: xgb_simple
      type: xgboost
      weight: 0.5
      enabled: true
      n_estimators: 50        # Меньше деревьев

trading:
  broker: paper
  signal_threshold: 0.7       # Более консервативно
  max_positions: 3            # Меньше позиций
  position_size: 0.05         # Меньший размер позиции

portfolio:
  initial_capital: 100000     # Меньший капитал
  max_risk_per_trade: 0.01    # 1% риск на сделку
```

### Конфигурация для опытных пользователей

```yaml
data:
  symbols: [SBER, GAZP, LKOH, NVTK, ROSN, NLMK, MAGN, YNDX]
  update_interval: 60         # Обновление каждую минуту
  history_days: 730           # 2 года истории

neural_networks:
  models:
    - name: lstm_advanced
      type: lstm
      weight: 0.4
      enabled: true
      sequence_length: 120    # Больше данных для анализа
      lstm_units: [100, 100, 50]  # Больше слоев
      epochs: 200             # Больше эпох
    - name: xgb_advanced
      type: xgboost
      weight: 0.6
      enabled: true
      n_estimators: 300       # Больше деревьев
      max_depth: 8            # Больше глубина

trading:
  broker: tinkoff
  signal_threshold: 0.6
  max_positions: 15           # Больше позиций
  position_size: 0.08         # Больший размер позиции

portfolio:
  initial_capital: 5000000    # Больший капитал
  max_risk_per_trade: 0.03    # 3% риск на сделку
```

## Рекомендации по настройке

### 1. Начальная настройка

1. Начните с бумажной торговли (`broker: paper`)
2. Используйте 2-3 инструмента для тестирования
3. Установите консервативные параметры риска
4. Включите подробное логирование (`level: DEBUG`)

### 2. Оптимизация производительности

- Увеличьте `update_interval` если система работает медленно
- Уменьшите `epochs` для быстрого обучения
- Увеличьте `batch_size` если есть достаточно памяти
- Ограничьте количество символов

### 3. Управление рисками

- Начинайте с `max_risk_per_trade: 0.01` (1%)
- Увеличивайте `signal_threshold` для более надежных сигналов
- Ограничивайте `max_positions` для диверсификации
- Используйте `rebalance_threshold` для контроля портфеля

### 4. Мониторинг и отладка

- Включите уведомления для важных событий
- Используйте веб-интерфейс для мониторинга
- Регулярно проверяйте логи
- Настройте экспорт метрик

## Безопасность

### Важные предупреждения:

1. **Никогда не храните пароли в конфигурации**
   - Используйте переменные окружения
   - Используйте пароли приложений, а не основные пароли

2. **Начните с sandbox режима**
   - Всегда тестируйте с `sandbox: true`
   - Переходите к реальной торговле только после тщательного тестирования

3. **Резервное копирование конфигурации**
   - Сохраняйте рабочие конфигурации
   - Ведите журнал изменений

4. **API ключи DeepSeek**
   - Получите API ключ на https://platform.deepseek.com/
   - Используйте переменную окружения `DEEPSEEK_API_KEY`
   - Следите за лимитами использования API

## Переменные окружения

Для безопасности используйте переменные окружения:

```bash
export TINKOFF_TOKEN="your_token"
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export EMAIL_PASSWORD="your_app_password"
```

```yaml
trading:
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}

neural_networks:
  models:
    - name: deepseek_analyzer
      type: deepseek
      api_key: ${DEEPSEEK_API_KEY}

notifications:
  email:
    password: ${EMAIL_PASSWORD}
```

## Проверка конфигурации

Перед запуском проверьте конфигурацию:

```python
from src.utils.config_manager import ConfigManager

config_manager = ConfigManager("config/main.yaml")
config = config_manager.get_config()
print("Конфигурация загружена успешно")
```

## Заключение

Правильная настройка конфигурации критически важна для успешной работы системы. Начните с консервативных параметров и постепенно оптимизируйте их на основе результатов работы системы.
