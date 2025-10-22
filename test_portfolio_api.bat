@echo off
chcp 65001 >nul
echo ========================================
echo Тестирование API портфеля
echo ========================================
echo.

call venv\Scripts\activate.bat
python test_portfolio_api.py

echo.
pause
