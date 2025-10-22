@echo off
chcp 65001 >nul
echo ========================================
echo УСТАНОВКА ЗАВИСИМОСТЕЙ ДЛЯ НЕЙРО-ИНВЕСТ
echo ========================================
echo.

echo Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ОШИБКА: Python не найден!
    echo Установите Python с https://python.org
    echo Обязательно поставьте галочку "Add Python to PATH"
    pause
    exit /b 1
)

echo Python найден!
echo.

echo Обновление pip...
python -m pip install --upgrade pip
echo.

echo Установка основных зависимостей...
python -m pip install numpy
python -m pip install pandas
python -m pip install scikit-learn
python -m pip install xgboost
echo.

echo Установка зависимостей для данных...
python -m pip install yfinance
python -m pip install requests
python -m pip install loguru
echo.

echo Установка зависимостей для визуализации...
python -m pip install matplotlib
python -m pip install seaborn
echo.

echo Установка остальных зависимостей...
python -m pip install sqlalchemy
python -m pip install pyyaml
python -m pip install python-dotenv
python -m pip install schedule
python -m pip install python-dateutil
python -m pip install pytz
echo.

echo ========================================
echo УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo.

echo Проверка установки...
python -c "import numpy, pandas, sklearn, xgboost, yfinance, loguru; print('Все основные зависимости установлены!')" 2>nul
if %errorlevel% equ 0 (
    echo ✓ Все зависимости работают!
) else (
    echo ⚠ Некоторые зависимости могут быть не установлены
)

echo.
echo Для проверки запустите: python test_dependencies.py
echo.
pause

