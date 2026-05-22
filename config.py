# ============================================================
#  config.py — Reworked for ball system + performance
# ============================================================

# --- Window ---
WINDOW_TITLE   = "Gesture Particle Playground"
WINDOW_WIDTH   = 1280
WINDOW_HEIGHT  = 720
TARGET_FPS     = 30

# --- Camera ---
CAMERA_INDEX   = 0

# --- Balls (replaces particle system) ---
BALL_COUNT      = 60       # visible glowing orbs
BALL_MIN_RADIUS = 8
BALL_MAX_RADIUS = 18
MAX_BALL_SPEED  = 14.0     # velocity cap — prevents fly-off
BALL_DAMPING    = 0.97
PINCH_SPAWN_COUNT = 3      # new balls per pinch frame

# --- Physics (recalibrated) ---
ATTRACTION_STRENGTH  = 300.0
REPULSION_STRENGTH   = 500.0
ORBIT_STRENGTH       = 260.0

# --- Gesture Thresholds ---
PINCH_DIST_THRESHOLD  = 0.05

# --- Two Hand Distance ---
TWO_HAND_COMPRESS_MAX = 200
TWO_HAND_EXPAND_MIN   = 400

# --- Visual ---
GLOW_BLUR_SIZE  = 21      # Gaussian kernel — must be ODD number
GLOW_STRENGTH   = 0.9
TRAIL_ALPHA     = 195      # lower = longer trails
PAINT_BRUSH_SIZE = 8  

# --- Hand skeleton ---
HAND_COLOR = (160, 160, 160)

# --- Pulse Effect ---
PULSE_MAX_RADIUS  = 380
PULSE_SPEED       = 14
PULSE_THICKNESS   = 3
PULSE_COLOR       = (60, 210, 255)

# --- Screenshot ---
SCREENSHOT_DIR = "screenshots"