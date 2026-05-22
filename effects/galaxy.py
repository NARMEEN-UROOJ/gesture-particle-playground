# ============================================================
#  galaxy.py — Visual overlay for GALAXY / orbit mode
#  Draws orbital rings and a glowing "black hole" at centre
# ============================================================

import cv2
import numpy as np


class GalaxyEffect:

    RINGS       = [70, 150, 250, 360]   # orbital ring radii
    RING_COLOR  = (55, 10, 75)          # dim purple  (BGR)
    CORE_COLORS = [                     # concentric glow layers
        (200, 80,  255),
        (130, 40,  200),
        ( 70, 10,  130),
    ]

    # ----------------------------------------------------------
    def draw(self, canvas, orbit_center, mode):
        if mode != 'GALAXY':
            return canvas

        cx, cy = int(orbit_center[0]), int(orbit_center[1])
        h, w   = canvas.shape[:2]
        if not (0 < cx < w and 0 < cy < h):
            return canvas

        # Faint orbital rings
        for r in self.RINGS:
            cv2.circle(canvas, (cx, cy), r,
                       self.RING_COLOR, 1, cv2.LINE_AA)

        # Glowing core (black hole)
        for radius, color in zip([18, 11, 5], self.CORE_COLORS):
            cv2.circle(canvas, (cx, cy), radius,
                       color, -1, cv2.LINE_AA)

        return canvas