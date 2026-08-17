"""Model Training Script for Face Recognition.

This script loads all face images stored in the 'dataset/' folder, extracts
the corresponding student IDs from the filenames, trains an LBPH (Local Binary
Patterns Histograms) face recognizer, and saves the trained model to 'trainer/trainer.yml'.
"""

from core.config import DATASET_DIR
from vision.models import load_dataset, train_recognizer


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