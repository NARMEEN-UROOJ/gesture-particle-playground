# ============================================================
#  particle_system.py  — Ball edition
#  60 glowing orbs, each with unique vivid colour
#  NumPy arrays for all physics; Python loop only at draw time
# ============================================================

import cv2
import numpy as np
from config import (
    BALL_COUNT, BALL_MIN_RADIUS, BALL_MAX_RADIUS,
    BALL_DAMPING, MAX_BALL_SPEED
)


class ParticleSystem:

    MAX_BALLS = 120     # hard cap

    def __init__(self, width, height):
        self.width  = width
        self.height = height
        self._init_balls(BALL_COUNT)
        self._frozen     = False
        self._frozen_vel = None

    # ----------------------------------------------------------
    def _init_balls(self, n):
        # Positions — spread across canvas
        self.pos  = np.random.rand(n, 2) * [self.width, self.height]

        # Velocities — slow random drift
        angles    = np.random.rand(n) * 2 * np.pi
        speeds    = np.random.uniform(0.5, 2.0, n)
        self.vel  = np.column_stack([
            np.cos(angles) * speeds,
            np.sin(angles) * speeds,
        ])

        self.acc  = np.zeros((n, 2), dtype=np.float32)
        self.radii = np.random.randint(
            BALL_MIN_RADIUS, BALL_MAX_RADIUS + 1, n
        ).astype(float)

        # Unique vivid colour per ball — hues spread evenly around wheel
        # OpenCV HSV hue range: 0–179
        hues = np.linspace(0, 179, n, endpoint=False).astype(np.uint8)
        np.random.shuffle(hues)
        self.hues   = hues
        self.colors = [self._hue_to_bgr(h) for h in hues]

    # ----------------------------------------------------------
    @staticmethod
    def _hue_to_bgr(hue):
        """Convert a single HSV hue (full sat+val) → BGR tuple"""
        hsv = np.uint8([[[hue, 230, 255]]])
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
        return tuple(int(x) for x in bgr)

    # ----------------------------------------------------------
    def add_balls(self, x, y, count=3):
        """Pinch gesture spawns new balls near (x, y)"""
        if self.count >= self.MAX_BALLS:
            return
        count = min(count, self.MAX_BALLS - self.count)

        new_pos  = np.tile([x, y], (count, 1)) \
                 + np.random.randn(count, 2) * 35

        angles   = np.random.rand(count) * 2 * np.pi
        speeds   = np.random.uniform(2.0, 5.0, count)
        new_vel  = np.column_stack([
            np.cos(angles) * speeds,
            np.sin(angles) * speeds,
        ])

        new_radii  = np.random.randint(
            BALL_MIN_RADIUS, BALL_MAX_RADIUS + 1, count
        ).astype(float)
        new_hues   = np.random.randint(0, 180, count).astype(np.uint8)
        new_colors = [self._hue_to_bgr(h) for h in new_hues]

        self.pos    = np.vstack([self.pos,   new_pos])
        self.vel    = np.vstack([self.vel,   new_vel])
        self.acc    = np.vstack([self.acc,   np.zeros((count, 2))])
        self.radii  = np.concatenate([self.radii,  new_radii])
        self.hues   = np.concatenate([self.hues,   new_hues])
        self.colors = self.colors + new_colors

    # ----------------------------------------------------------
    def apply_force(self, force):
        self.acc += force

    # ----------------------------------------------------------
    def update(self):
        if self._frozen:
            self.vel[:] = 0    # keep clearing every frame (safety)
            self.acc[:] = 0
            return             # skip all physics

        self.vel += self.acc
        self.vel *= BALL_DAMPING

        # Velocity cap
        spds = np.linalg.norm(self.vel, axis=1)
        over = spds > MAX_BALL_SPEED
        if np.any(over):
            self.vel[over] *= (MAX_BALL_SPEED / spds[over])[:, np.newaxis]

        self.pos  += self.vel
        self.acc[:]= 0
        self._bounce()

    # ----------------------------------------------------------
    def _bounce(self):
        """Elastic bounce off all four edges"""
        l = self.pos[:, 0] < 0;          self.vel[l, 0] =  np.abs(self.vel[l, 0])
        r = self.pos[:, 0] > self.width;  self.vel[r, 0] = -np.abs(self.vel[r, 0])
        t = self.pos[:, 1] < 0;           self.vel[t, 1] =  np.abs(self.vel[t, 1])
        b = self.pos[:, 1] > self.height; self.vel[b, 1] = -np.abs(self.vel[b, 1])
        self.pos[:, 0] = np.clip(self.pos[:, 0], 0, self.width)
        self.pos[:, 1] = np.clip(self.pos[:, 1], 0, self.height)

    # ----------------------------------------------------------
    @property
    def count(self):
        return len(self.pos)

    @property
    def speeds(self):
        return np.linalg.norm(self.vel, axis=1)
    
    def freeze(self):
        """
        Pause all motion. Idempotent — safe to call every frame
        while the freeze gesture is held.
        """
        if not self._frozen:
            self._frozen_vel = self.vel.copy()
            self._frozen     = True
        self.vel[:] = 0
        self.acc[:] = 0

    def unfreeze(self):
        """Resume with the velocities that existed before freezing."""
        if self._frozen and self._frozen_vel is not None:
            self.vel      = self._frozen_vel.copy()
            self.acc[:] = 0
            self._frozen  = False

    @property
    def is_frozen(self):
        return self._frozen
    
    def merge_check(self, speed_threshold=3.5, max_radius=28):
        """
        Find colliding balls with low relative speed → merge them.
        Fully vectorised detection; Python loop only over matched pairs.
        Skipped while frozen (avoids array-size mismatch).
        """
        if self.is_frozen or self.count < 2:
            return

        # Pairwise distances
        diff  = self.pos[:, np.newaxis, :] - self.pos[np.newaxis, :, :]
        dists = np.linalg.norm(diff, axis=2)          # (N,N)
        np.fill_diagonal(dists, np.inf)

        r_sum     = self.radii[:, np.newaxis] + self.radii[np.newaxis, :]
        colliding = dists < r_sum * 0.85              # touching

        vel_diff  = self.vel[:, np.newaxis, :] \
                  - self.vel[np.newaxis, :, :]
        rel_spd   = np.linalg.norm(vel_diff, axis=2)

        # Upper-triangle to avoid processing each pair twice
        merge_mask = np.triu(colliding & (rel_spd < speed_threshold), k=1)
        pairs      = np.argwhere(merge_mask)

        if len(pairs) == 0:
            return

        to_remove = set()
        new_data  = []

        for i, j in pairs:
            if i in to_remove or j in to_remove:
                continue

            r1, r2    = self.radii[i], self.radii[j]
            new_r     = float(min(np.sqrt(r1**2 + r2**2), max_radius))

            # Conservation of momentum (mass ∝ area ∝ r²)
            m1, m2    = r1**2, r2**2
            tm        = m1 + m2
            new_pos   = (m1 * self.pos[i] + m2 * self.pos[j]) / tm
            new_vel   = (m1 * self.vel[i] + m2 * self.vel[j]) / tm

            # Blend colours in BGR space
            c1        = np.array(self.colors[i], float)
            c2        = np.array(self.colors[j], float)
            new_color = tuple(int(v) for v in ((c1 + c2) / 2))
            new_hue   = int((int(self.hues[i]) + int(self.hues[j])) / 2) % 180

            to_remove.update([i, j])
            new_data.append((new_pos, new_vel, new_r, new_hue, new_color))

        if not to_remove:
            return

        # Rebuild arrays without removed indices
        keep = [k for k in range(self.count) if k not in to_remove]

        if keep:
            self.pos    = self.pos[keep]
            self.vel    = self.vel[keep]
            self.acc    = self.acc[keep]
            self.radii  = self.radii[keep]
            self.hues   = self.hues[keep]
            self.colors = [self.colors[k] for k in keep]
        else:
            # All balls were merged — start fresh arrays
            self.pos    = np.empty((0, 2), float)
            self.vel    = np.empty((0, 2), float)
            self.acc    = np.empty((0, 2), float)
            self.radii  = np.array([], float)
            self.hues   = np.array([], np.uint8)
            self.colors = []

        # Append merged balls
        for pos, vel, r, hue, color in new_data:
            self.pos    = np.vstack([self.pos,   pos.reshape(1, 2)])
            self.vel    = np.vstack([self.vel,   vel.reshape(1, 2)])
            self.acc    = np.vstack([self.acc,   np.zeros((1, 2))])
            self.radii  = np.append(self.radii,  r)
            self.hues   = np.append(self.hues,   hue)
            self.colors.append(color)

    # ── New method: set_count ─────────────────────────────────
    def set_count(self, target):
        """
        Trim or flag to grow toward target. Called from settings loop.
        Removal is instant; addition happens gradually via add_balls.
        """
        if self.count > target + 5:
            n           = target
            self.pos    = self.pos[:n]
            self.vel    = self.vel[:n]
            self.acc    = self.acc[:n]
            self.radii  = self.radii[:n]
            self.hues   = self.hues[:n]
            self.colors = self.colors[:n]