@echo off
chcp 65001 >nul
echo ========================================
echo   Отображение анализа нейросетей
echo ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python scripts\show_neural_analysis.py %*
) else (
    python scripts\show_neural_analysis.py %*
)

pause

