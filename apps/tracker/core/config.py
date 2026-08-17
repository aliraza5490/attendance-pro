"""Configuration settings and constants for the attendance tracker system."""

import os
from pathlib import Path

# ==============================================================================
# Paths & Directories
# ==============================================================================

# BASE_DIR points to apps/tracker/
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
TRAINER_DIR = BASE_DIR / "trainer"
MODEL_PATH = TRAINER_DIR / "trainer.yml"
CASCADE_PATH = BASE_DIR / "haarcascades" / "haarcascade_frontalface_default.xml"

GESTURE_MODEL_PATH = BASE_DIR / "gesture_recognizer.task"
GESTURE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
    "gesture_recognizer/float16/1/gesture_recognizer.task"
)

DATABASE_PATH = Path(
    os.environ.get(
        "DATABASE_PATH",
        (BASE_DIR.parent.parent / "attendance.db")
        if (BASE_DIR.parent.parent / "attendance.db").exists()
        else BASE_DIR / "attendance.db",
    )
)

# ==============================================================================
# Model & Recognition Parameters
# ==============================================================================

# Face image normalization size (must match training dimensions)
FACE_IMAGE_SIZE = (200, 200)

# Total samples captured per student during enrollment
TOTAL_SAMPLES = 30

# LBPH confidence threshold: lower value = stricter match (0 is exact match)
CONFIDENCE_THRESHOLD = 75

# 1-Hour Limit: Minimum seconds before allowing another action (check-in or check-out) for the same student
ACTION_COOLDOWN_SECONDS = 3600  # 1 hour (3600 seconds)

# Minimum seconds before showing another rate-limit warning toast for the same student
WARNING_TOAST_DEBOUNCE_SECONDS = 3.0

# ==============================================================================
# Colors (BGR Format for OpenCV)
# ==============================================================================

COLOR_SUCCESS = (50, 205, 50)       # Vibrant Lime Green (Check-In)
COLOR_CHECKOUT = (235, 135, 30)     # Deep Orange / Sky Blue (Check-Out)
COLOR_INFO = (255, 191, 0)          # Deep Sky Blue
COLOR_WARNING = (0, 165, 255)       # Orange
COLOR_UNKNOWN = (50, 50, 255)       # Coral Red
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (20, 20, 20)
COLOR_GRAY = (128, 128, 128)

# ==============================================================================
# Gesture Actions & Mappings
# ==============================================================================

ACTION_CHECK_IN = "CHECK_IN"
ACTION_CHECK_OUT = "CHECK_OUT"

GESTURE_ACTION_MAP = {
    "Victory": ACTION_CHECK_IN,
    "Thumb_Up": ACTION_CHECK_OUT,
}

GESTURE_DISPLAY_NAMES = {
    "Victory": "✌ Victory (Check-In)",
    "Thumb_Up": "👍 Thumbs Up (Check-Out)",
    "Thumb_Down": "👎 Thumbs Down",
    "Pointing_Up": "☝ Pointing Up",
    "Closed_Fist": "✊ Closed Fist",
    "Open_Palm": "✋ Open Palm",
    "ILoveYou": "🤟 I Love You",
}

# Hand skeleton connections for landmark drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]
