"""Hand gesture recognition and geometric landmark analysis."""

import math


def _dist(p1, p2) -> float:
    """Euclidean distance in 2D normalized coordinate space."""
    return math.hypot(p1.x - p2.x, p1.y - p2.y)


def classify_gesture_from_landmarks(
    landmarks,
    mp_gesture_name: str | None = None,
    mp_score: float = 0.0,
) -> tuple[str, float]:
    """Classify gesture using hand landmark geometry with MediaPipe model fallback.

    Ensures Victory sign (Index + Middle extended, Ring + Pinky curled) and
    Thumbs Up (Thumb extended upward, 4 fingers curled) are recognized with high
    precision regardless of hand orientation.

    Returns:
        tuple[str, float]: (gesture_name, confidence_score)
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
    if (
        thumb_extended
        and thumb_upward
        and (not index_extended)
        and (not middle_extended)
        and (not ring_extended)
        and (not pinky_extended)
    ):
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
