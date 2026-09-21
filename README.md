# 🖥️ Monitoring Canggih v16 — Anti Lag Video

**By. Entong Betawi**

Aplikasi monitoring host (ping monitor) berbasis **Python + Tkinter** untuk Windows,
dilengkapi alarm turun, filter grup, tema gelap/terang, dan tampilan foto/video di panel samping.

---

<img width="1076" height="727" alt="image" src="https://github.com/user-attachments/assets/22db862f-a9ec-4940-9fb4-a716b2149413" />


## ✨ Fitur

- **Ping monitoring multithread** — hingga 20 host diproses paralel (ThreadPoolExecutor).
- **Alarm beep otomatis** saat host berubah status dari UP → DOWN (durasi bisa diatur 1–60 detik).
- **Filter tampilan**: Semua / Hanya UP / Hanya DOWN.
- **Filter grup**: kelompokkan host per group, pilih lewat combobox.
- **Tabel interaktif** dengan checkbox centang, warna status (hijau UP, merah DOWN).
- **Kolom yang bisa disembunyikan/ditampilkan** sesuai kebutuhan.
- **Aksi cepat** pada host terpilih:
  - Remote Desktop (`mstsc /v:IP`)
  - Mapping network drive (`\\IP` lewat Explorer)
  - Buka via browser (`http://IP`)
- **Panel media**:
  - Upload foto (JPG/PNG/BMP)
  - Upload & putar video (MP4/AVI/MKV) dengan loop otomatis dan frame rate sesuai file asli
  - Tombol expand/collapse panel media
- **Marquee "Kata-Kata Hari Ini"** — teks berjalan yang bisa diedit sendiri.
- **Tema terang & gelap** dengan preview langsung di jendela pengaturan.
- **Konfigurasi otomatis tersimpan** di `~/monitoring_canggih.json`.
- Password host disimpan **terenkode (XOR + hex)** secara sederhana.

---

## 📋 Persyaratan

- **Windows** (menggunakan `ping -n`, `mstsc`, `explorer`, `winsound`)
- **Python 3.8+**

### Dependensi

| Paket | Kegunaan | Wajib? |
|-------|----------|--------|
| `Pillow` (PIL) | Menampilkan foto & frame video | Opsional (disarankan) |
| `opencv-python` (cv2) | Pemutaran & resize video cepat | Opsional (disarankan) |

Install:

```bash
pip install pillow opencv-python

---

build ke .exe 
simpan file ini dengan nama build.bat

---

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
