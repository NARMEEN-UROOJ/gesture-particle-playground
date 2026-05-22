# ============================================================
#  gesture_detector.py — Relaxed pinch threshold
# ============================================================

import numpy as np
from config import PINCH_DIST_THRESHOLD


class GestureDetector:

    FINGERTIP_IDS  = [4,  8,  12, 16, 20]
    FINGER_PIP_IDS = [3,  6,  10, 14, 18]

    def detect(self, hand_data, frame_w, frame_h):
        lm = hand_data['landmarks']

        if self._is_pinch(lm, frame_w, frame_h):
            return 'PINCH'

        fingers_up = self._fingers_extended(lm)
        n          = sum(fingers_up)

        if n == 0:                                          return 'FIST'
        if n >= 4:                                          return 'OPEN_HAND'
        if fingers_up[1] and fingers_up[2] \
           and not fingers_up[3] and not fingers_up[4]:    return 'PEACE'
      
        # POINT: only index finger extended (all others curled)
        # Triggers FLOCK mode
        if (    fingers_up[1]
            and not fingers_up[2]
            and not fingers_up[3]
            and not fingers_up[4]):
            return 'POINT'

        return 'UNKNOWN'
       
    

    # ----------------------------------------------------------
    def _fingers_extended(self, lm):
        out = [lm[4][0] < lm[3][0]]   # thumb: horizontal
        for tip, pip in zip(self.FINGERTIP_IDS[1:], self.FINGER_PIP_IDS[1:]):
            out.append(lm[tip][1] < lm[pip][1])
        return out

    # ----------------------------------------------------------
    def _is_pinch(self, lm, frame_w, frame_h):
        """
        Two conditions must both pass:
        1. Thumb tip and index tip are close (distance check)
        2. Index PIP (mid-knuckle) is above index MCP (base knuckle)
           — this rules out fists where everything is curled down

        Threshold relaxed to 0.065 (was 0.05) for easier triggering
        """
        thumb = np.array(lm[4], float)
        index = np.array(lm[8], float)

        diag      = np.hypot(frame_w, frame_h)
        norm_dist = np.linalg.norm(thumb - index) / diag

        # lm[6]=index PIP,  lm[5]=index MCP
        # PIP must be above MCP (lower y) — +40px tolerance
        index_not_fisted = lm[6][1] < lm[5][1] + 40

        return norm_dist < 0.065 and index_not_fisted