# 🔗 Полная интеграция Web GUI с торговой системой

## Обзор

Web GUI теперь **полностью интегрирован** с торговой системой Neyro-Invest. Все компоненты работают вместе для предоставления real-time данных и управления.

---

## 📊 Архитектура интеграции

```
┌──────────────────────────────────────────────────────────┐
│                    Web GUI (FastAPI)                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │  API Endpoints                                     │  │
│  │  - /api/system/start  → Запуск системы            │  │
│  │  - /api/system/stop   → Остановка системы         │  │
│  │  - /api/portfolio     → Данные портфеля           │  │
│  │  - /api/signals       → Торговые сигналы          │  │
│  │  - /api/system/info   → Информация о системе      │  │
│  │  - /api/system/metrics → Метрики                  │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                                │
│                          ▼                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  app_state (Глобальное состояние)                 │  │
│  │  - investment_system                              │  │
│  │  - portfolio_manager                              │  │
│  │  - network_manager                                │  │
│  │  - trading_engine                                 │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│            Investment System Components                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Portfolio   │  │   Network    │  │   Trading    │  │
│  │   Manager    │  │   Manager    │  │   Engine     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                          │                                │
│                          ▼                                │
│                  InvestmentSystem                        │
│                  (Основная система)                      │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│              External Services                           │
│  - T-Bank Invest API                                     │
│  - Market Data Providers                                 │
│  - Neural Networks (XGBoost, DeepSeek)                   │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 Основные возможности

### 1. Запуск/Остановка системы

#### Запуск через API:
```http
POST /api/system/start
```

**Что происходит:**
1. Создается экземпляр `InvestmentSystem`
2. Система инициализирует все компоненты:
   - `PortfolioManager` - управление портфелем
   - `NetworkManager` - нейросети
   - `TradingEngine` - торговые операции
3. Запускается фоновая задача `start_trading()`
4. Компоненты становятся доступны через `app_state`
5. WebSocket рассылает уведомление всем клиентам

#### Остановка через API:
```http
POST /api/system/stop
```

**Что происходит:**
1. Вызывается `investment_system.stop_trading()`
2. Отменяются все фоновые задачи
3. Очищается `app_state`
4. WebSocket уведомляет клиентов

### 2. Получение реальных данных

#### Портфель:
```http
GET /api/portfolio
```

**Источники данных (приоритет):**
1. **Реальные данные** - из `portfolio_manager` (если система запущена)
2. **Файл** - из `data/portfolio.json`
3. **Demo данные** - если нет других источников

#### Сигналы:
```http
GET /api/signals?limit=20
```

**Источники данных:**
1. **Реальные сигналы** - из `trading_engine` (если система запущена)
2. **Файл** - из `data/signals.json`
3. **Сохраненные** - из `app_state["signals"]`

### 3. Мониторинг системы

#### Детальная информация:
```http
GET /api/system/info
```

**Возвращает:**
```json
{
  "is_running": true,
  "has_investment_system": true,
  "has_portfolio_manager": true,
  "has_network_manager": true,
  "has_trading_engine": true,
  "system_available": true,
  "last_portfolio_update": "2025-10-22T18:30:00",
  "last_signals_update": "2025-10-22T18:30:05",
  "start_time": "2025-10-22T18:00:00",
  "active_websockets": 2,
  "system_running_internally": true
}
```

#### Метрики:
```http
GET /api/system/metrics
```

**Возвращает:**
```json
{
  "portfolio": {
    "total_value": 1500000,
    "total_pnl": 50000,
    "positions_count": 5
  },
  "signals": {
    "total_count": 150,
    "recent_count": 10
  },
  "system": {
    "uptime_seconds": 3600,
    "uptime": "1:00:00",
    "is_running": true
  }
}
```

### 4. Real-time обновления через WebSocket

#### Типы сообщений:

**1. Portfolio Update**
```json
{
  "type": "portfolio_update",
  "data": {
    "total_value": 1500000,
    "cash_balance": 200000,
    "positions": [...]
  }
}
```

**2. Signals Update**
```json
{
  "type": "signals_update",
  "data": [
    {
      "timestamp": "2025-10-22T18:30:00",
      "symbol": "SBER",
      "signal": "BUY",
      "confidence": 0.85
    }
  ]
}
```

**3. System Status**
```json
{
  "type": "system_status",
  "data": {
    "is_running": true,
    "uptime": "1:00:00",
    "last_update": "2025-10-22T18:30:00"
  }
}
```

---

## 🔧 Глобальное состояние (app_state)

### Структура:

```python
app_state = {
    # Статус системы
    "system_running": bool,          # Запущена ли система
    "start_time": datetime,          # Время запуска
    
    # Компоненты системы
    "investment_system": InvestmentSystem,
    "portfolio_manager": PortfolioManager,
    "network_manager": NetworkManager,
    "trading_engine": TradingEngine,
    "broker": TBankBroker,
    
    # Данные
    "portfolio_data": dict,          # Кэш портфеля
    "signals": list,                 # Кэш сигналов
    "config": dict,                  # Конфигурация
    
    # Метаданные
    "system_task": asyncio.Task,     # Фоновая задача
    "last_portfolio_update": datetime,
    "last_signals_update": datetime
}
```

### Жизненный цикл:

```
Startup → Idle → Start System → Running → Stop System → Idle
   │        │          │            │            │          │
   ▼        ▼          ▼            ▼            ▼          ▼
 init   check    create IS   update data   cleanup   ready
        process     start      real-time      state   for new
                    task                              start
```

---

## 🚀 Пример использования

### 1. Запуск системы через UI:

```javascript
// Frontend (app.js)
async function startSystem() {
    const response = await fetch('/api/system/start', {
        method: 'POST'
    });
    
    if (response.ok) {
        const data = await response.json();
        console.log('✅ Система запущена:', data.message);
    }
}
```

### 2. Получение данных:

```javascript
// Получить портфель
const portfolio = await fetch('/api/portfolio').then(r => r.json());

// Получить сигналы
const signals = await fetch('/api/signals?limit=10').then(r => r.json());

// Получить метрики
const metrics = await fetch('/api/system/metrics').then(r => r.json());
```

### 3. WebSocket подключение:

```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch(message.type) {
        case 'portfolio_update':
            updatePortfolioUI(message.data);
            break;
        case 'signals_update':
            updateSignalsUI(message.data);
            break;
        case 'system_status':
            updateStatusUI(message.data);
            break;
    }
};
```

---

## 📝 Логирование

### Уровни логов:

- **INFO** - Нормальная работа
  ```
  ✅ Торговая система успешно запущена
  📊 Получены данные портфеля
  ```

- **WARNING** - Предупреждения
  ```
  ⚠️ Ошибка получения данных из portfolio_manager
  ⚠️ Используются demo данные
  ```

- **ERROR** - Ошибки
  ```
  ❌ Ошибка запуска системы: ModuleNotFoundError
  ❌ Критическая ошибка в торговом движке
  ```

### Просмотр логов:

```http
GET /api/logs?lines=100
```

---

## 🔍 Проверка интеграции

### 1. Проверка доступности модулей:

```http
GET /api/health
```

Ответ:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T18:00:00",
  "system_available": true  ← Модули загружены
}
```

### 2. Проверка статуса:

```http
GET /api/system/info
```

Все поля `has_*` должны быть `true` когда система запущена.

### 3. Проверка данных:

```bash
# Портфель
curl http://127.0.0.1:8000/api/portfolio

# Сигналы
curl http://127.0.0.1:8000/api/signals

# Метрики
curl http://127.0.0.1:8000/api/system/metrics
```

---

## 🐛 Решение проблем

### Проблема: "Системные модули недоступны"

**Причина**: Не установлены зависимости

**Решение**:
```bash
pip install -r requirements.txt
```

### Проблема: Портфель показывает demo данные

**Причина**: Система не запущена или `portfolio_manager` не доступен

**Решение**:
1. Запустите систему: `POST /api/system/start`
2. Проверьте статус: `GET /api/system/info`
3. Проверьте логи: `GET /api/logs`

### Проблема: Сигналов нет

**Причина**: Торговый движок еще не создал сигналы

**Решение**:
- Подождите несколько минут после запуска
- Система генерирует сигналы по расписанию

### Проблема: WebSocket не подключается

**Причина**: Неправильный URL или CORS

**Решение**:
```javascript
// Правильный URL
const ws = new WebSocket('ws://127.0.0.1:8000/ws');

// Не wss:// для локального HTTP
```

---

## 📚 API Reference

### Системные endpoints:

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/health` | Health check |
| GET | `/api/system/status` | Статус системы |
| GET | `/api/system/info` | Детальная информация |
| GET | `/api/system/metrics` | Метрики системы |
| POST | `/api/system/start` | Запуск системы |
| POST | `/api/system/stop` | Остановка системы |

### Данные:

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/portfolio` | Данные портфеля |
| GET | `/api/signals?limit=20` | Торговые сигналы |
| GET | `/api/config` | Конфигурация |
| POST | `/api/config` | Сохранение конфигурации |
| GET | `/api/logs?lines=100` | Логи системы |

### T-Bank:

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/tbank/check` | Проверка подключения |
| POST | `/api/tbank/get-balance` | Получение баланса |

### WebSocket:

| Protocol | Endpoint | Описание |
|----------|----------|----------|
| WS | `/ws` | Real-time обновления |

---

## 🎯 Следующие шаги

### Для пользователя:

1. ✅ Запустите Web GUI: `run_web_gui.bat`
2. ✅ Откройте браузер: http://127.0.0.1:8000
3. ✅ Настройте T-Bank токен
4. ✅ Нажмите "▶️ Запустить систему"
5. ✅ Наблюдайте real-time данные!

### Для разработчика:

1. Изучите `src/gui/web_app.py` - главный файл
2. Посмотрите `src/core/investment_system.py` - логика системы
3. Добавьте новые endpoints при необходимости
4. Расширьте WebSocket сообщения

---

## 📊 Статистика интеграции

- ✅ **16 API endpoints** - полный набор
- ✅ **4 компонента** интегрированы
- ✅ **3 источника данных** - real-time, файлы, demo
- ✅ **Real-time обновления** - каждые 5 секунд
- ✅ **WebSocket** - двунаправленная связь
- ✅ **Логирование** - детальное на всех уровнях

---

**Дата интеграции**: 22 октября 2025  
**Версия**: 2.0.0  
**Статус**: ✅ Полностью интегрирован

