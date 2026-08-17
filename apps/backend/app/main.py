"""FastAPI Backend Application for Attendance Dashboard."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.database import init_db
from app.routers import analytics, attendance, employees, logs, students

app = FastAPI(
    title="Attendance System API",
    description="Backend API for Face & Gesture Recognition Attendance Dashboard",
    version="1.0.0",
)

# Enable CORS for Next.js frontend (allows both localhost and 127.0.0.1 on any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register routers
app.include_router(analytics.router)
app.include_router(attendance.router)
app.include_router(employees.router)
app.include_router(students.router)
app.include_router(logs.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "attendance-backend", "version": "1.0.0"}


def start():
    """Entrypoint for running the backend server."""
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    start()
