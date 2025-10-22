# 🔄 Интеграция GUI с торговой системой через экспорт данных

## ✅ Решение проблемы

### **Проблема:**
GUI не видел сигналы и данные из торговой системы, потому что система не экспортировала данные в доступном для GUI формате.

### **Решение:**
Добавлен автоматический экспорт данных в JSON файлы каждые 10 секунд.

## 📦 Что экспортируется

### 1. **Данные портфеля** (`data/portfolio.json`)

```json
{
  "total_value": 1000000,
  "cash_balance": 1000000,
  "positions": {
    "SBER": {
      "quantity": 100,
      "price": 250.5,
      "value": 25050,
      "pnl": 150,
      "pnl_percent": 0.6
    }
  },
  "timestamp": "2025-10-22T14:14:43.541651"
}
```

**Содержит:**
- Общая стоимость портфеля
- Баланс наличных
- Позиции по каждому инструменту
  - Количество
  - Текущая цена
  - Стоимость позиции
  - Прибыль/убыток (PnL)
  - Процент PnL
- Временная метка

### 2. **Торговые сигналы** (`data/signals.json`)

```json
[
  {
    "time": "14:15:30",
    "symbol": "SBER",
    "signal": "BUY",
    "confidence": 0.75,
    "action": "Сигнал: BUY",
    "price": 250.5
  },
  {
    "time": "14:16:45",
    "symbol": "GAZP",
    "signal": "SELL",
    "confidence": 0.68,
    "action": "Сигнал: SELL",
    "price": 180.2
  }
]
```

**Содержит:**
- Время сигнала
- Символ инструмента
- Тип сигнала (BUY/SELL/HOLD)
- Уверенность модели (0-1)
- Описание действия
- Цена в момент сигнала
- **Хранится последние 50 сигналов**

## 🔧 Реализация

### **Новый цикл экспорта в системе:**

```python
async def _export_loop(self):
    """Цикл экспорта данных для GUI"""
    while self.is_running:
        try:
            # Экспорт данных портфеля
            await self._export_portfolio_data()
            
            # Экспорт торговых сигналов
            await self._export_signals_data()
            
            # Экспорт каждые 10 секунд
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Ошибка экспорта данных: {e}")
            await asyncio.sleep(30)
```

### **Метод экспорта портфеля:**

```python
async def _export_portfolio_data(self):
    """Экспорт данных портфеля в JSON"""
    # Создание директории data
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Формирование данных
    portfolio_data = {
        'total_value': total_value,
        'cash_balance': cash_balance,
        'positions': positions_dict,
        'timestamp': datetime.now().isoformat()
    }
    
    # Сохранение в файл
    with open("data/portfolio.json", 'w') as f:
        json.dump(portfolio_data, f, indent=2)
```

### **Метод экспорта сигналов:**

```python
async def _export_signals_data(self):
    """Экспорт торговых сигналов в JSON"""
    # Получение сигналов из торгового движка
    signals = await self.trading_engine.get_trading_signals()
    
    # Формирование данных
    signals_data = []
    for symbol, signal_info in signals.items():
        signals_data.append({
            'time': datetime.now().strftime("%H:%M:%S"),
            'symbol': symbol,
            'signal': signal_info['action'],
            'confidence': signal_info['confidence'],
            'price': signal_info['price']
        })
    
    # Загрузка существующих сигналов
    existing_signals = load_existing_signals()
    
    # Добавление новых
    existing_signals.extend(signals_data)
    
    # Ограничение до 50 последних
    existing_signals = existing_signals[-50:]
    
    # Сохранение
    save_signals(existing_signals)
```

## 📊 Как GUI читает данные

### **Загрузка данных портфеля:**

```python
def load_system_data(self):
    """Загрузка данных из системы"""
    # Загрузка портфеля
    portfolio_file = Path("data/portfolio.json")
    if portfolio_file.exists():
        with open(portfolio_file, 'r') as f:
            portfolio_data = json.load(f)
            self.portfolio_value = portfolio_data['total_value']
            self.current_positions = portfolio_data['positions']
    
    # Загрузка сигналов
    signals_file = Path("data/signals.json")
    if signals_file.exists():
        with open(signals_file, 'r') as f:
            self.trading_signals = json.load(f)
```

### **Периодичность обновления:**

- **Система экспортирует:** каждые 10 секунд
- **GUI проверяет:** каждые 10 секунд
- **GUI обновляет интерфейс:** каждую секунду

## 🎯 Преимущества решения

### ✅ **Разделение ответственности:**
- Торговая система: Торговля и анализ
- GUI: Только визуализация
- Связь через файлы: Простая и надежная

### ✅ **Независимость процессов:**
- Системы работают в отдельных процессах
- Падение GUI не влияет на торговлю
- Падение торговли видно в GUI

### ✅ **Простота отладки:**
- Данные в читаемом формате (JSON)
- Можно посмотреть файлы вручную
- Легко проверить что экспортируется

### ✅ **Масштабируемость:**
- Легко добавить новые данные
- Можно подключить другие GUI
- Можно анализировать данные извне

## 🔄 Жизненный цикл данных

```
Торговая система (run.py)
  └─ Анализ рынка
  └─ Генерация сигналов
  └─ Управление портфелем
  └─ [Каждые 10 сек] Экспорт данных
       ├─ data/portfolio.json
       └─ data/signals.json

GUI (gui_launcher.py)
  └─ [Каждые 10 сек] Загрузка данных
       ├─ Чтение data/portfolio.json
       └─ Чтение data/signals.json
  └─ [Каждую секунду] Обновление интерфейса
       ├─ Графики
       ├─ Таблицы
       └─ Метрики
```

## 📁 Структура директории data

```
data/
├── portfolio.json     # Данные портфеля (обновляется каждые 10 сек)
└── signals.json       # Торговые сигналы (последние 50)
```

## 🚀 Использование

### **Запуск системы:**

```bash
# 1. Запустить торговую систему
python run.py

# 2. Подождать 10 секунд (первый экспорт)

# 3. Запустить GUI
python gui_launcher.py
```

### **Проверка данных:**

```bash
# Проверить данные портфеля
type data\portfolio.json

# Проверить сигналы
type data\signals.json
```

## ✅ Результат

Теперь GUI **всегда видит актуальные данные** из торговой системы:
- ✅ Реальная стоимость портфеля
- ✅ Реальные позиции
- ✅ Реальные торговые сигналы
- ✅ Обновление каждые 10 секунд
- ✅ Независимость процессов

---

**Проблема с невидимостью сигналов решена!** 🎉
