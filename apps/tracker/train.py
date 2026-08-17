"""Model Training Script for Face Recognition.

This script loads all face images stored in the 'dataset/' folder, extracts
the corresponding student IDs from the filenames, trains an LBPH (Local Binary
Patterns Histograms) face recognizer, and saves the trained model to 'trainer/trainer.yml'.
"""

from pathlib import Path
import re
import cv2
import numpy as np

# ==============================================================================
# Configuration & Constants
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
TRAINER_DIR = BASE_DIR / "trainer"
MODEL_PATH = TRAINER_DIR / "trainer.yml"

FACE_IMAGE_SIZE = (200, 200)

# ==============================================================================
# Dataset Loading
# ==============================================================================


def load_dataset() -> tuple[list[np.ndarray], list[int]]:
    """Scan the dataset directory and extract normalized face arrays and labels."""
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset directory not found at: {DATASET_DIR}")

    image_paths = sorted(DATASET_DIR.glob("*.jpg"))
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
        face_resized = cv2.resize(image, FACE_IMAGE_SIZE)

        faces.append(face_resized)
        ids.append(student_id)

    return faces, ids


# ==============================================================================
# Recognizer Training
# ==============================================================================


def train_recognizer(faces: list[np.ndarray], ids: list[int]) -> None:
    """Train the LBPH face recognizer and save the weights file."""
    TRAINER_DIR.mkdir(parents=True, exist_ok=True)

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    print(f"Training recognizer on {len(faces)} face samples across {len(set(ids))} student(s)...")
    recognizer.train(faces, np.array(ids))

    recognizer.write(str(MODEL_PATH))
    print(f"Model successfully saved to: {MODEL_PATH}")


# ==============================================================================
# Main Entry Point
# ==============================================================================


def main() -> None:
    faces, ids = load_dataset()

    if not faces:
        raise RuntimeError(
            f"No valid training samples found in '{DATASET_DIR}'. "
            "Please run 'uv run capture.py' first to capture face samples."
        )

    unique_students = sorted(list(set(ids)))
    print(f"Discovered student IDs: {unique_students}")

    train_recognizer(faces, ids)
    print("\nTraining completed successfully! You can now run 'uv run main.py'.")


if __name__ == "__main__":
    main()