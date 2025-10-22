# Быстрая настройка main.yaml

## 🚀 Быстрый старт (5 минут)

### 1. Базовые настройки

```yaml
data:
  symbols: [SBER, GAZP]          # Начните с 2 акций
  update_interval: 600           # Обновление каждые 10 минут
  history_days: 180              # 6 месяцев данных

trading:
  broker: paper                  # Бумажная торговля
  signal_threshold: 0.7          # Консервативные сигналы
  max_positions: 3               # Максимум 3 позиции

portfolio:
  initial_capital: 100000        # 100 тысяч рублей
  max_risk_per_trade: 0.01       # 1% риска на сделку
```

### 2. Простые нейросети

```yaml
neural_networks:
  models:
    - name: lstm_basic
      type: lstm
      weight: 0.5
      enabled: true
      epochs: 50                 # Быстрое обучение
      batch_size: 64
    
    - name: xgb_basic
      type: xgboost
      weight: 0.5
      enabled: true
      n_estimators: 50           # Меньше деревьев
```

## ⚙️ Основные параметры

| Параметр | Рекомендуемое значение | Описание |
|----------|----------------------|----------|
| `update_interval` | 600 сек | Интервал обновления данных |
| `signal_threshold` | 0.6-0.7 | Порог уверенности сигналов |
| `max_positions` | 3-10 | Максимум позиций |
| `position_size` | 0.05-0.1 | Размер позиции (% от капитала) |
| `max_risk_per_trade` | 0.01-0.02 | Риск на сделку (1-2%) |
| `epochs` | 50-100 | Эпохи обучения нейросети |

## 📊 Уровни риска

### Консервативный (новички)
```yaml
signal_threshold: 0.8
max_positions: 3
position_size: 0.05
max_risk_per_trade: 0.01
```

### Сбалансированный (опытные)
```yaml
signal_threshold: 0.6
max_positions: 8
position_size: 0.08
max_risk_per_trade: 0.02
```

### Агрессивный (эксперты)
```yaml
signal_threshold: 0.5
max_positions: 15
position_size: 0.1
max_risk_per_trade: 0.03
```

## 🛡️ Безопасность

### Всегда используйте:
```yaml
trading:
  broker: paper                  # Сначала бумажная торговля
  broker_settings:
    tinkoff:
      sandbox: true              # Sandbox режим
```

### Для реальной торговли:
```yaml
trading:
  broker: tinkoff
  broker_settings:
    tinkoff:
      token: ${TINKOFF_TOKEN}    # Из переменной окружения
      sandbox: false             # Только после тестирования
```

## 🔧 Решение проблем

### Медленная работа
```yaml
data:
  update_interval: 1800          # 30 минут
neural_networks:
  models:
    - epochs: 30                 # Меньше эпох
      batch_size: 128            # Больше батч
```

### Много ложных сигналов
```yaml
trading:
  signal_threshold: 0.8          # Выше порог
neural_networks:
  models:
    - buy_threshold: 0.08        # Выше порог покупки
      sell_threshold: -0.08      # Ниже порог продажи
```

### Недостаточно данных
```yaml
data:
  history_days: 730              # 2 года данных
  symbols: [SBER, GAZP, LKOH]   # Больше инструментов
```

## 📱 Уведомления

### Email (Gmail)
```yaml
notifications:
  enabled: true
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your_email@gmail.com"
    password: ${EMAIL_PASSWORD}  # Пароль приложения!
    to_email: "your_email@gmail.com"
```

### Telegram
```yaml
notifications:
  enabled: true
  telegram:
    bot_token: ${TELEGRAM_BOT_TOKEN}
    chat_id: ${TELEGRAM_CHAT_ID}
```

## 🎯 Готовые конфигурации

### Для тестирования
```yaml
# config/test.yaml
data:
  symbols: [SBER]
  update_interval: 3600
  history_days: 90

neural_networks:
  models:
    - name: simple_lstm
      type: lstm
      enabled: true
      epochs: 20
      batch_size: 128

trading:
  broker: paper
  signal_threshold: 0.8
  max_positions: 1
```

### Для продакшена
```yaml
# config/production.yaml
data:
  symbols: [SBER, GAZP, LKOH, NVTK, ROSN]
  update_interval: 300
  history_days: 365

neural_networks:
  models:
    - name: lstm_prod
      type: lstm
      enabled: true
      epochs: 100
      sequence_length: 60
    - name: xgb_prod
      type: xgboost
      enabled: true
      n_estimators: 200

trading:
  broker: tinkoff
  signal_threshold: 0.65
  max_positions: 8
  position_size: 0.08

portfolio:
  initial_capital: 1000000
  max_risk_per_trade: 0.02
```

## ✅ Чек-лист настройки

- [ ] Настроены символы для торговли
- [ ] Выбран тип брокера (paper для начала)
- [ ] Установлены параметры риска
- [ ] Настроены нейросети
- [ ] Включено логирование
- [ ] Настроены уведомления (опционально)
- [ ] Проверена конфигурация
- [ ] Созданы резервные копии
