@echo off
chcp 65001 >nul
title Neyro-Invest - Настройка виртуального окружения

echo ================================================================
echo     🔧 NEYRO-INVEST - Настройка виртуального окружения
echo ================================================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo.
    echo Установите Python 3.11+ с https://www.python.org/
    pause
    exit /b 1
)

echo Python версия:
python --version
echo.

REM Создание виртуального окружения
echo ================================================================
echo     Создание виртуального окружения...
echo ================================================================
echo.

if exist venv (
    echo ⚠️  Виртуальное окружение уже существует!
    echo.
    choice /C YN /M "Удалить и создать заново"
    if errorlevel 2 goto :skip_create
    if errorlevel 1 (
        echo Удаление старого окружения...
        rmdir /s /q venv
    )
)

echo Создание нового виртуального окружения...
python -m venv venv

if errorlevel 1 (
    echo ❌ Ошибка создания виртуального окружения!
    pause
    exit /b 1
)

echo ✓ Виртуальное окружение создано
echo.

:skip_create

REM Активация виртуального окружения
echo ================================================================
echo     Активация виртуального окружения...
echo ================================================================
echo.

call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ Ошибка активации виртуального окружения!
    pause
    exit /b 1
)

echo ✓ Виртуальное окружение активировано
echo.

REM Обновление pip
echo ================================================================
echo     Обновление pip...
echo ================================================================
echo.

python -m pip install --upgrade pip

echo ✓ pip обновлен
echo.

REM Установка зависимостей
echo ================================================================
echo     Установка зависимостей для Web GUI...
echo ================================================================
echo.

echo Устанавливаю основные зависимости...
pip install fastapi uvicorn[standard] pydantic websockets loguru pyyaml python-dotenv

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей!
    pause
    exit /b 1
)

echo.
echo ✓ Основные зависимости установлены
echo.

REM Установка дополнительных зависимостей (если нужны)
choice /C YN /M "Установить все зависимости из requirements.txt"
if errorlevel 2 goto :skip_full
if errorlevel 1 (
    echo.
    echo Установка полного набора зависимостей...
    pip install -r requirements.txt
    
    if errorlevel 1 (
        echo ⚠️  Некоторые зависимости не установлены
        echo    Но Web GUI должен работать с уже установленными
    ) else (
        echo ✓ Все зависимости установлены
    )
)

:skip_full

REM Проверка установленных пакетов
echo.
echo ================================================================
echo     Установленные пакеты:
echo ================================================================
echo.

pip list | findstr /I "fastapi uvicorn pydantic websockets loguru pyyaml"

echo.
echo ================================================================
echo     ✅ НАСТРОЙКА ЗАВЕРШЕНА!
echo ================================================================
echo.
echo Теперь вы можете запустить Web GUI:
echo.
echo   1. Активируйте окружение:
echo      venv\Scripts\activate.bat
echo.
echo   2. Запустите Web GUI:
echo      python web_launcher.py
echo.
echo   Или используйте:
echo      run_web_gui.bat (автоматически активирует окружение)
echo.

pause

