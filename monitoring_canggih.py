# -*- coding: utf-8 -*-
# =====================================================================
#  MONITORING CANGGIH  -  By. Entong Betawi  (v16 - Anti Lag Video)
# =====================================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess, re, json, os, sys, threading, time, winsound
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

# ---------- Keamanan Sederhana ----------
def xor(s, k="entong"):
    if not s: 
        return ""
    raw, kb = s.encode("utf-8"), k.encode("utf-8")
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw)).hex()

def unx(s, k="entong"):
    if not s: 
        return ""
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
        for x in range(int(x1*f), int(x2*f)+1):
            for y in range(int(y1*f), int(y2*f)+1):
                if frame is None or x <= frame[0]*f or x >= frame[1]*f or y <= frame[2]*f or y >= frame[3]*f:
                    img.put(col, (x, y))
    rect(6,  6, 57, 39, "#1e3a5f")
    rect(9,  9, 54, 36, "#3b82c4", frame=(8,55,8,37))
    rect(50, 9, 53, 12, "#4ade80")
    rect(28, 40, 36, 48, "#1e3a5f")
    rect(16, 48, 48, 53, "#1e3a5f")
    return img

COLUMNS = [("pilih",   50,  "Pilih",      True),
           ("status",  70,  "Status",     True),
           ("group",   100, "Group",      True),
           ("nama",    160, "Nama",       True),
           ("ip",      130, "IP Address", True),
           ("time",    75,  "Time (ms)",  True),
           ("ttl",     55,  "TTL",        True),
           ("ket",     280, "Keterangan", True)]

THEMES = {
    "terang": {"bg": "#f0f0f0", "fg": "#000000", "tree_bg": "#ffffff", "tree_fg": "#000000",
               "down_bg": "#ffcccc", "btn_bg": "#e1e1e1", "btn_fg": "#000000",
               "entry_bg": "#ffffff", "entry_fg": "#000000", "caption_fg": "#1e3a5f",
               "combo_fg": "#000000"},
    "gelap":  {"bg": "#2b2b2b", "fg": "#e8e8e8", "tree_bg": "#1e1e1e", "tree_fg": "#e8e8e8",
               "down_bg": "#8b1a1a", "btn_bg": "#3d3d3d", "btn_fg": "#e8e8e8",
               "entry_bg": "#1e1e1e", "entry_fg": "#e8e8e8", "caption_fg": "#9ec5fe",
               "combo_fg": "#000000"},
}

IMG_W, IMG_H = 236, 140

class App:
    def __init__(self, root):
        self.root = root
        root.title(f"{APP}  -  {WM}")
        root.geometry("1080x700")
        root.minsize(940, 560)

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
        
        threading.Thread(target=self.loop, daemon=True).start()

    def build(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=5, pady=(5, 0))

        # KOLOM 1 (KIRI)
        self.col1 = tk.Frame(top, width=250, height=230, relief="groove", bd=1)
        self.col1.pack(side="left", anchor="n", padx=(0, 6))
        self.col1.pack_propagate(False)

        head = tk.Frame(self.col1)
        head.pack(fill="x", padx=4, pady=(3, 1))
        self.lbl_col1_title = tk.Label(head, text="Expresikan Gayamu", justify="left", font=("Segoe UI", 9, "bold"))
        self.lbl_col1_title.pack(side="left", padx=(2, 0))
        
        self.btn_arrow = tk.Button(head, text="\u25B4", width=2, command=self.toggle_foto_btns, font=("Segoe UI", 8, "bold"), relief="flat", bd=0, cursor="hand2")
        self.btn_arrow.pack(side="right", padx=(2, 2))

        # FIX: Background hitam agar video terlihat full screen seperti media player asli
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

        # KOLOM 2 (KANAN)
        col2 = tk.Frame(top)
        col2.pack(side="left", fill="both", expand=True)

        rowA = tk.Frame(col2)
        rowA.pack(fill="x", pady=(0, 2))
        
        def btn(parent, t, c, w=None): 
            tk.Button(parent, text=t, command=c, padx=8, pady=2, width=w).pack(side="left", padx=3)
            
        btn(rowA, "Remote (RDP)", self.do_rdp)
        btn(rowA, "Mapping \\\\IP", self.do_map)
        btn(rowA, "Open (http)", self.do_open)

        rowB = tk.Frame(col2)
        rowB.pack(fill="x", pady=2)
        btn(rowB, "+ Tambah IP", lambda: self.host_dialog(None))
        btn(rowB, "Edit", self.edit_host)
        btn(rowB, "Hapus", self.del_host)
        btn(rowB, "Pengaturan", self.settings)
        btn(rowB, "Tentang", self.about)
        btn(rowB, "Keluar", self.quit)

        rowC = tk.Frame(col2)
        rowC.pack(fill="x", pady=2)
        tk.Label(rowC, text="Group:").pack(side="left", padx=(3,2))
        
        self.cmb_group = ttk.Combobox(rowC, state="readonly", width=25)
        self.cmb_group.pack(side="left")
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)
        
        tk.Button(rowC, text="Semua", width=6, command=self.set_group_all).pack(side="left", padx=(2, 2))
        tk.Button(rowC, text="Stop Alarm", command=self.stop_alarm, padx=6, pady=2).pack(side="left", padx=(10, 10))

        rowD = tk.Frame(col2)
        rowD.pack(fill="x", pady=2)
        tk.Label(rowD, text="Tampilkan:").pack(side="left", padx=(0,2))
        tk.Radiobutton(rowD, text="Semua", variable=self.show_mode, value="all", command=self.save_and_refresh).pack(side="left")
        tk.Radiobutton(rowD, text="Hanya UP", variable=self.show_mode, value="up", command=self.save_and_refresh).pack(side="left", padx=(2, 0))
        tk.Radiobutton(rowD, text="Hanya DOWN", variable=self.show_mode, value="down", command=self.save_and_refresh).pack(side="left", padx=(2, 15))

        rowE = tk.Frame(col2)
        rowE.pack(fill="x", pady=2)
        tk.Label(rowE, text="Kolom tampil:").pack(side="left", padx=(0, 4))
        for cid, _, label, _d in COLUMNS:
            tk.Checkbutton(rowE, text=label, variable=self.col_show[cid], command=self.apply_columns, font=("Segoe UI", 8)).pack(side="left", padx=1)

        # MARQUEE
        kata = tk.Frame(self.root, relief="groove", bd=1)
        kata.pack(fill="x", padx=5, pady=(4, 0))
        tk.Label(kata, text="Kata Kata Hari ini:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(6, 4))
        tk.Button(kata, text="Tulis Kata", command=self.edit_caption, padx=6, pady=1, width=10, font=("Segoe UI", 8)).pack(side="left", padx=4)
        
        self.cv_marquee = tk.Canvas(kata, height=26, highlightthickness=0)
        self.cv_marquee.pack(side="left", fill="both", expand=True, padx=6, pady=4)

        # TABEL MONITORING
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
            
        if idx < 0 or idx >= len(disp) or disp[idx] != "pilih": 
            return
        
        item = self.tv.identify_row(event.y)
        if item: 
            self.toggle_check(item)
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
        f = filedialog.askopenfilename(title="Pilih Gambar", filetypes=[("Gambar", "*.jpg *.jpeg *.png *.bmp"), ("Semua", "*.*")])
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
        
        if self.vid_path and os.path.exists(self.vid_path) and HAS_CV2 and HAS_PIL:
            try:
                cap = cv2.VideoCapture(self.vid_path)
                ok, frame = cap.read()
                cap.release()
                if ok:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w = frame.shape[:2]
                    
                    # FIX: OpenCV Resize untuk performa cepat
                    ratio = min((IMG_W-4) / w, (IMG_H-4) / h)
                    new_w, new_h = int(w * ratio), int(h * ratio)
                    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                    
                    im = Image.fromarray(frame)
                    self.img_tk = ImageTk.PhotoImage(im)
                    self.cv_img.create_image(IMG_W//2, IMG_H//2, image=self.img_tk, anchor="center")
                    return
            except: 
                pass
            
        if not self.img_path or not os.path.exists(self.img_path):
            self.cv_img.create_text(IMG_W//2, IMG_H//2, text="Belum ada foto/video", fill=ph_fg)
            return

        try:
            if HAS_PIL:
                im = Image.open(self.img_path).convert("RGB")
                ratio = min((IMG_W-4) / im.width, (IMG_H-4) / im.height)
                new_w, new_h = int(im.width * ratio), int(im.height * ratio)
                im = im.resize((new_w, new_h), Image.LANCZOS)
                
                self.img_tk = ImageTk.PhotoImage(im)
            else:
                self.img_tk = tk.PhotoImage(file=self.img_path)
            self.cv_img.create_image(IMG_W//2, IMG_H//2, image=self.img_tk, anchor="center")
        except:
            self.cv_img.create_text(IMG_W//2, IMG_H//2, text="Gagal muat file", fill="red")

    def upload_video(self):
        f = filedialog.askopenfilename(title="Pilih Video", filetypes=[("Video", "*.mp4 *.avi *.mkv"), ("Semua file", "*.*")])
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
            
            # FIX: Resize menggunakan OpenCV (Sangat Cepat - Anti Patah-patah)
            ratio = min((IMG_W-4) / w, (IMG_H-4) / h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            im = Image.fromarray(frame)
            self.img_tk = ImageTk.PhotoImage(im)
            self.cv_img.delete("all")
            self.cv_img.create_image(IMG_W//2, IMG_H//2, image=self.img_tk, anchor="center")
        except: 
            return self.stop_video()
        
        # Kecepatan frame dinamis sesuai info asli dari file video
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
            elif isinstance(c, tk.Entry) or isinstance(c, tk.Text) or isinstance(c, tk.Spinbox): 
                c.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"])

    def apply_theme(self):
        t = THEMES["gelap"] if self.dark_mode.get() else THEMES["terang"]
        self.root.configure(bg=t["bg"])
        if hasattr(self, "lbl_col1_title"):
            self.lbl_col1_title.configure(bg=t["bg"], fg=t["fg"])
            self.btn_arrow.configure(bg=t["btn_bg"], fg=t["btn_fg"])
            
        for w in self.root.winfo_children():
            if isinstance(w, tk.Frame): 
                self._theme_frame(w, t)
            
        self.style.configure("Treeview", background=t["tree_bg"], fieldbackground=t["tree_bg"], foreground=t["tree_fg"], rowheight=25)
        self.style.map('Treeview', background=[('selected', '#3b82c4')], foreground=[('selected', 'white')])
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
                self.status[ip] = res
                
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
            for _ in range(self.alarm_dur.get() * 2):
                if self.alarm_muted or not self.running: 
                    return
                winsound.Beep(1200, 300)
                time.sleep(0.2)
        except: 
            pass

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
            
            tag = "down" if up is False else ("up" if up else "chk")
            if h["ip"] in self.checked: 
                tag = tag if tag == "down" else "sel"
            
            if mode == "down" and up is not False: 
                continue
            if mode == "up" and not up: 
                continue
            
            cek = "\u2611" if h["ip"] in self.checked else "\u2610"
            vals = (cek, st, h.get("group", "-"), h["name"], h["ip"], s.get("time", "-"), s.get("ttl", "-"), ket)
            
            if h["ip"] in existing_iids:
                self.tv.item(h["ip"], values=vals, tags=(tag,))
                existing_iids.remove(h["ip"])
            else:
                self.tv.insert("", "end", iid=h["ip"], values=vals, tags=(tag,))
                
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
        
        def preview_light():
            self.apply_theme()
            self.theme_window(w)
            
        def preview_dark():
            self.apply_theme()
            self.theme_window(w)
            
        tk.Radiobutton(w, text="Terang", variable=self.dark_mode, value=False, command=preview_light).grid(row=row, column=1, sticky="w")
        tk.Radiobutton(w, text="Gelap", variable=self.dark_mode, value=True, command=preview_dark).grid(row=row, column=2, sticky="w")
        
        def apply(): 
            self.delay_cache = self.delay.get()
            self.save()
            w.destroy()
            
        tk.Button(w, text="Simpan Pengaturan", command=apply, width=18).grid(row=row+1, column=0, columnspan=4, pady=12)
        self.theme_window(w)

    def about(self):
        w = tk.Toplevel(self.root)
        w.title("Tentang Aplikasi")
        w.grab_set()
        w.resizable(False, False)
        
        tk.Label(w, text=f"{APP}\n{WM}\n(Diperbarui untuk performa lebih stabil & multithreading)", justify="center", font=("Segoe UI", 9)).pack(padx=20, pady=15)
        tk.Button(w, text="Tutup", command=w.destroy, width=12).pack(pady=(0, 15))
        self.theme_window(w)

    def dump(self):
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
            "imgcaption": self.img_caption
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