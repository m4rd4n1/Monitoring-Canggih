# -*- coding: utf-8 -*-
# =====================================================================
# MONITORING CANGGIH - By. Entong Betawi
# (v43 - Rekap Offline dengan Panel Detail Status Offline di Ruang Kosong)
# =====================================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess, re, json, os, sys, threading, time, winsound, math
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

APP = "Monitoring Canggih"
WM  = "By. Entong Betawi"

def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def cfg_path():
    return os.path.join(os.path.expanduser("~"), "monitoring_canggih.json")

# ---------- Cek Dependensi ----------
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ---------- Keamanan Sederhana ----------
def xor(s, k="entong"):
    if not s: return ""
    raw, kb = s.encode("utf-8"), k.encode("utf-8")
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw)).hex()

def unx(s, k="entong"):
    if not s: return ""
    try:
        kb = k.encode("utf-8")
        return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(bytes.fromhex(s))).decode("utf-8")
    except Exception:
        return ""

def make_icon(size=64):
    S = size
    img = tk.PhotoImage(width=S, height=S)
    f = S / 64.0
    def rect(x1, y1, x2, y2, col, frame=None):
        for x in range(int(x1 * f), int(x2 * f) + 1):
            for y in range(int(y1 * f), int(y2 * f) + 1):
                if frame is None or x <= frame[0]*f or x >= frame[1]*f or y <= frame[2]*f or y >= frame[3]*f:
                    img.put(col, (x, y))
    rect(6,  6, 57, 39, "#1e3a5f")
    rect(9,  9, 54, 36, "#3b82c4", frame=(8, 55, 8, 37))
    rect(50, 9, 53, 12, "#4ade80")
    rect(28, 40, 36, 48, "#1e3a5f")
    rect(16, 48, 48, 53, "#1e3a5f")
    return img

COLUMNS = [
    ("status",  70,  "Status",      True),
    ("group",   100, "Group",       True),
    ("nama",    160, "Nama",        True),
    ("ip",      130, "IP Address",  True),
    ("time",    75,  "Time (ms)",   True),
    ("ttl",     55,  "TTL",         True),
    ("down",    220, "Durasi Down", True),
    ("ctl",     85,  "Timer",       True),
    ("ket",     300, "Keterangan",  True)
]

DOA_DEFAULT = {
    "judul": "Doa Lancar Rezeki, Sehat & Terbaik",
    "arab": "رَبِّ إِنِّي لِمَا أَنْزَلْتَ إِلَيَّ مِنْ خَيْرٍ فَقِيرٌ ۝ رَبِّ اشْرَحْ لِي صَدْرِي وَيَسِّرْ لِي أَمْرِي ۝ رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
    "latin": "Rabbi inni limaa anzalta ilayya min khairin faqir. Rabbi isyrah li sadri wa yassir li amri. Rabbanaa aatinaa fid-dunyaa hasanah, wafil-aakhirati hasanah, wa qinaa 'adzaaban-naar.",
    "indo": "Ya Tuhanku, sungguh aku membutuhkan segala kebaikan yang Engkau turunkan kepadaku (lancarkanlah rezekiku). Ya Tuhanku, lapangkanlah dadaku dan mudahkanlah urusanku. Ya Tuhan kami, berilah kami kebaikan di dunia dan kebaikan di akhirat, serta lindungilah kami dari azab neraka."
}

THEMES = {
    "terang": {
        "bg": "#f0f0f0", "fg": "#111827", "tree_bg": "#ffffff", "tree_fg": "#000000",
        "down_bg": "#ffcccc", "btn_bg": "#e1e1e1", "btn_fg": "#000000", "entry_bg": "#ffffff",
        "entry_fg": "#000000", "caption_fg": "#1e3a5f", "combo_fg": "#000000",
        "dash_bg": "#ffffff", "sholat_bg": "#f3f4f6", "sholat_fg": "#1f2937"
    },
    "gelap": {
        "bg": "#2b2b2b", "fg": "#f3f4f6", "tree_bg": "#1e1e1e", "tree_fg": "#e8e8e8",
        "down_bg": "#8b1a1a", "btn_bg": "#3d3d3d", "btn_fg": "#e8e8e8", "entry_bg": "#1e1e1e",
        "entry_fg": "#e8e8e8", "caption_fg": "#9ec5fe", "combo_fg": "#000000",
        "dash_bg": "#1f2937", "sholat_bg": "#374151", "sholat_fg": "#f9fafb"
    }
}

IMG_W, IMG_H = 236, 140

class App:
    def __init__(self, root):
        self.root = root
        root.title(f"{APP}  -  {WM}")
        root.geometry("1180x750")
        root.minsize(980, 600)

        self.hosts = []
        self.status = {}
        self.delay = tk.IntVar(value=3)
        self.alarm_on = tk.BooleanVar(value=True)
        self.alarm_dur = tk.IntVar(value=3)
        self.show_mode = tk.StringVar(value="all")
        self.dark_mode = tk.BooleanVar(value=False)
        self.group_filter = tk.StringVar(value="")
        self.running = True
        self.delay_cache = 3
        self.alarm_muted = False
        self.col_show = {c[0]: tk.BooleanVar(value=c[3]) for c in COLUMNS}
        self.checked = set()

        self.down_since = {}
        self.down_accum = {}
        self.down_paused = set()
        self.offline_log = []

        self.doa_judul = DOA_DEFAULT["judul"]
        self.doa_arab = DOA_DEFAULT["arab"]
        self.doa_latin = DOA_DEFAULT["latin"]
        self.doa_indo = DOA_DEFAULT["indo"]

        self.img_path = ""
        self.img_tk = None
        self.vid_path = ""
        self.vid_playing = False
        self.vid_cap = None
        self.vid_after_id = None
        self.img_caption = ""
        self.btns_visible = True
        self._marquee_pos = 0
        self._marquee_txt = None
        self.colon_visible = True

        self.weather_type = ""
        self.weather_anim_step = 0
        self.sholat_times = {}

        self.load()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self._icon = make_icon(64)
        root.iconphoto(True, self._icon)

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.build()
        self.apply_theme()
        self.show_image()
        self.start_marquee()

        self.update_clock()
        self.animate_weather()
        self.tick_durations()

        threading.Thread(target=self.loop, daemon=True).start()
        threading.Thread(target=self.fetch_api_data, daemon=True).start()

    def build(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=5, pady=(5, 0))

        # ================= KOLOM 1 (KIRI) =================
        self.col1 = tk.Frame(top, width=250, height=230, relief="groove", bd=1)
        self.col1.pack(side="left", anchor="n", padx=(0, 6))
        self.col1.pack_propagate(False)

        head = tk.Frame(self.col1)
        head.pack(fill="x", padx=4, pady=(3, 1))
        self.lbl_col1_title = tk.Label(head, text="Expresikan Gayamu", justify="left", font=("Segoe UI", 9, "bold"))
        self.lbl_col1_title.pack(side="left", padx=(2, 0))

        self.btn_arrow = tk.Button(head, text="\u25B4", width=2, command=self.toggle_foto_btns, font=("Segoe UI", 8, "bold"), relief="flat", bd=0, cursor="hand2")
        self.btn_arrow.pack(side="right", padx=(2, 2))

        self.cv_img = tk.Canvas(self.col1, width=IMG_W, height=IMG_H, highlightthickness=1, highlightbackground="#888888", bg="black")
        self.cv_img.pack(padx=5, pady=(2, 2))

        self.btns_img = tk.Frame(self.col1)
        self.btns_img.pack(pady=(0, 2))

        baris1 = tk.Frame(self.btns_img)
        baris1.pack(anchor="w")
        tk.Button(baris1, text="Upload Foto", command=self.upload_image, width=12, font=("Segoe UI", 8)).pack(side="left", padx=2)
        tk.Button(baris1, text="Hapus Foto", command=self.remove_image, width=12, font=("Segoe UI", 8)).pack(side="left", padx=2)

        baris2 = tk.Frame(self.btns_img)
        baris2.pack(anchor="w", pady=(2, 0))
        tk.Button(baris2, text="Upload Video", command=self.upload_video, width=12, font=("Segoe UI", 8)).pack(side="left", padx=2)
        self.btn_play = tk.Button(baris2, text="Putar Video", command=self.toggle_video, width=12, font=("Segoe UI", 8), state="disabled")
        self.btn_play.pack(side="left", padx=2)

        # ================= KOLOM 2 (KANAN - DIBAGI 2 BAGIAN) =================
        col2 = tk.Frame(top)
        col2.pack(side="left", fill="both", expand=True)
        
        col2_top = tk.Frame(col2)
        col2_top.pack(fill="x", pady=(0, 6))
        
        col2_left = tk.Frame(col2_top)
        col2_left.pack(side="left", fill="both", expand=True)
        
        col2_right = tk.Frame(col2_top)
        col2_right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # --- DASHBOARD UTAMA (Di dalam col2_left) ---
        self.dash_frame = tk.Frame(col2_left, relief="solid", bd=1)
        self.dash_frame.pack(fill="x", pady=(0, 6))

        self.frm_clock = tk.Frame(self.dash_frame)
        self.frm_clock.pack(side="left", padx=(12, 10), pady=12)

        self.lbl_time1 = tk.Label(self.frm_clock, text="12", font=("Consolas", 30, "bold"))
        self.lbl_time1.pack(side="left")

        self.lbl_colon = tk.Label(self.frm_clock, text=":", font=("Consolas", 30, "bold"))
        self.lbl_colon.pack(side="left")

        self.lbl_time2 = tk.Label(self.frm_clock, text="00", font=("Consolas", 30, "bold"))
        self.lbl_time2.pack(side="left")

        frm_sub_clock = tk.Frame(self.frm_clock)
        frm_sub_clock.pack(side="left", anchor="n", padx=(4, 0), pady=(2, 0))

        self.lbl_sec = tk.Label(frm_sub_clock, text="00", font=("Consolas", 12, "bold"))
        self.lbl_sec.pack(anchor="w")

        self.lbl_ampm = tk.Label(frm_sub_clock, text="AM", font=("Segoe UI", 9, "bold"))
        self.lbl_ampm.pack(anchor="w", pady=(2, 0))

        self.sep1 = ttk.Separator(self.dash_frame, orient='vertical')
        self.sep1.pack(side='left', fill='y', pady=10, padx=8)

        self.frm_weather = tk.Frame(self.dash_frame)
        self.frm_weather.pack(side="left", fill="y", padx=10, pady=10)

        self.lbl_w_title = tk.Label(self.frm_weather, text="Cuaca (Jakarta)", font=("Segoe UI", 9, "bold"))
        self.lbl_w_title.pack(anchor="w", pady=(0, 4))

        frm_w_inner = tk.Frame(self.frm_weather)
        frm_w_inner.pack(anchor="w")
        self.cv_weather = tk.Canvas(frm_w_inner, width=54, height=48, highlightthickness=0)
        self.cv_weather.pack(side="left", padx=(0, 6))

        self.lbl_weather = tk.Label(frm_w_inner, text="Memuat...", justify="left", font=("Segoe UI", 9))
        self.lbl_weather.pack(side="left", fill="y")

        self.sep2 = ttk.Separator(self.dash_frame, orient='vertical')
        self.sep2.pack(side='left', fill='y', pady=10, padx=8)

        self.frm_sholat = tk.Frame(self.dash_frame)
        self.frm_sholat.pack(side="left", fill="y", padx=10, pady=10)

        self.lbl_s_title = tk.Label(self.frm_sholat, text="Jadwal Sholat", font=("Segoe UI", 9, "bold"))
        self.lbl_s_title.pack(anchor="w", pady=(0, 4))

        self.frm_sholat_list = tk.Frame(self.frm_sholat)
        self.frm_sholat_list.pack(anchor="w")

        self.sholat_cards = []
        self.sholat_labels = {}
        sholat_names = ["Subuh", "Dzuhur", "Ashar", "Maghrib", "Isya"]

        for i, name in enumerate(sholat_names):
            card = tk.Frame(self.frm_sholat_list, bd=1, relief="solid", padx=5, pady=2)
            card.grid(row=i%3, column=i//3, sticky="w", padx=(0, 6), pady=2)
            self.sholat_cards.append(card)

            lbl = tk.Label(card, text=f"{name.ljust(7)} : --:--", font=("Consolas", 8, "bold"))
            lbl.pack(side="left")
            self.sholat_labels[name] = lbl

        # --- MENU & TOMBOL ---
        rowA = tk.Frame(col2_left)
        rowA.pack(fill="x", pady=(0, 2))
        def btn(parent, t, c, w=None):
            tk.Button(parent, text=t, command=c, padx=8, pady=2, width=w).pack(side="left", padx=3)

        btn(rowA, "Remote (RDP)", self.do_rdp)
        btn(rowA, "Mapping \\\\IP", self.do_map)
        btn(rowA, "Open (http)", self.do_open)

        rowB = tk.Frame(col2_left)
        rowB.pack(fill="x", pady=2)
        btn(rowB, "+ Tambah IP", lambda: self.host_dialog(None))
        btn(rowB, "Edit", self.edit_host)
        btn(rowB, "Hapus", self.del_host)
        btn(rowB, "Pengaturan", self.settings)
        btn(rowB, "Rekap Offline", self.show_recap)
        btn(rowB, "Tentang", self.about)
        btn(rowB, "Keluar", self.quit)

        rowC = tk.Frame(col2_left)
        rowC.pack(fill="x", pady=2)
        tk.Label(rowC, text="Group:").pack(side="left", padx=(3,2))
        self.cmb_group = ttk.Combobox(rowC, state="readonly", width=25)
        self.cmb_group.pack(side="left")
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        tk.Button(rowC, text="Semua", width=6, command=self.set_group_all).pack(side="left", padx=(2, 2))
        tk.Button(rowC, text="Stop Alarm", command=self.stop_alarm, padx=6, pady=2).pack(side="left", padx=(10, 10))

        rowD = tk.Frame(col2_left)
        rowD.pack(fill="x", pady=2)
        tk.Label(rowD, text="Tampilkan:").pack(side="left", padx=(0,2))
        tk.Radiobutton(rowD, text="Semua", variable=self.show_mode, value="all", command=self.save_and_refresh).pack(side="left")
        tk.Radiobutton(rowD, text="Hanya UP", variable=self.show_mode, value="up", command=self.save_and_refresh).pack(side="left", padx=(2, 0))
        tk.Radiobutton(rowD, text="Hanya DOWN", variable=self.show_mode, value="down", command=self.save_and_refresh).pack(side="left", padx=(2, 15))

        rowE = tk.Frame(col2_left)
        rowE.pack(fill="x", pady=2)
        tk.Label(rowE, text="Kolom tampil:").pack(side="left", padx=(0, 4))
        
        for cid, _, label, _d in COLUMNS:
            tk.Checkbutton(rowE, text=label, variable=self.col_show[cid], command=self.apply_columns, font=("Segoe UI", 8)).pack(side="left", padx=1)

        # --- PANEL DOA ---
        self.frm_doa = tk.Frame(col2_right, relief="solid", bd=1)
        self.frm_doa.pack(fill="both", expand=True)

        hdr_doa = tk.Frame(self.frm_doa)
        hdr_doa.pack(anchor="w", fill="x", padx=8, pady=(8, 2))
        self.lbl_doa_title = tk.Label(hdr_doa, text="Doa", font=("Segoe UI", 9, "bold"))
        self.lbl_doa_title.pack(side="left")

        self.btn_doa_tulis = tk.Button(hdr_doa, text="\u270E Tulis", command=self.edit_doa, padx=4, pady=0, font=("Segoe UI", 7, "bold"), cursor="hand2")
        self.btn_doa_tulis.pack(side="right")

        frm_doa_body = tk.Frame(self.frm_doa)
        frm_doa_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.lbl_doa_judul = tk.Label(frm_doa_body, text="-", font=("Segoe UI", 9, "bold italic"), anchor="w")
        self.lbl_doa_judul.pack(anchor="w", fill="x", pady=(0, 6))

        self.lbl_doa_arab = tk.Label(frm_doa_body, text="", font=("Traditional Arabic", 18, "bold"), anchor="e", justify="right")
        self.lbl_doa_arab.pack(anchor="e", fill="x", pady=(0, 6))

        self.lbl_doa_latin = tk.Label(frm_doa_body, text="", font=("Segoe UI", 10, "italic"), anchor="w", justify="left")
        self.lbl_doa_latin.pack(anchor="w", fill="x", pady=(0, 6))

        self.lbl_doa_indo = tk.Label(frm_doa_body, text="", font=("Segoe UI", 10), anchor="w", justify="left")
        self.lbl_doa_indo.pack(anchor="w", fill="x")

        def on_doa_resize(event):
            w = max(250, event.width - 15)
            self.lbl_doa_arab.configure(wraplength=w)
            self.lbl_doa_latin.configure(wraplength=w)
            self.lbl_doa_indo.configure(wraplength=w)

        frm_doa_body.bind("<Configure>", on_doa_resize)
        self.update_doa_ui()

        # ================= MARQUEE & TABEL =================
        kata = tk.Frame(self.root, relief="groove", bd=1)
        kata.pack(fill="x", padx=5, pady=(4, 0))
        tk.Label(kata, text="Kata Kata Hari ini:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(6, 4))
        tk.Button(kata, text="Tulis Kata", command=self.edit_caption, padx=6, pady=1, width=10, font=("Segoe UI", 8)).pack(side="left", padx=4)

        self.cv_marquee = tk.Canvas(kata, height=26, highlightthickness=0)
        self.cv_marquee.pack(side="left", fill="both", expand=True, padx=6, pady=4)

        wrap = tk.Frame(self.root)
        wrap.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        cols = [c[0] for c in COLUMNS]
        self.tv = ttk.Treeview(wrap, columns=cols, show="headings")

        for cid, w, label, _d in COLUMNS:
            self.tv.heading(cid, text=label)
            self.tv.column(cid, width=w, anchor="center" if cid != "ket" else "w")

        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=vsb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        self.tv.tag_configure("up", foreground="green")
        self.tv.tag_configure("down", foreground="black", background="#ffcccc", font=("Segoe UI", 9, "bold"))
        self.tv.tag_configure("chk", foreground="gray")
        self.tv.tag_configure("sel", foreground="#1d4ed8")

        self.tv.bind("<Button-1>", self.on_tree_click)
        self.tv.bind("<space>", self.on_tree_space)

        self.apply_columns()
        self.update_group_combo()
        tk.Label(self.root, text=WM, fg="gray", anchor="e").pack(fill="x", padx=8, pady=2)

    def update_doa_ui(self):
        self.lbl_doa_judul.config(text=self.doa_judul if self.doa_judul else "-")
        self.lbl_doa_arab.config(text=self.doa_arab)
        self.lbl_doa_latin.config(text=self.doa_latin)
        self.lbl_doa_indo.config(text=self.doa_indo)

    def edit_doa(self):
        w = tk.Toplevel(self.root)
        w.title("Tulis Doa")
        w.grab_set()
        w.resizable(False, False)

        tk.Label(w, text="Isi doa secara manual (Arab, Latin, Indonesia):", justify="left", wraplength=380).pack(padx=12, pady=(10, 4))
        frm = tk.Frame(w)
        frm.pack(padx=12, pady=4)

        rows = [("Judul:", self.doa_judul), ("Arab:", self.doa_arab),
                ("Latin:", self.doa_latin), ("Indonesia:", self.doa_indo)]
        ents = {}
        for i, (lab, val) in enumerate(rows):
            tk.Label(frm, text=lab).grid(row=i, column=0, sticky="e", padx=4, pady=3)
            e = tk.Text(frm, width=40, height=2, font=("Segoe UI", 9), wrap="word")
            e.grid(row=i, column=1, padx=4, pady=3)
            e.insert("1.0", val)
            ents[lab[:-1].lower()] = e

        def do_save():
            judul = ents["judul"].get("1.0", "end").strip()
            arab = ents["arab"].get("1.0", "end").strip()
            latin = ents["latin"].get("1.0", "end").strip()
            indo = ents["indonesia"].get("1.0", "end").strip()
            if judul and (arab or latin or indo):
                self.doa_judul = judul
                self.doa_arab = arab
                self.doa_latin = latin
                self.doa_indo = indo
            else:
                self.doa_judul = DOA_DEFAULT["judul"]
                self.doa_arab = DOA_DEFAULT["arab"]
                self.doa_latin = DOA_DEFAULT["latin"]
                self.doa_indo = DOA_DEFAULT["indo"]
            self.update_doa_ui()
            self.save()
            w.destroy()

        tk.Button(w, text="Simpan", command=do_save, width=12).pack(pady=(6, 10))
        self.theme_window(w)

    def update_clock(self):
        t_hour12 = time.strftime("%I")
        t_min = time.strftime("%M")
        t_sec = time.strftime("%S")
        t_ampm = time.strftime("%p")

        is_dark = self.dark_mode.get()
        hm_color = "#38bdf8" if is_dark else "#0284c7"
        sec_color = "#fbbf24" if is_dark else "#d97706"
        ampm_color = "#4ade80" if is_dark else "#16a34a"

        self.lbl_time1.config(text=t_hour12, fg=hm_color)
        self.lbl_time2.config(text=t_min, fg=hm_color)
        self.lbl_sec.config(text=t_sec, fg=sec_color)
        self.lbl_ampm.config(text=t_ampm, fg=ampm_color)

        self.colon_visible = not self.colon_visible
        self.lbl_colon.config(text=":" if self.colon_visible else " ", fg=hm_color)

        self.check_prayer_highlight()
        self.root.after(1000, self.update_clock)

    def check_prayer_highlight(self):
        if not self.sholat_times:
            return

        now_str = time.strftime("%H:%M")
        active = "Isya"
        if now_str >= self.sholat_times.get("Subuh", "24:00") and now_str < self.sholat_times.get("Dzuhur", "24:00"):
            active = "Subuh"
        elif now_str >= self.sholat_times.get("Dzuhur", "24:00") and now_str < self.sholat_times.get("Ashar", "24:00"):
            active = "Dzuhur"
        elif now_str >= self.sholat_times.get("Ashar", "24:00") and now_str < self.sholat_times.get("Maghrib", "24:00"):
            active = "Ashar"
        elif now_str >= self.sholat_times.get("Maghrib", "24:00") and now_str < self.sholat_times.get("Isya", "24:00"):
            active = "Maghrib"

        t = THEMES["gelap"] if self.dark_mode.get() else THEMES["terang"]
        sholat_names = ["Subuh", "Dzuhur", "Ashar", "Maghrib", "Isya"]

        for name, card in zip(sholat_names, self.sholat_cards):
            lbl = self.sholat_labels[name]
            if name == active:
                card.config(bg="#d97706" if self.dark_mode.get() else "#b45309", highlightbackground="#fbbf24")
                lbl.config(bg="#d97706" if self.dark_mode.get() else "#b45309", fg="#ffffff", font=("Consolas", 8, "bold"))
            else:
                card.config(bg=t["sholat_bg"], highlightbackground="#6b7280" if self.dark_mode.get() else "#d1d5db")
                lbl.config(bg=t["sholat_bg"], fg=t["sholat_fg"], font=("Consolas", 8, "bold"))

    def animate_weather(self):
        try:
            t = THEMES["gelap"] if self.dark_mode.get() else THEMES["terang"]
            self.cv_weather.delete("all")
            self.cv_weather.configure(bg=t["dash_bg"])
            self.weather_anim_step += 1
            wt = getattr(self, "weather_type", "").lower()

            if any(k in wt for k in ["hujan", "gerimis", "badai"]):
                self.cv_weather.create_oval(6, 4, 42, 22, fill="#9ca3af", outline="")
                self.cv_weather.create_oval(14, 12, 48, 30, fill="#cbd5e1", outline="")
                offset = (self.weather_anim_step * 3) % 14
                for i in range(12, 42, 10):
                    self.cv_weather.create_line(i, 32+offset, i-2, 40+offset, fill="#38bdf8", width=2, capstyle="round")
            else:
                cx, cy = 25, 22
                puls = math.sin(self.weather_anim_step * 0.1) * 2
                self.cv_weather.create_oval(14-puls, 11-puls, 36+puls, 33+puls, fill="#facc15", outline="")
        except Exception:
            pass
        self.root.after(80, self.animate_weather)

    def translate_weather(self, text):
        t = text.lower()
        mapping = {
            "patchy light rain with thunder": "Hujan Ringan Disertai Petir",
            "light rain": "Hujan Ringan",
            "moderate rain": "Hujan Sedang",
            "heavy rain": "Hujan Lebat",
            "partly cloudy": "Berawan Sebagian",
            "overcast": "Mendung",
            "cloudy": "Berawan",
            "sunny": "Cerah",
            "clear": "Cerah"
        }
        for eng, ind in mapping.items():
            if eng in t:
                t = t.replace(eng, ind)
        return t.capitalize()

    def fetch_api_data(self):
        try:
            req = urllib.request.Request("https://wttr.in/Jakarta?format=%C+%t", headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw_cuaca = resp.read().decode('utf-8').strip()
                cuaca_indo = self.translate_weather(raw_cuaca)
                self.weather_type = cuaca_indo
                self.root.after(0, lambda: self.lbl_weather.config(text=cuaca_indo))
        except:
            self.root.after(0, lambda: self.lbl_weather.config(text="Gagal muat cuaca"))

        try:
            url_sholat = "https://api.aladhan.com/v1/timingsByCity?city=Jakarta&country=Indonesia&method=11"
            req2 = urllib.request.Request(url_sholat, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2, timeout=5) as resp2:
                data = json.loads(resp2.read().decode('utf-8'))
                t = data['data']['timings']
                self.sholat_times = {
                    "Subuh": t['Fajr'],
                    "Dzuhur": t['Dhuhr'],
                    "Ashar": t['Asr'],
                    "Maghrib": t['Maghrib'],
                    "Isya": t['Isha']
                }
                def update_sholat_ui():
                    for name in self.sholat_labels:
                        if name in self.sholat_times:
                            self.sholat_labels[name].config(text=f"{name.ljust(7)} : {self.sholat_times[name]}")
                self.root.after(0, update_sholat_ui)
        except:
            pass

    def on_tree_click(self, event):
        region = self.tv.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tv.identify_column(event.x)
        disp = list(self.tv["displaycolumns"]) if self.tv["displaycolumns"] else [c[0] for c in COLUMNS]
        if not disp:
            return
        try:
            idx = int(col.replace("#", "")) - 1
        except ValueError:
            return
        if idx < 0 or idx >= len(disp):
            return
        item = self.tv.identify_row(event.y)
        if not item:
            return

        if disp[idx] == "ctl":
            if self.status.get(item, {}).get("up") is False:
                self.toggle_timer(item)
            return "break"
        if disp[idx] == "ket":
            if self.status.get(item, {}).get("up") is False:
                self.edit_ket(item)
            else:
                messagebox.showinfo("Info", "Keterangan manual hanya untuk host yang DOWN.")
            return "break"

    def on_tree_space(self, event):
        for item in self.tv.selection():
            self.toggle_check(item)
        return "break"

    def toggle_check(self, ip):
        if ip in self.checked:
            self.checked.discard(ip)
        else:
            self.checked.add(ip)
        self.refresh_rows()

    def toggle_timer(self, ip):
        if ip in self.down_paused:
            self.down_paused.discard(ip)
            self.down_since[ip] = time.time()
        else:
            if ip in self.down_since:
                self.down_accum[ip] = self.down_accum.get(ip, 0) + (time.time() - self.down_since[ip])
                self.down_since.pop(ip, None)
            self.down_paused.add(ip)
        self.save()
        self.refresh_rows()

    def fmt_down(self, ip):
        total = self.down_accum.get(ip, 0)
        if ip in self.down_since:
            total += time.time() - self.down_since[ip]
        if total <= 0:
            return "-"
        return self.fmt_secs(total)

    def fmt_secs(self, total):
        s = int(total)
        h, m, sec = s // 3600, (s % 3600) // 60, s % 60
        return f"{h:02d}:{m:02d}:{sec:02d}"

    def reset_timer(self, ip):
        self.down_since.pop(ip, None)
        self.down_accum.pop(ip, None)
        self.down_paused.discard(ip)

    def tick_durations(self):
        try:
            for iid in self.tv.get_children():
                if self.status.get(iid, {}).get("up") is False:
                    vals = list(self.tv.item(iid, "values"))
                    disp = list(self.tv["displaycolumns"]) if self.tv["displaycolumns"] else [c[0] for c in COLUMNS]
                    if "down" in disp:
                        idx = disp.index("down")
                        if idx < len(vals):
                            vals[idx] = self.fmt_down(iid)
                            self.tv.item(iid, values=vals)
        except Exception:
            pass
        self.root.after(1000, self.tick_durations)

    def edit_ket(self, ip):
        h = next((x for x in self.hosts if x["ip"] == ip), None)
        if not h:
            return
        w = tk.Toplevel(self.root)
        w.title("Keterangan Offline")
        w.grab_set()
        w.resizable(False, False)

        tk.Label(w, text=f"Catatan untuk: {h['name']} ({ip})\nContoh: kabel putus, listrik mati", justify="left").pack(padx=12, pady=(10, 4))
        ent = tk.Text(w, width=45, height=4, font=("Segoe UI", 10), wrap="word")
        ent.pack(padx=12, pady=4)
        ent.insert("1.0", h.get("ket_manual", ""))

        def do_save():
            h["ket_manual"] = ent.get("1.0", "end").strip()
            self.save()
            self.refresh_rows()
            w.destroy()

        tk.Button(w, text="Simpan", command=do_save, width=12).pack(pady=(4, 10))
        self.theme_window(w)

    def toggle_foto_btns(self):
        self.btns_visible = not self.btns_visible
        if self.btns_visible:
            self.btns_img.pack(pady=(0, 2))
            self.btn_arrow.configure(text="\u25B4")
        else:
            self.btns_img.pack_forget()
            self.btn_arrow.configure(text="\u25BE")

    def stop_alarm(self):
        self.alarm_muted = True

    def edit_caption(self):
        w = tk.Toplevel(self.root)
        w.title("Tulis Kata")
        w.grab_set()
        w.resizable(False, False)
        ent = tk.Text(w, width=45, height=4, font=("Segoe UI", 10), wrap="word")
        ent.pack(padx=12, pady=12)
        ent.insert("1.0", self.img_caption)

        def do_save():
            self.img_caption = ent.get("1.0", "end").strip()
            self.save()
            self._marquee_pos = 0
            self._marquee_txt = None
            w.destroy()

        tk.Button(w, text="Simpan", command=do_save, width=12).pack(pady=(0,10))
        self.theme_window(w)

    def start_marquee(self):
        try:
            t = THEMES["gelap"] if self.dark_mode.get() else THEMES["terang"]
            self.cv_marquee.configure(bg=t["bg"])
            self.cv_marquee.delete("all")
            w = max(self.cv_marquee.winfo_width(), 100)

            if self.img_caption:
                self._marquee_pos -= 2
                item_w = 0
                if self._marquee_txt is not None:
                    try:
                        bb = self.cv_marquee.bbox(self._marquee_txt)
                        item_w = bb[2] - bb[0] if bb else 0
                    except:
                        pass
                if self._marquee_pos < -(item_w if item_w else 300):
                    self._marquee_pos = w
                self._marquee_txt = self.cv_marquee.create_text(
                    self._marquee_pos, 13, text=self.img_caption,
                    anchor="w", font=("Segoe UI", 9, "bold italic"), fill=t["caption_fg"]
                )
            else:
                self._marquee_pos = 0
        except Exception:
            pass
        self.root.after(50, self.start_marquee)

    def upload_image(self):
        f = filedialog.askopenfilename(title="Pilih Gambar", filetypes=[("Gambar", "*.jpg *.jpeg *.png *.bmp")])
        if f:
            self.stop_video()
            self.vid_path = ""
            self.img_path = f
            self.show_image()
            self.save()

    def remove_image(self):
        if messagebox.askyesno("Konfirmasi", "Hapus media?"):
            self.stop_video()
            self.img_path = ""
            self.vid_path = ""
            self.img_tk = None
            self.btn_play.configure(state="disabled", text="Putar Video")
            self.show_image()
            self.save()

    def show_image(self):
        if self.vid_playing:
            return
        self.cv_img.delete("all")
        ph_fg = "#aaaaaa"
        if not self.img_path or not os.path.exists(self.img_path):
            self.cv_img.create_text(IMG_W//2, IMG_H//2, text="Belum ada foto/video", fill=ph_fg)
            return
        try:
            if HAS_PIL:
                im = Image.open(self.img_path).convert("RGB")
                ratio = min((IMG_W-4) / im.width, (IMG_H-4) / im.height)
                im = im.resize((int(im.width * ratio), int(im.height * ratio)), Image.LANCZOS)
                self.img_tk = ImageTk.PhotoImage(im)
            else:
                self.img_tk = tk.PhotoImage(file=self.img_path)
            self.cv_img.create_image(IMG_W//2, IMG_H//2, image=self.img_tk, anchor="center")
        except:
            self.cv_img.create_text(IMG_W//2, IMG_H//2, text="Gagal muat file", fill="red")

    def upload_video(self):
        f = filedialog.askopenfilename(title="Pilih Video", filetypes=[("Video", "*.mp4 *.avi *.mkv")])
        if f:
            self.stop_video()
            self.vid_path = f
            self.btn_play.configure(state="normal")
            self.show_image()
            self.save()

    def toggle_video(self):
        if self.vid_playing:
            self.stop_video()
            self.show_image()
        else:
            self.play_video()

    def stop_video(self):
        self.vid_playing = False
        if self.vid_after_id:
            self.root.after_cancel(self.vid_after_id)
            self.vid_after_id = None
        if self.vid_cap:
            self.vid_cap.release()
            self.vid_cap = None
        if hasattr(self, "btn_play"):
            self.btn_play.configure(text="Putar Video")

    def play_video(self):
        if not self.vid_path or not HAS_CV2 or not HAS_PIL:
            return
        self.vid_cap = cv2.VideoCapture(self.vid_path)
        if not self.vid_cap.isOpened():
            return
        self.vid_playing = True
        self.btn_play.configure(text="Stop Video")
        self._vid_frame()

    def _vid_frame(self):
        if not self.vid_playing or not self.vid_cap:
            return
        ok, frame = self.vid_cap.read()
        if not ok:
            self.vid_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.vid_cap.read()
            if not ok:
                return self.stop_video()
        try:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]
            ratio = min((IMG_W-4) / w, (IMG_H-4) / h)
            frame = cv2.resize(frame, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_LINEAR)
            im = Image.fromarray(frame)
            self.img_tk = ImageTk.PhotoImage(im)
            self.cv_img.delete("all")
            self.cv_img.create_image(IMG_W//2, IMG_H//2, image=self.img_tk, anchor="center")
        except:
            return self.stop_video()
        fps = self.vid_cap.get(cv2.CAP_PROP_FPS)
        d = int(1000/fps) if fps and fps>0 else 33
        self.vid_after_id = self.root.after(d, self._vid_frame)

    def theme_window(self, w):
        t = THEMES["gelap"] if self.dark_mode.get() else THEMES["terang"]
        w.configure(bg=t["bg"])
        for c in w.winfo_children():
            if isinstance(c, tk.Frame):
                self._theme_frame(c, t)
            elif isinstance(c, (tk.Radiobutton, tk.Checkbutton)):
                c.configure(bg=t["bg"], fg=t["fg"], selectcolor="#1e1e1e" if self.dark_mode.get() else "#ffffff")
            elif isinstance(c, tk.Label):
                c.configure(bg=t["bg"], fg=t["fg"])
            elif isinstance(c, tk.Button):
                c.configure(bg=t["btn_bg"], fg=t["btn_fg"])

    def apply_theme(self):
        t = THEMES["gelap"] if self.dark_mode.get() else THEMES["terang"]
        self.root.configure(bg=t["bg"])
        dash_bg = t["dash_bg"]
        dash_fg = t["fg"]
        
        self.dash_frame.configure(bg=dash_bg, highlightbackground="#4b5563" if self.dark_mode.get() else "#cbd5e1")
        self.frm_clock.configure(bg=dash_bg)
        
        self.lbl_time1.configure(bg=dash_bg)
        self.lbl_colon.configure(bg=dash_bg)
        self.lbl_time2.configure(bg=dash_bg)
        self.lbl_sec.configure(bg=dash_bg)
        self.lbl_ampm.configure(bg=dash_bg)
        for child in self.frm_clock.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=dash_bg)
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Label):
                        sub.configure(bg=dash_bg)

        self.frm_weather.configure(bg=dash_bg)
        self.lbl_w_title.configure(bg=dash_bg, fg="#38bdf8" if self.dark_mode.get() else "#0284c7")
        self.lbl_weather.configure(bg=dash_bg, fg=dash_fg)
        for child in self.frm_weather.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=dash_bg)
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Label):
                        sub.configure(bg=dash_bg, fg=dash_fg)

        self.frm_sholat.configure(bg=dash_bg)
        self.lbl_s_title.configure(bg=dash_bg, fg="#4ade80" if self.dark_mode.get() else "#16a34a")
        self.frm_sholat_list.configure(bg=dash_bg)
        
        for card in self.sholat_cards:
            card.configure(bg=t["sholat_bg"])
        for name, lbl in self.sholat_labels.items():
            lbl.configure(bg=t["sholat_bg"], fg=t["sholat_fg"])

        if hasattr(self, "frm_doa"):
            self.frm_doa.configure(bg=dash_bg, highlightbackground="#4b5563" if self.dark_mode.get() else "#cbd5e1")
            self.lbl_doa_title.configure(bg=dash_bg, fg="#a78bfa" if self.dark_mode.get() else "#6d28d9")
            self.lbl_doa_judul.configure(bg=dash_bg, fg=dash_fg)
            
            arab_fg = "#fbbf24" if self.dark_mode.get() else "#000000"
            latin_fg = "#7dd3fc" if self.dark_mode.get() else "#0369a1"
            indo_fg = "#ffffff" if self.dark_mode.get() else "#111827"

            self.lbl_doa_arab.configure(bg=dash_bg, fg=arab_fg)
            self.lbl_doa_latin.configure(bg=dash_bg, fg=latin_fg)
            self.lbl_doa_indo.configure(bg=dash_bg, fg=indo_fg)

        for w in self.root.winfo_children():
            if isinstance(w, tk.Frame) and w not in (self.dash_frame, getattr(self, "frm_doa", None)):
                self._theme_frame(w, t)

        self.style.configure("Treeview", background=t["tree_bg"], fieldbackground=t["tree_bg"], foreground=t["tree_fg"], rowheight=25)
        self.style.configure("Treeview.Heading", background=t["btn_bg"], foreground=t["btn_fg"], font=('Segoe UI', 9, 'bold'))
        self.tv.tag_configure("down", foreground="white" if self.dark_mode.get() else "black", background=t["down_bg"])
        self.tv.tag_configure("up", foreground="#4ade80" if self.dark_mode.get() else "green")
        self.show_image()

    def _theme_frame(self, frm, t):
        try:
            frm.configure(bg=t["bg"])
        except:
            return
        for w in frm.winfo_children():
            if isinstance(w, tk.Frame):
                self._theme_frame(w, t)
            elif isinstance(w, (tk.Radiobutton, tk.Checkbutton)):
                w.configure(bg=t["bg"], fg=t["fg"], selectcolor="#1e1e1e" if self.dark_mode.get() else "#ffffff")
            elif isinstance(w, tk.Label):
                w.configure(bg=t["bg"], fg=t["fg"])
            elif isinstance(w, tk.Button):
                w.configure(bg=t["btn_bg"], fg=t["btn_fg"])

    def update_group_combo(self):
        groups = sorted({x.get("group", "").strip() for x in self.hosts if x.get("group", "").strip()})
        self.cmb_group["values"] = ["(Semua Grup)"] + groups
        if self.group_filter.get() and self.group_filter.get() in groups:
            self.cmb_group.set(self.group_filter.get())
        else:
            self.group_filter.set("")
            self.cmb_group.set("(Semua Grup)")

    def on_group_selected(self, event=None):
        val = self.cmb_group.get()
        self.group_filter.set("" if val == "(Semua Grup)" else val)
        self.save()
        self.refresh_rows()

    def set_group_all(self):
        self.group_filter.set("")
        self.cmb_group.set("(Semua Grup)")
        self.save()
        self.refresh_rows()

    def save_and_refresh(self):
        self.save()
        self.refresh_rows()

    def apply_columns(self):
        shown = [cid for cid, _, _, _ in COLUMNS if self.col_show[cid].get()] or ["status"]
        self.tv["displaycolumns"] = shown
        self.refresh_rows()

    def host_dialog(self, old_ip=None):
        h = next((x for x in self.hosts if x["ip"] == old_ip), None) if old_ip else None
        w = tk.Toplevel(self.root)
        w.title("Edit Host" if h else "Input IP")
        w.grab_set()
        w.resizable(False, False)

        fields = [("Nama:", "name", ""), ("Group:", "group", ""), ("IP / Hostname:", "ip", ""), ("Username:", "user", ""), ("Password:", "pwd", "*")]
        ents = {}
        for i, (lab, key, show) in enumerate(fields):
            tk.Label(w, text=lab).grid(row=i, column=0, sticky="e", padx=5, pady=4)
            e = tk.Entry(w, width=30, show=show)
            e.grid(row=i, column=1, padx=5, pady=4)
            ents[key] = e

        if h:
            ents["name"].insert(0, h["name"])
            ents["group"].insert(0, h.get("group", ""))
            ents["ip"].insert(0, h["ip"])
            ents["user"].insert(0, h.get("user", ""))
            ents["pwd"].insert(0, unx(h.get("pwd", "")))

        def save():
            name = ents["name"].get().strip()
            ip = ents["ip"].get().strip()
            group = ents["group"].get().strip()
            if not ip:
                return messagebox.showerror("Error", "IP tidak boleh kosong!", parent=w)
            if any(x["ip"] == ip for x in self.hosts if x["ip"] != old_ip):
                return messagebox.showerror("Error", "IP sudah ada!", parent=w)

            new = {"name": name or ip, "ip": ip, "group": group, "user": ents["user"].get().strip(), "pwd": xor(ents["pwd"].get())}
            if h:
                for key in ("ket_manual", "timer_paused", "down_accum", "down_since", "last_down_dur"):
                    if h.get(key) is not None and h.get(key) != "":
                        new[key] = h[key]
                self.hosts[self.hosts.index(h)] = new
            else:
                self.hosts.append(new)

            self.save()
            w.destroy()
            self.update_group_combo()
            self.refresh_rows()

        tk.Button(w, text="Simpan", command=save, width=12).grid(row=5, column=1, pady=10, sticky="w")
        self.theme_window(w)

    def target_ips(self):
        ips = [ip for ip in self.checked if any(h["ip"] == ip for h in self.hosts)]
        if ips:
            return ips
        s = self.tv.selection()
        return [s[0]] if s else []

    def edit_host(self):
        s = self.tv.selection()
        if not s:
            return messagebox.showinfo("Info", "Pilih baris dulu")
        self.host_dialog(old_ip=s[0])

    def del_host(self):
        ips = self.target_ips()
        if not ips:
            return messagebox.showinfo("Info", "Centang atau pilih baris dulu")
        if messagebox.askyesno("Konfirmasi", f"Hapus {len(ips)} host?"):
            self.hosts = [x for x in self.hosts if x["ip"] not in ips]
            for ip in ips:
                self.status.pop(ip, None)
                self.checked.discard(ip)
                self.reset_timer(ip)
            self.save()
            self.update_group_combo()
            self.refresh_rows()

    def do_rdp(self):
        for ip in self.target_ips():
            subprocess.Popen(["mstsc", "/v:" + ip])

    def do_map(self):
        for ip in self.target_ips():
            subprocess.Popen(["explorer", "\\\\" + ip])

    def do_open(self):
        for ip in self.target_ips():
            subprocess.Popen(["explorer", "http://" + ip])

    def ping_worker(self, ip):
        try:
            out = subprocess.run(["ping", "-n", "1", "-w", "1500", ip], capture_output=True, text=True, errors="replace", creationflags=0x08000000).stdout
            if "TTL=" in out:
                t = re.search(r"waktu[=<](\d+)ms|time[=<](\d+)ms", out)
                ttl = re.search(r"TTL[=:](\d+)", out)
                return ip, {"up": True, "time": (t.group(1) or t.group(2)) if t else "<1", "ttl": ttl.group(1) if ttl else "-", "ket": "OK - Host aktif"}
        except:
            pass
        return ip, {"up": False, "time": "-", "ttl": "-", "ket": "DOWN - Host tidak merespon!"}

    def loop(self):
        while self.running:
            d = self.delay_cache
            with ThreadPoolExecutor(max_workers=20) as executor:
                results = executor.map(self.ping_worker, [h["ip"] for h in self.hosts])

            for ip, res in results:
                if not self.running:
                    return
                prev = self.status.get(ip, {}).get("up", res["up"])
                
                if prev is False and res["up"]:
                    h_target = next((x for x in self.hosts if x["ip"] == ip), None)
                    if h_target:
                        durasi_str = self.fmt_down(ip)
                        now_dt = datetime.now()
                        tgl_str = now_dt.strftime("%d/%m/%Y")
                        jam_str = now_dt.strftime("%H:%M:%S")
                        
                        h_target["last_down_dur"] = f"{tgl_str}, {jam_str}, {durasi_str}"
                        
                        self.offline_log.append({
                            "date": tgl_str,
                            "time": jam_str,
                            "name": h_target["name"],
                            "ip": ip,
                            "group": h_target.get("group", "-"),
                            "duration": durasi_str
                        })

                self.status[ip] = res

                if not res["up"]:
                    if ip not in self.down_since and ip not in self.down_paused and ip not in self.down_accum:
                        self.down_since[ip] = time.time()
                else:
                    self.reset_timer(ip)

                if prev and not res["up"] and self.alarm_on.get():
                    self.alarm_muted = False
                    threading.Thread(target=self.beep, daemon=True).start()

            try:
                self.root.after(0, self.refresh_rows)
            except RuntimeError:
                return
            time.sleep(d)

    def beep(self):
        try:
            subprocess.Popen(
                ["powershell", "-Command", "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('Mati')"],
                creationflags=0x08000000
            )
            for _ in range(self.alarm_dur.get() * 2):
                if self.alarm_muted or not self.running:
                    return
                winsound.Beep(1200, 300)
                time.sleep(0.2)
        except:
            pass

    # ================= FUNGSI REKAP OFFLINE (Dengan Panel Detail Status Offline di Ruang Kosong) =================
    def show_recap(self):
        w = tk.Toplevel(self.root)
        w.title("Rekap Data Offline Harian")
        w.geometry("1020x580")
        w.grab_set()
        
        t = THEMES["gelap"] if self.dark_mode.get() else THEMES["terang"]
        w.configure(bg=t["bg"])

        top_frame = tk.Frame(w, bg=t["bg"])
        top_frame.pack(fill="x", padx=15, pady=12)
        
        tk.Label(top_frame, text="Log Riwayat Host Offline", font=("Segoe UI", 12, "bold"), bg=t["bg"], fg=t["fg"]).pack(side="left")

        # Frame Filter (Tanggal & Group)
        filter_frame = tk.Frame(top_frame, bg=t["bg"])
        filter_frame.pack(side="left", padx=15)
        
        # 1. Filter Tanggal
        tk.Label(filter_frame, text="Tanggal:", font=("Segoe UI", 9), bg=t["bg"], fg=t["fg"]).pack(side="left", padx=(0, 2))
        log_dates = sorted(list(set([log.get("date", "") for log in self.offline_log])))
        now_tgl = datetime.now().strftime("%d/%m/%Y")
        if now_tgl not in log_dates:
            log_dates.append(now_tgl)
        log_dates.insert(0, "Semua Tanggal")
        
        self.recap_date_var = tk.StringVar(value="Semua Tanggal")
        cmb_recap_date = ttk.Combobox(filter_frame, textvariable=self.recap_date_var, values=log_dates, state="readonly", width=14)
        cmb_recap_date.pack(side="left", padx=5)

        # 2. Filter Group
        tk.Label(filter_frame, text="Group:", font=("Segoe UI", 9), bg=t["bg"], fg=t["fg"]).pack(side="left", padx=(10, 2))
        log_groups = sorted(list(set([log.get("group", "-") for log in self.offline_log] + [h.get("group", "-") for h in self.hosts])))
        log_groups.insert(0, "Semua Group")
        
        self.recap_group_var = tk.StringVar(value="Semua Group")
        cmb_recap_group = ttk.Combobox(filter_frame, textvariable=self.recap_group_var, values=log_groups, state="readonly", width=16)
        cmb_recap_group.pack(side="left", padx=5)

        # Tombol Unduh
        btn_frame = tk.Frame(top_frame, bg=t["bg"])
        btn_frame.pack(side="right")

        tk.Button(btn_frame, text="Unduh PDF", command=lambda: self.export_recap_pdf(tv_log), width=12, bg=t["btn_bg"], fg=t["btn_fg"]).pack(side="right", padx=(5, 0))
        tk.Button(btn_frame, text="Unduh CSV", command=lambda: self.export_recap_csv(tv_log), width=12, bg=t["btn_bg"], fg=t["btn_fg"]).pack(side="right")

        # Container Utama untuk membagi Tabel (Kiri) dan Panel Detail Offline (Kanan)
        main_container = tk.Frame(w, bg=t["bg"])
        main_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Panel Kiri: Tabel Treeview
        frame_left = tk.Frame(main_container, bg=t["bg"])
        frame_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cols = ("date", "time", "name", "ip", "group", "duration")
        tv_log = ttk.Treeview(frame_left, columns=cols, show="headings")
        
        tv_log.heading("date", text="Tanggal")
        tv_log.column("date", width=85, anchor="center")
        tv_log.heading("time", text="Waktu Pulih")
        tv_log.column("time", width=110, anchor="center")
        tv_log.heading("name", text="Nama Perangkat")
        tv_log.column("name", width=140, anchor="w")
        tv_log.heading("ip", text="IP Address")
        tv_log.column("ip", width=110, anchor="center")
        tv_log.heading("group", text="Group")
        tv_log.column("group", width=90, anchor="center")
        tv_log.heading("duration", text="Lama Offline")
        tv_log.column("duration", width=100, anchor="center")

        tv_log.tag_configure("log_offline", background="#ff4d4d" if self.dark_mode.get() else "#ffcccc", foreground="black", font=("Segoe UI", 9, "bold"))
        tv_log.tag_configure("log_ganjil", background=t["tree_bg"], foreground=t["tree_fg"])
        tv_log.tag_configure("log_genap", background=t["dash_bg"], foreground=t["tree_fg"])

        vsb = ttk.Scrollbar(frame_left, orient="vertical", command=tv_log.yview)
        tv_log.configure(yscrollcommand=vsb.set)
        
        tv_log.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        # Panel Kanan: Rincian Host Status Offline (Mengisi Ruang Kosong)
        panel_right = tk.Frame(main_container, bg=t["dash_bg"], relief="solid", bd=1, width=280)
        panel_right.pack(side="right", fill="both", expand=False)
        panel_right.pack_propagate(False)

        lbl_panel_title = tk.Label(panel_right, text="DETAIL STATUS OFFLINE", font=("Segoe UI", 10, "bold"), bg=t["dash_bg"], fg="#ef4444" if self.dark_mode.get() else "#dc2626")
        lbl_panel_title.pack(anchor="w", padx=10, pady=(10, 4))

        lbl_sub_info = tk.Label(panel_right, text="Host yang sedang terputus saat ini:", font=("Segoe UI", 8, "italic"), bg=t["dash_bg"], fg=t["fg"])
        lbl_sub_info.pack(anchor="w", padx=10, pady=(0, 6))

        txt_detail = tk.Text(panel_right, bg=t["tree_bg"], fg=t["tree_fg"], font=("Consolas", 9), relief="flat", wrap="word")
        txt_detail.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        def update_offline_detail():
            txt_detail.config(state="normal")
            txt_detail.delete("1.0", "end")
            
            selected_group = self.recap_group_var.get()
            offline_hosts = []

            for h in self.hosts:
                ip = h["ip"]
                if self.status.get(ip, {}).get("up") is False:
                    match_group = (selected_group == "Semua Group" or h.get("group", "-") == selected_group)
                    if match_group:
                        offline_hosts.append(h)

            if not offline_hosts:
                txt_detail.insert("end", " Tidak ada host offline\n pada group ini.")
            else:
                txt_detail.insert("end", f" Total Down: {len(offline_hosts)} Perangkat\n")
                txt_detail.insert("end", "="*28 + "\n\n")
                for idx, h in enumerate(offline_hosts, 1):
                    ip = h["ip"]
                    dur = self.fmt_down(ip)
                    ket = h.get("ket_manual", "Host tidak merespon")
                    txt_detail.insert("end", f"{idx}. {h['name']}\n")
                    txt_detail.insert("end", f"   IP     : {ip}\n")
                    txt_detail.insert("end", f"   Group  : {h.get('group', '-')}\n")
                    txt_detail.insert("end", f"   Durasi : {dur}\n")
                    txt_detail.insert("end", f"   Ket    : {ket}\n")
                    txt_detail.insert("end", "-"*28 + "\n")

            txt_detail.config(state="disabled")

        def populate_recap(event=None):
            for item in tv_log.get_children():
                tv_log.delete(item)
            selected_date = self.recap_date_var.get()
            selected_group = self.recap_group_var.get()
            now_str = datetime.now().strftime("%d/%m/%Y")
            idx = 0

            # 1. Tampilkan Host yang SEDANG OFFLINE saat ini
            for h in self.hosts:
                ip = h["ip"]
                if self.status.get(ip, {}).get("up") is False:
                    match_date = (selected_date == "Semua Tanggal" or selected_date == now_str)
                    match_group = (selected_group == "Semua Group" or h.get("group", "-") == selected_group)
                    if match_date and match_group:
                        dur_current = self.fmt_down(ip)
                        tv_log.insert("", "end", values=(
                            now_str,
                            "[SEDANG OFFLINE]",
                            h["name"],
                            ip,
                            h.get("group", "-"),
                            dur_current
                        ), tags=("log_offline",))

            # 2. Tampilkan Riwayat Offline yang telah pulih
            for log in reversed(self.offline_log):
                match_date = (selected_date == "Semua Tanggal" or log.get("date", "") == selected_date)
                match_group = (selected_group == "Semua Group" or log.get("group", "-") == selected_group)
                
                if match_date and match_group:
                    baris_tag = "log_genap" if idx % 2 == 0 else "log_ganjil"
                    tv_log.insert("", "end", values=(log["date"], log["time"], log["name"], log["ip"], log["group"], log["duration"]), tags=(baris_tag,))
                    idx += 1

            update_offline_detail()

        cmb_recap_date.bind("<<ComboboxSelected>>", populate_recap)
        cmb_recap_group.bind("<<ComboboxSelected>>", populate_recap)
        populate_recap()
            
        self.theme_window(w)

    def export_recap_csv(self, tv):
        items = tv.get_children()
        if not items:
            messagebox.showinfo("Info", "Tidak ada data rekap di tabel yang sesuai dengan filter untuk diunduh.", parent=self.root)
            return
        
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], title="Simpan Rekap Offline (CSV)")
        if f:
            try:
                import csv
                with open(f, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Tanggal", "Waktu Pulih / Status", "Nama Perangkat", "IP Address", "Group", "Durasi Offline"])
                    for item in items:
                        vals = tv.item(item, 'values')
                        writer.writerow(vals)
                messagebox.showinfo("Sukses", "Data rekap berhasil diunduh ke CSV!", parent=self.root)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal mengunduh data CSV:\n{e}", parent=self.root)

    def export_recap_pdf(self, tv):
        if not HAS_REPORTLAB:
            messagebox.showerror("Modul Tidak Ditemukan", "Modul 'reportlab' belum terinstal.\nSilakan jalankan 'pip install reportlab' di CMD / Terminal.", parent=self.root)
            return

        items = tv.get_children()
        if not items:
            messagebox.showinfo("Info", "Tidak ada data rekap di tabel yang sesuai dengan filter untuk diunduh.", parent=self.root)
            return

        f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")], title="Simpan Rekap Offline (PDF)")
        if f:
            try:
                doc = SimpleDocTemplate(f, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                story = []
                styles = getSampleStyleSheet()

                title_style = ParagraphStyle(
                    'TitleStyle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    leading=20,
                    textColor=colors.HexColor("#1e3a5f"),
                    spaceAfter=10
                )
                story.append(Paragraph(f"LAPORAN REKAP OFFLINE - {APP}", title_style))
                
                dt_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=9, textColor=colors.gray, spaceAfter=15)
                story.append(Paragraph(f"Diunduh pada: {dt_now} | Dicetak oleh: {WM}", sub_style))

                table_data = [["Tanggal", "Waktu / Status", "Nama Perangkat", "IP Address", "Group", "Lama Offline"]]
                
                cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10)
                
                for item in items:
                    vals = list(tv.item(item, 'values'))
                    row_cells = [Paragraph(str(v), cell_style) for v in vals]
                    table_data.append(row_cells)

                t = Table(table_data, colWidths=[70, 95, 140, 85, 70, 75])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
                ]))

                story.append(t)
                doc.build(story)
                messagebox.showinfo("Sukses", "Laporan Rekap Offline berhasil disimpan ke PDF!", parent=self.root)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal mengekspor data ke PDF:\n{e}", parent=self.root)

    def refresh_rows(self):
        gf = self.group_filter.get().strip()
        mode = self.show_mode.get()
        existing_iids = set(self.tv.get_children())
        sorted_hosts = sorted(self.hosts, key=lambda x: (x.get("group", ""), x["name"].lower()))

        for h in sorted_hosts:
            if gf and h.get("group", "").strip() != gf:
                continue

            s = self.status.get(h["ip"], {"up": None, "time": "-", "ttl": "-", "ket": "Memeriksa..."})
            up = s.get("up")
            st = "UP" if up else ("DOWN" if up is False else "...")
            ket = ("\u26a0 " if up is False else "") + s.get("ket", "")

            if up is False:
                durasi = self.fmt_down(h["ip"])
                tombol_timer = "[ \u25B6 Start ]" if h["ip"] in self.down_paused else "[ \u23F8 Stop ]"
                manual = h.get("ket_manual", "")
                if manual:
                    ket = "\u270E " + manual
            else:
                durasi = h.get("last_down_dur", "-")
                tombol_timer = "-"
                ket = ("\u26a0 " if up is False else "") + s.get("ket", "")

            tag = "down" if up is False else ("up" if up else "chk")
            if h["ip"] in self.checked:
                tag = tag if tag == "down" else "sel"

            if mode == "down" and up is not False:
                continue
            if mode == "up" and not up:
                continue

            vals = []
            for cid, _, _, _ in COLUMNS:
                if cid == "status": vals.append(st)
                elif cid == "group": vals.append(h.get("group", "-"))
                elif cid == "nama": vals.append(h["name"])
                elif cid == "ip": vals.append(h["ip"])
                elif cid == "time": vals.append(s.get("time", "-"))
                elif cid == "ttl": vals.append(s.get("ttl", "-"))
                elif cid == "down": vals.append(durasi)
                elif cid == "ctl": vals.append(tombol_timer)
                elif cid == "ket": vals.append(ket)

            if h["ip"] in existing_iids:
                self.tv.item(h["ip"], values=tuple(vals), tags=(tag,))
                existing_iids.remove(h["ip"])
            else:
                self.tv.insert("", "end", iid=h["ip"], values=tuple(vals), tags=(tag,))

        for old_iid in existing_iids:
            self.tv.delete(old_iid)

    def settings(self):
        w = tk.Toplevel(self.root)
        w.title("Pengaturan")
        w.grab_set()
        w.resizable(False, False)

        row = 0
        tk.Label(w, text="Alarm & Durasi (Detik):").grid(row=row, column=0, sticky="e", padx=10, pady=(10, 2))
        tk.Radiobutton(w, text="ON", variable=self.alarm_on, value=True).grid(row=row, column=1, sticky="w")
        tk.Radiobutton(w, text="OFF", variable=self.alarm_on, value=False).grid(row=row, column=2, sticky="w")
        tk.Spinbox(w, from_=1, to=60, textvariable=self.alarm_dur, width=5).grid(row=row, column=3, sticky="w", padx=10)

        row += 1
        tk.Label(w, text="Delay ping (detik):").grid(row=row, column=0, sticky="e", padx=10, pady=(8, 2))
        for i, d in enumerate([3, 5, 7]):
            tk.Radiobutton(w, text=str(d), variable=self.delay, value=d).grid(row=row, column=1+i, sticky="w")

        row += 1
        tk.Label(w, text="Tampilan:").grid(row=row, column=0, sticky="e", padx=10, pady=(8, 2))
        tk.Radiobutton(w, text="Terang", variable=self.dark_mode, value=False, command=lambda: [self.apply_theme(), self.theme_window(w)]).grid(row=row, column=1, sticky="w")
        tk.Radiobutton(w, text="Gelap", variable=self.dark_mode, value=True, command=lambda: [self.apply_theme(), self.theme_window(w)]).grid(row=row, column=2, sticky="w")

        row += 1
        def apply():
            self.delay_cache = self.delay.get()
            self.save()
            w.destroy()

        tk.Button(w, text="Simpan Pengaturan", command=apply, width=18).grid(row=row, column=0, columnspan=4, pady=(10, 5))

        def do_backup():
            f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], title="Simpan Data Backup")
            if f:
                try:
                    with open(f, "w") as file:
                        file.write(self.dump())
                    messagebox.showinfo("Backup Berhasil", "Data berhasil dibackup ke:\n" + f, parent=w)
                except Exception as e:
                    messagebox.showerror("Backup Gagal", f"Terjadi kesalahan:\n{e}", parent=w)

        def do_restore():
            f = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Pilih File Backup")
            if f:
                if messagebox.askyesno("Konfirmasi Restore", "Apakah Anda yakin ingin memulihkan data dari file ini?\nData saat ini akan tertimpa.", parent=w):
                    try:
                        with open(f, "r") as file:
                            self.load_from(file.read())
                        self.save()
                        self.apply_theme()
                        messagebox.showinfo("Restore Berhasil", "Data berhasil dipulihkan.", parent=w)
                        w.destroy()
                    except Exception as e:
                        messagebox.showerror("Restore Gagal", f"File corrupt atau terjadi kesalahan:\n{e}", parent=w)

        frm_backup = tk.Frame(w)
        frm_backup.grid(row=row+1, column=0, columnspan=4, pady=(5, 15))
        tk.Button(frm_backup, text="Backup Data", command=do_backup, width=12).pack(side="left", padx=5)
        tk.Button(frm_backup, text="Restore Data", command=do_restore, width=12).pack(side="left", padx=5)

        self.theme_window(w)

    def about(self):
        w = tk.Toplevel(self.root)
        w.title("Tentang & Panduan Aplikasi")
        w.grab_set()
        w.resizable(False, False)

        tk.Label(w, text=f"{APP}\n{WM}", justify="center", font=("Segoe UI", 10, "bold")).pack(padx=20, pady=(15, 5))
        
        panduan = (
            "--- CARA PENGGUNAAN ---\n"
            "1. Klik '+ Tambah IP' untuk memasukkan perangkat.\n"
            "2. Status DOWN akan memicu alarm suara dan ucapan 'Mati'.\n"
            "3. Durasi offline terakhir tercatat lengkap (dd/mm/yyyy, jam, durasi) saat perangkat UP kembali.\n"
            "4. Gunakan menu 'Rekap Offline' untuk melihat, memfilter, dan mengunduh laporan ke PDF/CSV.\n\n"
            "--- INFORMASI KONTAK & DUKUNGAN ---\n"
            "• Gopay, OVO : 0898 33 78 733\n"
            "• WhatsApp   : 0898 33 78 733"
        )
        tk.Label(w, text=panduan, justify="left", font=("Segoe UI", 9)).pack(padx=20, pady=5, anchor="w")
        tk.Button(w, text="Tutup", command=w.destroy, width=12).pack(pady=(10, 15))
        self.theme_window(w)

    def _sync_timer_to_hosts(self):
        for h in self.hosts:
            ip = h["ip"]
            if ip in self.down_paused:
                h["timer_paused"] = True
                h["down_accum"] = self.down_accum.get(ip, 0)
                h.pop("down_since", None)
            elif ip in self.down_since:
                h["timer_paused"] = False
                h["down_accum"] = self.down_accum.get(ip, 0)
                h["down_since"] = self.down_since[ip]
            else:
                h.pop("timer_paused", None)
                h.pop("down_accum", None)
                h.pop("down_since", None)

    def _sync_timer_from_hosts(self):
        self.down_since = {}
        self.down_accum = {}
        self.down_paused = set()
        for h in self.hosts:
            ip = h["ip"]
            accum = float(h.get("down_accum", 0) or 0)
            since = h.get("down_since", None)
            if h.get("timer_paused"):
                self.down_paused.add(ip)
                if accum > 0:
                    self.down_accum[ip] = accum
            elif since:
                try:
                    since = float(since)
                except (TypeError, ValueError):
                    continue
                self.down_accum[ip] = accum
                self.down_since[ip] = since

    def dump(self):
        try:
            self._sync_timer_to_hosts()
        except Exception:
            pass
        data = {
            "hosts": self.hosts,
            "delay": self.delay.get(),
            "alarm": self.alarm_on.get(),
            "adur": self.alarm_dur.get(),
            "cols": {k: v.get() for k, v in self.col_show.items()},
            "gfilter": self.group_filter.get(),
            "show": self.show_mode.get(),
            "dark": self.dark_mode.get(),
            "imgpath": self.img_path,
            "vidpath": self.vid_path,
            "imgcaption": self.img_caption,
            "offline_log": self.offline_log,
            "doa_judul": self.doa_judul,
            "doa_arab": self.doa_arab,
            "doa_latin": self.doa_latin,
            "doa_indo": self.doa_indo
        }
        return json.dumps(data)

    def load_from(self, s):
        d = json.loads(s)
        self.hosts = d.get("hosts", [])
        self.delay_cache = d.get("delay", 3)
        self.delay.set(self.delay_cache)
        self.alarm_on.set(d.get("alarm", True))
        self.alarm_dur.set(d.get("adur", 3))
        self.show_mode.set(d.get("show", "all"))
        self.dark_mode.set(d.get("dark", False))

        for k, v in self.col_show.items():
            if k in d.get("cols", {}):
                v.set(bool(d["cols"][k]))

        self.group_filter.set(d.get("gfilter", ""))
        self.img_path = d.get("imgpath", "")
        self.vid_path = d.get("vidpath", "")
        self.img_caption = d.get("imgcaption", "")
        self.offline_log = d.get("offline_log", [])

        self.doa_judul = d.get("doa_judul", "") or DOA_DEFAULT["judul"]
        self.doa_arab = d.get("doa_arab", "") or DOA_DEFAULT["arab"]
        self.doa_latin = d.get("doa_latin", "") or DOA_DEFAULT["latin"]
        self.doa_indo = d.get("doa_indo", "") or DOA_DEFAULT["indo"]
        if hasattr(self, "lbl_doa_judul"):
            self.update_doa_ui()

        self._sync_timer_from_hosts()
        if hasattr(self, "btn_play"):
            self.btn_play.configure(state="normal" if self.vid_path else "disabled")
        if hasattr(self, "tv"):
            self.apply_columns()
            self.update_group_combo()

    def save(self):
        try:
            with open(cfg_path(), "w") as f:
                f.write(self.dump())
            return True, ""
        except Exception as e:
            return False, str(e)

    def load(self):
        try:
            with open(cfg_path(), "r") as f:
                self.load_from(f.read())
        except:
            pass

    def quit(self):
        self.running = False
        self.stop_video()
        self.save()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()