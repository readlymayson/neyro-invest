# Скрипт перезапуска виртуального окружения

## Описание

Скрипт `restart_venv.py` полностью пересоздает виртуальное окружение проекта, удаляя старое и создавая новое с чистой установкой всех зависимостей.

## Когда использовать

- 🔄 После обновления Python
- 🧹 При проблемах с зависимостями
- 📦 После изменения requirements.txt
- 🐛 При ошибках импорта модулей
- 🚀 Для "чистого" старта проекта

## Способы запуска

### 1. Автоматический (рекомендуется)

#### Windows:
```bash
restart_venv.bat
```

#### Linux/macOS:
```bash
./restart_venv.sh
```

### 2. Прямой запуск Python скрипта

```bash
python restart_venv.py
```

## Что делает скрипт

### 1. Проверки
- ✅ Проверяет версию Python (требуется 3.8+)
- ✅ Проверяет доступность модуля venv

### 2. Очистка
- 🗑️ Удаляет старое виртуальное окружение (папка `venv/`)
- 🧹 Очищает кэш pip

### 3. Создание нового окружения
- 🆕 Создает новое виртуальное окружение
- ⬆️ Обновляет pip до последней версии
- 📦 Устанавливает зависимости

### 4. Установка зависимостей
Пытается установить зависимости в следующем порядке:
1. `requirements_gui_minimal.txt` (минимальные для GUI)
2. `requirements_gui.txt` (полные для GUI)
3. `requirements_minimal.txt` (минимальные общие)
4. `requirements.txt` (полные общие)
5. Базовые пакеты вручную

### 5. Проверка
- 🔍 Тестирует импорт основных модулей
- ✅ Проверяет работоспособность окружения

## Результат работы

### При успехе:
```
🎉 Виртуальное окружение успешно перезапущено!

ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ
============================================================

1. Активация виртуального окружения:
   venv\Scripts\activate.bat  (Windows)
   source venv/bin/activate  (Linux/macOS)

2. Запуск GUI:
   python gui_launcher_simple.py
   # или
   python gui_launcher.py

3. Запуск через скрипты:
   run_gui.bat  (Windows)
   ./run_gui.sh  (Linux/macOS)
```

### При ошибках:
```
❌ Произошли ошибки. Проверьте сообщения выше.
```

## Требования

- Python 3.8 или выше
- Доступ к интернету (для установки пакетов)
- Права на запись в текущую директорию

## Устранение проблем

### Ошибка "Python не найден"
```bash
# Установите Python с https://python.org
# Или добавьте Python в PATH
```

### Ошибка "venv не найден"
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# CentOS/RHEL
sudo yum install python3-venv
```

### Ошибка "Permission denied"
```bash
# Linux/macOS
chmod +x restart_venv.sh

# Или запустите с правами администратора
sudo python3 restart_venv.py
```

### Проблемы с сетью
```bash
# Используйте зеркало PyPI
pip install -i https://pypi.douban.com/simple/ -r requirements_gui_minimal.txt
```

## Ручная установка после перезапуска

Если автоматическая установка не сработала:

```bash
# Активация окружения
# Windows:
venv\Scripts\activate.bat

# Linux/macOS:
source venv/bin/activate

# Установка зависимостей
pip install numpy pandas matplotlib loguru pyyaml requests

# Проверка
python -c "import tkinter, numpy, pandas, matplotlib; print('Все готово!')"
```

## Логи и отладка

Скрипт выводит подробную информацию о каждом шаге:
- ✅ Успешные операции
- ❌ Ошибки
- ⚠️ Предупреждения
- ℹ️ Информационные сообщения

## Безопасность

- Скрипт НЕ удаляет файлы проекта
- Удаляет только папку `venv/`
- Создает резервную копию не делает (venv можно пересоздать)

## Альтернативы

Если скрипт не работает, можно перезапустить вручную:

```bash
# 1. Удаление старого venv
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# 2. Создание нового
python -m venv venv

# 3. Активация
# Windows: venv\Scripts\activate.bat
# Linux/macOS: source venv/bin/activate

# 4. Установка зависимостей
pip install -r requirements_gui_minimal.txt
```

---

**Версия**: 1.0.0  
**Совместимость**: Windows, Linux, macOS  
**Требования**: Python 3.8+
