"""Face Capture and Student Enrollment Script.

This script captures 30 face samples from the webcam for a given student ID and name,
registers the student in the SQLite database, and saves normalized face crops
to the 'dataset/' directory for training.
"""

from pathlib import Path
import sqlite3
import cv2

# ==============================================================================
# Configuration & Constants
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
DATABASE_PATH = BASE_DIR / "attendance.db"
CASCADE_PATH = BASE_DIR / "haarcascades" / "haarcascade_frontalface_default.xml"

TOTAL_SAMPLES = 30
FACE_IMAGE_SIZE = (200, 200)

# ==============================================================================
# Database Functions
# ==============================================================================


def init_database() -> None:
    """Ensure the required database tables exist."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )
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


def register_student(student_id: int, student_name: str) -> None:
    """Insert or update a student record in the database."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO students (id, name)
            VALUES (?, ?)
            """,
            (student_id, student_name),
        )
        conn.commit()


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


def capture_face_samples(student_id: int, student_name: str) -> int:
    """Capture webcam frames, detect faces, and save cropped images."""
    if not CASCADE_PATH.exists():
        raise FileNotFoundError(f"Haar cascade XML not found at: {CASCADE_PATH}")

    face_detector = cv2.CascadeClassifier(str(CASCADE_PATH))
    if face_detector.empty():
        raise RuntimeError(f"Failed to load cascade classifier from: {CASCADE_PATH}")

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open webcam. Check camera connection/permissions.")

    sample_count = 0
    print(f"\nEnrolling '{student_name}' (ID: {student_id})...")
    print("Position your face in front of the camera. Press 'Q' to cancel/exit.\n")

    try:
        while sample_count < TOTAL_SAMPLES:
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
                face_resized = cv2.resize(face_roi, FACE_IMAGE_SIZE)

                # Save sample image
                file_path = DATASET_DIR / f"User.{student_id}.{sample_count}.jpg"
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
                    f"Samples: {sample_count}/{TOTAL_SAMPLES}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

                if sample_count >= TOTAL_SAMPLES:
                    break

            cv2.imshow("Enrolling Student - Face Capture", frame)

            # Check if user pressed 'q' or 'ESC' to exit early
            key = cv2.waitKey(100) & 0xFF
            if key in (ord("q"), 27):
                print("Capture cancelled by user.")
                break

    finally:
        # Guarantee camera and windows release
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