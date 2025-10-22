@echo off
chcp 65001 > nul
title Нейросетевая система инвестиций - GUI

echo ╔══════════════════════════════════════════════════════════════╗
echo ║              Нейросетевая система инвестиций                 ║
echo ║                     Запуск GUI                               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Проверка наличия Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Ошибка: Python не найден в системе
    echo Установите Python 3.8 или выше с https://python.org
    pause
    exit /b 1
)

REM Проверка наличия виртуального окружения
if not exist "venv\" (
    echo Создание виртуального окружения...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Ошибка создания виртуального окружения
        pause
        exit /b 1
    )
)

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Установка зависимостей
echo Проверка и установка зависимостей...
python install_gui_deps.py
if %errorlevel% neq 0 (
    echo.
    echo Попытка установки через pip...
    pip install -r requirements_gui_minimal.txt --quiet
)

REM Запуск GUI приложения
echo.
echo Запуск графического интерфейса...
echo.
python gui_launcher_simple.py

REM Деактивация виртуального окружения
deactivate

echo.
echo Приложение завершено.
pause
