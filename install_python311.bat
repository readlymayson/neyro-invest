@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Python 3.11 Installation
echo ========================================
echo.

echo Downloading Python 3.11.9 installer...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python-3.11.9-amd64.exe'"

if %errorlevel% neq 0 (
    echo Failed to download installer
    echo.
    echo Please download manually from:
    echo https://www.python.org/downloads/release/python-3119/
    pause
    exit /b 1
)

echo.
echo Starting Python 3.11.9 installer...
echo.
echo IMPORTANT: In the installer window:
echo   [x] Add Python 3.11 to PATH
echo   [x] Install for all users (optional)
echo.
pause

start /wait %TEMP%\python-3.11.9-amd64.exe

echo.
echo Installation completed!
echo.
echo Please CLOSE this window and open a NEW command prompt.
echo Then run: setup_python311_venv.bat
echo.
pause


