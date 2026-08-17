"""Real-Time Gesture-Driven Facial Recognition Attendance System.

This script runs a live webcam stream integrating:
1. Facial recognition using Haar Cascade + OpenCV LBPH Face Recognizer.
2. Robust Hand Gesture Recognition using MediaPipe + Geometric Landmark Classifier:
   - ✌ Victory Sign ('Victory'): Check-In
   - 👍 Thumbs Up ('Thumb_Up'): Check-Out
3. 1-Hour Rate Limit per student (only one check-in or check-out permitted per hour).
4. SQLite database persistence with daily check-in/out tracking and detailed audit logs.
5. Real-time HUD with visual status badges, entry counters, cooldown countdowns, and animated action toasts.
"""

from datetime import datetime
import time

import cv2
import mediapipe as mp

from core.config import (
    ACTION_CHECK_IN,
    ACTION_CHECK_OUT,
    COLOR_CHECKOUT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    CONFIDENCE_THRESHOLD,
    FACE_IMAGE_SIZE,
    GESTURE_ACTION_MAP,
    WARNING_TOAST_DEBOUNCE_SECONDS,
)
from core.db import (
    fetch_enrolled_students,
    get_student_today_summary,
    init_database,
    record_attendance_action,
)
from ui.hud import (
    NotificationToast,
    draw_gesture_prompt_banner,
    draw_hand_landmarks_and_gesture,
    draw_hud_footer,
    draw_hud_header,
    draw_recognized_face_box,
    draw_toast_notification,
    draw_unknown_face_box,
)
from vision.gesture import classify_gesture_from_landmarks
from vision.models import (
    load_detector_and_model,
    load_gesture_recognizer,
)


# ==============================================================================
# Real-Time Video, Gesture & Attendance Loop
# ==============================================================================


def run_attendance_stream() -> None:
    """Open webcam, detect faces and hand gestures, and enforce 1-hour action limits."""
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

    # Track warning toast debounce per student so we don't spam every frame: student_id -> last_warning_time
    last_warning_toast_time: dict[int, float] = {}

    print("\n-------------------------------------------------------------")
    print("  Smart Attendance System is LIVE")
    print("  ✌ Victory Sign   -> CHECK-IN (1 action / hr limit)")
    print("  👍 Thumbs Up     -> CHECK-OUT (1 action / hr limit)")
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

                    # Process gesture action for this student with 1-hour rate limit
                    for action in active_actions:
                        success_flag, msg, count, remaining = record_attendance_action(
                            student_id, action
                        )

                        if success_flag:
                            if action == ACTION_CHECK_IN:
                                toast_color = COLOR_SUCCESS
                                toast_prefix = "✔ CHECK-IN RECORDED"
                            else:
                                toast_color = COLOR_CHECKOUT
                                toast_prefix = "✔ CHECK-OUT RECORDED"

                            toast_msg = f"{toast_prefix}: {student_name} (ID: {student_id}) - {msg}"
                            toast.show(toast_msg, toast_color, duration=3.5)
                            print(f"[{action} SUCCESS] {student_name} (ID: {student_id}): {msg}")

                        else:
                            # Action was blocked due to 1-hour rate limit
                            time_since_warn = current_time - last_warning_toast_time.get(
                                student_id, 0.0
                            )
                            if time_since_warn >= WARNING_TOAST_DEBOUNCE_SECONDS:
                                last_warning_toast_time[student_id] = current_time
                                toast_msg = (
                                    f"⏳ 1-HOUR LIMIT: {student_name} (ID: {student_id}) - {msg}"
                                )
                                toast.show(toast_msg, COLOR_WARNING, duration=3.0)
                                print(f"[{action} BLOCKED] {student_name} (ID: {student_id}): {msg}")

                    draw_recognized_face_box(
                        frame,
                        x,
                        y,
                        width,
                        height,
                        student_name,
                        student_id,
                        confidence,
                        summary,
                    )

                else:
                    draw_unknown_face_box(frame, x, y, width, height, confidence)

            # If gesture is active but no face is recognized, prompt user
            if active_actions and not recognized_students_in_frame:
                draw_gesture_prompt_banner(frame, active_actions)

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
