# Устранение проблем с установкой GUI

## Проблема с asyncio-mqtt

Если вы получаете ошибку при установке `asyncio-mqtt`, это означает проблемы с подключением к PyPI или пакет недоступен.

### Решения:

#### 1. Используйте минимальные зависимости
```bash
pip install -r requirements_gui_minimal.txt
```

#### 2. Установите зависимости вручную
```bash
pip install numpy pandas matplotlib loguru pyyaml requests
```

#### 3. Используйте скрипт установки
```bash
python install_gui_deps.py
```

#### 4. Запустите упрощенную версию
```bash
python gui_launcher_simple.py
```

## Другие частые проблемы

### Ошибка "tkinter не найден"

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install tkinter
```

**Windows:**
tkinter включен в стандартную установку Python

### Ошибка "matplotlib не найден"

```bash
pip install matplotlib
```

Если не помогает:
```bash
pip install --upgrade pip
pip install matplotlib --no-cache-dir
```

### Проблемы с сетью

Если у вас проблемы с подключением к PyPI:

1. **Используйте зеркало:**
```bash
pip install -i https://pypi.douban.com/simple/ numpy pandas matplotlib
```

2. **Установите офлайн:**
Скачайте wheel-файлы и установите локально:
```bash
pip install package.whl
```

3. **Используйте conda:**
```bash
conda install numpy pandas matplotlib
```

## Минимальная установка

Для работы GUI достаточно:
- Python 3.8+
- tkinter (встроен в Python)
- numpy
- pandas  
- matplotlib
- loguru
- pyyaml

Остальные пакеты опциональны.

## Запуск без всех зависимостей

Если не удается установить все зависимости, можно запустить базовую версию:

```bash
python gui_launcher_simple.py
```

Эта версия работает с минимальным набором пакетов и имеет упрощенный функционал.

## Проверка установки

Проверьте, что Python может импортировать основные модули:

```python
import tkinter
import numpy
import pandas
import matplotlib
print("Все основные модули доступны!")
```

## Альтернативные способы запуска

### 1. Прямой запуск
```bash
cd src/gui
python -c "from main_window import MainWindow; MainWindow().run()"
```

### 2. Через Python модуль
```bash
python -m src.gui.main_window
```

### 3. Интерактивный режим
```python
from src.gui.main_window import MainWindow
app = MainWindow()
app.run()
```

## Получение помощи

Если проблемы не решаются:

1. Проверьте логи в папке `logs/`
2. Запустите с отладкой: `python -v gui_launcher_simple.py`
3. Создайте issue с описанием проблемы и логами
