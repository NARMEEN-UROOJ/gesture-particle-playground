# ============================================================
#  flock.py — Classic Boids algorithm
#  Three rules: Separation · Alignment · Cohesion
#  Fully vectorised with NumPy — zero Python loops over balls
# ============================================================

import numpy as np


class Flock:

    # Perception radius — considered a neighbour
    NEIGHBOR_DIST   = 110.0
    # Personal space — too close, push away
    SEPARATION_DIST =  42.0

    # Force strengths (tune here if behaviour feels off)
    SEP_STRENGTH     = 1.6    # avoid crowding
    ALIGN_STRENGTH   = 0.055  # match neighbour heading
    COHESION_STRENGTH= 0.007  # drift toward neighbour centre

    # ----------------------------------------------------------
    def compute(self, ps):
        """
        Returns (N, 2) force array for the whole flock.
        Call ps.apply_force(flock.compute(ps)) each frame.
        """
        pos = ps.pos   # (N, 2)
        vel = ps.vel   # (N, 2)
        n   = ps.count

        if n < 2:
            return np.zeros_like(pos)

        # ── Pairwise geometry ─────────────────────────────────
        # diff[i,j] = pos[i] - pos[j]  (vector FROM j TOWARD i)
        diff  = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]   # (N,N,2)
        dists = np.linalg.norm(diff, axis=2)                    # (N,N)
        np.fill_diagonal(dists, np.inf)                         # ignore self

        neighbor  = dists < self.NEIGHBOR_DIST    # (N,N) bool
        too_close = dists < self.SEPARATION_DIST  # (N,N) bool

        forces = np.zeros((n, 2))

        # ── Rule 1 — Separation ───────────────────────────────
        # Steer away from any ball inside personal space.
        # Weight by 1/dist so nearer balls push harder.
        safe_d  = np.where(too_close, np.maximum(dists, 0.1), 1.0)
        sep_w   = np.where(
            too_close[:, :, np.newaxis],
            diff / safe_d[:, :, np.newaxis],   # unit-ish direction away
            0.0
        )
        forces += np.sum(sep_w, axis=1) * self.SEP_STRENGTH

        # ── Rules 2 & 3 — Alignment + Cohesion ───────────────
        # Only applied to balls that actually have neighbours.
        n_count = np.sum(neighbor, axis=1, keepdims=True)       # (N,1)
        has_nbr = n_count.flatten() > 0

        if np.any(has_nbr):
            safe_n = np.maximum(n_count, 1).astype(float)

            # Alignment: steer toward average velocity of neighbours
            vel_sum  = (neighbor[:, :, np.newaxis]
                        * vel[np.newaxis, :, :]).sum(axis=1)    # (N,2)
            avg_vel  = vel_sum / safe_n
            align    = (avg_vel - vel) * self.ALIGN_STRENGTH
            align[~has_nbr] = 0
            forces  += align

            # Cohesion: steer toward average position of neighbours
            pos_sum  = (neighbor[:, :, np.newaxis]
                        * pos[np.newaxis, :, :]).sum(axis=1)    # (N,2)
            avg_pos  = pos_sum / safe_n
            cohesion = (avg_pos - pos) * self.COHESION_STRENGTH
            cohesion[~has_nbr] = 0
            forces  += cohesion

        return forces