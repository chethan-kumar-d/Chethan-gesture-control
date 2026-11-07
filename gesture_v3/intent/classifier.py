import math
import time
from gesture_v3 import config


class GestureClassifier:
    """Confirm a stable pinch once; rearm only after visible separation."""

    def __init__(self):
        self.state = "IDLE"
        self.pinch_confidence = 0.0
        self.pinch_type = None
        self.pinch_armed = True
        self.prev_wrist = None
        self.last_update = None
        self.last_click_time = float("-inf")

    def process(self, landmarks):
        if not landmarks:
            self.state = "IDLE"
            self.pinch_confidence = 0.0
            self.pinch_type = None
            self.prev_wrist = None
            self.last_update = None
            # Reacquiring a still-pinched hand must not produce a new click.
            self.pinch_armed = False
            return self.state, {}

        now = time.monotonic()
        wrist = (landmarks[0].x, landmarks[0].y)
        velocity = 0.0
        if self.prev_wrist is not None and now > self.last_update:
            velocity = math.hypot(wrist[0] - self.prev_wrist[0],
                                  wrist[1] - self.prev_wrist[1]) / (now - self.last_update)
        self.prev_wrist, self.last_update = wrist, now
        thumb, index, middle = landmarks[4], landmarks[8], landmarks[12]
        left = math.hypot(thumb.x - index.x, thumb.y - index.y)
        right = math.hypot(thumb.x - middle.x, thumb.y - middle.y)
        up = [landmarks[i].y < landmarks[i - 2].y for i in (8, 12, 16, 20)]
        thumb_out = math.hypot(thumb.x - landmarks[5].x, thumb.y - landmarks[5].y) > 0.05
        fist = not any(up)
        palm = all(up) and thumb_out
        separated = min(left, right) > config.PINCH_RELEASE_THRESHOLD_NORM
        if separated:
            self.pinch_armed = True
            self.pinch_confidence = 0.0
            self.pinch_type = None

        kind = "LEFT" if left < config.PINCH_THRESHOLD_NORM else (
            "RIGHT" if right < config.PINCH_THRESHOLD_NORM else None)
        # A curled fist is a grab, even when its fingertips are near the thumb.
        if fist:
            self.state = "FIST"
            self.pinch_confidence = 0.0
            self.pinch_type = None
        elif kind is not None or (self.pinch_type is not None and not separated):
            if kind != self.pinch_type and kind is not None:
                self.pinch_confidence = 0.0
                self.pinch_type = kind
            if self.pinch_armed and kind is not None and velocity < 2.0:
                self.pinch_confidence = min(1.0, self.pinch_confidence + config.CONFIDENCE_GROWTH)
            else:
                self.pinch_confidence = max(0.0, self.pinch_confidence - config.CONFIDENCE_DECAY)
            self.state = "CLICK_PENDING"
            if (self.pinch_armed and self.pinch_confidence >= config.GESTURE_CONFIDENCE_THRESHOLD
                    and now - self.last_click_time >= config.CLICK_COOLDOWN):
                self.state = "CLICK_" + self.pinch_type
                self.pinch_armed = False
                self.last_click_time = now
        else:
            self.pinch_confidence = 0.0
            self.pinch_type = None
            if palm:
                self.state = "MOVE"
            elif up[0] and up[1] and not up[2] and not up[3]:
                self.state = "SCROLL"
            else:
                self.state = "IDLE"
        return self.state, {"confidence": self.pinch_confidence, "pinch_dist": left,
                            "open_palm": palm}
