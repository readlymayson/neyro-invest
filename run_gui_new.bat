@echo off
chcp 65001 >nul
title GUI Системы нейросетевых инвестиций

echo.
echo ========================================
echo   GUI СИСТЕМЫ НЕЙРОСЕТЕВЫХ ИНВЕСТИЦИЙ
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python найден

REM Активация виртуального окружения если есть
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Активация виртуального окружения...
    call venv\Scripts\activate.bat
    echo ✅ Виртуальное окружение активировано
) else (
    echo ⚠️  Виртуальное окружение не найдено, используем системный Python
)

REM Установка зависимостей
echo.
echo 📦 Проверка и установка зависимостей...
python -c "import tkinter, matplotlib, pandas, numpy, loguru, yaml" 2>nul
if %errorlevel% neq 0 (
    echo 📥 Установка зависимостей...
    if exist "requirements_gui_minimal.txt" (
        pip install -r requirements_gui_minimal.txt --quiet
    ) else (
        pip install matplotlib pandas numpy loguru pyyaml --quiet
    )
    if %errorlevel% neq 0 (
        echo ❌ Ошибка установки зависимостей
        pause
        exit /b 1
    )
    echo ✅ Зависимости установлены
) else (
    echo ✅ Все зависимости уже установлены
)

REM Запуск GUI
echo.
echo 🖥️  Запуск графического интерфейса...
echo ========================================
echo.

python gui_launcher_new.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Ошибка запуска GUI
    echo Проверьте логи выше для диагностики
    pause
    exit /b 1
)

echo.
echo ✅ GUI завершен
pause
