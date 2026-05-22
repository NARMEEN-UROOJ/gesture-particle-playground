# 🌌 Gesture-Controlled Particle Playground


<p align="center">
  A real-time computer vision playground where your hands become physical forces.<br/>
  60 glowing balls, 7 gesture modes, live physics — all running on CPU.
</p>

---

> 📹 **Demo video** — *(coming soon — recording in progress)*

---

## ✨ Features

| Category | What's included |
|---|---|
| 🖐 **Hand Tracking** | Dual-hand detection via MediaPipe (threaded, non-blocking) |
| ⚛️ **Physics Engine** | Attraction · Repulsion · Orbital · Boids flocking · Two-hand compress/expand |
| 🎮 **7 Gesture Modes** | Open hand · Fist · Peace · Point · Pinch · Both hands · Clap |
| 🌟 **Visual Effects** | Glow (Gaussian blur) · Colour trails · Constellation lines · Galaxy rings · Pulse shockwave |
| 🎨 **Air Painting** | Rainbow trail follows your fingertip with magnetic physics attraction |
| ❄️ **Freeze Frame** | Hold both fists — balls pause mid-air, release to resume |
| 🐟 **Flock / Boids** | Classic separation · alignment · cohesion algorithm |
| 🔮 **Ball Merging** | Slow-colliding balls merge into one (momentum-conserving) |
| ⚙️ **Live Settings** | In-window sliders — force strength, ball count, trail length, glow |
| 📸 **Screenshot** | Press `S` to save any frame as PNG |

---

## 🎮 Gesture Guide

| Gesture | Hand shape | Mode |
|---|---|---|
| **Attract** | ✋ Open hand | Balls pulled toward your hand |
| **Explode** | ✊ Fist | Balls pushed away explosively |
| **Paint** | ✌️ Peace / V-sign | Rainbow magnetic trail |
| **Flock** | ☝️ One finger pointing | Boids algorithm — fish school effect |
| **Spawn** | 🤏 Pinch (hold) | New balls burst from fingertips |
| **Galaxy** | ✋✋ Both hands open | Balls orbit the midpoint |
| **Frozen** | ✊✊ Both fists | Freeze all motion mid-air |
| **Pulse** | 👏 Clap both hands | Shockwave ring pushes all balls outward |

---

## 🚀 Quick Start

### 1 — Clone the repo
```bash
git clone https://github.com/NARMEEN-UROOJ/gesture-particle-playground
cd gesture-particle-playground
```

### 2 — Create virtual environment (Python 3.10 required)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3.10 -m venv venv
source venv/bin/activate
```

### 3 — Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4 — Run
```bash
python main.py
```

> ⚠️ **Python 3.10.x is required.** MediaPipe does not support 3.12+.
> If your camera doesn't open, set `CAMERA_INDEX = 1` in `config.py`.

---

## ⌨️ Keyboard Controls

| Key | Action |
|---|---|
| `Q` | Quit |
| `S` | Save screenshot to `/screenshots` folder |
| `R` | Reset all balls to random positions |
| `C` | Clear paint trails and trail canvas |
| `X` | Toggle constellation lines on/off |
| `P` | Toggle live settings panel |

---

## ⚙️ Settings Panel

Press `P` in-game to open the overlay panel. Drag the sliders — changes apply **instantly** with no restart needed.

| Slider | Controls |
|---|---|
| Force Strength | How strongly hands attract / repel balls |
| Ball Count | Number of glowing balls (10 – 120) |
| Trail Length | How long motion trails persist |
| Glow Size | Gaussian blur kernel — tight dot or wide bloom |

---

## 🗂️ Project Structure

```
gesture_particle_playground/
│
├── main.py                     # Entry point
├── config.py                   # All tunable constants
├── requirements.txt
│
├── core/
│   ├── camera_thread.py        # Non-blocking camera reader
│   ├── hand_tracker.py         # MediaPipe (threaded, half-res)
│   ├── gesture_detector.py     # Classifies hand pose → gesture string
│   ├── particle_system.py      # Ball physics arrays (NumPy)
│   └── physics.py              # Force functions (attraction, orbit, boids…)
│
├── effects/
│   ├── constellation.py        # Distance-based connecting lines
│   ├── flock.py                # Boids: separation · alignment · cohesion
│   ├── galaxy.py               # Orbital ring overlay
│   ├── magnetic_trail.py       # PEACE gesture magnetic attractor path
│   ├── painter.py              # Rainbow air-painting trail
│   └── pulse.py                # Clap shockwave ring + outward force
│
├── rendering/
│   ├── renderer.py             # Ball drawing + Gaussian glow + trails
│   ├── settings_panel.py       # Live in-window slider overlay
│   └── ui.py                   # Mode badge, FPS counter, key hints
│
└── utils/
    └── screenshot.py           # S key → timestamped PNG
```

---

## 🛠️ Tech Stack

| Library | Version | Purpose |
|---|---|---|
| **OpenCV** | 4.9 | Camera capture, drawing, display |
| **MediaPipe** | 0.10 | Hand landmark detection |
| **NumPy** | 1.26 | Vectorised physics (zero Python loops over particles) |
| **Pillow** | 10.3 | Screenshot saving |
| **Python threading** | stdlib | Camera + MediaPipe run on background threads |

### Architecture highlights

- **Camera thread** — `cap.read()` runs in background; main loop never blocks waiting for a frame
- **MediaPipe thread** — inference runs in background at its own pace; main loop reads latest result instantly
- **All physics vectorised** — forces, collision detection, boids — all NumPy `(N,N,2)` operations; no Python loops over balls
- **Single blur pass** — one `cv2.GaussianBlur` on the whole frame replaces per-ball glow loops (key FPS win)

---

## 🔧 Configuration

Edit `config.py` to change defaults before running:

```python
BALL_COUNT      = 60      # starting number of balls
TARGET_FPS      = 30      # frame rate cap
CAMERA_INDEX    = 0       # change to 1 for external webcam
TRAIL_ALPHA     = 195     # lower = longer trails
GLOW_BLUR_SIZE  = 21      # higher = softer glow
ATTRACTION_STRENGTH = 300 # base force (scaled by settings panel)
```

---

## 📦 Requirements

```
opencv-python==4.9.0.80
mediapipe==0.10.11
numpy==1.26.4
Pillow==10.3.0
pygame==2.5.2
```

---

## 🤝 Contributing

Pull requests are welcome. To add a new gesture mode:

1. Add gesture string in `core/gesture_detector.py`
2. Map it to a mode in `resolve_mode()` in `main.py`
3. Add force logic in `core/physics.py`
4. Add colour to `MODE_COLORS` in `rendering/ui.py`

---


## 👤 Author

Built with Python, OpenCV and MediaPipe.  
If you found this useful or cool — ⭐ star the repo!