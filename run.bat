@echo off
cd /d "%~dp0"
echo Checking for Administrator privileges...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator.
) else (
    echo [WARNING] Not running as Administrator! Hotkeys might not work inside other applications.
    echo To fix this, right-click this run.bat file and select "Run as administrator".
    echo.
    choice /c YN /m "Do you want to continue anyway?"
    if errorlevel 2 exit
)

echo Starting Audio Assistant 3...
.venv\Scripts\python.exe audio_assistant_3.py
pause
