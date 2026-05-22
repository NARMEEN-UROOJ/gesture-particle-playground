# ============================================================
#  painter.py — Air-painting in PEACE gesture mode
#  Index fingertip leaves a rainbow trail that fades slowly
# ============================================================

import cv2
import numpy as np
from config import PAINT_BRUSH_SIZE


class Painter:

    def __init__(self, width, height):
        self.canvas     = np.zeros((height, width, 3), dtype=np.uint8)
        self._hue       = 0
        self._prev_pos  = {}    # per hand index → last tip position

    # ----------------------------------------------------------
    def update(self, hands_data, gestures):
        """Draw trail at index fingertip when gesture == PEACE"""
        for idx, (hand, gesture) in enumerate(zip(hands_data, gestures)):
            if gesture == 'PEACE':
                tip   = hand['fingertips']['index']
                color = self._hue_to_bgr(self._hue)
                prev  = self._prev_pos.get(idx)

                if prev:
                    cv2.line(self.canvas, prev, tip,
                             color, PAINT_BRUSH_SIZE, cv2.LINE_AA)
                    # Bright dot at tip for marker feel
                    cv2.circle(self.canvas, tip,
                               PAINT_BRUSH_SIZE // 2 + 2,
                               tuple(min(c+80, 255) for c in color),
                               -1, cv2.LINE_AA)
                else:
                    cv2.circle(self.canvas, tip,
                               PAINT_BRUSH_SIZE, color, -1)

                self._prev_pos[idx] = tip
                self._hue = (self._hue + 2) % 180

            else:
                self._prev_pos.pop(idx, None)

        # Very slow fade so paintings persist nicely
        self.canvas = cv2.convertScaleAbs(self.canvas, alpha=0.995)

    # ----------------------------------------------------------
    def draw(self, canvas):
        """Overlay paint layer onto main canvas"""
        mask = np.any(self.canvas > 0, axis=2)
        if not np.any(mask):
            return canvas
        return cv2.addWeighted(canvas, 1.0, self.canvas, 0.88, 0)

    # ----------------------------------------------------------
    def clear(self):
        self.canvas[:] = 0

    # ----------------------------------------------------------
    @staticmethod
    def _hue_to_bgr(hue):
        hsv = np.uint8([[[hue, 240, 255]]])
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
        return tuple(int(x) for x in bgr)