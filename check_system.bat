@echo off
chcp 65001 > nul
echo ========================================
echo Проверка статуса торговой системы
echo ========================================
echo.

REM Активация виртуального окружения
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Виртуальное окружение не найдено!
    echo Запустите setup_venv.bat
    pause
    exit /b 1
)

REM Запуск скрипта
python scripts\check_system_status.py

echo.
echo ========================================
pause


