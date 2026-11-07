import cv2
import math
import time
import pyautogui
from gesture_v3 import config
from gesture_v3.perception.tracker import HandTracker
from gesture_v3.perception.smoothing import OneEuroFilter
from gesture_v3.intent.classifier import GestureClassifier
from gesture_v3.control.mouse_physics import PhysicsCursor
from gesture_v3.ui.hud import CinematicHUD


class SystemController:
    """Camera loop with explicit gesture transitions and movement rebasing."""

    def __init__(self):
        self.running = True
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)
        self.tracker = HandTracker()
        self.start_time = time.monotonic()
        self._init_controls()

    def _init_controls(self):
        self.classifier = GestureClassifier()
        self.cursor = PhysicsCursor()
        self.drag_active = False
        self.previous_state = "IDLE"
        self.movement_mode = None
        self.smoother = None
        self.previous_point = None
        self.previous_raw_point = None
        self.scroll_reference = None

    def _reset_movement(self):
        self.movement_mode = None
        self.smoother = None
        self.previous_point = None
        self.previous_raw_point = None
        self.cursor.reset()

    def _release_drag(self):
        if self.drag_active:
            pyautogui.mouseUp()
            self.drag_active = False

    def _suspend(self):
        self._release_drag()
        self.classifier.process(None)
        self.previous_state = "IDLE"
        self.scroll_reference = None
        self._reset_movement()

    def _process_hand(self, landmarks, now, dt):
        if not landmarks:
            self._suspend()
            return "IDLE", 0.0
        state, meta = self.classifier.process(landmarks)
        was_dragging = self.drag_active
        if self.drag_active and state == "MOVE":
            self._release_drag()
        elif state == "FIST" and self.previous_state != "FIST" and not self.drag_active:
            pyautogui.mouseDown()
            self.drag_active = True
        self.previous_state = state
        drag_transition = was_dragging != self.drag_active

        # Consume pinch events during dragging as well: they must not leak on drop.
        if not self.drag_active and not was_dragging:
            if state in ("CLICK_LEFT", "CLICK_RIGHT"):
                if state == "CLICK_LEFT":
                    pyautogui.click()
                else:
                    pyautogui.rightClick()

        point = [landmarks[5].x, landmarks[5].y]
        mode = None
        if not drag_transition:
            if self.drag_active and state in ("FIST", "IDLE"):
                mode = "DRAG"
            elif not self.drag_active and state == "MOVE":
                mode = "MOVE"

        if mode is not None:
            if mode != self.movement_mode:
                self._reset_movement()
                self.movement_mode = mode
                # Seed with the actual hand, never the old gesture or screen center.
                self.smoother = OneEuroFilter(now, point,
                    min_cutoff=config.ONE_EURO_MIN_CUTOFF,
                    beta=config.ONE_EURO_BETA, d_cutoff=config.ONE_EURO_D_CUTOFF)
                self.previous_point = point
                self.previous_raw_point = point
            elif math.hypot(point[0] - self.previous_raw_point[0],
                            point[1] - self.previous_raw_point[1]) < config.DEAD_ZONE:
                # Stop immediately instead of replaying the position filter's tail.
                self.smoother = OneEuroFilter(now, point,
                    min_cutoff=config.ONE_EURO_MIN_CUTOFF,
                    beta=config.ONE_EURO_BETA, d_cutoff=config.ONE_EURO_D_CUTOFF)
                self.previous_point = point
                self.previous_raw_point = point
                self.cursor.reset()
            else:
                filtered = self.smoother(now, point)
                self.cursor.update_relative(filtered[0] - self.previous_point[0],
                                            filtered[1] - self.previous_point[1], dt)
                self.previous_point = filtered
                self.previous_raw_point = point
        else:
            # Pinch pending/held, scroll, drop and idle cannot retain cursor momentum.
            self._reset_movement()

        if not self.drag_active and not was_dragging and state == "SCROLL":
            # Scroll reference is separate from the cursor reset above.
            previous_y = getattr(self, "scroll_reference", None)
            if previous_y is not None:
                dy = point[1] - previous_y
                if abs(dy) > 0.005:
                    pyautogui.scroll(int(-dy * config.SCROLL_SPEED * 100))
            self.scroll_reference = point[1]
        else:
            self.scroll_reference = None
        return ("DRAG_ACTIVE" if self.drag_active else state), meta.get("confidence", 0.0)

    def run(self):
        print(f"[{config.APP_NAME}] System Initialized. Press 'Q' to Quit.")
        hud = CinematicHUD()
        last_time = time.monotonic()
        capture_seconds = inference_seconds = 0.0
        capture_count = inference_count = 0
        try:
            while self.running:
                current_time = time.monotonic()
                dt = current_time - last_time
                last_time = current_time
                started = time.perf_counter()
                success, img = self.cap.read()
                capture_seconds += time.perf_counter() - started
                capture_count += 1
                if not success:
                    self._suspend()
                    if cv2.waitKey(1) == ord('q'):
                        self.running = False
                    continue
                img = cv2.flip(img, 1)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                fps = 1 / dt if dt > 0 else 0
                if fps < config.FAILSAFE_FPS and current_time - self.start_time > 2.0:
                    self._suspend()
                    cv2.putText(img, "SAFETY PAUSE: LOW FPS",
                        (config.WINDOW_WIDTH // 2 - 150, config.WINDOW_HEIGHT // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                else:
                    started = time.perf_counter()
                    result = self.tracker.process(img_rgb, (current_time - self.start_time) * 1000)
                    inference_seconds += time.perf_counter() - started
                    inference_count += 1
                    landmarks = result.hand_landmarks[0] if result.hand_landmarks else None
                    state, confidence = self._process_hand(landmarks, current_time, dt)
                    if landmarks and state == "CLICK_LEFT":
                        anchor = landmarks[5]
                        cv2.circle(img, (int(anchor.x * config.WINDOW_WIDTH),
                                         int(anchor.y * config.WINDOW_HEIGHT)),
                                   50, config.COLOR_CLICK, 4)
                    hud.draw(img, landmarks, state, confidence)
                cv2.putText(img, f"{config.APP_NAME}  |  FPS: {int(fps)}", (20, 30),
                            cv2.FONT_HERSHEY_PLAIN, 1, (200, 255, 200), 1)
                cv2.imshow(config.APP_NAME, img)
                if cv2.waitKey(1) == ord('q'):
                    self.running = False
        finally:
            try:
                self._suspend()
            finally:
                self.cap.release()
                cv2.destroyAllWindows()
                if capture_count:
                    print(f"Capture read: {capture_seconds * 1000 / capture_count:.2f} ms mean ({capture_count} calls)")
                if inference_count:
                    print(f"Inference: {inference_seconds * 1000 / inference_count:.2f} ms mean ({inference_count} calls)")
