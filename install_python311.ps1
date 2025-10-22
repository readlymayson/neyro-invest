# Скрипт автоматической установки Python 3.11 для Windows
# Запустите от имени администратора: PowerShell -ExecutionPolicy Bypass -File install_python311.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Python 3.11 Installation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# URL для скачивания Python 3.11.9
$pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$installerPath = "$env:TEMP\python-3.11.9-amd64.exe"

Write-Host "1. Скачивание Python 3.11.9..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "   ✓ Загружено успешно" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Ошибка загрузки: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2. Запуск установщика..." -ForegroundColor Yellow
Write-Host "   ВАЖНО: В установщике выберите:" -ForegroundColor Cyan
Write-Host "   ✓ Add Python 3.11 to PATH" -ForegroundColor Green
Write-Host "   ✓ Install for all users (optional)" -ForegroundColor Green
Write-Host ""

# Запуск установщика
Start-Process -FilePath $installerPath -Wait

Write-Host ""
Write-Host "3. Проверка установки..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# Обновляем PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Проверка установки
$python311 = Get-Command python3.11 -ErrorAction SilentlyContinue
if ($python311) {
    Write-Host "   ✓ Python 3.11 установлен успешно!" -ForegroundColor Green
    & python3.11 --version
} else {
    Write-Host "   ⚠ Python 3.11 установлен, но требуется перезагрузка терминала" -ForegroundColor Yellow
    Write-Host "   Закройте и откройте PowerShell заново" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Установка завершена!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Следующие шаги:" -ForegroundColor Cyan
Write-Host "1. Закройте и откройте PowerShell/CMD заново" -ForegroundColor White
Write-Host "2. Перейдите в папку проекта" -ForegroundColor White
Write-Host "3. Запустите: setup_python311_venv.bat" -ForegroundColor White
Write-Host ""

# Удаление установщика
Remove-Item $installerPath -Force


