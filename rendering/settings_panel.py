# ============================================================
#  settings_panel.py
#  In-window overlay panel with draggable sliders.
#  Toggle with P key.  Mouse drag adjusts values live.
#  Values flow directly into physics, renderer, ball count.
# ============================================================

import cv2
import numpy as np


class SettingsPanel:

    W   = 220     # panel width in pixels
    PAD = 15

    # All sliders defined here — add more any time
    SLIDERS = [
        {'label': 'Force Strength', 'key': 'force',
         'lo': 50,  'hi': 600, 'val': 300},
        {'label': 'Ball Count',     'key': 'balls',
         'lo': 10,  'hi': 120, 'val': 60 },
        {'label': 'Trail Length',   'key': 'trail',
         'lo': 150, 'hi': 253, 'val': 195},
        {'label': 'Glow Size',      'key': 'glow',
         'lo': 5,   'hi': 31,  'val': 21 },
    ]

    def __init__(self, canvas_w, canvas_h):
        self.visible  = False
        self.cw       = canvas_w
        self.panel_x  = canvas_w - self.W - 12
        self.values   = {s['key']: s['val'] for s in self.SLIDERS}
        self._active  = None     # index of slider being dragged

    # ----------------------------------------------------------
    def toggle(self):
        self.visible = not self.visible
        print(f"[SETTINGS] {'open' if self.visible else 'closed'}")

    # ----------------------------------------------------------
    def mouse_callback(self, event, x, y, flags, param):
        """Attach with cv2.setMouseCallback(WINDOW_TITLE, panel.mouse_callback)"""
        if not self.visible:
            return

        pressing = bool(flags & cv2.EVENT_FLAG_LBUTTON)

        if event == cv2.EVENT_LBUTTONDOWN or \
           (event == cv2.EVENT_MOUSEMOVE and pressing):
            self._try_set(x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            self._active = None

    # ----------------------------------------------------------
    def _track(self, idx):
        """Returns (x, y_centre, width) of slider track for index idx."""
        x = self.panel_x + self.PAD
        y = 70 + idx * 65 + 28
        w = self.W - self.PAD * 2
        return x, y, w

    def _try_set(self, mx, my):
        for idx, s in enumerate(self.SLIDERS):
            tx, ty, tw = self._track(idx)
            if tx <= mx <= tx + tw and ty - 10 <= my <= ty + 16:
                t         = max(0.0, min(1.0, (mx - tx) / tw))
                val       = int(s['lo'] + t * (s['hi'] - s['lo']))
                # Glow kernel must be odd
                if s['key'] == 'glow':
                    val = val | 1
                s['val']            = val
                self.values[s['key']] = val
                self._active        = idx
                break

    # ----------------------------------------------------------
    def draw(self, canvas):
        if not self.visible:
            return canvas

        h, w  = canvas.shape[:2]
        px    = self.panel_x
        ph    = 70 + len(self.SLIDERS) * 65 + 24

        # Semi-transparent background
        overlay = canvas.copy()
        cv2.rectangle(overlay, (px - 8, 8),
                      (w - 4, ph + 10), (12, 12, 12), -1)
        cv2.addWeighted(overlay, 0.84, canvas, 0.16, 0, canvas)

        # Border
        cv2.rectangle(canvas, (px - 8, 8),
                      (w - 4, ph + 10), (70, 70, 70), 1, cv2.LINE_AA)

        # Title
        cv2.putText(canvas, 'Settings   P to close',
                    (px, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48,
                    (170, 170, 170), 1, cv2.LINE_AA)
        cv2.line(canvas, (px - 4, 50),
                 (w - 8, 50), (50, 50, 50), 1)

        # Each slider
        for idx, s in enumerate(self.SLIDERS):
            tx, ty, tw = self._track(idx)
            t       = (s['val'] - s['lo']) / max(s['hi'] - s['lo'], 1)
            fill_w  = int(tw * t)
            hx      = tx + fill_w       # handle x position

            # Label
            cv2.putText(canvas, f"{s['label']}  {s['val']}",
                        (tx, ty - 9),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                        (140, 140, 140), 1, cv2.LINE_AA)

            # Track background
            cv2.rectangle(canvas,
                          (tx,          ty - 1),
                          (tx + tw,     ty + 7),
                          (38, 38, 38), -1)

            # Filled portion
            if fill_w > 0:
                cv2.rectangle(canvas,
                              (tx,        ty - 1),
                              (tx + fill_w, ty + 7),
                              (75, 175, 255), -1)

            # Handle circle
            cv2.circle(canvas, (hx, ty + 3), 7,
                       (155, 205, 255), -1, cv2.LINE_AA)
            cv2.circle(canvas, (hx, ty + 3), 7,
                       (75, 140, 200), 1,  cv2.LINE_AA)

        return canvas