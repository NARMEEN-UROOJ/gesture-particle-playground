# ============================================================
#  pulse.py — Clap shockwave effect
#  Trigger: inter-hand distance drops >70px in one frame
#  Effect:  expanding ring + outward force on balls in its path
# ============================================================

import cv2
import numpy as np
from config import PULSE_COLOR, PULSE_MAX_RADIUS, PULSE_SPEED, PULSE_THICKNESS


class PulseEffect:

    CLAP_THRESHOLD = 70   # px drop in one frame = clap

    def __init__(self):
        self.waves  = []          # [{x,y,radius}]
        self._prev  = None

    # ----------------------------------------------------------
    def check_and_trigger(self, hands_data):
        """Call every frame. Auto-detects clap from hand distance."""
        if len(hands_data) < 2:
            self._prev = None
            return

        dist = hands_data[0].get('inter_hand_dist', 9999)
        if self._prev is not None and (self._prev - dist) > self.CLAP_THRESHOLD:
            c1 = hands_data[0]['center']
            c2 = hands_data[1]['center']
            self.emit((c1[0]+c2[0])//2, (c1[1]+c2[1])//2)

        self._prev = dist

    # ----------------------------------------------------------
    def emit(self, x, y):
        """Spawn a pulse manually (e.g. for testing)"""
        self.waves.append({'x': x, 'y': y, 'radius': 8})

    # ----------------------------------------------------------
    def update(self, canvas, ps, physics):
        """
        Expand each wave, draw it, push balls at its frontier.
        Returns updated canvas.
        """
        alive = []
        for w in self.waves:
            w['radius'] += PULSE_SPEED
            r = w['radius']

            if r < PULSE_MAX_RADIUS:
                # Fade ring as it expands
                alpha = 1.0 - r / PULSE_MAX_RADIUS
                color = tuple(int(c * alpha) for c in PULSE_COLOR)

                # Outer glow ring
                cv2.circle(canvas, (w['x'], w['y']),
                           int(r + 6),
                           tuple(c // 3 for c in color),
                           PULSE_THICKNESS + 4, cv2.LINE_AA)
                # Sharp inner ring
                cv2.circle(canvas, (w['x'], w['y']),
                           int(r), color,
                           PULSE_THICKNESS, cv2.LINE_AA)

                # Push balls sitting on the ring frontier outward
                ps.apply_force(
                    physics.pulse_push(ps.pos, (w['x'], w['y']), r)
                )
                alive.append(w)

        self.waves = alive
        return canvas