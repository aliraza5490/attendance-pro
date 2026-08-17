"""UI rendering, HUD overlays, notification banners, and visual feedback helpers."""

import time
import cv2

from core.config import (
    ACTION_CHECK_IN,
    ACTION_CHECK_OUT,
    COLOR_CHECKOUT,
    COLOR_GRAY,
    COLOR_INFO,
    COLOR_SUCCESS,
    COLOR_UNKNOWN,
    COLOR_WARNING,
    COLOR_WHITE,
    GESTURE_ACTION_MAP,
    GESTURE_DISPLAY_NAMES,
    HAND_CONNECTIONS,
)


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

    # Gesture guides with 1-hour limit notice
    guide_text = "✌ Victory: CHECK-IN   |   👍 Thumbs Up: CHECK-OUT (Limit: 1 action / hr)"
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

    hint = "Press 'Q' or 'ESC' to exit   |   Rate Limit: 1 action (check-in/out) per hour per student"
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
    scale = 0.60
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


def draw_recognized_face_box(
    frame,
    x: int,
    y: int,
    width: int,
    height: int,
    student_name: str,
    student_id: int,
    confidence: float,
    summary: dict,
) -> None:
    """Draw bounding box and status tags for a recognized enrolled student."""
    in_cnt = summary["check_in_count"]
    out_cnt = summary["check_out_count"]
    last_in = summary["last_check_in"] or "--"
    last_out = summary["last_check_out"] or "--"
    cooldown_rem = summary["cooldown_remaining_seconds"]

    # Format face bounding box label
    label_id = f"{student_name} (ID: {student_id}) [{int(confidence)}]"
    status_tag = f"In: {last_in} (x{in_cnt}) | Out: {last_out} (x{out_cnt})"

    if cooldown_rem > 0:
        rem_m = cooldown_rem // 60
        rem_s = cooldown_rem % 60
        cooldown_tag = f"1-Hr Limit: {rem_m:02d}m {rem_s:02d}s remaining"
        box_color = COLOR_INFO
    else:
        cooldown_tag = "Ready for Check-In/Out"
        box_color = COLOR_SUCCESS

    # Draw face bounding box
    cv2.rectangle(frame, (x, y), (x + width, y + height), box_color, 2)

    # Draw header tag above face
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw1, th1), _ = cv2.getTextSize(label_id, font, 0.6, 2)
    (tw2, th2), _ = cv2.getTextSize(status_tag, font, 0.45, 1)
    (tw3, th3), _ = cv2.getTextSize(cooldown_tag, font, 0.42, 1)
    max_w = max(tw1, tw2, tw3) + 14
    total_h = th1 + th2 + th3 + 22

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
    cooldown_color = (0, 165, 255) if cooldown_rem > 0 else (100, 255, 100)
    cv2.putText(
        frame,
        cooldown_tag,
        (x + 6, tag_top + th1 + th2 + th3 + 16),
        font,
        0.42,
        cooldown_color,
        1,
    )


def draw_unknown_face_box(
    frame,
    x: int,
    y: int,
    width: int,
    height: int,
    confidence: float,
) -> None:
    """Draw bounding box and status tags for an unrecognized or unenrolled face."""
    label_id = f"Unknown [{int(confidence)}]"
    status_tag = "Not Enrolled"
    box_color = COLOR_UNKNOWN

    # Draw face bounding box
    cv2.rectangle(frame, (x, y), (x + width, y + height), box_color, 2)

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


def draw_gesture_prompt_banner(frame, active_actions: list[str]) -> None:
    """Prompt user when gesture is detected without a recognized face."""
    if not active_actions:
        return
    frame_h, _, _ = frame.shape
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
