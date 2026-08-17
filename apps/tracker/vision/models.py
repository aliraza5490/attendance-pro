"""Model loaders, downloads, dataset loading, and LBPH trainer utilities."""

from pathlib import Path
import re
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

from core.config import (
    CASCADE_PATH,
    DATASET_DIR,
    FACE_IMAGE_SIZE,
    GESTURE_MODEL_PATH,
    GESTURE_MODEL_URL,
    MODEL_PATH,
    TRAINER_DIR,
)


# ==============================================================================
# Gesture Model Management
# ==============================================================================


def ensure_gesture_model(
    model_path: Path = GESTURE_MODEL_PATH,
    model_url: str = GESTURE_MODEL_URL,
) -> Path:
    """Ensure the MediaPipe gesture recognizer task model is downloaded."""
    if not model_path.exists():
        print(f"Downloading gesture recognizer model from {model_url}...")
        try:
            urllib.request.urlretrieve(model_url, str(model_path))
            print(f"Gesture model saved to: {model_path}")
        except Exception as err:
            raise RuntimeError(f"Failed to download gesture recognizer model: {err}") from err

    return model_path


def load_gesture_recognizer(model_path: Path = GESTURE_MODEL_PATH) -> vision.GestureRecognizer:
    """Initialize and return the MediaPipe GestureRecognizer instance."""
    model_file = ensure_gesture_model(model_path=model_path)
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


# ==============================================================================
# Face Detection & LBPH Recognition Model Management
# ==============================================================================


def load_cascade_classifier(cascade_path: Path = CASCADE_PATH) -> cv2.CascadeClassifier:
    """Validate and load the Haar cascade face detector."""
    if not cascade_path.exists():
        raise FileNotFoundError(f"Haar cascade XML not found at: {cascade_path}")

    face_detector = cv2.CascadeClassifier(str(cascade_path))
    if face_detector.empty():
        raise RuntimeError(f"Failed to load cascade classifier from: {cascade_path}")

    return face_detector


def load_detector_and_model(
    cascade_path: Path = CASCADE_PATH,
    model_path: Path = MODEL_PATH,
) -> tuple[cv2.CascadeClassifier, cv2.face.LBPHFaceRecognizer]:
    """Validate and load the Haar cascade face detector and trained LBPH model."""
    face_detector = load_cascade_classifier(cascade_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained model not found at '{model_path}'. "
            "Please run 'uv run capture.py' and 'uv run train.py' first."
        )

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(model_path))

    return face_detector, recognizer


# ==============================================================================
# Dataset Loading & Recognizer Training
# ==============================================================================


def load_dataset(
    dataset_dir: Path = DATASET_DIR,
    image_size: tuple[int, int] = FACE_IMAGE_SIZE,
) -> tuple[list[np.ndarray], list[int]]:
    """Scan the dataset directory and extract normalized face arrays and student IDs."""
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found at: {dataset_dir}")

    image_paths = sorted(dataset_dir.glob("*.jpg"))
    if not image_paths:
        return [], []

    faces: list[np.ndarray] = []
    ids: list[int] = []

    for img_path in image_paths:
        # Expected filename format: User.<student_id>.<sample_num>.jpg
        match = re.match(r"User\.(\d+)\.\d+\.jpg", img_path.name)
        if not match:
            continue

        student_id = int(match.group(1))

        # Read image directly in grayscale mode
        image = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue

        # Standardize face dimensions
        face_resized = cv2.resize(image, image_size)

        faces.append(face_resized)
        ids.append(student_id)

    return faces, ids


def train_recognizer(
    faces: list[np.ndarray],
    ids: list[int],
    trainer_dir: Path = TRAINER_DIR,
    model_path: Path = MODEL_PATH,
) -> None:
    """Train the LBPH face recognizer and save the weights file."""
    trainer_dir.mkdir(parents=True, exist_ok=True)

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    print(f"Training recognizer on {len(faces)} face samples across {len(set(ids))} student(s)...")
    recognizer.train(faces, np.array(ids))

    recognizer.write(str(model_path))
    print(f"Model successfully saved to: {model_path}")
