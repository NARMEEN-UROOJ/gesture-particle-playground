# ============================================================
#  camera_thread.py
#  Reads camera frames on a background thread so cap.read()
#  never blocks the main loop.
# ============================================================

import cv2
import threading


class CameraThread:

    def __init__(self, index, width, height):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)   # no stale frame lag

        self._frame   = None
        self._lock    = threading.Lock()
        self._stop    = False

        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ----------------------------------------------------------
    def _run(self):
        while not self._stop:
            ret, frame = self.cap.read()
            if ret:
                with self._lock:
                    self._frame = frame   # always keep latest only

    # ----------------------------------------------------------
    def read(self):
        """Returns (success, frame) instantly — never blocks."""
        with self._lock:
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    # ----------------------------------------------------------
    def is_opened(self):
        return self.cap.isOpened()

    def release(self):
        self._stop = True
        self._thread.join(timeout=1.0)
        self.cap.release()