@echo off
title Menjalankan Monitoring Canggih
color 0A

:: Berpindah ke direktori tempat file BAT berada
cd /d "%~dp0"

echo ============================================
echo   Menjalankan Aplikasi Monitoring Canggih...
echo ============================================
echo.

:: Cek apakah python tersedia
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan!
    echo Pastikan Python sudah terinstall dan masuk ke system PATH.
    echo.
    pause
    exit /b
)

:: Menjalankan script python
python monitoring_canggih.py

:: Jika aplikasi ditutup karena error, layar tidak akan langsung hilang
if errorlevel 1 (
    echo.
    echo [ERROR] Aplikasi berhenti secara paksa. Lihat log error di atas.
    pause
)