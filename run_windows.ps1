# Файл запуска системы нейросетевых инвестиций для Windows PowerShell

# Установка кодировки UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Установка политики выполнения (если нужно)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "   СИСТЕМА НЕЙРОСЕТЕВЫХ ИНВЕСТИЦИЙ" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Проверка Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python 3.8 или выше" -ForegroundColor Red
    Write-Host "Скачать: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Проверка виртуального окружения
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "🔄 Активация виртуального окружения..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  Виртуальное окружение не найдено" -ForegroundColor Yellow
    Write-Host "Создайте его командой: python -m venv venv" -ForegroundColor Yellow
}

# Проверка зависимостей
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ Файл requirements.txt не найден!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Установка зависимостей (если нужно)
Write-Host "🔍 Проверка зависимостей..." -ForegroundColor Yellow
try {
    python -c "import tensorflow" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📦 Установка зависимостей..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
} catch {
    Write-Host "📦 Установка зависимостей..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Проверка конфигурации
if (-not (Test-Path "config\main.yaml")) {
    Write-Host "❌ Файл конфигурации не найден!" -ForegroundColor Red
    Write-Host "📋 Создание базовой конфигурации..." -ForegroundColor Yellow
    if (Test-Path "config\examples\beginners.yaml") {
        Copy-Item "config\examples\beginners.yaml" "config\main.yaml"
        Write-Host "✅ Базовая конфигурация создана" -ForegroundColor Green
    } else {
        Write-Host "❌ Примеры конфигурации не найдены" -ForegroundColor Red
        Write-Host ""
        Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

# Создание необходимых директорий
@("logs", "models", "data") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ | Out-Null
        Write-Host "📁 Создана директория: $_" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🚀 Запуск системы..." -ForegroundColor Green
Write-Host ""

# Запуск с обработкой ошибок
try {
    python run.py $args
    Write-Host ""
    Write-Host "✅ Система завершила работу" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "❌ Произошла ошибка при запуске системы" -ForegroundColor Red
    Write-Host "📋 Проверьте логи в папке logs\" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")





