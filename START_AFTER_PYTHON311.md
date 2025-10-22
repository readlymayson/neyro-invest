# 🚀 Запуск после установки Python 3.11

## ✅ Python 3.11 установлен? Отлично! Продолжаем...

---

## 📋 Шаг 1: Проверьте установку

Откройте **НОВОЕ** окно CMD и выполните:

```cmd
python3.11 --version
```

**Должно показать:** `Python 3.11.9`

✅ Если видите версию - переходите к шагу 2  
❌ Если ошибка - закройте все окна CMD и откройте заново

---

## 📋 Шаг 2: Создайте виртуальное окружение

```cmd
cd C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest
setup_python311_venv.bat
```

Этот скрипт:
- ✅ Создаст виртуальное окружение `venv311`
- ✅ Установит все зависимости
- ✅ Подготовит систему к запуску

**Время выполнения:** 3-5 минут

---

## 📋 Шаг 3: Запустите тест T-Bank

После создания venv:

```cmd
venv311\Scripts\activate
python examples/tbank_sandbox_test.py
```

**Что должно произойти:**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    T-BANK SANDBOX TEST                                       ║
║               Тестирование песочницы T-Bank API                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ Токен найден: t.ZjCsAqNVJ...

================================================================================
ТЕСТ ПРОВАЙДЕРА ДАННЫХ T-BANK
================================================================================
✅ Провайдер создан
✅ Провайдер инициализирован
...
```

---

## 📋 Шаг 4: Запустите торговую систему

```cmd
venv311\Scripts\activate
python run.py --config config/test_config.yaml
```

**Или через GUI:**

```cmd
venv311\Scripts\activate
python gui_launcher.py
```

---

## 🎯 Быстрые команды (сохраните)

### Активация venv

```cmd
cd C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest
venv311\Scripts\activate
```

### Тест T-Bank песочницы

```cmd
python examples/tbank_sandbox_test.py
```

### Запуск торговой системы

```cmd
python run.py --config config/test_config.yaml
```

### Запуск GUI

```cmd
python gui_launcher.py
```

---

## 💡 Создайте батник для быстрого запуска

Создайте файл `start_system.bat`:

```bat
@echo off
cd C:\Users\frolo\YandexDisk\Code\ProjectsInWork\Testing\neyro-invest
call venv311\Scripts\activate
python run.py --config config/test_config.yaml
pause
```

Теперь просто запускайте `start_system.bat`!

---

## 🆘 Если что-то не работает

### Python 3.11 не найден

**Решение:** Перезагрузите компьютер и попробуйте снова

### Ошибка при создании venv

**Решение:**
```cmd
python3.11 -m pip install --upgrade pip
python3.11 -m venv venv311 --clear
```

### Ошибки при установке зависимостей

**Решение:**
```cmd
venv311\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## ✅ Чеклист готовности

После выполнения всех шагов:

- [ ] `python3.11 --version` работает
- [ ] Виртуальное окружение `venv311` создано
- [ ] `python -c "import tinkoff.invest"` без ошибок
- [ ] Тест T-Bank запускается
- [ ] Система запускается

**Если всё отмечено - вы готовы к работе!** 🎉

---

## 📚 Дополнительные материалы

- **Полное руководство T-Bank:** [docs/TBANK_SANDBOX_SETUP.md](docs/TBANK_SANDBOX_SETUP.md)
- **Решение проблем Python 3.14:** [PYTHON_314_ISSUE.md](PYTHON_314_ISSUE.md)
- **Руководство по установке:** [INSTALL_PYTHON311_GUIDE.md](INSTALL_PYTHON311_GUIDE.md)

---

**Удачи! Теперь всё должно работать идеально! ✨**


