@echo off
chcp 65001 >nul
echo ========================================
echo Тестирование Web GUI API
echo ========================================
echo.

call venv\Scripts\activate.bat
python test_web_gui_status.py

echo.
pause

