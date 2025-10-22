@echo off
chcp 65001 >nul
title Настройка переменных окружения

echo.
echo ========================================
echo   НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
echo ========================================
echo.

echo 🔑 Настройка API ключей для системы нейросетевых инвестиций
echo.

REM Проверка существующих переменных
echo 📋 Текущие переменные окружения:
echo.
if defined DEEPSEEK_API_KEY (
    echo ✅ DEEPSEEK_API_KEY: Установлен
) else (
    echo ❌ DEEPSEEK_API_KEY: Не установлен
)

if defined TINKOFF_TOKEN (
    echo ✅ TINKOFF_TOKEN: Установлен
) else (
    echo ❌ TINKOFF_TOKEN: Не установлен
)

echo.

REM Настройка DeepSeek API ключа
echo Warnung: Получите API ключ на https://platform.deepseek.com/
set /p deepseek_key="Введите ваш DeepSeek API ключ (или нажмите Enter для пропуска): "
if not "%deepseek_key%"=="" (
    setx DEEPSEEK_API_KEY "%deepseek_key%"
    echo ✅ DEEPSEEK_API_KEY установлен
) else (
    echo ⚠️  DEEPSEEK_API_KEY пропущен
)

echo.

REM Настройка Tinkoff API ключа
echo Warnung: Получите токен на https://www.tinkoff.ru/invest/sandbox/
set /p tinkoff_token="Введите ваш Tinkoff API токен (или нажмите Enter для пропуска): "
if not "%tinkoff_token%"=="" (
    setx TINKOFF_TOKEN "%tinkoff_token%"
    echo ✅ TINKOFF_TOKEN установлен
) else (
    echo ⚠️  TINKOFF_TOKEN пропущен
)

echo.

REM Настройка email пароля для уведомлений
echo Warnung: Используйте пароль приложения, а не основной пароль!
set /p email_password="Введите пароль приложения для email (или нажмите Enter для пропуска): "
if not "%email_password%"=="" (
    setx EMAIL_PASSWORD "%email_password%"
    echo ✅ EMAIL_PASSWORD установлен
) else (
    echo ⚠️  EMAIL_PASSWORD пропущен
)

echo.
echo ========================================
echo ✅ Настройка завершена!
echo ========================================
echo.
echo 📝 Важно:
echo   • Перезапустите командную строку для применения изменений
echo   • Переменные окружения будут доступны во всех новых сессиях
echo   • Для проверки используйте: python run.py --status
echo.

echo Нажмите любую клавишу для выхода...
pause >nul





