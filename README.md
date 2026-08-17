# Real-Time Gesture-Driven Attendance System & Dashboard

An AI-powered attendance tracking system combining **Face Recognition** (Haar Cascade + LBPH) and **Hand Gesture Recognition** (MediaPipe) with a **FastAPI** backend and a modern **Next.js** dashboard.

---

## 🏗 Monorepo Architecture (`uv` Workspaces)

```text
attendance_system/
├── pyproject.toml              # Root uv workspace manifest
├── attendance.db               # Shared SQLite database
├── apps/
│   ├── tracker/                # Computer Vision Face & Gesture HUD
│   │   ├── pyproject.toml
│   │   ├── main.py             # Live stream gesture & face recognition
│   │   ├── capture.py          # Face enrollment script (30 samples)
│   │   ├── train.py            # LBPH trainer
│   │   ├── core/               # Configuration & SQLite DB operations
│   │   │   ├── config.py
│   │   │   └── db.py
│   │   ├── vision/             # Face models & gesture recognition
│   │   │   ├── models.py
│   │   │   └── gesture.py
│   │   ├── ui/                 # HUD rendering & notification toasts
│   │   │   └── hud.py
│   │   ├── dataset/            # Face crops
│   │   ├── trainer/            # trainer.yml
│   │   └── haarcascades/
│   └── backend/                # FastAPI REST API & Analytics Service
│       ├── pyproject.toml
│       └── app/
│           ├── main.py         # FastAPI entrypoint & CORS
│           ├── database.py     # SQLite queries & metric calculators
│           ├── schemas.py      # Pydantic models
│           └── routers/        # Analytics, Attendance, Employees, Logs
└── frontend/                   # Next.js 16 + TailwindCSS Dashboard
    ├── src/app/
    │   ├── page.tsx            # Analytics Overview & KPI charts
    │   ├── attendance/page.tsx # Filterable attendance records & CSV export
    │   ├── employees/page.tsx  # Employee directory & profile history
    │   └── live/page.tsx       # Real-time live HUD event stream
    └── package.json
```

---

## ✌ Features & Hand Gestures

| Gesture | Action | Description |
| :--- | :--- | :--- |
| ✌ **Victory / Peace Sign** | **Check-In** | Marks daily check-in timestamp for the recognized employee with cooldown protection. |
| 👍 **Thumbs Up** | **Check-Out** | Records or updates daily check-out timestamp for the recognized employee. |

---

## 🚀 Getting Started

### 1. Workspace Installation
Install all Python workspace packages using `uv`:
```bash
uv sync
```

Install frontend packages:
```bash
cd frontend && npm install && cd ..
```

---

### 2. Running the Applications

#### 🖥️ A. Start the Dashboard Backend (FastAPI - Port 8000)
```bash
uv run --package attendance-backend uvicorn app.main:app --reload --port 8000
```
API documentation available at: `http://localhost:8000/docs`

#### 🌐 B. Start the Next.js Frontend Dashboard (Port 3000)
```bash
cd frontend && npm run dev
```
Dashboard available at: `http://localhost:3000`

#### 🎥 C. Run the Tracker / Enrollment
- **Capture face samples for new employee**:
  ```bash
  uv run --package attendance-tracker capture
  ```
- **Train LBPH Model**:
  ```bash
  uv run --package attendance-tracker train
  ```
- **Launch Live Recognition Stream HUD**:
  ```bash
  uv run --package attendance-tracker tracker
  # or simply:
  uv run tracker
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
