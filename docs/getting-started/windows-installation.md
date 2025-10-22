# 🪟 Настройка для Windows

## 📋 Быстрый старт на Windows

### 1. Установка Python

1. Скачайте Python 3.8+ с https://www.python.org/downloads/
2. При установке **обязательно отметьте** "Add Python to PATH"
3. Проверьте установку:
   ```cmd
   python --version
   ```

### 2. Настройка переменных окружения

#### Автоматическая настройка (рекомендуется)

```cmd
# Запустите установщик переменных окружения
setup_env.bat
```

Или в PowerShell:
```powershell
setup_env.ps1
```

#### Ручная настройка

```cmd
# Временная установка (для текущей сессии)
set DEEPSEEK_API_KEY=your_api_key_here

# Постоянная установка
setx DEEPSEEK_API_KEY "your_api_key_here"
```

### 3. Установка зависимостей

```cmd
# Создание виртуального окружения (рекомендуется)
python -m venv venv
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### 4. Создание конфигурации

```cmd
# Копирование примера конфигурации
copy config\examples\beginners.yaml config\main.yaml
```

### 5. Запуск системы

#### Command Prompt
```cmd
run_windows.bat
```

#### PowerShell
```powershell
run_windows.ps1
```

#### Прямой запуск Python
```cmd
python run.py
```

## 🔧 Режимы работы

### Торговая система
```cmd
run_windows.bat --mode trading
```

### Обучение моделей
```cmd
run_windows.bat --mode train
```

### Бэктестинг
```cmd
run_windows.bat --mode backtest --start 2023-01-01 --end 2023-12-31
```

### Проверка статуса
```cmd
run_windows.bat --status
```

## 🛠️ Решение проблем

### Проблема с кодировкой
Если видите кракозябры вместо русских символов:

1. **В Command Prompt:**
   ```cmd
   chcp 65001
   set PYTHONIOENCODING=utf-8
   ```

2. **В PowerShell:**
   ```powershell
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   $env:PYTHONIOENCODING = "utf-8"
   ```

### Проблема с PowerShell
Если PowerShell блокирует выполнение скриптов:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Проблема с путями
Если Python не найден:

1. Переустановите Python с отметкой "Add Python to PATH"
2. Или добавьте Python в PATH вручную:
   - Откройте "Параметры системы" → "Переменные среды"
   - Добавьте путь к Python в переменную PATH

### Проблема с зависимостями
Если не устанавливаются пакеты:

```cmd
# Обновите pip
python -m pip install --upgrade pip

# Установите зависимости
pip install -r requirements.txt --force-reinstall
```

## 📁 Структура файлов для Windows

```
neyro-invest/
├── run_windows.bat          # Запуск для Command Prompt
├── run_windows.ps1          # Запуск для PowerShell
├── setup_env.bat            # Настройка переменных (cmd)
├── setup_env.ps1            # Настройка переменных (ps1)
├── run.py                   # Главный Python скрипт
├── config/
│   ├── main.yaml           # Ваша конфигурация
│   └── examples/           # Примеры конфигураций
├── logs/                   # Логи системы
├── models/                 # Обученные модели
└── data/                   # Данные рынка
```

## 🎯 Рекомендации для Windows

### 1. Используйте виртуальное окружение
```cmd
python -m venv venv
venv\Scripts\activate
```

### 2. Настройте переменные окружения
```cmd
setup_env.bat
```

### 3. Используйте правильные скрипты запуска
- `run_windows.bat` для Command Prompt
- `run_windows.ps1` для PowerShell

### 4. Проверяйте логи
```cmd
type logs\investment_system.log
```

### 5. Мониторьте статус
```cmd
python run.py --status
```

## 🚨 Частые ошибки

### "Python не найден"
**Решение:** Переустановите Python с отметкой "Add Python to PATH"

### "Модуль не найден"
**Решение:** 
```cmd
pip install -r requirements.txt
```

### "Конфигурация не найдена"
**Решение:**
```cmd
copy config\examples\beginners.yaml config\main.yaml
```

### "API ключ не найден"
**Решение:**
```cmd
set DEEPSEEK_API_KEY=your_key
# или
setup_env.bat
```

### Кракозябры в консоли
**Решение:** Используйте `run_windows.bat` или `run_windows.ps1`

## 📞 Поддержка

Если у вас проблемы:

1. Проверьте логи в папке `logs\`
2. Запустите `python run.py --status`
3. Проверьте переменные окружения
4. Убедитесь в правильности конфигурации

---

**Успешной торговли на Windows! 🪟📈**





