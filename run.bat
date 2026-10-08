@echo off 
title Menjalankan Monitoring Canggih 
color 0B

echo =================================================== 
echo       MEMULAI APLIKASI MONITORING CANGGIH 
echo =================================================== 
echo. 
echo Sedang memuat modul dan tampilan antarmuka...

:: Menjalankan script Python 
python monitoring_canggih.py

:: Jika terjadi error dan keluar sendiri 
if errorlevel 1 ( 
    echo. 
    echo [ERROR] Aplikasi berhenti. Silakan cek pesan di atas. 
    pause 
)