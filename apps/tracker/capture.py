"""Face Capture and Student Enrollment Script.

This script captures 30 face samples from the webcam for a given student ID and name,
registers the student in the SQLite database, and saves normalized face crops
to the 'dataset/' directory for training.
"""

from pathlib import Path
import cv2

from core.config import CASCADE_PATH, DATASET_DIR, FACE_IMAGE_SIZE, TOTAL_SAMPLES
from core.db import init_database, register_student
from vision.models import load_cascade_classifier


# ==============================================================================
# User Input Validation
# ==============================================================================


def prompt_student_details() -> tuple[int, str]:
    """Prompt the user for a valid student ID and name."""
    while True:
        id_str = input("Enter Student ID (positive integer, e.g. 101): ").strip()
        if id_str.isdigit() and int(id_str) >= 0:
            student_id = int(id_str)
            break
        print("Invalid ID. Please enter numeric digits only.")

    while True:
        student_name = input("Enter Student Name (e.g. Ali): ").strip()
        if student_name:
            break
        print("Student name cannot be empty. Please try again.")

    return student_id, student_name


# ==============================================================================
# Face Capture Loop
# ==============================================================================


def capture_face_samples(
    student_id: int,
    student_name: str,
    total_samples: int = TOTAL_SAMPLES,
    dataset_dir: Path = DATASET_DIR,
    face_image_size: tuple[int, int] = FACE_IMAGE_SIZE,
    cascade_path: Path = CASCADE_PATH,
) -> int:
    """Capture webcam frames, detect faces, and save cropped images."""
    face_detector = load_cascade_classifier(cascade_path)
    dataset_dir.mkdir(parents=True, exist_ok=True)

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open webcam. Check camera connection/permissions.")

    sample_count = 0
    print(f"\nEnrolling '{student_name}' (ID: {student_id})...")
    print("Position your face in front of the camera. Press 'Q' to cancel/exit.\n")

    try:
        while sample_count < total_samples:
            success, frame = camera.read()
            if not success:
                print("Failed to read frame from camera.")
                break

            # Mirror frame horizontally for intuitive interaction
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces in the frame
            faces = face_detector.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(60, 60),
            )

            for x, y, width, height in faces:
                sample_count += 1

                # Extract face region of interest (ROI) and normalize size
                face_roi = gray[y : y + height, x : x + width]
                face_resized = cv2.resize(face_roi, face_image_size)

                # Save sample image
                file_path = dataset_dir / f"User.{student_id}.{sample_count}.jpg"
                cv2.imwrite(str(file_path), face_resized)

                # Draw bounding box and progress label
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + width, y + height),
                    (255, 0, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Samples: {sample_count}/{total_samples}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

                if sample_count >= total_samples:
                    break

            cv2.imshow("Enrolling Student - Face Capture", frame)

            # Check if user pressed 'q' or 'ESC' to exit early
            key = cv2.waitKey(100) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                print("Capture cancelled by user.")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    return sample_count


# ==============================================================================
# Main Entry Point
# ==============================================================================


def main() -> None:
    init_database()
    student_id, student_name = prompt_student_details()
    register_student(student_id, student_name)

    captured = capture_face_samples(student_id, student_name)

    if captured > 0:
        print(f"\nCapture complete! Saved {captured} samples for {student_name} (ID: {student_id}).")
        print("Run 'uv run train.py' to train the recognizer on the updated dataset.")
    else:
        print("\nNo samples were captured.")


if __name__ == "__main__":
    main()