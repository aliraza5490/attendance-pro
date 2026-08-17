# Real-Time Gesture-Driven Attendance System

An AI-powered attendance tracking system combining **Face Recognition** (Haar Cascade + LBPH) and **Hand Gesture Recognition** (MediaPipe) with an automated **SQLite** database backend.

---

## ✌ Features & Hand Gestures

| Gesture | Action | Description |
| :--- | :--- | :--- |
| ✌ **Victory / Peace Sign** | **Check-In** | Marks daily check-in timestamp for the recognized student. Prevents duplicate check-ins on the same day. |
| 👍 **Thumbs Up** | **Check-Out** | Records or updates daily check-out timestamp for the recognized student. |

---

## 🚀 Quickstart Guide

### 1. Enroll New Students
Capture 30 normalized face samples from your webcam and register the student:
```bash
uv run capture.py
```

### 2. Train the Recognition Model
Train the LBPH recognizer on the captured dataset:
```bash
uv run train.py
```

### 3. Launch Live Attendance Stream
Start the real-time recognition loop with gesture-based check-in / check-out:
```bash
uv run main.py
```

---

## 🗄 Database Schema (`attendance.db`)

### `students`
- `id` (INTEGER PRIMARY KEY)
- `name` (TEXT NOT NULL)

### `attendance`
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `student_id` (INTEGER NOT NULL)
- `date` (TEXT NOT NULL) - `YYYY-MM-DD`
- `check_in_time` (TEXT) - `HH:MM:SS`
- `check_out_time` (TEXT) - `HH:MM:SS`
- `status` (TEXT) - `'CHECKED_IN'` / `'CHECKED_OUT'`
- `UNIQUE(student_id, date)`

### `attendance_logs`
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `student_id` (INTEGER NOT NULL)
- `action` (TEXT NOT NULL) - `'CHECK_IN'` / `'CHECK_OUT'`
- `date` (TEXT NOT NULL)
- `time` (TEXT NOT NULL)
- `timestamp` (TEXT NOT NULL) - ISO 8601 string
