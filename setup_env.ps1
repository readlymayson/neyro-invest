# Настройка переменных окружения для системы нейросетевых инвестиций

# Установка кодировки UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "   НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

Write-Host "🔑 Настройка API ключей для системы нейросетевых инвестиций" -ForegroundColor Yellow
Write-Host ""

# Проверка существующих переменных
Write-Host "📋 Текущие переменные окружения:" -ForegroundColor Cyan
Write-Host ""

$deepseekKey = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
$tinkoffToken = [Environment]::GetEnvironmentVariable("TINKOFF_TOKEN", "User")

if ($deepseekKey) {
    Write-Host "✅ DEEPSEEK_API_KEY: Установлен" -ForegroundColor Green
} else {
    Write-Host "❌ DEEPSEEK_API_KEY: Не установлен" -ForegroundColor Red
}

if ($tinkoffToken) {
    Write-Host "✅ TINKOFF_TOKEN: Установлен" -ForegroundColor Green
} else {
    Write-Host "❌ TINKOFF_TOKEN: Не установлен" -ForegroundColor Red
}

Write-Host ""

# Настройка DeepSeek API ключа
Write-Host "💡 Получите API ключ на https://platform.deepseek.com/" -ForegroundColor Yellow
$deepseekInput = Read-Host "Введите ваш DeepSeek API ключ (или нажмите Enter для пропуска)"
if ($deepseekInput) {
    [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", $deepseekInput, "User")
    Write-Host "✅ DEEPSEEK_API_KEY установлен" -ForegroundColor Green
} else {
    Write-Host "⚠️  DEEPSEEK_API_KEY пропущен" -ForegroundColor Yellow
}

Write-Host ""

# Настройка Tinkoff API ключа
Write-Host "💡 Получите токен на https://www.tinkoff.ru/invest/sandbox/" -ForegroundColor Yellow
$tinkoffInput = Read-Host "Введите ваш Tinkoff API токен (или нажмите Enter для пропуска)"
if ($tinkoffInput) {
    [Environment]::SetEnvironmentVariable("TINKOFF_TOKEN", $tinkoffInput, "User")
    Write-Host "✅ TINKOFF_TOKEN установлен" -ForegroundColor Green
} else {
    Write-Host "⚠️  TINKOFF_TOKEN пропущен" -ForegroundColor Yellow
}

Write-Host ""

# Настройка email пароля для уведомлений
Write-Host "💡 Используйте пароль приложения, а не основной пароль!" -ForegroundColor Yellow
$emailInput = Read-Host "Введите пароль приложения для email (или нажмите Enter для пропуска)"
if ($emailInput) {
    [Environment]::SetEnvironmentVariable("EMAIL_PASSWORD", $emailInput, "User")
    Write-Host "✅ EMAIL_PASSWORD установлен" -ForegroundColor Green
} else {
    Write-Host "⚠️  EMAIL_PASSWORD пропущен" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "✅ Настройка завершена!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

Write-Host "📝 Важно:" -ForegroundColor Yellow
Write-Host "  • Перезапустите PowerShell для применения изменений" -ForegroundColor White
Write-Host "  • Переменные окружения будут доступны во всех новых сессиях" -ForegroundColor White
Write-Host "  • Для проверки используйте: python run.py --status" -ForegroundColor White
Write-Host ""

Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")





