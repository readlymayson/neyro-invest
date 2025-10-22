@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Проверка Python и запуск системы
echo ========================================
echo.

echo Проверяю установленные версии Python...
echo.

REM Поиск Python 3.11
where python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo Текущая версия Python:
    python --version
    echo.
)

REM Поиск py launcher
where py.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo Доступные версии через py launcher:
    py -0
    echo.
)

echo ----------------------------------------
echo.

REM Пытаемся найти Python 3.11
set PYTHON311=

REM Проверяем py launcher
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python 3.11 найден через py launcher
    set PYTHON311=py -3.11
    goto :found
)

REM Проверяем python3.11
python3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python 3.11 найден как python3.11
    set PYTHON311=python3.11
    goto :found
)

REM Проверяем основной python
python --version 2>&1 | findstr "3.11" >nul
if %errorlevel% equ 0 (
    echo ✓ Python 3.11 установлен как основной
    set PYTHON311=python
    goto :found
)

REM Проверяем стандартные пути
if exist "C:\Python311\python.exe" (
    echo ✓ Python 3.11 найден в C:\Python311
    set PYTHON311=C:\Python311\python.exe
    goto :found
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
    echo ✓ Python 3.11 найден в AppData
    set PYTHON311=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
    goto :found
)

:notfound
echo.
echo ❌ Python 3.11 не найден!
echo.
echo Возможные причины:
echo 1. Python 3.11 не установлен
echo 2. Нужно закрыть и открыть НОВОЕ окно CMD
echo 3. Python 3.11 установлен в нестандартную папку
echo.
echo Решение:
echo 1. ЗАКРОЙТЕ это окно
echo 2. Откройте НОВОЕ окно CMD
echo 3. Запустите этот скрипт снова
echo.
echo Или установите Python 3.11:
echo https://www.python.org/downloads/release/python-3119/
echo.
pause
exit /b 1

:found
echo.
echo Используемый Python:
%PYTHON311% --version
echo.

REM Проверка venv
if exist "venv311\Scripts\activate.bat" (
    echo ✓ Виртуальное окружение venv311 существует
    echo.
    echo Активирую venv...
    call venv311\Scripts\activate.bat
    
    echo.
    echo ========================================
    echo   venv активировано!
    echo ========================================
    echo.
    
    goto :menu
) else (
    echo ⚠ Виртуальное окружение venv311 не найдено
    echo.
    echo Создать виртуальное окружение? (Y/N)
    set /p CREATE_VENV=
    
    if /i "%CREATE_VENV%"=="Y" goto :create_venv
    if /i "%CREATE_VENV%"=="Д" goto :create_venv
    goto :end
)

:create_venv
echo.
echo Создание виртуального окружения...
%PYTHON311% -m venv venv311
if %errorlevel% neq 0 (
    echo ❌ Ошибка создания venv
    pause
    exit /b 1
)

echo ✓ venv создано
echo.
echo Активация venv...
call venv311\Scripts\activate.bat

echo.
echo Обновление pip...
python -m pip install --upgrade pip --quiet

echo.
echo Установка зависимостей (это займет 2-3 минуты)...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ⚠ Некоторые зависимости не установились
    echo Попробуйте установить вручную:
    echo   pip install -r requirements.txt
    echo.
    pause
) else (
    echo.
    echo ✓ Все зависимости установлены!
)

:menu
echo.
echo ========================================
echo   Что запустить?
echo ========================================
echo.
echo 1. Тест T-Bank песочницы
echo 2. Торговая система (тестовая конфигурация)
echo 3. GUI интерфейс
echo 4. Выход
echo.
set /p CHOICE=Выберите (1-4): 

if "%CHOICE%"=="1" goto :test_tbank
if "%CHOICE%"=="2" goto :run_system
if "%CHOICE%"=="3" goto :run_gui
if "%CHOICE%"=="4" goto :end

echo Неверный выбор
goto :menu

:test_tbank
echo.
echo ========================================
echo   Запуск теста T-Bank
echo ========================================
echo.
python examples/tbank_sandbox_test.py
echo.
pause
goto :menu

:run_system
echo.
echo ========================================
echo   Запуск торговой системы
echo ========================================
echo.
python run.py --config config/test_config.yaml
echo.
pause
goto :menu

:run_gui
echo.
echo ========================================
echo   Запуск GUI
echo ========================================
echo.
python gui_launcher.py
echo.
pause
goto :menu

:end
echo.
echo До свидания!
echo.
timeout /t 2 >nul
exit /b 0


