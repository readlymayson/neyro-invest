# Руководство по установке Python 3.11

## 🎯 Цель

Установить Python 3.11 для корректной работы системы (Python 3.14 не совместим с protobuf).

---

## 🚀 Вариант 1: Автоматическая установка (рекомендуется)

### Шаг 1: Запустите скрипт установки

**В PowerShell (от имени администратора):**

```powershell
# Откройте PowerShell как администратор (правой кнопкой -> Запуск от имени администратора)
cd "C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest"

# Разрешите выполнение скриптов (однократно)
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Запустите установку
.\install_python311.ps1
```

### Шаг 2: Создайте виртуальное окружение

**После установки Python 3.11, откройте новое окно CMD и выполните:**

```cmd
cd C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest
setup_python311_venv.bat
```

### Шаг 3: Готово!

После этого можете запускать систему:

```cmd
venv311\Scripts\activate
python run.py --config config/test_config.yaml
```

---

## 🔧 Вариант 2: Ручная установка

### Шаг 1: Скачайте Python 3.11

**Прямая ссылка:**
https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

**Или через сайт:**
https://www.python.org/downloads/release/python-3119/

### Шаг 2: Установите Python 3.11

1. Запустите скачанный установщик
2. ✅ **ОБЯЗАТЕЛЬНО поставьте галочку:** "Add Python 3.11 to PATH"
3. Нажмите "Install Now"
4. Дождитесь завершения установки
5. Нажмите "Close"

### Шаг 3: Проверьте установку

**Откройте новое окно CMD и выполните:**

```cmd
python3.11 --version
```

Должно показать: `Python 3.11.9`

### Шаг 4: Создайте виртуальное окружение

```cmd
cd C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest

# Создание venv
python3.11 -m venv venv311

# Активация
venv311\Scripts\activate

# Обновление pip
python -m pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 5: Запустите систему

```cmd
# Убедитесь что venv активирован (в начале строки должно быть (venv311))
python run.py --config config/test_config.yaml
```

---

## ✅ Проверка работы

### 1. Проверьте Python версию

```cmd
venv311\Scripts\activate
python --version
```

Должно быть: `Python 3.11.9`

### 2. Проверьте T-Bank библиотеку

```cmd
python -c "import tinkoff.invest; print('✅ T-Bank OK')"
```

Должно показать: `✅ T-Bank OK`

### 3. Запустите тест

```cmd
python examples/tbank_sandbox_test.py
```

Если всё работает - увидите данные по акциям и портфелю!

---

## 🆘 Решение проблем

### Ошибка: "python3.11 не является внутренней командой"

**Решение:**
1. Перезапустите CMD/PowerShell
2. Или добавьте Python в PATH вручную:
   - Найдите где установлен Python 3.11 (обычно `C:\Users\frolo\AppData\Local\Programs\Python\Python311`)
   - Добавьте этот путь в переменную PATH

### Ошибка: "venv311\Scripts\activate не работает"

**Решение:**
1. Используйте полный путь:
   ```cmd
   C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest\venv311\Scripts\activate
   ```

2. Или создайте батник для активации (уже есть `setup_python311_venv.bat`)

### Ошибка при установке зависимостей

**Решение:**
```cmd
# Попробуйте минимальные зависимости
pip install -r requirements_minimal.txt

# Потом добавьте T-Bank
pip install tinkoff-investments
```

---

## 📊 Что будет после установки

### Структура проекта

```
neyro-invest/
├── venv311/              ← Виртуальное окружение Python 3.11
│   ├── Scripts/
│   │   └── activate.bat  ← Скрипт активации
│   └── Lib/
├── src/
├── config/
└── ...
```

### Как работать

**Каждый раз при открытии CMD:**

```cmd
cd C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest
venv311\Scripts\activate
python run.py
```

**Или создайте батник `start.bat`:**

```bat
@echo off
call venv311\Scripts\activate
python run.py --config config/test_config.yaml
pause
```

---

## 🎯 Итоговый чеклист

После выполнения всех шагов проверьте:

- [ ] Python 3.11 установлен
- [ ] `python3.11 --version` показывает 3.11.9
- [ ] Виртуальное окружение venv311 создано
- [ ] Зависимости установлены
- [ ] T-Bank библиотека работает
- [ ] Система запускается без ошибок

---

## 🚀 Быстрый старт (после установки)

```cmd
cd C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest
venv311\Scripts\activate
python examples/tbank_sandbox_test.py
```

**Если видите данные по акциям - всё работает! ✅**

---

*Создано: 22.10.2025*  
*Версия: 1.0*


