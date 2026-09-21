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
