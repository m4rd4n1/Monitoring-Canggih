<img width="1919" height="1031" alt="image" src="https://github.com/user-attachments/assets/2bd9de77-4ec2-40ae-ac09-ae77be77a314" />
<img width="1019" height="607" alt="image" src="https://github.com/user-attachments/assets/971b6488-bec6-4f88-b0e7-cf35ea062144" />

# 🖥️ Monitoring Canggih

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)

**Monitoring Canggih** adalah aplikasi desktop berbasis Python & Tkinter yang dirancang untuk memantau status jaringan (Ping) host/perangkat secara real-time. Aplikasi ini dilengkapi dengan notifikasi suara/alarm, pelaporan rekap offline harian, widget cuaca, jadwal sholat, hingga integrasi pemutar media.

---

## ✨ Fitur Utama

- **Real-time Host Ping Monitoring**: Memantau status jaringan (*UP* / *DOWN*), *Latency* (ms), dan *TTL* secara presisi.
- **Alarm & Notifikasi Suara**:
  - Mengeluarkan bunyi alarm beep dan *Voice Speech* ("Mati") saat host mengalami *DOWN*.
  - Opsi *Mute* / *Stop Alarm* dan durasi alarm yang dapat diatur.
- **Rekap Data Offline Harian**:
  - Menyimpan log riwayat perangkat yang mengalami gangguan beserta durasi perbaikannya.
  - Sisi kanan jendela rekap dilengkapi **Panel Rincian Status Offline** yang menampilkan detail perangkat *DOWN* secara *real-time*.
  - Filter pencarian berdasarkan **Tanggal** dan **Group/Kategori**.
  - Ekspor laporan rekap ke format **PDF** dan **CSV**.
- **Aksi Cepat Remote**:
  - Direct Remote Desktop (RDP - `mstsc`).
  - Direct Open Explorer / Mapping IP (`\\IP`).
  - Direct Open Web Browser (`http://IP`).
- **Dashboard & Widget Interaktif**:
  - Jam digital real-time beserta indikator waktu.
  - Widget perkiraan cuaca lokal (*API Integration*).
  - Jadwal sholat harian otomatis disesuaikan (*API Integration*).
  - Display foto/video samping dan panel Doa Harian.
  - Running text / Teks berjalan (*Marquee*) untuk catatan/kata-kata hari ini.
- **Kustomisasi & Keamanan**:
  - Dukungan **Tema Terang (Light Mode)** dan **Tema Gelap (Dark Mode)**.
  - Fitur **Backup & Restore** data konfigurasi (*JSON*).
  - Enkripsi sederhana untuk penyimpanan password kredensial remote.

---

## 🛠️ Persyaratan Sistem & Dependensi

Aplikasi ini menggunakan **Python 3.8+** pada sistem operasi Windows.

### Modul Python yang Dibutuhkan:
- `Pillow` (Pengolahan gambar)
- `opencv-python` (Pemutaran video)
- `reportlab` (Pembuatan laporan ekspor PDF)
- `pyinstaller` (Opsional, untuk kompilasi ke `.exe`)

---

## 🚀 Cara Instalasi & Menjalankan

### 1. Cloning Repository
```bash
git clone [https://github.com/USERNAME_ANDA/monitoring-canggih.git](https://github.com/USERNAME_ANDA/monitoring-canggih.git)
cd monitoring-canggih

2. Instalasi Dependensi
Jalankan perintah berikut di Command Prompt / Terminal:

Bash
pip install Pillow opencv-python reportlab pyinstaller
3. Menjalankan Aplikasi
Anda dapat menjalankan aplikasi secara langsung dengan mengetik:

Bash
python monitoring_canggih.py
Atau cukup klik 2x pada file run.bat.

📦 Kompilasi ke File .exe (Standalone)
Jika Anda ingin membuat aplikasi menjadi file executable tunggal tanpa membutuhkan instalasi Python di komputer lain:

Jalankan script build.bat.

Tunggu proses build PyInstaller selesai.

File MonitoringCanggih.exe akan terbentuk di folder utama.

📁 Struktur Direktori
Plaintext
├── monitoring_canggih.py   # Code utama aplikasi (Single-file GUI & Engine)
├── run.bat                 # Shortcut untuk menjalankan script Python
├── build.bat               # Script otomatisasi kompilasi PyInstaller ke EXE
├── README.md               # Dokumentasi proyek
└── monitoring_canggih.json # File penyimpanan data & konfigurasi (Otomatis dibuat)
👨‍💻 Penulis & Kontak
Monitoring Canggih
Developed by Entong Betawi

WhatsApp / Kontak: 0898 33 78 733

Dukungan (Gopay / OVO): 0898 33 78 733

📄 Lisensi
Proyek ini terlisensi di bawah MIT License. Silakan gunakan dan kembangkan sesuai kebutuhan Anda.
