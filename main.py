import tkinter as tk
from tkinter import ttk, filedialog
import threading
import subprocess
import os
import time
import json
from yt_dlp import YoutubeDL

CONFIG_FILE = "config.json"

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pobierak")
        self.root.geometry("1400x600")
        self.root.configure(bg="#1e1e1e")

        self.download_dir = self.load_config()
        self.entries = []
        self.active_downloads = 0
        self.max_concurrent_downloads = 3

        self.set_dark_style()

        control_frame = ttk.Frame(self.root, style="Dark.TFrame")
        control_frame.pack(fill="x", padx=10, pady=(10, 0))

        self.folder_label = ttk.Label(control_frame, text=f"Folder: {self.download_dir}", style="Dark.TLabel")
        self.folder_label.pack(side="left")
        ttk.Button(control_frame, text="Wybierz folder", command=self.choose_folder, style="Dark.TButton").pack(side="left", padx=10)

        label_frame = ttk.Frame(self.root, style="Dark.TFrame")
        label_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(label_frame, text="Nazwa pliku", style="Dark.TLabel").grid(row=0, column=0, padx=(25, 0), sticky="w")
        ttk.Label(label_frame, text="Link do filmu", style="Dark.TLabel").grid(row=0, column=1, padx=(150, 0), sticky="w")
        ttk.Label(label_frame, text="Jakość video", style="Dark.TLabel").grid(row=0, column=2, padx=(100, 0), sticky="w")
        ttk.Label(label_frame, text="Audio", style="Dark.TLabel").grid(row=0, column=3, padx=(100, 0), sticky="w")

        self.entries_frame = ttk.Frame(self.root, style="Dark.TFrame")
        self.entries_frame.pack(fill="both", expand=True, padx=10)

        self.add_entry()

        button_frame = ttk.Frame(self.root, style="Dark.TFrame")
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Dodaj +", command=self.add_entry, style="Dark.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="Pobierz", command=self.start_downloads, style="Dark.TButton").pack(side="left", padx=5)

    def set_dark_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Dark.TFrame", background="#1e1e1e")
        style.configure("Dark.TLabel", background="#1e1e1e", foreground="#e5e5e5")
        style.configure("Dark.TButton", background="#333333", foreground="#e5e5e5", font=("Segoe UI", 10), padding=6)
        style.map("Dark.TButton", background=[("active", "#444444")], foreground=[("disabled", "#888888")])
        style.configure("TEntry", fieldbackground="#2d2d2d", foreground="#ffffff", insertcolor="#ffffff")
        style.configure("TScrollbar", background="#444444")
        style.configure("Orange.Horizontal.TProgressbar", troughcolor="#2d2d2d", background="#ff9800", thickness=10)
        style.configure("Green.Horizontal.TProgressbar", troughcolor="#2d2d2d", background="#4caf50", thickness=10)
        style.configure("Red.Horizontal.TProgressbar", troughcolor="#2d2d2d", background="#f44336", thickness=10)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_dir = folder
            self.folder_label.config(text=f"Folder: {self.download_dir}")
            self.save_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("download_dir", os.path.expanduser("~/Downloads"))
        return os.path.expanduser("~/Downloads")

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"download_dir": self.download_dir}, f)

    def add_entry(self):
        frame = ttk.Frame(self.entries_frame, style="Dark.TFrame")
        frame.pack(fill="x", pady=5)

        filename_entry = ttk.Entry(frame, width=30)
        filename_entry.pack(side="left", padx=5)

        url_entry = ttk.Entry(frame, width=21)
        url_entry.pack(side="left", padx=(20, 5))

        video_combobox = ttk.Combobox(frame, width=25, state="readonly")
        video_combobox.pack(side="left", padx=5)

        audio_combobox = ttk.Combobox(frame, width=35, state="readonly")
        audio_combobox.pack(side="left", padx=5)
        audio_combobox.pack_forget()

        def fetch_formats():
            url = url_entry.get()
            if not url:
                return
            threading.Thread(target=self.populate_formats, args=(url, video_combobox, audio_combobox)).start()

        ttk.Button(frame, text="🔍", width=2, command=fetch_formats, style="Dark.TButton").pack(side="left")

        remove_button = ttk.Button(frame, text="-", width=2, command=lambda: self.remove_entry(frame), style="Dark.TButton")
        remove_button.pack(side="left", padx=5)

        progress = ttk.Progressbar(frame, length=150, mode='determinate', style="Orange.Horizontal.TProgressbar")
        progress.pack(side="left", padx=5)

        time_label = ttk.Label(frame, text="", style="Dark.TLabel")
        time_label.pack(side="left", padx=5)

        self.entries.append((filename_entry, url_entry, video_combobox, audio_combobox, progress, time_label))

    def remove_entry(self, frame):
        for i, (fname, url, vcb, acb, prog, label) in enumerate(self.entries):
            if fname.master == frame:
                frame.destroy()
                del self.entries[i]
                break

    def populate_formats(self, url, video_combo, audio_combo):
        try:
            ydl_opts = {'quiet': True, 'skip_download': True}
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])

                video_choices = []
                audio_choices = []

                for fmt in formats:
                    f_id = fmt.get('format_id')
                    resolution = fmt.get('height')
                    ext = fmt.get('ext')
                    proto = fmt.get('protocol')
                    acodec = fmt.get('acodec')
                    vcodec = fmt.get('vcodec')
                    abr = fmt.get('abr')

                    if not f_id or not ext:
                        continue

                    label = f"{f_id}"
                    if 'dash' in f_id or 'dash' in proto:
                        label = f"[DASH] {f_id}"
                    elif 'hls' in f_id or 'hls' in proto:
                        label = f"[HLS] {f_id}"
                    elif resolution:
                        label = f"{resolution}p ({f_id})"

                    if acodec != 'none' and vcodec == 'none':
                        if abr:
                            label += f" ({int(abr)} kbps)"
                        audio_choices.append((label, f_id))
                    elif vcodec != 'none':
                        video_choices.append((label, f_id))

                if video_choices:
                    video_combo["values"] = [label for label, _ in video_choices]
                    video_combo.format_map = {label: f_id for label, f_id in video_choices}
                    video_combo.current(0)

                if audio_choices:
                    audio_combo["values"] = [label for label, _ in audio_choices]
                    audio_combo.format_map = {label: f_id for label, f_id in audio_choices}
                    audio_combo.current(0)
                    audio_combo.pack(side="left", padx=5)

        except Exception as e:
            video_combo["values"] = ["Błąd pobierania"]
            video_combo.current(0)
            print("Błąd przy pobieraniu formatów:", e)

    def start_downloads(self):
        self.download_queue = [
            (
                f.get(), u.get(), vcb.get(),
                getattr(vcb, "format_map", {}).get(vcb.get(), None),
                acb.get(),
                getattr(acb, "format_map", {}).get(acb.get(), None),
                p, t
            )
            for f, u, vcb, acb, p, t in self.entries if f.get() and u.get() and vcb.get()
        ]
        for _ in range(min(self.max_concurrent_downloads, len(self.download_queue))):
            self.next_download()

    def next_download(self):
        if self.download_queue:
            filename, url, v_label, v_fmt_id, a_label, a_fmt_id, progress, time_label = self.download_queue.pop(0)
            threading.Thread(target=self.download_worker, args=(filename, url, v_fmt_id, a_fmt_id, progress, time_label)).start()

    def download_worker(self, filename, url, v_fmt_id, a_fmt_id, progress_bar, time_label):
        self.active_downloads += 1
        start_time = time.time()
        try:
            self.set_progressbar_color(progress_bar, "orange")
            self.download_video(filename, url, v_fmt_id, a_fmt_id, progress_bar)
            self.set_progressbar_color(progress_bar, "green")
            progress_bar["value"] = 100
        except Exception as e:
            print(f"Błąd pobierania {filename}: {e}")
            self.set_progressbar_color(progress_bar, "red")
        finally:
            elapsed = time.time() - start_time
            time_label.config(text=f"{elapsed:.1f}s")
            self.active_downloads -= 1
            self.next_download()

    def download_video(self, filename, url, v_fmt_id, a_fmt_id, progress_bar):
        output_template = os.path.join(self.download_dir, f"{filename}.%(ext)s")
        format_string = v_fmt_id if not a_fmt_id else f"{v_fmt_id}+{a_fmt_id}"
        ydl_opts = {
            'format': format_string,
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'progress_hooks': [lambda d: self.update_progress(d, progress_bar)],
            'quiet': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def update_progress(self, d, progress_bar):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total * 100
                progress_bar["value"] = percent

    def set_progressbar_color(self, progressbar, color_name):
        styles = {
            "orange": "Orange.Horizontal.TProgressbar",
            "green": "Green.Horizontal.TProgressbar",
            "red": "Red.Horizontal.TProgressbar"
        }
        progressbar.configure(style=styles.get(color_name, "Orange.Horizontal.TProgressbar"))

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()