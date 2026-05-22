# ============================================================
#  magnetic_trail.py
#  PEACE gesture leaves a path that physically attracts balls.
#
#  How it works:
#    • Fingertip positions are stored as (x, y, age) tuples
#    • Each frame: fully vectorised force from T trail points
#      to N balls — shape (T, N, 2), no Python loops
#    • Points age out over ~3 seconds and are removed
#    • Visual: cyan glow drawn UNDER the painter rainbow trail
# ============================================================

import cv2
import numpy as np


class MagneticTrail:

    MAX_POINTS      = 150     # older points are dropped
    AGE_PER_FRAME   = 0.004   # 1.0/0.004 = 250 frames ≈ 8s at 30fps
    ATTRACT_STRENGTH= 65.0
    DRAW_COLOR      = (220, 200, 50)   # cyan-ish (BGR)

    def __init__(self):
        self._pts  = []    # list of np.array([x, y])
        self._ages = []    # float 0.0 (fresh) → 1.0 (dead)

    # ----------------------------------------------------------
    def add_point(self, x, y):
        """Call every frame the PEACE gesture is active."""
        self._pts.append(np.array([x, y], dtype=float))
        self._ages.append(0.0)

        # Drop oldest if over cap
        if len(self._pts) > self.MAX_POINTS:
            self._pts.pop(0)
            self._ages.pop(0)

    # ----------------------------------------------------------
    def update(self):
        """Age all points. Call once per frame."""
        self._ages = [a + self.AGE_PER_FRAME for a in self._ages]

        # Remove fully-aged points
        valid = [(p, a) for p, a in zip(self._pts, self._ages) if a < 1.0]
        if valid:
            self._pts, self._ages = map(list, zip(*valid))
        else:
            self._pts, self._ages = [], []

    # ----------------------------------------------------------
    def get_force(self, ball_pos):
        """
        Returns (N, 2) attraction force toward all trail points.
        Vectorised: single numpy operation over (T, N, 2).
        """
        if not self._pts:
            return np.zeros_like(ball_pos)

        pts     = np.array(self._pts)              # (T, 2)
        weights = 1.0 - np.array(self._ages)       # (T,) 1=new, 0=old

        # diff[t, n, :] = pts[t] - ball_pos[n]
        diff = pts[:, np.newaxis, :] \
             - ball_pos[np.newaxis, :, :]          # (T, N, 2)
        dist = np.linalg.norm(diff, axis=2,
                              keepdims=True)       # (T, N, 1)
        dist = np.maximum(dist, 20.0)

        direction = diff / dist                    # (T, N, 2) unit vecs
        magnitude = (weights[:, np.newaxis, np.newaxis]
                     * self.ATTRACT_STRENGTH
                     / (dist + 90))               # (T, N, 1)

        return np.sum(direction * magnitude, axis=0)   # (N, 2)

    # ----------------------------------------------------------
    def draw(self, canvas):
        """
        Draws a faint glowing cyan underlay.
        Called BEFORE painter.draw() so rainbow sits on top.
        """
        if len(self._pts) < 2:
            return canvas

        for i in range(1, len(self._pts)):
            age   = self._ages[i]
            alpha = (1.0 - age) * 0.7
            color = tuple(int(c * alpha) for c in self.DRAW_COLOR)

            p1 = tuple(self._pts[i - 1].astype(int))
            p2 = tuple(self._pts[i].astype(int))

            cv2.line(canvas, p1, p2, color, 4, cv2.LINE_AA)  # thick glow
            cv2.line(canvas, p1, p2,                          # bright core
                     tuple(min(c + 60, 255) for c in color),
                     1, cv2.LINE_AA)

        return canvas

    # ----------------------------------------------------------
    def clear(self):
        self._pts, self._ages = [], []