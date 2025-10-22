@echo off
chcp 65001 >nul
title Neyro-Invest - Web GUI

echo ============================================================
echo     🚀 NEYRO-INVEST WEB GUI
echo     Запуск веб-интерфейса
echo ============================================================
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

REM Активация виртуального окружения если есть
if exist venv\Scripts\activate.bat (
    echo ✓ Активация виртуального окружения...
    call venv\Scripts\activate.bat
    echo ✓ Виртуальное окружение активировано
    echo.
) else (
    echo ⚠️  Виртуальное окружение не найдено
    echo    Рекомендуется создать: python -m venv venv
    echo.
)

REM Запуск веб-GUI
echo.
echo Запуск веб-сервера...
echo.
python web_launcher.py

pause

