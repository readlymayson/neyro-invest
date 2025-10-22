# 🚀 Быстрый старт системы нейросетевых инвестиций

## 📋 Что нужно сделать за 5 минут

### 1. Установка зависимостей

```bash
# Windows
pip install -r requirements.txt

# Linux/macOS
pip3 install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
# Windows (автоматическая настройка)
setup_env.bat

# Windows (PowerShell)
setup_env.ps1

# Ручная настройка
# Windows (cmd)
set DEEPSEEK_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your_api_key_here"

# Linux/macOS
export DEEPSEEK_API_KEY="your_api_key_here"
```

### 3. Создание конфигурации

```bash
# Скопируйте пример конфигурации
cp config/examples/beginners.yaml config/main.yaml
```

### 4. Запуск системы

```bash
# Простой запуск
python run.py

# Или используйте готовые скрипты
# Windows (Command Prompt)
run_windows.bat

# Windows (PowerShell)
run_windows.ps1

# Linux/macOS
./run.sh
```

## 🎯 Режимы работы

### Торговая система (по умолчанию)
```bash
python run.py --mode trading
```

### Обучение моделей
```bash
python run.py --mode train
```

### Бэктестинг
```bash
python run.py --mode backtest --start 2023-01-01 --end 2023-12-31
```

### Проверка статуса
```bash
python run.py --status
```

### Валидация конфигурации
```bash
python run.py --validate
```

## 🛠️ Использование Makefile

Если у вас установлен `make`:

```bash
# Справка
make help

# Настройка проекта
make setup

# Установка зависимостей
make install

# Запуск торговли
make run

# Обучение моделей
make train

# Бэктестинг
make backtest START=2023-01-01 END=2023-12-31

# Проверка статуса
make status

# Очистка
make clean
```

## 📁 Структура проекта после запуска

```
neyro-invest/
├── run.py                 # Главный файл запуска
├── run.bat               # Запуск для Windows
├── run.sh                # Запуск для Linux/macOS
├── run.ps1               # Запуск для PowerShell
├── Makefile              # Команды для make
├── config.yaml           # Ваша конфигурация
├── logs/                 # Логи системы
├── models/               # Обученные модели
└── data/                 # Данные рынка
```

## 🔧 Настройка конфигурации

### Для начинающих
```bash
cp config/examples/beginners.yaml config/main.yaml
```

### Для опытных пользователей
```bash
cp config/examples/advanced.yaml config/main.yaml
```

### Для продакшена
```bash
cp config/examples/production.yaml config/main.yaml
```

## 🚨 Решение проблем

### Ошибка "Python не найден"
- Установите Python 3.8+ с https://python.org
- Добавьте Python в PATH

### Ошибка "Модуль не найден"
```bash
pip install -r requirements.txt
```

### Ошибка "Конфигурация не найдена"
```bash
cp config/examples/beginners.yaml config/main.yaml
```

### Ошибка "API ключ не найден"
```bash
# Windows
set DEEPSEEK_API_KEY=your_key

# Linux/macOS
export DEEPSEEK_API_KEY="your_key"
```

## 📊 Мониторинг

### Просмотр логов
```bash
# Последние логи
tail -f logs/investment_system.log

# Логи торговли
tail -f logs/trading.log

# Логи нейросетей
tail -f logs/neural_networks.log
```

### Проверка статуса
```bash
python run.py --status
```

## 🎯 Следующие шаги

1. **Протестируйте систему** с бумажной торговлей
2. **Настройте уведомления** в конфигурации
3. **Обучите модели** на исторических данных
4. **Запустите бэктестинг** для проверки стратегии
5. **Переходите к реальной торговле** только после успешного тестирования

## 📞 Поддержка

- **Документация**: [docs/README.md](docs/README.md)
- **Настройка конфигурации**: [docs/CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md)
- **Настройка DeepSeek**: [docs/DEEPSEEK_SETUP.md](docs/DEEPSEEK_SETUP.md)
- **Решение проблем**: [РЕШЕНИЕ_ПРОБЛЕМ.md](РЕШЕНИЕ_ПРОБЛЕМ.md)

---

**Удачи в инвестициях! 🚀📈**
