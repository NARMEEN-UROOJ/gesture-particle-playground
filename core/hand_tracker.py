# ============================================================
#  hand_tracker.py — MediaPipe runs on background thread
#  Main loop submits a frame and gets the LATEST result
#  instantly without ever waiting ~50ms for MediaPipe.
# ============================================================

import time
import threading
import cv2
import numpy as np
import mediapipe as mp
from config import HAND_COLOR


class HandTracker:

    _PROC_W = 640
    _PROC_H = 360

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands    = self.mp_hands.Hands(
            static_image_mode        = False,
            max_num_hands            = 2,
            min_detection_confidence = 0.7,
            min_tracking_confidence  = 0.6,
            model_complexity         = 0,       # lite = fastest
        )

        self._pending  = None    # latest frame submitted by main loop
        self._result   = None    # latest processed result
        self._plock    = threading.Lock()   # guards _pending
        self._rlock    = threading.Lock()   # guards _result
        self._running  = True

        self._thread   = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    # ----------------------------------------------------------
    def _worker(self):
        """
        Background thread — processes frames as fast as it can.
        Always grabs the NEWEST pending frame (drops stale ones).
        """
        while self._running:
            # Pick up whatever frame is waiting
            with self._plock:
                frame          = self._pending
                self._pending  = None

            if frame is not None:
                small  = cv2.resize(frame, (self._PROC_W, self._PROC_H))
                rgb    = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                result = self.hands.process(rgb)
                with self._rlock:
                    self._result = result
            else:
                time.sleep(0.001)      # avoid busy-spinning when idle

    # ----------------------------------------------------------
    def process(self, frame):
        """
        Submit frame for background processing.
        Returns the latest result IMMEDIATELY (non-blocking).
        Result may be 1-2 frames old — imperceptible at 30 FPS.
        """
        with self._plock:
            self._pending = frame      # newest frame replaces any queued one

        with self._rlock:
            return self._result        # instant return

    # ----------------------------------------------------------
    def extract_hand_data(self, results, frame_w, frame_h):
        hands_data = []

        # Guard: result may be None on first frames
        if results is None or not results.multi_hand_landmarks:
            return hands_data

        for hand_lm in results.multi_hand_landmarks:
            landmarks = [
                (int(lm.x * frame_w), int(lm.y * frame_h))
                for lm in hand_lm.landmark
            ]

            fingertips = {
                'thumb' : landmarks[4],
                'index' : landmarks[8],
                'middle': landmarks[12],
                'ring'  : landmarks[16],
                'pinky' : landmarks[20],
            }

            xs     = [p[0] for p in landmarks]
            ys     = [p[1] for p in landmarks]
            center = (int(np.mean(xs)), int(np.mean(ys)))

            hands_data.append({
                'landmarks' : landmarks,
                'fingertips': fingertips,
                'center'    : center,
                'raw'       : hand_lm,
            })

        if len(hands_data) == 2:
            c1, c2 = hands_data[0]['center'], hands_data[1]['center']
            dist   = float(np.linalg.norm(
                np.array(c1, float) - np.array(c2, float)
            ))
            hands_data[0]['inter_hand_dist'] = dist
            hands_data[1]['inter_hand_dist'] = dist

        return hands_data

    # ----------------------------------------------------------
    def draw_skeleton(self, canvas, hands_data):
        if not hands_data:
            return canvas
        for hand in hands_data:
            lm = hand['landmarks']
            for s, e in self.mp_hands.HAND_CONNECTIONS:
                cv2.line(canvas, lm[s], lm[e], HAND_COLOR, 1, cv2.LINE_AA)
            for i, pt in enumerate(lm):
                r = 5 if i in (4, 8, 12, 16, 20) else 3
                cv2.circle(canvas, pt, r, HAND_COLOR, -1, cv2.LINE_AA)
        return canvas

    # ----------------------------------------------------------
    def release(self):
        self._running = False
        self._thread.join(timeout=2.0)
        self.hands.close()