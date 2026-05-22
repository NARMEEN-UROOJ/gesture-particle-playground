# ============================================================
#  ui.py
#  Mode badge, FPS counter, control hints overlay
# ============================================================

import cv2
import time


MODE_COLORS = {
    'ATTRACT'  : (255, 180,  50),
    'EXPLODE'  : ( 40, 100, 255),
    'PAINT'    : ( 50, 230, 120),
    'GALAXY'   : (200,  60, 255),
    'IDLE'     : (130, 130, 130),
    'FROZEN'   : (200, 230, 255),   
    'FLOCK'    : ( 80, 255, 180),
    'WRITE'   : (255, 255, 255),
}

CONTROLS = [
    "Q — quit",
    "S — screenshot",
    "R — reset particles",
]


class UI:

    def __init__(self):
        self._tick_times = []

    # ----------------------------------------------------------
    def tick_fps(self):
        """Call once per frame. Returns current FPS."""
        now = time.time()
        self._tick_times.append(now)
        self._tick_times = [t for t in self._tick_times if now - t < 1.0]
        return len(self._tick_times)

    # ----------------------------------------------------------
    def draw(self, canvas, mode, fps):
        h, w   = canvas.shape[:2]
        color  = MODE_COLORS.get(mode, (180, 180, 180))

        # ── Mode badge (top-left) ──────────────────────────────
        label = f"  {mode}  "
        (lw, lh), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2
        )
        cv2.rectangle(canvas, (10, 10), (10 + lw + 10, 50),
                      (15, 15, 15), -1)
        cv2.rectangle(canvas, (10, 10), (10 + lw + 10, 50),
                      color, 1)
        cv2.putText(canvas, label, (15, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)

        # ── FPS (top-right) ────────────────────────────────────
        fps_txt = f"FPS {fps:02d}"
        cv2.putText(canvas, fps_txt, (w - 100, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (90, 90, 90), 1, cv2.LINE_AA)

        # ── Controls (bottom-left) ────────────────────────────
        for i, hint in enumerate(CONTROLS):
            cv2.putText(canvas, hint,
                        (12, h - 12 - i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.38, (65, 65, 65), 1, cv2.LINE_AA)

        return canvas