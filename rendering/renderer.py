# ============================================================
#  renderer.py — Optimised trail fade + smaller blur kernel
# ============================================================

import cv2
import numpy as np
from config import GLOW_BLUR_SIZE, GLOW_STRENGTH, TRAIL_ALPHA


class Renderer:

    def __init__(self, width, height):
        self.width        = width
        self.height       = height
        self.trail_canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.trail_alpha  = TRAIL_ALPHA     # overridden by settings
        self.glow_kernel  = GLOW_BLUR_SIZE
    # ----------------------------------------------------------
    def fade_trails(self):
        self.trail_canvas = cv2.convertScaleAbs(
            self.trail_canvas, alpha=self.trail_alpha / 255.0
        )

    # ----------------------------------------------------------
    @staticmethod
    def _brightness(color, speed):
        t = min(speed / 8.0, 1.0)
        f = 0.5 + 0.5 * t
        return tuple(min(int(c * f), 255) for c in color)

    # ----------------------------------------------------------
    def draw_balls(self, ps):
        h, w   = self.height, self.width
        layer  = np.zeros((h, w, 3), dtype=np.uint8)
        pos    = ps.pos.astype(int)
        speeds = ps.speeds

        for i in range(ps.count):
            x, y = pos[i]
            if not (0 <= x < w and 0 <= y < h):
                continue

            r     = int(ps.radii[i])
            color = self._brightness(ps.colors[i], speeds[i])

            # Trail stamp
            cv2.circle(self.trail_canvas, (x, y), r,
                       ps.colors[i], -1, cv2.LINE_AA)

            # Outer dim halo
            cv2.circle(layer, (x, y), r + 4,
                       tuple(c // 4 for c in color), -1, cv2.LINE_AA)
            # Core
            cv2.circle(layer, (x, y), r, color, -1, cv2.LINE_AA)
            # Highlight
            if r >= 6:
                hl = tuple(min(c + 100, 255) for c in color)
                cv2.circle(layer, (x - r//3, y - r//3),
                           max(r//4, 2), hl, -1, cv2.LINE_AA)

        return layer

    # ----------------------------------------------------------
    def render_frame(self, ps, hands_data, tracker):
        self.fade_trails()
        ball_layer = self.draw_balls(ps)

        # Single blur pass — kernel 21 is noticeably faster than 31
        k    = int(self.glow_kernel) | 1      # force odd
        glow = cv2.GaussianBlur(ball_layer, (k, k), 0)

        canvas = self.trail_canvas.copy()
        canvas = cv2.addWeighted(canvas, 1.0, glow,       GLOW_STRENGTH, 0)
        canvas = cv2.addWeighted(canvas, 1.0, ball_layer, 1.0,           0)
        canvas = tracker.draw_skeleton(canvas, hands_data)
        return canvas