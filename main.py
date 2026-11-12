import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import piexif
from PIL import Image, ImageOps, ImageTk, PngImagePlugin

# Drag & Drop Support (mit automatischem Fallback, falls nicht installiert)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


class MFWatermarkApp:

    def __init__(self, root):
        self.root = root
        self.root.title("MF_Watermark - EU AI Act Labelling Tool")
        self.root.geometry("1040x760")
        self.root.minsize(880, 660)

        self.image_paths = []
        self.current_preview_path = None
        self.tk_preview_img = None

        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "config.json"
        self.watermark_dir = self.base_dir / "watermarks"
        self.watermark_dir.mkdir(exist_ok=True)

        # Variablen für Optionen (Suffix & Überschreiben)
        self.overwrite_orig_var = tk.BooleanVar(value=False)
        self.suffix_var = tk.StringVar(value="_mf")
        self.delete_orig_on_convert_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._load_watermarks()
        self._load_config()

        # Beim Schließen Einstellungen automatisch speichern
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # --- 1. Top-Bar: Start Button & Options Button ---
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(
            top_frame,
            text="▶ Start Batch Processing",
            command=self.process_images,
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 8))

        self.options_btn = ttk.Button(
            top_frame,
            text="⚙ Options",
            command=self.open_options_dialog,
            width=16,
        )
        self.options_btn.pack(side=tk.RIGHT, ipady=8)

        # --- 2. Split-Bereich: Links Dateiliste, Rechts Live-Vorschau ---
        workspace = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        workspace.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Linkes Panel: Dateiliste & Buttons
        left_panel = ttk.LabelFrame(
            workspace, text="Image Queue (Drag & Drop files/folders here)", padding=8
        )
        workspace.add(left_panel, weight=1)

        list_container = ttk.Frame(left_panel)
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            list_container,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            activestyle="none",
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        self.file_listbox.bind("<<ListboxSelect>>", self._on_file_selected)

        if DND_AVAILABLE:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)

        btn_frame = ttk.Frame(left_panel, padding=(0, 8, 0, 0))
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="➕ Add Images", command=self.add_images).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(btn_frame, text="📁 Add Folder", command=self.add_folder).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_frame, text="➖ Remove", command=self.remove_selected).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_frame, text="✖ Clear", command=self.remove_all).pack(
            side=tk.RIGHT
        )

        # Rechtes Panel: Live-Vorschau
        right_panel = ttk.LabelFrame(workspace, text="Live Preview", padding=8)
        workspace.add(right_panel, weight=2)

        self.preview_canvas = tk.Canvas(
            right_panel, bg="#1e1f22", highlightthickness=0
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind("<Configure>", lambda e: self.update_preview())

        # --- 3. Einstellungen (Watermark & Output) ---
        settings_frame = ttk.LabelFrame(
            self.root, text="Watermark & Output Settings", padding=10
        )
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # Wasserzeichen-Auswahl
        wm_row = ttk.Frame(settings_frame)
        wm_row.pack(fill=tk.X, pady=3)
        ttk.Label(wm_row, text="EU Label (PNG):", width=18).pack(side=tk.LEFT)
        self.wm_combo = ttk.Combobox(wm_row, state="readonly")
        self.wm_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.wm_combo.bind("<<ComboboxSelected>>", self._on_wm_selected)
        ttk.Button(
            wm_row, text="Browse PNG...", command=self.browse_watermark
        ).pack(side=tk.LEFT)

        # Meta-Tag Text
        meta_row = ttk.Frame(settings_frame)
        meta_row.pack(fill=tk.X, pady=3)
        ttk.Label(meta_row, text="Meta / EXIF Tag:", width=18).pack(side=tk.LEFT)
        self.meta_var = tk.StringVar(value="AI GENERATED (EU AI Act Art. 50)")
        ttk.Entry(meta_row, textvariable=self.meta_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5
        )

        # Mittlerer Bereich: 3x3 Anchor Grid, Padding, Skalierung & Deckkraft
        mid_frame = ttk.Frame(settings_frame)
        mid_frame.pack(fill=tk.X, pady=8)

        # 3x3 Anchor Grid
        anchor_frame = ttk.LabelFrame(mid_frame, text="Anchor", padding=8)
        anchor_frame.pack(side=tk.LEFT, padx=(0, 12))
        self.anchor_var = tk.StringVar(value="se")
        anchors = [
            ("nw", 0, 0),
            ("n", 0, 1),
            ("ne", 0, 2),
            ("w", 1, 0),
            ("center", 1, 1),
            ("e", 1, 2),
            ("sw", 2, 0),
            ("s", 2, 1),
            ("se", 2, 2),
        ]
        for val, r, c in anchors:
            ttk.Radiobutton(
                anchor_frame,
                variable=self.anchor_var,
                value=val,
                command=self.update_preview,
            ).grid(row=r, column=c, padx=6, pady=3)

        # Padding (Abstand zum Rand)
        pad_frame = ttk.LabelFrame(mid_frame, text="Padding", padding=8)
        pad_frame.pack(side=tk.LEFT, padx=12)

        ttk.Label(pad_frame, text="Horizontal (X):").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.pad_x = tk.IntVar(value=20)
        ttk.Spinbox(
            pad_frame,
            from_=0,
            to=2000,
            textvariable=self.pad_x,
            width=7,
            command=self.update_preview,
        ).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(pad_frame, text="px").grid(row=0, column=2)

        ttk.Label(pad_frame, text="Vertical (Y):").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.pad_y = tk.IntVar(value=20)
        ttk.Spinbox(
            pad_frame,
            from_=0,
            to=2000,
            textvariable=self.pad_y,
            width=7,
            command=self.update_preview,
        ).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(pad_frame, text="px").grid(row=1, column=2)

        # Skalierung & Deckkraft
        prop_frame = ttk.LabelFrame(mid_frame, text="Scale & Opacity", padding=8)
        prop_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(prop_frame, text="Width (%):").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.scale_var = tk.IntVar(value=15)
        ttk.Scale(
            prop_frame,
            from_=2,
            to=100,
            variable=self.scale_var,
            command=lambda v: (
                self.scale_var.set(int(float(v))),
                self.update_preview(),
            ),
        ).grid(row=0, column=1, sticky=tk.EW, padx=8)
        ttk.Spinbox(
            prop_frame,
            from_=1,
            to=100,
            textvariable=self.scale_var,
            width=5,
            command=self.update_preview,
        ).grid(row=0, column=2, padx=2, pady=2)

        ttk.Label(prop_frame, text="Opacity (%):").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.opacity_var = tk.IntVar(value=90)
        ttk.Scale(
            prop_frame,
            from_=5,
            to=100,
            variable=self.opacity_var,
            command=lambda v: (
                self.opacity_var.set(int(float(v))),
                self.update_preview(),
            ),
        ).grid(row=1, column=1, sticky=tk.EW, padx=8)
        ttk.Spinbox(
            prop_frame,
            from_=1,
            to=100,
            textvariable=self.opacity_var,
            width=5,
            command=self.update_preview,
        ).grid(row=1, column=2, padx=2, pady=2)
        prop_frame.columnconfigure(1, weight=1)

        for var in (self.pad_x, self.pad_y, self.scale_var, self.opacity_var):
            var.trace_add("write", lambda *args: self.update_preview())

        # Zielordner-Optionen
        self.out_frame = ttk.LabelFrame(
            settings_frame, text="Output Directory & Naming", padding=8
        )
        self.out_frame.pack(fill=tk.X, pady=(4, 0))

        top_out_row = ttk.Frame(self.out_frame)
        top_out_row.pack(fill=tk.X)

        self.use_custom_out = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            top_out_row,
            text="Save to custom folder (Default: same folder as original)",
            variable=self.use_custom_out,
            command=self._toggle_out_dir,
        ).pack(side=tk.LEFT, anchor=tk.W)

        # Dynamische Anzeige des aktuellen Namensschemas
        self.naming_info_label = ttk.Label(
            top_out_row, text="", foreground="#2b7de9"
        )
        self.naming_info_label.pack(side=tk.RIGHT)
        self._update_naming_info_label()

        out_row = ttk.Frame(self.out_frame)
        out_row.pack(fill=tk.X, pady=(4, 0))
        self.out_dir_var = tk.StringVar(value="")
        self.out_entry = ttk.Entry(
            out_row, textvariable=self.out_dir_var, state="disabled"
        )
        self.out_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.out_btn = ttk.Button(
            out_row,
            text="Select Folder...",
            command=self.browse_out_dir,
            state="disabled",
        )
        self.out_btn.pack(side=tk.LEFT)

        # --- 4. Statusleiste ---
        dnd_status = (
            "Drag & Drop active."
            if DND_AVAILABLE
            else "Tip: Run 'pip install tkinterdnd2' to enable Drag & Drop."
        )
        self.status_var = tk.StringVar(value=f"Ready. {dnd_status}")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=4,
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # --- Options-Dialog (Überschreiben & freies Suffix) ---
    def open_options_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Options - File Naming & Overwrite")
        dlg.geometry("460x260")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        # Dialog zentrieren
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 230
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 130
        dlg.geometry(f"+{x}+{y}")

        frame = ttk.Frame(dlg, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Temporäre Variablen für den Dialog
        temp_overwrite = tk.BooleanVar(value=self.overwrite_orig_var.get())
        temp_suffix = tk.StringVar(value=self.suffix_var.get())
        temp_del_orig = tk.BooleanVar(value=self.delete_orig_on_convert_var.get())

        def toggle_fields():
            if temp_overwrite.get():
                suffix_entry.config(state="disabled")
                del_chk.config(state="normal")
                preview_lbl.config(
                    text="Result: <OriginalName>.png (Overwrites original!)"
                )
            else:
                suffix_entry.config(state="normal")
                del_chk.config(state="disabled")
                sfx = temp_suffix.get()
                preview_lbl.config(text=f"Result: <OriginalName>{sfx}.png")

        chk_overwrite = ttk.Checkbutton(
            frame,
            text="Overwrite original files (No suffix appended)",
            variable=temp_overwrite,
            command=toggle_fields,
        )
        chk_overwrite.pack(anchor=tk.W, pady=(0, 6))

        # Zusatz-Option falls Original z.B. .jpg war und in .png umgewandelt wird
        del_chk = ttk.Checkbutton(
            frame,
            text="Delete original non-PNG file (.jpg/.webp) after PNG conversion",
            variable=temp_del_orig,
        )
        del_chk.pack(anchor=tk.W, padx=(22, 0), pady=(0, 15))

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        suffix_row = ttk.Frame(frame)
        suffix_row.pack(fill=tk.X, pady=8)
        ttk.Label(suffix_row, text="Custom filename suffix:").pack(side=tk.LEFT)
        suffix_entry = ttk.Entry(suffix_row, textvariable=temp_suffix, width=18)
        suffix_entry.pack(side=tk.LEFT, padx=10)
        temp_suffix.trace_add("write", lambda *args: toggle_fields())

        preview_lbl = ttk.Label(frame, text="", foreground="#666666")
        preview_lbl.pack(anchor=tk.W, pady=4)

        toggle_fields()

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        def save_and_close():
            if not temp_overwrite.get() and not temp_suffix.get().strip():
                if not messagebox.askyesno(
                    "Empty Suffix",
                    "An empty suffix without 'Overwrite' enabled will still overwrite existing PNG files in the same folder.\n\nContinue anyway?",
                    parent=dlg,
                ):
                    return
            self.overwrite_orig_var.set(temp_overwrite.get())
            self.suffix_var.set(temp_suffix.get())
            self.delete_orig_on_convert_var.set(temp_del_orig.get())
            self._update_naming_info_label()
            self._save_config()
            dlg.destroy()

        ttk.Button(btn_row, text="Cancel", command=dlg.destroy).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(btn_row, text="Save Options", command=save_and_close).pack(
            side=tk.RIGHT
        )

    def _update_naming_info_label(self):
        if self.overwrite_orig_var.get():
            self.naming_info_label.config(
                text="Mode: Overwrite Original (<name>.png)", foreground="#d9534f"
            )
        else:
            sfx = self.suffix_var.get()
            self.naming_info_label.config(
                text=f"Mode: Append Suffix (<name>{sfx}.png)",
                foreground="#2b7de9",
            )

    def _load_config(self):
        if not self.config_file.exists():
            return
        try:
            data = json.loads(self.config_file.read_text(encoding="utf-8"))
            self.overwrite_orig_var.set(data.get("overwrite_original", False))
            self.suffix_var.set(data.get("suffix", "_mf"))
            self.delete_orig_on_convert_var.set(
                data.get("delete_orig_on_convert", True)
            )
            self.anchor_var.set(data.get("anchor", "se"))
            self.pad_x.set(data.get("pad_x", 20))
            self.pad_y.set(data.get("pad_y", 20))
            self.scale_var.set(data.get("scale", 15))
            self.opacity_var.set(data.get("opacity", 90))
            self.use_custom_out.set(data.get("use_custom_out", False))
            self.out_dir_var.set(data.get("out_dir", ""))
            self._toggle_out_dir()
            self._update_naming_info_label()

            saved_wm = data.get("watermark_path", "")
            if saved_wm and os.path.exists(saved_wm):
                vals = list(self.wm_combo["values"])
                if saved_wm not in vals:
                    vals.append(saved_wm)
                    self.wm_combo["values"] = vals
                self.wm_combo.set(saved_wm)
                self._on_wm_selected()
        except Exception:
            pass

    def _save_config(self):
        data = {
            "overwrite_original": self.overwrite_orig_var.get(),
            "suffix": self.suffix_var.get(),
            "delete_orig_on_convert": self.delete_orig_on_convert_var.get(),
            "anchor": self.anchor_var.get(),
            "pad_x": self.pad_x.get(),
            "pad_y": self.pad_y.get(),
            "scale": self.scale_var.get(),
            "opacity": self.opacity_var.get(),
            "use_custom_out": self.use_custom_out.get(),
            "out_dir": self.out_dir_var.get(),
            "watermark_path": self.wm_combo.get(),
        }
        try:
            self.config_file.write_text(
                json.dumps(data, indent=4), encoding="utf-8"
            )
        except Exception:
            pass

    def _on_close(self):
        self._save_config()
        self.root.destroy()

    def _load_watermarks(self):
        pngs = sorted([str(p) for p in self.watermark_dir.glob("*.png")])
        self.wm_combo["values"] = pngs
        if pngs:
            self.wm_combo.current(0)
            self._on_wm_selected()

    def _on_wm_selected(self, event=None):
        wm_name = Path(self.wm_combo.get()).stem.upper()
        if "MODIFIED" in wm_name:
            self.meta_var.set("AI MODIFIED (EU AI Act Art. 50)")
        elif "GENERATED" in wm_name:
            self.meta_var.set("AI GENERATED (EU AI Act Art. 50)")
        else:
            self.meta_var.set("AI CONTENT (EU AI Act Art. 50)")
        self.update_preview()

    def browse_watermark(self):
        path = filedialog.askopenfilename(
            title="Select Watermark PNG", filetypes=[("PNG Files", "*.png")]
        )
        if path:
            vals = list(self.wm_combo["values"])
            if path not in vals:
                vals.append(path)
                self.wm_combo["values"] = vals
            self.wm_combo.set(path)
            self._on_wm_selected()

    def _toggle_out_dir(self):
        state = "normal" if self.use_custom_out.get() else "disabled"
        self.out_entry.config(state=state)
        self.out_btn.config(state=state)

    def browse_out_dir(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.out_dir_var.set(folder)

    def _enqueue_paths(self, raw_paths):
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
        current_suffix = self.suffix_var.get().strip()
        overwrite = self.overwrite_orig_var.get()

        added = 0
        for item in raw_paths:
            p = Path(item)
            if p.is_dir():
                for sub in sorted(p.iterdir()):
                    # Überspringe bereits gestempelte Dateien beim Ordner-Import
                    is_already_suffixed = (
                        not overwrite
                        and current_suffix
                        and sub.stem.endswith(current_suffix)
                    )
                    if (
                        sub.is_file()
                        and sub.suffix.lower() in exts
                        and not is_already_suffixed
                        and str(sub) not in self.image_paths
                    ):
                        self.image_paths.append(str(sub))
                        self.file_listbox.insert(tk.END, str(sub))
                        added += 1
            elif p.is_file() and p.suffix.lower() in exts:
                if str(p) not in self.image_paths:
                    self.image_paths.append(str(p))
                    self.file_listbox.insert(tk.END, str(p))
                    added += 1

        if added > 0 and not self.current_preview_path:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(0)
            self.current_preview_path = self.image_paths[0]
            self.update_preview()

        self.status_var.set(
            f"{len(self.image_paths)} image(s) in queue (+{added} added)."
        )

    def _on_drop(self, event):
        dropped_items = self.root.tk.splitlist(event.data)
        self._enqueue_paths(dropped_items)

    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif")
            ],
        )
        if files:
            self._enqueue_paths(files)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Images")
        if folder:
            self._enqueue_paths([folder])

    def remove_selected(self):
        selected = self.file_listbox.curselection()
        if not selected:
            return
        for idx in reversed(selected):
            removed_path = self.image_paths[idx]
            self.file_listbox.delete(idx)
            del self.image_paths[idx]
            if removed_path == self.current_preview_path:
                self.current_preview_path = None

        if self.image_paths and not self.current_preview_path:
            self.file_listbox.selection_set(0)
            self.current_preview_path = self.image_paths[0]

        self.update_preview()
        self.status_var.set(f"{len(self.image_paths)} image(s) in queue.")

    def remove_all(self):
        self.file_listbox.delete(0, tk.END)
        self.image_paths.clear()
        self.current_preview_path = None
        self.update_preview()
        self.status_var.set("Queue cleared.")

    def _on_file_selected(self, event=None):
        sel = self.file_listbox.curselection()
        if sel:
            self.current_preview_path = self.image_paths[sel[0]]
            self.update_preview()

    @staticmethod
    def _calc_position(bg_w, bg_h, wm_w, wm_h, anchor, pad_x, pad_y):
        positions = {
            "nw": (pad_x, pad_y),
            "n": ((bg_w - wm_w) // 2, pad_y),
            "ne": (bg_w - wm_w - pad_x, pad_y),
            "w": (pad_x, (bg_h - wm_h) // 2),
            "center": ((bg_w - wm_w) // 2, (bg_h - wm_h) // 2),
            "e": (bg_w - wm_w - pad_x, (bg_h - wm_h) // 2),
            "sw": (pad_x, bg_h - wm_h - pad_y),
            "s": ((bg_w - wm_w) // 2, bg_h - wm_h - pad_y),
            "se": (bg_w - wm_w - pad_x, bg_h - wm_h - pad_y),
        }
        x, y = positions.get(anchor, (pad_x, pad_y))
        return max(0, x), max(0, y)

    def _render_watermarked_image(self, base_img, wm_img):
        try:
            scale_pct = max(1, min(100, int(self.scale_var.get()))) / 100.0
            opacity_pct = max(1, min(100, int(self.opacity_var.get()))) / 100.0
            pad_x = max(0, int(self.pad_x.get()))
            pad_y = max(0, int(self.pad_y.get()))
        except (tk.TclError, ValueError):
            scale_pct, opacity_pct, pad_x, pad_y = 0.15, 0.90, 20, 20

        anchor = self.anchor_var.get()
        bg_w, bg_h = base_img.size

        target_wm_w = max(1, int(bg_w * scale_pct))
        aspect_ratio = wm_img.height / wm_img.width
        target_wm_h = max(1, int(target_wm_w * aspect_ratio))
        wm_resized = wm_img.resize(
            (target_wm_w, target_wm_h), Image.Resampling.LANCZOS
        )

        if opacity_pct < 1.0:
            alpha = wm_resized.getchannel("A")
            alpha = alpha.point(lambda a: int(a * opacity_pct))
            wm_resized.putalpha(alpha)

        pos_x, pos_y = self._calc_position(
            bg_w, bg_h, target_wm_w, target_wm_h, anchor, pad_x, pad_y
        )
        layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        layer.paste(wm_resized, (pos_x, pos_y))
        return Image.alpha_composite(base_img, layer)

    def update_preview(self):
        self.preview_canvas.delete("all")
        c_w = self.preview_canvas.winfo_width()
        c_h = self.preview_canvas.winfo_height()
        if c_w < 20 or c_h < 20:
            return

        if not self.current_preview_path or not os.path.exists(
            self.current_preview_path
        ):
            self.preview_canvas.create_text(
                c_w // 2,
                c_h // 2,
                text="Drag & Drop images here\nor select an image from the list",
                fill="#888888",
                font=("Segoe UI", 11),
                justify=tk.CENTER,
            )
            return

        try:
            with Image.open(self.current_preview_path) as orig:
                base_rgba = ImageOps.exif_transpose(orig).convert("RGBA")

            wm_path = self.wm_combo.get()
            if wm_path and os.path.exists(wm_path):
                with Image.open(wm_path) as wm_orig:
                    wm_rgba = wm_orig.convert("RGBA")
                composed = self._render_watermarked_image(base_rgba, wm_rgba)
            else:
                composed = base_rgba

            img_w, img_h = composed.size
            ratio = min((c_w - 16) / img_w, (c_h - 16) / img_h)
            new_w = max(1, int(img_w * ratio))
            new_h = max(1, int(img_h * ratio))

            preview_pil = composed.resize(
                (new_w, new_h), Image.Resampling.BILINEAR
            )
            self.tk_preview_img = ImageTk.PhotoImage(preview_pil)
            self.preview_canvas.create_image(
                c_w // 2, c_h // 2, image=self.tk_preview_img, anchor=tk.CENTER
            )
        except Exception as e:
            self.preview_canvas.create_text(
                c_w // 2,
                c_h // 2,
                text=f"Preview Error:\n{e}",
                fill="#ff6b6b",
                justify=tk.CENTER,
            )

    @staticmethod
    def _prepare_metadata(original_img, label_text, wm_filename):
        pnginfo = PngImagePlugin.PngInfo()
        reserved = {"exif", "icc_profile", "transparency", "gamma", "dpi"}
        for k, v in original_img.info.items():
            if k not in reserved and isinstance(v, str):
                pnginfo.add_text(k, v)

        pnginfo.add_itxt("AI-Label", label_text)
        pnginfo.add_itxt("AI-Watermark-File", wm_filename)
        pnginfo.add_itxt(
            "DigitalSourceType",
            "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
        )

        raw_exif = original_img.info.get("exif")
        try:
            exif_dict = (
                piexif.load(raw_exif)
                if raw_exif
                else {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
            )
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

        exif_dict["0th"][piexif.ImageIFD.Orientation] = 1

        existing_desc = exif_dict["0th"].get(
            piexif.ImageIFD.ImageDescription, b""
        )
        if isinstance(existing_desc, bytes):
            existing_desc = existing_desc.decode(
                "utf-8", errors="ignore"
            ).strip("\x00")
        new_desc = (
            f"{existing_desc} | {label_text}".strip(" |")
            if existing_desc
            else label_text
        )
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = new_desc.encode(
            "utf-8"
        )

        user_comment = b"ASCII\x00\x00\x00" + label_text.encode("utf-8")
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = user_comment

        exif_bytes = piexif.dump(exif_dict)
        return pnginfo, exif_bytes

    def process_images(self):
        if not self.image_paths:
            messagebox.showwarning("No Images", "Please add at least one image.")
            return

        wm_path = self.wm_combo.get()
        if not wm_path or not os.path.exists(wm_path):
            messagebox.showerror(
                "No Watermark", "Please select a valid watermark PNG."
            )
            return

        custom_out = (
            self.out_dir_var.get().strip() if self.use_custom_out.get() else None
        )
        if self.use_custom_out.get() and not custom_out:
            messagebox.showwarning(
                "Output Folder", "Please select a custom output folder."
            )
            return

        if custom_out:
            os.makedirs(custom_out, exist_ok=True)

        overwrite_mode = self.overwrite_orig_var.get()
        suffix = "" if overwrite_mode else self.suffix_var.get()
        delete_orig_non_png = self.delete_orig_on_convert_var.get()

        wm_base = Image.open(wm_path).convert("RGBA")
        wm_filename = Path(wm_path).name
        label_text = self.meta_var.get().strip()

        success_count = 0
        errors = []

        for idx, img_path in enumerate(list(self.image_paths), start=1):
            try:
                p = Path(img_path)
                self.status_var.set(
                    f"Processing ({idx}/{len(self.image_paths)}): {p.name}..."
                )
                self.root.update_idletasks()

                with Image.open(p) as orig_img:
                    icc_profile = orig_img.info.get("icc_profile")
                    dpi = orig_img.info.get("dpi")
                    pnginfo, exif_bytes = self._prepare_metadata(
                        orig_img, label_text, wm_filename
                    )
                    transposed = ImageOps.exif_transpose(orig_img)
                    base_rgba = transposed.convert("RGBA")

                combined = self._render_watermarked_image(base_rgba, wm_base)

                out_dir = Path(custom_out) if custom_out else p.parent
                out_path = out_dir / f"{p.stem}{suffix}.png"

                save_kwargs = {
                    "format": "PNG",
                    "pnginfo": pnginfo,
                    "exif": exif_bytes,
                }
                if icc_profile:
                    save_kwargs["icc_profile"] = icc_profile
                if dpi:
                    save_kwargs["dpi"] = dpi

                combined.save(out_path, **save_kwargs)

                # Wenn "Originaldatei überschreiben" aktiv ist und das Original kein PNG war
                # (z.B. foto.jpg -> foto.png im selben Ordner), alte Quelldatei optional entfernen
                if (
                    overwrite_mode
                    and delete_orig_non_png
                    and not custom_out
                    and p.resolve() != out_path.resolve()
                    and p.exists()
                ):
                    p.unlink()
                    # Pfad in der Queue aktualisieren, damit die Vorschau weiterhin funktioniert
                    list_idx = self.image_paths.index(img_path)
                    self.image_paths[list_idx] = str(out_path)
                    self.file_listbox.delete(list_idx)
                    self.file_listbox.insert(list_idx, str(out_path))
                    if self.current_preview_path == img_path:
                        self.current_preview_path = str(out_path)

                success_count += 1

            except Exception as e:
                errors.append(f"{Path(img_path).name}: {e}")

        self.update_preview()
        self.status_var.set(
            f"Finished: {success_count}/{len(self.image_paths)} processed."
        )
        if errors:
            messagebox.showwarning(
                "Completed with Errors",
                f"Processed {success_count} images.\n\nErrors:\n"
                + "\n".join(errors[:10]),
            )
        else:
            messagebox.showinfo(
                "Success", f"Successfully processed {success_count} image(s)!"
            )


if __name__ == "__main__":
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    app = MFWatermarkApp(root)
    root.mainloop()