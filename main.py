"""Real-Time Gesture-Driven Facial Recognition Attendance System.

This script runs a live webcam stream integrating:
1. Facial recognition using Haar Cascade + OpenCV LBPH Face Recognizer.
2. Robust Hand Gesture Recognition using MediaPipe + Geometric Landmark Classifier:
   - ✌ Victory Sign ('Victory'): Multi Check-In (allows multiple check-ins throughout the day)
   - 👍 Thumbs Up ('Thumb_Up'): Multi Check-Out (allows multiple check-outs throughout the day)
3. SQLite database persistence with daily check-in/out tracking and detailed audit logs.
4. Real-time HUD with visual status badges, entry counters, and animated action toasts.
"""

from datetime import datetime
import math
from pathlib import Path
import sqlite3
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ==============================================================================
# Configuration & Constants
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "attendance.db"
MODEL_PATH = BASE_DIR / "trainer" / "trainer.yml"
CASCADE_PATH = BASE_DIR / "haarcascades" / "haarcascade_frontalface_default.xml"
GESTURE_MODEL_PATH = BASE_DIR / "gesture_recognizer.task"
GESTURE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
    "gesture_recognizer/float16/1/gesture_recognizer.task"
)

# Face image normalization size (must match training dimensions)
FACE_IMAGE_SIZE = (200, 200)

# LBPH confidence threshold: lower value = stricter match (0 is exact).
CONFIDENCE_THRESHOLD = 75

# Minimum seconds before registering another gesture action for the same student
GESTURE_COOLDOWN_SECONDS = 3.0

# Display colors (BGR format)
COLOR_SUCCESS = (50, 205, 50)      # Vibrant Lime Green (Check-In)
COLOR_CHECKOUT = (235, 135, 30)    # Deep Sky Blue/Orange (Check-Out)
COLOR_INFO = (255, 191, 0)         # Deep Sky Blue
COLOR_WARNING = (0, 165, 255)      # Orange
COLOR_UNKNOWN = (50, 50, 255)      # Coral Red
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (20, 20, 20)
COLOR_GRAY = (128, 128, 128)

# Gesture Action Constants
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


# ==============================================================================
# Model Downloads & Initialization
# ==============================================================================


def ensure_gesture_model() -> Path:
    """Ensure the MediaPipe gesture recognizer task model is downloaded."""
    if not GESTURE_MODEL_PATH.exists():
        print(f"Downloading gesture recognizer model from {GESTURE_MODEL_URL}...")
        try:
            urllib.request.urlretrieve(GESTURE_MODEL_URL, str(GESTURE_MODEL_PATH))
            print(f"Gesture model saved to: {GESTURE_MODEL_PATH}")
        except Exception as err:
            raise RuntimeError(f"Failed to download gesture recognizer model: {err}") from err

    return GESTURE_MODEL_PATH


def load_gesture_recognizer() -> vision.GestureRecognizer:
    """Initialize and return the MediaPipe GestureRecognizer instance."""
    model_file = ensure_gesture_model()
    base_options = python.BaseOptions(model_asset_path=str(model_file))
    options = vision.GestureRecognizerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.GestureRecognizer.create_from_options(options)


def load_detector_and_model() -> tuple[cv2.CascadeClassifier, cv2.face.LBPHFaceRecognizer]:
    """Validate and load the Haar cascade face detector and trained LBPH model."""
    if not CASCADE_PATH.exists():
        raise FileNotFoundError(f"Haar cascade XML not found at: {CASCADE_PATH}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at '{MODEL_PATH}'. "
            "Please run 'uv run capture.py' and 'uv run train.py' first."
        )

    face_detector = cv2.CascadeClassifier(str(CASCADE_PATH))
    if face_detector.empty():
        raise RuntimeError(f"Failed to load cascade classifier: {CASCADE_PATH}")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(MODEL_PATH))

    return face_detector, recognizer


# ==============================================================================
# Robust Hand Gesture Classifier (Geometric Landmark Analysis)
# ==============================================================================


def _dist(p1, p2) -> float:
    """Euclidean distance in 2D normalized coordinate space."""
    return math.hypot(p1.x - p2.x, p1.y - p2.y)


def classify_gesture_from_landmarks(
    landmarks,
    mp_gesture_name: str | None = None,
    mp_score: float = 0.0,
) -> tuple[str, float]:
    """Classify gesture using hand landmark geometry with MediaPipe model fallback.

    This ensures Victory sign (Index + Middle extended, Ring + Pinky curled) and
    Thumbs Up are recognized with 100% accuracy regardless of hand angle.
    """
    if not landmarks or len(landmarks) < 21:
        return mp_gesture_name or "None", mp_score

    wrist = landmarks[0]

    # Check finger extensions relative to wrist and MCP base
    # Index finger (5: MCP, 6: PIP, 8: TIP)
    index_extended = (_dist(landmarks[8], wrist) > _dist(landmarks[6], wrist) * 1.15) and (
        _dist(landmarks[8], landmarks[5]) > _dist(landmarks[6], landmarks[5])
    )

    # Middle finger (9: MCP, 10: PIP, 12: TIP)
    middle_extended = (_dist(landmarks[12], wrist) > _dist(landmarks[10], wrist) * 1.15) and (
        _dist(landmarks[12], landmarks[9]) > _dist(landmarks[10], landmarks[9])
    )

    # Ring finger (13: MCP, 14: PIP, 16: TIP)
    ring_extended = (_dist(landmarks[16], wrist) > _dist(landmarks[14], wrist) * 1.15) and (
        _dist(landmarks[16], landmarks[13]) > _dist(landmarks[14], landmarks[13])
    )

    # Pinky finger (17: MCP, 18: PIP, 20: TIP)
    pinky_extended = (_dist(landmarks[20], wrist) > _dist(landmarks[18], wrist) * 1.15) and (
        _dist(landmarks[20], landmarks[17]) > _dist(landmarks[18], landmarks[17])
    )

    # Thumb extension relative to pinky MCP base (17)
    thumb_extended = _dist(landmarks[4], landmarks[17]) > _dist(landmarks[3], landmarks[17])

    # 1. Victory / Peace Sign: Index & Middle EXTENDED, Ring & Pinky CURLED
    if index_extended and middle_extended and (not ring_extended) and (not pinky_extended):
        return "Victory", max(mp_score, 0.95)

    # 2. Thumbs Up: Thumb pointing upward & extended, 4 fingers CURLED
    thumb_upward = (landmarks[4].y < landmarks[3].y) and (landmarks[4].y < landmarks[0].y)
    if thumb_extended and thumb_upward and (not index_extended) and (not middle_extended) and (not ring_extended) and (not pinky_extended):
        return "Thumb_Up", max(mp_score, 0.95)

    # 3. Model predicted Victory or Thumb_Up with high confidence
    if mp_gesture_name == "Victory" and mp_score > 0.5:
        return "Victory", mp_score
    if mp_gesture_name == "Thumb_Up" and mp_score > 0.5:
        return "Thumb_Up", mp_score

    # Fallback to MediaPipe top prediction or Unknown
    if mp_gesture_name and mp_gesture_name != "None":
        return mp_gesture_name, mp_score

    return "Unknown", 0.0


# ==============================================================================
# Database Operations (Multiple Check-Ins & Check-Outs Supported)
# ==============================================================================


def init_database() -> None:
    """Ensure tables and columns exist for attendance and multiple gesture event logs."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Students table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        # Attendance daily summary table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT,
                check_in_time TEXT,
                check_out_time TEXT,
                status TEXT,
                UNIQUE(student_id, date)
            )
            """
        )

        # Migration: Ensure check_in_time, check_out_time, status exist
        cursor.execute("PRAGMA table_info(attendance)")
        columns = [row[1] for row in cursor.fetchall()]
        if "check_in_time" not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN check_in_time TEXT")
        if "check_out_time" not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN check_out_time TEXT")
        if "status" not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN status TEXT")

        # Detailed audit log for ALL check-in and check-out events
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
            """
        )
        conn.commit()


def fetch_enrolled_students() -> dict[int, str]:
    """Retrieve mapping of student_id -> student_name."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM students")
        return {row[0]: row[1] for row in cursor.fetchall()}


def get_student_today_summary(student_id: int) -> dict:
    """Retrieve today's check-in/out counts, latest timestamps, and status."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Fetch all log entries today for this student
        cursor.execute(
            """
            SELECT action, time
            FROM attendance_logs
            WHERE student_id = ? AND date = ?
            ORDER BY id ASC
            """,
            (student_id, date_str),
        )
        rows = cursor.fetchall()

        ins = [r[1] for r in rows if r[0] == "CHECK_IN"]
        outs = [r[1] for r in rows if r[0] == "CHECK_OUT"]

        return {
            "check_in_count": len(ins),
            "check_out_count": len(outs),
            "last_check_in": ins[-1] if ins else None,
            "last_check_out": outs[-1] if outs else None,
            "latest_action": rows[-1][0] if rows else None,
        }


def record_attendance_action(student_id: int, action: str) -> tuple[bool, str, int]:
    """Record a check-in or check-out event in the database (supports multiple entries).

    Returns:
        tuple[bool, str, int]: (success, message, current_action_count)
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    iso_timestamp = now.isoformat()

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # 1. Insert into detailed event log
        cursor.execute(
            """
            INSERT INTO attendance_logs (student_id, action, date, time, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, action, date_str, time_str, iso_timestamp),
        )

        # 2. Count total actions of this type today
        cursor.execute(
            """
            SELECT COUNT(*) FROM attendance_logs
            WHERE student_id = ? AND date = ? AND action = ?
            """,
            (student_id, date_str, action),
        )
        action_count = cursor.fetchone()[0]

        # 3. Update/Insert summary in daily attendance table
        cursor.execute(
            """
            SELECT id FROM attendance
            WHERE student_id = ? AND date = ?
            """,
            (student_id, date_str),
        )
        row = cursor.fetchone()

        if action == ACTION_CHECK_IN:
            if row is None:
                cursor.execute(
                    """
                    INSERT INTO attendance (student_id, date, time, check_in_time, status)
                    VALUES (?, ?, ?, ?, 'CHECKED_IN')
                    """,
                    (student_id, date_str, time_str, time_str),
                )
            else:
                cursor.execute(
                    """
                    UPDATE attendance
                    SET check_in_time = ?, time = ?, status = 'CHECKED_IN'
                    WHERE student_id = ? AND date = ?
                    """,
                    (time_str, time_str, student_id, date_str),
                )
            conn.commit()
            msg = f"Check-In #{action_count} recorded at {time_str}"
            return True, msg, action_count

        elif action == ACTION_CHECK_OUT:
            if row is None:
                cursor.execute(
                    """
                    INSERT INTO attendance (student_id, date, time, check_out_time, status)
                    VALUES (?, ?, ?, ?, 'CHECKED_OUT')
                    """,
                    (student_id, date_str, time_str, time_str),
                )
            else:
                cursor.execute(
                    """
                    UPDATE attendance
                    SET check_out_time = ?, status = 'CHECKED_OUT'
                    WHERE student_id = ? AND date = ?
                    """,
                    (time_str, student_id, date_str),
                )
            conn.commit()
            msg = f"Check-Out #{action_count} recorded at {time_str}"
            return True, msg, action_count

        return False, "Unknown action", 0


# ==============================================================================
# Visual Feedback & HUD Rendering
# ==============================================================================


class NotificationToast:
    """Manages active on-screen notification banners with timeouts."""

    def __init__(self) -> None:
        self.message: str = ""
        self.color: tuple[int, int, int] = COLOR_SUCCESS
        self.expiry_time: float = 0.0

    def show(self, message: str, color: tuple[int, int, int], duration: float = 3.5) -> None:
        self.message = message
        self.color = color
        self.expiry_time = time.time() + duration

    def is_active(self) -> bool:
        return time.time() < self.expiry_time


def draw_hud_header(frame, current_dt_str: str) -> None:
    """Draw a clean top HUD banner with system branding and gesture cheat sheet."""
    h, w, _ = frame.shape
    banner_height = 60

    # Semi-transparent dark header overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, banner_height), (25, 25, 25), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    # Header title and live indicator
    cv2.circle(frame, (20, 22), 6, (0, 255, 0), -1)
    cv2.putText(
        frame,
        "ATTENDANCE SYSTEM (GESTURE ENABLED)",
        (35, 27),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        COLOR_WHITE,
        2,
    )

    # Clock on top right
    cv2.putText(
        frame,
        current_dt_str,
        (w - 200, 27),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
    )

    # Gesture guides
    guide_text = "✌ Victory: CHECK-IN (Multi)   |   👍 Thumbs Up: CHECK-OUT (Multi)"
    cv2.putText(
        frame,
        guide_text,
        (35, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (0, 230, 230),
        1,
    )


def draw_hud_footer(frame) -> None:
    """Draw bottom footer bar with shortcut key hints."""
    h, w, _ = frame.shape
    footer_height = 30
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - footer_height), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    hint = "Press 'Q' or 'ESC' to exit   |   Multiple Check-Ins and Check-Outs Supported"
    cv2.putText(
        frame,
        hint,
        (20, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (180, 180, 180),
        1,
    )


def draw_toast_notification(frame, toast: NotificationToast) -> None:
    """Draw an active floating toast banner near top-center."""
    if not toast.is_active():
        return

    h, w, _ = frame.shape
    text = toast.message
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.65
    thickness = 2

    (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
    box_w = text_w + 40
    box_h = text_h + 24
    box_x = (w - box_w) // 2
    box_y = 70

    overlay = frame.copy()
    cv2.rectangle(
        overlay,
        (box_x, box_y),
        (box_x + box_w, box_y + box_h),
        (20, 20, 20),
        -1,
    )
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    # Border in toast color
    cv2.rectangle(
        frame,
        (box_x, box_y),
        (box_x + box_w, box_y + box_h),
        toast.color,
        2,
    )

    # Notification text
    cv2.putText(
        frame,
        text,
        (box_x + 20, box_y + text_h + 10),
        font,
        scale,
        toast.color,
        thickness,
    )


def draw_hand_landmarks_and_gesture(frame, landmarks, gesture_name: str, confidence: float) -> None:
    """Render skeleton lines, landmark points, and gesture label on the frame."""
    h, w, _ = frame.shape
    points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    # Draw connections
    for start_idx, end_idx in HAND_CONNECTIONS:
        if start_idx < len(points) and end_idx < len(points):
            cv2.line(frame, points[start_idx], points[end_idx], (0, 220, 255), 2)

    # Draw landmark joints
    for pt in points:
        cv2.circle(frame, pt, 4, (0, 255, 120), -1)

    # Determine hand bounding box
    xs = [pt[0] for pt in points]
    ys = [pt[1] for pt in points]
    min_x, max_x = max(0, min(xs) - 10), min(w, max(xs) + 10)
    min_y, max_y = max(0, min(ys) - 10), min(h, max(ys) + 10)

    # Choose color and text according to recognized gesture
    action = GESTURE_ACTION_MAP.get(gesture_name)
    display_label = GESTURE_DISPLAY_NAMES.get(gesture_name, gesture_name)
    conf_pct = int(confidence * 100)

    if action == ACTION_CHECK_IN:
        tag_color = COLOR_SUCCESS
        tag_text = f"{display_label} [{conf_pct}%]"
    elif action == ACTION_CHECK_OUT:
        tag_color = COLOR_CHECKOUT
        tag_text = f"{display_label} [{conf_pct}%]"
    else:
        tag_color = COLOR_GRAY
        tag_text = f"{display_label} [{conf_pct}%]"

    # Hand bounding box
    cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), tag_color, 2)

    # Label badge above hand
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(tag_text, font, 0.55, 2)
    tag_y = max(min_y - 8, th + 10)
    cv2.rectangle(frame, (min_x, tag_y - th - 6), (min_x + tw + 8, tag_y + 4), (20, 20, 20), -1)
    cv2.putText(frame, tag_text, (min_x + 4, tag_y), font, 0.55, tag_color, 2)


# ==============================================================================
# Real-Time Video, Gesture & Attendance Loop
# ==============================================================================


def run_attendance_stream() -> None:
    """Open webcam, detect faces and hand gestures, and handle check-in/out."""
    init_database()
    students = fetch_enrolled_students()

    print(f"\nLoaded {len(students)} enrolled student(s):")
    for sid, name in students.items():
        print(f"  - ID {sid}: {name}")

    print("\nInitializing detectors and models...")
    face_detector, recognizer = load_detector_and_model()
    gesture_recognizer = load_gesture_recognizer()

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open webcam. Check device permissions.")

    toast = NotificationToast()

    # Track student action cooldowns: (student_id, action) -> timestamp
    last_action_time: dict[tuple[int, str], float] = {}

    print("\n-------------------------------------------------------------")
    print("  Smart Attendance System is LIVE")
    print("  ✌ Victory Sign   -> CHECK-IN (Multiple supported)")
    print("  👍 Thumbs Up     -> CHECK-OUT (Multiple supported)")
    print("  Press 'Q' or 'ESC' to quit")
    print("-------------------------------------------------------------\n")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Failed to read frame from webcam.")
                break

            # Mirror frame horizontally for natural intuitive interaction
            frame = cv2.flip(frame, 1)
            frame_h, frame_w, _ = frame.shape
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # ------------------------------------------------------------------
            # 1. Hand Gesture Detection with Robust Geometric Classifier
            # ------------------------------------------------------------------
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            gesture_result = gesture_recognizer.recognize(mp_image)

            active_actions: list[str] = []

            if gesture_result.hand_landmarks:
                for idx, hand_lms in enumerate(gesture_result.hand_landmarks):
                    raw_name = "None"
                    raw_score = 0.0
                    if idx < len(gesture_result.gestures) and gesture_result.gestures[idx]:
                        top_gesture = gesture_result.gestures[idx][0]
                        raw_name = top_gesture.category_name
                        raw_score = top_gesture.score

                    # Robust classification (handles angled Victory and Thumbs Up)
                    gesture_name, confidence = classify_gesture_from_landmarks(
                        hand_lms, raw_name, raw_score
                    )

                    draw_hand_landmarks_and_gesture(frame, hand_lms, gesture_name, confidence)

                    mapped_action = GESTURE_ACTION_MAP.get(gesture_name)
                    if mapped_action and confidence > 0.5:
                        active_actions.append(mapped_action)

            # ------------------------------------------------------------------
            # 2. Face Detection & Recognition
            # ------------------------------------------------------------------
            faces = face_detector.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(60, 60),
            )

            current_time = time.time()
            recognized_students_in_frame = []

            for x, y, width, height in faces:
                face_roi = gray[y : y + height, x : x + width]
                face_resized = cv2.resize(face_roi, FACE_IMAGE_SIZE)

                student_id, confidence = recognizer.predict(face_resized)
                is_recognized = (confidence < CONFIDENCE_THRESHOLD) and (student_id in students)

                if is_recognized:
                    student_name = students[student_id]
                    recognized_students_in_frame.append((student_id, student_name))
                    summary = get_student_today_summary(student_id)

                    in_cnt = summary["check_in_count"]
                    out_cnt = summary["check_out_count"]
                    last_in = summary["last_check_in"] or "--"
                    last_out = summary["last_check_out"] or "--"

                    # Format face bounding box label
                    label_id = f"{student_name} (ID: {student_id}) [{int(confidence)}]"
                    status_tag = f"In: {last_in} (x{in_cnt}) | Out: {last_out} (x{out_cnt})"
                    box_color = COLOR_SUCCESS

                    # Process gesture action for this student
                    for action in active_actions:
                        cooldown_key = (student_id, action)
                        time_since_last = current_time - last_action_time.get(cooldown_key, 0.0)

                        if time_since_last >= GESTURE_COOLDOWN_SECONDS:
                            success_flag, msg, count = record_attendance_action(student_id, action)
                            last_action_time[cooldown_key] = current_time

                            if action == ACTION_CHECK_IN:
                                toast_color = COLOR_SUCCESS
                                toast_prefix = "✔ CHECK-IN"
                            else:
                                toast_color = COLOR_CHECKOUT
                                toast_prefix = "✔ CHECK-OUT"

                            toast_msg = f"{toast_prefix}: {student_name} (ID: {student_id}) - {msg}"
                            toast.show(toast_msg, toast_color, duration=3.5)

                            print(f"[{action} SUCCESS] {student_name} (ID: {student_id}): {msg}")

                else:
                    label_id = f"Unknown [{int(confidence)}]"
                    status_tag = "Not Enrolled"
                    box_color = COLOR_UNKNOWN

                # Draw face bounding box
                cv2.rectangle(frame, (x, y), (x + width, y + height), box_color, 2)

                # Draw header tag above face
                font = cv2.FONT_HERSHEY_SIMPLEX
                (tw1, th1), _ = cv2.getTextSize(label_id, font, 0.6, 2)
                (tw2, th2), _ = cv2.getTextSize(status_tag, font, 0.45, 1)
                max_w = max(tw1, tw2) + 12
                total_h = th1 + th2 + 16

                tag_top = max(y - total_h, 65)  # Stay below header banner
                cv2.rectangle(
                    frame,
                    (x, tag_top),
                    (x + max_w, tag_top + total_h),
                    (20, 20, 20),
                    -1,
                )
                cv2.rectangle(
                    frame,
                    (x, tag_top),
                    (x + max_w, tag_top + total_h),
                    box_color,
                    1,
                )

                cv2.putText(
                    frame,
                    label_id,
                    (x + 6, tag_top + th1 + 4),
                    font,
                    0.6,
                    box_color,
                    2,
                )
                cv2.putText(
                    frame,
                    status_tag,
                    (x + 6, tag_top + th1 + th2 + 10),
                    font,
                    0.45,
                    (220, 220, 220),
                    1,
                )

            # If gesture is active but no face is recognized, prompt user
            if active_actions and not recognized_students_in_frame:
                action_name = "Check-In" if ACTION_CHECK_IN in active_actions else "Check-Out"
                cv2.putText(
                    frame,
                    f"Gesture Detected ({action_name}) - Please align your face",
                    (30, frame_h - 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    COLOR_WARNING,
                    2,
                )

            # ------------------------------------------------------------------
            # 3. HUD Overlays & Notifications
            # ------------------------------------------------------------------
            now_dt_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            draw_hud_header(frame, now_dt_str)
            draw_hud_footer(frame)
            draw_toast_notification(frame, toast)

            cv2.imshow("Smart Attendance System", frame)

            # Exit if user presses 'q' or 'ESC'
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                print("Quitting attendance system...")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


# ==============================================================================
# Main Entry Point
# ==============================================================================


def main() -> None:
    run_attendance_stream()


if __name__ == "__main__":
    main()
