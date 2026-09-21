@echo off
setlocal EnableDelayedExpansion
title Build Monitoring Canggih
cd /d "%~dp0"

echo ============================================
echo   Build Monitoring Canggih menjadi EXE
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan. Install Python 3.6+ terlebih dahulu.
    pause
    exit /b 1
)

echo [1/3] Memeriksa instalasi PyInstaller...
python -m pip install --upgrade pyinstaller >nul 2>&1

echo [2/3] Membuild EXE... (Mohon tunggu)
python -m PyInstaller --onefile --noconsole --clean --name "MonitoringCanggih" "monitoring_canggih.py"

if exist "dist\MonitoringCanggih.exe" (
    copy /y "dist\MonitoringCanggih.exe" "MonitoringCanggih.exe" >nul
    echo.
    echo ============================================
    echo   BERHASIL! Cek file MonitoringCanggih.exe
    echo ============================================
) else (
    echo [ERROR] Build gagal.
)
pause >nul
endlocal