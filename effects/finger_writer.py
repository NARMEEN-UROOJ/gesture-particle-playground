# ============================================================
#  finger_writer.py  — OPTION A: SAFE VERSION
#  (Fixed hand data key issues)
#
#  Design:
#    - OPEN_HAND (all fingers up)  = draw (natural, easy)
#    - FIST (closed hand)           = erase
#    - PINCH (thumb+index)          = cycle color
#    - W key                        = exit write mode
# ============================================================

import cv2
import numpy as np


class FingerWriter:

    # Vibrant 6-color palette (BGR format)
    PALETTE = [
        (  0, 255, 255),   # yellow  (bright, visible)
        (255,  50,  50),   # blue
        (200,   0, 255),   # magenta
        ( 50, 255,  50),   # green
        (255, 200,   0),   # cyan
        ( 50,  50, 255),   # red
    ]

    BRUSH_SIZE   = 8       # Thick, visible strokes
    ERASER_SIZE  = 45      # Big eraser circle

    def __init__(self, width, height):
        self.width  = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.active = False

        self._color_idx  = 0
        self._prev_pos   = {}       # hand idx → last drawn point
        self._pinch_held = {}       # debounce pinch color
        self._eraser_pos = {}       # hand idx → eraser cursor pos

    # ----------------------------------------------------------
    def toggle(self):
        self.active = not self.active
        if self.active:
            print("[WRITE] ON — Open hand=draw  Fist=erase  Pinch=next color  W=exit")
        else:
            print("[WRITE] OFF")

    # ----------------------------------------------------------
    @property
    def pen_color(self):
        return self.PALETTE[self._color_idx]

    # ----------------------------------------------------------
    def update(self, hands_data, gestures):
        """
        Process hand data for writing.
        Handles missing/invalid data gracefully.
        """
        if not self.active:
            return False

        if not hands_data or not gestures:
            return False

        seen = set()
        self._eraser_pos.clear()

        try:
            for idx, (hand, gesture) in enumerate(zip(hands_data, gestures)):
                seen.add(idx)
                
                # Get hand position — try multiple sources
                pos = None
                if isinstance(hand, dict):
                    # Try hand['center'] first (most reliable)
                    if 'center' in hand:
                        try:
                            pos = hand['center']
                        except:
                            pass
                    
                    # Fallback to fingertips['index']
                    if pos is None and 'fingertips' in hand:
                        try:
                            pos = hand['fingertips'].get('index')
                        except:
                            pass
                    
                    # Fallback to palm_center
                    if pos is None and 'palm_center' in hand:
                        try:
                            pos = hand['palm_center']
                        except:
                            pass
                
                # Skip if no valid position found
                if pos is None:
                    self._prev_pos.pop(idx, None)
                    self._pinch_held[idx] = False
                    continue
                
                # Ensure pos is tuple of ints
                try:
                    pos = (int(pos[0]), int(pos[1]))
                except (TypeError, ValueError, IndexError):
                    self._prev_pos.pop(idx, None)
                    self._pinch_held[idx] = False
                    continue

                # ── OPEN_HAND — draw ──────────────────────────────
                if gesture == 'OPEN_HAND':
                    prev = self._prev_pos.get(idx)

                    if prev is not None:
                        try:
                            dx = abs(pos[0] - prev[0])
                            dy = abs(pos[1] - prev[1])
                            dist = np.sqrt(dx*dx + dy*dy)

                            # Draw if moved but not a huge jump
                            if 1.0 < dist < 150:
                                cv2.line(self.canvas, prev, pos,
                                         self.pen_color, self.BRUSH_SIZE,
                                         cv2.LINE_AA)
                        except Exception as e:
                            print(f"[WRITE] Draw error: {e}")

                    self._prev_pos[idx]   = pos
                    self._pinch_held[idx] = False

                # ── FIST — erase ──────────────────────────────────
                elif gesture == 'FIST':
                    try:
                        cv2.circle(self.canvas, pos,
                                   self.ERASER_SIZE, (0, 0, 0), -1, cv2.LINE_AA)
                        self._eraser_pos[idx] = pos
                    except Exception as e:
                        print(f"[WRITE] Erase error: {e}")
                    
                    self._prev_pos.pop(idx, None)
                    self._pinch_held[idx] = False

                # ── PINCH — cycle color (debounced) ───────────────
                elif gesture == 'PINCH':
                    if not self._pinch_held.get(idx, False):
                        self._color_idx = (self._color_idx + 1) % len(self.PALETTE)
                        self._pinch_held[idx] = True
                        print(f"[WRITE] Color {self._color_idx + 1}/{len(self.PALETTE)}")
                    self._prev_pos.pop(idx, None)

                # ── Any other gesture — pen lifted ─────────────────
                else:
                    self._prev_pos.pop(idx, None)
                    self._pinch_held[idx] = False

            # Clean stale hand state
            for idx in list(self._prev_pos.keys()):
                if idx not in seen:
                    self._prev_pos.pop(idx, None)
                    self._pinch_held.pop(idx, None)

        except Exception as e:
            print(f"[WRITE] Update error: {e}")
            return False

        return True

    # ----------------------------------------------------------
    def draw(self, canvas):
        """
        Composite writing canvas onto main canvas.
        100% opaque — bold, visible strokes.
        """
        if not np.any(self.canvas):
            return canvas

        try:
            mask = np.any(self.canvas > 0, axis=2)
            result = canvas.copy()
            # 95% canvas, 5% background = very opaque
            result[mask] = cv2.addWeighted(
                self.canvas, 0.95, canvas, 0.05, 0
            )[mask]
            return result
        except Exception as e:
            print(f"[WRITE] Draw composite error: {e}")
            return canvas

    # ----------------------------------------------------------
    def draw_ui(self, canvas):
        """
        Minimal, clean UI on display canvas.
        """
        if not self.active:
            return canvas

        try:
            h, w = canvas.shape[:2]

            # ── Eraser cursor (circle + crosshair) ─────────────────
            for pos in self._eraser_pos.values():
                try:
                    cv2.circle(canvas, pos, self.ERASER_SIZE,
                               (180, 180, 180), 2, cv2.LINE_AA)
                    sz = 12
                    cv2.line(canvas, (pos[0] - sz, pos[1]), (pos[0] + sz, pos[1]),
                             (180, 180, 180), 1, cv2.LINE_AA)
                    cv2.line(canvas, (pos[0], pos[1] - sz), (pos[0], pos[1] + sz),
                             (180, 180, 180), 1, cv2.LINE_AA)
                except:
                    pass

            # ── Title: WRITE MODE ──────────────────────────────────
            title = "  WRITE MODE  "
            font = cv2.FONT_HERSHEY_SIMPLEX
            (tw, _), _ = cv2.getTextSize(title, font, 0.7, 2)
            tx = w // 2 - tw // 2
            ty = 35

            cv2.rectangle(canvas, (tx - 10, 8), (tx + tw + 10, 50),
                          (10, 10, 10), -1)
            cv2.rectangle(canvas, (tx - 10, 8), (tx + tw + 10, 50),
                          self.pen_color, 2, cv2.LINE_AA)
            cv2.putText(canvas, title, (tx, ty), font, 0.7,
                        self.pen_color, 2, cv2.LINE_AA)

            # ── Color palette — bottom ─────────────────────────────
            swatch = 28
            gap = 6
            n = len(self.PALETTE)
            total_w = n * (swatch + gap) - gap
            sx = w // 2 - total_w // 2
            sy = h - 80

            cv2.rectangle(canvas, (sx - 10, sy - 8),
                          (sx + total_w + 10, sy + swatch + 8),
                          (10, 10, 10), -1)

            for i, col in enumerate(self.PALETTE):
                x = sx + i * (swatch + gap)
                cv2.rectangle(canvas, (x, sy), (x + swatch, sy + swatch), col, -1)

                if i == self._color_idx:
                    cv2.rectangle(canvas,
                                  (x - 4, sy - 4),
                                  (x + swatch + 4, sy + swatch + 4),
                                  (255, 255, 255), 3, cv2.LINE_AA)

            # ── Instructions (bottom) ──────────────────────────────
            hint = "OPEN HAND = draw    FIST = erase    PINCH = color    W = close"
            (hh, _), _ = cv2.getTextSize(hint, font, 0.4, 1)
            cv2.putText(canvas, hint,
                        (w // 2 - hh // 2, h - 10),
                        font, 0.4, (100, 100, 100), 1, cv2.LINE_AA)

        except Exception as e:
            print(f"[WRITE] UI error: {e}")

        return canvas

    # ----------------------------------------------------------
    def clear(self):
        """Clear the canvas completely."""
        self.canvas[:] = 0
        self._prev_pos.clear()