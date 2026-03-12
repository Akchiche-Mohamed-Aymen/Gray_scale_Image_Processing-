import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from processing import *

# ─── Colors & Fonts ───────────────────────────────────────────────────────────

BG      = "#F7F7F8"
WHITE   = "#FFFFFF"
ACCENT  = "#5B6BF5"
TEXT    = "#1A1A2E"
SUBTEXT = "#8888A0"
BORDER  = "#E2E2EE"
PINK    = "#EC4899"
GREEN   = "#059669"
PURPLE  = "#8B5CF6"
GRAY    = "#6B7280"

FONT    = ("Segoe UI", 10)
FONT_B  = ("Segoe UI", 10, "bold")
FONT_SM = ("Segoe UI", 9)
FONT_H  = ("Segoe UI", 13, "bold")


# ─── Small Reusable Helpers ───────────────────────────────────────────────────

def Card(parent, **kw):
    return tk.Frame(parent, bg=WHITE,
                    highlightbackground=BORDER, highlightthickness=1, **kw)

def Label(parent, text, font=FONT, fg=TEXT, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg,
                    bg=parent["bg"], **kw)

def Button(parent, text, cmd, color=ACCENT):
    btn = tk.Button(parent, text=text, command=cmd,
                    bg=color, fg=WHITE, font=FONT_B,
                    relief="flat", cursor="hand2",
                    padx=14, pady=7, bd=0,
                    activebackground=color,
                    activeforeground=WHITE)
    btn.bind("<Enter>", lambda e: btn.config(bg=_darken(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn

class Slider(tk.Frame):
    """Clean flat slider replacing the ugly tk.Scale widget."""

    def __init__(self, parent, var, from_, to, cmd, resolution=1, **kw):
        super().__init__(parent, bg=WHITE, **kw)
        self.var        = var
        self.from_      = from_
        self.to         = to
        self.cmd        = cmd
        self.resolution = resolution
        self._dragging  = False

        self.W, self.H  = 220, 36
        self.PAD        = 10   # horizontal padding for the track

        self.canvas = tk.Canvas(self, width=self.W, height=self.H,
                                bg=WHITE, highlightthickness=0)
        self.canvas.pack()

        # Value label on the right
        self.val_lbl = tk.Label(self, font=FONT_SM, fg=SUBTEXT, bg=WHITE, width=5)
        self.val_lbl.pack(side="right", padx=(0, 4))

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        var.trace_add("write", lambda *_: self._redraw())
        self._redraw()

    # ── internals ─────────────────────────────────────────────────

    def _track_x(self):
        """X range available for the thumb."""
        return self.PAD, self.W - self.PAD

    def _val_to_x(self, val):
        x0, x1 = self._track_x()
        t = (val - self.from_) / (self.to - self.from_)
        return x0 + t * (x1 - x0)

    def _x_to_val(self, x):
        x0, x1 = self._track_x()
        t = max(0.0, min(1.0, (x - x0) / (x1 - x0)))
        raw = self.from_ + t * (self.to - self.from_)
        # snap to resolution
        snapped = round(raw / self.resolution) * self.resolution
        return max(self.from_, min(self.to, snapped))

    def _redraw(self):
        c  = self.canvas
        cx = self._val_to_x(self.var.get())
        cy = self.H // 2

        c.delete("all")

        # Track background (full)
        c.create_rounded_rect = lambda *a, **kw: None   # no-op placeholder
        x0, x1 = self._track_x()
        c.create_rectangle(x0, cy - 3, x1, cy + 3,
                           fill="#E0E0F0", outline="", tags="track_bg")

        # Track fill (left of thumb)
        if cx > x0:
            c.create_rectangle(x0, cy - 3, cx, cy + 3,
                               fill=ACCENT, outline="", tags="track_fill")

        # Thumb circle
        r = 8
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      fill=ACCENT, outline=WHITE, width=2, tags="thumb")

        # Update value label
        val = self.var.get()
        fmt = f"{val:.2f}" if self.resolution < 1 else f"{int(val):+d}" if self.from_ < 0 else f"{int(val)}"
        self.val_lbl.config(text=fmt)

    def _on_press(self, e):
        self._dragging = True
        self._set(e.x)

    def _on_drag(self, e):
        if self._dragging:
            self._set(e.x)

    def _on_release(self, e):
        self._dragging = False

    def _set(self, x):
        val = self._x_to_val(x)
        self.var.set(val)
        if self.cmd:
            self.cmd(val)

def Separator(parent):
    return tk.Frame(parent, bg=BORDER, height=1)

def _darken(hex_color):
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    r, g, b = max(0, r - 25), max(0, g - 25), max(0, b - 25)
    return f"#{r:02x}{g:02x}{b:02x}"


# ─── Image Panel ──────────────────────────────────────────────────────────────

def make_image_panel(parent, title, color=ACCENT):
    frame = Card(parent)
    frame.pack(side="left", fill="both", expand=True, padx=6)

    header = tk.Frame(frame, bg=color, height=30)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text=title, font=FONT_B,
             fg=WHITE, bg=color).pack(side="left", padx=12, pady=5)

    lbl = tk.Label(frame, bg="#F2F2FA", text="No image loaded",
                   font=FONT_SM, fg=SUBTEXT)
    lbl.pack(fill="both", expand=True, padx=10, pady=10)
    return lbl


# ─── Main Application ─────────────────────────────────────────────────────────

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Image Studio")
        self.configure(bg=BG)
        self.minsize(1000, 700)

        self.original  = None
        self.processed = None
        self.filepath  = None

        self.v_bright  = tk.DoubleVar(value=0)
        self.v_alpha   = tk.DoubleVar(value=1.0)
        self.v_lc_beta = tk.DoubleVar(value=0)
        self.v_thresh  = tk.DoubleVar(value=128)

        self._build_menu()
        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # MENU
    # ─────────────────────────────────────────────────────────────────────────

    def _build_menu(self):
        menu = tk.Menu(self, bg=WHITE, fg=TEXT, relief="flat")
        self.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=False, bg=WHITE, fg=TEXT)
        file_menu.add_command(label="Open Image…",  command=self.open_image,  accelerator="Ctrl+O")
        file_menu.add_command(label="Save Result…", command=self.save_result, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit",         command=self.destroy)
        menu.add_cascade(label="File", menu=file_menu)

        self.bind_all("<Control-o>", lambda e: self.open_image())
        self.bind_all("<Control-s>", lambda e: self.save_result())

    # ─────────────────────────────────────────────────────────────────────────
    # LAYOUT  —  top bar / left controls / right: images on top + histogram below
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ──
        bar = tk.Frame(self, bg=WHITE, height=50,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="✦ Image Studio", font=FONT_H,
                 fg=ACCENT, bg=WHITE).pack(side="left", padx=20)

        self.lbl_tx   = tk.Label(bar, text="No transformation", font=FONT_SM, fg=ACCENT,  bg=WHITE)
        self.lbl_size = tk.Label(bar, text="",                  font=FONT_SM, fg=SUBTEXT, bg=WHITE)
        self.lbl_file = tk.Label(bar, text="No file open",      font=FONT_SM, fg=SUBTEXT, bg=WHITE)

        self.lbl_tx  .pack(side="right", padx=(0, 20))
        tk.Label(bar, text="·", font=FONT_SM, fg=SUBTEXT, bg=WHITE).pack(side="right")
        self.lbl_size.pack(side="right", padx=6)
        tk.Label(bar, text="·", font=FONT_SM, fg=SUBTEXT, bg=WHITE).pack(side="right")
        self.lbl_file.pack(side="right", padx=(20, 4))

        # ── Body: left controls | right content ──
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_controls(body)   # left column

        # Right column: images on top, histogram on bottom
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_images(right)     # top of right column
        self._build_histogram(right)  # bottom of right column

    # ─────────────────────────────────────────────────────────────────────────
    # LEFT — CONTROLS (scrollable + pinned buttons)
    # ─────────────────────────────────────────────────────────────────────────

    def _build_controls(self, parent):
        panel = Card(parent, width=265)
        panel.pack(side="left", fill="y", padx=(0, 8))
        panel.pack_propagate(False)

        # Pinned at bottom — packed first so always visible
        bottom = tk.Frame(panel, bg=WHITE)
        bottom.pack(side="bottom", fill="x", padx=16, pady=12)
        Separator(bottom).pack(fill="x", pady=(0, 10))
        Button(bottom, "⊞  Compare Side by Side", self._compare,
               color=ACCENT).pack(fill="x", pady=(0, 6))
        Button(bottom, "↺  Reset to Original", self._reset,
               color=GRAY).pack(fill="x")

        # Scrollable controls
        canvas = tk.Canvas(panel, bg=WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        f = tk.Frame(canvas, bg=WHITE)
        canvas.create_window((0, 0), window=f, anchor="nw")
        f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1 * e.delta / 120), "units"))

        fp = tk.Frame(f, bg=WHITE)
        fp.pack(fill="x", padx=16, pady=16)

        # ── 1. Brightness ──
        Label(fp, "☀  Brightness", font=FONT_B).pack(anchor="w")
        Label(fp, "β ∈ [−150, +150]  —  real-time", font=FONT_SM, fg=SUBTEXT).pack(anchor="w")
        Slider(fp, self.v_bright, -150, 150,
               lambda _: self._apply_brightness()).pack(anchor="w", pady=(4, 10))
        Separator(fp).pack(fill="x", pady=10)

        # ── 2. Linear Contrast ──
        Label(fp, "◈  Linear Contrast", font=FONT_B).pack(anchor="w")
        Label(fp, "α ∈ [0.1, 3.0]  —  real-time", font=FONT_SM, fg=SUBTEXT).pack(anchor="w")
        Slider(fp, self.v_alpha, 0.1, 3.0, lambda _: self._apply_linear_contrast(), resolution=0.05).pack(anchor="w", pady=(4, 4))
        Label(fp, "β ∈ [−100, +100]", font=FONT_SM, fg=SUBTEXT).pack(anchor="w")
        Slider(fp, self.v_lc_beta, -100, 100,
               lambda _: self._apply_linear_contrast()).pack(anchor="w", pady=(4, 10))
        Separator(fp).pack(fill="x", pady=10)

        # ── 3. Contrast Stretch ──
        Label(fp, "⟷  Contrast Stretch", font=FONT_B).pack(anchor="w")
        Label(fp, "Leave empty for Auto (uses image min/max)", font=FONT_SM, fg=SUBTEXT).pack(anchor="w", pady=(2, 6))

        row = tk.Frame(fp, bg=WHITE)
        row.pack(anchor="w")
        tk.Label(row, text="f_min", font=FONT_SM, fg=SUBTEXT, bg=WHITE).pack(side="left")
        self.e_fmin = tk.Entry(row, width=5, font=FONT_SM, relief="solid", bd=1)
        self.e_fmin.pack(side="left", padx=(4, 8))
        tk.Label(row, text="f_max", font=FONT_SM, fg=SUBTEXT, bg=WHITE).pack(side="left")
        self.e_fmax = tk.Entry(row, width=5, font=FONT_SM, relief="solid", bd=1)
        self.e_fmax.pack(side="left", padx=4)

        Button(fp, "Apply Stretch", self._apply_contrast_stretch,
               color=PURPLE).pack(anchor="w", pady=(8, 10))
        Separator(fp).pack(fill="x", pady=10)

        # ── 4. Threshold ──
        Label(fp, "▣  Threshold", font=FONT_B).pack(anchor="w")
        Label(fp, "T ∈ [0, 255]  →  output is binary (0 or 255)", font=FONT_SM, fg=SUBTEXT).pack(anchor="w")
        Slider(fp, self.v_thresh, 0, 255,
               lambda _: None).pack(anchor="w", pady=(4, 4))
        Button(fp, "Apply Threshold", self._apply_threshold,
               color=PINK).pack(anchor="w", pady=(2, 10))
        Separator(fp).pack(fill="x", pady=10)

        Label(fp, "≋  Histogram Equalization", font=FONT_B).pack(anchor="w")
        Label(fp, "Redistributes pixel intensities", font=FONT_SM, fg=SUBTEXT).pack(anchor="w", pady=(2, 6))
        Button(fp, "Equalize", self._apply_histogram_eq,
               color=GREEN).pack(anchor="w", pady=(0, 10))

    # ─────────────────────────────────────────────────────────────────────────
    # TOP-RIGHT — IMAGE PANELS
    # ─────────────────────────────────────────────────────────────────────────

    def _build_images(self, parent):
        # Fixed height so the histogram below always has consistent space
        container = tk.Frame(parent, bg=BG, height=380)
        container.pack(fill="x", pady=(0, 8))
        container.pack_propagate(False)

        self.lbl_original  = make_image_panel(container, "Original (Grayscale)", color=ACCENT)
        self.lbl_processed = make_image_panel(container, "Processed",            color=PURPLE)

    # ─────────────────────────────────────────────────────────────────────────
    # BOTTOM-RIGHT — HISTOGRAM + CDF  (side by side in one figure)
    # ─────────────────────────────────────────────────────────────────────────

    def _build_histogram(self, parent):
        panel = Card(parent)
        panel.pack(fill="x", pady=(0, 0))

        header = tk.Frame(panel, bg=ACCENT, height=30)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Histogram & CDF  —  Processed Image",
                 font=FONT_B, fg=WHITE, bg=ACCENT).pack(side="left", padx=12, pady=5)

        # One wide figure: histogram on left, CDF on right
        self.fig = Figure(figsize=(8, 2.2), dpi=95, facecolor=WHITE)
        self.ax_hist = self.fig.add_subplot(121)
        self.ax_cdf  = self.fig.add_subplot(122)
        self.fig.tight_layout(pad=2.5)

        self.canvas_hist = FigureCanvasTkAgg(self.fig, master=panel)
        self.canvas_hist.get_tk_widget().pack(fill="x", padx=10, pady=8)

        self._draw_placeholder_histogram()

    # ─────────────────────────────────────────────────────────────────────────
    # FILE ACTIONS
    # ─────────────────────────────────────────────────────────────────────────

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if not path:
            return

        try:
            self.original  = load_image(path)
            self.processed = self.original.copy()
            self.filepath  = path
            self._reset_sliders()
            self._refresh(tx="Original")
            h, w = self.original.shape
            name = path.split("/")[-1].split("\\")[-1]
            self.lbl_file.config(text=name)
            self.lbl_size.config(text=f"{w}×{h} px  ·  Grayscale")
        except Exception as ex:
            messagebox.showerror("Error", f"Could not open image:\n{ex}")

    def save_result(self):
        if self.processed is None:
            messagebox.showwarning("Nothing to save", "Process an image first.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Result",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")])
        if not path:
            return

        try:
            Image.fromarray(self.processed.astype(np.uint8)).save(path)
            messagebox.showinfo("Saved", f"Saved to:\n{path}")
        except Exception as ex:
            messagebox.showerror("Error", f"Could not save:\n{ex}")


    def _apply_brightness(self):
        if self.original is None:
            return
        b = self.v_bright.get()
        self.processed = adjust_brightness(self.original, b)
        self._refresh(tx=f"Brightness  β={int(b):+d}")

    def _apply_linear_contrast(self):
        if self.original is None:
            return
        a, b = self.v_alpha.get(), self.v_lc_beta.get()
        self.processed = linear_contrast(self.original, a, b)
        self._refresh(tx=f"Linear Contrast  α={a:.2f}  β={int(b):+d}")

    def _apply_contrast_stretch(self):
        if self.original is None:
            return
        try:
            f_min = float(self.e_fmin.get()) if self.e_fmin.get().strip() else None
            f_max = float(self.e_fmax.get()) if self.e_fmax.get().strip() else None
        except ValueError:
            messagebox.showerror("Invalid Input", "f_min and f_max must be numbers (or leave empty).")
            return
        self.processed = contrast_strech(self.original, f_min, f_max)
        lo = int(f_min) if f_min is not None else "auto"
        hi = int(f_max) if f_max is not None else "auto"
        self._refresh(tx=f"Contrast Stretch  [{lo} → {hi}]")

    def _apply_threshold(self):
        if self.original is None:
            return
        t = self.v_thresh.get()
        self.processed = threshold(self.original, t)
        self._refresh(tx=f"Threshold  T={int(t)}  (binary)")

    def _apply_histogram_eq(self):
        if self.original is None:
            return
        self.processed = histogram_equalization(self.original)
        self._refresh(tx="Histogram Equalization")

    def _reset(self):
        if self.original is None:
            return
        self.processed = self.original.copy()
        self._reset_sliders()
        self._refresh(tx="Original")


    def _compare(self):
        if self.original is None:
            messagebox.showwarning("No Image", "Open an image first.")
            return

        win = tk.Toplevel(self)
        win.title("Compare — Original vs Processed")
        win.configure(bg=BG)
        win.minsize(900, 600)

        # Images side by side
        img_row = tk.Frame(win, bg=BG)
        img_row.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        for arr, title, color in [
            (self.original,  "Original",  ACCENT),
            (self.processed, "Processed", PURPLE),
        ]:
            col = Card(img_row)
            col.pack(side="left", fill="both", expand=True, padx=6)

            hdr = tk.Frame(col, bg=color, height=28)
            hdr.pack(fill="x")
            hdr.pack_propagate(False)
            tk.Label(hdr, text=title, font=FONT_B, fg=WHITE, bg=color).pack(pady=4)
            ph = self._to_photo(arr, 400, 300)
            lbl = tk.Label(col, image=ph, bg="#F2F2FA")
            lbl.image = ph
            lbl.pack(padx=10, pady=10)

        hist_card = Card(win)
        hist_card.pack(fill="x", padx=22, pady=(0, 16))
        hdr2 = tk.Frame(hist_card, bg=GRAY, height=28)
        hdr2.pack(fill="x")
        hdr2.pack_propagate(False)
        tk.Label(hdr2, text="Histograms — Original vs Processed",
                 font=FONT_B, fg=WHITE, bg=GRAY).pack(side="left", padx=12, pady=4)
        fig = Figure(figsize=(9, 2.2), dpi=90, facecolor=WHITE)
        ax1 = fig.add_subplot(121)
        ax1.fill_between(range(256), compute_histogram(self.original), color=ACCENT, alpha=0.7)
        ax1.set_title("Histogram — Original", fontsize=9, color=TEXT)
        ax1.set_xlim(0, 255)
        ax1.tick_params(labelsize=7)
        ax1.spines[["top", "right"]].set_visible(False)
        ax2 = fig.add_subplot(122)
        ax2.fill_between(range(256), compute_histogram(self.processed), color=PURPLE, alpha=0.7)
        ax2.set_title("Histogram — Processed", fontsize=9, color=TEXT)
        ax2.set_xlim(0, 255)
        ax2.tick_params(labelsize=7)
        ax2.spines[["top", "right"]].set_visible(False)
        fig.tight_layout(pad=2.0)
        c = FigureCanvasTkAgg(fig, master=hist_card)
        c.get_tk_widget().pack(padx=10, pady=(6, 10))
        c.draw()
        
    def _refresh(self, tx=""):
        if tx:
            self.lbl_tx.config(text=tx)

        if self.original is not None:
            ph = self._to_photo(self.original)
            self.lbl_original.config(image=ph, text="")
            self.lbl_original.image = ph

        if self.processed is not None:
            ph = self._to_photo(self.processed)
            self.lbl_processed.config(image=ph, text="")
            self.lbl_processed.image = ph

        self._update_histogram()

    def _update_histogram(self):
        if self.processed is None:
            return

        H   = compute_histogram(self.processed)
        cdf = compute_cdf(self.processed)

        self.ax_hist.cla()
        self.ax_hist.fill_between(range(256), H, color=ACCENT, alpha=0.7)
        self.ax_hist.set_title("Histogram — Processed Image", fontsize=9, color=TEXT)
        self.ax_hist.set_xlim(0, 255)
        self.ax_hist.tick_params(labelsize=8)
        self.ax_hist.spines[["top", "right"]].set_visible(False)

        self.ax_cdf.cla()
        self.ax_cdf.plot(cdf, color=PINK, linewidth=1.5)
        self.ax_cdf.fill_between(range(256), cdf, color=PINK, alpha=0.15)
        self.ax_cdf.set_title("CDF — Processed Image", fontsize=9, color=TEXT)
        self.ax_cdf.set_xlim(0, 255)
        self.ax_cdf.tick_params(labelsize=8)
        self.ax_cdf.spines[["top", "right"]].set_visible(False)

        self.fig.tight_layout(pad=2.5)
        self.canvas_hist.draw()

    def _draw_placeholder_histogram(self):
        for ax, title in [
            (self.ax_hist, "Histogram — Processed Image"),
            (self.ax_cdf,  "CDF — Processed Image"),
        ]:
            ax.set_facecolor("#F5F5FA")
            ax.set_title(title, fontsize=8, color=SUBTEXT)
            ax.tick_params(labelsize=7)
            ax.spines[["top", "right"]].set_visible(False)
        self.canvas_hist.draw()

    def _to_photo(self, arr, max_w=430, max_h=360):
        img = Image.fromarray(arr.astype(np.uint8))
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def _reset_sliders(self):
        self.v_bright.set(0)
        self.v_alpha.set(1.0)
        self.v_lc_beta.set(0)
        self.v_thresh.set(128)
        self.e_fmin.delete(0, -1)
        self.e_fmax.delete(0, -1)

if __name__ == "__main__":
    app = App()
    app.mainloop()