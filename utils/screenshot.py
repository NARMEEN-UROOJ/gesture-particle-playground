# ============================================================
#  screenshot.py — Press S to save current frame as PNG
# ============================================================

import cv2
import os
from datetime import datetime
from config import SCREENSHOT_DIR


def save_screenshot(canvas):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(SCREENSHOT_DIR, f"capture_{stamp}.png")
    cv2.imwrite(filepath, canvas)
    print(f"[SCREENSHOT] Saved → {filepath}")
    return filepath