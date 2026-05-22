# ============================================================
#  physics.py  — Recalibrated forces
#  Formula: direction * strength / (distance + softener)
#  Gives ~1.0 force at 200px — clearly visible on balls
# ============================================================

import numpy as np
from config import (
    ATTRACTION_STRENGTH, REPULSION_STRENGTH, ORBIT_STRENGTH,
    TWO_HAND_COMPRESS_MAX, TWO_HAND_EXPAND_MIN
)
def __init__(self):
        self.force_mult = 1.0 

class Physics:

    # ----------------------------------------------------------
    @staticmethod
    def _vectors(pos, center):
        """
        Returns (unit_dir, dist) from every ball toward center.
        unit_dir : (N, 2) — normalised direction vectors
        dist     : (N, 1) — scalar distances, min-clamped at 20px
        """
        diff     = np.array(center, dtype=float) - pos      # (N,2)
        dist     = np.linalg.norm(diff, axis=1, keepdims=True)  # (N,1)
        dist     = np.maximum(dist, 20.0)
        unit_dir = diff / dist                               # (N,2)
        return unit_dir, dist

    # ----------------------------------------------------------
    def attraction(self, pos, center, strength=None):
        """Gravity well — pull balls toward hand center"""
        s = (strength or ATTRACTION_STRENGTH) * self.force_mult
        unit_dir, dist = self._vectors(pos, center)
        # Force falls off with distance but stays strong enough to feel
        magnitude = s / (dist + 100)                         # (N,1)
        return unit_dir * magnitude                          # (N,2)

    # ----------------------------------------------------------
    def repulsion(self, pos, center, strength=None):
        """Explosion — push balls away from hand center"""
        s = (strength or REPULSION_STRENGTH) * self.force_mult
        unit_dir, dist = self._vectors(pos, center)
        magnitude      = s / (dist + 80)
        return -unit_dir * magnitude                         # reversed

    # ----------------------------------------------------------
    def orbit(self, pos, center, strength=None):
        """
        Swirl — tangential force makes balls circle around center.
        Tiny inward pull keeps them from spiralling out.
        """
        s = (strength or ORBIT_STRENGTH) * self.force_mult
        unit_dir, dist = self._vectors(pos, center)

        # Perpendicular = rotate unit_dir 90°
        tangent    = np.column_stack([-unit_dir[:, 1], unit_dir[:, 0]])

        tangential = s       * tangent   / (dist + 60)
        inward     = 0.25 * s * unit_dir / (dist + 80)

        return tangential + inward

    # ----------------------------------------------------------
    def two_hand_force(self, pos, c1, c2, inter_dist):
        """
        Two hands close  → compress balls toward midpoint
        Two hands far    → expand balls from midpoint
        """
        mid = ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2)

        if inter_dist < TWO_HAND_COMPRESS_MAX:
            t  = 1.0 - inter_dist / TWO_HAND_COMPRESS_MAX
            return self.attraction(pos, mid, ATTRACTION_STRENGTH * t * 3)

        elif inter_dist > TWO_HAND_EXPAND_MIN:
            t  = min((inter_dist - TWO_HAND_EXPAND_MIN) / 200, 1.0)
            return self.repulsion(pos, mid, REPULSION_STRENGTH * t)

        return np.zeros_like(pos)

    # ----------------------------------------------------------
    def velocity_push(self, pos, center, hand_vel, threshold=5.0):
        """Fast hand movement shoves nearby balls in motion direction"""
        speed = np.linalg.norm(hand_vel)
        if speed < threshold:
            return np.zeros_like(pos)

        diff = np.array(center) - pos
        dist = np.linalg.norm(diff, axis=1)

        force        = np.zeros_like(pos)
        nearby       = dist < 150
        force[nearby] = np.array(hand_vel) * 0.2
        return force
    # ----------------------------------------------------------
    def pulse_push(self, pos, center, radius,
                   ring_width=45, strength=6.0):
        """
        Push balls outward when the pulse ring sweeps past them.
        Only balls within ring_width px of the current radius are affected.
        """
        diff = pos - np.array(center, float)
        dist = np.linalg.norm(diff, axis=1)

        on_ring = np.abs(dist - radius) < ring_width
        force   = np.zeros_like(pos)

        if np.any(on_ring):
            d     = dist[on_ring]
            dirs  = diff[on_ring] / np.maximum(d[:, np.newaxis], 1.0)
            force[on_ring] = dirs * strength

        return force