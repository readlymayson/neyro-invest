@echo off
chcp 65001 > nul
title Перезапуск виртуального окружения

echo ╔══════════════════════════════════════════════════════════════╗
echo ║              Перезапуск виртуального окружения              ║
echo ║                     Система инвестиций                      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Проверка наличия Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ошибка: Python не найден в системе
    echo Установите Python 3.8 или выше с https://python.org
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Запуск Python скрипта
python restart_venv.py

REM Проверка результата
if %errorlevel% equ 0 (
    echo.
    echo 🎉 Перезапуск завершен успешно!
    echo.
    echo Теперь можно запустить GUI:
    echo   run_gui.bat
    echo   или
    echo   python gui_launcher_simple.py
) else (
    echo.
    echo ❌ Произошли ошибки при перезапуске
    echo Проверьте сообщения выше для диагностики
)

echo.
pause
