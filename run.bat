@echo off
chcp 65001 > nul
echo ========================================
echo Neyro-Invest Interactive Console
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

REM Запуск в интерактивном режиме (по умолчанию) с конфигурацией config\main.yaml
python run.py --config config\main.yaml

echo.
echo ========================================
pause
