@echo off
chcp 65001 >nul
REM Файл запуска системы нейросетевых инвестиций для Windows

title Система нейросетевых инвестиций

echo.
echo ========================================
echo    СИСТЕМА НЕЙРОСЕТЕВЫХ ИНВЕСТИЦИЙ
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8 или выше
    echo Скачать: https://www.python.org/downloads/
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

REM Проверка виртуального окружения
if exist "venv\Scripts\activate.bat" (
    echo 🔄 Активация виртуального окружения...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Виртуальное окружение не найдено
    echo Создайте его командой: python -m venv venv
)

REM Проверка зависимостей
if not exist "requirements.txt" (
    echo ❌ Файл requirements.txt не найден!
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

REM Установка зависимостей (если нужно)
echo 🔍 Проверка зависимостей...
if errorlevel 1 (
    echo 📦 Установка зависимостей...
    pip install -r requirements.txt
)

REM Проверка конфигурации
if not exist "config\main.yaml" (
    echo ❌ Файл конфигурации не найден!
    echo 📋 Создание базовой конфигурации...
    if exist "config\examples\beginners.yaml" (
        copy "config\examples\beginners.yaml" "config\main.yaml"
        echo ✅ Базовая конфигурация создана
    ) else (
        echo ❌ Примеры конфигурации не найдены
        echo.
        echo Нажмите любую клавишу для выхода...
        pause >nul
        exit /b 1
    )
)

REM Создание необходимых директорий
if not exist "logs" mkdir logs
if not exist "models" mkdir models
if not exist "data" mkdir data

echo.
echo 🚀 Запуск системы...
echo.

REM Запуск с обработкой ошибок
python run.py %*

echo.
if errorlevel 1 (
    echo ❌ Произошла ошибка при запуске системы
    echo 📋 Проверьте логи в папке logs\
    echo.
) else (
    echo ✅ Система завершила работу
    echo.
)

echo Нажмите любую клавишу для выхода...
pause >nul





