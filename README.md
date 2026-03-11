# 🖼️ Image Processing Studio

A desktop application for grayscale image processing built with Python and Tkinter.  
All algorithms are implemented manually using **NumPy** — no OpenCV, no skimage shortcuts.

---

## 📁 Project Structure

```
├── app.py            # UI — Tkinter interface
├── processing.py     # Core algorithms (NumPy only)
└── requirements.txt  # Dependencies
```

---

## ⚙️ Installation

```bash
pip install -r requirements.txt
```

Then run:

```bash
python app.py
```

---

## 🧠 How It Works

The app is split into two clear layers:

- **`processing.py`** — pure functions that take NumPy arrays and return NumPy arrays. No UI logic, no imports from `app.py`.
- **`app.py`** — the Tkinter UI that calls those functions and displays the results. No algorithm logic lives here.

---

## 🔧 Processing Functions (`processing.py`)

| Function | Description |
|---|---|
| `load_image(path)` | Opens an image and converts it to grayscale (L mode) |
| `adjust_brightness(img, β)` | Adds β to every pixel, clips to [0, 255] |
| `linear_contrast(img, α, β)` | Applies `α × img + β`, clips to [0, 255] |
| `contrast_strech(img, f_min, f_max)` | Stretches pixel range to fill [0, 255] |
| `compute_histogram(img)` | Returns a 256-value list of pixel counts |
| `histogram_equalization(img)` | Returns the CDF (used as equalization lookup table) |
| `threshold(img, T)` | Returns a binary image — pixels are either **0** or **255** |

> **Note:** `np.histogram` is not used anywhere. Histogram is computed manually via list comprehension.

---

## 🖥️ UI Features (`app.py`)

### Controls Panel (left, scrollable)

| Control | Widget | Trigger |
|---|---|---|
| Brightness β ∈ [−150, +150] | Custom slider | Real-time |
| Linear contrast α ∈ [0.1, 3.0] | Custom slider | Real-time |
| Linear contrast β ∈ [−100, +100] | Custom slider | Real-time |
| Contrast stretch (f_min, f_max or Auto) | Entry + Button | On click |
| Threshold T ∈ [0, 255] | Custom slider + Button | On click |
| Histogram equalization | Button | On click |
| Reset to original | Button | On click |
| Compare side by side | Button | Opens popup |

### Image Panels (center)
- **Left** — Original grayscale image
- **Right** — Processed result, updates after every operation

### Histogram Panel (bottom)
- **Histogram of processed image** — pixel intensity distribution
- **CDF of processed image** — cumulative distribution function
- Both refresh automatically on every change

### Compare Popup
Opens a `Toplevel` window with:
- Original and processed images side by side
- Both histograms displayed below for direct comparison

### Status Bar (top)
Displays: `filename · width×height px · Grayscale · active transformation`

---

## 📦 Requirements

```
Pillow
numpy
matplotlib
```

See `requirements.txt` for pinned versions.

---

## 📌 Constraints & Rules

- `skimage.exposure`, `cv2.equalizeHist`, and any function performing the transformation directly are **forbidden**
- `np.histogram` is **forbidden** — histograms are computed manually
- Every algorithm is implemented from scratch using **NumPy only**
- The threshold output is always **binary**: each pixel is strictly `0` or `255`