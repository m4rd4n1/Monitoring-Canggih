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
    echo [ERROR] Python tidak ditemukan. Install Python terlebih dahulu.
    pause
    exit /b 1
)

echo [1/3] Memeriksa modul pendukung (PyInstaller, Pillow, OpenCV, ReportLab)...
pip install --upgrade pyinstaller Pillow opencv-python reportlab >nul 2>&1

echo [2/3] Membuild EXE... (Mohon tunggu beberapa saat)
python -m PyInstaller --onefile --noconsole --clean --name "MonitoringCanggih" "monitoring_canggih.py"

echo [3/3] Memindahkan hasil build...
if exist "dist\MonitoringCanggih.exe" (
    copy /y "dist\MonitoringCanggih.exe" "MonitoringCanggih.exe" >nul
    echo.
    echo ============================================
    echo   BERHASIL! Cek file MonitoringCanggih.exe
    echo ============================================
) else (
    echo [ERROR] Build gagal. Silakan periksa log di atas.
)
pause >nul
endlocal