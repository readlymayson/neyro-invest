# Быстрый старт GUI

## 🚀 Самый простой способ запуска

### Windows
```bash
run_gui.bat
```

### Linux/macOS  
```bash
./run_gui.sh
```

## 📦 Если возникают проблемы с зависимостями

### 1. Установите минимальные зависимости
```bash
python install_gui_deps.py
```

### 2. Или установите вручную
```bash
pip install numpy pandas matplotlib loguru pyyaml requests
```

### 3. Запустите упрощенную версию
```bash
python gui_launcher_simple.py
```

## ⚡ Быстрая проверка

Проверьте, что Python может импортировать основные модули:
```python
python -c "import tkinter, numpy, pandas, matplotlib; print('Все готово!')"
```

## 🔧 Решение частых проблем

### Ошибка "asyncio-mqtt не найден"
- Используйте `requirements_gui_minimal.txt` вместо `requirements_gui.txt`
- Или запустите `python install_gui_deps.py`

### Ошибка "tkinter не найден" (Linux)
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL  
sudo yum install tkinter
```

### Проблемы с matplotlib
```bash
pip install --upgrade matplotlib
```

## 📁 Структура файлов

- `gui_launcher.py` - основной launcher (требует все зависимости)
- `gui_launcher_simple.py` - упрощенный launcher (минимальные зависимости)
- `install_gui_deps.py` - скрипт установки зависимостей
- `requirements_gui_minimal.txt` - минимальные зависимости
- `run_gui.bat` / `run_gui.sh` - скрипты автоматического запуска

## 🎯 Что делать, если ничего не работает

1. Убедитесь, что у вас Python 3.8+
2. Установите только tkinter и numpy: `pip install numpy`
3. Запустите: `python gui_launcher_simple.py`
4. Если и это не работает, см. `INSTALL_TROUBLESHOOTING.md`

## ✅ Проверка успешного запуска

После запуска вы должны увидеть:
- Главное окно с вкладками
- Панель инструментов сверху
- Строку состояния снизу
- Возможность переключаться между вкладками

Готово! 🎉
