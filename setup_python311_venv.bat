@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Создание виртуального окружения
echo   Python 3.11
echo ========================================
echo.

REM Проверка наличия Python 3.11
python3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.11 не найден!
    echo.
    echo Установите Python 3.11:
    echo 1. Запустите: install_python311.ps1 (PowerShell)
    echo 2. Или скачайте вручную: https://www.python.org/downloads/release/python-3119/
    echo.
    pause
    exit /b 1
)

echo ✓ Python 3.11 найден
python3.11 --version
echo.

REM Создание виртуального окружения
echo Создание виртуального окружения venv311...
python3.11 -m venv venv311
if %errorlevel% neq 0 (
    echo ❌ Ошибка создания venv
    pause
    exit /b 1
)
echo ✓ Виртуальное окружение создано
echo.

REM Активация venv
echo Активация venv...
call venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Ошибка активации venv
    pause
    exit /b 1
)
echo ✓ venv активирован
echo.

REM Обновление pip
echo Обновление pip...
python -m pip install --upgrade pip --quiet
echo ✓ pip обновлен
echo.

REM Установка зависимостей
echo Установка зависимостей из requirements.txt...
echo (это может занять несколько минут)
echo.
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ⚠ Возможны ошибки при установке некоторых пакетов
    echo Попробуйте установить минимальные зависимости:
    echo pip install -r requirements_minimal.txt
    echo.
) else (
    echo.
    echo ✓ Все зависимости установлены успешно!
)

echo.
echo ========================================
echo   Готово!
echo ========================================
echo.
echo Виртуальное окружение создано и активировано.
echo.
echo Для запуска системы используйте:
echo   python run.py --config config/test_config.yaml
echo.
echo Для тестирования T-Bank:
echo   python examples/tbank_sandbox_test.py
echo.
echo Для активации venv в будущем:
echo   venv311\Scripts\activate
echo.
pause


