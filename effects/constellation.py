# ============================================================
#  constellation.py
#  Draws glowing lines between balls that are close together.
#  Fully vectorised — no Python loops over pairs.
#  Toggle ON/OFF with the X key.
# ============================================================

import cv2
import numpy as np


class Constellation:

    MAX_DIST = 130      # px — max distance a line appears
    MIN_PAIRS = 1       # skip draw call if no close pairs found

    def __init__(self):
        self.enabled = True

    def toggle(self):
        self.enabled = not self.enabled
        print(f"[CONSTELLATION] {'ON' if self.enabled else 'OFF'}")

    # ----------------------------------------------------------
    def draw(self, canvas, ps):
        if not self.enabled or ps.count < 2:
            return canvas

        pos = ps.pos          # (N, 2) float — no copy needed

        # ── Vectorised pairwise distances ─────────────────────
        # diff[i,j] = pos[i] - pos[j]
        diff  = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]  # (N,N,2)
        dists = np.linalg.norm(diff, axis=2)                   # (N,N)

        # Upper triangle only → avoids drawing each line twice
        close = np.triu((dists > 0) & (dists < self.MAX_DIST), k=1)
        pairs = np.argwhere(close)

        if len(pairs) < self.MIN_PAIRS:
            return canvas

        ipos = pos.astype(int)

        for i, j in pairs:
            d     = dists[i, j]
            # Non-linear fade: lines vanish quickly near MAX_DIST
            alpha = (1.0 - d / self.MAX_DIST) ** 2.0

            # Blend the two balls' colours at current alpha
            ci = ps.colors[i]
            cj = ps.colors[j]
            color = tuple(
                int(((ci[k] + cj[k]) / 2) * alpha)
                for k in range(3)
            )

            cv2.line(canvas,
                     (ipos[i][0], ipos[i][1]),
                     (ipos[j][0], ipos[j][1]),
                     color, 1, cv2.LINE_AA)

        return canvas