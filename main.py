# ============================================================
#  main.py — CORRECTED FINAL VERSION
#
#  All features:
#    Gestures  : ATTRACT · EXPLODE · PAINT · FLOCK
#                FROZEN · GALAXY · PULSE · SPAWN · WRITE
#    Effects   : Constellation · Galaxy rings · Painter
#                Finger writer · Pulse shockwave
#    Physics   : Attraction · Repulsion · Orbit · Boids
#                Two-hand compress/expand · Velocity push
#                Ball merging
#    Settings  : Force · Ball count · Trail · Glow (live)
#
#  Keys:
#    Q  quit        S  screenshot    R  reset balls
#    C  clear all   X  constellation  P  settings
#    W  write mode toggle
# ============================================================

import cv2
import numpy as np
import time

from config                   import *
from core.camera_thread        import CameraThread
from core.hand_tracker         import HandTracker
from core.gesture_detector     import GestureDetector
from core.particle_system      import ParticleSystem
from core.physics              import Physics
from rendering.renderer        import Renderer
from rendering.ui              import UI
from rendering.settings_panel  import SettingsPanel
from utils.screenshot          import save_screenshot
from effects.pulse             import PulseEffect
from effects.galaxy            import GalaxyEffect
from effects.painter           import Painter
from effects.constellation     import Constellation
from effects.flock             import Flock
from effects.finger_writer     import FingerWriter
# FIX 1: MagneticTrail removed — was never instantiated but was still
#         referenced in 3 places (mag_trail.update / draw / clear)


# ── Helpers ───────────────────────────────────────────────────

def resolve_mode(gestures):
    if not gestures:
        return 'IDLE'
    if len(gestures) == 2:
        if all(g == 'FIST' for g in gestures):
            return 'FROZEN'
        return 'GALAXY'
    g = gestures[0]
    if g == 'OPEN_HAND': return 'ATTRACT'
    if g == 'FIST':      return 'EXPLODE'
    if g == 'PEACE':     return 'PAINT'
    if g == 'POINT':     return 'FLOCK'
    return 'IDLE'


class VelocityTracker:
    def __init__(self):
        self._prev = {}

    def update(self, idx, center):
        prev = self._prev.get(idx, center)
        self._prev[idx] = center
        return (center[0] - prev[0], center[1] - prev[1])

    def clear(self):
        self._prev.clear()


# ── Main ──────────────────────────────────────────────────────

def main():
    # ── Systems ───────────────────────────────────────────────
    cam       = CameraThread(CAMERA_INDEX, WINDOW_WIDTH, WINDOW_HEIGHT)
    tracker   = HandTracker()
    detector  = GestureDetector()
    ps        = ParticleSystem(WINDOW_WIDTH, WINDOW_HEIGHT)
    physics   = Physics()
    renderer  = Renderer(WINDOW_WIDTH, WINDOW_HEIGHT)
    ui        = UI()
    vel_track = VelocityTracker()
    settings  = SettingsPanel(WINDOW_WIDTH, WINDOW_HEIGHT)

    # ── Effects ───────────────────────────────────────────────
    pulse_fx      = PulseEffect()
    galaxy_fx     = GalaxyEffect()
    painter       = Painter(WINDOW_WIDTH, WINDOW_HEIGHT)
    constellation = Constellation()
    flock         = Flock()
    writer        = FingerWriter(WINDOW_WIDTH, WINDOW_HEIGHT)

    if not cam.is_opened():
        print("[ERROR] Camera not found — try CAMERA_INDEX=1 in config.py")
        return

    cv2.namedWindow(WINDOW_TITLE)
    cv2.setMouseCallback(WINDOW_TITLE, settings.mouse_callback)

    frame_delay  = int(1000 / TARGET_FPS)
    orbit_center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    prev_mode    = 'IDLE'
    frame_n      = 0

    print("[INFO] Ready.")
    print("[INFO] Q=quit  S=screenshot  R=reset  C=clear  X=lines  P=settings  W=write")

    while True:
        ret, frame = cam.read()
        if not ret or frame is None:
            time.sleep(0.001)
            continue

        frame  = cv2.flip(frame, 1)
        h, w   = frame.shape[:2]
        frame_n += 1

        # ── 1. Apply live settings ────────────────────────────
        physics.force_mult   = settings.values['force'] / 300.0
        renderer.trail_alpha = settings.values['trail']
        renderer.glow_kernel = settings.values['glow']

        target_balls = settings.values['balls']
        if frame_n % 20 == 0:
            if ps.count < target_balls:
                rx = int(np.random.randint(80, WINDOW_WIDTH  - 80))
                ry = int(np.random.randint(80, WINDOW_HEIGHT - 80))
                ps.add_balls(rx, ry, min(4, target_balls - ps.count))
            elif ps.count > target_balls + 5:
                ps.set_count(target_balls)

        # ── 2. Track hands + gestures ─────────────────────────
        results    = tracker.process(frame)
        hands_data = tracker.extract_hand_data(results, w, h)
        gestures   = [detector.detect(hd, w, h) for hd in hands_data]
        mode       = resolve_mode(gestures)

        # ── 3. Freeze state machine ───────────────────────────
        # OPTION A: Also freeze when in write mode (balls don't interfere)
        if mode == 'FROZEN' or writer.active:
            ps.freeze()
        elif ps.is_frozen:
            ps.unfreeze()

        # ── 4. Pulse — clap detection ─────────────────────────
        pulse_fx.check_and_trigger(hands_data)

        # ── 5. Write mode OR physics (mutually exclusive) ─────
        # FIX 2: writer.update() moved OUT of is_frozen guard so
        #         you can write even while balls are frozen.
        # FIX 3: painter.update() called ONCE, only in the else
        #         branch — was previously called twice.
        if writer.active:
            writer.update(hands_data, gestures)
            mode = 'WRITE'          # override mode for UI badge

        else:
            # Normal physics — skip while frozen
            if not ps.is_frozen:

                if mode == 'GALAXY' and len(hands_data) == 2:
                    c1 = hands_data[0]['center']
                    c2 = hands_data[1]['center']
                    orbit_center = (
                        (c1[0] + c2[0]) // 2,
                        (c1[1] + c2[1]) // 2,
                    )
                    ps.apply_force(physics.orbit(ps.pos, orbit_center))
                    if 'inter_hand_dist' in hands_data[0]:
                        ps.apply_force(physics.two_hand_force(
                            ps.pos, c1, c2,
                            hands_data[0]['inter_hand_dist']
                        ))

                elif mode == 'FLOCK':
                    ps.apply_force(flock.compute(ps))
                    for hand in hands_data:
                        ps.apply_force(
                            physics.attraction(
                                ps.pos, hand['center'], strength=50
                            )
                        )

                else:
                    for idx, (hand, gesture) in enumerate(
                        zip(hands_data, gestures)
                    ):
                        cx, cy = hand['center']
                        hvel   = vel_track.update(idx, (cx, cy))

                        if mode == 'ATTRACT':
                            ps.apply_force(
                                physics.attraction(ps.pos, (cx, cy))
                            )
                            ps.apply_force(
                                physics.velocity_push(
                                    ps.pos, (cx, cy), hvel
                                )
                            )
                        elif mode == 'EXPLODE':
                            ps.apply_force(
                                physics.repulsion(ps.pos, (cx, cy))
                            )

                        if gesture == 'PINCH':
                            ps.add_balls(cx, cy, PINCH_SPAWN_COUNT)

            # Painter runs only when NOT in write mode (called once)
            painter.update(hands_data, gestures)

        if not hands_data:
            vel_track.clear()

        # ── 6. Ball merging (every 2 frames) ──────────────────
        if frame_n % 2 == 0:
            ps.merge_check()

        # ── 7. Physics step ───────────────────────────────────
        ps.update()

        # ── 8. Render base frame ──────────────────────────────
        canvas = renderer.render_frame(ps, hands_data, tracker)

        # ── 9. Effect overlays (order matters) ────────────────
        canvas = constellation.draw(canvas, ps)   # deepest layer
        canvas = writer.draw(canvas)              # FIX 4: was missing
        canvas = painter.draw(canvas)             # painter on top of writer
        canvas = pulse_fx.update(canvas, ps, physics)
        canvas = galaxy_fx.draw(canvas, orbit_center, mode)
        canvas = writer.draw_ui(canvas)           # FIX 4: palette/badge on top

        # Frozen: faint blue tint
        if ps.is_frozen:
            tint       = np.zeros_like(canvas)
            tint[:, :] = (40, 20, 0)
            canvas     = cv2.addWeighted(canvas, 0.92, tint, 0.08, 0)

        # ── 10. UI + settings panel ───────────────────────────
        fps    = ui.tick_fps()
        canvas = ui.draw(canvas, mode, fps)
        canvas = settings.draw(canvas)

        if mode != prev_mode:
            print(f"[MODE] {prev_mode} → {mode}")
            prev_mode = mode

        cv2.imshow(WINDOW_TITLE, canvas)

        # ── 11. Keys ──────────────────────────────────────────
        key = cv2.waitKey(frame_delay) & 0xFF
        if   key == ord('q'): break
        elif key == ord('s'): save_screenshot(canvas)
        elif key == ord('r'):
            ps.__init__(WINDOW_WIDTH, WINDOW_HEIGHT)
            renderer.trail_canvas[:] = 0
            print("[INFO] Balls reset.")
        elif key == ord('c'):
            painter.clear()
            writer.clear()                # FIX 6: was missing
            renderer.trail_canvas[:] = 0
            print("[INFO] Canvas cleared.")
        elif key == ord('x'): constellation.toggle()
        elif key == ord('p'): settings.toggle()
        elif key == ord('w'): writer.toggle()   # FIX 5: was missing entirely

    cam.release()
    tracker.release()
    cv2.destroyAllWindows()
    print("[INFO] Closed.")


if __name__ == "__main__":
    main()