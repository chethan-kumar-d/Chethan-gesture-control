
"""
Centralized source of truth for all physics, UI, and logic constants.
"""
import math
import pyautogui

# --- SYSTEM ---
APP_NAME = "Chethan Gesture Control"
WINDOW_WIDTH, WINDOW_HEIGHT = pyautogui.size()
TARGET_FPS = 60

# --- PERCEPTION (OneEuroFilter) ---
# Low-jitter smoothing parameters
ONE_EURO_MIN_CUTOFF = 3.0  # Hz. Lower = more smoothing when slow
ONE_EURO_BETA = 4.0         # Reduced from 10.0 to 4.0 to reduce jitter/dancing
ONE_EURO_D_CUTOFF = 1.0     # Hz. Cutoff for derivative

# --- GESTURE CONFIG ---
# Confidence accumulation (0.0 to 1.0)
GESTURE_CONFIDENCE_THRESHOLD = 0.8  # Increased back to 0.8 (require more certainty)
CONFIDENCE_DECAY = 0.2             # Faster decay (forget partial pinches quickly)
CONFIDENCE_GROWTH = 0.15           # Slower growth (require sustained pinch)


# --- V6 RELATIVE PHYSICS (AIR MOUSE) ---
DEAD_ZONE = 0.002        # Anti-tremor: Movement below this is ignored
BASE_SENSITIVITY = 0.75 # Base speed
ACCELERATION_FACTOR = 4.0 # Gain for fast movements
MAX_SENSITIVITY = 2.0   # Cap
DELTA_SMOOTHING = 0.15   # Lag reduction

# --- GESTURES ---
# Pinch
PINCH_THRESHOLD_NORM = 0.06
PINCH_RELEASE_THRESHOLD_NORM = 0.085  # Hysteresis: visibly separate before rearming
CLICK_COOLDOWN = 0.4

# Scroll
SCROLL_SPEED = 20
SCROLL_DEADZONE = 0.05

# Drag appearance (fist grabs; open palm releases)
COLOR_DRAG_ACTIVE = (0, 255, 0) # Green (Locked)

# --- UI COLORS (BGR) ---
COLOR_IDLE = (255, 255, 0)      # Cyan
COLOR_MOVE = (255, 255, 255)    # White (Open Palm)
COLOR_CLICK = (0, 0, 255)       # Red
COLOR_RIGHT_CLICK = (255, 0, 0) # Blue
COLOR_SCROLL = (255, 0, 255)    # Magenta
COLOR_TEXT = (255, 255, 255)

# --- SAFETY ---
FAILSAFE_FPS = 15  # Minimum FPS to maintain active control
